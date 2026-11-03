"""Factory and distributor for document extractors by file extension."""

from __future__ import annotations

from app.hus.extractors.docx import extract_docx
from app.hus.extractors.excel import extract_excel
from app.hus.extractors.pdf import extract_pdf
from app.hus.urls import CrawlError


def extract_attachment(raw: bytes, file_type: str) -> tuple[str, bool]:
    """Distribute attachment bytes to appropriate parser.

    Returns:
        tuple (markdown_content, needs_ocr)
    """
    ft = file_type.lower().lstrip(".")
    if ft == "pdf":
        return extract_pdf(raw)
    if ft == "docx":
        return extract_docx(raw), False
    if ft == "xlsx":
        return extract_excel(raw), False
    raise CrawlError(f"unsupported file format: {file_type}")


def extract_content(raw_bytes: bytes, mime_or_ext: str) -> tuple[str, bool]:
    """Resolve a supported attachment extension or MIME type."""
    file_type = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    }.get(mime_or_ext.lower(), mime_or_ext)
    return extract_attachment(raw_bytes, file_type)
