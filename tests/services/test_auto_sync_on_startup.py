"""Tests for automatic startup sync of crawled documents and review status."""
import json
from pathlib import Path

import pytest

from app.crawler.document_review_service import (
    compute_content_hash,
    get_document_review_summary,
    parse_frontmatter,
    sync_crawled_documents_and_reviews,
)
from tests.support.admin_database import db_transaction_rollback


@pytest.fixture
def isolated_db_conn():
    with db_transaction_rollback() as conn:
        yield conn


@pytest.mark.hus_postgres
def test_full_auto_sync_pipeline(isolated_db_conn, tmp_path):
    conn = isolated_db_conn
    docs_dir = Path("data/hus/processed/documents")
    assert docs_dir.is_dir()

    # Resolve actual content hashes for target seeded documents
    f1 = docs_dir / "computer_science" / "nganh-khoa-hoc-may-tinh-va-thong-tin--d6370261.md"
    f2 = docs_dir / "computer_science" / "may-tinh-va-khoa-hoc-thong-tin-clc--f8672caf.md"
    _, c1 = parse_frontmatter(f1.read_text(encoding="utf-8"))
    _, c2 = parse_frontmatter(f2.read_text(encoding="utf-8"))
    hash_1 = compute_content_hash(c1)
    hash_2 = compute_content_hash(c2)

    # Create a test reviews file with 2 specific review states
    test_reviews_file = tmp_path / "test_reviews_startup.json"
    test_reviews_file.write_text(
        json.dumps(
            {
                "doc_test_approved": {
                    "doc_id": "doc_test_approved",
                    "url": "http://mim.hus.vnu.edu.vn/vi/khmt-tt",
                    "content_hash": hash_1,
                    "title": "Ngành Khoa học máy tính và thông tin",
                    "review_status": "approved",
                    "review_reason": "Chương trình chuẩn đã kiểm duyệt",
                    "reviewed_at": "2026-11-08T00:00:00+00:00",
                },
                "doc_test_rejected": {
                    "doc_id": "doc_test_rejected",
                    "url": "http://mim.hus.vnu.edu.vn/vi/mt-khtt-clc",
                    "content_hash": hash_2,
                    "title": "Máy tính và Khoa học thông tin CLC",
                    "review_status": "rejected",
                    "review_reason": "Bản nháp trùng lặp",
                    "reviewed_at": "2026-11-08T00:00:00+00:00",
                },
            }
        ),
        encoding="utf-8",
    )

    res = sync_crawled_documents_and_reviews(
        conn, docs_dir=docs_dir, reviews_file=test_reviews_file
    )
    assert res["total"] >= 170, f"Expected at least 170 total documents, got {res['total']}"
    assert res["reviews_applied"] >= 2, f"Expected 2 applied reviews, got {res['reviews_applied']}"

    # Verify summary includes both approved and rejected
    summary = get_document_review_summary(conn)
    assert summary["total"] >= 170
    assert summary["approved"] >= 1
    assert summary["rejected"] >= 1
