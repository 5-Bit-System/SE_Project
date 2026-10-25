"""Data models for HUS crawling, extraction, cleaning, and catalog indexing."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional
from urllib.parse import urlsplit

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator


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
        default=MajorCategory.GENERAL,
        description="Ngành học áp dụng của tài liệu (hoặc 'general' nếu là quy định chung toàn trường)",
    )
    links: list[str] = Field(default_factory=list)
    attachments: list[HUSAttachment] = Field(default_factory=list)
    status: DocumentStatus = DocumentStatus.ACTIVE
    raw_source: Optional[RawSourceReference] = None

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
