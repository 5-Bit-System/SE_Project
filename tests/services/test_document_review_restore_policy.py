"""Decision/version regression tests using real sync SQL and SQLite fixtures.

PostgreSQL advisory locks are stubbed here; dedicated hus_postgres tests own
transaction/locking acceptance. No production settings or network are used.
"""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, text

from app.crawler import document_review_service as service
from tools.seed_real_crawled_documents import create_initial_git_reviews_if_empty

UID = "57e9a52b-7365-4fe2-b9ce-1320ef48dc02"
BODY = "Synthetic curriculum text long enough to pass the document content quality gate."


@pytest.fixture
def store(monkeypatch):
    monkeypatch.setattr(service, "publication_lock", lambda conn: None)
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE accounts(id TEXT PRIMARY KEY)"))
        conn.execute(text("INSERT INTO accounts VALUES (:id)"), {"id": UID})
        conn.execute(text("""CREATE TABLE crawled_documents(
            id TEXT PRIMARY KEY, url TEXT, content_hash TEXT, title TEXT,
            major TEXT, doc_type TEXT, metadata_json TEXT, markdown_content TEXT,
            review_status TEXT, review_reason TEXT, reviewer_id TEXT,
            reviewed_at TEXT, is_published BOOLEAN DEFAULT false)"""))
        yield conn
    engine.dispose()


def add(conn, did="source", *, status="pending", published=False, **overrides):
    doc = {
        "id": did, "url": "https://example.invalid/" + did,
        "content_hash": service.compute_content_hash(BODY), "title": "Original title",
        "major": "mathematics", "doc_type": "curriculum", "metadata_json": "{}",
        "markdown_content": BODY, "review_status": status, "review_reason": None,
        "reviewer_id": None, "reviewed_at": None, "is_published": published,
    }
    doc.update(overrides)
    columns = ",".join(doc)
    values = ",".join(":" + k for k in doc)
    conn.execute(text(f"INSERT INTO crawled_documents ({columns}) VALUES ({values})"), doc)
    return doc


def decision(doc, **overrides):
    data = {
        "doc_id": doc["id"], "url": doc["url"], "content_hash": doc["content_hash"],
        "review_status": "approved", "review_reason": "Reviewed synthetic source",
        "reviewer_id": UID, "reviewed_at": "2026-11-09T01:00:00+00:00",
        "review_fingerprint": service.document_review_fingerprint(doc),
    }
    data.update(overrides)
    return data


def sync(conn, tmp_path, reviews):
    empty = tmp_path / "empty"
    empty.mkdir(exist_ok=True)
    path = tmp_path / "reviews.json"
    path.write_text(json.dumps(reviews), encoding="utf-8")
    return service.sync_crawled_documents_and_reviews(conn, empty, path)


def stored(conn, did="source"):
    return dict(conn.execute(text("SELECT * FROM crawled_documents WHERE id=:id"),
                             {"id": did}).mappings().one())


def test_restore_exact_version_into_untouched_draft_and_replay_is_noop(store, tmp_path):
    doc = add(store)
    snapshot = {doc["id"]: decision(doc)}
    first = sync(store, tmp_path, snapshot)
    after = stored(store)
    assert first["reviews_applied"] == 1
    assert after["review_status"] == "approved" and after["reviewer_id"] == UID
    second = sync(store, tmp_path, snapshot)
    assert second["reviews_applied"] == 0
    assert stored(store) == after


@pytest.mark.parametrize("published", [False, True])
def test_old_review_does_not_approve_metadata_replacement(store, tmp_path, published):
    old = add(store, status="approved", published=published, reviewer_id=UID,
              reviewed_at="2026-11-09T01:00:00+00:00", review_reason="Old decision")
    replacement = add(store, "replacement", url=old["url"], major="data_science",
                      metadata_json='{"previous_document_id":"source","version":2}')
    before = stored(store, replacement["id"])
    result = sync(store, tmp_path, {old["id"]: decision(old)})
    assert result["reviews_applied"] == 0
    assert stored(store, "replacement") == before


def test_url_does_not_resolve_missing_old_version_id(store, tmp_path):
    replacement = add(store, "replacement")
    old = dict(replacement, id="old_source")
    result = sync(store, tmp_path, {old["id"]: decision(old)})
    assert result["version_mismatches"] == 1
    assert stored(store, "replacement")["review_status"] == "pending"


@pytest.mark.parametrize("change", [
    {"title": "Changed"}, {"major": "data_science"},
    {"doc_type": "regulation"}, {"metadata_json": '{"cohort":2023}'},
])
def test_fingerprint_rejects_unreviewed_metadata_at_same_id(store, tmp_path, change):
    doc = add(store)
    snapshot = decision(doc)
    store.execute(text("UPDATE crawled_documents SET " + ",".join(k + "=:" + k for k in change)
                       + " WHERE id='source'"), change)
    result = sync(store, tmp_path, {doc["id"]: snapshot})
    assert result["version_mismatches"] == 1
    assert stored(store)["review_status"] == "pending"


@pytest.mark.parametrize("existing", [
    {"review_status": "rejected", "reviewer_id": UID, "review_reason": "Newer rejection",
     "reviewed_at": "2026-11-09T02:00:00+00:00"},
    {"review_status": "pending", "review_reason": "Explicit revocation"},
    {"review_status": "pending", "reviewed_at": "2026-11-09T02:00:00+00:00"},
])
def test_stale_file_after_failed_export_never_overwrites_database(store, tmp_path, existing):
    doc = add(store, **existing)
    before = stored(store)
    result = sync(store, tmp_path, {doc["id"]: decision(doc)})
    assert result["skipped_existing_decisions"] == 1
    assert stored(store) == before


@pytest.mark.parametrize("missing", ["reviewer_id", "reviewed_at", "review_fingerprint", "review_reason"])
def test_incomplete_legacy_review_cannot_authorize_approval(store, tmp_path, missing):
    doc = add(store)
    data = decision(doc)
    del data[missing]
    result = sync(store, tmp_path, {doc["id"]: data})
    assert result["reviews_applied"] == 0
    assert stored(store)["review_status"] == "pending"
    assert stored(store)["reviewed_at"] is None


@pytest.mark.parametrize("timestamp", ["invalid", "2026-11-09T01:00:00", 42])
def test_invalid_or_naive_review_timestamp_is_not_replaced_with_now(store, tmp_path, timestamp):
    doc = add(store)
    result = sync(store, tmp_path, {doc["id"]: decision(doc, reviewed_at=timestamp)})
    assert result["invalid_review_evidence"] == 1
    assert stored(store)["reviewed_at"] is None


def test_export_initializer_and_sync_preserve_small_review_snapshot(store, tmp_path):
    add(store, status="approved", reviewer_id=UID,
              reviewed_at="2026-11-09T01:00:00+00:00", review_reason="Original decision")
    before = stored(store)
    path = tmp_path / "reviews.json"
    service.export_git_reviews_from_db(store, path)
    exported = path.read_bytes()
    empty = tmp_path / "empty"
    empty.mkdir()
    create_initial_git_reviews_if_empty(empty, path)
    assert path.read_bytes() == exported
    result = service.sync_crawled_documents_and_reviews(store, empty, path)
    assert result["reviews_applied"] == 0
    assert stored(store) == before


def test_pending_snapshot_never_revokes_database_approval(store, tmp_path):
    doc = add(store, status="approved", reviewer_id=UID, review_reason="Original")
    before = stored(store)
    sync(store, tmp_path, {doc["id"]: decision(doc, review_status="pending")})
    assert stored(store) == before


@pytest.mark.parametrize("published", [False, True])
def test_sync_never_cleans_sources_based_on_url_substrings(store, tmp_path, published):
    doc = add(store, url="https://example.invalid/cntt-2022/dummy-real-curriculum",
              status="approved", published=published, reviewer_id=UID,
              reviewed_at="2026-11-09T01:00:00+00:00", review_reason="Real decision")
    before = stored(store)
    sync(store, tmp_path, {doc["id"]: decision(doc)})
    assert stored(store) == before


def test_export_fingerprint_binds_reviewed_version_metadata(store, tmp_path):
    doc = add(store, status="approved", reviewer_id=UID,
              reviewed_at="2026-11-09T01:00:00+00:00", review_reason="Original")
    path = tmp_path / "export.json"
    service.export_git_reviews_from_db(store, path)
    review = json.loads(path.read_text(encoding="utf-8"))[doc["id"]]
    assert review["review_fingerprint"] == service.document_review_fingerprint(doc)
    assert review["review_fingerprint"] != service.document_review_fingerprint(dict(doc, major="data_science"))


def test_fingerprint_canonicalizes_json_metadata():
    doc = {"id": "one", "metadata_json": {"b": 2, "a": 1}}
    other = {"id": "one", "metadata_json": '{"a":1,"b":2}'}
    assert service.document_review_fingerprint(doc) == service.document_review_fingerprint(other)


def test_fingerprint_export_mock_remains_compatible_with_atomic_file_retries(tmp_path):
    conn = MagicMock()
    row = MagicMock()
    row._mapping = {
        "id": "source", "url": "https://example.invalid/source", "content_hash": "hash",
        "title": "Source", "major": "mathematics", "doc_type": "curriculum",
        "metadata_json": {}, "review_status": "approved", "reviewer_id": UID,
        "review_reason": "Reviewed", "reviewed_at": datetime(2026, 11, 9, tzinfo=timezone.utc),
    }
    conn.execute.return_value.fetchall.return_value = [row]
    assert service.export_git_reviews_from_db(conn, tmp_path / "export.json") == 1
