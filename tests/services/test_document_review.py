"""Unit tests for document review service, sanitization, and deduplication."""

import os
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine

from app.crawler.document_review_service import (
    create_document,
    find_duplicates,
    review_document,
    sanitize_markdown_for_preview,
    update_document_metadata,
)

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@pytest.fixture(scope="module")
def db_engine():
    config = dotenv_values(ENV_PATH)
    url = os.environ.get("HUS_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or config.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not configured")
    eng = create_engine(url)
    try:
        with eng.connect():
            pass
    except Exception:
        pytest.skip("PostgreSQL database not reachable")
    return eng


def test_markdown_sanitization():
    raw = """
    # Tiêu đề tài liệu
    <script>alert('xss attack');</script>
    Nội dung an toàn.
    <iframe src="http://malicious.com"></iframe>
    <a href="javascript:alert(1)">Liên kết</a>
    <img src="pic.jpg" onerror="alert('hack')">
    """
    clean = sanitize_markdown_for_preview(raw)
    assert "<script>" not in clean
    assert "<iframe>" not in clean
    assert "javascript:" not in clean
    assert "onerror=" not in clean
    assert "Nội dung an toàn." in clean


@pytest.mark.hus_postgres
def test_document_review_lifecycle_and_duplicates(db_engine):
    with db_engine.begin() as conn:
        content_1 = "# Khung chương trình chuẩn CNTT 2022"
        # 1. Create original document
        doc1 = create_document(
            conn,
            url="https://hus.vnu.edu.vn/cntt-2022",
            title="Khung CTĐT CNTT 2022",
            markdown_content=content_1,
            major="computer_science",
        )
        assert doc1["review_status"] == "pending"

        # 2. Create duplicate document with identical content
        doc2 = create_document(
            conn,
            url="https://tuyensinh.hus.vnu.edu.vn/cntt-copy",
            title="Bản sao CTĐT CNTT",
            markdown_content=content_1,
            major="computer_science",
        )
        assert doc2["content_hash"] == doc1["content_hash"]

        # 3. Find duplicates
        dups = find_duplicates(conn, doc1["content_hash"], exclude_id=doc1["id"])
        assert len(dups) >= 1
        assert any(d["id"] == doc2["id"] for d in dups)

        # 4. Update metadata on draft document
        upd = update_document_metadata(conn, doc1["id"], title="Khung CTĐT CNTT Chuẩn ĐHQGHN 2022")
        assert upd["title"] == "Khung CTĐT CNTT Chuẩn ĐHQGHN 2022"

        # 5. Review document: approve
        app_doc = review_document(
            conn,
            doc1["id"],
            decision="approved",
            reason="Đối chiếu chuẩn theo Quyết định 3568/QĐ-ĐHKHTN",
        )
        assert app_doc["review_status"] == "approved"
        assert "3568" in app_doc["review_reason"]
        assert app_doc["reviewed_at"] is not None

        # 6. Review duplicate document: reject
        rej_doc = review_document(
            conn,
            doc2["id"],
            decision="rejected",
            reason="Trùng lặp nội dung với tài liệu chính thức",
        )
        assert rej_doc["review_status"] == "rejected"

        # 7. Validation: review without valid reason fails
        with pytest.raises(ValueError, match="ít nhất 3 ký tự"):
            review_document(conn, doc1["id"], decision="approved", reason=" ")
