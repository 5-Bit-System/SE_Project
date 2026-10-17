"""Request and response contracts for the course advisor."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AdvisorMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: Literal["user", "assistant", "system"]
    content: str


class AdvisorRequest(BaseModel):
    program_id: str
    message: str = Field(..., max_length=1000, description="Nội dung câu hỏi của sinh viên")
    passed_course_codes: list[str] = Field(default_factory=list)
    history: list[AdvisorMessage] = Field(default_factory=list)
    selected_track_id: str | None = None
    selected_graduation_path_id: str | None = None


class AdvisorResponse(BaseModel):
    reply: str
    mode: Literal["gemini_llm", "heuristic_fallback", "guardrail_rejected"]
    is_guardrail_triggered: bool = False
    guardrail_reason: str | None = None
    suggested_courses: list[str] = Field(default_factory=list)
