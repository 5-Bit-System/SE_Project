"""Attachment scope, storage, and skip reporting with the shipped source configuration."""

import json
from pathlib import Path

import httpx
import pytest

from app.hus.allowlist import Allowlist, check_allowed
from app.hus.pipeline import HUSPipeline
from app.hus.state import CrawlStateManager
from app.hus.storage import ProcessedStorage, RawStorage
from app.hus.urls import CrawlError

HOST = "https://tuyensinh.hus.vnu.edu.vn"
CONFIG = Path(__file__).parents[1] / "data/hus/config/sources.json"
PDF_PATHS = (
    "/DATA/TUYENSINH/IMAGES/2024/08/"
    "2622_signed.signed.thong-bao-tuyen-sinh-chuong-trinh-vnu-12-plus_hus_final.signed.pdf",
    "/DATA/TUYENSINH/IMAGES/2026/03/9.1.26-chi-tiet-du-thao_dang-cong-tuyen-sinh-1-edit.pdf",
)
BLOCKED_URLS = (
    HOST + "/DATA/KHOA-KHAC/rules.pdf",
    HOST + "/DATA/TUYENSINH-KHAC/rules.pdf",
    "https://chem.hus.vnu.edu.vn/DATA/TUYENSINH/rules.pdf",
)


@pytest.mark.parametrize("path", PDF_PATHS)
def test_shipped_config_allows_tuyensinh_pdf_paths(path):
    assert check_allowed(HOST + path, Allowlist.load(CONFIG)) == HOST + path


@pytest.mark.parametrize("url", BLOCKED_URLS + (
    HOST + "/DATA/TUYENSINH/../KHOA-KHAC/rules.pdf",
    HOST + "/DATA/TUYENSINH/%2e%2e/KHOA-KHAC/rules.pdf",
))
def test_attachment_scope_does_not_open_other_data_directories(url):
    with pytest.raises(CrawlError):
        check_allowed(url, Allowlist.load(CONFIG))


@pytest.mark.parametrize("repeat_with_304", [False, True])
def test_pipeline_downloads_tuyensinh_pdfs_and_reports_unique_skips(tmp_path, repeat_with_304):
    allowlist = Allowlist.load(CONFIG)
    seeds = [HOST + "/dai-hoc", HOST + "/dai-hoc/thong-bao"]
    allowlist.seeds = seeds
    pdf = (Path(__file__).parent / "fixtures/hus/sample_text.pdf").read_bytes()
    seen = []
    phase = 1
    links = "".join(f'<a href="{HOST + path}">PDF</a>' for path in PDF_PATHS)
    links += "".join(f'<a href="{url}">Blocked</a>' for url in BLOCKED_URLS)
    html = f"<main><h1>Admissions rules</h1><p>Official documents.</p>{links}</main>"

    def handler(request):
        url = str(request.url)
        seen.append(url)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if url in seeds:
            if phase == 2:
                assert request.headers["if-none-match"] == '"page-v1"'
                return httpx.Response(304)
            return httpx.Response(200, text=html, headers={
                "content-type": "text/html", "etag": '"page-v1"',
            })
        if request.url.path in PDF_PATHS:
            if phase == 2:
                assert request.headers["if-none-match"] == '"pdf-v1"'
                return httpx.Response(304)
            return httpx.Response(200, content=pdf, headers={
                "content-type": "application/pdf", "etag": '"pdf-v1"',
            })
        raise AssertionError(f"Out-of-scope attachment was requested: {url}")

    def make_pipeline():
        return HUSPipeline(
            allowlist, RawStorage(tmp_path), ProcessedStorage(tmp_path),
            CrawlStateManager(tmp_path / "state/crawl_state.json"),
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first = make_pipeline().run(client=client, sleep=lambda _: None, max_depth=0)
        assert first.attachment_count == 2
        if repeat_with_304:
            phase = 2
            seen.clear()
            summary = make_pipeline().run(client=client, sleep=lambda _: None, max_depth=0)
            assert summary.unchanged_count == 2
            assert summary.attachment_count == 0
        else:
            summary = first

    assert summary.error_count == 0
    assert summary.skipped_attachment_count == 3
    assert set(summary.skipped_attachments) == set(BLOCKED_URLS)
    assert "outside allowlist" in summary.skipped_attachments[BLOCKED_URLS[0]]
    assert "outside allowlist" in summary.skipped_attachments[BLOCKED_URLS[1]]
    assert "excluded faculty host" in summary.skipped_attachments[BLOCKED_URLS[2]]
    for path in PDF_PATHS:
        assert seen.count(HOST + path) == 1
    assert not set(BLOCKED_URLS) & set(seen)

    raw_files = list((tmp_path / "raw/documents").glob("*.pdf"))
    assert len(raw_files) == 2
    assert all(path.read_bytes() == pdf for path in raw_files)
    catalog = json.loads((tmp_path / "processed/catalog.json").read_text(encoding="utf-8"))
    attachments = [doc for doc in catalog["documents"].values() if doc["parent_url"]]
    assert {doc["source_url"] for doc in attachments} == {HOST + path for path in PDF_PATHS}
    for doc in attachments:
        assert doc["parent_url"] == seeds[0]
        assert "Official course information" in doc["content_markdown"]
        markdown = tmp_path / "processed/documents" / f'{doc["document_id"]}.md'
        assert "Official course information" in markdown.read_text(encoding="utf-8")
