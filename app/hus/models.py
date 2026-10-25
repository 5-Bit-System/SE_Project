"""Data models for HUS crawling, extraction, cleaning, and catalog indexing."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional
from urllib.parse import urlsplit

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator
from app.hus.quality_models import QualityReview, SourceQuality


def _http_url(value: str) -> str:
    value = value.strip()
    parts = urlsplit(value)
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("must contain a valid port") from exc
    if (
        any(char.isspace() for char in value)
        or parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or port not in (None, 80, 443)
    ):
        raise ValueError("must be an absolute HTTP(S) URL")
    return value


def _non_empty(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty")
    return value.strip()


def _iso_datetime(value: str) -> str:
    if "T" not in value:
        raise ValueError("must be an ISO 8601 datetime")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("must be an ISO 8601 datetime") from exc
    return value


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class DocumentType(str, Enum):
    REGULATION = "regulation"
    ANNOUNCEMENT = "announcement"
    CURRICULUM = "curriculum"
    FORM = "form"
    GENERAL_INFO = "general_info"


class Publisher(str, Enum):
    HUS = "HUS"
    MIM = "MIM"
    TUYENSINH = "TUYENSINH"


class DocumentStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    PENDING_OCR = "pending_ocr"
    ARCHIVED = "archived"


class ReviewDecision(BaseModel):
    """A review of the whole document, bound to its content and original source.

    Unknown validity is usable only for descriptive information, never a current rule.
    Older include decisions without a timestamp must be reviewed again before export.
    """

    model_config = ConfigDict(extra="forbid", strict=True)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_url: str | None = None
    review_scope: Literal["document"] = "document"
    status: Literal["include", "needs_review", "pending_ocr", "exclude"]
    reason: str = Field(min_length=1)
    reviewer: str | None = None
    reviewed_at: str | None = None
    evidence_locator: str | None = None
    reviewed_source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_checksum_encoding: Literal["binary", "utf8-lf"] = "binary"
    validity_status: Literal["unknown", "historical", "current_verified", "future_draft"] = "unknown"
    usage_scope: Literal["descriptive", "historical", "current"] = "descriptive"
    validity_evidence_locator: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    source_quality: QualityReview | None = None

    @property
    def review_status(self) -> str:
        return self.status

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, value: str) -> str:
        return _non_empty(value)

    @field_validator("source_url")
    @classmethod
    def review_source_url(cls, value: str | None) -> str | None:
        return _http_url(value) if value is not None else None

    @field_validator("reviewed_at")
    @classmethod
    def aware_review_time(cls, value: str | None) -> str | None:
        if value is not None:
            _iso_datetime(value)
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError("reviewed_at must include timezone")
        return value

    @field_validator("effective_from", "effective_to")
    @classmethod
    def effective_date(cls, value: str | None) -> str | None:
        if value is not None:
            return date.fromisoformat(value).isoformat()
        return value

    @model_validator(mode="after")
    def validate_validity(self) -> "ReviewDecision":
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValueError("effective_to precedes effective_from")
        if self.validity_status != "unknown" and not (self.validity_evidence_locator or "").strip():
            raise ValueError("Known validity needs its own source evidence")
        if self.usage_scope == "current" and self.validity_status != "current_verified":
            raise ValueError("Current usage requires current_verified validity")
        if self.usage_scope == "historical" and self.validity_status != "historical":
            raise ValueError("Historical usage requires historical validity")
        return self


class MajorCategory(str, Enum):
    MATHEMATICS = "mathematics"
    MATHEMATICS_INFORMATICS = "mathematics_informatics"
    COMPUTER_SCIENCE = "computer_science"
    DATA_SCIENCE = "data_science"
    GENERAL = "general"
    UNKNOWN = "unknown"
    OUT_OF_SCOPE = "out_of_scope"


class MetadataEvidence(_StrictModel):
    field: Literal["title", "source_url", "content_markdown", "parent_url"]
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    quote: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_span(self) -> "MetadataEvidence":
        if self.end <= self.start:
            raise ValueError("Evidence span must be non-empty")
        if not self.quote.strip():
            raise ValueError("Evidence quote must contain text")
        return self


class MetadataField(_StrictModel):
    proposed: str = "unknown"
    proposal_method: str = "unknown"
    proposal_evidence: list[MetadataEvidence] = Field(default_factory=list)
    verified: str = "unknown"
    evidence: list[MetadataEvidence] = Field(default_factory=list)
    reviewer: Optional[str] = None
    reviewed_at: Optional[str] = None

    @field_validator("proposed", "verified", "proposal_method")
    @classmethod
    def non_blank_value(cls, value: str) -> str:
        return _non_empty(value)

    @field_validator("reviewed_at")
    @classmethod
    def aware_metadata_review(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            _iso_datetime(value)
            if datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is None:
                raise ValueError("Metadata review time must include timezone")
        return value

    @model_validator(mode="after")
    def verified_requires_evidence(self) -> "MetadataField":
        if self.verified != "unknown" and (
            not self.evidence or not (self.reviewer or "").strip() or not self.reviewed_at
        ):
            raise ValueError("Verified metadata needs evidence, reviewer and review time")
        if self.verified != "unknown" and all(item.field == "parent_url" for item in self.evidence):
            raise ValueError("Verified metadata needs evidence from the document itself")
        return self


class ApplicabilityMetadata(_StrictModel):
    source_url: Optional[str] = None
    content_hash: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    major: MetadataField = Field(default_factory=MetadataField)
    education_level: MetadataField = Field(default_factory=MetadataField)
    program: MetadataField = Field(default_factory=MetadataField)
    program_variant: MetadataField = Field(default_factory=MetadataField)
    admission_cohort: MetadataField = Field(default_factory=MetadataField)
    academic_year: MetadataField = Field(default_factory=MetadataField)
    validity_status: MetadataField = Field(default_factory=MetadataField)
    effective_from: MetadataField = Field(default_factory=MetadataField)
    effective_to: MetadataField = Field(default_factory=MetadataField)

    @model_validator(mode="after")
    def metadata_vocabulary(self) -> "ApplicabilityMetadata":
        vocabularies = {
            "major": {item.value for item in MajorCategory},
            "education_level": {"unknown", "undergraduate", "master", "doctoral", "shared"},
            "program_variant": {"unknown", "standard", "high_quality", "talent", "advanced"},
            "validity_status": {"unknown", "historical", "current_verified", "future_draft"},
        }
        for name, values in vocabularies.items():
            field = getattr(self, name)
            if field.proposed not in values or field.verified not in values:
                raise ValueError(f"Invalid metadata vocabulary: {name}")
        for name in ("effective_from", "effective_to"):
            for value in (getattr(self, name).proposed, getattr(self, name).verified):
                if value != "unknown":
                    date.fromisoformat(value)
        for status in ("proposed", "verified"):
            start, end = getattr(self.effective_from, status), getattr(self.effective_to, status)
            if start != "unknown" and end != "unknown" and date.fromisoformat(start) > date.fromisoformat(end):
                raise ValueError("Applicability effective_to precedes effective_from")
        return self


class RawSourceReference(_StrictModel):
    capture_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    document_id: str = Field(pattern=r"^[0-9a-f]{16}$")
    source_url: str
    raw_path: str
    raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(ge=0)
    file_type: str
    content_type: Optional[str] = None
    observed_at: str
    fetched_at: Optional[str] = None
    version_status: Literal["captured", "unverified"] = "unverified"

    _validate_url = field_validator("source_url")(_http_url)
    @field_validator("observed_at", "fetched_at")
    @classmethod
    def aware_capture_time(cls, value: str | None) -> str | None:
        if value is not None:
            _iso_datetime(value)
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError("Capture timestamps must include timezone")
        return value


class HUSAttachment(_StrictModel):
    attachment_id: str
    source_url: str
    file_type: str
    file_size: Optional[int] = Field(default=None, ge=0)
    raw_path: Optional[str] = None
    status: DocumentStatus = DocumentStatus.ACTIVE

    _validate_url = field_validator("source_url")(_http_url)
    _validate_strings = field_validator("attachment_id", "file_type")(_non_empty)


class HUSDocument(_StrictModel):
    document_id: Optional[str] = None
    source_url: str = Field(validation_alias=AliasChoices("source_url", "url"))
    title: str
    content_markdown: str = Field(validation_alias=AliasChoices("content_markdown", "content"))
    content_hash: str
    fetched_at: str
    published_at: Optional[str] = None
    parent_url: Optional[str] = None
    document_type: DocumentType = DocumentType.GENERAL_INFO
    publisher: Publisher = Publisher.MIM
    academic_year: Optional[str] = None
    major: MajorCategory = Field(
        default=MajorCategory.UNKNOWN,
        description="Unverified crawler proposal; use applicability.major.verified for filtering",
    )
    applicability: ApplicabilityMetadata = Field(default_factory=ApplicabilityMetadata)
    links: list[str] = Field(default_factory=list)
    attachments: list[HUSAttachment] = Field(default_factory=list)
    status: DocumentStatus = DocumentStatus.ACTIVE
    raw_source: Optional[RawSourceReference] = None
    source_quality: Optional[SourceQuality] = None

    _validate_url = field_validator("source_url")(_http_url)
    _validate_strings = field_validator("title", "content_markdown", "content_hash")(_non_empty)
    _validate_fetched_at = field_validator("fetched_at")(_iso_datetime)

    @field_validator("parent_url")
    @classmethod
    def validate_parent_url(cls, value: Optional[str]) -> Optional[str]:
        return _http_url(value) if value is not None else value

    @field_validator("links")
    @classmethod
    def validate_links(cls, values: list[str]) -> list[str]:
        return [_http_url(value) for value in values]

    @field_validator("published_at")
    @classmethod
    def validate_published_at(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            date.fromisoformat(value)
        except ValueError:
            _iso_datetime(value)
        return value

    @property
    def url(self) -> str:
        return self.source_url

    @model_validator(mode="after")
    def validate_applicability(self) -> "HUSDocument":
        if self.applicability != ApplicabilityMetadata():
            from app.hus.metadata import validate_metadata

            self.applicability = validate_metadata(self, self.applicability)
        return self

    @property
    def content(self) -> str:
        return self.content_markdown


class HUSChunk(_StrictModel):
    chunk_id: str
    url: str
    title: str
    heading: Optional[str] = None
    text: str
    review_status: Literal["include"]
    review: ReviewDecision
    review_as_of: Optional[str] = None
    applicability: ApplicabilityMetadata
    source_quality_sha256: Optional[str] = None
    source_unit_ids: list[str] = Field(default_factory=list)


class CrawlRecord(_StrictModel):
    url: str
    content_hash: str
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    last_crawled: str
    status_code: int = Field(default=200, ge=100, le=599)
    document_id: Optional[str] = None

    _validate_url = field_validator("url")(_http_url)
    _validate_hash = field_validator("content_hash")(_non_empty)
    _validate_last_crawled = field_validator("last_crawled")(_iso_datetime)


class AllowlistSourceConfig(_StrictModel):
    host: str
    path_prefixes: list[str] = Field(default_factory=list)
    exclude_prefixes: list[str] = Field(default_factory=list)
    seeds: list[str] = Field(default_factory=list)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        host = value.strip().lower()
        if not host or urlsplit(f"//{host}").hostname != host or ":" in host or "/" in host:
            raise ValueError("host must be a bare hostname")
        return host

    @field_validator("path_prefixes", "exclude_prefixes")
    @classmethod
    def validate_prefixes(cls, values: list[str]) -> list[str]:
        if any(not value.startswith("/") for value in values):
            raise ValueError("path prefixes must start with /")
        return values

    @field_validator("seeds")
    @classmethod
    def validate_seeds(cls, values: list[str]) -> list[str]:
        return [_http_url(value) for value in values]
