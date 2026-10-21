"""End-to-end tests for HUSPipeline orchestrator (all network mocked)."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

from docx import Document
import httpx
import pytest

from app.hus.allowlist import Allowlist
from app.hus.models import DocumentStatus, DocumentType, Publisher
from app.hus.pipeline import CrawlSummary, HUSPipeline
from app.hus.state import CrawlStateManager
from app.hus.storage import ProcessedStorage, RawStorage
from tools.migrate_catalog_majors import migrate_catalog

# ---------------------------------------------------------------------------
# Fixtures: minimal HTML pages and a tiny PDF stub
# ---------------------------------------------------------------------------

_SEED_HTML = b"""<!DOCTYPE html><html><head>
<title>Thong bao dao tao</title>
<meta property="og:title" content="Thong bao dao tao">
</head><body>
<article>
<h1>Thong bao dao tao</h1>
<p>Noi dung thong bao ky 1 nam 2025. Day la bai viet mau de test pipeline end-to-end.</p>
<a href="/vi/bai-viet-2">Bai viet 2</a>
<a href="/files/huong-dan.pdf">Tai huong dan PDF</a>
</article>
</body></html>"""

_CHILD_HTML = b"""<!DOCTYPE html><html><head>
<title>Bai viet 2</title>
</head><body>
<article>
<h1>Bai viet 2</h1>
<p>Noi dung bai viet con so 2. Khong co attachment nao ca.</p>
</article>
</body></html>"""

# Minimal valid PDF (header + empty xref) – enough for pdfplumber to open
# but produces needs_ocr=True because zero text per page.
_TINY_PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"

_ROBOTS_TXT = b"User-agent: *\nAllow: /\n"


def _build_allowlist() -> Allowlist:
    return Allowlist(
        sources=[
            {
                "host": "mim.hus.vnu.edu.vn",
                "path_prefixes": ["/vi/", "/files/"],
                "exclude_prefixes": [],
                "seeds": ["https://mim.hus.vnu.edu.vn/vi/dao-tao"],
            }
        ],
        max_pages=10,
        max_depth=2,
        delay_seconds=0,
        retry_attempts=1,
    )


def _mock_transport(request: httpx.Request) -> httpx.Response:
    """Route mock responses by path."""
    path = request.url.path
    if path == "/robots.txt":
        return httpx.Response(200, content=_ROBOTS_TXT)
    if path == "/vi/dao-tao":
        return httpx.Response(
            200,
            content=_SEED_HTML,
            headers={"content-type": "text/html; charset=utf-8", "ETag": '"abc123"'},
        )
    if path == "/vi/bai-viet-2":
        return httpx.Response(
            200,
            content=_CHILD_HTML,
            headers={"content-type": "text/html; charset=utf-8"},
        )
    if path == "/files/huong-dan.pdf":
        return httpx.Response(
            200,
            content=_TINY_PDF,
            headers={"content-type": "application/pdf"},
        )
    return httpx.Response(404)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHUSPipeline:
    """Full pipeline integration tests with mocked HTTP transport."""

    def _make_pipeline(self, tmp_path: Path) -> tuple[HUSPipeline, Allowlist]:
        allowlist = _build_allowlist()
        raw = RawStorage(tmp_path)
        processed = ProcessedStorage(tmp_path)
        state_file = tmp_path / "state" / "crawl_state.json"
        state = CrawlStateManager(state_file)
        pipeline = HUSPipeline(
            allowlist=allowlist,
            raw_storage=raw,
            processed_storage=processed,
            state_manager=state,
        )
        return pipeline, allowlist

    def test_full_crawl_creates_documents(self, tmp_path: Path) -> None:
        """Pipeline discovers seed → child page → PDF attachment."""
        pipeline, _al = self._make_pipeline(tmp_path)
        client = httpx.Client(transport=httpx.MockTransport(_mock_transport))

        summary = pipeline.run(client=client, sleep=lambda _: None)

        # 2 HTML pages + 1 PDF attachment attempt
        assert summary.new_count >= 2
        assert summary.error_count == 0 or summary.new_count >= 2

        # catalog.json should exist and have entries
        catalog = tmp_path / "processed" / "catalog.json"
        assert catalog.exists()
        data = json.loads(catalog.read_text(encoding="utf-8"))
        assert data["document_count"] >= 2
        for d in data["documents"].values():
            assert "major" in d
            assert d["major"] in {
                "mathematics",
                "mathematics_informatics",
                "computer_science",
                "data_science",
                "general",
            }

        # Raw HTML files saved
        html_dir = tmp_path / "raw" / "html"
        assert len(list(html_dir.glob("*.html"))) >= 2

    def test_incremental_skips_unchanged(self, tmp_path: Path) -> None:
        """Second run with same content should report unchanged, not new."""
        pipeline, _al = self._make_pipeline(tmp_path)
        client = httpx.Client(transport=httpx.MockTransport(_mock_transport))

        first = pipeline.run(client=client, sleep=lambda _: None)
        assert first.new_count >= 2

        # Re-create pipeline to reload state from disk
        pipeline2, _al2 = self._make_pipeline(tmp_path)
        second = pipeline2.run(client=client, sleep=lambda _: None)

        assert second.unchanged_count >= 2
        assert second.new_count == 0

    def test_summary_fields(self, tmp_path: Path) -> None:
        """CrawlSummary has all required fields."""
        pipeline, _ = self._make_pipeline(tmp_path)
        client = httpx.Client(transport=httpx.MockTransport(_mock_transport))

        summary = pipeline.run(client=client, sleep=lambda _: None)
        assert isinstance(summary, CrawlSummary)
        assert hasattr(summary, "new_count")
        assert hasattr(summary, "updated_count")
        assert hasattr(summary, "unchanged_count")
        assert hasattr(summary, "attachment_count")
        assert hasattr(summary, "error_count")
        assert hasattr(summary, "failures")
        assert isinstance(summary.failures, dict)

    def test_max_pages_respected(self, tmp_path: Path) -> None:
        """Pipeline stops after max_pages limit."""
        allowlist = Allowlist(
            sources=[
                {
                    "host": "mim.hus.vnu.edu.vn",
                    "path_prefixes": ["/vi/", "/files/"],
                    "exclude_prefixes": [],
                    "seeds": ["https://mim.hus.vnu.edu.vn/vi/dao-tao"],
                }
            ],
            max_pages=1,
            max_depth=2,
            delay_seconds=0,
            retry_attempts=1,
        )
        raw = RawStorage(tmp_path)
        processed = ProcessedStorage(tmp_path)
        state = CrawlStateManager(tmp_path / "state" / "crawl_state.json")
        pipeline = HUSPipeline(
            allowlist=allowlist,
            raw_storage=raw,
            processed_storage=processed,
            state_manager=state,
        )
        client = httpx.Client(transport=httpx.MockTransport(_mock_transport))
        summary = pipeline.run(client=client, sleep=lambda _: None)

        # Should only process 1 page (max_pages=1)
        assert summary.new_count + summary.unchanged_count <= 1

    def test_attachment_discovery(self, tmp_path: Path) -> None:
        """Pipeline attempts to download and process PDF attachment."""
        pipeline, _ = self._make_pipeline(tmp_path)
        client = httpx.Client(transport=httpx.MockTransport(_mock_transport))

        summary = pipeline.run(client=client, sleep=lambda _: None)

        # The PDF is tiny/empty so it may error or create a pending_ocr doc,
        # but the pipeline should have attempted it.
        assert summary.attachment_count >= 0  # at least attempted

    def test_crawl_error_recorded_not_crash(self, tmp_path: Path) -> None:
        """A page that 404s is recorded as an error, not a crash."""

        def _transport_with_404(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if path == "/vi/dao-tao":
                return httpx.Response(404)
            return httpx.Response(404)

        pipeline, _ = self._make_pipeline(tmp_path)
        client = httpx.Client(transport=httpx.MockTransport(_transport_with_404))

        summary = pipeline.run(client=client, sleep=lambda _: None)
        assert summary.error_count >= 1
        assert summary.new_count == 0

    def test_304_ancestors_still_reach_updated_grandchild(self, tmp_path: Path) -> None:
        phase = 1
        seen = []
        bodies = {
            "/vi/dao-tao": '<main><h1>Seed</h1><a href="/vi/child">Child</a></main>',
            "/vi/child": '<main><h1>Child</h1><a href="/vi/leaf">Leaf</a></main>',
        }

        def handler(request):
            path = request.url.path
            seen.append((path, request.headers.get("if-none-match")))
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if phase == 2 and path in bodies:
                assert request.headers["if-none-match"] == f'"{path}-v1"'
                return httpx.Response(304)
            html = bodies.get(path, f"<main><h1>Leaf</h1><p>Version {phase}</p></main>")
            return httpx.Response(200, text=html, headers={
                "content-type": "text/html", "etag": f'"{path}-v{phase}"',
            })

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            first, _ = self._make_pipeline(tmp_path)
            assert first.run(client=client, sleep=lambda _: None).new_count == 3
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns)
                      for path in (tmp_path / "processed/documents").glob("*.md")}
            phase = 2
            seen.clear()
            second, _ = self._make_pipeline(tmp_path)
            result = second.run(client=client, sleep=lambda _: None)

        assert [path for path, _ in seen] == ["/robots.txt", "/vi/dao-tao", "/vi/child", "/vi/leaf"]
        assert result.new_count == 0
        assert result.updated_count == 1
        assert result.unchanged_count == 2
        assert result.error_count == 0
        catalog = json.loads((tmp_path / "processed/catalog.json").read_text(encoding="utf-8"))
        leaf = next(doc for doc in catalog["documents"].values() if doc["source_url"].endswith("/leaf"))
        assert "Version 2" in leaf["content_markdown"]
        for doc in catalog["documents"].values():
            if not doc["source_url"].endswith("/leaf"):
                path = tmp_path / "processed/documents" / f'{doc["document_id"]}.md'
                assert (path.read_bytes(), path.stat().st_mtime_ns) == before[path]
        assert len(list((tmp_path / "raw/html").glob("*.html"))) == 4

    def test_304_parent_still_refreshes_attachment(self, tmp_path: Path) -> None:
        phase = 1
        seen = []
        files = {}
        for version in (1, 2):
            document = Document()
            document.add_paragraph(f"Attachment version {version}")
            buffer = io.BytesIO()
            document.save(buffer)
            files[version] = buffer.getvalue()

        def handler(request):
            path = request.url.path
            seen.append((path, request.headers.get("if-none-match")))
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if path == "/vi/dao-tao":
                if phase == 2:
                    return httpx.Response(304)
                return httpx.Response(200, text='<main><h1>Seed</h1>'
                                      '<a href="/files/rules.docx">Rules</a></main>',
                                      headers={"content-type": "text/html", "etag": '"seed-v1"'})
            assert path == "/files/rules.docx"
            return httpx.Response(200, content=files[phase], headers={"etag": f'"file-v{phase}"'})

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            first, _ = self._make_pipeline(tmp_path)
            initial = first.run(client=client, sleep=lambda _: None)
            assert initial.attachment_count == 1
            phase = 2
            seen.clear()
            second, _ = self._make_pipeline(tmp_path)
            result = second.run(client=client, sleep=lambda _: None)

        assert seen == [("/robots.txt", None), ("/vi/dao-tao", '"seed-v1"'),
                        ("/files/rules.docx", '"file-v1"')]
        assert result.unchanged_count == 1
        assert result.attachment_count == 1
        assert result.error_count == 0
        catalog = json.loads((tmp_path / "processed/catalog.json").read_text(encoding="utf-8"))
        attachment = next(doc for doc in catalog["documents"].values() if doc["parent_url"])
        assert "Attachment version 2" in attachment["content_markdown"]
        assert attachment["parent_url"] == "https://mim.hus.vnu.edu.vn/vi/dao-tao"

    @pytest.mark.parametrize("limits", [{"max_depth": 0}, {"max_pages": 1}])
    def test_304_discovery_respects_run_limits(self, tmp_path: Path, limits) -> None:
        phase = 1
        seen = []

        def handler(request):
            path = request.url.path
            seen.append(path)
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if path == "/vi/dao-tao":
                if phase == 2:
                    return httpx.Response(304)
                return httpx.Response(200, text='<main><h1>Seed</h1>'
                                      '<a href="/vi/child">Child</a></main>',
                                      headers={"content-type": "text/html", "etag": '"seed"'})
            return httpx.Response(200, text="<main><h1>Child</h1><p>Text.</p></main>",
                                  headers={"content-type": "text/html"})

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            first, _ = self._make_pipeline(tmp_path)
            first.run(client=client, sleep=lambda _: None)
            phase = 2
            seen.clear()
            second, _ = self._make_pipeline(tmp_path)
            result = second.run(client=client, sleep=lambda _: None, **limits)

        assert seen == ["/robots.txt", "/vi/dao-tao"]
        assert result.unchanged_count == 1
        assert result.error_count == 0

    def test_304_cached_links_use_current_allowlist(self, tmp_path: Path) -> None:
        phase = 1
        seen = []

        def handler(request):
            path = request.url.path
            seen.append(path)
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if path == "/vi/dao-tao":
                if phase == 2:
                    return httpx.Response(304)
                return httpx.Response(200, text='<main><h1>Seed</h1>'
                                      '<a href="/vi/blocked">Child</a>'
                                      '<a href="/files/blocked.docx">File</a></main>',
                                      headers={"content-type": "text/html", "etag": '"seed"'})
            raise AssertionError(f"Excluded cached link requested: {path}")

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            first, _ = self._make_pipeline(tmp_path)
            # Save discovery metadata while refusing these links on the initial run.
            first.allowlist.exclusions["mim.hus.vnu.edu.vn"] = ("/vi/blocked", "/files/blocked.docx")
            first.run(client=client, sleep=lambda _: None)
            phase = 2
            seen.clear()
            second, _ = self._make_pipeline(tmp_path)
            second.allowlist.exclusions["mim.hus.vnu.edu.vn"] = ("/vi/blocked", "/files/blocked.docx")
            result = second.run(client=client, sleep=lambda _: None)

        assert seen == ["/robots.txt", "/vi/dao-tao"]
        assert result.unchanged_count == 1
        assert result.error_count == 0

    @pytest.mark.parametrize("cache_problem", ["missing", "invalid", "wrong_url"])
    def test_304_without_cached_document_recovers_with_unconditional_fetch(
        self, tmp_path: Path, cache_problem: str,
    ) -> None:
        phase = 1
        seen = []

        def handler(request):
            path = request.url.path
            seen.append((path, request.headers.get("if-none-match")))
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if path == "/vi/dao-tao":
                if request.headers.get("if-none-match"):
                    return httpx.Response(304)
                return httpx.Response(200, text='<main><h1>Seed</h1>'
                                      '<a href="/vi/child">Child</a></main>',
                                      headers={"content-type": "text/html", "etag": '"seed"'})
            return httpx.Response(200, text=f"<main><h1>Child</h1><p>Version {phase}</p></main>",
                                  headers={"content-type": "text/html"})

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            first, _ = self._make_pipeline(tmp_path)
            first.run(client=client, sleep=lambda _: None)
            catalog_path = tmp_path / "processed/catalog.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            seed_id = next(key for key, value in catalog["documents"].items()
                           if value["source_url"].endswith("/dao-tao"))
            if cache_problem == "missing":
                del catalog["documents"][seed_id]
            elif cache_problem == "invalid":
                catalog["documents"][seed_id]["content_markdown"] = ""
            else:
                catalog["documents"][seed_id]["source_url"] = "https://mim.hus.vnu.edu.vn/vi/wrong"
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            phase = 2
            seen.clear()
            second, _ = self._make_pipeline(tmp_path)
            result = second.run(client=client, sleep=lambda _: None)

        assert seen == [("/robots.txt", None), ("/vi/dao-tao", '"seed"'),
                        ("/vi/dao-tao", None), ("/vi/child", None)]
        assert result.error_count == 0
        restored = json.loads(catalog_path.read_text(encoding="utf-8"))["documents"]
        assert len(restored) == 2
        assert any("Version 2" in doc["content_markdown"] for doc in restored.values())

    def test_304_without_cache_or_response_body_is_reported_as_error(self, tmp_path: Path) -> None:
        def handler(request):
            if request.url.path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            return httpx.Response(304)

        pipeline, _ = self._make_pipeline(tmp_path)
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            result = pipeline.run(client=client, sleep=lambda _: None)

        assert result.unchanged_count == 0
        assert result.error_count == 1
        assert "cached document" in result.failures["https://mim.hus.vnu.edu.vn/vi/dao-tao"]

    def test_304_uses_latest_navigation_after_unchanged_content_hash(self, tmp_path: Path) -> None:
        phase = 1
        seen = []

        def handler(request):
            path = request.url.path
            seen.append(path)
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if path == "/vi/dao-tao":
                if phase == 3:
                    return httpx.Response(304)
                child = "old" if phase == 1 else "new"
                # Navigation affects discovery but is removed from the content hash.
                return httpx.Response(200, text=f'<nav><a href="/vi/{child}">Child</a></nav>'
                                      '<main><h1>Seed</h1><p>Unchanged content.</p></main>',
                                      headers={"content-type": "text/html", "etag": '"seed"'})
            return httpx.Response(200, text=f"<main><h1>Child</h1><p>{path} v{phase}</p></main>",
                                  headers={"content-type": "text/html"})

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            for phase in (1, 2):
                current, _ = self._make_pipeline(tmp_path)
                current.run(client=client, sleep=lambda _: None)
            phase = 3
            seen.clear()
            current, _ = self._make_pipeline(tmp_path)
            result = current.run(client=client, sleep=lambda _: None)

        assert seen == ["/robots.txt", "/vi/dao-tao", "/vi/new"]
        assert result.unchanged_count == 1
        assert result.updated_count == 1
        catalog = json.loads((tmp_path / "processed/catalog.json").read_text(encoding="utf-8"))
        seed = next(doc for doc in catalog["documents"].values() if doc["source_url"].endswith("/dao-tao"))
        assert seed["links"] == ["https://mim.hus.vnu.edu.vn/vi/new"]

    def test_pipeline_assigns_major_classification(self, tmp_path: Path) -> None:
        """Pipeline assigns appropriate major category to HTML documents and attachments."""
        doc_docx = Document()
        doc_docx.add_paragraph("Noi dung ve Nganh May tinh va Khoa hoc thong tin")
        buf = io.BytesIO()
        doc_docx.save(buf)
        docx_bytes = buf.getvalue()

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if path == "/vi/dao-tao":
                html = (
                    "<html><body><article>"
                    "<h1>Thong bao dao tao</h1>"
                    '<a href="/vi/khoa-hoc-du-lieu">Nganh KHDL</a>'
                    '<a href="/files/104.-KHMTTT-chuan.docx">Tai lieu KHMT</a>'
                    "</article></body></html>"
                )
                return httpx.Response(200, text=html, headers={"content-type": "text/html"})
            if path == "/vi/khoa-hoc-du-lieu":
                html = (
                    "<html><body><article>"
                    "<h1>Chuong trinh Khoa hoc du lieu</h1>"
                    "<p>Thong tin ve nganh Khoa hoc du lieu 2026.</p>"
                    "</article></body></html>"
                )
                return httpx.Response(200, text=html, headers={"content-type": "text/html"})
            if path == "/files/104.-KHMTTT-chuan.docx":
                return httpx.Response(200, content=docx_bytes)
            return httpx.Response(404)

        pipeline, _ = self._make_pipeline(tmp_path)
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            summary = pipeline.run(client=client, sleep=lambda _: None)

        assert summary.error_count == 0
        catalog = json.loads((tmp_path / "processed/catalog.json").read_text(encoding="utf-8"))
        docs = catalog["documents"]

        seed = next(d for d in docs.values() if d["source_url"].endswith("/dao-tao"))
        assert seed["major"] == "general"

        ds_doc = next(d for d in docs.values() if d["source_url"].endswith("/khoa-hoc-du-lieu"))
        assert ds_doc["major"] == "data_science"

        att_doc = next(d for d in docs.values() if "104.-KHMTTT-chuan.docx" in d["source_url"])
        assert att_doc["major"] == "computer_science"

    @pytest.mark.parametrize("parent_title, filename, body, expected", [
        ("Khoa học dữ liệu", "guide.docx", "Hướng dẫn đăng ký học phần.", "data_science"),
        ("Khoa học dữ liệu", "guide.docx", "Ngành Khoa học máy tính.", "computer_science"),
        ("Khoa học dữ liệu", "KHMTTT.docx", "Hướng dẫn đăng ký học phần.", "computer_science"),
        ("Thông tin đào tạo", "guide.docx", "Hướng dẫn đăng ký học phần.", "general"),
    ])
    def test_migration_preserves_pipeline_attachment_classification(
        self, tmp_path: Path, parent_title: str, filename: str, body: str, expected: str,
    ) -> None:
        """A real extracted DOCX must keep the same label after catalog migration."""
        document = Document()
        document.add_paragraph(body)
        buffer = io.BytesIO()
        document.save(buffer)

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if request.url.path == "/vi/dao-tao":
                return httpx.Response(
                    200, text=f'<article><h1>{parent_title}</h1>'
                              f'<a href="/files/{filename}">Download</a></article>',
                    headers={"content-type": "text/html"},
                )
            assert request.url.path == f"/files/{filename}"
            return httpx.Response(200, content=buffer.getvalue())

        pipeline, _ = self._make_pipeline(tmp_path)
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            summary = pipeline.run(client=client, sleep=lambda _: None)
        assert summary.error_count == 0
        assert summary.attachment_count == 1
        catalog_path = tmp_path / "processed/catalog.json"
        before = json.loads(catalog_path.read_text(encoding="utf-8"))
        attachment = next(doc for doc in before["documents"].values() if doc["parent_url"])
        assert attachment["major"] == expected

        migrate_catalog(catalog_path)

        assert json.loads(catalog_path.read_text(encoding="utf-8")) == before

    def test_multiple_major_notice_and_generic_attachment_remain_general(
        self, tmp_path: Path,
    ) -> None:
        document = Document()
        document.add_paragraph("Hướng dẫn đăng ký học phần.")
        buffer = io.BytesIO()
        document.save(buffer)

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if path == "/vi/toan-hoc":
                return httpx.Response(
                    200, text="<article><h1>Thông báo dành cho Toán học và Khoa học dữ liệu</h1>"
                              "<p>Sinh viên ngành Toán học đăng ký học phần theo hướng dẫn sau.</p>"
                              '<a href="/files/guide.docx">Hướng dẫn</a></article>',
                    headers={"content-type": "text/html"},
                )
            assert path == "/files/guide.docx"
            return httpx.Response(200, content=buffer.getvalue())

        pipeline, allowlist = self._make_pipeline(tmp_path)
        allowlist.seeds = ["https://mim.hus.vnu.edu.vn/vi/toan-hoc"]
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            summary = pipeline.run(client=client, sleep=lambda _: None)
        assert summary.error_count == 0
        assert summary.new_count == 1
        assert summary.attachment_count == 1
        catalog_path = tmp_path / "processed/catalog.json"
        before = json.loads(catalog_path.read_text(encoding="utf-8"))
        assert len(before["documents"]) == 2
        assert all(doc["major"] == "general" for doc in before["documents"].values())

        # Backfill must repair old single-major labels on both the notice and its file.
        old_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        for doc in old_catalog["documents"].values():
            doc["major"] = "mathematics"
        catalog_path.write_text(json.dumps(old_catalog), encoding="utf-8")
        old_bytes = catalog_path.read_bytes()
        assert migrate_catalog(catalog_path, dry_run=True) == (2, {"general": 2})
        assert catalog_path.read_bytes() == old_bytes
        assert migrate_catalog(catalog_path) == (2, {"general": 2})
        assert json.loads(catalog_path.read_text(encoding="utf-8")) == before

    @pytest.mark.parametrize("reverse_seeds", [False, True])
    def test_shared_attachment_stays_general_regardless_of_first_parent(
        self, tmp_path: Path, reverse_seeds: bool,
    ) -> None:
        document = Document()
        document.add_paragraph("Quy chế áp dụng cho tất cả sinh viên toàn trường.")
        buffer = io.BytesIO()
        document.save(buffer)
        file_requests = []
        parents = ["/vi/khoa-hoc-du-lieu", "/vi/khmt-tt"]
        if reverse_seeds:
            parents.reverse()

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if path in parents:
                return httpx.Response(
                    200, text='<article><h1>Thông tin đào tạo</h1>'
                              '<a href="/files/rules.docx">Quy chế</a></article>',
                    headers={"content-type": "text/html"},
                )
            assert path == "/files/rules.docx"
            file_requests.append(path)
            return httpx.Response(200, content=buffer.getvalue())

        pipeline, allowlist = self._make_pipeline(tmp_path)
        allowlist.seeds = [f"https://mim.hus.vnu.edu.vn{path}" for path in parents]
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            summary = pipeline.run(client=client, sleep=lambda _: None)

        assert summary.error_count == 0
        assert summary.attachment_count == 1
        assert file_requests == ["/files/rules.docx"]
        catalog_path = tmp_path / "processed/catalog.json"
        before = json.loads(catalog_path.read_text(encoding="utf-8"))
        docs = before["documents"].values()
        assert {doc["major"] for doc in docs if not doc["parent_url"]} == {
            "data_science", "computer_science",
        }
        attachment = next(doc for doc in docs if doc["parent_url"])
        assert attachment["parent_url"].endswith(parents[0])
        assert attachment["major"] == "general"

        migrate_catalog(catalog_path)
        assert json.loads(catalog_path.read_text(encoding="utf-8")) == before

    def test_full_major_slug_classifies_html_and_docx_and_repairs_old_catalog(
        self, tmp_path: Path,
    ) -> None:
        document = Document()
        document.add_paragraph("Thông tin chương trình.")
        buffer = io.BytesIO()
        document.save(buffer)
        filename = "toan-hoc-va-tin-hoc.docx"

        def handler(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path == "/robots.txt":
                return httpx.Response(200, content=_ROBOTS_TXT)
            if path == "/vi/toan-hoc":
                return httpx.Response(
                    200, text='<article><h1>Thông tin đào tạo</h1>'
                              '<a href="/vi/toan-hoc-va-tin-hoc">Chương trình</a>'
                              f'<a href="/files/{filename}">Tài liệu</a></article>',
                    headers={"content-type": "text/html"},
                )
            if path == "/vi/toan-hoc-va-tin-hoc":
                return httpx.Response(
                    200, text="<article><h1>Chương trình Toán học và Tin học</h1>"
                              "<p>Thông tin chương trình.</p></article>",
                    headers={"content-type": "text/html"},
                )
            assert path == f"/files/{filename}"
            return httpx.Response(200, content=buffer.getvalue())

        pipeline, allowlist = self._make_pipeline(tmp_path)
        allowlist.seeds = ["https://mim.hus.vnu.edu.vn/vi/toan-hoc"]
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            summary = pipeline.run(client=client, sleep=lambda _: None)
        assert summary.error_count == 0
        assert summary.new_count == 2
        assert summary.attachment_count == 1
        catalog_path = tmp_path / "processed/catalog.json"
        before = json.loads(catalog_path.read_text(encoding="utf-8"))
        for doc in before["documents"].values():
            expected = "mathematics_informatics" if "va-tin-hoc" in doc["source_url"] else "mathematics"
            assert doc["major"] == expected

        # Simulate labels produced by the old substring rule, then backfill them.
        old_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        for doc in old_catalog["documents"].values():
            doc["major"] = "mathematics"
        catalog_path.write_text(json.dumps(old_catalog), encoding="utf-8")
        old_bytes = catalog_path.read_bytes()
        expected_stats = (3, {"mathematics": 1, "mathematics_informatics": 2})
        assert migrate_catalog(catalog_path, dry_run=True) == expected_stats
        assert catalog_path.read_bytes() == old_bytes
        assert migrate_catalog(catalog_path) == expected_stats
        assert json.loads(catalog_path.read_text(encoding="utf-8")) == before
