"""Data models for HUS crawling, extraction, cleaning, and catalog indexing."""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


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


class HUSAttachment(BaseModel):
    attachment_id: str
    source_url: str
    file_type: str
    file_size: Optional[int] = None
    raw_path: Optional[str] = None
    status: DocumentStatus = DocumentStatus.ACTIVE


class HUSDocument(BaseModel):
    document_id: Optional[str] = None
    url: str
    title: str
    content: str
    content_hash: str
    fetched_at: str
    published_at: Optional[str] = None
    parent_url: Optional[str] = None
    document_type: DocumentType = DocumentType.GENERAL_INFO
    publisher: Publisher = Publisher.MIM
    academic_year: Optional[str] = None
    links: list[str] = Field(default_factory=list)
    attachments: list[HUSAttachment] = Field(default_factory=list)
    status: DocumentStatus = DocumentStatus.ACTIVE


class HUSChunk(BaseModel):
    chunk_id: str
    url: str
    title: str
    heading: Optional[str] = None
    text: str


class CrawlRecord(BaseModel):
    url: str
    content_hash: str
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    last_crawled: str
    status_code: int = 200
    document_id: Optional[str] = None


class AllowlistSourceConfig(BaseModel):
    host: str
    path_prefixes: list[str] = Field(default_factory=list)
    exclude_prefixes: list[str] = Field(default_factory=list)
    seeds: list[str] = Field(default_factory=list)
