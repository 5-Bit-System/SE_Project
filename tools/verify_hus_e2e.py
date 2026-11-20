"""Accept HUS data -> live HTTP -> optional real Chromium, without product DB/provider.

python -X utf8 -m tools.verify_hus_e2e --out backups/hus_e2e/run01 --with-browser
Requires Playwright + an installed Chromium only when --with-browser is supplied.
UI catalogs/profiles are invented fixtures; HUS evidence is the real packaged handoff.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import socket
import threading
import time
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PROGRAMS = {
    "7460101": ("mathematics", "toan_hoc_7460101_2022", "MAT3300"),
    "7460117": ("mathematics_informatics", "toan_tin_7460117_2022", "MAT3539"),
    "7480113QTD": ("computer_science", "khmtt_7480113qtd_2022", "MAT3507"),
    "7460108": ("data_science", "khdl_7460108_2022", "MAT3533"),
}


def _read(path):
    return json.loads(path.read_bytes())


def _rows(path):
    return [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]


class EvidenceOracle:
    """Read original artifacts directly; do not call loader/retriever to derive expected facts."""

    def __init__(self, package=None, asset_root=None):
        self.package = Path(package) if package is not None else ROOT / "data/hus/rag"
        self.current = _read(self.package / "CURRENT.json")
        self.root = self.package / self.current["release_path"]
        self.bundle = _read(self.root / "evidence/canonical_f2.json")
        self.tables = self.bundle["tables"]
        self.chunks = {kind: {c["chunk_id"]: c for c in _rows(self.root / f"{kind}_chunks.jsonl")}
                       for kind in ("f1", "f3")}
        self.hashes = {kind: hashlib.sha256((self.root / f"{kind}_chunks.jsonl").read_bytes()).hexdigest()
                       for kind in self.chunks}
        self.records = {(r["membership"]["curriculum_id"], r["course_code"]): r
                        for r in _rows(self.root / "f2_records.jsonl")}
        self.f3_records = {r["record_id"]: r for r in _rows(self.root / "f3_records.jsonl")}
        self.curricula = {(PROGRAMS[c["major_code"]][0], c["curriculum_version"]): c["curriculum_id"]
                          for c in self.tables["curricula"]}
        self.f2_url = next(iter(self.records.values()))["citation"]["url"]
        self.asset_root = Path(asset_root) if asset_root is not None else ROOT / "data/hus/citation_assets"
        self.asset_registry = _read(self.asset_root / "registry.json")
        self.sources = {s["source_id"]: s for s in _rows(self.root / "sources.jsonl")}
        self.check_asset_binding()
        unsigned = {k: v for k, v in self.asset_registry.items() if k != "registry_sha256"}
        registry_bytes = (json.dumps(unsigned, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        assert hashlib.sha256(registry_bytes).hexdigest() == self.asset_registry["registry_sha256"]
        self.recovered_pages = _rows(self.root / "evidence/recovered_text.jsonl")
        self._page_ownership = {}
        self.seen_citations = {}
        for chunk in self.chunks["f1"].values():
            loc = chunk["citation"]
            source = (self.root / loc["evidence_path"]).read_text(encoding="utf-8")
            assert source[loc["start_char"]:loc["end_char"]] == chunk["source_quote"]

    def check_asset_binding(self):
        assert self.asset_registry["release_sha256"] == self.current["release_sha256"]

    def check_f3_quote(self, citation, original):
        assert citation["quote"] == original["text"]

    def expected_f1_pages(self, source_id, quote):
        """Independent character ownership oracle; never call CitationResolver._quote_pages.

        Share only the release's display normalization (ligatures/artifact removal).
        Map every captured character to its physical page, then find quote occurrences.
        Several matches with different page owners are ambiguous and must stay unknown.
        """
        from app.hus.release_text import display_text

        def clean(text):
            return "".join(c for c in display_text(text)[0].casefold() if c.isalnum())

        if source_id not in self._page_ownership:
            capture = self.sources[source_id]["recovered_capture"]
            pieces, owners = [], []
            for row in sorted((r for r in self.recovered_pages if r["document_id"] == source_id),
                              key=lambda row: row["page"]):
                assert row["raw_sha256"] == capture["sha256"]
                assert hashlib.sha256(row["text"].encode()).hexdigest() == row["text_sha256"]
                part = clean(row["text"])
                pieces.append(part)
                owners.extend([row["page"]] * len(part))
            self._page_ownership[source_id] = ("".join(pieces), owners)
        text, owners = self._page_ownership[source_id]
        needle = clean(quote)
        spans = {tuple(dict.fromkeys(owners[m.start():m.start() + len(needle)]))
                 for m in re.finditer(f"(?={re.escape(needle)})", text)} if needle else set()
        return list(next(iter(spans))) if len(spans) == 1 else []

    def check(self, answer, major, *, dataset=None, code=None, version=None, expected="answered"):
        assert answer["status"] == expected, (major, dataset, code, answer["reply"][:200])
        assert answer["major"] == major
        assert answer["release_id"] == self.current["release_id"]
        assert answer["release_sha256"] == self.current["release_sha256"]
        if expected != "answered":
            assert not answer["citations"] and not answer["facts"]
            assert "Chưa có thông tin" in answer["reply"]
            return
        assert answer["dataset"] == dataset and answer["citations"]
        assert [c["citation_id"] for c in answer["citations"]] == [str(i + 1) for i in range(len(answer["citations"]))]
        if dataset == "f2":
            record = self.records[self.curricula[major, version], code]
            assert [c["metadata"]["source_row_pointer"] for c in answer["citations"]] == record["citation"]["json_pointers"], \
                "F2 must retain every source occurrence exactly once"
        for citation in answer["citations"]:
            assert f"[{citation['citation_id']}]" in answer["reply"]
            assert citation["dataset"] == dataset
            kind = citation["evidence_kind"]
            if kind in {"pdf", "file"}:
                sha = citation["document_sha256"]
                entry = self.asset_registry["assets"][sha]
                assert citation["availability"] == "available"
                assert entry["file_type"] == ("pdf" if kind == "pdf" else "docx")
                assert citation["media_type"] == ("application/pdf" if kind == "pdf" else
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                pages = citation["pdf_pages"]
                assert pages == sorted(set(pages)) and all(type(p) is int and p > 0 for p in pages)
                assert citation["pdf_page"] == (pages[0] if pages else None)
                assert kind == "pdf" or not pages
                expected_url = f"/hus/sources/{sha}"
                if citation["pdf_page"]:
                    assert 1 <= citation["pdf_page"] <= max(citation["pdf_pages"]) <= entry["page_count"]
                    expected_url += f"?page={citation['pdf_page']}#page={citation['pdf_page']}"
                assert citation["open_url"] == expected_url
                self.seen_citations[expected_url] = citation
            elif kind == "web":
                assert citation["open_url"] == citation["source_url"]
                assert citation["document_sha256"] is None and citation["pdf_page"] is None and not citation["pdf_pages"]
            if dataset == "f2":
                pointer = citation["metadata"]["source_row_pointer"]
                assert pointer.startswith("/tables/official_curriculum_entries/")
                row = self.tables["official_curriculum_entries"][int(pointer.rsplit("/", 1)[1])]
                assert json.loads(citation["quote"]) == row == citation["locator"]
                curriculum = next(c for c in self.tables["curricula"] if c["curriculum_id"] == row["curriculum_id"])
                assert PROGRAMS[curriculum["major_code"]][0] == major
                assert curriculum["curriculum_version"] == version and row["course_code"] == code
                pdf_locator = next(p for p in self.records[row["curriculum_id"], code]["citation"]["pdf_locators"]
                                   if p["document"] == row["pdf_document"] and p["page"] == row["pdf_page"])
                assert kind == "pdf" and citation["source_url"] == pdf_locator["url"]
                assert citation["content_origin"] == "structured_source_draft"
                assert citation["document_sha256"] == pdf_locator["sha256"]
                assert citation["pdf_pages"] == [row["pdf_page"]]
                assert citation["metadata"]["provenance"]["source_comparison"]["source"]["url"] == self.f2_url
                expected_review = self.records[row["curriculum_id"], code]["catalog_review"]
                assert citation["review_status"] == answer["facts"]["review_status"] == expected_review["status"]
                assert answer["facts"]["catalog_review"] == expected_review
                continue
            meta = citation["metadata"]
            original = self.chunks[dataset][meta["chunk_id"]]
            assert original["scope"]["major"] == major
            assert meta["package_sha256"] == self.hashes[dataset]
            assert meta["portable_chunk"] == original
            assert citation["content_origin"] == original["content_origin"]
            assert meta["release_sha256"] == self.current["release_sha256"]
            if dataset == "f1":
                assert citation["quote"] == original["source_quote"]
                assert citation["source_url"] == original["citation"]["url"]
                assert citation["locator"]["start_char"] == original["citation"]["start_char"]
                assert citation["locator"]["end_char"] == original["citation"]["end_char"]
                assert citation["review_status"] == original["citation"]["review_status"]
                capture = self.sources[original["citation"]["source_id"]].get("recovered_capture") or {}
                assert citation["source_id"] == original["citation"]["source_id"]
                if capture.get("file_type") in {"pdf", "docx"}:
                    assert citation["document_sha256"] == capture["sha256"]
                    assert kind == ("pdf" if capture["file_type"] == "pdf" else "file")
                    if kind == "pdf":
                        assert citation["pdf_pages"] == self.expected_f1_pages(citation["source_id"], citation["quote"]), \
                            "F1 PDF pages must locate the quote in hash-bound captured text"
                else:
                    assert kind == "web" and citation["availability"] == "unverified"
            else:
                assert original["course_code"] == code and original["scope"]["curriculum_version"] == version
                self.check_f3_quote(citation, original)
                record = self.f3_records[original["record_id"]]
                assert citation["review_status"] == record["review_status"]
                assert meta["warning"] == record["warning"] and record["warning"] in answer["warnings"]
                assert record["warning"] in answer["reply"]
                assert answer["generated_reference_allowed"] is True
                assert citation["display_label"] == "kiến thức AI" and kind == "ai"
                assert "kiến thức AI" in answer["reply"] and citation["open_url"] is None
                assert not meta["academic_verified"] and meta["disclosure_required"]
                assert citation["source_url"] is None
                assert citation["document_sha256"] is None and citation["pdf_page"] is None and not citation["pdf_pages"]
                assert citation["media_type"] is None and citation["availability"] == "available"
                assert not re.search(r"\d+(?:[.,]\d+)?\s*%", answer["reply"])
            assert citation["quote"] in answer["reply"]


@contextmanager
def isolated_server(out):
    # Child-process settings only; never seed or inspect the existing product database.
    os.environ.update(STORAGE_BACKEND="json", DATABASE_URL="", GEMINI_API_KEY="",
                      RECOMMENDATION_LLM_ENABLED="false")
    import httpx
    import uvicorn
    from tests.catalog_fixtures import create_catalog_fixture

    import app.catalog as catalog_module
    import app.profiles as profile_module
    from app.config import get_settings
    from app.main import app

    catalogs, profiles = create_catalog_fixture(out / "synthetic_ui")
    catalog_module.DATA_ROOT, profile_module.PROFILES_PATH = catalogs, profiles
    get_settings.cache_clear()

    def block_provider(*args, **kwargs):
        raise AssertionError("Outbound provider HTTP forbidden during HUS acceptance")

    original = httpx.HTTPTransport.handle_request
    httpx.HTTPTransport.handle_request = block_provider
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    worker = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            if not worker.is_alive() or time.monotonic() > deadline:
                raise AssertionError("Isolated HTTP server failed to start")
            threading.Event().wait(0.05)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        worker.join(timeout=10)
        sock.close()
        httpx.HTTPTransport.handle_request = original


def _post(base, path, payload):
    request = Request(base + path, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urlopen(request, timeout=15) as response:
        assert response.status == 200
        return json.load(response)


def api_acceptance(base, oracle):
    counts = {"f1": 0, "f2": 0, "f3": 0, "official_assessment_refused": 0,
              "cross_major_refused": 0, "wrong_version_refused": 0, "major_alias": 0,
              "generated_opt_in": 0, "chatbot": 0}
    all_codes = {m["course_code"] for m in oracle.tables["curriculum_courses"]}
    for curriculum in oracle.tables["curricula"]:
        cid, version = curriculum["curriculum_id"], curriculum["curriculum_version"]
        major, pid, example = PROGRAMS[curriculum["major_code"]]
        scope = {"major": major, "version": version}
        for field, query in [("introduction", "Giới thiệu ngành"), ("careers", "Nghề nghiệp"),
                             ("objectives", "Mục tiêu đào tạo"), ("further_study", "Học tiếp")]:
            a = _post(base, "/hus/chat", {"question": query, "major": major, "dataset": "f1", "field": field})
            oracle.check(a, major, dataset="f1")
            counts["f1"] += 1
        members = {m["course_code"] for m in oracle.tables["curriculum_courses"] if m["curriculum_id"] == cid}
        for code in sorted(members):
            a = _post(base, "/hus/chat", {**scope, "question": f"Số tín chỉ {code}?"})
            oracle.check(a, major, dataset="f2", code=code, version=version)
            expected = {r["credits_in_source"] for r in oracle.tables["official_curriculum_entries"]
                        if r["curriculum_id"] == cid and r["course_code"] == code}
            assert expected == {a["facts"]["value"]}
            counts["f2"] += 1
            for query in ("Nội dung", "Mục tiêu", "Gợi ý đánh giá"):
                a = _post(base, "/hus/chat", {**scope, "question": f"{query} {code}?", "allow_generated_reference": True})
                oracle.check(a, major, dataset="f3", code=code, version=version)
                counts["f3"] += 1
            a = _post(base, "/hus/chat", {**scope, "question": f"{code} thi cuối kỳ bao nhiêu phần trăm?", "allow_generated_reference": True})
            oracle.check(a, major, expected="no_information")
            counts["official_assessment_refused"] += 1
        for code in sorted(all_codes - members):
            for query in ("Số tín chỉ", "Nội dung"):
                a = _post(base, "/hus/chat", {**scope, "question": f"{query} {code}?"})
                oracle.check(a, major, expected="no_information")
                counts["cross_major_refused"] += 1
        for query in ("Số tín chỉ", "Nội dung"):
            a = _post(base, "/hus/chat", {"major": major, "version": "NONEXISTENT-VERSION",
                                          "question": f"{query} {example}?"})
            oracle.check(a, major, expected="no_information")
            counts["wrong_version_refused"] += 1
        for allowed, status in [(False, "needs_clarification"), (True, "answered")]:
            a = _post(base, "/hus/chat", {**scope, "question": f"Nội dung {example}?", "allow_generated_reference": allowed})
            oracle.check(a, major, dataset="f3", code=example, version=version, expected=status)
            assert a["generated_reference_allowed"] == allowed
            counts["generated_opt_in"] += 1
        alias = {"mathematics": "ngành Toán", "mathematics_informatics": "Toán-Tin",
                 "computer_science": "khmtt", "data_science": "KHDL"}[major]
        other = "khmtt" if major == "data_science" else "KHDL"
        for name, status in [(alias, "answered"), (other, "no_information")]:
            a = _post(base, "/hus/chat", {**scope, "question": f"Số tín chỉ {example} thuộc {name}?"})
            oracle.check(a, major, dataset="f2", code=example, version=version, expected=status)
            counts["major_alias"] += 1
        for query, dataset, status in [("Giới thiệu ngành", "f1", "answered"),
                                        (f"Số tín chỉ {example}?", "f2", "answered"),
                                        (f"Nội dung {example}?", "f3", "answered"),
                                        (f"Nên học {example} vì thi cuối kỳ 20% đúng không?", "f3", "no_information")]:
            a = _post(base, "/advisor/chat", {"program_id": pid, "message": query, "allow_generated_reference": dataset == "f3"})
            assert a["mode"] == "hus_rag" and a["reply"] == a["hus_answer"]["reply"]
            oracle.check(a["hus_answer"], major, dataset=dataset, code=example, version=version, expected=status)
            counts["chatbot"] += 1
        print(f"API passed: {major}, {len(members)} memberships; totals {sum(counts.values())}", flush=True)
    return counts


def binary_acceptance(base, oracle):
    """Verify every registered binary through live HTTP, independently of the resolver."""
    import pdfplumber
    results = []
    for sha, entry in oracle.asset_registry["assets"].items():
        path = f"/hus/sources/{sha}"
        with urlopen(base + path, timeout=30) as response:
            raw = response.read()
            assert response.status == 200 and hashlib.sha256(raw).hexdigest() == sha
            assert raw == (oracle.asset_root / entry["path"]).read_bytes()
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            if entry["file_type"] == "pdf":
                assert response.headers["Content-Type"] == "application/pdf" and raw.startswith(b"%PDF-")
                assert response.headers["Content-Disposition"].startswith("inline;")
                with pdfplumber.open(io.BytesIO(raw)) as pdf:
                    assert len(pdf.pages) == entry["page_count"]
            else:
                assert response.headers["Content-Type"].endswith("wordprocessingml.document")
                assert response.headers["Content-Disposition"].startswith("attachment;")
                with zipfile.ZipFile(io.BytesIO(raw)) as doc:
                    assert "word/document.xml" in doc.namelist()
        with urlopen(Request(base + path, method="HEAD"), timeout=30) as response:
            assert int(response.headers["Content-Length"]) == entry["bytes"] and not response.read()
        with urlopen(Request(base + path, headers={"Range": "bytes=0-4"}), timeout=30) as response:
            assert response.status == 206 and response.read() == raw[:5]
        results.append({"sha256": sha, "kind": entry["file_type"], "bytes": len(raw),
                        "pages": entry["page_count"], "GET_HEAD_range": "pass"})
    # Also check all page-specific URLs actually emitted by real answers.
    for path, citation in oracle.seen_citations.items():
        with urlopen(Request(base + path.split("#")[0], method="HEAD"), timeout=30) as response:
            assert response.status == 200
            assert response.headers["ETag"] == '"' + citation["document_sha256"] + '"'
    return {"files": results, "emitted_page_urls_checked": len(oracle.seen_citations),
            "external_web_health_checked": False, "academic_or_visual_page_review_added": False}


def browser_acceptance(base, out, oracle):
    from playwright.sync_api import expect, sync_playwright

    results, errors = [], []
    with sync_playwright() as p:
        # Full Chromium has the built-in PDF viewer; headless_shell does not.
        browser = p.chromium.launch(headless=True, channel="chromium", timeout=15000)
        try:
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            internal_pdf = ("chrome-extension://mhjfbmdgcfjbbpaeojofohoefgiehjai/", "chrome://resources/")
            context.route("**/*", lambda route: route.continue_()
                          if route.request.url.startswith((base + "/", *internal_pdf)) else route.abort())
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base, wait_until="networkidle")
            expect(page.locator("#program-select option")).to_have_count(4)
            page.locator("#advisor-bubble-btn").click()

            def ask(query, major, version, code, dataset, status, allow_generated=None):
                page.locator("#hus-generated-opt-in").set_checked(dataset == "f3" if allow_generated is None else allow_generated)
                page.locator("#advisor-input-text").fill(query)
                with page.expect_response(lambda response: response.url.endswith("/advisor/chat")) as event:
                    page.locator("#btn-send-chat").click()
                response = event.value
                assert response.status == 200
                a = response.json()
                assert a["mode"] == "hus_rag"
                oracle.check(a["hus_answer"], major, dataset=dataset, code=code, version=version, expected=status)
                expect(page.locator("#btn-send-chat")).to_be_enabled()
                message = page.locator("#chat-messages-container .message-advisor").last
                assert a["reply"] in message.text_content()
                urls = {urljoin(base, c["open_url"]) for c in a["hus_answer"]["citations"] if c["open_url"]}
                assert {link.get_attribute("href") for link in message.locator("a").all()} == urls
                if status == "answered" and dataset == "f3":
                    citations = a["hus_answer"]["citations"]
                    spans = message.locator(".chat-sources span")
                    expect(spans).to_have_count(len(citations))
                    expect(message.locator(".chat-sources a")).to_have_count(0)
                    expect(spans).to_contain_text([f"kiến thức AI — {c['metadata']['course_code']}" for c in citations])
                    for i in range(len(citations)):
                        expect(spans.nth(i)).to_be_visible()
                    results.append({"case": "ai-null-open-url-visible", "major": major,
                                    "api_open_urls": [c["open_url"] for c in citations],
                                    "visible_source_cards": len(citations), "anchors": 0, "result": "pass"})
                results.append({"major": major, "dataset": dataset, "question": query, "status": status, "result": "pass"})
                return a["hus_answer"], message

            def open_pdf(link, citation, name):
                expected_url = urljoin(base, citation["open_url"])
                with page.expect_popup() as popup_event:
                    link.click()
                popup = popup_event.value
                popup.bring_to_front()
                popup.wait_for_url(expected_url, wait_until="commit")
                deadline, viewer = time.monotonic() + 10, None
                while time.monotonic() < deadline:
                    viewer = next((f for f in popup.frames if f.url.startswith(internal_pdf[0])), None)
                    if viewer and viewer.locator('embed[type="application/x-google-chrome-pdf"]').count():
                        break
                    popup.wait_for_timeout(100)
                assert viewer and viewer.locator('embed[type="application/x-google-chrome-pdf"]').count() == 1
                if citation["pdf_page"]:
                    expect(viewer.locator("viewer-page-selector input")).to_have_value(str(citation["pdf_page"]))
                # Toolbar and viewport coordinates update optimistically before the
                # remote PDF plugin applies the scroll. Require its acknowledgment
                # and actual inner-document scroll, not just the requested number.
                ready, remote, deadline = None, None, time.monotonic() + 20
                while time.monotonic() < deadline:
                    ready = viewer.evaluate("""() => {
                        const p = document.querySelector('pdf-viewer');
                        const loaded = p.getLoadSucceededForTesting();
                        return {loaded, initial_load_complete: p.initialLoadComplete_,
                            visible_page: loaded ? p.viewport_.getMostVisiblePage() + 1 : null,
                            pending_scrolls: p.viewport_?.scrollContent_?.unackedScrollsToRemote_,
                            viewport: p.viewport_?.position};
                    }""")
                    inner = next((f for f in popup.frames if f != popup.main_frame and f.url == expected_url), None)
                    if inner:
                        remote = inner.evaluate("({x: scrollX, y: scrollY})")
                    if (ready["loaded"] and ready["initial_load_complete"] and ready.get("pending_scrolls") == 0
                            and (not citation["pdf_page"] or ready["visible_page"] == citation["pdf_page"])
                            and remote and abs(remote["y"] - ready["viewport"]["y"]) <= 1):
                        break
                    popup.wait_for_timeout(100)
                else:
                    raise AssertionError(f"PDF plugin did not apply the physical-page scroll: {ready}, remote={remote}")
                viewer.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                popup.screenshot(path=str(out / f"pdf-{name}.png"))
                popup.close()
                results.append({"case": "click-real-pdf-viewer", "source": name,
                                "open_url": citation["open_url"], "physical_page": citation["pdf_page"],
                                "viewer_ready": ready, "remote_scroll": remote, "result": "pass"})

            for curriculum in oracle.tables["curricula"]:
                major, pid, example = PROGRAMS[curriculum["major_code"]]
                version = curriculum["curriculum_version"]
                page.locator("#program-select").select_option(pid)
                page.wait_for_load_state("networkidle")
                assert page.evaluate("state.currentProgramId") == pid
                f1_answer, f1_message = ask("Giới thiệu ngành", major, version, example, "f1", "answered")
                web = next((c for c in f1_answer["citations"] if c["evidence_kind"] == "web"), None)
                if web:
                    # Verify actual navigation destination without claiming the external site is online.
                    context.route(web["open_url"], lambda route: route.fulfill(
                        status=200, content_type="text/html", body="<p>Navigation target captured locally</p>"))
                    with page.expect_popup() as event:
                        f1_message.locator(f'a[href="{web["open_url"]}"]').click()
                    popup = event.value
                    popup.wait_for_url(web["open_url"], wait_until="commit")
                    popup.close()
                    context.unroute(web["open_url"])
                    results.append({"case": "web-click-original-url-intercepted", "major": major,
                                    "url": web["open_url"], "remote_health_verified": False, "result": "pass"})
                pdf_answer, pdf_message = ask(f"Số tín chỉ {example}?", major, version, example, "f2", "answered")
                open_pdf(pdf_message.locator("a").first, pdf_answer["citations"][0], major)
                ask(f"Nội dung {example}?", major, version, example, "f3", "needs_clarification", allow_generated=False)
                ask(f"Nội dung {example}?", major, version, example, "f3", "answered")
                page.screenshot(path=str(out / f"chat-{major}.png"), full_page=True)
                ask(f"Nên học {example} vì thi cuối kỳ 20% đúng không?", major, version, example, "f3", "no_information")
                ask("Nội dung MAT9999?", major, version, "MAT9999", "f3", "no_information")
                other = "khmtt" if major == "data_science" else "KHDL"
                ask(f"Số tín chỉ {example} của ngành {other}?", major, version, example, "f2", "no_information")
                print(f"Browser passed: {major}", flush=True)

            # A real canonical F2 answer has two source occurrences in one PDF.
            # Verify the actual API -> renderer -> PDF viewer chain, with no fabricated pages.
            page.locator("#program-select").select_option("toan_hoc_7460101_2022")
            page.wait_for_load_state("networkidle")
            multi_answer, multi_message = ask("Tiên quyết MAT3325?", "mathematics", "QD3565-2023",
                                            "MAT3325", "f2", "answered")
            multi = multi_answer["citations"]
            assert len(multi) == 2 and {c["pdf_page"] for c in multi} == {12, 13}
            assert len({c["document_sha256"] for c in multi}) == 1
            expect(multi_message.locator(".chat-sources a")).to_have_count(2)
            assert {link.get_attribute("href") for link in multi_message.locator("a").all()} == {
                urljoin(base, c["open_url"]) for c in multi}
            for i, citation in enumerate(multi):
                open_pdf(multi_message.locator("a").nth(i), citation, f"MAT3325-page-{citation['pdf_page']}")
            results.append({"case": "real-api-same-pdf-distinct-pages", "course_code": "MAT3325",
                            "source_occurrences": 2, "pages": [c["pdf_page"] for c in multi], "result": "pass"})

            # Renderer edge cases use declared UI fixtures and real registered binaries.
            # These are not claims that retrieval produced a new answer.
            doc_sha, doc = next((sha, e) for sha, e in oracle.asset_registry["assets"].items() if e["file_type"] == "docx")
            fixture = {"citation_id": "1", "label": "DOCX renderer fixture", "evidence_kind": "file",
                       "source_id": doc_sha, "document_sha256": doc_sha, "availability": "available",
                       "open_url": f"/hus/sources/{doc_sha}", "review_status": "include_markdown"}
            page.evaluate("c => appendChatMessage('advisor', 'UI fixture: DOCX', false, [c])", fixture)
            with page.expect_download() as event:
                page.locator("#chat-messages-container .message-advisor").last.locator("a").click()
            download = event.value
            assert download.failure() is None
            assert hashlib.sha256(Path(download.path()).read_bytes()).hexdigest() == doc_sha
            results.append({"case": "docx-click-download-ui-fixture", "sha256": doc_sha, "result": "pass"})
            first, second = multi
            missing = {**first, "citation_id": "3", "open_url": None, "availability": "missing",
                       "availability_note": "UI fixture: source missing"}
            page.evaluate("cs => appendChatMessage('advisor', 'UI fixture: duplicate and missing', false, cs)",
                          [first, first, second, missing])
            message = page.locator("#chat-messages-container .message-advisor").last
            expect(message.locator("a")).to_have_count(2)
            expect(message.locator(".chat-sources span")).to_contain_text(["source missing"])
            results.append({"case": "exact-duplicate-removed-distinct-pages-and-missing-kept-ui-fixture", "result": "pass"})

            # Hold a real chat request while changing the selected major, then release
            # the real old-scope server response. No mocked answer payload is used.
            held = []
            page.route("**/advisor/chat", lambda route: held.append(route))
            page.locator("#advisor-input-text").fill("Giới thiệu ngành")
            page.locator("#btn-send-chat").click()
            page.wait_for_timeout(100)
            assert held
            old_pid = page.evaluate("state.currentProgramId")
            new_pid = next(v[1] for v in PROGRAMS.values() if v[1] != old_pid)
            page.locator("#program-select").select_option(new_pid)
            page.wait_for_function("pid => state.currentProgramId === pid", arg=new_pid)
            response = held[0].fetch()
            held[0].fulfill(response=response)
            page.unroute("**/advisor/chat")
            page.wait_for_load_state("networkidle")
            assert page.evaluate("state.chatHistory.length") == 0
            assert page.locator("#chat-messages-container .chat-message").count() == 0
            results.append({"case": "late-old-major-response-discarded", "result": "pass"})
            assert not errors, errors
        finally:
            browser.close()
    return {"cases": results, "page_errors": errors,
            "external_requests": "blocked; source-web navigation intercepted locally; built-in PDF resources allowed"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--with-browser", action="store_true")
    args = parser.parse_args(argv)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": "2.0", "started_at": datetime.now(timezone.utc).isoformat(), "status": "running",
              "scope": "local acceptance; real HUS package; synthetic UI catalogs; no academic certification",
              "acceptance_level": "http_and_browser" if args.with_browser else "http_only",
              "artifact_directory": out.relative_to(ROOT).as_posix() if out.is_relative_to(ROOT) else str(out),
              "browser": "not_run", "product_database_modified": False, "llm_used": False}
    try:
        oracle = EvidenceOracle()
        inputs = [oracle.package / "CURRENT.json", oracle.root / "manifest.json"]
        inputs += [oracle.root / name for name in _read(oracle.root / "manifest.json")["files"]]
        inputs += [oracle.asset_root / "registry.json"]
        inputs += [oracle.asset_root / e["path"] for e in oracle.asset_registry["assets"].values()]
        report["selected_release"] = oracle.current
        report["input_sha256"] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
        code = list((ROOT / "app/hus").glob("*.py")) + [ROOT / p for p in [
            "app/api/routes.py", "app/advisor.py", "app/static/app.js", "app/static/index.html", "app/schemas/hus.py",
            "app/services/hus_service.py", "tools/verify_hus_e2e.py"]]
        report["implementation_sha256"] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in code}
        verification = list((ROOT / "tests/hus").glob("test_*.py")) + list((ROOT / "tests/frontend").glob("*.cjs"))
        verification += [ROOT / "tests/conftest.py", ROOT / "tests/catalog_fixtures.py"]
        report["verification_sha256"] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                                         for p in sorted(verification)}
        with isolated_server(out) as base:
            report["api"] = api_acceptance(base, oracle)
            report["binaries"] = binary_acceptance(base, oracle)
            if args.with_browser:
                report["browser"] = browser_acceptance(base, out, oracle)
        assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                   for name, digest in report["input_sha256"].items()), "Acceptance changed input data"
        for category in ("implementation_sha256", "verification_sha256"):
            assert all(hashlib.sha256((ROOT / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == digest
                       for name, digest in report[category].items()), "Code/tests changed during acceptance"
        report["artifacts_sha256"] = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in sorted(out.glob("*.png"))}
        report["status"] = "pass"
    except Exception as exc:
        report["status"] = "fail"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Acceptance {report['status']}: {out / 'report.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
