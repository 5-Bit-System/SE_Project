"""Chấm điểm deterministic từ metadata thực sự có trong catalog."""

from app.models import Course, RankingWeights, StructuredPreference


def _metadata(course: Course) -> dict:
    return course.model_extra or {}


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


def score_course(
    course: Course,
    preference: StructuredPreference,
    weights: RankingWeights | None = None,
) -> float:
    """Trả về điểm [0, 1]; không coi metadata thiếu là điểm phù hợp."""
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
    hits = sum(1 for topic in preference.interest_topics if topic.casefold().replace("_", " ") in searchable)
    topic_score = min(hits / max(len(preference.interest_topics), 1), 1.0) if preference.interest_topics else 0.0

    type_score = 1.0 if preference.course_type and metadata.get("requirement_type") == preference.course_type else 0.0
    orientation_score = _metadata_match(course, "orientation", preference.orientation)
    difficulty_score = _metadata_match(course, "difficulty", preference.difficulty)
    workload_score = _metadata_match(course, "workload", preference.workload)
    goal_words = {
        word.casefold()
        for word in (preference.raw_goal or "").split()
        if len(word) > 2
    }
    name_score = min(sum(word in searchable for word in goal_words) / max(len(goal_words), 1), 1.0)
    weights = weights or RankingWeights()
    weighted_total = (
        weights.topic * topic_score
        + weights.keyword * name_score
        + weights.course_type * type_score
        + weights.orientation * orientation_score
        + weights.difficulty * difficulty_score
        + weights.workload * workload_score
    )
    total_weight = sum(weights.model_dump().values())
    return round(min(1.0, weighted_total / total_weight), 4)


def fit_reason(course: Course, preference: StructuredPreference, score: float) -> str:
    metadata = _metadata(course)
    matches: list[str] = []
    searchable = " ".join(
        [course.name, str(metadata.get("name_en", "")), course.block, _as_text(metadata.get("topics"))]
    ).casefold()
    for topic in preference.interest_topics:
        if topic.casefold().replace("_", " ") in searchable:
            matches.append(topic)
    if matches:
        return f"Tên hoặc metadata môn có chứa chủ đề người học nêu: {', '.join(matches)}."
    if preference.course_type and metadata.get("requirement_type") == preference.course_type:
        return f"Môn có loại {preference.course_type} đúng với preference đã chuẩn hóa."
    if score > 0:
        return "Môn có một phần từ khóa trùng với mục tiêu đã nhập."
    return "Catalog hiện chưa có metadata đủ để xác định điểm phù hợp cụ thể cho preference này."
