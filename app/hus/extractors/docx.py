"""DOCX document extraction using python-docx."""

from __future__ import annotations

import io
import re
import unicodedata

import docx

from app.hus.urls import CrawlError


def _clean(text: str) -> str:
    text = text.replace("\u200b", "")
    return unicodedata.normalize("NFC", re.sub(r"[ \t]+", " ", text)).strip()


def _format_table(table) -> list[str]:
    rows_data: list[list[str]] = []
    for row in table.rows:
        cells = [_clean(cell.text).replace("|", "/") for cell in row.cells]
        # De-duplicate adjacent identical text caused by merged cells in docx
        deduped = []
        for c in cells:
            deduped.append(c)
        if any(deduped):
            rows_data.append(deduped)

    if not rows_data:
        return []

    col_count = max(len(r) for r in rows_data)
    padded = [r + [""] * (col_count - len(r)) for r in rows_data]
    lines = ["| " + " | ".join(padded[0]) + " |", "|" + " --- |" * col_count]
    for r in padded[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return lines


def extract_docx(raw: bytes) -> str:
    """Extract paragraphs and tables from DOCX bytes to markdown."""
    if not raw:
        raise CrawlError("empty docx file")

    try:
        doc = docx.Document(io.BytesIO(raw))
        lines: list[str] = []

        # Interleave paragraphs and tables
        for p in doc.paragraphs:
            text = _clean(p.text)
            if not text:
                continue
            if p.style and p.style.name.startswith("Heading"):
                try:
                    level = int(p.style.name.replace("Heading", "").strip())
                except ValueError:
                    level = 2
                lines.append(f"{'#' * min(max(level, 1), 6)} {text}")
            else:
                lines.append(text)

        for table in doc.tables:
            lines.extend(_format_table(table))

        content = "\n\n".join(lines).strip()
        if not content:
            raise CrawlError("docx contains no text")
        return content
    except Exception as exc:
        if isinstance(exc, CrawlError):
            raise
        raise CrawlError(f"docx extraction failed: {exc}") from exc
