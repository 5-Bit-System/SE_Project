"""Data models for HUS crawling, extraction, cleaning, and catalog indexing."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional
from urllib.parse import urlsplit

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


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


class MajorCategory(str, Enum):
    MATHEMATICS = "mathematics"
    MATHEMATICS_INFORMATICS = "mathematics_informatics"
    COMPUTER_SCIENCE = "computer_science"
    DATA_SCIENCE = "data_science"
    GENERAL = "general"


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
