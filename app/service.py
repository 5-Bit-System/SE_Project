from app.models import Catalog, RecommendationRequest, RecommendationResponse, RecommendedCourse
from app.ranking import KeywordRanker, Ranker
from app.rules import eligible_courses


def recommend(
    catalog: Catalog,
    request: RecommendationRequest,
    ranker: Ranker | None = None,
) -> RecommendationResponse:
    if request.program_id != catalog.program.program_id:
        raise ValueError("Ngành đã chọn không khớp catalog")
    known = {course.code for course in catalog.courses}
    passed = set(request.passed_course_codes)
    unknown = passed - known
    if unknown:
        raise ValueError("Mã môn không thuộc catalog đã chọn: " + ", ".join(sorted(unknown)))
    candidates = eligible_courses(catalog, passed, request.max_credits)
    by_code = {course.code: course for course in candidates}
    warnings = []
    try:
        ranking = (ranker or KeywordRanker()).rank(candidates, request.goal)
        if not isinstance(ranking, list):
            raise ValueError("Ranker must return a list")
    except Exception:
        ranking = []
        warnings.append("Bộ xếp hạng gặp lỗi; đã dùng thứ tự dự phòng.")
    # Reject hallucinated/foreign/duplicate codes; fill gaps from safe baseline.
    ordered_codes = list(dict.fromkeys(code for code in ranking if isinstance(code, str) and code in by_code))
    ordered_codes.extend(code for code in KeywordRanker().rank(candidates, request.goal) if code not in ordered_codes)
    selected = []
    total = 0
    for code in ordered_codes:
        course = by_code[code]
        if total + course.credits > request.max_credits:
            continue
        selected.append(RecommendedCourse(
            code=course.code,
            name=course.name,
            credits=course.credits,
            reason="Đủ tiên quyết theo catalog; phù hợp mục tiêu cần được người học kiểm tra thêm.",
        ))
        total += course.credits
        if len(selected) >= request.limit:
            break
    if catalog.program.catalog_status != "verified":
        warnings.append("Catalog chưa được xác minh đầy đủ; kết quả chỉ dùng thử, không phải tư vấn học vụ.")
    return RecommendationResponse(
        program_id=catalog.program.program_id,
        catalog_status=catalog.program.catalog_status,
        recommendations=selected,
        eligible_count=len(candidates),
        warnings=warnings,
    )
