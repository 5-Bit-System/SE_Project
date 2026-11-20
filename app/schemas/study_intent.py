"""Additive input/provenance contract; course metadata remains independent."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FormValues(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    workload: Literal["light", "moderate", "heavy"] | None = None
    orientation: Literal["theory", "practice", "research"] | None = None
    difficulty: Literal["easy", "moderate", "advanced"] | None = None
    course_type: Literal["required", "elective"] | None = None
    interest_topics: list[str] = Field(default_factory=list, max_length=20)
    target_credits: int | None = Field(default=None, ge=1, le=30)
    target_course_count: int | None = Field(default=None, ge=1, le=20)


class FormInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    values: FormValues = Field(default_factory=FormValues)
    explicit_fields: list[str] = Field(default_factory=list, max_length=7)

    @model_validator(mode="after")
    def valid_fields(self):
        if not set(self.explicit_fields) <= set(FormValues.model_fields):
            raise ValueError("Unknown explicit form field")
        return self


class FieldUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    operation: Literal["set", "add", "remove", "clear"] = "set"
    value: str | int | list[str] | None = None
    source: Literal["text_rule", "llm", "explicit_form"] = "text_rule"
    evidence: str = Field(default="", max_length=1000)


class ConstraintParseResult(BaseModel):
    updates: list[FieldUpdate] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


class IntentDiagnostics(BaseModel):
    status: Literal["ready", "needs_clarification"] = "ready"
    extraction_source: Literal["rules", "llm", "fallback"] = "rules"
    field_sources: dict[str, str] = Field(default_factory=dict)
    questions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StudyIntentState(BaseModel):
    """Internal state only; never accepted as trusted state in a request body."""
    values: dict = Field(default_factory=dict)
    field_sources: dict[str, str] = Field(default_factory=dict)
    excluded_topics: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    workload_policy: bool = False
