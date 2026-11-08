"""Unit tests for document review service, sanitization, and deduplication."""

import pytest

from app.crawler.document_review_service import (
    create_document,
    find_duplicates,
    review_document,
    sanitize_markdown_for_preview,
    update_document_metadata,
)
from tests.support.admin_database import admin_test_engine


@pytest.fixture(scope="module")
def db_engine():
    eng = admin_test_engine()
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
        content_1 = "# Khung chương trình đào tạo chuẩn ngành Công nghệ thông tin năm 2022 của Trường ĐHKHTN"
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



@pytest.mark.hus_postgres
def test_metadata_update_on_approved_or_published_document_revokes_approval(db_engine):
    with db_engine.begin() as conn:
        doc = create_document(
            conn,
            url="https://hus.vnu.edu.vn/approved-doc-test",
            title="Tài liệu ban đầu",
            markdown_content="# Nội dung văn bản chi tiết chương trình đào tạo chuẩn bậc đại học chính quy",
            major="computer_science",
        )
        doc_id = doc["id"]

        # Approve and publish document
        review_document(conn, doc_id, decision="approved", reason="Phê duyệt lần đầu")
        from sqlalchemy import text
        conn.execute(text("UPDATE crawled_documents SET is_published = true WHERE id = :id"), {"id": doc_id})

        doc_approved = create_document.__globals__["get_document"](conn, doc_id)
        assert doc_approved["review_status"] == "approved"
        assert doc_approved["is_published"] is True

        # Now update metadata on this approved/published document
        upd = update_document_metadata(conn, doc_id, title="Tiêu đề đã sửa sau khi duyệt", major="data_science")
        assert upd["title"] == "Tiêu đề đã sửa sau khi duyệt"
        assert upd["major"] == "data_science"

        # MUST be revoked to pending and unpublished
        assert upd["review_status"] == "pending"
        assert upd["is_published"] is False
        assert upd["reviewer_id"] is None
        assert upd["review_reason"] is None
        assert upd["reviewed_at"] is None

        # Subsequent re-approval applies to the edited document
        assert upd["id"] != doc_id
        preserved = create_document.__globals__["get_document"](conn, doc_id)
        assert preserved["title"] == doc_approved["title"]
        assert preserved["is_published"] is True
        re_app = review_document(conn, upd["id"], decision="approved", reason="Duyệt lại bản sửa đổi")
        assert re_app["review_status"] == "approved"
        assert re_app["title"] == "Tiêu đề đã sửa sau khi duyệt"
