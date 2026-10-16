import httpx
import pytest

from app.hus.allowlist import Allowlist
from app.hus.crawler import Robots, fetch_attachment
from app.hus.urls import CrawlError

SOURCES = [{"host": "mim.hus.vnu.edu.vn", "path_prefixes": ["/files/"], "seeds": []}]


def test_fetch_attachment_success():
    def handler(request: httpx.Request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        if request.url.path == "/files/doc.pdf":
            return httpx.Response(200, content=b"%PDF-1.4 mock", headers={"content-type": "application/pdf"})
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    al = Allowlist(SOURCES)
    robots = Robots(client, al.user_agent)

    final_url, headers, body = fetch_attachment("https://mim.hus.vnu.edu.vn/files/doc.pdf", al, client, robots)
    assert final_url == "https://mim.hus.vnu.edu.vn/files/doc.pdf"
    assert body == b"%PDF-1.4 mock"


def test_fetch_attachment_outside_allowlist_rejected():
    client = httpx.Client()
    al = Allowlist(SOURCES)
    robots = Robots(client, al.user_agent)

    with pytest.raises(CrawlError, match="outside allowlist"):
        fetch_attachment("https://evil.example.com/files/doc.pdf", al, client, robots)
