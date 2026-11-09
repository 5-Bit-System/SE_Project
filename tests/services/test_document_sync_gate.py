"""Tests for reviewer verification and sync content/reviewer gates (Issue #142)."""

import json

import pytest
from sqlalchemy import text

from app.crawler.document_review_service import (
    compute_content_hash,
    create_document,
    export_git_reviews_from_db,
    get_document,
    review_document,
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

    # Restore requires complete evidence bound to this exact source version.
    reviews_file.write_text(json.dumps({doc_id: snapshot_decision(doc)}), encoding="utf-8")

    res = sync_crawled_documents_and_reviews(conn, docs_dir=docs_dir, reviews_file=reviews_file)

    stored = get_document(conn, doc_id)
    assert stored is not None
    assert stored["review_status"] == "approved"
    assert res.get("reviews_applied", 0) >= 1


@pytest.mark.hus_postgres
def test_seed_sync_pipeline_when_file_content_hash_diverges(isolated_db_conn, tmp_path):
    conn = isolated_db_conn
    docs_dir = tmp_path / "documents" / "mathematics"
    docs_dir.mkdir(parents=True, exist_ok=True)
    doc_file = docs_dir / "test_hash_divergence.md"

    file_content_v1 = (
        "---\n"
        'title: "Chương trình kiểm thử đổi hash"\n'
        'url: "http://mim.hus.vnu.edu.vn/vi/test-hash-divergence"\n'
        'major: "mathematics"\n'
        "---\n"
        "Nội dung phiên bản A ban đầu đạt chuẩn độ dài tối thiểu lớn hơn 50 ký tự."
    )
    doc_file.write_text(file_content_v1, encoding="utf-8")

    # Clean up any leftover row with same url
    conn.execute(
        text("DELETE FROM crawled_documents WHERE url = 'http://mim.hus.vnu.edu.vn/vi/test-hash-divergence'")
    )

    # Seed into DB using seed_crawled_documents_from_disk
    seed_count = seed_crawled_documents_from_disk(conn, base_dir=tmp_path / "documents")
    assert seed_count == 1

    row = conn.execute(
        text("SELECT id, content_hash FROM crawled_documents WHERE url = 'http://mim.hus.vnu.edu.vn/vi/test-hash-divergence'")
    ).mappings().first()
    assert row is not None
    doc_id = row["id"]
    hash_v1 = row["content_hash"]

    # Approve doc using review_document
    review_document(
        conn,
        doc_id=doc_id,
        decision="approved",
        reason="Phiên bản A chuẩn",
        reviewer_id="57e9a52b-7365-4fe2-b9ce-1320ef48dc02",
    )

    # Export to JSON reviews_file using export_git_reviews_from_db
    reviews_file = tmp_path / "document_reviews.json"
    exported = export_git_reviews_from_db(conn, file_path=reviews_file)
    assert exported >= 1
    reviews_data = json.loads(reviews_file.read_text(encoding="utf-8"))
    assert doc_id in reviews_data
    assert reviews_data[doc_id]["content_hash"] == hash_v1
    assert reviews_data[doc_id]["review_status"] == "approved"

    # Modify the file on disk to version B (different text >= 50 chars)
    file_content_v2 = (
        "---\n"
        'title: "Chương trình kiểm thử đổi hash"\n'
        'url: "http://mim.hus.vnu.edu.vn/vi/test-hash-divergence"\n'
        'major: "mathematics"\n'
        "---\n"
        "Nội dung phiên bản B thay đổi khác biệt hoàn toàn nội dung cũ và vẫn đạt chuẩn trên 50 ký tự."
    )
    doc_file.write_text(file_content_v2, encoding="utf-8")

    # Directly update the document in DB to have the new content and new content_hash
    # (simulating re-crawl of changed page), reset review_status to 'pending'
    body_v2 = "Nội dung phiên bản B thay đổi khác biệt hoàn toàn nội dung cũ và vẫn đạt chuẩn trên 50 ký tự."
    hash_v2 = compute_content_hash(body_v2)
    assert hash_v2 != hash_v1

    conn.execute(
        text("""
            UPDATE crawled_documents
            SET markdown_content = :content,
                content_hash = :hash,
                review_status = 'pending',
                review_reason = NULL,
                reviewer_id = NULL,
                reviewed_at = NULL
            WHERE id = :id
        """),
        {"content": body_v2, "hash": hash_v2, "id": doc_id},
    )

    # Run sync_crawled_documents_and_reviews
    res = sync_crawled_documents_and_reviews(
        conn,
        docs_dir=tmp_path / "documents",
        reviews_file=reviews_file,
    )

    # Assert res["hash_mismatches"] >= 1
    assert res.get("hash_mismatches", 0) >= 1

    # Assert document review_status remains 'pending' (stale review for hash A is rejected)
    stored = get_document(conn, doc_id)
    assert stored is not None
    assert stored["review_status"] == "pending"
    assert stored["content_hash"] == hash_v2


@pytest.mark.hus_postgres
def test_seed_sync_pipeline_protects_published_even_if_json_says_pending(isolated_db_conn, tmp_path):
    conn = isolated_db_conn
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    reviews_file = tmp_path / "document_reviews.json"

    url = "http://mim.hus.vnu.edu.vn/vi/test-published-protect-pipeline"
    content = "Nội dung tài liệu đã được xuất bản chính thức và thẩm định đầy đủ trên năm mươi ký tự."
    content_h = compute_content_hash(content)
    doc_id = "doc_test_pub_pipeline_protect"

    # Pre-clean
    conn.execute(
        text("DELETE FROM crawled_documents WHERE id = :id OR url = :url"),
        {"id": doc_id, "url": url},
    )

    # Create document with is_published = True, review_status = 'approved'
    create_document(
        conn,
        url=url,
        title="Tài liệu đã xuất bản bảo vệ",
        markdown_content=content,
        major="mathematics",
        doc_id=doc_id,
    )
    conn.execute(
        text("""
            UPDATE crawled_documents
            SET review_status = 'approved',
                is_published = true,
                reviewer_id = '57e9a52b-7365-4fe2-b9ce-1320ef48dc02',
                review_reason = 'Đã duyệt và xuất bản',
                reviewed_at = now()
            WHERE id = :id
        """),
        {"id": doc_id},
    )

    # Prepare reviews_file where this document has review_status: 'pending' (or 'rejected') with matching content_hash
    reviews = {
        doc_id: {
            "doc_id": doc_id,
            "url": url,
            "content_hash": content_h,
            "title": "Tài liệu đã xuất bản bảo vệ",
            "review_status": "pending",
            "review_reason": "Cố tình hạ trạng thái xuống pending từ snapshot cũ",
        }
    }
    reviews_file.write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")

    # Run sync_crawled_documents_and_reviews
    res = sync_crawled_documents_and_reviews(
        conn,
        docs_dir=docs_dir,
        reviews_file=reviews_file,
    )

    # Assert res["protected_published"] >= 1
    assert res.get("protected_published", 0) >= 1

    # Assert document in DB still has is_published is True and review_status == 'approved'
    stored = get_document(conn, doc_id)
    assert stored is not None
    assert stored["is_published"] is True
    assert stored["review_status"] == "approved"
    assert stored["reviewer_id"] == "57e9a52b-7365-4fe2-b9ce-1320ef48dc02"
