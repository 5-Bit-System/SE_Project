"""Unit tests for audit service redaction and query operations."""

from unittest.mock import MagicMock

from app.audit.service import (
    get_audit_trail,
    log_admin_action,
    redact_sensitive_payload,
)


def test_redact_sensitive_payload():
    raw = {
        "user_email": "admin@hus.vnu.edu.vn",
        "password": "SuperSecretPassword123",
        "nested": {
            "token": "bearer_jwt_token_xyz",
            "session_id": "sess_abc",
            "safe_field": 42,
            "vnu_password": "raw_pass_secret",
        },
        "items": [
            {"id": 1, "secret_key": "private_key_abc"},
            {"id": 2, "title": "Normal title"},
        ],
        "long_text": "A" * 600,
    }

    clean = redact_sensitive_payload(raw)

    assert clean["user_email"] == "admin@hus.vnu.edu.vn"
    assert clean["password"] == "[REDACTED]"
    assert clean["nested"]["token"] == "[REDACTED]"
    assert clean["nested"]["session_id"] == "[REDACTED]"
    assert clean["nested"]["vnu_password"] == "[REDACTED]"
    assert clean["nested"]["safe_field"] == 42
    assert clean["items"][0]["secret_key"] == "[REDACTED]"
    assert clean["items"][1]["title"] == "Normal title"
    assert "TRUNCATED 600 chars" in clean["long_text"]
    assert len(clean["long_text"]) < 300


def test_log_admin_action_calls_insert(monkeypatch):
    mock_conn = MagicMock()
    mock_insert = MagicMock(return_value={"id": 1, "action": "catalog.publish"})
    monkeypatch.setattr("app.audit.service.insert_audit_log", mock_insert)

    res = log_admin_action(
        conn=mock_conn,
        actor_id="00000000-0000-0000-0000-000000000001",
        actor_email="admin@hus.edu.vn",
        action="catalog.publish",
        target_type="catalog_revision",
        target_id="rev_101",
        result="ok",
        summary="Published revision rev_101",
        details={"token": "secret_abc", "version": "v1.0"},
    )

    assert res["id"] == 1
    mock_insert.assert_called_once()
    call_kwargs = mock_insert.call_args[1]
    assert call_kwargs["action"] == "catalog.publish"
    assert call_kwargs["details"]["token"] == "[REDACTED]"
    assert call_kwargs["details"]["version"] == "v1.0"


def test_get_audit_trail_bounds(monkeypatch):
    mock_conn = MagicMock()
    mock_query = MagicMock(return_value=([], 0))
    monkeypatch.setattr("app.audit.service.query_audit_logs", mock_query)

    get_audit_trail(mock_conn, limit=999, offset=-10)
    mock_query.assert_called_once_with(
        conn=mock_conn,
        action_group=None,
        target_type=None,
        actor_id=None,
        query=None,
        limit=200,  # Clamped to max 200
        offset=0,  # Clamped to min 0
    )
