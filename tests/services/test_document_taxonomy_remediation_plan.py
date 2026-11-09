"""Offline plan safety and explicit apply boundary tests; no DB connection is opened."""

import copy
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.crawler.document_review_service import compute_content_hash
from tools import plan_document_taxonomy_remediation as remediation

ACTOR_ID = "57e9a52b-7365-4fe2-b9ce-1320ef48dc02"
CONTENT = "Nội dung giới thiệu ngành Hóa dược được đối chiếu với nguồn tài liệu đã lưu."


@pytest.fixture
def source_and_rows(tmp_path):
    docs = tmp_path / "documents"
    docs.mkdir()
    source = docs / "hoa-duoc.md"
    source.write_text(
        "---\ntitle: Hóa dược\nurl: https://mim.hus.vnu.edu.vn/vi/hoa-duoc\n"
        "major: mathematics\n---\n" + CONTENT,
        encoding="utf-8",
    )
    row = {
        "id": "doc_existing", "url": "http://mim.hus.vnu.edu.vn/vi/hoa-duoc",
        "content_hash": compute_content_hash(CONTENT), "title": "Hóa dược",
        "major": "mathematics", "doc_type": "general_info", "metadata_json": {"version": 1},
        "review_status": "pending", "is_published": False,
    }
    return docs, [row]


def test_plan_existing_rows_normalizes_url_and_preserves_inputs(source_and_rows):
    docs, rows = source_and_rows
    original_rows = copy.deepcopy(rows)
    original_source = (docs / "hoa-duoc.md").read_bytes()
    plan = remediation.build_plan(docs, rows)
    assert plan["actions"] == [{
        "document_id": "doc_existing",
        "expected_fingerprint": remediation._sha256(rows[0]),
        "current_major": "mathematics", "target_major": "general",
        "action": "update_draft_metadata", "source_paths": ["hoa-duoc.md"],
    }]
    assert plan["conflicts"] == []
    assert rows == original_rows
    assert (docs / "hoa-duoc.md").read_bytes() == original_source
    assert plan == remediation.build_plan(docs, rows)


@pytest.mark.parametrize("status,published", [("approved", False), ("approved", True)])
def test_reviewed_or_published_proposes_pending_replacement(source_and_rows, status, published):
    docs, rows = source_and_rows
    rows[0].update(review_status=status, is_published=published)
    plan = remediation.build_plan(docs, rows)
    assert plan["actions"][0]["action"] == "create_pending_replacement"
    assert rows[0]["review_status"] == status
    assert rows[0]["is_published"] is published


def test_completed_replacement_is_not_proposed_again(source_and_rows):
    docs, rows = source_and_rows
    rows[0].update(review_status="approved", is_published=True)
    replacement = copy.deepcopy(rows[0])
    replacement.update(
        id="doc_prepared", major="general", review_status="pending", is_published=False,
        metadata_json={"previous_document_id": rows[0]["id"], "version": 2},
    )
    rows.append(replacement)
    assert remediation.build_plan(docs, rows)["actions"] == []


def test_changed_content_and_ambiguous_source_are_blocked(source_and_rows):
    docs, rows = source_and_rows
    rows[0]["content_hash"] = compute_content_hash("Different content")
    plan = remediation.build_plan(docs, rows)
    assert plan["actions"] == []
    assert plan["conflicts"][0]["reason"] == "source_content_hash_changed"
    (docs / "other.md").write_text(
        "---\ntitle: Another\nurl: http://mim.hus.vnu.edu.vn/vi/hoa-duoc\n"
        "major: mathematics\n---\nUnrelated body",
        encoding="utf-8",
    )
    assert remediation.build_plan(docs, rows)["conflicts"][0]["reason"] == "ambiguous_source_url"


def test_plan_digest_binds_sources_and_metadata(source_and_rows):
    docs, rows = source_and_rows
    initial = remediation.build_plan(docs, rows)["plan_sha256"]
    rows[0]["metadata_json"]["version"] = 2
    assert remediation.build_plan(docs, rows)["plan_sha256"] != initial
    rows[0]["metadata_json"]["version"] = 1
    source = docs / "hoa-duoc.md"
    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert remediation.build_plan(docs, rows)["plan_sha256"] != initial


def _apply_boundary(monkeypatch, rows):
    conn = MagicMock()
    conn.execute.return_value.mappings.return_value.one_or_none.return_value = {
        "role": "admin", "is_active": True, "email_verified_at": "verified",
    }
    monkeypatch.setattr(remediation, "read_inventory", lambda connection, lock=False: rows)
    update = MagicMock(return_value={"id": "doc_new_pending"})
    audit = MagicMock()
    monkeypatch.setattr(remediation, "update_document_metadata", update)
    monkeypatch.setattr(remediation, "log_admin_action", audit)
    return conn, update, audit


def test_apply_stale_or_tampered_plan_never_mutates(source_and_rows, monkeypatch):
    docs, rows = source_and_rows
    plan = remediation.build_plan(docs, rows)
    conn, update, audit = _apply_boundary(monkeypatch, rows)
    rows[0]["title"] = "Concurrent title change"
    with pytest.raises(ValueError, match="stale"):
        remediation.apply_plan(
            conn, docs, plan, expected_plan_sha256=plan["plan_sha256"],
            actor_id=ACTOR_ID, reason="Reviewed taxonomy correction",
        )
    update.assert_not_called()
    audit.assert_not_called()
    plan["actions"][0]["target_major"] = "computer_science"
    with pytest.raises(ValueError, match="digest"):
        remediation.apply_plan(
            conn, docs, plan, expected_plan_sha256=plan["plan_sha256"],
            actor_id=ACTOR_ID, reason="Reviewed taxonomy correction",
        )
    update.assert_not_called()


@pytest.mark.parametrize("status,published", [("pending", False), ("approved", False), ("approved", True)])
def test_apply_uses_metadata_service_and_same_connection_audit(
    source_and_rows, monkeypatch, status, published,
):
    docs, rows = source_and_rows
    rows[0].update(review_status=status, is_published=published)
    plan = remediation.build_plan(docs, rows)
    conn, update, audit = _apply_boundary(monkeypatch, rows)
    result = remediation.apply_plan(
        conn, docs, plan, expected_plan_sha256=plan["plan_sha256"],
        actor_id=ACTOR_ID, reason="Reviewed taxonomy correction",
    )
    update.assert_called_once_with(conn, "doc_existing", major="general")
    assert audit.call_args.kwargs["conn"] is conn
    assert audit.call_args.kwargs["actor_id"] == ACTOR_ID
    assert audit.call_args.kwargs["details"]["operation"] == plan["actions"][0]["action"]
    assert result == [{"document_id": "doc_existing", "result_document_id": "doc_new_pending"}]
    # Transaction ownership stays with the caller, including audit failure rollback.
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_apply_rejects_non_admin_and_propagates_audit_failure(source_and_rows, monkeypatch):
    docs, rows = source_and_rows
    plan = remediation.build_plan(docs, rows)
    conn, update, audit = _apply_boundary(monkeypatch, rows)
    actor = conn.execute.return_value.mappings.return_value.one_or_none.return_value
    actor["role"] = "student"
    with pytest.raises(ValueError, match="administrator"):
        remediation.apply_plan(
            conn, docs, plan, expected_plan_sha256=plan["plan_sha256"],
            actor_id=ACTOR_ID, reason="Reviewed taxonomy correction",
        )
    update.assert_not_called()
    actor["role"] = "admin"
    audit.side_effect = RuntimeError("Synthetic audit failure")
    with pytest.raises(RuntimeError, match="audit failure"):
        remediation.apply_plan(
            conn, docs, plan, expected_plan_sha256=plan["plan_sha256"],
            actor_id=ACTOR_ID, reason="Reviewed taxonomy correction",
        )


def test_offline_cli_is_plan_only_and_refuses_overwrite(source_and_rows, tmp_path, monkeypatch):
    docs, rows = source_and_rows
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "plan.json"
    engine_factory = MagicMock(side_effect=AssertionError("No database allowed"))
    monkeypatch.setattr(remediation, "create_engine", engine_factory)
    args = ["--docs-dir", str(docs), "--inventory-json", str(inventory), "--output", str(output)]
    assert remediation.main(args) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["mode"] == "taxonomy_remediation_plan"
    original = output.read_bytes()
    assert remediation.main(args) == 1
    assert output.read_bytes() == original
    engine_factory.assert_not_called()
    with pytest.raises(SystemExit):
        remediation.main([*args, "--apply", str(output)])


def test_default_database_inventory_transaction_is_read_only(source_and_rows, monkeypatch, capsys):
    docs, rows = source_and_rows
    engine = MagicMock()
    conn = engine.begin.return_value.__enter__.return_value
    conn.execute.return_value.mappings.return_value.all.return_value = rows
    monkeypatch.setenv("SYNTHETIC_TAXONOMY_DB", "postgresql://synthetic:synthetic@127.0.0.1/ai07")
    monkeypatch.setattr(remediation, "create_engine", lambda url: engine)
    assert remediation.main([
        "--docs-dir", str(docs), "--database-url-env", "SYNTHETIC_TAXONOMY_DB",
    ]) == 0
    assert str(conn.execute.call_args_list[0].args[0]) == "SET TRANSACTION READ ONLY"
    assert json.loads(capsys.readouterr().out)["mode"] == "taxonomy_remediation_plan"
    engine.dispose.assert_called_once()


def test_cli_apply_audit_failure_exits_transaction_with_error(source_and_rows, tmp_path, monkeypatch):
    docs, rows = source_and_rows
    plan = remediation.build_plan(docs, rows)
    plan_file = tmp_path / "approved_plan.json"
    plan_file.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    conn, update, audit = _apply_boundary(monkeypatch, rows)
    engine = MagicMock()
    engine.begin.return_value.__enter__.return_value = conn
    engine.begin.return_value.__exit__.return_value = False
    audit.side_effect = RuntimeError("Synthetic audit failure")
    monkeypatch.setenv("SYNTHETIC_TAXONOMY_DB", "postgresql://synthetic:synthetic@127.0.0.1/ai07")
    monkeypatch.setattr(remediation, "create_engine", lambda url: engine)
    assert remediation.main([
        "--docs-dir", str(docs), "--database-url-env", "SYNTHETIC_TAXONOMY_DB",
        "--apply", str(plan_file), "--expected-plan-sha256", plan["plan_sha256"],
        "--actor-id", ACTOR_ID, "--reason", "Reviewed taxonomy correction",
    ]) == 1
    update.assert_called_once()
    # Engine.begin receives the error and therefore rolls back, never commits partial audit work.
    assert engine.begin.return_value.__exit__.call_args.args[0] is RuntimeError
    engine.dispose.assert_called_once()


def test_receipt_write_failure_reports_confirmed_commit(
    source_and_rows, tmp_path, monkeypatch, capsys,
):
    docs, rows = source_and_rows
    plan = remediation.build_plan(docs, rows)
    plan_file = tmp_path / "approved_plan.json"
    plan_file.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    output_file = tmp_path / "new_receipt.json"
    conn, update, audit = _apply_boundary(monkeypatch, rows)
    engine = MagicMock()
    engine.begin.return_value.__enter__.return_value = conn
    engine.begin.return_value.__exit__.return_value = False
    monkeypatch.setenv("SYNTHETIC_TAXONOMY_DB", "postgresql://synthetic:synthetic@127.0.0.1/ai07")
    monkeypatch.setattr(remediation, "create_engine", lambda url: engine)
    original_open = Path.open

    def fail_receipt_open(path, mode="r", *args, **kwargs):
        if path == output_file and mode == "x":
            raise OSError("Synthetic output failure after commit")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_receipt_open)
    assert remediation.main([
        "--docs-dir", str(docs), "--database-url-env", "SYNTHETIC_TAXONOMY_DB",
        "--apply", str(plan_file), "--expected-plan-sha256", plan["plan_sha256"],
        "--actor-id", ACTOR_ID, "--reason", "Reviewed taxonomy correction",
        "--output", str(output_file),
    ]) == 2
    assert engine.begin.return_value.__exit__.call_args.args == (None, None, None)
    update.assert_called_once()
    audit.assert_called_once()
    error = capsys.readouterr().err
    assert "committed=true" in error
    assert "Do not rerun --apply" in error
    assert plan["plan_sha256"] in error
    assert "doc_new_pending" in error
    assert "no success is claimed" not in error
    engine.dispose.assert_called_once()
