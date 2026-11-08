"""Tests for SSOT database review state and atomic post-commit git review export (Issue #135 / P1.3)."""

import asyncio
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from app.api import admin as admin_mod
from app.api.admin import (
    DocumentReviewActionRequest,
    approve_crawled_document,
    reject_crawled_document,
)
from app.crawler import document_review_service
from app.crawler.document_review_service import (
    export_git_reviews_from_db,
    review_document,
)


def test_rollback_in_db_does_not_mutate_json_file(tmp_path, monkeypatch):
    """Lỗi P1.3: If a DB transaction is aborted or rolled back, the JSON file on disk must NOT be mutated."""
    test_json = tmp_path / "document_reviews.json"
    initial_content = {
        "doc_existing": {
            "doc_id": "doc_existing",
            "url": "https://example.com/existing",
            "content_hash": "hash_existing",
            "title": "Existing Doc",
            "review_status": "pending",
            "review_reason": "Chờ duyệt",
            "reviewer_id": None,
            "reviewed_at": None,
        }
    }
    test_json.write_text(json.dumps(initial_content, indent=2), encoding="utf-8")
    monkeypatch.setattr(document_review_service, "DEFAULT_REVIEWS_FILE", test_json)

    mock_conn = MagicMock()
    mock_conn.execute.return_value = MagicMock()

    doc_data = {
        "id": "doc_uncommitted",
        "url": "https://example.com/uncommitted",
        "content_hash": "hash_uncommitted",
        "title": "Uncommitted Document",
        "markdown_content": "Nội dung văn bản chi tiết kiểm thử rollback với độ dài hợp lệ đạt tiêu chuẩn kiểm duyệt",
        "review_status": "pending",
        "is_published": False,
        "review_reason": None,
        "reviewer_id": None,
        "reviewed_at": None,
    }
    updated_doc_data = dict(doc_data)
    updated_doc_data["review_status"] = "approved"
    updated_doc_data["review_reason"] = "Hợp lệ chuẩn"

    with patch.object(document_review_service, "publication_lock"):
        with patch.object(
            document_review_service, "get_document", side_effect=[doc_data, updated_doc_data]
        ):
            try:
                review_document(
                    mock_conn,
                    doc_id="doc_uncommitted",
                    decision="approved",
                    reason="Hợp lệ chuẩn",
                    reviewer_id="reviewer_1",
                )
                raise RuntimeError("Simulated DB transaction rollback before commit")
            except RuntimeError:
                pass

    # The file on disk must NOT contain doc_uncommitted
    current_data = json.loads(test_json.read_text(encoding="utf-8"))
    assert "doc_uncommitted" not in current_data, (
        "Dual-write violation: JSON reviews file was modified before DB transaction committed!"
    )
    assert current_data == initial_content


def test_atomic_export_recovers_from_transient_write_error(tmp_path, monkeypatch):
    """export_git_reviews_from_db must write atomically via .tmp and retry on transient Windows file lock."""
    test_json = tmp_path / "document_reviews.json"

    # Mock DB connection returning 1 approved document
    mock_conn = MagicMock()
    mock_row = MagicMock()
    mock_row._mapping = {
        "id": "doc_test_1",
        "url": "https://example.com/test1",
        "content_hash": "hash1",
        "title": "Tài liệu kiểm thử 1",
        "review_status": "approved",
        "review_reason": "Duyệt chuẩn",
        "reviewer_id": "00000000-0000-0000-0000-000000000001",
        "reviewed_at": "2026-11-09T00:00:00",
    }
    mock_conn.execute.return_value.fetchall.return_value = [mock_row]

    # Simulate os.replace failing with PermissionError twice, then succeeding on 3rd attempt
    original_replace = os.replace
    attempts = 0

    def flaky_replace(src, dst):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise PermissionError(13, "Permission denied (simulated Windows file lock)")
        return original_replace(src, dst)

    with patch("os.replace", side_effect=flaky_replace):
        count = export_git_reviews_from_db(mock_conn, file_path=test_json)

    assert count >= 1
    assert attempts == 3
    assert test_json.is_file()
    exported = json.loads(test_json.read_text(encoding="utf-8"))
    assert "doc_test_1" in exported
    assert exported["doc_test_1"]["review_status"] == "approved"

    # Temporary files should be cleaned up
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_atomic_export_raises_after_max_retries(tmp_path):
    """export_git_reviews_from_db must raise after exceeding max retries."""
    test_json = tmp_path / "document_reviews.json"
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = []

    with patch("os.replace", side_effect=PermissionError(13, "Persistent lock")):
        with pytest.raises(PermissionError):
            export_git_reviews_from_db(mock_conn, file_path=test_json)


def test_export_git_reviews_queries_committed_states_from_db(tmp_path):
    """export_git_reviews_from_db correctly queries DB and formats output JSON."""
    test_json = tmp_path / "document_reviews.json"

    # Pre-populate test_json with one existing pending review
    test_json.write_text(
        json.dumps({
            "doc_pending": {
                "doc_id": "doc_pending",
                "url": "https://example.com/pending",
                "content_hash": "hash_pending",
                "title": "Pending Doc",
                "review_status": "pending",
                "review_reason": "Chờ duyệt",
                "reviewer_id": None,
                "reviewed_at": "",
            }
        }),
        encoding="utf-8",
    )

    mock_conn = MagicMock()
    row_approved = MagicMock()
    row_approved._mapping = {
        "id": "doc_approved",
        "url": "https://example.com/app",
        "content_hash": "hash_app",
        "title": "Approved Doc",
        "review_status": "approved",
        "review_reason": "Đạt chuẩn",
        "reviewer_id": "00000000-0000-0000-0000-000000000002",
        "reviewed_at": "2026-11-09T01:00:00",
    }
    row_rejected = MagicMock()
    row_rejected._mapping = {
        "id": "doc_rejected",
        "url": "https://example.com/rej",
        "content_hash": "hash_rej",
        "title": "Rejected Doc",
        "review_status": "rejected",
        "review_reason": "Trùng lặp",
        "reviewer_id": None,
        "reviewed_at": "2026-11-09T01:30:00",
    }
    mock_conn.execute.return_value.fetchall.return_value = [row_approved, row_rejected]

    count = export_git_reviews_from_db(mock_conn, file_path=test_json)
    assert count == 3  # 1 existing pending + 2 from DB

    exported = json.loads(test_json.read_text(encoding="utf-8"))
    assert exported["doc_approved"]["review_status"] == "approved"
    assert exported["doc_rejected"]["review_status"] == "rejected"
    assert exported["doc_pending"]["review_status"] == "pending"


def test_admin_api_calls_export_only_post_commit(monkeypatch):
    """Admin endpoint calls export_git_reviews_from_db after commit, never on transaction abort."""
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_begin_context = MagicMock()
    mock_begin_context.__enter__.return_value = mock_conn
    mock_begin_context.__exit__.return_value = None
    mock_engine.begin.return_value = mock_begin_context

    exported = []

    def fake_export(eng):
        exported.append(eng)
        return 1

    async def fake_auth(req):
        return {"role": "admin", "account_id": "u1", "email": "admin@hus.vnu.edu.vn"}

    monkeypatch.setattr(admin_mod, "engine", lambda: mock_engine)
    monkeypatch.setattr(admin_mod, "export_git_reviews_from_db", fake_export)
    monkeypatch.setattr(
        admin_mod,
        "review_document",
        lambda conn, **kwargs: {"id": "doc_1", "review_status": kwargs.get("decision")},
    )
    monkeypatch.setattr(admin_mod, "log_admin_action", lambda *args, **kwargs: None)
    monkeypatch.setattr(admin_mod, "require_account", fake_auth)

    req = MagicMock()

    # 1. Successful approve -> export called post-commit
    res = asyncio.run(
        approve_crawled_document(
            req, "doc_1", DocumentReviewActionRequest(reason="Hợp lệ đủ chuẩn")
        )
    )
    assert res["id"] == "doc_1"
    assert res["review_status"] == "approved"
    assert len(exported) == 1

    # 2. Successful reject -> export called post-commit
    res_rej = asyncio.run(
        reject_crawled_document(
            req, "doc_1", DocumentReviewActionRequest(reason="Nội dung đã lỗi thời")
        )
    )
    assert res_rej["id"] == "doc_1"
    assert res_rej["review_status"] == "rejected"
    assert len(exported) == 2

    # 3. Transaction error inside begin() block -> export is NOT called
    def failing_log(*args, **kwargs):
        raise RuntimeError("Audit log DB insert error")

    monkeypatch.setattr(admin_mod, "log_admin_action", failing_log)
    with pytest.raises(RuntimeError, match="Audit log DB insert error"):
        asyncio.run(
            approve_crawled_document(
                req, "doc_1", DocumentReviewActionRequest(reason="Hợp lệ đủ chuẩn")
            )
        )

    # Export count must still be 2 (not incremented on rollback)
    assert len(exported) == 2
