import io
from pathlib import Path
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


def test_real_pdf_fixture_preserves_text_table_order_without_duplicates():
    raw = (Path(__file__).parent / "fixtures/hus/sample_text.pdf").read_bytes()
    content, needs_ocr = extract_pdf(raw)
    assert not needs_ocr
    assert content.index("Official course information") < content.index("| Code | Course |")
    assert "| MAT101 | Calculus |" in content
    assert content.count("MAT101") == 1


def test_extract_pdf_ignores_one_column_fragments_and_separates_tables(monkeypatch):
    class Table:
        def __init__(self, bbox, rows):
            self.bbox = bbox
            self.rows = rows

        def extract(self):
            return self.rows

    class Page:
        width = 100
        height = 100

        def extract_text(self):
            return "Introduction\nCourse A\nCourse B\nAfterword"

        def find_tables(self):
            return [
                Table((0, 10, 90, 30), [["Code", "Name"], ["A", "Course A"]]),
                Table((40, 12, 80, 22), [["Course"], ["A"]]),
                Table((0, 30, 90, 50), [["ID", "Title"], ["B", "Course B"]]),
                Table((0, 70, 90, 80), [["Afterword"], ["continues"]]),
            ]

        def crop(self, bbox):
            top, bottom = bbox[1], bbox[3]
            result = "Introduction" if bottom <= 10 else "Afterword" if top >= 50 else ""
            return type("Crop", (), {"extract_text": lambda self: result})()

    class PDF:
        pages = [Page()]

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

    monkeypatch.setattr("app.hus.extractors.pdf.pdfplumber.open", lambda _: PDF())
    content, _ = extract_pdf(b"mock")

    assert "| Code | Name |\n| --- | --- |\n| A | Course A |" in content
    assert "| ID | Title |\n| --- | --- |\n| B | Course B |" in content
    assert "| A | Course A |\n\n| ID | Title |" in content
    assert content.count("Course A") == 1
    assert "| Afterword |" not in content
    assert content.endswith("Afterword")


def test_extract_pdf_text_table_and_approved_ocr_threshold(monkeypatch):
    class Page:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

        def extract_tables(self):
            return []

        def find_tables(self):
            return []

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
    assert needs_ocr is True

    monkeypatch.setattr("app.hus.extractors.pdf.pdfplumber.open", lambda _: PDF("A" * 50))
    _, needs_ocr = extract_pdf(b"mock")
    assert needs_ocr is False
