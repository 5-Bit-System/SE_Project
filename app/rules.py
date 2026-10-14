"""Eligibility rule engine.

Eligibility is deterministic and runs before ranking. This module is the
single place that decides whether a course can enter a recommendation
candidate set; ranking code must only choose from the returned eligible list.

The public models are intentionally unchanged. Input validation errors use
stable prefixes so API clients can distinguish an invalid transcript from an
invalid track/path selection without parsing the Vietnamese detail message.
"""

from app.models import (
    BlockedCourse,
    BlockedReason,
    Catalog,
    Course,
    EligibilityResult,
    GraduationPath,
    Track,
)


# Stable input error codes. The API currently serializes these through the
# HTTP 422 detail field, so keep the prefixes machine-readable.
UNKNOWN_PASSED_CODES = "unknown_passed_course_codes"
INVALID_TRACK_ID = "invalid_track_id"
INVALID_GRADUATION_PATH_ID = "invalid_graduation_path_id"
INCOMPATIBLE_TRACK_GRADUATION_PATH = "incompatible_track_graduation_path"
INVALID_MAX_CREDITS = "invalid_max_credits"


def _prepare_selection_context(
    catalog: Catalog,
    selected_track_id: str | None,
    selected_graduation_path_id: str | None,
) -> tuple[
    dict[str, Track],
    Track | None,
    set[str],
    set[str],
    dict[str, GraduationPath],
    GraduationPath | None,
    set[str],
    set[str],
]:
    """Validate selectors and return normalized track/path lookup data.

    A path with a non-empty ``allowed_track_ids`` list is constrained to those
    tracks. When both selectors are supplied and the pair is incompatible,
    the request is invalid as a whole. Returning unrelated courses as
    eligible in that state would make the recommendation appear valid while
    silently ignoring the student's selected graduation plan.
    """

    tracks = catalog.program.track_selection.tracks
    tracks_by_id = {track.id: track for track in tracks}
    if selected_track_id and selected_track_id not in tracks_by_id:
        raise ValueError(
            f"{INVALID_TRACK_ID}: Track không tồn tại trong catalog: {selected_track_id}"
        )

    selected_track = tracks_by_id.get(selected_track_id)
    selected_track_groups = (
        set(selected_track.choice_group_ids) if selected_track else set()
    )
    all_track_groups = {
        group_id
        for track in tracks_by_id.values()
        for group_id in track.choice_group_ids
    }

    paths = catalog.program.graduation_selection.paths
    paths_by_id = {path.id: path for path in paths}
    if selected_graduation_path_id and selected_graduation_path_id not in paths_by_id:
        raise ValueError(
            f"{INVALID_GRADUATION_PATH_ID}: Hướng tốt nghiệp không tồn tại trong "
            f"catalog: {selected_graduation_path_id}"
        )

    selected_path = paths_by_id.get(selected_graduation_path_id)
    selected_path_courses = (
        set(selected_path.course_codes) if selected_path else set()
    )
    path_course_ids = {
        course_code
        for path in paths_by_id.values()
        for course_code in path.course_codes
    }

    if selected_track and selected_path:
        allowed_tracks = set(selected_path.allowed_track_ids)
        if allowed_tracks and selected_track.id not in allowed_tracks:
            raise ValueError(
                f"{INCOMPATIBLE_TRACK_GRADUATION_PATH}: "
                f"Track '{selected_track.id}' không áp dụng cho hướng tốt nghiệp "
                f"'{selected_path.id}'."
            )

    return (
        tracks_by_id,
        selected_track,
        selected_track_groups,
        all_track_groups,
        paths_by_id,
        selected_path,
        selected_path_courses,
        path_course_ids,
    )


def _validate_passed_codes(
    passed_codes: set[str] | list[str],
    known_codes: set[str],
) -> set[str]:
    """Normalize passed codes and reject codes outside the selected catalog."""

    passed = set(passed_codes)
    unknown = passed - known_codes
    if unknown:
        raise ValueError(
            f"{UNKNOWN_PASSED_CODES}: Mã môn không thuộc catalog đã chọn: "
            + ", ".join(sorted(unknown))
        )
    return passed


def _validate_max_credits(max_credits: int) -> None:
    """Ensure the total recommendation budget is usable."""

    if max_credits <= 0:
        raise ValueError(f"{INVALID_MAX_CREDITS}: max_credits phải lớn hơn 0.")


def evaluate_eligibility(
    catalog: Catalog,
    passed_codes: set[str] | list[str],
    max_credits: int = 30,
    selected_track_id: str | None = None,
    selected_graduation_path_id: str | None = None,
) -> EligibilityResult:
    """Evaluate every course in one catalog against hard eligibility rules.

    ``max_credits`` is the total credit budget for the recommendation request.
    Eligibility does not greedily consume that budget across courses because
    doing so would make the eligible set depend on catalog order. It only
    blocks a single course whose own credits exceed the total budget; the
    recommendation service applies the same budget while selecting a set and
    sums the selected course credits.
    """

    _validate_max_credits(max_credits)

    groups = {group.id: group for group in catalog.program.choice_groups}
    course_map = {course.code: course for course in catalog.courses}
    passed = _validate_passed_codes(passed_codes, set(course_map))
    (
        _tracks_by_id,
        selected_track,
        selected_track_groups,
        all_track_groups,
        _paths_by_id,
        selected_path,
        selected_path_courses,
        path_course_ids,
    ) = _prepare_selection_context(
        catalog,
        selected_track_id,
        selected_graduation_path_id,
    )

    # Credits already earned count toward each group the course belongs to.
    # A course in multiple groups is counted in each group's independent
    # quota, while transcript credit totals still count it once.
    used_by_group: dict[str, int] = {
        group_id: sum(
            course_map[code].credits
            for code in passed
            if group_id in course_map[code].choice_group_ids
        )
        for group_id in groups
    }

    eligible: list[Course] = []
    blocked: list[BlockedCourse] = []
    completed: list[str] = []
    eligible_reasons: dict[str, list[str]] = {}

    for course in catalog.courses:
        if course.code in passed:
            completed.append(course.code)
            continue

        reasons: list[BlockedReason] = []

        # Reason order is deliberate and stable for UI/fallback consumers:
        # source -> prerequisites -> track/path -> group -> credit budget.
        if course.prerequisite_status in ("source_conflict", "conflict"):
            reasons.append(
                BlockedReason(
                    kind="source_conflict",
                    message=(
                        "Môn học có xung đột điều kiện tiên quyết trong tài liệu "
                        "nguồn PDF."
                    ),
                )
            )
        elif course.prerequisite_status == "unknown":
            reasons.append(
                BlockedReason(
                    kind="prerequisite_unknown",
                    message="Điều kiện tiên quyết của môn học chưa được xác định từ tài liệu nguồn.",
                )
            )

        # Outer list is AND; each inner list is OR. Unknown prerequisite
        # references remain missing and can never be unlocked by an external
        # code because passed codes are restricted to this catalog.
        missing_clauses: list[list[str]] = []
        for alternatives in course.prerequisites:
            if not any(code in passed for code in alternatives):
                missing_clauses.append(alternatives)

        if missing_clauses:
            clause_strings = []
            for alternatives in missing_clauses:
                if len(alternatives) == 1:
                    clause_strings.append(alternatives[0])
                else:
                    clause_strings.append(f"({' hoặc '.join(alternatives)})")
            reasons.append(
                BlockedReason(
                    kind="missing_prerequisites",
                    message=(
                        "Chưa hoàn thành môn tiên quyết: "
                        + ", ".join(clause_strings)
                    ),
                    missing_prerequisites=missing_clauses,
                )
            )

        # Track membership is represented by choice groups. Courses shared by
        # multiple tracks remain available when they intersect the selected
        # track; courses belonging to another track are blocked.
        if selected_track_id and course.choice_group_ids:
            course_track_groups = set(course.choice_group_ids) & all_track_groups
            if course_track_groups and not course_track_groups & selected_track_groups:
                reasons.append(
                    BlockedReason(
                        kind="track_mismatch",
                        message=(
                            "Môn thuộc hướng khác với track đã chọn: "
                            f"{selected_track.name if selected_track else selected_track_id}."
                        ),
                    )
                )

        # With a selected graduation path, every course explicitly assigned to
        # another path is blocked. A course shared by paths is available when
        # it is included in the selected path.
        if (
            selected_graduation_path_id
            and course.code in path_course_ids
            and course.code not in selected_path_courses
        ):
            reasons.append(
                BlockedReason(
                    kind="graduation_path_mismatch",
                    message=(
                        "Môn thuộc nhánh tốt nghiệp khác với nhánh đã chọn: "
                        f"{selected_path.name if selected_path else selected_graduation_path_id}."
                    ),
                )
            )

        # A choice-group quota is full only when every known group attached to
        # the course is full. This preserves OR-style membership for courses
        # that can satisfy more than one group.
        course_groups = [
            groups[group_id]
            for group_id in course.choice_group_ids
            if group_id in groups
        ]
        if course_groups and all(
            used_by_group[group.id] >= group.required_credits
            for group in course_groups
        ):
            reasons.append(
                BlockedReason(
                    kind="choice_group_full",
                    message=(
                        "Nhóm môn tự chọn ("
                        + ", ".join(group.name for group in course_groups)
                        + ") đã hoàn thành đủ số tín chỉ yêu cầu."
                    ),
                )
            )

        # This is a per-course feasibility check against the same total budget
        # used by recommendation selection. Courses are not greedily removed
        # based on the sum of all eligible courses.
        if course.credits > max_credits:
            reasons.append(
                BlockedReason(
                    kind="credits_exceeded",
                    message=(
                        f"Số tín chỉ môn học ({course.credits} TC) vượt quá "
                        f"ngân sách recommendation ({max_credits} TC)."
                    ),
                )
            )

        if reasons:
            blocked.append(
                BlockedCourse(
                    code=course.code,
                    name=course.name,
                    credits=course.credits,
                    block=course.block,
                    reasons=reasons,
                )
            )
        else:
            eligible.append(course)
            eligible_reasons[course.code] = [
                "Chưa hoàn thành môn này và đã thỏa các prerequisite trong catalog."
            ]

    return EligibilityResult(
        program_id=catalog.program.program_id,
        eligible_courses=eligible,
        blocked_courses=blocked,
        completed_course_codes=sorted(completed),
        total_eligible=len(eligible),
        total_blocked=len(blocked),
        total_completed=len(completed),
        eligible_reasons=eligible_reasons,
    )


def eligible_courses(
    catalog: Catalog,
    passed: set[str],
    max_credits: int,
    selected_track_id: str | None = None,
    selected_graduation_path_id: str | None = None,
) -> list[Course]:
    """Backward-compatible wrapper returning only eligible courses."""

    return evaluate_eligibility(
        catalog,
        passed,
        max_credits,
        selected_track_id=selected_track_id,
        selected_graduation_path_id=selected_graduation_path_id,
    ).eligible_courses
