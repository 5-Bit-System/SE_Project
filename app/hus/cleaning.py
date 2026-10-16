"""Text normalization, cleaning utilities, table formatting, and document type inference."""

from __future__ import annotations

import re
import unicodedata

from app.hus.models import DocumentType


def clean_text(text: str) -> str:
    """Normalize Unicode to NFC, strip zero-width characters, and collapse spaces."""
    if not text:
        return ""
    for char in ("\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"):
        text = text.replace(char, "")
    return unicodedata.normalize("NFC", re.sub(r"[ \t]+", " ", text)).strip()


def infer_document_type(title: str, content: str = "") -> DocumentType:
    """Infer DocumentType using keyword rules on title and content."""
    for text in (title.lower(), content[:300].lower()):
        if any(k in text for k in ("đơn", "biểu mẫu", "phiếu đăng ký")):
            return DocumentType.FORM
        if any(k in text for k in ("quy chế", "quy định", "hướng dẫn thực hiện", "điều lệ")):
            return DocumentType.REGULATION
        if any(k in text for k in ("thông báo", "kế hoạch", "lịch thi", "lịch học", "thời khóa biểu")):
            return DocumentType.ANNOUNCEMENT
        if any(k in text for k in ("chương trình đào tạo", "khung chương trình", "chuẩn đầu ra", "học phần")):
            return DocumentType.CURRICULUM
    return DocumentType.GENERAL_INFO


def format_markdown_table(rows: list[list[str]]) -> list[str]:
    """Format 2D table grid to standard Markdown table with column alignment."""
    if not rows:
        return []

    cleaned_rows = []
    for row in rows:
        cells = [clean_text(str(c)).replace("|", "/") for c in row]
        if any(cells):
            cleaned_rows.append(cells)

    if not cleaned_rows:
        return []

    col_count = max(len(r) for r in cleaned_rows)
    padded = [r + [""] * (col_count - len(r)) for r in cleaned_rows]

    lines = ["| " + " | ".join(padded[0]) + " |", "|" + " --- |" * col_count]
    for r in padded[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return lines


def extract_document(raw: bytes, url: str, fetched_at: str):
    from app.hus.extractors.html import extract_html

    doc, _ = extract_html(raw, url, fetched_at)
    doc.document_type = infer_document_type(doc.title, doc.content)
    return doc
