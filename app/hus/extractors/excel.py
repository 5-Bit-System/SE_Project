"""XLSX spreadsheet extraction using openpyxl."""

from __future__ import annotations

import io
import re
import unicodedata

import openpyxl

from app.hus.urls import CrawlError


def _clean(text: str) -> str:
    text = text.replace("\u200b", "")
    return unicodedata.normalize("NFC", re.sub(r"[ \t]+", " ", text)).strip()


def extract_excel(raw: bytes) -> str:
    """Extract sheets and table data from XLSX bytes to markdown tables."""
    if not raw:
        raise CrawlError("empty xlsx file")

    try:
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        sections: list[str] = []

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows: list[list[str]] = []
            for row in ws.iter_rows(values_only=True):
                cells = [_clean(str(c)) if c is not None else "" for c in row]
                # Drop rows where all cells are empty
                if any(cells):
                    rows.append(cells)

            if not rows:
                continue

            sheet_lines = [f"## Sheet: {sheet_name}"]
            col_count = max(len(r) for r in rows)
            padded = [r + [""] * (col_count - len(r)) for r in rows]

            sheet_lines.append("| " + " | ".join(padded[0]) + " |")
            sheet_lines.append("|" + " --- |" * col_count)
            for r in padded[1:]:
                sheet_lines.append("| " + " | ".join(r) + " |")

            sections.append("\n".join(sheet_lines))

        content = "\n\n".join(sections).strip()
        if not content:
            raise CrawlError("xlsx contains no readable tabular data")
        return content
    except Exception as exc:
        if isinstance(exc, CrawlError):
            raise
        raise CrawlError(f"excel extraction failed: {exc}") from exc
