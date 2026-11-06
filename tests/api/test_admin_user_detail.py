"""Admin account detail exposes only account metadata and bounded activity."""

from fastapi.testclient import TestClient

from app.auth import repository
from app.main import app

ACCOUNT_ID = "00000000-0000-4000-8000-000000000123"


def test_account_detail_requires_admin(verified_client, fake_accounts):
    assert verified_client.get(f"/admin/users/{ACCOUNT_ID}").status_code == 403
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"
    assert verified_client.get("/admin/users/not-a-uuid").status_code == 400


def test_account_detail_anonymous_rejected():
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        assert client.get(f"/admin/users/{ACCOUNT_ID}").status_code == 401


def test_account_detail_returns_source_events(verified_client, fake_accounts, monkeypatch):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"
    expected = {
        "account": {"id": ACCOUNT_ID, "vnu_subject": "synthetic-student", "email": None,
                    "display_name": "Synthetic", "role": "student", "is_active": True,
                    "created_at": "2026-11-05T00:00:00Z"},
        "events": [{"kind": "login_vnu", "created_at": "2026-11-05T01:00:00Z"}],
    }
    monkeypatch.setattr(repository, "account_detail", lambda principal, account_id: expected)
    response = verified_client.get(f"/admin/users/{ACCOUNT_ID}")
    assert response.status_code == 200
    assert response.json() == expected
