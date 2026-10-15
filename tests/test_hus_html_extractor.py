import pytest

from app.hus.extractors.html import extract_html
from app.hus.models import Publisher


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
