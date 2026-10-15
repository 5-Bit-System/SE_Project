import io
import pypdfium2
import pytest

from app.hus.extractors.pdf import extract_pdf
from app.hus.urls import CrawlError


def _create_mock_pdf() -> bytes:
    pdf = pypdfium2.PdfDocument.new()
    pdf.new_page(200, 200)
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


def test_extract_pdf_empty_error():
    with pytest.raises(CrawlError, match="empty pdf file"):
        extract_pdf(b"")


def test_extract_pdf_scanned_marks_needs_ocr():
    raw_pdf = _create_mock_pdf()
    content, needs_ocr = extract_pdf(raw_pdf)
    assert "<!-- Page 1 -->" in content
    assert needs_ocr is True
