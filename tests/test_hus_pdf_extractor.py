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


def test_extract_pdf_text_table_and_approved_ocr_threshold(monkeypatch):
    class Page:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

        def extract_tables(self):
            return [[ ["Mã", "Tên"], ["MAT101", "Giải tích"] ]]

    class PDF:
        def __init__(self, text):
            self.pages = [Page(text)]

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

    monkeypatch.setattr("app.hus.extractors.pdf.pdfplumber.open", lambda _: PDF("A" * 45))
    content, needs_ocr = extract_pdf(b"mock")
    assert "<!-- Page 1 -->" in content
    assert "| MAT101 | Giải tích |" in content
    assert needs_ocr is True

    monkeypatch.setattr("app.hus.extractors.pdf.pdfplumber.open", lambda _: PDF("A" * 50))
    _, needs_ocr = extract_pdf(b"mock")
    assert needs_ocr is False
