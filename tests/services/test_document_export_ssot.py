"""Tests for PostgreSQL pure Single Source of Truth (SSOT) review export and concurrency serialization (Issue #143)."""

import concurrent.futures
import json
from pathlib import Path

import pytest
from sqlalchemy import text

from app.crawler.document_review_service import (
    create_document,
    export_git_reviews_from_db,
    review_document,
)
from tests.support.admin_database import admin_test_engine, db_transaction_rollback


@pytest.fixture
def isolated_db_conn():
    with db_transaction_rollback() as conn:
        yield conn


@pytest.mark.hus_postgres
def test_export_purges_revoked_or_pending_documents(isolated_db_conn, tmp_path: Path):
    """Purge revoked or pending documents from JSON export file (Pure SSOT from DB)."""
    conn = isolated_db_conn
    test_json = tmp_path / "reviews.json"

    doc_keep = create_document(
        conn,
        url="https://hus.vnu.edu.vn/doc-keep-ssot-test",
        title="Tài liệu giữ lại đạt chuẩn chất lượng",
        markdown_content="Đây là nội dung hợp lệ có độ dài lớn hơn năm mươi ký tự cho tài liệu giữ lại",
        major="computer_science",
    )
    doc_revoke = create_document(
        conn,
        url="https://hus.vnu.edu.vn/doc-revoke-ssot-test",
        title="Tài liệu bị thu hồi sau khi duyệt",
        markdown_content="Đây là nội dung hợp lệ có độ dài lớn hơn năm mươi ký tự cho tài liệu thu hồi",
        major="computer_science",
    )

    valid_reviewer = "57e9a52b-7365-4fe2-b9ce-1320ef48dc02"
    review_document(
        conn,
        doc_keep["id"],
        decision="approved",
        reason="Phê duyệt chuẩn",
        reviewer_id=valid_reviewer,
    )
    review_document(
        conn,
        doc_revoke["id"],
        decision="approved",
        reason="Phê duyệt chuẩn lần đầu",
        reviewer_id=valid_reviewer,
    )

    # Pre-populate test JSON containing both documents
    initial_reviews = {
        doc_keep["id"]: {
            "doc_id": doc_keep["id"],
            "url": doc_keep["url"],
            "content_hash": doc_keep["content_hash"],
            "title": doc_keep["title"],
            "review_status": "approved",
            "review_reason": "Phê duyệt chuẩn",
            "reviewer_id": valid_reviewer,
            "reviewed_at": "2026-11-09T00:00:00",
        },
        doc_revoke["id"]: {
            "doc_id": doc_revoke["id"],
            "url": doc_revoke["url"],
            "content_hash": doc_revoke["content_hash"],
            "title": doc_revoke["title"],
            "review_status": "approved",
            "review_reason": "Phê duyệt chuẩn lần đầu",
            "reviewer_id": valid_reviewer,
            "reviewed_at": "2026-11-09T00:00:00",
        },
    }
    test_json.write_text(json.dumps(initial_reviews, ensure_ascii=False, indent=2), encoding="utf-8")

    # Now update doc_revoke in DB to pending with no reviewer
    conn.execute(
        text("""
            UPDATE crawled_documents
            SET review_status = 'pending', reviewer_id = NULL, review_reason = 'Thu hồi về chờ duyệt'
            WHERE id = :id
        """),
        {"id": doc_revoke["id"]},
    )

    count = export_git_reviews_from_db(conn, file_path=test_json)
    assert count >= 1

    exported = json.loads(test_json.read_text(encoding="utf-8"))
    assert doc_keep["id"] in exported
    assert doc_revoke["id"] not in exported
    assert exported[doc_keep["id"]]["review_status"] == "approved"


@pytest.mark.hus_postgres
def test_export_never_includes_unverified_approved_rows(isolated_db_conn, tmp_path: Path):
    """Never export approved rows missing a reviewer (orphan approvals)."""
    conn = isolated_db_conn
    test_json = tmp_path / "reviews.json"

    orphan_id = "doc_orphan_approved_test"
    conn.execute(
        text("""
            INSERT INTO crawled_documents (
                id, url, title, markdown_content, content_hash, doc_type, major, review_status, review_reason, reviewer_id
            ) VALUES (
                :id, 'https://hus.vnu.edu.vn/orphan-test', 'Tài liệu mồ côi',
                'Nội dung tài liệu mồ côi không có reviewer với độ dài hơn năm mươi ký tự',
                'hash_orphan_123', 'curriculum', 'computer_science', 'approved', 'Duyệt thiếu reviewer', NULL
            )
        """),
        {"id": orphan_id},
    )

    export_git_reviews_from_db(conn, file_path=test_json)

    assert test_json.is_file()
    exported = json.loads(test_json.read_text(encoding="utf-8"))
    assert orphan_id not in exported


@pytest.mark.hus_postgres
def test_export_concurrent_serialization_lock(tmp_path: Path):
    """Ensure concurrent export calls serialize safely via module lock without data corruption."""
    eng = admin_test_engine()
    test_json = tmp_path / "reviews.json"

    # Pre-populate test_json with initial valid JSON
    test_json.write_text("{}", encoding="utf-8")

    def run_export():
        return export_git_reviews_from_db(eng, file_path=test_json)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_export) for _ in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 5
    assert all(isinstance(r, int) for r in results)

    # Verify JSON file is valid and readable
    assert test_json.is_file()
    data = json.loads(test_json.read_text(encoding="utf-8"))
    assert isinstance(data, dict)

    # No leftover .tmp files
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0
