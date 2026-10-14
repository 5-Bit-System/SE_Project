from pydantic import Field

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

__all__ = [
    "Catalog",
    "ChoiceGroup",
    "Course",
    "GraduationPath",
    "GraduationSelection",
    "Program",
    "ProgramCatalogMetadata",
    "Track",
    "TrackSelection",
]
