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
) -> float:
    """Trả về điểm [0, 1]; giữ tương thích ngược hoàn toàn với các caller hiện có."""
    return pref_fit_score(course, preference, weights)


def fit_reason(course: Course, preference: StructuredPreference, score: float) -> str:
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
    if matches:
        return f"Tên hoặc metadata môn có chứa chủ đề người học nêu: {', '.join(matches)}."
    for field in ("orientation", "difficulty", "workload"):
        if _metadata_match(course, field, getattr(preference, field)):
            return f"Metadata {field} của môn khớp sở thích đã nêu."
    if preference.course_type and metadata.get("requirement_type") == preference.course_type:
        return f"Môn có loại {preference.course_type} đúng với preference đã chuẩn hóa."
    if score > 0:
        return "Môn có một phần từ khóa trùng với mục tiêu đã nhập."
    return "Catalog hiện chưa có metadata đủ để xác định điểm phù hợp cụ thể cho preference này."
