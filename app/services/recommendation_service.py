import heapq
import logging
from dataclasses import dataclass

from app.models import (
    Catalog,
    Course,
    EligibilityResult,
    RankingWeights,
    RecommendationRequest,
    RecommendationResponse,
    RecommendedCourse,
)
from app.progress import counts_toward_total
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
    early_thesis_reason,
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
    co_prerequisite_clauses: tuple[tuple[str, ...], ...] = ()
    dag_layer: int = 0


def _group_allows(course, used_by_group: dict[str, int], group_required: dict[str, int]) -> bool:
    bounded = [gid for gid in course.choice_group_ids if gid in group_required]
    if not bounded:
        return True
    return any(used_by_group.get(gid, 0) < group_required[gid] for gid in bounded)


def _is_bundle_prereq_valid(chosen: list[_CandidateEval]) -> bool:
    """Kiểm tra mọi môn học song hành trong tổ hợp đều mở được từ môn đã đạt."""
    reached = {item.course.code for item in chosen if not item.co_prerequisite_clauses}
    pending = [item for item in chosen if item.co_prerequisite_clauses]
    while pending:
        next_pending: list[_CandidateEval] = []
        progressed = False
        for item in pending:
            if all(any(req in reached for req in clause) for clause in item.co_prerequisite_clauses):
                reached.add(item.course.code)
                progressed = True
            else:
                next_pending.append(item)
        if not progressed:
            return False
        pending = next_pending
    return True


def _topological_order_pool(
    pool: list[_CandidateEval],
    utilities: dict[str, float],
) -> list[_CandidateEval]:
    """Sắp topo (Kahn) để tiên quyết luôn đứng trước môn phụ thuộc và giữ ưu tiên cặp cao."""
    by_code = {item.course.code: item for item in pool}
    pool_codes = set(by_code)
    dependents: dict[str, set[str]] = {code: set() for code in pool_codes}
    in_degree: dict[str, int] = {code: 0 for code in pool_codes}
    for item in pool:
        prereq_nodes = {
            req
            for clause in item.co_prerequisite_clauses
            for req in clause
            if req in pool_codes and req != item.course.code
        }
        in_degree[item.course.code] = len(prereq_nodes)
        for req in prereq_nodes:
            dependents[req].add(item.course.code)

    effective_priority: dict[str, float] = {}
    for item in sorted(
        pool,
        key=lambda ev: (-ev.dag_layer, -utilities[ev.course.code], ev.course.code),
    ):
        code = item.course.code
        child_priorities = [
            effective_priority[dep] for dep in dependents[code] if dep in effective_priority
        ]
        if child_priorities:
            best_pair = 0.5 * (utilities[code] + max(child_priorities))
            effective_priority[code] = max(utilities[code], best_pair)
        else:
            effective_priority[code] = utilities[code]

    heap: list[tuple[float, int, float, str]] = [
        (-effective_priority[code], by_code[code].dag_layer, -utilities[code], code)
        for code, deg in in_degree.items()
        if deg == 0
    ]
    heapq.heapify(heap)
    ordered: list[_CandidateEval] = []
    emitted: set[str] = set()

    while len(ordered) < len(pool):
        if not heap:
            # Phòng hờ vòng lặp OR tổng hợp: phá vòng theo tầng DAG nhỏ nhất.
            remaining_codes = sorted(
                pool_codes - emitted,
                key=lambda c: (by_code[c].dag_layer, -effective_priority[c], -utilities[c], c),
            )
            seed = remaining_codes[0]
            in_degree[seed] = 0
            heapq.heappush(heap, (-effective_priority[seed], by_code[seed].dag_layer, -utilities[seed], seed))
        _, _, _, code = heapq.heappop(heap)
        if code in emitted:
            continue
        emitted.add(code)
        ordered.append(by_code[code])
        for dep in dependents[code]:
            if dep in emitted:
                continue
            in_degree[dep] -= 1
            if in_degree[dep] <= 0:
                heapq.heappush(
                    heap,
                    (-effective_priority[dep], by_code[dep].dag_layer, -utilities[dep], dep),
                )
    return ordered


def _expand_co_prerequisite_candidates(
    catalog: Catalog,
    eligibility: EligibilityResult,
    base_eligible: list[Course],
    transcript_ctx,
    *,
    upper_credits: int,
    max_courses: int,
    course_type_only: str | None,
) -> tuple[list[Course], dict[str, tuple[tuple[str, ...], ...]], dict[str, int], dict[str, str]]:
    """Mở rộng tập ứng viên theo đồ thị DAG cho phép học cùng kỳ với môn tiên quyết."""
    course_by_code = {c.code: c for c in catalog.courses}
    effective_passed = set(eligibility.completed_course_codes)
    early_thesis_reasons: dict[str, str] = {}
    active: list[Course] = []
    dag_layers: dict[str, int] = {}
    raw_missing_clauses: dict[str, list[list[str]]] = {}

    for course in base_eligible:
        thesis_reason = early_thesis_reason(course, transcript_ctx)
        if thesis_reason is not None:
            early_thesis_reasons[course.code] = thesis_reason
        else:
            active.append(course)
            dag_layers[course.code] = 0

    active_codes = {c.code for c in active}
    available = effective_passed | active_codes
    layer = 1
    while True:
        promoted: list[tuple[Course, list[list[str]]]] = []
        for blocked in eligibility.blocked_courses:
            if blocked.code in active_codes:
                continue
            course = course_by_code.get(blocked.code)
            if course is None or not counts_toward_total(catalog, course):
                continue
            if course_type_only and course.requirement_type != course_type_only:
                continue
            if not blocked.reasons or any(r.kind != "missing_prerequisites" for r in blocked.reasons):
                continue
            thesis_reason = early_thesis_reason(course, transcript_ctx)
            if thesis_reason is not None:
                early_thesis_reasons[course.code] = thesis_reason
                continue
            clauses = [clause for r in blocked.reasons for clause in r.missing_prerequisites]
            if clauses and all(any(req in available for req in clause) for clause in clauses):
                promoted.append((course, clauses))
        if not promoted:
            break
        for course, clauses in promoted:
            active.append(course)
            active_codes.add(course.code)
            dag_layers[course.code] = layer
            raw_missing_clauses[course.code] = clauses
        available.update(course.code for course, _ in promoted)
        layer += 1

    co_clauses: dict[str, tuple[tuple[str, ...], ...]] = {
        code: tuple(
            tuple(req for req in clause if req in active_codes)
            for clause in clauses
        )
        for code, clauses in raw_missing_clauses.items()
    }

    # Lọc các môn phụ thuộc chắc chắn vượt giới hạn tín chỉ/số môn tối thiểu (cận dưới chắc chắn).
    while True:
        pruned: set[str] = set()
        for course in active:
            clauses = co_clauses.get(course.code, ())
            if not clauses:
                if course.credits > upper_credits or max_courses < 1:
                    pruned.add(course.code)
                continue
            if any(not clause for clause in clauses):
                pruned.add(course.code)
                continue
            must_have = {course.code}
            changed = True
            while changed:
                changed = False
                for code in list(must_have):
                    for clause in co_clauses.get(code, ()):
                        if len(clause) == 1 and clause[0] not in must_have:
                            must_have.add(clause[0])
                            changed = True
            must_credits = sum(course_by_code[code].credits for code in must_have)
            if must_credits > upper_credits or len(must_have) > max_courses:
                pruned.add(course.code)
                continue
            unsatisfied_or = [
                clause for clause in clauses if not any(req in must_have for req in clause)
            ]
            if any(
                all(must_credits + course_by_code[req].credits > upper_credits for req in clause)
                or len(must_have) + 1 > max_courses
                for clause in unsatisfied_or
            ):
                pruned.add(course.code)
        if not pruned:
            break
        active = [c for c in active if c.code not in pruned]
        active_codes = {c.code for c in active}
        co_clauses = {
            code: tuple(
                tuple(req for req in clause if req in active_codes)
                for clause in clauses
            )
            for code, clauses in co_clauses.items()
            if code in active_codes
        }

    return active, co_clauses, dag_layers, early_thesis_reasons


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

    # Giữ tập ứng viên có tính kiểm soát để Branch-and-Bound luôn < 5ms, đồng thời kéo theo tiên quyết bắt buộc.
    by_code = {item.course.code: item for item in candidates}
    if len(candidates) > 28:
        top_part = candidates[:22]
        top_codes = {item.course.code for item in top_part}
        small_fillers = sorted(
            (item for item in candidates if item.course.code not in top_codes),
            key=lambda item: (item.course.credits, -utilities[item.course.code], item.course.code),
        )[:6]
        pool = [*top_part, *small_fillers]
        pool_codes = {item.course.code for item in pool}
        queue_idx = 0
        while queue_idx < len(pool):
            item = pool[queue_idx]
            queue_idx += 1
            for clause in item.co_prerequisite_clauses:
                if any(req in pool_codes for req in clause):
                    continue
                options = [req for req in clause if req in by_code]
                if options:
                    best_req = max(
                        options,
                        key=lambda code: (utilities[code], -by_code[code].course.credits, code),
                    )
                    pool.append(by_code[best_req])
                    pool_codes.add(best_req)
    else:
        pool = list(candidates)

    ordered_pool = _topological_order_pool(pool, utilities)

    def score_subset(chosen: list[_CandidateEval], credits_sum: int) -> tuple:
        total_util = sum(utilities[item.course.code] + 0.05 for item in chosen)
        diff = abs(credits_sum - target_credits)
        in_band = lower_credits <= credits_sum <= upper_credits
        if in_band:
            objective = round(total_util - 0.08 * diff, 6)
            return (1, objective, -diff, int(credits_sum <= target_credits), round(total_util, 6))
        return (0, -diff, round(total_util, 6), credits_sum, 0)

    # Seed bằng greedy hợp lệ theo thứ tự topo-ưu tiên để đảm bảo luôn có lời giải cận tốt.
    best_chosen: list[_CandidateEval] = []
    seed_used = dict(group_earned)
    seed_codes: set[str] = set()
    seed_credits = 0
    for item in ordered_pool:
        if len(best_chosen) >= max_courses:
            break
        if seed_credits + item.course.credits > upper_credits:
            continue
        if not _group_allows(item.course, seed_used, group_required):
            continue
        clauses = item.co_prerequisite_clauses
        if clauses and not all(any(req in seed_codes for req in clause) for clause in clauses):
            continue
        best_chosen.append(item)
        seed_codes.add(item.course.code)
        seed_credits += item.course.credits
        for gid in item.course.choice_group_ids:
            if gid in group_required:
                seed_used[gid] = seed_used.get(gid, 0) + item.course.credits
    best_key = score_subset(best_chosen, seed_credits) if best_chosen else (-1, 0, 0, 0, 0)

    n = len(ordered_pool)
    suffix_max_credits = [0] * (n + 1)
    suffix_codes: list[set[str]] = [set() for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        suffix_max_credits[i] = suffix_max_credits[i + 1] + ordered_pool[i].course.credits
        suffix_codes[i] = suffix_codes[i + 1] | {ordered_pool[i].course.code}

    # Chuẩn bị suffix utility sắp giảm dần để ước lượng cận trên chặt.
    used_groups = dict(group_earned)
    chosen_codes: set[str] = set()
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
            if cand_key > best_key and _is_bundle_prereq_valid(current):
                best_key = cand_key
                best_chosen = list(current)
        if idx >= n or len(current) >= max_courses:
            return
        if best_key[0] == 1 and credits_sum + suffix_max_credits[idx] < lower_credits:
            return
        rem_slots = max_courses - len(current)
        # Cận trên lạc quan khả chấp: chỉ xét các môn còn nhóm, đủ ngân sách và có thể thỏa tiên quyết.
        if best_key[0] == 1:
            rem_budget = upper_credits - credits_sum
            future_avail = chosen_codes | suffix_codes[idx]
            top_utils = sorted(
                (
                    utilities[ordered_pool[j].course.code] + 0.05
                    for j in range(idx, n)
                    if ordered_pool[j].course.credits <= rem_budget
                    and _group_allows(ordered_pool[j].course, used_groups, group_required)
                    and (
                        not ordered_pool[j].co_prerequisite_clauses
                        or all(
                            any(req in future_avail for req in clause)
                            for clause in ordered_pool[j].co_prerequisite_clauses
                        )
                    )
                ),
                reverse=True,
            )[:rem_slots]
            optimistic = util_sum + sum(top_utils)
            if round(optimistic, 6) < best_key[1]:
                return

        item = ordered_pool[idx]
        course = item.course
        clauses = item.co_prerequisite_clauses
        prereqs_ok = not clauses or all(
            any(req in chosen_codes for req in clause) for clause in clauses
        )
        if (
            prereqs_ok
            and credits_sum + course.credits <= upper_credits
            and _group_allows(course, used_groups, group_required)
        ):
            bounded = [gid for gid in course.choice_group_ids if gid in group_required]
            for gid in bounded:
                used_groups[gid] = used_groups.get(gid, 0) + course.credits
            chosen_codes.add(course.code)
            current.append(item)
            dfs(idx + 1, credits_sum + course.credits, util_sum + utilities[course.code] + 0.05)
            current.pop()
            chosen_codes.remove(course.code)
            for gid in bounded:
                used_groups[gid] -= course.credits

        dfs(idx + 1, credits_sum, util_sum)

    dfs(0, 0, 0.0)
    assert _is_bundle_prereq_valid(best_chosen)
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
        if counts_toward_total(catalog, c)
    ]
    ranking_weights = request.ranking_weights or RankingWeights()

    course_type_only = (
        preference.course_type
        if preference.course_type_mode == "only" and preference.course_type
        else None
    )
    if course_type_only:
        candidates = [c for c in candidates if c.requirement_type == course_type_only]
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

    active_candidates, co_clauses_by_code, dag_layers, early_thesis_reasons = (
        _expand_co_prerequisite_candidates(
            catalog,
            eligibility,
            candidates,
            transcript_ctx,
            upper_credits=upper_credits,
            max_courses=intent.max_courses,
            course_type_only=course_type_only,
        )
    )
    active_by_code = {c.code: c for c in active_candidates}
    if early_thesis_reasons:
        deferred_codes = ", ".join(sorted(early_thesis_reasons))
        if transcript_ctx.target_remaining_terms is not None and transcript_ctx.target_remaining_terms > 1:
            warnings.append(
                f"Đã tạm hoãn {deferred_codes} (Khóa luận tốt nghiệp) khỏi gợi ý kỳ tới "
                f"vì mục tiêu tốt nghiệp còn {transcript_ctx.target_remaining_terms} học kỳ."
            )
        else:
            warnings.append(
                f"Đã tạm hoãn {deferred_codes} (Khóa luận tốt nghiệp) khỏi gợi ý kỳ tới "
                "do bảng điểm hiện chưa ở giai đoạn tốt nghiệp cuối khóa."
            )

    eval_by_code: dict[str, _CandidateEval] = {}
    for course in active_candidates:
        p_score = pref_fit_score(course, preference, ranking_weights)
        n_score, signals = transcript_need_score(course, transcript_ctx)
        t_score = combine_scores(
            p_score,
            n_score,
            ranking_weights,
            early_thesis_penalty=False,
        )
        eval_by_code[course.code] = _CandidateEval(
            course=course,
            pref_score=p_score,
            need_score=n_score,
            total_score=t_score,
            probability=0.0,
            signals=signals,
            is_retake=course.code in failed,
            co_prerequisite_clauses=co_clauses_by_code.get(course.code, ()),
            dag_layer=dag_layers.get(course.code, 0),
        )

    ordered_evals_for_prob = [eval_by_code[c.code] for c in active_candidates]
    probs = softmax_probabilities([ev.total_score for ev in ordered_evals_for_prob])
    for ev, prob in zip(ordered_evals_for_prob, probs, strict=True):
        ev.probability = prob

    backend_name = "probabilistic-transcript-dp-v2"
    explicit_order: list[str] | None = None
    if active_candidates and (ranker is not None or llm_ranker is not None):
        try:
            active_ranker = ranker or llm_ranker
            if isinstance(active_ranker, (KeywordRanker, LLMRanker)):
                ranking = active_ranker.rank(
                    active_candidates,
                    request.goal,
                    preference=preference,
                    weights=ranking_weights,
                )
            else:
                ranking = active_ranker.rank(active_candidates, request.goal)
            backend_name = (
                f"custom:{active_ranker.__class__.__name__}"
                if ranker is not None
                else f"llm:{active_ranker.__class__.__name__}"
            )
            ordered_codes, validation_warnings = validate_ranking_output(ranking, set(active_by_code))
            warnings.extend(validation_warnings)
            if active_candidates and not ordered_codes:
                backend_name = "probabilistic-transcript-dp-v2"
                warnings.append("Output ranking không có mã eligible hợp lệ; đã dùng toàn bộ fallback deterministic.")
            else:
                explicit_order = ordered_codes
        except Exception as exc:
            logger.warning("Ranking fallback: %s", type(exc).__name__)
            warnings.append("LLM/bộ xếp hạng gặp lỗi; đã dùng thứ tự deterministic dự phòng.")

    if explicit_order is not None:
        fallback_rest = sorted(
            (c.code for c in active_candidates if c.code not in explicit_order),
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

    selected_codes = {ev.course.code for ev in chosen_evals}
    co_enrolled_prereqs: dict[str, list[str]] = {}
    selected: list[RecommendedCourse] = []
    total = 0
    for ev in chosen_evals:
        course = ev.course
        co_prereqs: list[str] = []
        if ev.co_prerequisite_clauses:
            for clause in ev.co_prerequisite_clauses:
                for req in clause:
                    if req in selected_codes and req not in co_prereqs:
                        co_prereqs.append(req)
        if co_prereqs:
            co_enrolled_prereqs[course.code] = co_prereqs
            prereq_joined = ", ".join(co_prereqs)
            item_eligibility_reasons = [
                f"Đủ điều kiện học cùng kỳ với học phần tiên quyết {prereq_joined}."
            ]
            item_signals = [
                *ev.signals,
                f"Học song hành cùng học phần tiên quyết {prereq_joined} trong học kỳ này.",
            ]
        else:
            item_eligibility_reasons = eligibility.eligible_reasons.get(course.code, [])
            item_signals = ev.signals
        explanation, fit = build_grounded_explanation(
            course,
            preference,
            item_eligibility_reasons,
            ev.total_score,
            transcript_signals=item_signals,
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
                transcript_signals=item_signals,
                eligibility_reason=item_eligibility_reasons,
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
    if preference.interest_topics and not any(c.topics for c in active_candidates):
        warnings.append("Metadata chủ đề của các môn còn thiếu; chưa đủ căn cứ chấm phù hợp theo nhãn chủ đề.")
    assert total <= upper_credits and total <= 30 and len(selected) <= intent.max_courses

    omitted_eligible_count = max(0, len(active_candidates) - len(selected))
    deterministic_plan = build_deterministic_plan_explanation(
        catalog,
        selected,
        active_by_code,
        preference,
        transcript_ctx,
        target_credits=target_credits,
        selected_credits=total,
        credit_tolerance=effective_tolerance,
        omitted_eligible_count=omitted_eligible_count,
        ranking_weights=ranking_weights,
        warnings=warnings,
        co_enrolled_prereqs=co_enrolled_prereqs,
    )
    if request.include_narrative and selected:
        active_explainer = plan_explainer if plan_explainer is not None else configured_plan_explainer()
        if active_explainer is not None:
            plan_explanation = active_explainer.explain(
                catalog,
                selected,
                active_by_code,
                preference,
                transcript_ctx,
                target_credits=target_credits,
                selected_credits=total,
                credit_tolerance=effective_tolerance,
                omitted_eligible_count=omitted_eligible_count,
                ranking_weights=ranking_weights,
                warnings=warnings,
                fallback=deterministic_plan,
                co_enrolled_prereqs=co_enrolled_prereqs,
            )
        else:
            plan_explanation = deterministic_plan
    else:
        plan_explanation = deterministic_plan

    return RecommendationResponse(
        program_id=catalog.program.program_id,
        catalog_status=catalog.program.catalog_status,
        recommendations=selected,
        eligible_count=len(active_candidates),
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
