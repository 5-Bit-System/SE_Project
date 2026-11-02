"""API and integration tests for admin action audit logs."""

import os
import uuid
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

    config = dotenv_values(ENV_PATH)
    url = os.environ.get("HUS_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or config.get("DATABASE_URL")
    eng = create_engine(url)

    # 1. Trigger an administrative action: approve a document
    doc_id = f"doc_audit_{uuid.uuid4().hex[:6]}"
    with eng.begin() as conn:
        create_document(
            conn,
            url=f"https://hus.vnu.edu.vn/doc-{doc_id}",
            title="Audit Test Document",
            markdown_content="# Test Content",
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
