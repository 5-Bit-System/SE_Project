"""Tests for Git-tracked review state dual-write and auto-sync."""
import json
from pathlib import Path

import pytest

from app.crawler.document_review_service import (
    create_document,
    get_document,
    load_git_reviews,
    review_document,
    save_git_review,
    sync_crawled_documents_and_reviews,
)
from tests.support.admin_database import admin_test_engine


@pytest.fixture(scope="module")
def db_engine():
    try:
        eng = admin_test_engine()
        with eng.connect():
            pass
        return eng
    except Exception:
        pytest.skip("PostgreSQL database not reachable")


def test_save_and_load_git_reviews(tmp_path):
    review_file = tmp_path / "reviews.json"
    assert load_git_reviews(review_file) == {}

    save_git_review(
        doc_id="doc_test_123",
        url="http://mim.hus.vnu.edu.vn/vi/khmt-tt",
        content_hash="abc123hash",
        title="Khoa học máy tính",
        review_status="approved",
        review_reason="Nội dung chuẩn",
        file_path=review_file,
    )

    data = load_git_reviews(review_file)
    assert "doc_test_123" in data
    assert data["doc_test_123"]["review_status"] == "approved"
    assert data["doc_test_123"]["url"] == "http://mim.hus.vnu.edu.vn/vi/khmt-tt"


@pytest.mark.hus_postgres
def test_dual_write_on_review_document(db_engine, tmp_path, monkeypatch):
    test_json = tmp_path / "test_reviews.json"
    import app.crawler.document_review_service as srv
    monkeypatch.setattr(srv, "DEFAULT_REVIEWS_FILE", test_json)

    with db_engine.begin() as conn:
        from sqlalchemy import text
        conn.execute(text("DELETE FROM crawled_documents WHERE id = 'doc_dual_write_test'"))
        doc = create_document(
            conn,
            url="http://mim.hus.vnu.edu.vn/vi/test-dual-write",
            title="Tài liệu kiểm tra dual write",
            markdown_content="# Nội dung kiểm thử dual write",
            major="computer_science",
            doc_type="curriculum",
            doc_id="doc_dual_write_test",
        )
        assert doc["review_status"] == "pending"

        # Review document as approved
        reviewed = review_document(
            conn,
            doc_id="doc_dual_write_test",
            decision="approved",
            reason="Phê duyệt chương trình chuẩn",
        )
        assert reviewed["review_status"] == "approved"

        # Verify JSON file was created and contains the review
        assert test_json.is_file(), "Reviews JSON file must be created on review"
        reviews = json.loads(test_json.read_text(encoding="utf-8"))
        assert "doc_dual_write_test" in reviews
        assert reviews["doc_dual_write_test"]["review_status"] == "approved"
        assert reviews["doc_dual_write_test"]["review_reason"] == "Phê duyệt chương trình chuẩn"


@pytest.mark.hus_postgres
def test_auto_sync_on_startup(db_engine, tmp_path):
    test_json = tmp_path / "sync_reviews.json"
    test_json.write_text(
        json.dumps(
            {
                "doc_sync_target": {
                    "doc_id": "doc_sync_target",
                    "url": "http://mim.hus.vnu.edu.vn/vi/test-sync",
                    "content_hash": "hash_sync",
                    "title": "Tài liệu đồng bộ",
                    "review_status": "approved",
                    "review_reason": "Đồng bộ từ Git repo",
                }
            }
        ),
        encoding="utf-8",
    )

    with db_engine.begin() as conn:
        from sqlalchemy import text
        conn.execute(text("DELETE FROM crawled_documents WHERE id = 'doc_sync_target'"))
        create_document(
            conn,
            url="http://mim.hus.vnu.edu.vn/vi/test-sync",
            title="Tài liệu đồng bộ",
            markdown_content="# Nội dung đồng bộ",
            major="mathematics",
            doc_id="doc_sync_target",
        )

        res = sync_crawled_documents_and_reviews(
            conn,
            docs_dir=Path("data/hus/processed/documents"),
            reviews_file=test_json,
        )
        assert res["reviews_applied"] >= 1

        synced = get_document(conn, "doc_sync_target")
        assert synced is not None
        assert synced["review_status"] == "approved"
        assert synced["review_reason"] == "Đồng bộ từ Git repo"
