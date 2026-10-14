from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChoiceGroup(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    required_credits: int = Field(ge=0)


class Track(BaseModel):
    id: str
    name: str
    choice_group_ids: list[str] = Field(default_factory=list)


class TrackSelection(BaseModel):
    mode: Literal["not_applicable", "exactly_one_track"] = "not_applicable"
    tracks: list[Track] = Field(default_factory=list)


class GraduationPath(BaseModel):
    id: str
    name: str
    course_codes: list[str] = Field(default_factory=list)
    allowed_track_ids: list[str] = Field(default_factory=list)


class GraduationSelection(BaseModel):
    mode: Literal["not_applicable", "exactly_one_path"] = "not_applicable"
    required_credits: int = Field(default=0, ge=0)
    paths: list[GraduationPath] = Field(default_factory=list)


class Program(BaseModel):
    # Preserve curriculum blocks, tracks, graduation paths and source issues.
    model_config = ConfigDict(extra="allow")

    program_id: str
    name: str
    total_credits: int = Field(gt=0)
    catalog_status: Literal["draft_unverified", "verified"]
    source_file: str
    source_pages: str
    notes: list[str] = Field(default_factory=list)
    choice_groups: list[ChoiceGroup] = Field(default_factory=list)
    track_selection: TrackSelection = Field(default_factory=TrackSelection)
    graduation_selection: GraduationSelection = Field(default_factory=GraduationSelection)


class Course(BaseModel):
    # Preserve source provenance and bilingual names while keeping the core API.
    model_config = ConfigDict(extra="allow")

    code: str
    name: str
    credits: int = Field(gt=0)
    block: str
    # Outer list = AND; each inner list = OR. [] means no prerequisite.
    prerequisites: list[list[str]] = Field(default_factory=list)
    prerequisite_status: Literal["transcribed", "source_conflict"] = "transcribed"
    choice_group_ids: list[str] = Field(default_factory=list)
    source_page: int | None = None
    year: int | None = Field(default=None, ge=1, le=4, description="Năm học (1..4)")
    suggested_term: int | None = Field(default=None, ge=1, le=8, description="Học kỳ đề xuất (1..8)")


class Catalog(BaseModel):
    program: Program
    courses: list[Course]


class StructuredPreference(BaseModel):
    """Preference đã chuẩn hóa từ câu chat hoặc do client gửi trực tiếp.

    Các giá trị không có bằng chứng trong catalog được giữ ở dạng tùy chọn;
    chúng không được dùng để khẳng định một môn có workload hay độ khó cụ thể.
    """

    raw_goal: str = Field(default="", max_length=500)
    workload: Literal["light", "moderate", "heavy"] | None = None
    difficulty: Literal["easy", "moderate", "advanced"] | None = None
    orientation: Literal["theory", "practice", "research"] | None = None
    interest_topics: list[str] = Field(default_factory=list, max_length=20)
    career_goal: str | None = Field(default=None, max_length=200)
    target_credits: int | None = Field(default=None, ge=1, le=30)
    target_course_count: int | None = Field(default=None, ge=1, le=20)
    course_type: Literal["required", "elective"] | None = None
    prerequisite_tolerance: Literal["low", "medium", "high"] | None = None


class RankingWeights(BaseModel):
    """Trọng số xếp hạng; tổng trọng số được chuẩn hóa khi chấm điểm."""

    topic: float = Field(default=0.6, ge=0, le=1)
    keyword: float = Field(default=0.25, ge=0, le=1)
    course_type: float = Field(default=0.15, ge=0, le=1)
    orientation: float = Field(default=0.0, ge=0, le=1)
    difficulty: float = Field(default=0.0, ge=0, le=1)
    workload: float = Field(default=0.0, ge=0, le=1)

    @model_validator(mode="after")
    def require_positive_total(self) -> "RankingWeights":
        if sum(self.model_dump().values()) <= 0:
            raise ValueError("Ít nhất một ranking weight phải lớn hơn 0")
        return self


class RecommendationRequest(BaseModel):
    program_id: str
    passed_course_codes: list[str] = Field(default_factory=list)
    goal: str = Field(default="", max_length=500)
    max_credits: int = Field(default=18, ge=1, le=30)
    limit: int = Field(default=5, ge=1, le=20)
    selected_track_id: str | None = None
    selected_graduation_path_id: str | None = None
    preference: StructuredPreference | None = None
    ranking_weights: RankingWeights | None = None


class WhatIfRequest(RecommendationRequest):
    """Request xếp hạng lại trên cùng eligibility với bộ trọng số mới."""

    ranking_weights: RankingWeights = Field(default_factory=RankingWeights)


class RecommendedCourse(BaseModel):
    code: str
    name: str
    credits: int
    reason: str
    rank: int = Field(default=0, ge=0)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    eligibility_reason: list[str] = Field(default_factory=list)
    fit_reason: str = "Chưa có dữ liệu đủ để xác định mức độ phù hợp chi tiết."
    source_status: str = "unknown"
    offering_status: str = "unknown"


class RecommendationResponse(BaseModel):
    program_id: str
    catalog_status: str
    recommendations: list[RecommendedCourse]
    eligible_count: int
    warnings: list[str] = Field(default_factory=list)
    preference: StructuredPreference = Field(default_factory=StructuredPreference)
    ranking_backend: str = "deterministic-keyword-v1"
    ranking_version: str = "v1"
    blocked_summary: dict[str, int] = Field(default_factory=dict)
    ranking_weights: RankingWeights = Field(default_factory=RankingWeights)
    what_if: bool = False


class BlockedReason(BaseModel):
    kind: Literal[
        "missing_prerequisites",
        "choice_group_full",
        "credits_exceeded",
        "source_conflict",
        "track_mismatch",
        "graduation_path_mismatch",
    ]
    message: str
    missing_prerequisites: list[list[str]] = Field(default_factory=list)


class BlockedCourse(BaseModel):
    code: str
    name: str
    credits: int
    block: str
    reasons: list[BlockedReason] = Field(default_factory=list)


class EligibilityResult(BaseModel):
    program_id: str
    eligible_courses: list[Course]
    blocked_courses: list[BlockedCourse]
    completed_course_codes: list[str]
    total_eligible: int
    total_blocked: int
    total_completed: int
    eligible_reasons: dict[str, list[str]] = Field(default_factory=dict)


class EligibilityRequest(BaseModel):
    program_id: str
    passed_course_codes: list[str] = Field(default_factory=list)
    max_credits: int = Field(default=30, ge=1, le=50)
    selected_track_id: str | None = None
    selected_graduation_path_id: str | None = None
