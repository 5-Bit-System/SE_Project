"""Tests for Content Quality Gate preventing approval of empty or marker-only scanned documents (Issue #136)."""

import hashlib
import json
import re
from pathlib import Path

import pytest

from app.crawler.document_review_service import (
    create_document,
    get_document,
    is_meaningful_content,
    normalize_crawled_url,
    parse_frontmatter,
    review_document,
)
from tests.support.admin_database import admin_test_engine, db_transaction_rollback


@pytest.fixture
def isolated_db_conn():
    with db_transaction_rollback() as conn:
        yield conn


def test_meaningful_content_threshold():
    """Verify is_meaningful_content threshold and marker stripping logic."""
    # 1. Empty / None
    ok, reason = is_meaningful_content("")
    assert not ok
    assert "cần OCR" in reason

    ok, reason = is_meaningful_content("   \n\t  ")
    assert not ok

    # 2. Only HTML comments / page markers
    marker_only = "<!-- page 1 -->\n<!-- page 2 -->\n<!-- page 3 -->"
    ok, reason = is_meaningful_content(marker_only)
    assert not ok
    assert "cần OCR" in reason

    # 3. With YAML frontmatter and markers
    with_frontmatter = "---\ntitle: CTĐT Scan\nurl: http://example.com/scan.pdf\n---\n<!-- page 1 -->"
    ok, reason = is_meaningful_content(with_frontmatter)
    assert not ok
    assert "cần OCR" in reason

    # 4. Exact boundaries (min_length = 50)
    boundary_49 = "a" * 49
    ok, reason = is_meaningful_content(boundary_49, min_length=50)
    assert not ok

    boundary_50 = "a" * 50
    ok, reason = is_meaningful_content(boundary_50, min_length=50)
    assert ok
    assert reason == ""

    # 5. Marker + text boundaries
    marker_plus_49 = "<!-- page 1 -->\n" + ("x" * 49)
    ok, reason = is_meaningful_content(marker_plus_49, min_length=50)
    assert not ok

    marker_plus_50 = "<!-- page 1 -->\n" + ("x" * 50)
    ok, reason = is_meaningful_content(marker_plus_50, min_length=50)
    assert ok
    assert reason == ""


@pytest.mark.hus_postgres
def test_cannot_approve_empty_or_marker_only_document(isolated_db_conn):
    """Quality gate must reject approval of empty or marker-only documents with ValueError."""
    conn = isolated_db_conn
    # Create a document with only page markers
    doc = create_document(
        conn,
        url="https://hus.vnu.edu.vn/test-marker-quality-gate-doc",
        title="Tài liệu scan chỉ có marker trang",
        markdown_content="<!-- page 1 -->\n<!-- page 2 -->",
        major="computer_science",
    )
    doc_id = doc["id"]

    # Detail must expose needs_ocr=True
    detail = get_document(conn, doc_id)
    assert detail is not None
    assert detail.get("needs_ocr") is True

    # Attempting to approve must raise ValueError with OCR required message
    with pytest.raises(
        ValueError,
        match="Nội dung tài liệu rỗng hoặc chỉ chứa marker trang, không đủ điều kiện phê duyệt \\(cần OCR\\)",
    ):
        review_document(
            conn,
            doc_id=doc_id,
            decision="approved",
            reason="Duyệt tài liệu scan chưa OCR",
            reviewer_id="57e9a52b-7365-4fe2-b9ce-1320ef48dc02",
        )

    # Rejecting a marker-only document is allowed
    rejected = review_document(
        conn,
        doc_id=doc_id,
        decision="rejected",
        reason="Tài liệu chỉ có marker trang, chưa có nội dung văn bản",
        reviewer_id="57e9a52b-7365-4fe2-b9ce-1320ef48dc02",
    )
    assert rejected["review_status"] == "rejected"

    # Create document with meaningful content (>= 50 chars)
    meaningful_content = (
        "Chương trình đào tạo cử nhân ngành Khoa học máy tính và Thông tin định hướng ứng dụng"
    )
    doc_good = create_document(
        conn,
        url="https://hus.vnu.edu.vn/test-good-content-gate-doc",
        title="Tài liệu có nội dung chuẩn",
        markdown_content=meaningful_content,
        major="computer_science",
    )
    detail_good = get_document(conn, doc_good["id"])
    assert detail_good["needs_ocr"] is False

    # Approving good document succeeds
    approved_good = review_document(
        conn,
        doc_id=doc_good["id"],
        decision="approved",
        reason="Nội dung đầy đủ, hợp lệ",
        reviewer_id="57e9a52b-7365-4fe2-b9ce-1320ef48dc02",
    )
    assert approved_good["review_status"] == "approved"


def test_21_marker_files_marked_pending_with_ocr_reason():
    """Verify that all 21 marker-only files on disk are marked 'pending'

    with OCR reason in data/hus/document_reviews.json, and 0 are approved.
    """
    docs_dir = Path("data/hus/processed/documents")
    assert docs_dir.is_dir(), f"Documents directory not found: {docs_dir}"

    reviews_file = Path("data/hus/document_reviews.json")
    assert reviews_file.is_file(), f"Reviews file not found: {reviews_file}"
    reviews = json.loads(reviews_file.read_text(encoding="utf-8"))

    expected_ocr_reason = (
        "Chờ OCR: Tài liệu chỉ chứa marker trang scan, chưa có nội dung văn bản để kiểm định"
    )

    marker_files = []
    for path in sorted(docs_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata, content = parse_frontmatter(text)
        cleaned = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL).strip()
        if len(cleaned) < 50:
            raw_url = str(metadata.get("url") or "")
            url = normalize_crawled_url(raw_url)
            doc_id = f"doc_{hashlib.sha256(url.encode('utf-8')).hexdigest()[:12]}"
            marker_files.append((doc_id, url, path.name))

    assert len(marker_files) == 21, f"Expected exactly 21 marker files, found {len(marker_files)}"

    for doc_id, url, fname in marker_files:
        assert doc_id in reviews, f"Marker document {doc_id} ({fname}) missing from document_reviews.json"
        rev = reviews[doc_id]
        assert rev["review_status"] == "pending", (
            f"Document {doc_id} has invalid review_status '{rev['review_status']}', expected 'pending'"
        )
        assert rev["review_reason"] == expected_ocr_reason, (
            f"Document {doc_id} has review_reason '{rev['review_reason']}', expected '{expected_ocr_reason}'"
        )
        assert rev["reviewer_id"] is None, f"Document {doc_id} must have reviewer_id=None"
        assert rev["reviewed_at"] is None, f"Document {doc_id} must have reviewed_at=None"

    # Explicit check for doc_42f38f75db40
    assert "doc_42f38f75db40" in reviews
    assert reviews["doc_42f38f75db40"]["review_status"] == "pending"
    assert reviews["doc_42f38f75db40"]["review_reason"] == expected_ocr_reason
    assert reviews["doc_42f38f75db40"]["reviewer_id"] is None


@pytest.mark.hus_postgres
def test_api_cannot_approve_empty_or_marker_only_document(
    verified_client, fake_accounts, monkeypatch
):
    """API endpoint /admin/crawler/documents/{id}/approve must return 400 Bad Request

    when attempting to approve empty or marker-only scanned documents.
    """
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    eng = admin_test_engine()
    monkeypatch.setattr("app.api.admin.engine", lambda: eng)

    with eng.begin() as conn:
        doc = create_document(
            conn,
            url="https://hus.vnu.edu.vn/test-api-marker-quality-gate-doc",
            title="Tài liệu API scan chỉ có marker",
            markdown_content="<!-- page 1 -->\n<!-- page 2 -->",
            major="computer_science",
        )
        doc_id = doc["id"]

    try:
        # Verify detail returns needs_ocr=True
        detail_resp = verified_client.get(f"/admin/crawler/documents/{doc_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["needs_ocr"] is True

        # Attempt approve via API -> must return 400 Bad Request
        resp = verified_client.post(
            f"/admin/crawler/documents/{doc_id}/approve",
            json={"reason": "Cố tình duyệt tài liệu chưa OCR"},
        )
        assert resp.status_code == 400
        assert "cần OCR" in resp.json()["detail"]
    finally:
        with eng.begin() as conn:
            from sqlalchemy import text
            conn.execute(text("DELETE FROM crawled_documents WHERE id = :id"), {"id": doc_id})

