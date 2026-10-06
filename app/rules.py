from app.models import Catalog, Course


def eligible_courses(catalog: Catalog, passed: set[str], max_credits: int) -> list[Course]:
    """Filter using known, deterministic rules. More curriculum rules remain TODO."""
    groups = {group.id: group for group in catalog.program.choice_groups}
    course_map = {course.code: course for course in catalog.courses}
    used_by_group = {
        group_id: sum(
            course_map[code].credits
            for code in passed
            if group_id in course_map[code].choice_group_ids
        )
        for group_id in groups
    }
    eligible = []
    for course in catalog.courses:
        if course.code in passed or course.credits > max_credits:
            continue
        if not all(any(code in passed for code in alternatives) for alternatives in course.prerequisites):
            continue
        if course.choice_group_ids and all(
            used_by_group[group_id] >= groups[group_id].required_credits
            for group_id in course.choice_group_ids
        ):
            continue
        eligible.append(course)
    return eligible
