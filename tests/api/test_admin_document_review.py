"""Tests for admin crawled documents list, preview, and review approval API."""

import os
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine

pytestmark = pytest.mark.hus_postgres

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    config = dotenv_values(ENV_PATH)
    url = os.environ.get("HUS_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or config.get("DATABASE_URL")
    if not url:
        pytest.skip("PostgreSQL database URL not configured")
    eng = create_engine(url)
    monkeypatch.setattr("app.api.admin.engine", lambda: eng)


def test_admin_document_review_api(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    url = os.environ.get("HUS_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or dotenv_values(ENV_PATH).get("DATABASE_URL")
    eng = create_engine(url)
    from app.crawler.document_review_service import create_document, get_document
    with eng.begin() as conn:
        if not get_document(conn, "doc_test_review"):
            create_document(
                conn,
                url="https://hus.vnu.edu.vn/test-review-doc",
                title="Tài liệu kiểm thử kiểm duyệt",
                markdown_content="# Nội dung tài liệu kiểm thử",
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
