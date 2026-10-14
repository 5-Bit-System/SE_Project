from typing import Any

from pydantic import BaseModel, Field

from app.profiles import DemoProfile
from app.progress import CurriculumProgress
from app.schemas.catalog import ProgramCatalogMetadata


class ProfileSummary(BaseModel):
    """Thông tin nhẹ dùng để hiển thị danh sách profile demo."""

    profile_id: str
    program_id: str
    label: str
    current_term: int
    target_track: str | None = None
    career_goal: str = ""
    preferences: dict[str, Any] = Field(default_factory=dict)
    record_count: int = Field(ge=0)
    catalog: ProgramCatalogMetadata


class ProfileDetail(DemoProfile):
    """Profile đầy đủ, kèm metadata catalog mà profile đang dùng."""

    catalog: ProgramCatalogMetadata


class TranscriptSummary(BaseModel):
    """Tóm tắt transcript và phạm vi catalog đã dùng để tính toán."""

    profile_id: str | None = None
    program_id: str
    program_name: str
    current_term: int | None = None
    target_track: str | None = None
    career_goal: str | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)
    earned_credits: int
    progress: CurriculumProgress | None = None
    gpa: float | None = None
    gpa_10: float | None = None
    gpa_scale: float = 4.0
    passed_courses: list[str] = Field(default_factory=list)
    failed_courses: list[str] = Field(default_factory=list)
    isolation: dict[str, list[str]] = Field(default_factory=dict)
    catalog: ProgramCatalogMetadata


__all__ = ["ProfileDetail", "ProfileSummary", "TranscriptSummary"]
