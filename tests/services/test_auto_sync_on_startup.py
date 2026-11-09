"""Tests for automatic startup sync of crawled documents and review status."""
import json
from pathlib import Path

import pytest
from sqlalchemy import text

from app.crawler.document_review_service import (
    get_document,
    get_document_review_summary,
    seed_crawled_documents_from_disk,
    sync_crawled_documents_and_reviews,
)
from tests.support.admin_database import db_transaction_rollback
from tests.support.document_reviews import snapshot_decision


@pytest.fixture
def isolated_db_conn():
    with db_transaction_rollback() as conn:
        yield conn


@pytest.mark.hus_postgres
def test_full_auto_sync_pipeline(isolated_db_conn, tmp_path):
    conn = isolated_db_conn
    docs_dir = Path("data/hus/processed/documents")
    assert docs_dir.is_dir()

    urls = ["http://mim.hus.vnu.edu.vn/vi/khmt-tt", "http://mim.hus.vnu.edu.vn/vi/mt-khtt-clc"]
    for url in urls:
        conn.execute(text("DELETE FROM crawled_documents WHERE url=:url"), {"url": url})
    seed_crawled_documents_from_disk(conn, docs_dir)
    reviews = {}
    for url, status in zip(urls, ("approved", "rejected")):
        did = conn.execute(text("SELECT id FROM crawled_documents WHERE url=:url"), {"url": url}).scalar_one()
        reviews[did] = snapshot_decision(get_document(conn, did), status)

    test_reviews_file = tmp_path / "test_reviews_startup.json"
    test_reviews_file.write_text(json.dumps(reviews), encoding="utf-8")

    res = sync_crawled_documents_and_reviews(
        conn, docs_dir=docs_dir, reviews_file=test_reviews_file
    )
    assert res["total"] >= 170, f"Expected at least 170 total documents, got {res['total']}"
    assert res["reviews_applied"] == 2

    # Verify summary includes both approved and rejected
    summary = get_document_review_summary(conn)
    assert summary["total"] >= 170
    assert summary["approved"] >= 1
    assert summary["rejected"] >= 1
    # Existing decisions are authoritative on a repeated startup.
    assert sync_crawled_documents_and_reviews(
        conn, docs_dir, test_reviews_file,
    )["reviews_applied"] == 0
