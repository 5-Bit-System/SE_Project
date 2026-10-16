"""PDF text and table extraction using pdfplumber."""

from __future__ import annotations

import io
import re
import unicodedata

import pdfplumber

from app.hus.urls import CrawlError


def _clean(text: str) -> str:
    text = text.replace("\u200b", "")
    return unicodedata.normalize("NFC", re.sub(r"[ \t]+", " ", text)).strip()


def _format_table(table: list[list[str | None]]) -> list[str]:
    cleaned_rows = []
    for row in table:
        cells = [_clean(c or "").replace("|", "/") for c in row]
        if any(cells):
            cleaned_rows.append(cells)
    if not cleaned_rows:
        return []
    col_count = max(len(r) for r in cleaned_rows)
    padded_rows = [r + [""] * (col_count - len(r)) for r in cleaned_rows]
    lines = ["| " + " | ".join(padded_rows[0]) + " |", "|" + " --- |" * col_count]
    for r in padded_rows[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return lines


def extract_pdf(raw: bytes) -> tuple[str, bool]:
    """Extract text and tables from PDF bytes.

    Returns:
        tuple (markdown_content, needs_ocr)
    """
    if not raw:
        raise CrawlError("empty pdf file")

    pages_text: list[str] = []
    total_chars = 0

    try:
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            page_count = len(pdf.pages)
            if page_count == 0:
                raise CrawlError("pdf has 0 pages")

            for idx, page in enumerate(pdf.pages, start=1):
                page_lines: list[str] = [f"<!-- Page {idx} -->"]
                # Extract tables first
                tables = page.extract_tables() or []
                for table in tables:
                    page_lines.extend(_format_table(table))

                # Extract plain text
                text = page.extract_text() or ""
                cleaned_text = _clean(text)
                if cleaned_text:
                    total_chars += len(cleaned_text)
                    page_lines.append(cleaned_text)

                pages_text.append("\n".join(page_lines))

            needs_ocr = (total_chars / page_count) < 50
            content = "\n\n".join(pages_text).strip()
            return content, needs_ocr
    except Exception as exc:
        if isinstance(exc, CrawlError):
            raise
        raise CrawlError(f"pdf extraction failed: {exc}") from exc
