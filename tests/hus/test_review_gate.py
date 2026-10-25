"""All export paths fail closed; withdrawn approvals cannot preserve cached chunks."""

from datetime import date
import hashlib
import json

import pytest

from app.hus.index import HUSIndex, chunk_document
from app.hus.models import DocumentStatus, HUSDocument, ReviewDecision
from tests.hus_review_fixtures import approved_review
from tools.build_hus_index import main as legacy_main


@pytest.fixture
def reviewed():
    content = "# Synthetic document\nInvented facts for a test, not academic source data."
    doc = HUSDocument(
        url="https://mim.hus.vnu.edu.vn/vi/synthetic-review", title="Synthetic document",
        content=content, content_hash=hashlib.sha256(content.encode()).hexdigest(),
        fetched_at="2026-10-26T00:00:00Z",
    )
    raw = b"<article>Synthetic original for tests only.</article>"
    return doc, raw, approved_review(doc, raw)


def test_direct_chunking_and_index_need_explicit_review(reviewed, tmp_path):
    doc, raw, _ = reviewed
    with pytest.raises(ValueError, match="Missing review"):
        chunk_document(doc, raw=raw)
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw")
    with pytest.raises(ValueError, match="Missing review"):
        index.add(doc, raw)
    index.save()
    assert json.loads(index.path.read_text())["documents"] == {}


@pytest.mark.parametrize("status", ["pending_ocr", "superseded", "archived"])
def test_inactive_document_revokes_chunks_even_when_text_is_unchanged(reviewed, tmp_path, status):
    doc, raw, review = reviewed
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw")
    index.add(doc, raw, review=review)
    index.save()
    withdrawn = doc.model_copy(update={"status": DocumentStatus(status)})
    with pytest.raises(ValueError, match="Only active"):
        chunk_document(withdrawn, review=review, raw=raw)
    with pytest.raises(ValueError, match="Only active"):
        index.add(withdrawn, raw, review=review)
    assert doc.url not in index.documents
    index.save()
    assert json.loads(index.path.read_text())["documents"] == {}


@pytest.mark.parametrize("status", ["needs_review", "pending_ocr", "exclude"])
def test_revoked_decision_is_removed_on_save_and_reload(reviewed, tmp_path, status):
    doc, raw, review = reviewed
    reviews = {doc.url: review}
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw", reviews=reviews)
    index.add(doc, raw)
    index.save()
    reviews[doc.url] = review.model_copy(update={"status": status})
    reloaded = HUSIndex(index.path, index.raw_dir, reviews=reviews)
    assert reloaded.documents == {}
    index.save()
    assert json.loads(index.path.read_text())["documents"] == {}


def test_cached_review_is_not_authority_and_missing_decision_removes_record(reviewed, tmp_path):
    doc, raw, review = reviewed
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw")
    index.add(doc, raw, review=review)
    index.save()
    assert HUSIndex(index.path, index.raw_dir).documents == {}
    index.reviews.clear()
    index.save()
    assert json.loads(index.path.read_text())["documents"] == {}


def test_cached_chunks_are_regenerated_and_tampered_raw_is_rejected(reviewed, tmp_path):
    doc, raw, review = reviewed
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw")
    index.add(doc, raw, review=review)
    index.documents[doc.url]["chunks"][0]["text"] = "Injected unreviewed text"
    index.save()
    assert "Injected" not in index.path.read_text(encoding="utf-8")
    raw_file = index.raw_dir / index.documents[doc.url]["raw_file"]
    raw_file.write_bytes(b"Changed original")
    index.save()
    assert json.loads(index.path.read_text())["documents"] == {}


@pytest.mark.parametrize("update", [
    {"reviewed_at": None}, {"reviewed_at": "2026-10-26T00:00:00"},
    {"reviewer": " "}, {"reason": " "}, {"evidence_locator": " "},
    {"reviewed_source_sha256": "0" * 64}, {"content_hash": "0" * 64},
    {"source_url": "https://mim.hus.vnu.edu.vn/vi/different-source"},
    {"review_scope": "section"},
    {"validity_status": "current_verified"}, {"usage_scope": "current"},
    {"effective_from": "2026-10-27", "effective_to": "2026-10-26"},
])
def test_incomplete_or_stale_evidence_never_exports(reviewed, tmp_path, update):
    doc, raw, review = reviewed
    bad = review.model_copy(update=update)
    with pytest.raises(ValueError):
        chunk_document(doc, raw=raw, review=bad)
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw")
    with pytest.raises(ValueError):
        index.add(doc, raw, review=bad)
    index.save()
    assert index.documents == {}


def test_current_validity_is_evidence_bound_and_checked_at_explicit_date(reviewed):
    doc, raw, review = reviewed
    current = ReviewDecision.model_validate({
        **review.model_dump(), "usage_scope": "current", "validity_status": "current_verified",
        "validity_evidence_locator": "Synthetic section on effective dates",
        "effective_from": "2026-10-26", "effective_to": "2026-10-27",
    })
    chunk = chunk_document(doc, raw=raw, review=current, as_of=date(2026, 10, 26))[0]
    assert chunk.review_as_of == "2026-10-26"
    for as_of in (None, date(2026, 10, 25), date(2026, 10, 28)):
        with pytest.raises(ValueError):
            chunk_document(doc, raw=raw, review=current, as_of=as_of)
    no_start = current.model_copy(update={"effective_from": None})
    with pytest.raises(ValueError, match="effective_from"):
        chunk_document(doc, raw=raw, review=no_start, as_of=date(2026, 10, 26))


def test_unknown_validity_stays_descriptive_and_never_becomes_current(reviewed):
    doc, raw, review = reviewed
    result = chunk_document(doc, raw=raw, review=review)[0]
    assert result.review_status == "include"
    assert result.review.validity_status == "unknown"
    assert result.review.usage_scope == "descriptive"


def test_effective_date_order_uses_dates_not_string_formats(reviewed):
    _, _, review = reviewed
    with pytest.raises(ValueError, match="precedes"):
        ReviewDecision.model_validate({
            **review.model_dump(), "effective_from": "2026-10-28", "effective_to": "20261027",
        })


def test_legacy_cli_cannot_crawl_into_an_unreviewed_index(tmp_path, monkeypatch, capsys):
    config = tmp_path / "allowlist.json"
    config.write_text(json.dumps({"sources": [{
        "host": "mim.hus.vnu.edu.vn", "path_prefixes": ["/vi"],
        "seeds": ["https://mim.hus.vnu.edu.vn/vi/synthetic"],
    }]}))
    def forbidden(*args, **kwargs):
        raise AssertionError("Legacy export must fail before calling the crawler")

    monkeypatch.setattr("app.hus.crawler.crawl", forbidden)
    out = tmp_path / "out"
    assert legacy_main(["--allowlist", str(config), "--out", str(out)]) == 1
    assert "disabled" in capsys.readouterr().err
    assert not out.exists()


def test_expired_current_review_is_removed_from_saved_index(reviewed, tmp_path):
    doc, raw, review = reviewed
    review = ReviewDecision.model_validate({
        **review.model_dump(), "usage_scope": "current", "validity_status": "current_verified",
        "validity_evidence_locator": "Synthetic dates", "effective_from": "2026-10-26",
        "effective_to": "2026-10-27",
    })
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw", as_of=date(2026, 10, 26))
    index.add(doc, raw, review=review)
    index.save()
    index.as_of = date(2026, 10, 28)
    index.save()
    assert json.loads(index.path.read_text())["documents"] == {}
