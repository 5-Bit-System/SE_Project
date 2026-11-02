import logging

from app.models import (
    Catalog,
    EligibilityResult,
    RankingWeights,
    RecommendationRequest,
    RecommendationResponse,
    RecommendedCourse,
    StructuredPreference,
)
from app.recommendation.explanation import build_grounded_explanation
from app.recommendation.llm import LLMRanker
from app.recommendation.preference import PreferenceExtractor, extract_structured_preference
from app.recommendation.ranking import KeywordRanker, Ranker
from app.recommendation.scoring import score_course
from app.recommendation.validation import validate_ranking_output
from app.rules import evaluate_eligibility
from app.transcript import resolve_program_id

logger = logging.getLogger(__name__)


def recommend(
    catalog: Catalog,
    request: RecommendationRequest,
    ranker: Ranker | None = None,
    preference_extractor: PreferenceExtractor | None = None,
    llm_ranker: LLMRanker | None = None,
    eligibility: EligibilityResult | None = None,
    what_if: bool = False,
) -> RecommendationResponse:
    if resolve_program_id(request.program_id) != catalog.program.program_id:
        raise ValueError("Ngành đã chọn không khớp catalog")
    known = {course.code for course in catalog.courses}
    passed = set(request.passed_course_codes)
    unknown = passed - known
    if unknown:
        raise ValueError("Mã môn không thuộc catalog đã chọn: " + ", ".join(sorted(unknown)))
    eligibility = eligibility or evaluate_eligibility(
        catalog,
        passed,
        max_credits=request.max_credits,
        selected_track_id=request.selected_track_id,
        selected_graduation_path_id=request.selected_graduation_path_id,
    )
    candidates = eligibility.eligible_courses
    by_code = {course.code: course for course in candidates}
    ranking_weights = request.ranking_weights or RankingWeights()

    warnings: list[str] = []
    preference = request.preference
    if preference is None:
        try:
            if preference_extractor is None:
                preference = extract_structured_preference(request.goal)
            else:
                preference = preference_extractor.extract(request.goal)
                if isinstance(preference, dict):
                    preference = StructuredPreference.model_validate(preference)
                if not isinstance(preference, StructuredPreference):
                    raise ValueError("Preference extractor trả về sai schema")
        except Exception as exc:
            logger.warning("Preference fallback: %s", type(exc).__name__)
            preference = extract_structured_preference(request.goal)
            warnings.append("Preference extractor gặp lỗi; đã dùng structured preference deterministic.")
    if not preference.raw_goal and request.goal:
        preference = preference.model_copy(update={"raw_goal": request.goal[:500]})

    backend_name = "deterministic-keyword-v1"
    try:
        active_ranker = ranker or llm_ranker or KeywordRanker()
        if isinstance(active_ranker, (KeywordRanker, LLMRanker)):
            ranking = active_ranker.rank(
                candidates,
                request.goal,
                preference=preference,
                weights=ranking_weights,
            )
        else:
            ranking = active_ranker.rank(candidates, request.goal)
        if ranker is not None:
            backend_name = f"custom:{active_ranker.__class__.__name__}"
        elif llm_ranker is not None:
            backend_name = f"llm:{active_ranker.__class__.__name__}"
    except Exception as exc:
        logger.warning("Ranking fallback: %s", type(exc).__name__)
        ranking = []
        warnings.append("LLM/bộ xếp hạng gặp lỗi; đã dùng thứ tự deterministic dự phòng.")

    ordered_codes, validation_warnings = validate_ranking_output(ranking, set(by_code))
    warnings.extend(validation_warnings)
    if candidates and not ordered_codes and (llm_ranker is not None or ranker is not None):
        backend_name = "deterministic-keyword-v1"
        warnings.append("Output ranking không có mã eligible hợp lệ; đã dùng toàn bộ fallback deterministic.")
    fallback_codes = KeywordRanker().rank(
        candidates,
        request.goal,
        preference=preference,
        weights=ranking_weights,
    )
    ordered_codes.extend(code for code in fallback_codes if code not in ordered_codes)
    selected = []
    total = 0
    for code in ordered_codes:
        course = by_code[code]
        if total + course.credits > request.max_credits:
            continue
        score = score_course(course, preference, ranking_weights)
        explanation, fit = build_grounded_explanation(
            course,
            preference,
            eligibility.eligible_reasons.get(course.code, []),
            score,
        )
        selected.append(RecommendedCourse(
            code=course.code,
            name=course.name,
            credits=course.credits,
            reason=explanation,
            rank=len(selected) + 1,
            score=score,
            eligibility_reason=eligibility.eligible_reasons.get(course.code, []),
            fit_reason=fit,
            source_status=catalog.program.catalog_status,
            offering_status="unknown",
        ))
        total += course.credits
        if len(selected) >= request.limit:
            break
    blocked_summary: dict[str, int] = {}
    for blocked in eligibility.blocked_courses:
        for reason in blocked.reasons:
            blocked_summary[reason.kind] = blocked_summary.get(reason.kind, 0) + 1
    if catalog.program.catalog_status != "verified":
        warnings.append("Catalog chưa được xác minh đầy đủ; kết quả chỉ dùng thử, không phải tư vấn học vụ.")
    warnings.append("Trạng thái mở lớp trong học kỳ chưa được xác minh từ dữ liệu hiện có.")
    return RecommendationResponse(
        program_id=catalog.program.program_id,
        catalog_status=catalog.program.catalog_status,
        recommendations=selected,
        eligible_count=len(candidates),
        warnings=warnings,
        preference=preference,
        ranking_backend=backend_name,
        ranking_version="v1",
        blocked_summary=blocked_summary,
        ranking_weights=ranking_weights,
        what_if=what_if,
    )
