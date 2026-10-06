from typing import Literal

from pydantic import BaseModel, Field


class ChoiceGroup(BaseModel):
    id: str
    name: str
    required_credits: int = Field(ge=0)


class Program(BaseModel):
    program_id: str
    name: str
    total_credits: int = Field(gt=0)
    catalog_status: Literal["draft_unverified", "verified"]
    source_file: str
    source_pages: str
    notes: list[str] = Field(default_factory=list)
    choice_groups: list[ChoiceGroup] = Field(default_factory=list)


class Course(BaseModel):
    code: str
    name: str
    credits: int = Field(gt=0)
    block: str
    # Outer list = AND; each inner list = OR. [] means no prerequisite.
    prerequisites: list[list[str]] = Field(default_factory=list)
    choice_group_ids: list[str] = Field(default_factory=list)
    source_page: int | None = None


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
