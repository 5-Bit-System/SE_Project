"""End-to-end API tests for curriculum publication gate and provenance manifest."""

import uuid
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, text

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    config = dotenv_values(ENV_PATH)
    url = config.get("DATABASE_URL")
    if url:
        eng = create_engine(url)
        monkeypatch.setattr("app.api.admin.engine", lambda: eng)


def test_publication_gate_full_lifecycle(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    config = dotenv_values(ENV_PATH)
    eng = create_engine(config.get("DATABASE_URL"))

    # 1. Insert test crawled document directly in pending status
    doc_id = f"doc_gate_{uuid.uuid4().hex[:8]}"
    with eng.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO crawled_documents (
                    id, url, content_hash, title, major, doc_type,
                    markdown_content, metadata_json, review_status, is_published
                ) VALUES (
                    :id, :url, :hash, :title, :major, :doc_type,
                    :content, :meta, 'pending', false
                )
            """),
            {
                "id": doc_id,
                "url": "https://hus.vnu.edu.vn/ctdt-khdl-gate.pdf",
                "hash": "abc123hash",
                "title": "Chương trình chuẩn KHDL 2022",
                "major": "data_science",
                "doc_type": "curriculum",
                "content": "# Nội dung CTĐT KHDL",
                "meta": "{}",
            },
        )

    # 2. Import a curriculum revision and approve it
    csv_data = """code,name,credits,prerequisites,block
DAT1001,Nhập môn KHDL,3,,Cơ sở ngành
DAT1002,Lập trình Python,3,,Cơ sở ngành
"""
    import_resp = verified_client.post(
        "/admin/catalog-revisions/import",
        json={
            "program_id": "khdl_7460108_2022",
            "version_title": "KHDL Gate Test",
            "csv_content": csv_data,
        },
    )
    assert import_resp.status_code == 200
    rev_id = import_resp.json()["revision_id"]

    # Approve revision
    appr_resp = verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/approve",
        json={"reason": "Hội đồng đã xem xét nội dung"},
    )
    assert appr_resp.status_code == 200

    # 3. Attempt to publish referencing the pending document -> Rejected by publication gate
    pub_fail_pending = verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/publish",
        json={"reason": "Ban hành", "linked_document_ids": [doc_id]},
    )
    assert pub_fail_pending.status_code == 400
    assert "pending approval" in pub_fail_pending.json()["detail"]

    # 4. Reject the document and attempt publish -> Rejected by gate
    verified_client.post(
        f"/admin/crawler/documents/{doc_id}/reject",
        json={"reason": "Tài liệu bị lỗi font"},
    )
    pub_fail_rejected = verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/publish",
        json={"reason": "Ban hành", "linked_document_ids": [doc_id]},
    )
    assert pub_fail_rejected.status_code == 400
    assert "was rejected" in pub_fail_rejected.json()["detail"]

    # 5. Approve document and publish successfully
    verified_client.post(
        f"/admin/crawler/documents/{doc_id}/approve",
        json={"reason": "Đã đính chính hợp lệ"},
    )

    pub_ok = verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/publish",
        json={
            "reason": "Ban hành chính thức cùng tài liệu căn cứ",
            "linked_document_ids": [doc_id],
        },
    )
    assert pub_ok.status_code == 200
    pub_data = pub_ok.json()
    assert pub_data["status"] == "published"
    assert pub_data["is_active"] is True
    assert "provenance_manifest" in pub_data
    manifest = pub_data["provenance_manifest"]
    assert manifest["revision_id"] == rev_id
    assert manifest["documents_count"] == 1
    assert manifest["source_documents"][0]["document_id"] == doc_id
    assert len(manifest["manifest_checksum"]) == 64

    # 6. Retrieve provenance manifest via API
    prov_resp = verified_client.get(f"/admin/catalog-revisions/{rev_id}/provenance")
    assert prov_resp.status_code == 200
    saved_manifest = prov_resp.json()["provenance_manifest"]
    assert saved_manifest["manifest_checksum"] == manifest["manifest_checksum"]

    # 7. Check user-facing retrieval /academic/documents/published
    pub_docs_resp = verified_client.get("/academic/documents/published?major=data_science")
    assert pub_docs_resp.status_code == 200
    pub_docs = pub_docs_resp.json()
    found_doc = next((d for d in pub_docs if d["id"] == doc_id), None)
    assert found_doc is not None
    assert found_doc["is_published"] is True
    assert found_doc["review_status"] == "approved"
