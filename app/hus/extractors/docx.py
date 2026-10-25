"""DOCX document extraction using python-docx."""

from __future__ import annotations

import io

import docx
from docx.table import Table

from app.hus.cleaning import clean_text, format_markdown_table
from app.hus.urls import CrawlError


def _format_table(table: Table) -> list[str]:
    rows_data: list[list[str]] = [[cell.text for cell in row.cells] for row in table.rows]
    return format_markdown_table(rows_data)


def extract_docx(raw: bytes) -> str:
    """Extract paragraphs and tables from DOCX bytes to markdown."""
    if not raw:
        raise CrawlError("empty docx file")

    try:
        doc = docx.Document(io.BytesIO(raw))
        lines: list[str] = []

        for block in doc.iter_inner_content():
            if isinstance(block, Table):
                if table_lines := _format_table(block):
                    lines.append("\n".join(table_lines))
                continue
            p = block
            text = clean_text(p.text)
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

        content = "\n\n".join(lines).strip()
        if not content:
            raise CrawlError("docx contains no text")
        return content
    except Exception as exc:
        if isinstance(exc, CrawlError):
            raise
        raise CrawlError(f"docx extraction failed: {exc}") from exc
