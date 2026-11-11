"""Evidence-bearing contracts for the HUS question-answering branch."""

from typing import Any, Literal
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from urllib.parse import urlsplit

HUSMajor = Literal["mathematics", "mathematics_informatics", "computer_science", "data_science"]
HUSDataset = Literal["f1", "f2", "f3"]
# Source interpretation only; none of these states authorizes registration.
F2PrerequisiteStatus = Literal["unknown", "present", "conflict", "unresolved"]


class HUSQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=1000)
    major: HUSMajor
    dataset: Literal["auto", "f1", "f2", "f3"] = "auto"
    version: str | None = Field(default=None, min_length=1, max_length=80)
    course_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}\d{4}[A-Z]?$")
    field: Literal["introduction", "careers", "further_study", "objectives", "content",
                   "suggested_assessment", "official_assessment", "credits", "prerequisites",
                   "name", "hours", "course_info", "program_credits", "program_groups", "group_rules"] | None = None
    group_key: str | None = Field(default=None, max_length=32, pattern=r"^[IVX]+(?:\.[0-9]+)*$")
    program_variant: str | None = Field(default=None, min_length=1, max_length=80)
    allow_generated_reference: bool = Field(default=False, strict=True)

    @field_validator("course_code", mode="before")
    @classmethod
    def normalized_code(cls, value):
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("group_key", mode="before")
    @classmethod
    def normalized_group(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


class HUSCitation(BaseModel):
    citation_id: str
    dataset: HUSDataset
    label: str
    source_url: str | None = None
    quote: str
    locator: dict[str, Any]
    review_status: str
    content_origin: str
    metadata: dict[str, Any]
    evidence_kind: Literal["ai", "pdf", "web", "file", "unavailable"]
    display_label: str
    source_id: str | None = None
    open_url: str | None = None
    document_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    pdf_page: int | None = Field(default=None, ge=1, strict=True)
    pdf_pages: list[int] = Field(default_factory=list)
    availability: Literal["available", "unverified", "missing", "hash_mismatch", "invalid_file", "invalid_page", "unavailable"]
    availability_note: str | None = None
    media_type: str | None = None

    @model_validator(mode="after")
    def evidence_contract(self):
        if self.content_origin == "generated" or self.evidence_kind == "ai":
            if (self.evidence_kind != "ai" or self.content_origin != "generated"
                    or self.display_label != "kiến thức AI" or self.open_url is not None
                    or self.source_url is not None or self.document_sha256 is not None or self.pdf_page is not None):
                raise ValueError("Generated evidence must remain labeled AI, without document links")
        if self.open_url:
            parts = urlsplit(self.open_url)
            if self.evidence_kind in {"pdf", "file"}:
                if not re.fullmatch(r"/hus/sources/[0-9a-f]{64}(?:\?page=[1-9]\d*)?(?:#page=[1-9]\d*)?", self.open_url):
                    raise ValueError("File citation must use the trusted source resolver")
                if self.availability != "available" or not self.document_sha256:
                    raise ValueError("Unavailable file cannot have an open URL")
                expected = f"/hus/sources/{self.document_sha256}"
                if self.pdf_page is not None:
                    expected += f"?page={self.pdf_page}#page={self.pdf_page}"
                if self.open_url != expected:
                    raise ValueError("Resolver URL must match the document hash and physical page")
            elif self.evidence_kind == "web":
                if (parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password
                        or any(c.isspace() for c in self.open_url)
                        or self.open_url != self.source_url):
                    raise ValueError("Web citation must open its original HTTP(S) source")
            else:
                raise ValueError("This evidence kind cannot open a URL")
        if self.evidence_kind != "pdf" and (self.pdf_page is not None or self.pdf_pages):
            raise ValueError("Only PDF evidence can declare physical pages")
        if self.pdf_pages and (any(type(p) is not int or p < 1 for p in self.pdf_pages)
                               or self.pdf_page != self.pdf_pages[0] or self.pdf_pages != sorted(set(self.pdf_pages))):
            raise ValueError("Invalid PDF page span")
        return self


class HUSAnswer(BaseModel):
    reply: str
    status: Literal["answered", "no_information", "needs_clarification"]
    dataset: HUSDataset | None = None
    major: HUSMajor
    version: str | None = None
    citations: list[HUSCitation] = Field(default_factory=list)
    facts: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    release_id: str | None = None
    release_sha256: str | None = None
    generated_reference_allowed: bool = False


class HUSRetrievedChunk(BaseModel):
    rank: int = Field(ge=1)
    chunk_id: str
    dataset: HUSDataset
    major: HUSMajor
    version: str
    field: str | None = None
    course_code: str | None = None
    course_name: str | None = None
    title: str | None = None
    body: str
    score: float
    matched_terms: list[str] = Field(default_factory=list)
    passed_support_gate: bool = False
    review_status: str | None = None
    content_origin: str | None = None
    citation: HUSCitation | None = None


class HUSRetrievalBundle(BaseModel):
    question: str
    normalized_question: str
    major: HUSMajor
    version: str | None = None
    dataset: HUSDataset | None = None
    field: str | None = None
    intent_source: Literal["explicit", "rule", "semantic", "broad_fallback", "none"]
    intent_confidence: float = 0.0
    resolved_course_code: str | None = None
    resolved_courses: list[dict[str, str]] = Field(default_factory=list)
    top_k: int
    top_k_chunks: list[HUSRetrievedChunk] = Field(default_factory=list)
    structured_data: dict[str, Any] = Field(default_factory=dict)
    release_id: str | None = None
    release_sha256: str | None = None


class HUSChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    reply: str = Field(max_length=20000)
    citations: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    generation_mode: str | None = Field(default=None, max_length=64)
    timestamp: str | None = Field(default=None, max_length=64)


class HUSChatHistoryAppend(BaseModel):
    major: str = Field(min_length=1, max_length=64)
    role: Literal["user", "assistant"]
    reply: str = Field(max_length=20000)
    citations: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    generation_mode: str | None = Field(default=None, max_length=64)
    timestamp: str | None = Field(default=None, max_length=64)


class HUSChatHistoryResponse(BaseModel):
    account_id: str | None = Field(default=None, max_length=128)
    major: str = Field(min_length=1, max_length=64)
    messages: list[HUSChatMessage] = Field(default_factory=list)


