"""Allowlisted provider token counters; no provider debug metadata."""

from pydantic import BaseModel, ConfigDict, Field


class HUSUsage(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, strict=True)
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
