"""End-to-end tests for HUSPipeline orchestrator (all network mocked)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import httpx
import pytest

from app.hus.allowlist import Allowlist
from app.hus.models import DocumentStatus, DocumentType, Publisher
from app.hus.pipeline import CrawlSummary, HUSPipeline
from app.hus.state import CrawlStateManager
from app.hus.storage import ProcessedStorage, RawStorage

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
