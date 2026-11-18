"""Chấm điểm deterministic và modular từ metadata thực sự có trong catalog."""

import math

from app.models import Course, RankingWeights, StructuredPreference

LEVEL_MAPS = {
    "workload": {"light": 1.0, "moderate": 2.0, "heavy": 3.0},
    "difficulty": {"easy": 1.0, "moderate": 2.0, "advanced": 3.0},
}


def _metadata(course: Course) -> dict:
    return course.model_dump()


def _as_text(value: object) -> str:
    if isinstance(value, list | tuple | set):
        return " ".join(str(item) for item in value)
    return str(value) if value is not None else ""


def _metadata_match(course: Course, field: str, expected: str | None) -> float:
    if not expected:
        return 0.0
    metadata = _metadata(course)
    actual = metadata.get(field)
    if isinstance(actual, (list, tuple, set)):
        return 1.0 if expected in {str(item).casefold() for item in actual} else 0.0
    return 1.0 if str(actual).casefold() == expected.casefold() else 0.0


def gaussian_level_match(
    course_level: str | None,
    target_level: str | None,
    dimension: str = "workload",
    sigma: float = 1.0,
) -> float:
    """Tính điểm khớp mức độ tải học / độ khó theo hàm suy giảm Gaussian mềm [0..1]."""
    if not course_level or not target_level:
        return 0.0
    mapping = LEVEL_MAPS.get(dimension, {})
    val_course = mapping.get(str(course_level).casefold())
    val_target = mapping.get(str(target_level).casefold())
    if val_course is None or val_target is None:
        return 0.0
    diff = val_course - val_target
    return round(math.exp(-(diff**2) / (2.0 * (sigma**2))), 4)


def pref_fit_score(
    course: Course,
    preference: StructuredPreference,
    weights: RankingWeights | None = None,
) -> float:
    """Tính điểm độ phù hợp sở thích (pref_fit_score) trong khoảng [0..1]."""
    metadata = _metadata(course)
    searchable = " ".join(
        [
            course.code,
            course.name,
            str(metadata.get("name_en", "")),
            course.block,
            str(metadata.get("requirement_type", "")),
            _as_text(metadata.get("topics")),
            _as_text(metadata.get("orientation")),
        ]
    ).casefold()
    hits = sum(
        1
        for topic in preference.interest_topics
        if topic in (course.topics or []) or topic.casefold().replace("_", " ") in searchable
    )
    topic_score = (
        min(hits / max(len(preference.interest_topics), 1), 1.0)
        if preference.interest_topics
        else 0.0
    )

    type_score = (
        1.0
        if preference.course_type and metadata.get("requirement_type") == preference.course_type
        else 0.0
    )
    orientation_score = _metadata_match(course, "orientation", preference.orientation)
    difficulty_score = gaussian_level_match(
        metadata.get("difficulty") or getattr(course, "difficulty", None),
        preference.difficulty,
        "difficulty",
    )
    workload_score = gaussian_level_match(
        metadata.get("workload") or getattr(course, "workload", None),
        preference.workload,
        "workload",
    )
    goal_words = {word.casefold() for word in (preference.raw_goal or "").split() if len(word) > 2}
    name_score = min(sum(word in searchable for word in goal_words) / max(len(goal_words), 1), 1.0)
    career_score = (
        len(set(preference.career_paths) & set(course.career_paths or [])) / max(len(preference.career_paths), 1)
        if preference.career_paths
        else 0.0
    )

    weights = weights or RankingWeights()
    weighted_total = (
        weights.topic * topic_score
        + weights.career * career_score
        + weights.keyword * name_score
        + weights.course_type * type_score
        + weights.orientation * orientation_score
        + weights.difficulty * difficulty_score
        + weights.workload * workload_score
    )
    total_weight = sum(weights.model_dump().values())
    return round(min(1.0, weighted_total / max(total_weight, 1e-6)), 4)


def score_course(
    course: Course,
    preference: StructuredPreference,
    weights: RankingWeights | None = None,
    catalog_courses: list[Course] | None = None,
    failed_course_codes: set[str] | list[str] | None = None,
    choice_group_deficits: dict[str, int] | None = None,
    is_track_course: bool = False,
    alpha: float | None = None,
) -> float:
    """Trả về điểm [0, 1].

    - Nếu alpha is None (mặc định): Trả về pref_fit_score giữ tương thích ngược 100%.
    - Nếu alpha is not None: Kết hợp pref_fit_score và transcript_need_score theo hệ số alpha.
    """
    pref = pref_fit_score(course, preference, weights)
    if alpha is None:
        return pref
    need = transcript_need_score(
        course,
        catalog_courses=catalog_courses,
        failed_course_codes=failed_course_codes,
        choice_group_deficits=choice_group_deficits,
        is_track_course=is_track_course,
    )
    return combine_scores(pref, need, alpha=alpha)


def fit_reason(
    course: Course,
    preference: StructuredPreference,
    score: float,
    need_score: float | None = None,
) -> str:
    metadata = _metadata(course)
    matches: list[str] = []
    searchable = " ".join(
        [
            course.name,
            str(metadata.get("name_en", "")),
            course.block,
            _as_text(metadata.get("topics")),
        ]
    ).casefold()
    for topic in preference.interest_topics:
        if topic in (course.topics or []) or topic.casefold().replace("_", " ") in searchable:
            matches.append(topic)
    reasons: list[str] = []
    if matches:
        reasons.append(f"Tên hoặc metadata môn có chứa chủ đề người học nêu: {', '.join(matches)}.")
    for field in ("orientation", "difficulty", "workload"):
        if _metadata_match(course, field, getattr(preference, field)):
            reasons.append(f"Metadata {field} của môn khớp sở thích đã nêu.")
    if preference.course_type and metadata.get("requirement_type") == preference.course_type:
        reasons.append(f"Môn có loại {preference.course_type} đúng với preference đã chuẩn hóa.")
    if need_score is not None and need_score >= 0.5:
        if course.block == "required":
            reasons.append("Môn học bắt buộc quan trọng trong khung chương trình.")
        else:
            reasons.append("Môn có vai trò mở khóa điều kiện tiên quyết cho các kỳ tiếp theo.")
    if reasons:
        return " ".join(reasons)
    if score > 0:
        return "Môn có một phần từ khóa trùng với mục tiêu đã nhập."
    return "Catalog hiện chưa có metadata đủ để xác định điểm phù hợp cụ thể cho preference này."



def count_dag_dependents(course_code: str, catalog_courses: list[Course] | None = None) -> int:
    """Đếm số học phần trong catalog phụ thuộc (yêu cầu tiên quyết) vào course_code."""
    if not catalog_courses:
        return 0
    count = 0
    target = course_code.casefold()
    for c in catalog_courses:
        if c.code.casefold() == target:
            continue
        # c.prerequisites is list[list[str]] (outer AND, inner OR)
        prereqs = [code.casefold() for alt in (c.prerequisites or []) for code in alt]
        if target in prereqs:
            count += 1
    return count


def transcript_need_score(
    course: Course,
    catalog_courses: list[Course] | None = None,
    failed_course_codes: set[str] | list[str] | None = None,
    choice_group_deficits: dict[str, int] | None = None,
    is_track_course: bool = False,
) -> float:
    """Tính điểm cấp thiết học vụ (transcript_need_score) trong khoảng [0..1].

    Bao gồm:
    - Học lại môn bị điểm F (ưu tiên trả nợ môn).
    - Môn bắt buộc khối kiến thức hoặc môn thuộc nhánh chuyên ngành đã chọn.
    - Mở khóa các môn tiếp theo trên đồ thị có hướng tiên quyết (DAG).
    - Đáp ứng nhóm tự chọn còn thiếu nhiều tín chỉ nhất.
    """
    failed_set = set(failed_course_codes or [])
    retake_score = 1.0 if course.code in failed_set else 0.0

    if course.block == "required":
        req_score = 1.0
    elif is_track_course:
        req_score = 0.7
    else:
        req_score = 0.3

    dependents_count = count_dag_dependents(course.code, catalog_courses)
    dag_score = min(dependents_count / 2.0, 1.0)

    if choice_group_deficits and course.choice_group_ids:
        deficits = [choice_group_deficits.get(gid, 0) for gid in course.choice_group_ids]
        max_deficit = max(deficits) if deficits else 0
        quota_score = min(max_deficit / 10.0, 1.0) if max_deficit > 0 else 0.2
    else:
        quota_score = 0.5

    w_retake = 0.35
    w_req = 0.25
    w_dag = 0.25
    w_quota = 0.15
    total = (
        w_retake * retake_score
        + w_req * req_score
        + w_dag * dag_score
        + w_quota * quota_score
    )
    return round(min(1.0, max(0.0, total)), 4)



def combine_scores(pref_score: float, need_score: float, alpha: float = 0.5) -> float:
    """Kết hợp điểm phù hợp sở thích và điểm cấp thiết học vụ theo hệ số alpha [0..1].

    - alpha = 0.7: Ưu tiên sở thích, định hướng cá nhân (Phương án Đam mê).
    - alpha = 0.3: Ưu tiên tiến độ tốt nghiệp, mở khóa điều kiện (Phương án Tiến độ).
    - alpha = 0.5: Cân bằng hài hòa giữa sở thích và tiến độ.
    """
    alpha_clamped = max(0.0, min(1.0, float(alpha)))
    score = alpha_clamped * float(pref_score) + (1.0 - alpha_clamped) * float(need_score)
    return round(max(0.0, min(1.0, score)), 4)


def softmax_probabilities(
    scores: list[float] | dict[str, float],
    temperature: float = 1.0,
) -> list[float] | dict[str, float]:
    """Tính phân phối xác suất softmax (~%) từ danh sách hoặc dict điểm số của các môn ứng viên."""
    temp = max(1e-6, float(temperature))
    if isinstance(scores, dict):
        if not scores:
            return {}
        keys = list(scores.keys())
        vals = [float(scores[k]) for k in keys]
        max_v = max(vals)
        exp_vals = [math.exp((v - max_v) / temp) for v in vals]
        sum_exp = sum(exp_vals)
        probs = [round(v / sum_exp, 4) for v in exp_vals]
        diff = round(1.0 - sum(probs), 4)
        if probs:
            probs[0] = round(probs[0] + diff, 4)
        return dict(zip(keys, probs, strict=True))

    if not scores:
        return []
    if len(scores) == 1:
        return [1.0]
    vals = [float(s) for s in scores]
    max_val = max(vals)
    exp_vals = [math.exp((s - max_val) / temp) for s in vals]
    sum_exp = sum(exp_vals)
    probs = [round(v / sum_exp, 4) for v in exp_vals]
    diff = round(1.0 - sum(probs), 4)
    if probs:
        probs[0] = round(probs[0] + diff, 4)
    return probs
