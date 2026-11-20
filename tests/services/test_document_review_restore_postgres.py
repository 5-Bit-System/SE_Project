"""Real PostgreSQL version isolation and failed post-commit export regressions."""
import asyncio
import json
import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from app.api import admin as admin_api
from app.crawler import document_review_service as service
from tests.support.admin_database import admin_test_engine, db_transaction_rollback
from tests.support.document_reviews import REVIEWER_ID, snapshot_decision
from tools import plan_document_taxonomy_remediation as remediation

pytestmark = pytest.mark.hus_postgres
BODY = "Synthetic curriculum content long enough for the content quality and reviewer gates."


@pytest.mark.parametrize("published", [False, True])
def test_metadata_replacement_remains_pending_after_sync(tmp_path, published):
    empty = tmp_path / "empty"
    empty.mkdir()
    with db_transaction_rollback() as conn:
        original = service.create_document(conn, url="https://example.invalid/" + uuid.uuid4().hex,
                                           title="Original math source", markdown_content=BODY,
                                           major="mathematics")
        reviewed = service.review_document(conn, original["id"], "approved", "Original review", REVIEWER_ID)
        if published:
            conn.execute(text("UPDATE crawled_documents SET is_published=true WHERE id=:id"),
                         {"id": original["id"]})
        replacement = service.update_document_metadata(conn, original["id"], major="data_science")
        assert replacement["review_status"] == "pending"
        path = tmp_path / "reviews.json"
        path.write_text(json.dumps({original["id"]: snapshot_decision(reviewed)}), encoding="utf-8")
        result = service.sync_crawled_documents_and_reviews(conn, empty, path)
        assert result["reviews_applied"] == 0
        after = service.get_document(conn, replacement["id"])
        assert after["review_status"] == "pending"
        assert after["reviewer_id"] is None and after["reviewed_at"] is None
        assert after["major"] == "data_science"


def test_failed_export_after_api_commit_cannot_restore_old_approval(tmp_path, monkeypatch):
    """Two real connections verify committed rejection survives replay of old JSON."""
    eng = admin_test_engine()
    actor_id = str(uuid.uuid4())
    did = "review_restore_" + uuid.uuid4().hex[:12]
    empty = tmp_path / "empty"
    empty.mkdir()
    path = tmp_path / "reviews.json"

    async def authenticated_admin(request):
        return {"role": "admin", "account_id": actor_id, "email": "synthetic@example.invalid"}

    def fail_export(*args, **kwargs):
        raise PermissionError("Synthetic export lock after DB commit")

    monkeypatch.setattr(admin_api, "engine", lambda: eng)
    monkeypatch.setattr(admin_api, "require_account", authenticated_admin)
    # Audit transaction failure has separate coverage; avoid leaving append-only
    # audit records for this test's independently committed synthetic actor.
    monkeypatch.setattr(admin_api, "log_admin_action", lambda *args, **kwargs: None)
    try:
        with eng.begin() as conn:
            conn.execute(text("""INSERT INTO accounts(id,username,password_hash,role)
                VALUES(:id,:name,'synthetic-test-only','admin')"""),
                         {"id": actor_id, "name": "restore_" + uuid.uuid4().hex[:12]})
            service.create_document(conn, url="https://example.invalid/" + did,
                                    title="Synthetic source", markdown_content=BODY, doc_id=did)
            service.review_document(conn, did, "approved", "Initial approval", actor_id)
        service.export_git_reviews_from_db(eng, path)
        old_file = path.read_bytes()
        assert json.loads(old_file)[did]["review_status"] == "approved"
        monkeypatch.setattr(admin_api, "export_git_reviews_from_db", fail_export)
        response = asyncio.run(admin_api.reject_crawled_document(
            MagicMock(), did, admin_api.DocumentReviewActionRequest(reason="New rejection"),
        ))
        assert response["review_status"] == "rejected"
        assert path.read_bytes() == old_file
        with eng.begin() as conn:
            committed = service.get_document(conn, did)
            assert committed["review_status"] == "rejected"
            service.sync_crawled_documents_and_reviews(conn, empty, path)
            after = service.get_document(conn, did)
            assert after["review_status"] == "rejected"
            assert after["reviewed_at"] == committed["reviewed_at"]
            assert after["review_reason"] == "New rejection"
    finally:
        with eng.begin() as conn:
            conn.execute(text("DELETE FROM crawled_documents WHERE id=:id"), {"id": did})
            conn.execute(text("DELETE FROM accounts WHERE id=:id"), {"id": actor_id})
        eng.dispose()


def taxonomy_fixture(conn, tmp_path, status):
    conn.execute(text("UPDATE accounts SET email_verified_at=now(),is_active=true WHERE id=:id"),
                 {"id": REVIEWER_ID})
    url = "https://example.invalid/" + uuid.uuid4().hex
    doc = service.create_document(conn, url=url, title="Hóa dược", markdown_content=BODY,
                                  major="mathematics")
    if status in {"approved", "published"}:
        service.review_document(conn, doc["id"], "approved", "Original review", REVIEWER_ID)
    if status == "published":
        conn.execute(text("UPDATE crawled_documents SET is_published=true WHERE id=:id"), {"id": doc["id"]})
    docs = tmp_path / "documents"
    docs.mkdir()
    source = docs / "hoa-duoc.md"
    source.write_text(f"---\ntitle: Hóa dược\nurl: {url}\nmajor: mathematics\n---\n{BODY}", encoding="utf-8")
    plan = remediation.build_plan(docs, remediation.read_inventory(conn))
    return service.get_document(conn, doc["id"]), docs, source, plan


@pytest.mark.parametrize("status", ["pending", "approved", "published"])
def test_taxonomy_apply_audits_and_preserves_reviewed_versions(tmp_path, status):
    with db_transaction_rollback() as conn:
        original, docs, source, plan = taxonomy_fixture(conn, tmp_path, status)
        source_bytes = source.read_bytes()
        result = remediation.apply_plan(conn, docs, plan, expected_plan_sha256=plan["plan_sha256"],
                                        actor_id=REVIEWER_ID, reason="Reviewed taxonomy correction")
        assert len(result) == 1
        changed_id = result[0]["result_document_id"]
        updated = service.get_document(conn, changed_id)
        assert updated["major"] == "general" and updated["review_status"] == "pending"
        if status != "pending":
            assert changed_id != original["id"]
            preserved = service.get_document(conn, original["id"])
            assert preserved["major"] == "mathematics"
            assert preserved["review_status"] == original["review_status"]
            assert preserved["is_published"] == original["is_published"]
        else:
            assert changed_id == original["id"]
        assert conn.execute(text("""SELECT count(*) FROM admin_audit_logs
            WHERE action='crawler.document.taxonomy_remediation' AND target_id=:id"""),
                            {"id": original["id"]}).scalar_one() == 1
        assert source.read_bytes() == source_bytes
        assert remediation.build_plan(docs, remediation.read_inventory(conn))["actions"] == []


def test_taxonomy_apply_rolls_back_replacement_when_audit_fails(tmp_path, monkeypatch):
    with db_transaction_rollback() as conn:
        original, docs, source, plan = taxonomy_fixture(conn, tmp_path, "published")
        before = remediation.read_inventory(conn)

        def failed_audit(*args, **kwargs):
            raise RuntimeError("Synthetic audit failure")

        monkeypatch.setattr(remediation, "log_admin_action", failed_audit)
        with pytest.raises(RuntimeError, match="audit failure"):
            with conn.begin_nested():
                remediation.apply_plan(conn, docs, plan, expected_plan_sha256=plan["plan_sha256"],
                                        actor_id=REVIEWER_ID, reason="Reviewed taxonomy correction")
        assert remediation.read_inventory(conn) == before
        assert service.get_document(conn, original["id"])["is_published"] is True


def test_taxonomy_apply_rejects_changed_inventory_before_writing(tmp_path):
    with db_transaction_rollback() as conn:
        original, docs, source, plan = taxonomy_fixture(conn, tmp_path, "pending")
        service.update_document_metadata(conn, original["id"], title="Concurrent title change")
        with pytest.raises(ValueError, match="stale"):
            remediation.apply_plan(conn, docs, plan, expected_plan_sha256=plan["plan_sha256"],
                                    actor_id=REVIEWER_ID, reason="Reviewed taxonomy correction")
        assert service.get_document(conn, original["id"])["major"] == "mathematics"
