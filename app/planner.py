"""Module 4 — Curriculum Roadmap Allocator (`app.planner`).

Phân bổ và xuất lộ trình học tập 4 năm (Năm 1 -> Năm 4) cho sinh viên:
1. Tính toán độ sâu đồ thị tiên quyết (DAG depth) cho từng môn.
2. Phân loại mốc năm học (Year 1, 2, 3, 4) và học kỳ gợi ý (Term 1..8) dựa trên khối kiến thức và đồ thị tiên quyết.
3. Đảm bảo bất biến Topo (Topological Invariant): không xếp môn học ở năm trước môn tiên quyết của nó.
4. Tích hợp trạng thái sinh viên (completed, eligible, blocked) từ Rule Engine để hiển thị tiến độ 4 năm trực quan.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.models import Catalog, Course
from app.rules import evaluate_eligibility

BLOCK_NAMES: dict[str, str] = {
    "general": "Khối kiến thức chung",
    "field": "Khối kiến thức theo lĩnh vực",
    "discipline": "Khối kiến thức theo khối ngành",
    "group": "Khối kiến thức theo nhóm ngành",
    "major": "Khối kiến thức ngành",
}


class PlannedCourse(BaseModel):
    """Thông tin môn học được phân bổ trong lộ trình 4 năm."""

    model_config = ConfigDict(extra="allow")

    code: str
    name: str
    name_en: str | None = None
    credits: int
    block: str
    block_name: str
    year: int = Field(ge=1, le=4, description="Năm học (1..4)")
    suggested_term: int = Field(ge=1, le=8, description="Học kỳ đề xuất (1..8)")
    requirement_type: str = Field(default="required", description="required hoặc elective")
    prerequisites: list[list[str]] = Field(default_factory=list)
    status: str = Field(
        default="available",
        description="Trạng thái học vụ: completed, eligible, blocked, available",
    )
    blocked_reasons: list[str] = Field(default_factory=list)


class YearPlan(BaseModel):
    """Kế hoạch học tập cho một năm học."""

    year: int = Field(ge=1, le=4)
    year_name: str
    total_credits: int
    course_count: int
    completed_credits: int = 0
    courses: list[PlannedCourse] = Field(default_factory=list)


class CurriculumRoadmap(BaseModel):
    """Lộ trình học tập tổng thể 4 năm của chương trình đào tạo."""

    program_id: str
    program_name: str
    total_credits: int
    years: list[YearPlan]
    progress: dict[str, Any] = Field(default_factory=dict)


def compute_prerequisite_depths(catalog: Catalog) -> dict[str, int]:
    """Tính độ sâu tiên quyết (prerequisite depth) của từng môn học trong catalog."""
    course_map = {c.code: c for c in catalog.courses}
    depths: dict[str, int] = {}

    def get_depth(code: str) -> int:
        if code in depths:
            return depths[code]
        course = course_map.get(code)
        if not course or not course.prerequisites:
            depths[code] = 0
            return 0

        clause_depths: list[int] = []
        for clause in course.prerequisites:
            # Với mệnh đề OR [A, B], độ sâu cần thiết để mở khóa là min depth của các phương án
            alts_in_cat = [p for p in clause if p in course_map]
            if alts_in_cat:
                clause_depths.append(min(get_depth(p) for p in alts_in_cat))
            else:
                # Nếu tiên quyết là mã ngoại lai
                clause_depths.append(0)

        depth = 1 + max(clause_depths) if clause_depths else 0
        depths[code] = depth
        return depth

    for c in catalog.courses:
        get_depth(c.code)

    return depths


def allocate_course_years(catalog: Catalog) -> dict[str, tuple[int, int]]:
    """Phân bổ năm học (1..4) và học kỳ đề xuất (1..8) cho toàn bộ môn trong catalog.

    Trả về dict: course_code -> (year, suggested_term).
    """
    depths = compute_prerequisite_depths(catalog)
    year_map: dict[str, int] = {}

    # Bước 1: Gán baseline year dựa vào khối kiến thức (block) và loại môn
    for c in catalog.courses:
        depth = depths.get(c.code, 0)
        grad_paths = getattr(c, "graduation_path_ids", [])

        if grad_paths:
            # Khóa luận tốt nghiệp hoặc môn thay thế khóa luận luôn ở Năm 4
            base_year = 4
        elif c.block in ("general", "field", "discipline"):
            base_year = 1 if depth == 0 else 2
        elif c.block == "group":
            base_year = 1 if depth == 0 else 2
        else:  # major
            if depth <= 1:
                base_year = 2
            elif depth == 2:
                base_year = 3
            else:
                base_year = 4

        year_map[c.code] = base_year

    # Bước 2: Hiệu chỉnh Topo (Topological Relaxation)
    # Môn con không được phép có năm học nhỏ hơn năm học của bất kỳ môn tiên quyết bắt buộc nào
    changed = True
    while changed:
        changed = False
        for c in catalog.courses:
            if not c.prerequisites:
                continue
            valid_clauses = [[p for p in cl if p in year_map] for cl in c.prerequisites]
            valid_clauses = [cl for cl in valid_clauses if cl]
            if not valid_clauses:
                continue
            min_req_year = max(min(year_map[p] for p in cl) for cl in valid_clauses)
            if year_map[c.code] < min_req_year:
                year_map[c.code] = min_req_year
                changed = True

    # Giới hạn năm học trong khoảng 1..4
    for c in catalog.courses:
        year_map[c.code] = min(4, max(1, year_map[c.code]))

    # Bước 3: Gán suggested_term (1..8)
    allocation: dict[str, tuple[int, int]] = {}
    for c in catalog.courses:
        yr = year_map[c.code]
        depth = depths.get(c.code, 0)
        # Nếu depth chẵn thì xếp kỳ đầu của năm, depth lẻ xếp kỳ sau của năm
        sub_term = 1 if (depth % 2 == 0) else 2
        term = (yr - 1) * 2 + sub_term
        allocation[c.code] = (yr, term)

    return allocation


def generate_roadmap(
    catalog: Catalog,
    passed_course_codes: list[str] | set[str] | None = None,
) -> CurriculumRoadmap:
    """Tạo lộ trình học tập 4 năm đầy đủ, tích hợp trạng thái học vụ sinh viên."""
    passed = set(passed_course_codes or [])
    allocation = allocate_course_years(catalog)

    # Đánh giá điều kiện học vụ nếu sinh viên có bảng điểm
    eligibility = evaluate_eligibility(catalog, passed, max_credits=40)
    eligible_set = {c.code for c in eligibility.eligible_courses}
    blocked_dict = {b.code: b for b in eligibility.blocked_courses}
    completed_set = set(eligibility.completed_course_codes)

    year_courses: dict[int, list[PlannedCourse]] = {1: [], 2: [], 3: [], 4: []}

    for c in catalog.courses:
        year, term = allocation.get(c.code, (1, 1))

        # Xác định trạng thái môn học
        if c.code in completed_set:
            status = "completed"
            reasons = []
        elif c.code in eligible_set:
            status = "eligible"
            reasons = []
        elif c.code in blocked_dict:
            status = "blocked"
            reasons = [r.message for r in blocked_dict[c.code].reasons]
        else:
            status = "available"
            reasons = []

        planned = PlannedCourse(
            code=c.code,
            name=c.name,
            name_en=getattr(c, "name_en", None),
            credits=c.credits,
            block=c.block,
            block_name=BLOCK_NAMES.get(c.block, c.block),
            year=year,
            suggested_term=term,
            requirement_type=getattr(c, "requirement_type", "required"),
            prerequisites=c.prerequisites,
            status=status,
            blocked_reasons=reasons,
        )
        year_courses[year].append(planned)

    years_plan: list[YearPlan] = []
    total_completed_credits = 0

    for yr in range(1, 5):
        courses = year_courses[yr]
        total_cred = sum(p.credits for p in courses)
        completed_cred = sum(p.credits for p in courses if p.status == "completed")
        total_completed_credits += completed_cred

        years_plan.append(
            YearPlan(
                year=yr,
                year_name=f"Năm {yr}",
                total_credits=total_cred,
                course_count=len(courses),
                completed_credits=completed_cred,
                courses=courses,
            )
        )

    progress = {
        "completed_courses_count": len(completed_set),
        "completed_credits": total_completed_credits,
        "eligible_courses_count": len(eligible_set),
        "blocked_courses_count": len(blocked_dict),
        "total_catalog_courses": len(catalog.courses),
    }

    return CurriculumRoadmap(
        program_id=catalog.program.program_id,
        program_name=catalog.program.name,
        total_credits=catalog.program.total_credits,
        years=years_plan,
        progress=progress,
    )
