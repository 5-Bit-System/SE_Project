"""Module 3 — Eligibility Rule Engine (`app.rules`).

Cổng kiểm tra điều kiện cứng:
1. Đảm bảo tỷ lệ vi phạm Eligibility Violation Rate = 0%.
2. Lọc môn đã hoàn thành.
3. Đối soát tiên quyết AND/OR chuẩn xác.
4. Kiểm soát định mức tín chỉ nhóm tự chọn (choice group quota).
5. Phân loại chi tiết tập môn Đủ điều kiện (eligible) và Bị chặn (blocked) kèm lý do cụ thể.
"""

from app.models import (
    BlockedCourse,
    BlockedReason,
    Catalog,
    Course,
    EligibilityResult,
)


def evaluate_eligibility(
    catalog: Catalog,
    passed_codes: set[str] | list[str],
    max_credits: int = 30,
) -> EligibilityResult:
    """Đánh giá toàn diện điều kiện học của tất cả môn học trong chương trình đào tạo."""
    passed = set(passed_codes)
    groups = {group.id: group for group in catalog.program.choice_groups}
    course_map = {course.code: course for course in catalog.courses}

    # Tính số tín chỉ đã học theo từng nhóm tự chọn (chỉ tính các môn trong catalog đã passed)
    used_by_group: dict[str, int] = {
        group_id: sum(
            course_map[code].credits
            for code in passed
            if code in course_map and group_id in course_map[code].choice_group_ids
        )
        for group_id in groups
    }

    eligible: list[Course] = []
    blocked: list[BlockedCourse] = []
    completed: list[str] = []

    for course in catalog.courses:
        # Nếu môn đã hoàn thành
        if course.code in passed:
            completed.append(course.code)
            continue

        reasons: list[BlockedReason] = []

        # 1. Kiểm tra trạng thái dữ liệu tiên quyết từ nguồn PDF
        if course.prerequisite_status == "source_conflict":
            reasons.append(
                BlockedReason(
                    kind="source_conflict",
                    message="Môn học có xung đột điều kiện tiên quyết trong tài liệu nguồn PDF.",
                )
            )

        # 2. Kiểm tra điều kiện tiên quyết (AND của các mệnh đề OR)
        missing_clauses: list[list[str]] = []
        for alternatives in course.prerequisites:
            if not any(code in passed for code in alternatives):
                missing_clauses.append(alternatives)

        if missing_clauses:
            clause_strs = []
            for alts in missing_clauses:
                if len(alts) == 1:
                    clause_strs.append(alts[0])
                else:
                    clause_strs.append(f"({' hoặc '.join(alts)})")
            reasons.append(
                BlockedReason(
                    kind="missing_prerequisites",
                    message=f"Chưa hoàn thành môn tiên quyết: {', '.join(clause_strs)}",
                    missing_prerequisites=missing_clauses,
                )
            )

        # 3. Kiểm tra định mức nhóm tự chọn
        if course.choice_group_ids and all(
            used_by_group.get(gid, 0) >= groups[gid].required_credits
            for gid in course.choice_group_ids
            if gid in groups
        ):
            full_group_names = [
                groups[gid].name
                for gid in course.choice_group_ids
                if gid in groups
            ]
            reasons.append(
                BlockedReason(
                    kind="choice_group_full",
                    message=f"Nhóm môn tự chọn ({', '.join(full_group_names)}) đã hoàn thành đủ số tín chỉ yêu cầu.",
                )
            )

        # 4. Kiểm tra giới hạn tín chỉ tối đa
        if course.credits > max_credits:
            reasons.append(
                BlockedReason(
                    kind="credits_exceeded",
                    message=f"Số tín chỉ môn học ({course.credits} TC) vượt quá giới hạn tối đa kỳ này ({max_credits} TC).",
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

    return EligibilityResult(
        program_id=catalog.program.program_id,
        eligible_courses=eligible,
        blocked_courses=blocked,
        completed_course_codes=sorted(completed),
        total_eligible=len(eligible),
        total_blocked=len(blocked),
        total_completed=len(completed),
    )


def eligible_courses(
    catalog: Catalog,
    passed: set[str],
    max_credits: int,
) -> list[Course]:
    """Hàm wrapper tương thích ngược, trả về danh sách môn eligible."""
    return evaluate_eligibility(catalog, passed, max_credits).eligible_courses
