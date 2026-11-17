import logging
from dataclasses import dataclass

from app.models import (
    Catalog,
    EligibilityResult,
    RankingWeights,
    RecommendationRequest,
    RecommendationResponse,
    RecommendedCourse,
)
from app.recommendation.explanation import (
    LLMPlanExplainer,
    build_deterministic_plan_explanation,
    build_grounded_explanation,
    configured_plan_explainer,
)
from app.recommendation.llm import LLMRanker
from app.recommendation.preference import PreferenceExtractor
from app.recommendation.ranking import KeywordRanker, Ranker
from app.recommendation.scoring import (
    combine_scores,
    compute_transcript_context,
    pref_fit_score,
    softmax_probabilities,
    transcript_need_score,
)
from app.recommendation.validation import validate_ranking_output
from app.rules import evaluate_eligibility
from app.services.study_intent_service import resolve_study_intent
from app.transcript import resolve_program_id

logger = logging.getLogger(__name__)


@dataclass
class _CandidateEval:
    course: object
    pref_score: float
    need_score: float
    total_score: float
    probability: float
    signals: list[str]
    is_retake: bool


def _group_allows(course, used_by_group: dict[str, int], group_required: dict[str, int]) -> bool:
    bounded = [gid for gid in course.choice_group_ids if gid in group_required]
    if not bounded:
        return True
    return any(used_by_group.get(gid, 0) < group_required[gid] for gid in bounded)


def _select_optimal_bundle(
    candidates: list[_CandidateEval],
    utilities: dict[str, float],
    *,
    target_credits: int,
    lower_credits: int,
    upper_credits: int,
    max_courses: int,
    group_earned: dict[str, int],
    group_required: dict[str, int],
) -> list[_CandidateEval]:
    """Chọn tổ hợp môn tối ưu tổng điểm phù hợp sao cho tổng TC nằm trong [L, U]."""
    if not candidates or max_courses <= 0 or upper_credits <= 0:
        return []

    # Giữ tập ứng viên có tính kiểm soát để Branch-and-Bound luôn < 5ms.
    if len(candidates) > 28:
        top_part = candidates[:22]
        top_codes = {item.course.code for item in top_part}
        small_fillers = sorted(
            (item for item in candidates if item.course.code not in top_codes),
            key=lambda item: (item.course.credits, -utilities[item.course.code], item.course.code),
        )[:6]
        pool = [*top_part, *small_fillers]
    else:
        pool = list(candidates)

    def score_subset(chosen: list[_CandidateEval], credits_sum: int) -> tuple:
        total_util = sum(utilities[item.course.code] + 0.05 for item in chosen)
        diff = abs(credits_sum - target_credits)
        in_band = lower_credits <= credits_sum <= upper_credits
        if in_band:
            objective = round(total_util - 0.08 * diff, 6)
            return (1, objective, -diff, int(credits_sum <= target_credits), round(total_util, 6))
        return (0, -diff, round(total_util, 6), credits_sum, 0)

    # Seed bằng greedy hợp lệ theo thứ tự ưu tiên để đảm bảo luôn có lời giải cận tốt.
    best_chosen: list[_CandidateEval] = []
    seed_used = dict(group_earned)
    seed_credits = 0
    for item in pool:
        if len(best_chosen) >= max_courses:
            break
        if seed_credits + item.course.credits > upper_credits:
            continue
        if not _group_allows(item.course, seed_used, group_required):
            continue
        best_chosen.append(item)
        seed_credits += item.course.credits
        for gid in item.course.choice_group_ids:
            if gid in group_required:
                seed_used[gid] = seed_used.get(gid, 0) + item.course.credits
    best_key = score_subset(best_chosen, seed_credits) if best_chosen else (-1, 0, 0, 0, 0)

    n = len(pool)
    suffix_max_credits = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix_max_credits[i] = suffix_max_credits[i + 1] + pool[i].course.credits

    # Chuẩn bị suffix utility sắp giảm dần để ước lượng cận trên chặt.
    used_groups = dict(group_earned)
    current: list[_CandidateEval] = []
    nodes = 0
    max_nodes = 35000

    def dfs(idx: int, credits_sum: int, util_sum: float) -> None:
        nonlocal best_chosen, best_key, nodes
        nodes += 1
        if nodes > max_nodes:
            return
        if current:
            cand_key = score_subset(current, credits_sum)
            if cand_key > best_key:
                best_key = cand_key
                best_chosen = list(current)
        if idx >= n or len(current) >= max_courses:
            return
        if best_key[0] == 1 and credits_sum + suffix_max_credits[idx] < lower_credits:
            return
        rem_slots = max_courses - len(current)
        # Cận trên lạc quan: lấy tối đa rem_slots môn còn lại có utility cao nhất vừa phần dư tín chỉ.
        if best_key[0] == 1:
            rem_budget = upper_credits - credits_sum
            optimistic = util_sum
            taken = 0
            for j in range(idx, n):
                if taken >= rem_slots or rem_budget <= 0:
                    break
                c_cred = pool[j].course.credits
                if c_cred <= rem_budget:
                    optimistic += utilities[pool[j].course.code] + 0.05
                    rem_budget -= c_cred
                    taken += 1
            if round(optimistic, 6) <= best_key[1]:
                return

        item = pool[idx]
        course = item.course
        if (
            credits_sum + course.credits <= upper_credits
            and _group_allows(course, used_groups, group_required)
        ):
            bounded = [gid for gid in course.choice_group_ids if gid in group_required]
            for gid in bounded:
                used_groups[gid] = used_groups.get(gid, 0) + course.credits
            current.append(item)
            dfs(idx + 1, credits_sum + course.credits, util_sum + utilities[course.code] + 0.05)
            current.pop()
            for gid in bounded:
                used_groups[gid] -= course.credits

        dfs(idx + 1, credits_sum, util_sum)

    dfs(0, 0, 0.0)
    return best_chosen


def recommend(
    catalog: Catalog,
    request: RecommendationRequest,
    ranker: Ranker | None = None,
    preference_extractor: PreferenceExtractor | None = None,
    llm_ranker: LLMRanker | None = None,
    eligibility: EligibilityResult | None = None,
    what_if: bool = False,
    plan_explainer: LLMPlanExplainer | None = None,
) -> RecommendationResponse:
    if resolve_program_id(request.program_id) != catalog.program.program_id:
        raise ValueError("Ngành đã chọn không khớp catalog")
    known = {course.code for course in catalog.courses}
    passed = set(request.passed_course_codes)
    unknown = passed - known
    if unknown:
        raise ValueError("Mã môn không thuộc catalog đã chọn: " + ", ".join(sorted(unknown)))
    failed = set(request.failed_course_codes) & known

    intent = resolve_study_intent(
        request.goal,
        catalog,
        form_input=request.form_input,
        legacy_preference=request.preference,
        extractor=preference_extractor,
        max_credits=request.max_credits,
        max_courses=request.limit,
    )
    preference = intent.preference
    # Ràng buộc cứng từ câu chat ("tối đa N tín chỉ") giữ tolerance = 0; mục tiêu bình thường dùng ±2.
    is_hard_text_cap = intent.diagnostics.field_sources.get("target_credits") == "text_rule"
    effective_tolerance = 0 if is_hard_text_cap else request.credit_tolerance
    target_credits = intent.max_credits
    upper_credits = min(30, target_credits + effective_tolerance)
    lower_credits = max(1, target_credits - effective_tolerance)

    eligibility = eligibility or evaluate_eligibility(
        catalog,
        passed,
        max_credits=upper_credits,
        selected_track_id=request.selected_track_id,
        selected_graduation_path_id=request.selected_graduation_path_id,
    )
    candidates = [
        c for c in eligibility.eligible_courses
        if getattr(c, "counted_in_total", True) is not False
    ]
    by_code = {course.code: course for course in candidates}
    ranking_weights = request.ranking_weights or RankingWeights()

    if preference.course_type_mode == "only" and preference.course_type:
        candidates = [c for c in candidates if c.requirement_type == preference.course_type]
        by_code = {c.code: c for c in candidates}
    warnings = intent.diagnostics.warnings.copy()
    if intent.diagnostics.status != "ready":
        return RecommendationResponse(
            program_id=catalog.program.program_id,
            catalog_status=catalog.program.catalog_status,
            recommendations=[],
            eligible_count=len(candidates),
            target_credits=target_credits,
            selected_credits=0,
            credit_tolerance=effective_tolerance,
            preference=preference,
            warnings=[*warnings, *intent.diagnostics.questions],
            intent=intent.diagnostics,
            plan_explanation=None,
        )

    transcript_ctx = compute_transcript_context(
        catalog,
        passed,
        failed_codes=failed,
        selected_track_id=request.selected_track_id,
        selected_graduation_path_id=request.selected_graduation_path_id,
        target_remaining_terms=request.target_remaining_terms,
    )
    if (
        transcript_ctx.remaining_total_credits is not None
        and 0 < transcript_ctx.remaining_total_credits < lower_credits
        and passed
    ):
        target_credits = min(target_credits, transcript_ctx.remaining_total_credits)
        lower_credits = max(1, target_credits - effective_tolerance)
        upper_credits = min(30, target_credits + effective_tolerance)
        warnings.append(
            f"Bạn chỉ còn thiếu {transcript_ctx.remaining_total_credits} tín chỉ theo CTĐT; "
            f"hệ thống đã điều chỉnh mục tiêu gợi ý sát phần tín chỉ còn lại."
        )

    eval_by_code: dict[str, _CandidateEval] = {}
    for course in candidates:
        p_score = pref_fit_score(course, preference, ranking_weights)
        n_score, signals = transcript_need_score(course, transcript_ctx)
        t_score = combine_scores(p_score, n_score, ranking_weights)
        eval_by_code[course.code] = _CandidateEval(
            course=course,
            pref_score=p_score,
            need_score=n_score,
            total_score=t_score,
            probability=0.0,
            signals=signals,
            is_retake=course.code in failed,
        )

    ordered_evals_for_prob = [eval_by_code[c.code] for c in candidates]
    probs = softmax_probabilities([ev.total_score for ev in ordered_evals_for_prob])
    for ev, prob in zip(ordered_evals_for_prob, probs, strict=True):
        ev.probability = prob

    backend_name = "probabilistic-transcript-dp-v2"
    explicit_order: list[str] | None = None
    if ranker is not None or llm_ranker is not None:
        try:
            active_ranker = ranker or llm_ranker
            if isinstance(active_ranker, (KeywordRanker, LLMRanker)):
                ranking = active_ranker.rank(
                    candidates,
                    request.goal,
                    preference=preference,
                    weights=ranking_weights,
                )
            else:
                ranking = active_ranker.rank(candidates, request.goal)
            backend_name = (
                f"custom:{active_ranker.__class__.__name__}"
                if ranker is not None
                else f"llm:{active_ranker.__class__.__name__}"
            )
            ordered_codes, validation_warnings = validate_ranking_output(ranking, set(by_code))
            warnings.extend(validation_warnings)
            if candidates and not ordered_codes:
                backend_name = "probabilistic-transcript-dp-v2"
                warnings.append("Output ranking không có mã eligible hợp lệ; đã dùng toàn bộ fallback deterministic.")
            else:
                explicit_order = ordered_codes
        except Exception as exc:
            logger.warning("Ranking fallback: %s", type(exc).__name__)
            warnings.append("LLM/bộ xếp hạng gặp lỗi; đã dùng thứ tự deterministic dự phòng.")

    if explicit_order is not None:
        fallback_rest = sorted(
            (c.code for c in candidates if c.code not in explicit_order),
            key=lambda code: (-eval_by_code[code].total_score, code),
        )
        ordered_codes = [*explicit_order, *fallback_rest]
        utilities = {
            code: max(0.01, 1.0 - idx * 0.01)
            for idx, code in enumerate(ordered_codes)
        }
        ranked_evals = [eval_by_code[code] for code in ordered_codes]
    else:
        ranked_evals = sorted(
            eval_by_code.values(),
            key=lambda ev: (-ev.total_score, -ev.pref_score, ev.course.code),
        )
        utilities = {ev.course.code: ev.total_score for ev in ranked_evals}

    chosen_evals = _select_optimal_bundle(
        ranked_evals,
        utilities,
        target_credits=target_credits,
        lower_credits=lower_credits,
        upper_credits=upper_credits,
        max_courses=intent.max_courses,
        group_earned=transcript_ctx.group_earned,
        group_required=transcript_ctx.group_required,
    )
    chosen_evals.sort(key=lambda ev: (-utilities[ev.course.code], ev.course.code))

    selected: list[RecommendedCourse] = []
    total = 0
    for ev in chosen_evals:
        course = ev.course
        explanation, fit = build_grounded_explanation(
            course,
            preference,
            eligibility.eligible_reasons.get(course.code, []),
            ev.total_score,
            transcript_signals=ev.signals,
        )
        selected.append(
            RecommendedCourse(
                code=course.code,
                name=course.name,
                credits=course.credits,
                reason=explanation,
                rank=len(selected) + 1,
                score=ev.total_score,
                fit_probability=ev.probability,
                is_retake=ev.is_retake,
                transcript_signals=ev.signals,
                eligibility_reason=eligibility.eligible_reasons.get(course.code, []),
                fit_reason=fit,
                source_status=catalog.program.catalog_status,
                offering_status="unknown",
            )
        )
        total += course.credits

    blocked_summary: dict[str, int] = {}
    for blocked in eligibility.blocked_courses:
        for reason in blocked.reasons:
            blocked_summary[reason.kind] = blocked_summary.get(reason.kind, 0) + 1
    if catalog.program.catalog_status != "verified":
        warnings.append("Catalog chưa được xác minh đầy đủ; kết quả chỉ dùng thử, không phải tư vấn học vụ.")
    warnings.append("Trạng thái mở lớp trong học kỳ chưa được xác minh từ dữ liệu hiện có.")
    if preference.interest_topics and not any(c.topics for c in candidates):
        warnings.append("Metadata chủ đề của các môn còn thiếu; chưa đủ căn cứ chấm phù hợp theo nhãn chủ đề.")
    assert total <= upper_credits and total <= 30 and len(selected) <= intent.max_courses

    omitted_eligible_count = max(0, len(candidates) - len(selected))
    deterministic_plan = build_deterministic_plan_explanation(
        catalog,
        selected,
        by_code,
        preference,
        transcript_ctx,
        target_credits=target_credits,
        selected_credits=total,
        credit_tolerance=effective_tolerance,
        omitted_eligible_count=omitted_eligible_count,
        ranking_weights=ranking_weights,
        warnings=warnings,
    )
    if request.include_narrative and selected:
        active_explainer = plan_explainer if plan_explainer is not None else configured_plan_explainer()
        if active_explainer is not None:
            plan_explanation = active_explainer.explain(
                catalog,
                selected,
                by_code,
                preference,
                transcript_ctx,
                target_credits=target_credits,
                selected_credits=total,
                credit_tolerance=effective_tolerance,
                omitted_eligible_count=omitted_eligible_count,
                ranking_weights=ranking_weights,
                warnings=warnings,
                fallback=deterministic_plan,
            )
        else:
            plan_explanation = deterministic_plan
    else:
        plan_explanation = deterministic_plan

    return RecommendationResponse(
        program_id=catalog.program.program_id,
        catalog_status=catalog.program.catalog_status,
        recommendations=selected,
        eligible_count=len(candidates),
        target_credits=target_credits,
        selected_credits=total,
        credit_tolerance=effective_tolerance,
        warnings=warnings,
        preference=preference,
        ranking_backend=backend_name,
        ranking_version="v2",
        blocked_summary=blocked_summary,
        ranking_weights=ranking_weights,
        what_if=what_if,
        intent=intent.diagnostics,
        plan_explanation=plan_explanation,
    )
