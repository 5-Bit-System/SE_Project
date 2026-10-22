"""Keep effective HTTP URLs while retaining canonical identity across crawl runs."""

import hashlib
import io
import json

from docx import Document
import httpx
import pytest

from app.hus.allowlist import Allowlist
from app.hus.crawler import Robots, fetch_attachment, fetch_html
from app.hus.extractors.html import extract_html
from app.hus.index import HUSIndex
from app.hus.pipeline import HUSPipeline
from app.hus.state import CrawlStateManager
from app.hus.storage import ProcessedStorage, RawStorage
from app.hus.urls import CrawlError

HOST = "mim.hus.vnu.edu.vn"
HTTPS = f"https://{HOST}"
HTTP = f"http://{HOST}"
NOW = "2026-10-21T00:00:00Z"


def rules():
    return Allowlist([{"host": HOST, "path_prefixes": ["/vi/", "/files/"],
                       "seeds": [HTTPS + "/vi/seed"]}], delay_seconds=0)


@pytest.mark.parametrize("attachment", [False, True])
def test_fetch_returns_effective_http_url_and_drops_https_validators(attachment):
    seen = []
    path = "/files/rules.pdf" if attachment else "/vi/seed"
    body = b"%PDF-example" if attachment else b"<main><h1>Seed</h1></main>"

    def handler(request):
        seen.append((str(request.url), request.headers.get("if-none-match")))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.scheme == "https":
            raise httpx.ConnectError("simulated HTTPS connection failure", request=request)
        return httpx.Response(200, content=body, headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        robots = Robots(client, rules().user_agent, delay_seconds=0)
        fetch = fetch_attachment if attachment else fetch_html
        final, _, raw = fetch(HTTPS + path, rules(), client, robots,
                              headers={"If-None-Match": '"https-version"'})
    assert final == HTTP + path
    assert raw == body
    assert seen[-1] == (HTTP + path, None)


def test_relative_redirect_after_fallback_keeps_http_scheme():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.scheme == "https":
            raise httpx.ConnectError("simulated HTTPS connection failure", request=request)
        if request.url.path == "/vi/seed":
            return httpx.Response(302, headers={"location": "child"})
        return httpx.Response(200, content=b"<main><h1>Child</h1></main>",
                              headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        final, _, _ = fetch_html(HTTPS + "/vi/seed", rules(), client,
                                 Robots(client, rules().user_agent, delay_seconds=0))
    assert final == HTTP + "/vi/child"
    assert seen[-1] == HTTP + "/vi/child"
    assert HTTPS + "/vi/child" not in seen


@pytest.mark.parametrize("target", ["http://chem.hus.vnu.edu.vn/vi/private", "/outside/private"])
def test_http_redirect_still_checks_allowlist(target):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.scheme == "https":
            raise httpx.ConnectError("simulated HTTPS connection failure", request=request)
        assert request.url.path == "/vi/seed"
        return httpx.Response(302, headers={"location": target})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CrawlError, match="outside allowlist"):
            fetch_html(HTTPS + "/vi/seed", rules(), client,
                       Robots(client, rules().user_agent, delay_seconds=0))
    assert all("private" not in url for url in seen)


def test_http_sources_survive_reload_and_304_without_duplicate_documents(tmp_path):
    phase = 1
    seen = []
    files = {}
    for version in (1, 2):
        doc = Document()
        doc.add_paragraph(f"Attachment version {version}")
        buffer = io.BytesIO()
        doc.save(buffer)
        files[version] = buffer.getvalue()

    def handler(request):
        path = request.url.path
        seen.append((str(request.url), request.headers.get("if-none-match")))
        if path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.scheme == "https":
            raise httpx.ConnectError("simulated HTTPS connection failure", request=request)
        if phase == 2:
            assert request.headers["if-none-match"] == f'"{path}-v1"'
        if path == "/vi/seed":
            if phase == 2:
                return httpx.Response(304)
            body = '<main><h1>Seed</h1><a href="child">Child</a>'
            body += '<a href="/files/rules.docx">Rules</a></main>'
            return httpx.Response(200, text=body, headers={
                "content-type": "text/html", "etag": f'"{path}-v1"',
            })
        if path == "/files/rules.docx":
            return httpx.Response(200, content=files[phase], headers={"etag": f'"{path}-v{phase}"'})
        return httpx.Response(200, text=f"<main><h1>Child</h1><p>Version {phase}</p></main>",
                              headers={"content-type": "text/html", "etag": f'"{path}-v{phase}"'})

    def make_pipeline():
        return HUSPipeline(rules(), RawStorage(tmp_path), ProcessedStorage(tmp_path),
                           CrawlStateManager(tmp_path / "state/crawl_state.json"))

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first = make_pipeline().run(client=client)
        assert first.new_count == 2
        assert first.attachment_count == 1
        phase = 2
        seen.clear()
        second = make_pipeline().run(client=client)

    assert second.error_count == 0
    assert second.new_count == 0
    assert second.unchanged_count == 1
    assert second.updated_count == 1
    assert second.attachment_count == 1
    requests = [(url, etag) for url, etag in seen if not url.endswith("/robots.txt")]
    assert len(requests) == 3
    assert all(url.startswith(HTTP) and etag for url, etag in requests)
    documents = json.loads((tmp_path / "processed/catalog.json").read_text(encoding="utf-8"))["documents"]
    assert len(documents) == 3
    for key, doc in documents.items():
        assert doc["source_url"].startswith(HTTP)
        canonical = doc["source_url"].replace("http://", "https://", 1)
        assert key == hashlib.sha256(canonical.encode()).hexdigest()[:16]
        markdown = list((tmp_path / "processed/documents").rglob(f"*{key[:8]}.md"))[0].read_text(encoding="utf-8")
        assert f'url: {doc["source_url"]}' in markdown
        if doc["parent_url"]:
            assert doc["parent_url"] == HTTP + "/vi/seed"
    state = json.loads((tmp_path / "state/crawl_state.json").read_text(encoding="utf-8"))["records"]
    assert len(state) == 3
    assert all(key.startswith(HTTPS) and record["url"].startswith(HTTP)
               for key, record in state.items())


def test_existing_https_record_is_corrected_without_new_document_id(tmp_path):
    html = b"<main><h1>Seed</h1><p>Unchanged content.</p></main>"
    old, _ = extract_html(html, HTTPS + "/vi/seed", NOW)
    storage = ProcessedStorage(tmp_path)
    old_id = storage.save_document(old)
    storage.commit()
    state = CrawlStateManager(tmp_path / "state/crawl_state.json")
    state.update_record(url=old.url, content_hash=old.content_hash, last_crawled=NOW,
                        etag='"old"', document_id=old_id)
    state.save()

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.scheme == "https":
            raise httpx.ConnectError("simulated HTTPS connection failure", request=request)
        return httpx.Response(200, content=html, headers={"content-type": "text/html"})

    pipeline = HUSPipeline(rules(), RawStorage(tmp_path), ProcessedStorage(tmp_path),
                           CrawlStateManager(tmp_path / "state/crawl_state.json"))
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = pipeline.run(client=client)
    assert result.updated_count == 1
    catalog = json.loads((tmp_path / "processed/catalog.json").read_text(encoding="utf-8"))
    assert set(catalog["documents"]) == {old_id}
    assert catalog["documents"][old_id]["source_url"] == HTTP + "/vi/seed"


def test_legacy_index_updates_actual_source_without_a_duplicate(tmp_path):
    html = b"<main><h1>Seed</h1><p>Unchanged content.</p></main>"
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw")
    https_doc, _ = extract_html(html, HTTPS + "/vi/seed", NOW)
    http_doc, _ = extract_html(html, HTTP + "/vi/seed", NOW)
    assert index.add(https_doc, html) == "new"
    assert index.add(http_doc, html) == "unchanged"
    assert len(index.documents) == 1
    record = index.documents[HTTPS + "/vi/seed"]
    assert record["source_url"] == HTTP + "/vi/seed"
    assert all(chunk["url"] == HTTP + "/vi/seed" for chunk in record["chunks"])


def test_cached_validators_are_only_sent_to_the_effective_url(tmp_path):
    state_file = tmp_path / "crawl_state.json"
    state = CrawlStateManager(state_file)
    state.update_record(url=HTTP + "/vi/seed", content_hash="hash", last_crawled=NOW,
                        etag='"http-v1"', last_modified="Wed, 21 Oct 2026 00:00:00 GMT")
    state.save()
    reloaded = CrawlStateManager(state_file)
    assert reloaded.get_record(HTTPS + "/vi/seed").url == HTTP + "/vi/seed"
    assert reloaded.get_request_headers(HTTPS + "/vi/seed") == {}
    assert reloaded.get_request_headers(HTTP + "/vi/seed") == {
        "If-None-Match": '"http-v1"',
        "If-Modified-Since": "Wed, 21 Oct 2026 00:00:00 GMT",
    }
