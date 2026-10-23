"""Tests for table formatting, cell cleaning, extractor table generation, and table repair."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock

import docx
import openpyxl
import pytest

from app.hus.cleaning import clean_table_cell, format_markdown_table
from app.hus.extractors.docx import extract_docx
from app.hus.extractors.excel import extract_excel
from app.hus.extractors.pdf import _format_table as format_pdf_table
from tools.repair_markdown_tables import (
    repair_all,
    repair_markdown_text,
    verify_no_broken_tables,
)


def test_clean_table_cell_variations():
    assert clean_table_cell(None) == ""
    assert clean_table_cell("") == ""
    assert clean_table_cell("hello | world") == "hello / world"
    assert clean_table_cell("line 1\r\nline 2") == "line 1<br>line 2"
    assert clean_table_cell("line 1\nline 2\nline 3") == "line 1<br>line 2<br>line 3"
    assert clean_table_cell("  <br>  line 1  <br>  ") == "line 1"
    assert clean_table_cell("line 1 <br/> line 2") == "line 1<br>line 2"
    assert clean_table_cell("<br><br>leading and trailing<br><br>") == "leading and trailing"
    assert clean_table_cell(42) == "42"


def test_format_markdown_table_single_line_guarantee():
    matrix = [
        ["Header 1\nLine 2", "Header 2\r\nLine B"],
        ["Cell 1\nwith\nmultiple\nlines", "Cell 2 | with pipe"],
        ["Normal 1", "Normal 2"],
    ]
    lines = format_markdown_table(matrix)
    assert len(lines) == 4
    for line in lines:
        assert "\n" not in line
        assert "\r" not in line
        assert line.startswith("|")
        assert line.endswith("|")

    assert lines[0] == "| Header 1<br>Line 2 | Header 2<br>Line B |"
    assert lines[1] == "| --- | --- |"
    assert lines[2] == "| Cell 1<br>with<br>multiple<br>lines | Cell 2 / with pipe |"
    assert lines[3] == "| Normal 1 | Normal 2 |"


def test_repair_markdown_text():
    broken = (
        "# Document Title\n\n"
        "Some introductory text.\n\n"
        "| STT | Mã\n"
        "học phần | Học phần | Số\n"
        "tín chỉ |\n"
        "| --- | --- | --- | ---\n"
        "|\n"
        "| 1 | MAT1001\n"
        "Toán 1 | Giải tích 1 | 3 |\n"
        "| 2 | MAT1002 | Đại số tuyến tính | 3 |\n\n"
        "Trailing notes.\n"
    )

    repaired, count = repair_markdown_text(broken)
    assert count == 3  # The header row, separator row, and first data row were broken

    for line in repaired.splitlines():
        s = line.strip()
        if s.startswith("|"):
            assert s.endswith("|")
            assert not (s.startswith("|") and not s.endswith("|"))

    assert "| STT | Mã<br>học phần | Học phần | Số<br>tín chỉ |" in repaired
    assert "| 1 | MAT1001<br>Toán 1 | Giải tích 1 | 3 |" in repaired
    assert "| 2 | MAT1002 | Đại số tuyến tính | 3 |" in repaired


def test_repair_markdown_text_cleans_dividers():
    broken = (
        "| Col 1 |\n"
        "Col 2 |\n"
        "| Col A <br>|\n"
        "|<br> Col B |\n"
    )
    repaired, count = repair_markdown_text(broken)
    for line in repaired.splitlines():
        assert "<br>|" not in line
        assert "|<br>" not in line


def test_docx_extractor_table_with_multiline_cells():
    doc = docx.Document()
    doc.add_heading("Khung chương trình", level=1)
    table = doc.add_table(rows=2, cols=2)

    # Cell with multiple paragraphs (which docx renders as \n)
    table.rows[0].cells[0].text = "Header 1"
    table.rows[0].cells[1].text = "Header 2"

    p0 = table.rows[1].cells[0].paragraphs[0]
    p0.text = "Para 1"
    p1 = table.rows[1].cells[0].add_paragraph("Para 2")
    p1.text = "Para 2"

    table.rows[1].cells[1].text = "Single para"

    bio = io.BytesIO()
    doc.save(bio)
    raw = bio.getvalue()

    md = extract_docx(raw)
    assert md
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|"):
            assert s.endswith("|")
            assert "\n" not in s

    assert "| Para 1<br>Para 2 | Single para |" in md


def test_excel_extractor_table_with_multiline_cells():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ChuongTrinh"
    ws.append(["Mã HP", "Tên HP\n(Ghi chú)", "Số TC"])
    ws.append(["MAT1001", "Toán rời rạc\n(Toán - Tin)", 3])

    bio = io.BytesIO()
    wb.save(bio)
    raw = bio.getvalue()

    md = extract_excel(raw)
    assert md
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|"):
            assert s.endswith("|")
            assert "\n" not in s

    assert "| Mã HP | Tên HP<br>(Ghi chú) | Số TC |" in md
    assert "| MAT1001 | Toán rời rạc<br>(Toán - Tin) | 3 |" in md


def test_pdf_format_table_with_multiline_cells():
    table_data = [
        ["STT", "Học phần\n(Ngành KHDL)", "Số TC"],
        ["1", "Học máy\nvà ứng dụng", "3"],
        [None, None, None],
    ]
    lines = format_pdf_table(table_data)
    assert len(lines) == 3
    for line in lines:
        assert "\n" not in line
        assert line.startswith("|")
        assert line.endswith("|")

    assert lines[0] == "| STT | Học phần<br>(Ngành KHDL) | Số TC |"
    assert lines[2] == "| 1 | Học máy<br>và ứng dụng | 3 |"


def test_repair_all_and_verify(tmp_path: Path):
    doc_dir = tmp_path / "processed" / "documents" / "cs"
    doc_dir.mkdir(parents=True, exist_ok=True)
    file_path = doc_dir / "broken_doc--12345678.md"

    file_path.write_text(
        "| Header 1 | Header 2\n"
        "Subtitle |\n"
        "| --- | --- |\n"
        "| Value 1\n"
        "Line 2 | Value 2 |\n",
        encoding="utf-8",
    )

    # Initial check fails
    assert verify_no_broken_tables(tmp_path) == 1

    # Repair
    count, rows, paths = repair_all(tmp_path)
    assert count == 1
    assert rows == 2
    assert len(paths) == 1

    # Post-repair verify passes
    assert verify_no_broken_tables(tmp_path) == 0
