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
    if ft in ("docx", "doc"):
        return extract_docx(raw), False
    if ft in ("xlsx", "xls"):
        return extract_excel(raw), False
    raise CrawlError(f"unsupported file format: {file_type}")
