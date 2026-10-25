import pytest
from pathlib import Path
import hashlib

from app.hus.extractors.html import extract_html
from app.hus.models import Publisher


def test_sample_mim_fixture():
    raw = (Path(__file__).parent / "fixtures/hus/sample_mim.html").read_bytes()
    doc, attachments = extract_html(
        raw, "https://mim.hus.vnu.edu.vn/vi/hoc-vu", "2026-10-16T00:00:00Z"
    )
    assert doc.title == "Thông báo học vụ"
    assert doc.published_at == "2026-10-15T08:00:00+07:00"
    assert attachments == ["https://mim.hus.vnu.edu.vn/files/quy-che.pdf"]
    assert "[Quy chế đào tạo](https://mim.hus.vnu.edu.vn/files/quy-che.pdf)" in doc.content
    assert "| Mã | 2026 |" in doc.content


def test_html_hash_uses_cleaned_content():
    raw = "<main><h1>Thông báo</h1><p>A\u200c\u200d\u2060B</p></main>".encode()
    doc, _ = extract_html(raw, "https://mim.hus.vnu.edu.vn/vi/test", "2026-10-16T00:00:00Z")
    assert "AB" in doc.content
    assert "\u200c" not in doc.content
    assert doc.content_hash == hashlib.sha256(doc.content.encode()).hexdigest()


def test_short_main_does_not_include_unrelated_body_text():
    raw = b"<body><main><h1>Notice</h1><p>Read the rules.</p></main><div>Unrelated news</div></body>"
    doc, _ = extract_html(raw, "https://mim.hus.vnu.edu.vn/vi/short", "2026-10-16T00:00:00Z")
    assert "Read the rules." in doc.content
    assert "Unrelated news" not in doc.content


def test_malformed_or_huge_table_span_does_not_crash():
    raw = b"<main><table><tr><th rowspan='oops'>A</th><th colspan='1000000000'>B</th></tr><tr><td>C</td></tr></table></main>"
    doc, _ = extract_html(raw, "https://mim.hus.vnu.edu.vn/vi/table", "2026-10-16T00:00:00Z")
    assert "| A |" in doc.content
    assert len(doc.content) < 2000


def test_html_table_is_separated_from_numbered_paragraph():
    raw = b"<main><p>2. Khung chuong trinh</p><table><tr><th>Ma</th><th>Hoc phan</th></tr><tr><td>1</td><td>Toan</td></tr></table></main>"

    doc, _ = extract_html(raw, "https://mim.hus.vnu.edu.vn/vi/table", "2026-10-16T00:00:00Z")

    assert "2. Khung chuong trinh\n\n| Ma | Hoc phan |" in doc.content


def test_extract_html_with_attachments_and_tables():
    raw_html = b"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Th\xc3\xb4ng b\xc3\xa1o h\xe1\xbb\x8dc v\xe1\xbb\xa5 | MIM</title>
        <meta property="article:published_time" content="2026-10-15T08:00:00+07:00">
    </head>
    <body>
        <nav><a href="/vi/home">Home</a></nav>
        <div id="content">
            <h1>K\xe1\xba\xbf ho\xe1\xba\xa1ch \xc4\x91\xc3\xa0o t\xe1\xba\xa1o n\xc4\x83m 2026</h1>
            <p>Chi ti\xe1\xba\xbft xem t\xe1\xba\xa1i file sau:</p>
            <p><a href="/files/kehoach.pdf">T\xe1\xba\xa3i PDF k\xe1\xba\xbf ho\xe1\xba\xa1ch</a></p>
            <p><a href="/files/bieumau.docx">Bi\xe1\xbb\x83u m\xe1\xba\xabu Word</a></p>
            <table>
                <tr><th>M\xc3\xa3 m\xc3\xb4n</th><th>T\xc3\xaan m\xc3\xb4n</th></tr>
                <tr><td>MAT1001</td><td>Gi\xe1\xba\xa3i t\xc3\xadch 1</td></tr>
            </table>
            <a href="/vi/khac">Trang li\xc3\xaan quan</a>
        </div>
        <footer>B\xe1\xba\xa3n quy\xe1\xbb\x81n HUS</footer>
    </body>
    </html>
    """
    url = "https://mim.hus.vnu.edu.vn/vi/thong-bao-1"
    doc, attachments = extract_html(raw_html, url, fetched_at="2026-10-15T12:00:00Z")

    assert doc.title == "Kế hoạch đào tạo năm 2026"
    assert doc.publisher == Publisher.MIM
    assert doc.published_at == "2026-10-15T08:00:00+07:00"
    assert len(doc.attachments) == 2
    assert doc.attachments[0].file_type == "pdf"
    assert doc.attachments[1].file_type == "docx"
    assert "https://mim.hus.vnu.edu.vn/files/kehoach.pdf" in attachments
    assert "https://mim.hus.vnu.edu.vn/files/bieumau.docx" in attachments
    assert "https://mim.hus.vnu.edu.vn/vi/khac" in doc.links
    assert "| MAT1001 | Giải tích 1 |" in doc.content


def test_extract_html_only_discovers_main_attachments_and_keeps_links():
    raw = b"""
    <html><body><nav><a href='/files/menu.pdf'>Menu</a></nav>
    <main><h1>Training notice</h1><p>Official details are in
    <a href='/files/rules.pdf'>Rules PDF</a>.</p>
    <table><tr><th rowspan='2'>Code</th><th>Year</th></tr>
    <tr><td>2026</td></tr></table></main></body></html>
    """
    doc, attachments = extract_html(
        raw, "https://mim.hus.vnu.edu.vn/vi/notice", "2026-10-15T08:00:00Z"
    )
    assert attachments == ["https://mim.hus.vnu.edu.vn/files/rules.pdf"]
    assert "[Rules PDF](https://mim.hus.vnu.edu.vn/files/rules.pdf)" in doc.content
    assert "Menu" not in doc.content
    assert "| Code | Year |" in doc.content
    assert "| Code | 2026 |" in doc.content
