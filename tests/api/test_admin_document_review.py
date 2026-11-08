"""Tests for admin crawled documents list, preview, and review approval API."""

import pytest

from tests.support.admin_database import admin_test_engine, admin_test_url

pytestmark = pytest.mark.hus_postgres



@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    eng = admin_test_engine()
    monkeypatch.setattr("app.api.admin.engine", lambda: eng)


@pytest.fixture(autouse=True)
def cleanup_test_documents():
    eng = admin_test_engine()
    from sqlalchemy import text

    def _cleanup():
        with eng.begin() as conn:
            conn.execute(
                text(
                    "DELETE FROM crawled_documents "
                    "WHERE id = 'doc_test_review' "
                    "OR url LIKE '%test-review-doc%' "
                    "OR url LIKE '%test%' "
                    "OR id LIKE '%test%'"
                )
            )

    _cleanup()
    try:
        yield
    finally:
        _cleanup()



def test_admin_document_review_api(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    admin_test_url()
    eng = admin_test_engine()
    from app.crawler.document_review_service import create_document, get_document
    with eng.begin() as conn:
        if not get_document(conn, "doc_test_review"):
            create_document(
                conn,
                url="https://hus.vnu.edu.vn/test-review-doc",
                title="Tài liệu kiểm thử kiểm duyệt",
                markdown_content="# Nội dung văn bản chi tiết tài liệu kiểm thử đạt tiêu chuẩn phê duyệt",
                major="toan_hoc",
                doc_type="curriculum",
                source_id="src_hus_main",
                doc_id="doc_test_review",
            )

    # 1. List documents (triggers disk seeding if empty)
    resp = verified_client.get("/admin/crawler/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert "documents" in data
    assert data["total"] >= 1
    doc = data["documents"][0]
    doc_id = doc["id"]

    # 2. Get document detail
    detail_resp = verified_client.get(f"/admin/crawler/documents/{doc_id}")
    assert detail_resp.status_code == 200
    doc_detail = detail_resp.json()
    assert "safe_markdown" in doc_detail
    assert "duplicates" in doc_detail
    assert doc_detail["review_status"] in ("pending", "approved", "rejected")

    # 3. Update document metadata
    meta_resp = verified_client.put(
        f"/admin/crawler/documents/{doc_id}/metadata",
        json={"title": "Tài liệu cập nhật tiêu đề kiểm duyệt", "major": "data_science"},
    )
    assert meta_resp.status_code == 200
    assert meta_resp.json()["title"] == "Tài liệu cập nhật tiêu đề kiểm duyệt"
    assert meta_resp.json()["major"] == "data_science"

    # 4. Reject document without reason fails (validation error)
    bad_rev = verified_client.post(
        f"/admin/crawler/documents/{doc_id}/approve",
        json={"reason": ""},
    )
    assert bad_rev.status_code == 422

    # 5. Approve document with valid reason
    app_resp = verified_client.post(
        f"/admin/crawler/documents/{doc_id}/approve",
        json={"reason": "Nội dung khớp với chương trình đào tạo chính quy"},
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["review_status"] == "approved"
    assert "chương trình đào tạo" in app_resp.json()["review_reason"]

    # 6. Reject document with valid reason
    rej_resp = verified_client.post(
        f"/admin/crawler/documents/{doc_id}/reject",
        json={"reason": "Thông tin đã hết hiệu lực tuyển sinh"},
    )
    assert rej_resp.status_code == 200
    assert rej_resp.json()["review_status"] == "rejected"


    # 7. Edit metadata on approved document resets review_status to pending
    verified_client.post(
        f"/admin/crawler/documents/{doc_id}/approve",
        json={"reason": "Duyệt lại để kiểm tra sửa metadata"},
    )
    edit_after_app = verified_client.put(
        f"/admin/crawler/documents/{doc_id}/metadata",
        json={"title": "Tài liệu sau khi duyệt bị sửa lại tiêu đề"},
    )
    assert edit_after_app.status_code == 200
    res_meta = edit_after_app.json()
    assert res_meta["title"] == "Tài liệu sau khi duyệt bị sửa lại tiêu đề"
    assert res_meta["review_status"] == "pending"
    assert res_meta["is_published"] is False


def test_admin_document_review_db_clean():
    from sqlalchemy import text
    eng = admin_test_engine()
    with eng.connect() as conn:
        dirty = conn.execute(
            text(
                "SELECT count(*) FROM crawled_documents "
                "WHERE id = 'doc_test_review' OR url LIKE '%test-review-doc%'"
            )
        ).scalar()
        assert dirty == 0

