from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FieldEvidenceItem(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    source_ref: str
    locator: str
    method: Literal["transcription", "curated_mapping", "survey"]
    status: Literal["verified", "draft_unverified", "conflict"]
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    rubric_ref: str | None = None
    note: str | None = None

    @field_validator("source_ref", "locator")
    @classmethod
    def require_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Evidence source_ref and locator must not be blank")
        return value

    @model_validator(mode="after")
    def validate_review(self) -> "FieldEvidenceItem":
        if self.reviewed_at is not None:
            reviewed = datetime.fromisoformat(self.reviewed_at.replace("Z", "+00:00"))
            if reviewed.tzinfo is None or reviewed.utcoffset() is None:
                raise ValueError("reviewed_at must include timezone")
        if self.status == "verified" and (
            not self.reviewed_by or not self.reviewed_by.strip() or not self.reviewed_at
        ):
            raise ValueError("Verified evidence requires reviewer and aware review time")
        if self.method == "curated_mapping" and not (self.rubric_ref or "").strip():
            raise ValueError("curated_mapping requires versioned rubric_ref")
        return self


class Hours(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    lecture: int | None = Field(default=None, ge=0)
    practice: int | None = Field(default=None, ge=0)
    self_study: int | None = Field(default=None, ge=0)


class CourseMetadata(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    code: str
    name: str
    name_en: str | None = None
    credits: int = Field(gt=0)
    block: Literal["general", "field", "discipline", "group", "major"]
    requirement_type: Literal["required", "elective", "required_excluded", "graduation"]
    counted_in_total: bool
    hours: Hours | None = None
    instruction_language: str | None = None
    prerequisites: list[list[str]]
    prerequisites_raw: str | None = None
    prerequisite_status: Literal[
        "verified",
        "draft_unverified",
        "unresolved_external",
        "conflict",
        "unknown",
    ]
    prerequisite_variants: list[list[list[str]]] = Field(default_factory=list)
    external_prerequisite_codes: list[str] = Field(default_factory=list)
    choice_group_ids: list[str] = Field(default_factory=list)
    graduation_path_ids: list[str] = Field(default_factory=list)
    source_page: int | None = None
    source_rows: list[int] = Field(default_factory=list)
    year: int | None = Field(default=None, ge=1)
    suggested_term: int | None = Field(default=None, ge=1)
    topics: list[str] | None = None
    orientation: Literal["theory", "practice", "research"] | None = None
    difficulty: Literal["easy", "moderate", "advanced"] | None = None
    workload: Literal["light", "moderate", "heavy"] | None = None
    description: str | None = None
    career_paths: list[str] | None = None
    source_status: Literal["verified", "draft_unverified"]
    offering_status: Literal["unknown"]
    field_evidence: dict[str, list[FieldEvidenceItem]]

    @field_validator("code", "name")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Course code/name must not be blank")
        return value.strip()

    @model_validator(mode="after")
    def validate_evidence(self) -> "CourseMetadata":
        if self.code != self.code.upper():
            raise ValueError("Course code must be normalized uppercase")
        if self.requirement_type == "required_excluded" and self.counted_in_total:
            raise ValueError("required_excluded cannot count toward total")
        fields = (
            "code",
            "name",
            "name_en",
            "credits",
            "block",
            "requirement_type",
            "counted_in_total",
            "hours",
            "instruction_language",
            "prerequisites",
            "choice_group_ids",
            "graduation_path_ids",
            "source_page",
            "year",
            "suggested_term",
            "topics",
            "orientation",
            "difficulty",
            "workload",
            "description",
            "career_paths",
        )
        advisory = {
            "topics",
            "orientation",
            "difficulty",
            "workload",
            "description",
            "career_paths",
        }
        for name in fields:
            if getattr(self, name) is None:
                continue
            evidence = self.field_evidence.get(name, [])
            if not evidence:
                raise ValueError(f"Non-null {name} requires field_evidence")
            if name in advisory and any(e.status == "conflict" for e in evidence):
                raise ValueError(f"Conflicting advisory {name} must remain null")
            if name in {"difficulty", "workload"} and any(
                not (e.rubric_ref or "").strip() for e in evidence
            ):
                raise ValueError(f"{name} requires versioned rubric_ref")
        if self.prerequisite_status == "verified" and not any(
            e.status == "verified" for e in self.field_evidence.get("prerequisites", [])
        ):
            raise ValueError("Verified prerequisites require verified evidence")
        if self.source_status == "verified" and any(
            not any(e.status == "verified" for e in self.field_evidence.get(name, []))
            for name in ("code", "name", "credits", "block")
        ):
            raise ValueError("Verified source requires verified core field evidence")
        variants = {tuple(sorted(tuple(sorted(c)) for c in v)) for v in self.prerequisite_variants}
        conflict_evidence = any(
            e.status == "conflict" for e in self.field_evidence.get("prerequisites", [])
        )
        if (conflict_evidence or len(variants) > 1) and self.prerequisite_status != "conflict":
            raise ValueError("Conflicting prerequisite evidence/variants require conflict status")
        if self.prerequisite_status == "conflict":
            if len(variants) < 2 or len(self.field_evidence.get("prerequisites", [])) < 2:
                raise ValueError("Conflicting prerequisites require distinct variants and evidence")
        return self


class CourseEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    metadata_schema_version: str
    vocabulary_version: str
    program_id: str
    catalog_revision: str
    courses: list[CourseMetadata]


__all__ = [
    "CourseEnvelope",
    "CourseMetadata",
    "FieldEvidenceItem",
    "Hours",
]
