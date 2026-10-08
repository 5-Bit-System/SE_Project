from dataclasses import dataclass, field

from app.models import Catalog, ChoiceGroup, Course


@dataclass
class CourseVerdict:
    """Kết quả kiểm tra một môn; reasons rỗng nghĩa là hợp lệ."""

    course: Course
    reasons: list[dict] = field(default_factory=list)

    @property
    def eligible(self) -> bool:
        return not self.reasons


def missing_prerequisites(course: Course, passed: set[str]) -> list[list[str]]:
    """Các nhóm tiên quyết chưa có mã nào trong passed; qua 1 mã mỗi nhóm là đủ."""
    return [
        alternatives
        for alternatives in course.prerequisites
        if not any(code in passed for code in alternatives)
    ]


def group_usage(
    program_groups: list[ChoiceGroup], courses: list[Course], passed: set[str]
) -> dict[str, int]:
    """Tổng tín chỉ đã qua của từng nhóm; mỗi môn được tính vào mọi nhóm nó thuộc."""
    course_map = {course.code: course for course in courses}
    return {
        group.id: sum(
            course_map[code].credits
            for code in passed
            if code in course_map and group.id in course_map[code].choice_group_ids
        )
        for group in program_groups
    }


def evaluate_course(
    course: Course,
    passed: set[str],
    max_credits: int,
    groups: dict[str, ChoiceGroup],
    usage: dict[str, int],
) -> CourseVerdict:
    """Chạy mọi luật trên một môn, gom đủ lý do thay vì bỏ qua sớm."""
    reasons: list[dict] = []
    if course.prerequisite_status == "source_conflict":
        reasons.append(
            {
                "rule": "source_conflict",
                "message": "Tiên quyết trong nguồn PDF mâu thuẫn; chờ xác minh.",
            }
        )
    if course.code in passed:
        reasons.append(
            {"rule": "already_passed", "message": "Sinh viên đã hoàn thành môn này."}
        )
    if course.credits > max_credits:
        reasons.append(
            {
                "rule": "credit_limit",
                "message": f"Môn {course.credits} TC vượt hạn mức {max_credits} TC.",
            }
        )
    missing = missing_prerequisites(course, passed)
    if missing:
        reason: dict = {
            "rule": "missing_prerequisite",
            "message": "Chưa đủ tiên quyết.",
            "missing_groups": missing,
        }
        # Extra field: courses.json luôn có, fixture test-built có thể thiếu.
        known_external = set(getattr(course, "external_prerequisite_codes", []) or [])
        external = sorted(
            {code for group in missing for code in group} & known_external
        )
        if external:
            reason["external_codes"] = external
            reason["message"] = (
                "Thiếu mã nằm ngoài danh mục ngành; cần xác minh tương đương."
            )
        reasons.append(reason)
    if course.choice_group_ids and all(
        usage[group_id] >= groups[group_id].required_credits
        for group_id in course.choice_group_ids
    ):
        reasons.append(
            {
                "rule": "group_full",
                "message": "Nhóm tự chọn đã đủ chỉ tiêu.",
                "groups": list(course.choice_group_ids),
            }
        )
    return CourseVerdict(course=course, reasons=reasons)


def _evaluate_all(
    catalog: Catalog, passed: set[str], max_credits: int
) -> list[CourseVerdict]:
    groups = {group.id: group for group in catalog.program.choice_groups}
    usage = group_usage(catalog.program.choice_groups, catalog.courses, passed)
    return [
        evaluate_course(course, passed, max_credits, groups, usage)
        for course in catalog.courses
    ]


def eligible_courses(catalog: Catalog, passed: set[str], max_credits: int) -> list[Course]:
    """Filter using known, deterministic rules. More curriculum rules remain TODO."""
    return [
        verdict.course
        for verdict in _evaluate_all(catalog, passed, max_credits)
        if verdict.eligible
    ]
