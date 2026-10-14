"""Module 2 — Transcript & Profile Ingestion (`app.transcript`).

Quản lý tiếp nhận, chuẩn hóa bảng điểm sinh viên nhập tay, xác thực ngành học,
bảo đảm tính cô lập ngành (Major Isolation) và cung cấp interface nhận diện ngành từ bảng điểm.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Catalog

PROGRAM_ALIASES: dict[str, str] = {
    # Short aliases
    "khdl": "khdl_7460108_2022",
    "khmtt": "khmtt_7480113qtd_2022",
    "toan_hoc": "toan_hoc_7460101_2022",
    "toan_tin": "toan_tin_7460117_2022",
    # Full IDs
    "khdl_7460108_2022": "khdl_7460108_2022",
    "khmtt_7480113qtd_2022": "khmtt_7480113qtd_2022",
    "toan_hoc_7460101_2022": "toan_hoc_7460101_2022",
    "toan_tin_7460117_2022": "toan_tin_7460117_2022",
}


def grade_to_gpa4(grade: float) -> float:
    """Quy đổi điểm hệ 10 sang GPA hệ 4 theo bảng quy đổi của dự án."""
    if grade >= 9.0:
        return 4.0
    if grade >= 8.5:
        return 3.7
    if grade >= 8.0:
        return 3.5
    if grade >= 7.0:
        return 3.0
    if grade >= 6.5:
        return 2.5
    if grade >= 5.5:
        return 2.0
    if grade >= 5.0:
        return 1.5
    if grade >= 4.0:
        return 1.0
    return 0.0


def resolve_program_id(identifier: str) -> str:
    """Chuẩn hóa mã ngành học từ alias hoặc trả về ID gốc nếu hợp lệ."""
    cleaned = identifier.strip().lower()
    return PROGRAM_ALIASES.get(cleaned, identifier.strip())


class TranscriptRecord(BaseModel):
    """Bản ghi kết quả của một môn học trong bảng điểm."""

    model_config = ConfigDict(extra="allow")

    course_code: str = Field(..., description="Mã môn học, ví dụ MAT1093")
    grade: float | None = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Điểm số thang 10 (từ 0.0 đến 10.0)",
    )
    term: int | None = Field(
        default=None,
        ge=1,
        le=12,
        description="Học kỳ hoàn thành môn học (1..12)",
    )
    passed: bool = Field(
        default=True,
        description="Trạng thái hoàn thành/đạt môn học (điểm >= 5.0 hoặc được miễn)",
    )

    @field_validator("course_code")
    @classmethod
    def normalize_course_code(cls, v: str) -> str:
        code = v.strip().upper()
        if not code:
            raise ValueError("Mã môn học không được để trống")
        return code

    def model_post_init(self, __context: Any) -> None:
        """Nếu có điểm số thì tự động xác định trạng thái đạt theo quy chế (grade >= 5.0)."""
        if self.grade is not None:
            self.passed = self.grade >= 5.0


class StudentTranscript(BaseModel):
    """Bảng điểm sinh viên gắn liền với 1 ngành học duy nhất (Major Isolation)."""

    model_config = ConfigDict(extra="allow")

    program_id: str = Field(..., description="Mã CTĐT của sinh viên")
    records: list[TranscriptRecord] = Field(
        default_factory=list,
        description="Danh sách môn học đã học/đã nhập điểm",
    )

    @field_validator("program_id")
    @classmethod
    def normalize_program(cls, v: str) -> str:
        return resolve_program_id(v)

    @property
    def passed_course_codes(self) -> set[str]:
        """Tập hợp mã các môn đã đạt (passed = True)."""
        return {rec.course_code for rec in self.records if rec.passed}

    @property
    def failed_course_codes(self) -> set[str]:
        """Tập hợp mã các môn học nhưng chưa đạt (passed = False)."""
        return {rec.course_code for rec in self.records if not rec.passed}

    @property
    def all_course_codes(self) -> set[str]:
        """Tất cả mã môn có trong bảng điểm."""
        return {rec.course_code for rec in self.records}

    @property
    def grade_map(self) -> dict[str, float]:
        """Từ điển mã môn -> điểm số cho các môn có điểm."""
        return {rec.course_code: rec.grade for rec in self.records if rec.grade is not None}

    def validate_major_isolation(self, catalog: Catalog) -> dict[str, list[str]]:
        """Kiểm tra tính cô lập ngành và phạm vi của transcript.

        ``StudentTranscript`` luôn gắn với đúng một ``program_id``. Vì vậy
        transcript của ngành A không được coi là hợp lệ chỉ vì một vài mã môn
        tình cờ cũng xuất hiện trong catalog của ngành B.
        """
        catalog_program_id = resolve_program_id(catalog.program.program_id)
        if self.program_id != catalog_program_id:
            return {
                "valid_courses": [],
                "foreign_courses": sorted(self.all_course_codes),
            }

        catalog_codes = {c.code for c in catalog.courses}
        valid_courses = [code for code in self.all_course_codes if code in catalog_codes]
        foreign_courses = [code for code in self.all_course_codes if code not in catalog_codes]
        return {
            "valid_courses": sorted(valid_courses),
            "foreign_courses": sorted(foreign_courses),
        }

    def calculate_earned_credits(self, catalog: Catalog) -> int:
        """Tính tổng số tín chỉ tích lũy hợp lệ theo CTĐT."""
        excluded = getattr(catalog.program, "excluded_from_total", [])
        if not isinstance(excluded, list):
            excluded = []
        excluded_set = set(excluded)

        course_map = {c.code: c for c in catalog.courses}
        earned = 0
        for code in self.passed_course_codes:
            course = course_map.get(code)
            if course and code not in excluded_set:
                earned += course.credits
        return earned

    def calculate_gpa_10(self, catalog: Catalog) -> float | None:
        """Tính điểm trung bình tích lũy (GPA thang 10) có trọng số theo số tín chỉ.

        Không tính các học phần điều kiện (nằm trong excluded_from_total hoặc counted_in_total = False).
        """
        excluded = getattr(catalog.program, "excluded_from_total", [])
        if not isinstance(excluded, list):
            excluded = []
        excluded_set = set(excluded)

        course_map = {c.code: c for c in catalog.courses}
        total_weighted_points = 0.0
        total_credits = 0

        for rec in self.records:
            if rec.grade is not None and rec.course_code in course_map:
                if rec.course_code in excluded_set:
                    continue
                c = course_map[rec.course_code]
                if getattr(c, "counted_in_total", True) is False:
                    continue
                total_weighted_points += rec.grade * c.credits
                total_credits += c.credits

        if total_credits == 0:
            return None
        return round(total_weighted_points / total_credits, 2)

    def calculate_gpa(self, catalog: Catalog) -> float | None:
        """Tính GPA hệ 4 bằng cách quy đổi từng điểm môn rồi tính theo tín chỉ."""
        excluded = getattr(catalog.program, "excluded_from_total", [])
        if not isinstance(excluded, list):
            excluded = []
        excluded_set = set(excluded)

        course_map = {c.code: c for c in catalog.courses}
        total_weighted_points = 0.0
        total_credits = 0

        for rec in self.records:
            if rec.grade is not None and rec.course_code in course_map:
                if rec.course_code in excluded_set:
                    continue
                course = course_map[rec.course_code]
                if getattr(course, "counted_in_total", True) is False:
                    continue
                total_weighted_points += grade_to_gpa4(rec.grade) * course.credits
                total_credits += course.credits

        if total_credits == 0:
            return None
        return round(total_weighted_points / total_credits, 2)
