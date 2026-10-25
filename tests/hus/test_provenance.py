"""Immutable originals, explicit recovery blockers, and raw-aware HTTP validators."""

import hashlib
import json
from pathlib import Path

import httpx
import pytest

from app.hus.allowlist import Allowlist
from app.hus.extractors.pdf import extract_pdf
from app.hus.models import HUSDocument
from app.hus.pipeline import HUSPipeline
from app.hus.provenance import RawArchive, document_id_for
from app.hus.state import CrawlStateManager
from app.hus.storage import ProcessedStorage, RawStorage
from app.hus.urls import CrawlError
from tools.recover_hus_sources import recover


HOST = "https://mim.hus.vnu.edu.vn"


@pytest.mark.parametrize("kind", ["html", "pdf"])
def test_raw_versions_and_capture_history_are_independent(tmp_path, kind):
    store = RawStorage(tmp_path)
    url = HOST + "/vi/source." + kind
    def save(raw):
        if kind == "html":
            return store.save_raw_html(url, raw, fetched_at="2026-10-26T00:00:00Z")
        return store.save_raw_document(url, raw, "pdf", fetched_at="2026-10-26T00:00:00Z")

    first, second = save(b"first bytes\r\n"), save(b"second bytes\n")
    assert first != second
    assert first.read_bytes() == b"first bytes\r\n"
    assert second.read_bytes() == b"second bytes\n"
    assert save(b"second bytes\n") == second
    events = RawArchive(tmp_path).events()
    assert len(events) == 3
    assert len({e.event_id for e in events}) == 3
    assert {e.document_id for e in events} == {document_id_for(url)}
    assert {e.reference.fetched_at for e in events} == {"2026-10-26T00:00:00Z"}
    for event in events:
        ref = event.reference
        assert ref.raw_sha256 in ref.raw_path
        assert ref.raw_sha256 == hashlib.sha256((tmp_path / ref.raw_path).read_bytes()).hexdigest()
        assert ref.file_type == kind


def test_latest_never_falls_back_to_an_older_version(tmp_path):
    store = RawStorage(tmp_path)
    url = HOST + "/vi/source"
    first = store.save_raw_html(url, b"v1")
    second = store.save_raw_html(url, b"v2")
    second.unlink()
    assert first.exists()
    assert store.archive.latest(url) is None
    store.save_raw_html(url, b"v2")
    assert store.archive.latest(url).raw_sha256 == hashlib.sha256(b"v2").hexdigest()


def test_corrupt_immutable_blob_and_ledger_are_not_overwritten(tmp_path):
    store = RawStorage(tmp_path)
    url = HOST + "/vi/source"
    path = store.save_raw_html(url, b"v1")
    path.write_bytes(b"corrupted")
    with pytest.raises(CrawlError, match="Corrupted immutable"):
        store.save_raw_html(url, b"v1")
    assert path.read_bytes() == b"corrupted"
    ledger = store.archive.ledger_path
    ledger.write_bytes(b"broken history")
    with pytest.raises(CrawlError, match="ledger"):
        store.save_raw_html(url, b"v2")
    assert ledger.read_bytes() == b"broken history"


def make_pipeline(root):
    rules = Allowlist([{"host": "mim.hus.vnu.edu.vn", "path_prefixes": ["/vi", "/files"],
                        "seeds": [HOST + "/vi/seed"]}], delay_seconds=0, retry_attempts=1)
    return HUSPipeline(rules, RawStorage(root), ProcessedStorage(root),
                       CrawlStateManager(root / "state/crawl_state.json"))


@pytest.mark.parametrize("missing_kind", ["html", "pdf"])
def test_missing_original_is_refetched_without_validators(tmp_path, missing_kind):
    pdf = (Path(__file__).resolve().parents[1] / "fixtures/hus/sample_text.pdf").read_bytes()
    html = '<main><h1>Seed</h1><a href="/files/original.pdf">File</a></main>'
    phase, requests = 1, []
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        kind = "pdf" if request.url.path.endswith(".pdf") else "html"
        validator = request.headers.get("if-none-match")
        requests.append((kind, validator))
        if phase == 2 and kind != missing_kind:
            assert validator == f'"{kind}"'
            return httpx.Response(304)
        assert validator is None
        return httpx.Response(200, content=pdf if kind == "pdf" else html.encode(),
                              headers={"etag": f'"{kind}"', "content-type":
                                       "application/pdf" if kind == "pdf" else "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first = make_pipeline(tmp_path)
        assert first.run(client=client).error_count == 0
        archive = first.raw_storage.archive
        url = HOST + ("/files/original.pdf" if missing_kind == "pdf" else "/vi/seed")
        raw_path = tmp_path / archive.latest(url).raw_path
        raw_path.unlink()
        phase = 2
        requests.clear()
        second = make_pipeline(tmp_path)
        result = second.run(client=client)
    assert result.error_count == 0
    assert (missing_kind, None) in requests
    assert raw_path.exists()
    catalog = json.loads((tmp_path / "processed/catalog.json").read_text(encoding="utf-8"))
    for doc in catalog["documents"].values():
        ref = doc["raw_source"]
        assert ref["document_id"] == doc["document_id"]
        assert (tmp_path / ref["raw_path"]).is_file()
    parent = next(d for d in catalog["documents"].values() if d["source_url"].endswith("seed"))
    assert parent["attachments"][0]["raw_path"]


def test_304_without_original_or_body_is_a_persisted_blocker(tmp_path):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        assert "if-none-match" not in request.headers
        return httpx.Response(304)

    pipeline = make_pipeline(tmp_path)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = pipeline.run(client=client)
    assert result.error_count == 1
    assert "cached document" in result.source_blockers[HOST + "/vi/seed"]
    event = pipeline.raw_storage.archive.events()[-1]
    assert event.kind == "failed" and event.reason


def test_unavailable_attachment_records_failure_and_keeps_parent(tmp_path):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path.endswith(".pdf"):
            return httpx.Response(404)
        return httpx.Response(200, text='<main><h1>Seed</h1><a href="/files/missing.pdf">PDF</a></main>',
                              headers={"content-type": "text/html"})

    pipeline = make_pipeline(tmp_path)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = pipeline.run(client=client)
    assert result.error_count == 1
    assert HOST + "/files/missing.pdf" in result.source_blockers
    assert pipeline.raw_storage.archive.events()[-1].kind == "failed"
    assert len(pipeline.processed_storage.documents) == 1


def test_304_attachment_without_raw_is_retried_and_persisted_as_blocked(tmp_path):
    seen = []
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path.endswith(".pdf"):
            seen.append(request.headers.get("if-none-match"))
            return httpx.Response(304)
        return httpx.Response(200, text='<main><h1>Seed</h1><a href="/files/empty.pdf">PDF</a></main>',
                              headers={"content-type": "text/html"})
    pipeline = make_pipeline(tmp_path)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = pipeline.run(client=client)
    assert seen == [None, None]
    assert result.error_count == 1
    assert "304" in result.source_blockers[HOST + "/files/empty.pdf"]
    assert pipeline.raw_storage.archive.events()[-1].kind == "failed"


def test_new_snapshot_uses_explicit_raw_reference_not_filename_guessing(tmp_path):
    from app.hus.corpus import create_source_manifest, verify_sources

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, text='<main><h1>Seed</h1><p>Source content.</p></main>',
                              headers={"content-type": "text/html"})
    pipeline = make_pipeline(tmp_path)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert pipeline.run(client=client).error_count == 0
    manifest = create_source_manifest(tmp_path, "synthetic", "fixture://synthetic")
    docs = verify_sources(tmp_path, manifest)
    ref = next(iter(docs.values())).raw_source
    assert manifest.documents[ref.document_id].raw_path == ref.raw_path
    raw_file = next(f for f in manifest.files if f.path == ref.raw_path)
    assert raw_file.encoding == "binary" and raw_file.sha256 == ref.raw_sha256


def test_local_recovery_compares_text_but_does_not_approve_or_guess_fetch_time(tmp_path):
    pdf = (Path(__file__).resolve().parents[1] / "fixtures/hus/sample_text.pdf").read_bytes()
    text, _ = extract_pdf(pdf)
    storage = ProcessedStorage(tmp_path)
    for url, content in [(HOST + "/files/found.pdf", text), (HOST + "/files/missing.docx", "Unknown")]:
        storage.save_document(HUSDocument(
            url=url, title="Synthetic input", content=content,
            content_hash=hashlib.sha256(content.strip().encode()).hexdigest(),
            fetched_at="2026-10-26T00:00:00Z",
        ))
    storage.commit()
    catalog_before = storage.catalog_path.read_bytes()
    digest = hashlib.sha256(pdf).hexdigest()
    source = tmp_path / "old-capture" / ("source-" + digest[:12] + ".pdf")
    source.parent.mkdir()
    source.write_bytes(pdf)
    candidate_manifest = tmp_path / "candidates.json"
    candidate_manifest.write_text(json.dumps([{
        "final_url": HOST + "/files/found.pdf", "raw_path": str(source), "bytes": len(pdf),
    }]))
    out = tmp_path / "report"
    report = recover(tmp_path, candidate_manifest, out)
    assert report["recovered_candidates"] == report["queued_missing_sources"] == 1
    assert report["verified_original_versions"] == report["academic_review_completed"] == 0
    rows = [json.loads(line) for line in (out / "inventory.jsonl").read_text().splitlines()]
    found = next(row for row in rows if row["status"] == "recovered_candidate")
    assert found["exact_extracted_text_match"] is True
    assert found["expected_original_sha256"] is found["original_fetched_at"] is None
    assert found["version_status"] == "unverified"
    assert (tmp_path / found["raw_path"]).read_bytes() == pdf
    assert RawArchive(tmp_path).events()[-1].reference.fetched_at is None
    assert storage.catalog_path.read_bytes() == catalog_before
    with pytest.raises(ValueError, match="already exists"):
        recover(tmp_path, candidate_manifest, out)
