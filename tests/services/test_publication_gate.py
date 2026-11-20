"""Unit tests for curriculum publication gate and provenance manifest service."""

import hashlib
from unittest.mock import MagicMock

import pytest

from app.curriculum.publication_gate import (
    build_publication_manifest,
    get_published_documents,
    validate_publication_gate,
)


def test_build_provenance_manifest():
    rev = {
        "revision_id": "rev_test_123",
        "program_id": "khdl_7460108_2022",
        "version_title": "Chương trình 2026",
        "source_digest": "sha256_mock_digest",
        "payload": {
            "courses": [
                {"code": "MAT1001", "name": "Giải tích 1", "credits": 3},
                {"code": "DAT2001", "name": "Khoa học dữ liệu", "credits": 3},
            ]
        },
    }
    docs = [
        {
            "id": "doc_abc",
            "url": "https://hus.vnu.edu.vn/ctdt-khdl.pdf",
            "title": "Khung CTĐT KHDL 2022",
            "major": "data_science",
            "content_hash": hashlib.sha256(b"document-content").hexdigest(),
            "review_status": "approved",
            "reviewed_at": "2026-11-01T10:00:00Z",
            "reviewer_id": "00000000-0000-0000-0000-000000000001",
        }
    ]

    manifest = build_publication_manifest(
        revision=rev,
        approved_documents=docs,
        publisher_id="admin_account_uuid",
        reason="Ban hành kỳ 1",
    )

    assert manifest["manifest_version"] == "2.0"
    assert manifest["revision_id"] == "rev_test_123"
    assert manifest["program_id"] == "khdl_7460108_2022"
    assert manifest["documents_count"] == 1
    assert len(manifest["source_documents"]) == 1
    assert manifest["source_documents"][0]["document_id"] == "doc_abc"
    assert len(manifest["manifest_checksum"]) == 64
    assert len(manifest["payload_hash"]) == 64

    # Verify checksum changes if payload or documents change
    rev_tampered = dict(rev, source_digest="altered_digest")
    manifest_tampered = build_publication_manifest(
        revision=rev_tampered,
        approved_documents=docs,
        publisher_id="admin_account_uuid",
        reason="Ban hành kỳ 1",
    )
    assert manifest_tampered["manifest_checksum"] != manifest["manifest_checksum"]


def test_validate_publication_gate_status_and_errors(monkeypatch):
    mock_conn = MagicMock()

    # Case 1: Target revision not found
    monkeypatch.setattr(
        "app.curriculum.publication_gate.locked_revision",
        lambda conn, rev_id: None,
    )
    with pytest.raises(ValueError, match="not found"):
        validate_publication_gate(mock_conn, "missing_rev")

    # Case 2: Status is draft, not approved
    monkeypatch.setattr(
        "app.curriculum.publication_gate.locked_revision",
        lambda conn, rev_id: {"revision_id": "r1", "status": "draft", "validation_summary": {}},
    )
    with pytest.raises(ValueError, match="Must be 'approved'"):
        validate_publication_gate(mock_conn, "r1")

    # Case 3: Validation summary contains errors
    monkeypatch.setattr(
        "app.curriculum.publication_gate.locked_revision",
        lambda conn, rev_id: {
            "revision_id": "r2",
            "status": "approved",
            "validation_summary": {"valid": False, "errors": [{"message": "Cycle detected"}]},
        },
    )
    with pytest.raises(ValueError, match="cannot be published"):
        validate_publication_gate(mock_conn, "r2")


def test_validate_publication_gate_linked_documents(monkeypatch):
    from app.curriculum.publication_gate import compute_payload_digest

    mock_conn = MagicMock()

    payload = {"courses": [{"code": "A", "name": "A", "credits": 3}]}
    digest_val = compute_payload_digest(payload)
    rev = {
        "revision_id": "r_ok",
        "status": "approved",
        "validation_summary": {"valid": True, "errors": [], "payload_digest": digest_val},
        "payload": payload,
    }
    monkeypatch.setattr(
        "app.curriculum.publication_gate.locked_revision",
        lambda conn, rev_id: rev,
    )

    # Document missing
    mock_conn.execute.return_value.mappings.return_value.one_or_none.return_value = None
    with pytest.raises(ValueError, match="not found"):
        validate_publication_gate(mock_conn, "r_ok", linked_document_ids=["missing_doc"])

    # Document is pending
    pending_doc = {
        "id": "doc_pend",
        "title": "Bản thảo thông báo",
        "review_status": "pending",
        "content_hash": "hash_pend",
    }
    mock_conn.execute.return_value.mappings.return_value.one_or_none.return_value = pending_doc
    with pytest.raises(ValueError, match="is pending approval"):
        validate_publication_gate(mock_conn, "r_ok", linked_document_ids=["doc_pend"])

    # Document is rejected
    rejected_doc = {
        "id": "doc_rej",
        "title": "Tài liệu sai lệch",
        "review_status": "rejected",
        "content_hash": "hash_rej",
    }
    mock_conn.execute.return_value.mappings.return_value.one_or_none.return_value = rejected_doc
    with pytest.raises(ValueError, match="was rejected"):
        validate_publication_gate(mock_conn, "r_ok", linked_document_ids=["doc_rej"])

    # Document is approved
    approved_doc = {
        "id": "doc_appr",
        "title": "Chương trình chuẩn",
        "review_status": "approved",
        "content_hash": hashlib.sha256(b'Synthetic').hexdigest(),
        "markdown_content": "Synthetic",
        "url": "https://example.invalid/source",
    }
    mock_conn.execute.return_value.mappings.return_value.one_or_none.return_value = approved_doc
    target, approved_list = validate_publication_gate(
        mock_conn, "r_ok", linked_document_ids=["doc_appr"]
    )
    assert target["revision_id"] == "r_ok"
    assert len(approved_list) == 1
    assert approved_list[0]["id"] == "doc_appr"


def test_get_published_documents_exclusion():
    mock_conn = MagicMock()
    mock_rows = [
        {
            "id": "doc1",
            "url": "https://hus.vnu.edu.vn/doc1",
            "title": "Doc 1",
            "major": "computer_science",
            "doc_type": "curriculum",
            "markdown_content": "# Doc 1",
            "metadata_json": {},
            "review_status": "approved",
            "reviewed_at": None,
            "is_published": True,
            "created_at": None,
        }
    ]
    mock_conn.execute.return_value.mappings.return_value.all.return_value = mock_rows

    results = get_published_documents(mock_conn, major="computer_science")
    assert len(results) == 1
    assert results[0]["id"] == "doc1"
    assert results[0]["is_published"] is True
    assert results[0]["review_status"] == "approved"
