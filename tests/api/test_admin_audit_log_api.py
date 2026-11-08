"""API and integration tests for admin action audit logs."""

import uuid

import pytest

from tests.support.admin_database import admin_test_engine, admin_test_url

pytestmark = pytest.mark.hus_postgres



@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    eng = admin_test_engine()
    monkeypatch.setattr("app.api.admin.engine", lambda: eng)


def test_audit_log_access_forbidden_for_non_admin(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "student"

    resp = verified_client.get("/admin/audit-logs")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "forbidden"


def test_audit_log_lifecycle_and_actions(verified_client, fake_accounts):
    from app.crawler.document_review_service import create_document

    for session in fake_accounts.sessions.values():
        session["role"] = "admin"
        session["account_id"] = "57e9a52b-7365-4fe2-b9ce-1320ef48dc02"

    admin_test_url()
    eng = admin_test_engine()

    # 1. Trigger an administrative action: approve a document
    doc_id = f"doc_audit_{uuid.uuid4().hex[:6]}"
    with eng.begin() as conn:
        create_document(
            conn,
            url=f"https://hus.vnu.edu.vn/doc-{doc_id}",
            title="Audit Test Document",
            markdown_content="# Test Content: Nội dung chi tiết tài liệu phục vụ kiểm toán hệ thống đạt chuẩn",
            doc_id=doc_id,
        )

    approve_resp = verified_client.post(
        f"/admin/crawler/documents/{doc_id}/approve",
        json={"reason": "Phê duyệt kiểm toán"},
    )
    assert approve_resp.status_code == 200

    # 2. Query audit logs
    logs_resp = verified_client.get("/admin/audit-logs?action=document&limit=20")
    assert logs_resp.status_code == 200
    data = logs_resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1

    # Find the approved document action
    item = next((it for it in data["items"] if it["target_id"] == doc_id), None)
    assert item is not None
    assert item["action"] == "document.approve"
    assert item["target_type"] == "document"
    assert "Phê duyệt kiểm toán" in item["summary"]
    assert item["result"] == "ok"

    # 3. Test text search with query parameter
    search_resp = verified_client.get(f"/admin/audit-logs?q={doc_id}")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total"] >= 1
    assert any(it["target_id"] == doc_id for it in search_data["items"])

    # 4. Test summary metrics
    metrics_resp = verified_client.get("/admin/audit-logs/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert "total_events" in metrics
    assert "events_last_24h" in metrics
    assert metrics["total_events"] >= 1
