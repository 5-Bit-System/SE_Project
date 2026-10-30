from typing import Literal

from pydantic import BaseModel, Field

from app.models import (
    Catalog,
    ChoiceGroup,
    Course,
    GraduationPath,
    GraduationSelection,
    Program,
    Track,
    TrackSelection,
)


class ProgramCatalogMetadata(Program):
    """Metadata CTĐT dùng trong response API, kèm số môn đã nạp."""

    course_count: int = Field(ge=0)


CourseSort = Literal["code", "name", "credits"]
CourseRequirementType = Literal["required", "elective", "required_excluded", "graduation"]


class CourseSearchPage(BaseModel):
    """Additive search contract; the legacy /courses array remains unchanged."""

    program_id: str
    items: list[Course]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


__all__ = [
    "Catalog",
    "ChoiceGroup",
    "Course",
    "CourseRequirementType",
    "CourseSearchPage",
    "CourseSort",
    "GraduationPath",
    "GraduationSelection",
    "Program",
    "ProgramCatalogMetadata",
    "Track",
    "TrackSelection",
]
