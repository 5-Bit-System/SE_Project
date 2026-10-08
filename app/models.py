from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChoiceGroup(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    required_credits: int = Field(ge=0)


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


class RecommendationRequest(BaseModel):
    program_id: str
    passed_course_codes: list[str] = Field(default_factory=list)
    goal: str = Field(default="", max_length=500)
    max_credits: int = Field(default=18, ge=1, le=30)
    limit: int = Field(default=5, ge=1, le=20)


class RecommendedCourse(BaseModel):
    code: str
    name: str
    credits: int
    reason: str


class RecommendationResponse(BaseModel):
    program_id: str
    catalog_status: str
    recommendations: list[RecommendedCourse]
    eligible_count: int
    warnings: list[str] = Field(default_factory=list)


class BlockedReason(BaseModel):
    kind: Literal[
        "missing_prerequisites",
        "choice_group_full",
        "credits_exceeded",
        "source_conflict",
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


class EligibilityRequest(BaseModel):
    program_id: str
    passed_course_codes: list[str] = Field(default_factory=list)
    max_credits: int = Field(default=30, ge=1, le=50)
