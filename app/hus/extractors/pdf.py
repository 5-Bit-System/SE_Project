"""PDF text and table extraction using pdfplumber."""

from __future__ import annotations

import io

import pdfplumber

from app.hus.cleaning import clean_text, format_markdown_table
from app.hus.urls import CrawlError


def _format_table(table: list[list[str | None]]) -> list[str]:
    return format_markdown_table(table)


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
                text = clean_text(page.extract_text() or "")
                total_chars += len(text)
                tables = [
                    (table, rows)
                    for table in sorted(page.find_tables(), key=lambda table: table.bbox[1])
                    if (rows := table.extract()) and max(map(len, rows)) > 1
                ]
                if not tables and text:
                    page_lines.append(text)
                cursor = 0
                for table, rows in tables:
                    top, bottom = table.bbox[1], table.bbox[3]
                    if cursor < top:
                        before = clean_text(page.crop((0, cursor, page.width, top)).extract_text() or "")
                        if before:
                            page_lines.append(before)
                    if page_lines[-1].strip():
                        page_lines.append("")
                    page_lines.extend(_format_table(rows))
                    cursor = max(cursor, bottom)
                if tables and cursor < page.height:
                    after = clean_text(page.crop((0, cursor, page.width, page.height)).extract_text() or "")
                    if after:
                        page_lines.append(after)

                pages_text.append("\n".join(page_lines))

            needs_ocr = (total_chars / page_count) < 50
            content = "\n\n".join(pages_text).strip()
            return content, needs_ocr
    except Exception as exc:
        if isinstance(exc, CrawlError):
            raise
        raise CrawlError(f"pdf extraction failed: {exc}") from exc
