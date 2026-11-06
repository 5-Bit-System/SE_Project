"""Source-level geometry and human checks; presentation is never the raw table model."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QualityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceCell(QualityModel):
    cell_id: str
    row_id: str
    column_id: str
    row: int
    column: int
    raw_value: str | None
    display_value: str | None
    presence: Literal["present", "empty", "missing", "covered", "unresolved"]
    role: Literal["header", "data", "unknown"] = "unknown"
    header_scope: Literal["column", "row", "column_group", "row_group", "unknown", "none"] = (
        "unknown"
    )
    rowspan: int = 1
    colspan: int = 1
    covered_by: str | None = None
    locator: dict[str, Any]


class SourceTable(QualityModel):
    table_id: str
    locator: dict[str, Any]
    row_ids: list[str]
    column_ids: list[str]
    raw_rows: list[list[str | None]]
    cells: list[SourceCell]
    header_rows: list[int]
    header_status: Literal["explicit", "proposed", "unknown"]
    header_paths: dict[str, list[str]]
    display_markdown: str
    issues: list[str] = Field(default_factory=list)


class PageQuality(QualityModel):
    page_id: str
    page_number: int
    text_chars: int
    image_count: int
    graphic_count: int
    needs_ocr: bool
    reasons: list[str]
    raw_text: str
    display_text: str
    locator: dict[str, Any]


class SourceQuality(QualityModel):
    schema_version: Literal["1.0"] = "1.0"
    source_url: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    checksum_encoding: Literal["binary", "utf8-lf"]
    source_kind: Literal["pdf", "docx", "xlsx", "html", "unknown"]
    display_content: str
    display_content_sha256: str
    pages: list[PageQuality] = Field(default_factory=list)
    tables: list[SourceTable] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class SourceCheck(QualityModel):
    outcome: Literal["verified", "unresolved", "rejected"]
    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    locator: dict[str, Any]
    reviewer: str = Field(min_length=1)
    reviewed_at: str
    observed_value: str | None = None
    resolution: Literal["text_verified", "short_text_verified", "blank_verified", "ocr_pending"] = (
        "text_verified"
    )

    @field_validator("reviewer")
    @classmethod
    def named_reviewer(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Source check requires a reviewer")
        return value.strip()

    @field_validator("reviewed_at")
    @classmethod
    def aware_time(cls, value: str) -> str:
        if (
            "T" not in value
            or datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is None
        ):
            raise ValueError("Source check review time must include timezone")
        return value


class TableCheck(SourceCheck):
    confirmed_header_rows: list[int]


class QualityReview(QualityModel):
    report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_checks: dict[str, SourceCheck] = Field(default_factory=dict)
    table_checks: dict[str, TableCheck] = Field(default_factory=dict)
    cell_checks: dict[str, SourceCheck] = Field(default_factory=dict)
