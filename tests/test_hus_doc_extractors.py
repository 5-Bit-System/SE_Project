import io
import docx
import openpyxl
import pytest

from app.hus.extractors import extract_attachment
from app.hus.extractors.docx import extract_docx
from app.hus.extractors.excel import extract_excel
from app.hus.urls import CrawlError


def _create_mock_docx() -> bytes:
    doc = docx.Document()
    doc.add_heading("Quy chế đào tạo", level=1)
    doc.add_paragraph("Điều 1: Quy định chung về tín chỉ.")
    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "STT"
    table.rows[0].cells[1].text = "Môn học"
    table.rows[1].cells[0].text = "1"
    table.rows[1].cells[1].text = "Đại số"
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _create_mock_xlsx() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Học phần"
    ws.append(["Mã", "Tên", "Số tín"])
    ws.append(["MAT101", "Giải tích", 3])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_docx_extractor():
    raw_docx = _create_mock_docx()
    md = extract_docx(raw_docx)
    assert "# Quy chế đào tạo" in md
    assert "Điều 1: Quy định chung về tín chỉ." in md
    assert "| STT | Môn học |" in md
    assert "| 1 | Đại số |" in md


def test_excel_extractor():
    raw_xlsx = _create_mock_xlsx()
    md = extract_excel(raw_xlsx)
    assert "## Sheet: Học phần" in md
    assert "| Mã | Tên | Số tín |" in md
    assert "| MAT101 | Giải tích | 3 |" in md


def test_extractor_factory():
    raw_docx = _create_mock_docx()
    content, needs_ocr = extract_attachment(raw_docx, "docx")
    assert not needs_ocr
    assert "Quy chế" in content

    with pytest.raises(CrawlError, match="unsupported file format"):
        extract_attachment(b"123", "exe")
