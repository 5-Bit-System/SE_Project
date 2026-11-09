"""Tests for reviewer verification and sync content/reviewer gates (Issue #142)."""

import json

import pytest

from app.crawler.document_review_service import (
    create_document,
    get_document,
    review_document,
    sync_crawled_documents_and_reviews,
)
from tests.support.admin_database import db_transaction_rollback


@pytest.fixture
def isolated_db_conn():
    with db_transaction_rollback() as conn:
        yield conn


@pytest.mark.hus_postgres
def test_review_document_raises_if_reviewer_missing_or_invalid_on_approved(isolated_db_conn):
    conn = isolated_db_conn
    doc = create_document(
        conn,
        url="https://hus.vnu.edu.vn/test-review-gate-doc",
        title="Tài liệu có nội dung chuẩn trên 50 ký tự",
        markdown_content="Đây là nội dung tài liệu chuẩn có độ dài lớn hơn năm mươi ký tự để kiểm tra reviewer gate",
        major="computer_science",
    )
    doc_id = doc["id"]

    expected_msg = (
        r"Phê duyệt tài liệu bắt buộc phải có tài khoản người duyệt \(reviewer\) hợp lệ trong hệ thống\."
    )

    # Missing reviewer (None)
    with pytest.raises(ValueError, match=expected_msg):
        review_document(conn, doc_id, decision="approved", reason="Hợp lệ", reviewer_id=None)

    # Invalid reviewer (not in accounts)
    with pytest.raises(ValueError, match=expected_msg):
        review_document(
            conn,
            doc_id,
            decision="approved",
            reason="Hợp lệ",
            reviewer_id="00000000-0000-0000-0000-000000000000",
        )


@pytest.mark.hus_postgres
def test_sync_rejects_approved_on_marker_only_document(isolated_db_conn, tmp_path):
    conn = isolated_db_conn
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    reviews_file = tmp_path / "reviews.json"

    doc = create_document(
        conn,
        url="https://hus.vnu.edu.vn/test-marker-sync-gate",
        title="Tài liệu scan marker only",
        markdown_content="<!-- page 1 -->\n<!-- page 2 -->",
        major="computer_science",
    )
    doc_id = doc["id"]

    reviews = {
        doc_id: {
            "doc_id": doc_id,
            "url": doc["url"],
            "content_hash": doc["content_hash"],
            "review_status": "approved",
            "review_reason": "ok",
            "reviewer_id": "57e9a52b-7365-4fe2-b9ce-1320ef48dc02",
        }
    }
    reviews_file.write_text(json.dumps(reviews, ensure_ascii=False), encoding="utf-8")

    res = sync_crawled_documents_and_reviews(conn, docs_dir=docs_dir, reviews_file=reviews_file)

    stored = get_document(conn, doc_id)
    assert stored is not None
    assert stored["review_status"] == "pending"
    assert res.get("skipped_marker_only", 0) >= 1


@pytest.mark.hus_postgres
def test_sync_rejects_approved_when_reviewer_not_in_accounts(isolated_db_conn, tmp_path):
    conn = isolated_db_conn
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    reviews_file = tmp_path / "reviews.json"

    doc = create_document(
        conn,
        url="https://hus.vnu.edu.vn/test-invalid-reviewer-sync-gate",
        title="Tài liệu có nội dung đầy đủ hợp lệ",
        markdown_content="Đây là văn bản tài liệu hợp lệ có độ dài vượt mức tối thiểu năm mươi ký tự",
        major="computer_science",
    )
    doc_id = doc["id"]

    reviews = {
        doc_id: {
            "doc_id": doc_id,
            "url": doc["url"],
            "content_hash": doc["content_hash"],
            "review_status": "approved",
            "review_reason": "ok",
            "reviewer_id": "00000000-0000-0000-0000-000000000000",
        }
    }
    reviews_file.write_text(json.dumps(reviews, ensure_ascii=False), encoding="utf-8")

    res = sync_crawled_documents_and_reviews(conn, docs_dir=docs_dir, reviews_file=reviews_file)

    stored = get_document(conn, doc_id)
    assert stored is not None
    assert stored["review_status"] == "pending"
    assert res.get("skipped_unverified_approvals", 0) >= 1


@pytest.mark.hus_postgres
def test_sync_applies_approved_when_content_and_reviewer_are_valid(isolated_db_conn, tmp_path):
    conn = isolated_db_conn
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    reviews_file = tmp_path / "reviews.json"

    doc = create_document(
        conn,
        url="https://hus.vnu.edu.vn/test-valid-sync-gate",
        title="Tài liệu nội dung và reviewer hợp lệ",
        markdown_content="Nội dung chương trình đào tạo chuẩn bậc cử nhân đã được rà soát và kiểm định đầy đủ",
        major="computer_science",
    )
    doc_id = doc["id"]

    reviews = {
        doc_id: {
            "doc_id": doc_id,
            "url": doc["url"],
            "content_hash": doc["content_hash"],
            "review_status": "approved",
            "review_reason": "ok",
            "reviewer_id": "57e9a52b-7365-4fe2-b9ce-1320ef48dc02",
        }
    }
    reviews_file.write_text(json.dumps(reviews, ensure_ascii=False), encoding="utf-8")

    res = sync_crawled_documents_and_reviews(conn, docs_dir=docs_dir, reviews_file=reviews_file)

    stored = get_document(conn, doc_id)
    assert stored is not None
    assert stored["review_status"] == "approved"
    assert res.get("reviews_applied", 0) >= 1
