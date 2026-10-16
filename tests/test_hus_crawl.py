"""HUS crawler tests. All HTML is mock (tests/fixtures/hus); no real network is used."""

import json
from pathlib import Path

import httpx
import pytest

from app.hus.cleaning import extract_document
from app.hus.crawler import MAX_BYTES, Allowlist, check_allowed, crawl
from app.hus.index import HUSIndex, chunk_document
from app.hus.models import HUSDocument
from app.hus.urls import CrawlError, canonicalize_url
from tools.build_hus_index import main as build_main

FIXTURE = Path(__file__).parent / "fixtures" / "hus" / "mock_page.html"
HOST = "mim.hus.vnu.edu.vn"
SOURCES = [{"host": HOST, "path_prefixes": ["/vi/"], "seeds": [f"https://{HOST}/vi/start"]}]


def allowlist(**kwargs) -> Allowlist:
    return Allowlist(SOURCES, delay_seconds=0, **kwargs)


def client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def html_response(body: str | bytes = "<html><body><div id='content'></div></body></html>"):
    return httpx.Response(200, content=body, headers={"content-type": "text/html; charset=utf-8"})


def page(title: str, links: str = "", filler: str = "") -> str:
    text = f"Nội dung trang {title}. " * 6 + filler
    return f"<html><body><div id='content'><h1>{title}</h1><p>{text}</p>{links}</div></body></html>"


def no_sleep(_seconds):
    pass


def test_empty_allowlist_makes_no_request():
    def handler(request):
        raise AssertionError("no request may be made")

    documents, failures = crawl(Allowlist([]), client_for(handler), sleep=no_sleep)
    assert (documents, failures) == ([], {})


def test_urls_outside_scope_are_refused():
    rules = allowlist()
    for url in (
        "https://evil.example/vi/x",
        f"https://{HOST}/en/x",
        "https://localhost/vi/x",
        "https://127.0.0.1/vi/x",
        "https://10.0.0.5/vi/x",
        f"https://{HOST}:8080/vi/x",
        "ftp://mim.hus.vnu.edu.vn/vi/x",
    ):
        with pytest.raises(CrawlError):
            check_allowed(url, rules)


def test_canonicalize_url():
    assert canonicalize_url("http://MIM.hus.vnu.edu.vn/vi/a/?utm_source=x&b=2&a=1#frag") == (
        "https://mim.hus.vnu.edu.vn/vi/a?a=1&b=2"
    )
    assert canonicalize_url("https://x.vn/vi/n%C3%AA") == canonicalize_url("https://x.vn/vi/nê")


def test_redirect_out_of_scope_and_robots_are_blocked():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /vi/private\n")
        if request.url.path == "/vi/hop":
            return httpx.Response(302, headers={"location": "https://evil.example/vi/x"})
        return html_response(page("ok"))

    rules = Allowlist(
        [{"host": HOST, "path_prefixes": ["/vi/"], "seeds": [f"https://{HOST}/vi/hop",
                                                            f"https://{HOST}/vi/private/a",
                                                            f"https://{HOST}/vi/ok"]}],
        delay_seconds=0,
    )
    documents, failures = crawl(rules, client_for(handler), sleep=no_sleep)
    assert [d.url for d, _ in documents] == [f"https://{HOST}/vi/ok"]
    assert "outside allowlist" in failures[f"https://{HOST}/vi/hop"]
    assert "robots.txt disallows" in failures[f"https://{HOST}/vi/private/a"]
    assert not any("evil.example" in url for url in seen)


def test_robots_failure_modes():
    for status, expect_pages in ((404, 1), (503, 0)):
        def handler(request, status=status):
            if request.url.path == "/robots.txt":
                return httpx.Response(status)
            return html_response(page("x"))

        documents, _ = crawl(allowlist(), client_for(handler), sleep=no_sleep)
        assert len(documents) == expect_pages


def test_http_error_oversize_and_non_html_are_failures_not_pages():
    calls = {"/vi/err": 0}

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.path == "/vi/err":
            calls["/vi/err"] += 1
            return httpx.Response(500)
        if request.url.path == "/vi/big":
            return html_response(b"x" * (MAX_BYTES + 1))
        return httpx.Response(200, content=b"%PDF", headers={"content-type": "application/pdf"})

    rules = Allowlist(
        [{"host": HOST, "path_prefixes": ["/vi/"], "seeds": [f"https://{HOST}/vi/{n}"
                                                            for n in ("err", "big", "pdf")]}],
        delay_seconds=0,
    )
    documents, failures = crawl(rules, client_for(handler), sleep=no_sleep)
    assert documents == []
    assert calls["/vi/err"] == 3  # retry_attempts
    assert "gave up" in failures[f"https://{HOST}/vi/err"]
    assert "over" in failures[f"https://{HOST}/vi/big"]
    assert "not HTML" in failures[f"https://{HOST}/vi/pdf"]


def test_crawl_follows_menu_links_within_depth_and_page_limits():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        n = request.url.path.rsplit("/", 1)[-1]
        links = {
            "start": '<a href="/vi/a">a</a><a href="https://evil.example/vi/z">z</a>',
            "a": '<a href="/vi/b">b</a>',
            "b": '<a href="/vi/c">c</a>',
        }.get(n, "")
        return html_response(page(n, links))

    documents, failures = crawl(allowlist(max_depth=1), client_for(handler), sleep=no_sleep)
    assert [d.url.rsplit("/", 1)[-1] for d, _ in documents] == ["start", "a"]
    assert failures == {}
    documents, _ = crawl(allowlist(max_pages=1), client_for(handler), sleep=no_sleep)
    assert len(documents) == 1


def test_extract_document_cleans_and_keeps_structure():
    raw = FIXTURE.read_bytes()
    doc = extract_document(raw, f"https://{HOST}/vi/content/mau", "2026-10-15T00:00:00+00:00")
    assert doc.title == "Thông báo mẫu về đăng ký học phần"
    assert doc.published_at == "2026-09-15T08:30:00+07:00"
    for junk in ("SCRIPT_TEXT", "HEADER_MENU_TEXT", "FOOTER_TEXT", "COMMENT_TEXT", "Ngoài phạm vi"):
        assert junk not in doc.content
    assert "## Danh sách học phần" in doc.content
    assert "| Mã học phần | Tên học phần | Số tín chỉ |" in doc.content
    assert "| MAT1000 | Giải tích | 4 |" in doc.content
    assert "- Mục một" in doc.content
    assert f"[hướng dẫn](https://{HOST}/vi/content/huong-dan)" in doc.content
    # menu links drive discovery; mail, attachments and tracking params are dropped
    assert f"https://{HOST}/vi/cacctrdaotao" in doc.links
    assert not any(link.endswith(".pdf") or "mailto" in link for link in doc.links)


def test_published_at_is_null_without_dedicated_markup_and_text_is_nfc():
    html = "<div id='content'><h1>Chương trình đào tạo</h1><p>" + "Toán học 2020. " * 10 + "</p></div>"
    decomposed = html.replace("à", "a\u0300")
    doc = extract_document(
        decomposed.encode(), f"https://{HOST}/vi/x", "2026-10-15T22:00:00Z"
    )
    assert doc.published_at is None
    assert "Chương trình" in doc.content and "\u0300" not in doc.content


def test_empty_page_is_rejected():
    with pytest.raises(CrawlError):
        extract_document(b"<html><body><nav>menu</nav></body></html>", f"https://{HOST}/vi/x", "t")


def make_doc(url: str, content: str) -> HUSDocument:
    return HUSDocument(
        url=url, title="Tiêu đề", fetched_at="2026-10-15T00:00:00+00:00",
        content_hash=f"hash-{content}", content=content,
    )


def test_chunks_keep_provenance_and_have_stable_ids():
    content = "# Mục A\n" + "\n".join(f"Dòng số {i} " * 20 for i in range(30)) + "\n## Mục B\nKết."
    doc = make_doc(f"https://{HOST}/vi/long", content)
    chunks = chunk_document(doc, max_chars=500)
    assert len(chunks) > 3
    assert all(len(c.text) <= 500 + 20 for c in chunks)
    assert {c.url for c in chunks} == {doc.url}
    assert chunks[0].heading == "Mục A" and chunks[-1].heading == "Mục B"
    assert [c.chunk_id for c in chunks] == [c.chunk_id for c in chunk_document(doc, 500)]
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_index_dedup_update_and_atomic_reload(tmp_path):
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw")
    a = make_doc(f"https://{HOST}/vi/a", "Nội dung A")
    assert index.add(a, b"<html>a</html>") == "new"
    assert index.add(a, b"<html>a</html>") == "unchanged"
    assert len(index.documents[a.url]["chunks"]) == 1  # no duplicate chunks on re-crawl

    changed = make_doc(a.url, "Nội dung A đã sửa")
    assert index.add(changed, b"<html>a2</html>") == "updated"
    record = index.documents[a.url]
    assert record["version"] == 2 and record["history"][0]["content_hash"] == a.content_hash
    assert "đã sửa" in record["chunks"][0]["text"]
    assert len(list((tmp_path / "raw").iterdir())) == 2  # both original versions kept

    same_elsewhere = make_doc(f"https://{HOST}/vi/copy", "Nội dung A đã sửa")
    assert index.add(same_elsewhere, b"<html>copy</html>") == "duplicate"
    copy = index.documents[same_elsewhere.url]
    assert copy["duplicate_of"] == a.url and copy["chunks"] == []

    index.save()
    assert not (tmp_path / "index.tmp").exists()
    assert HUSIndex(tmp_path / "index.json", tmp_path / "raw").documents == index.documents


def test_cli_empty_allowlist_and_dry_run_do_not_touch_network(tmp_path, capsys):
    empty = tmp_path / "empty.json"
    empty.write_text('{"sources": []}', encoding="utf-8")
    assert build_main(["--allowlist", str(empty), "--out", str(tmp_path / "out")]) == 0
    assert "trống" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()

    filled = tmp_path / "filled.json"
    filled.write_text(json.dumps({"sources": SOURCES}), encoding="utf-8")
    assert build_main(["--allowlist", str(filled), "--dry-run"]) == 0
    assert HOST in capsys.readouterr().out


def test_shipped_allowlist_is_empty_until_robots_are_reviewed():
    shipped = Path(__file__).parents[1] / "data" / "hus" / "allowlist.json"
    assert Allowlist.load(shipped).sources == []
