"""Consultation activity stores metadata, never message or grade content."""

import pytest

from app.auth import repository


class FakeConnection:
    def __init__(self):
        self.calls = []

    def execute(self, statement, values):
        self.calls.append((str(statement), values))


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection

    def begin(self):
        return self

    def __enter__(self):
        return self.connection

    def __exit__(self, *_):
        return False


def test_record_activity_keeps_only_account_and_kind(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(repository, "engine", lambda: FakeEngine(connection))

    repository.record_activity("00000000-0000-4000-8000-000000000123", "advisor")

    assert len(connection.calls) == 1
    sql, params = connection.calls[0]
    assert "account_activity_events" in sql
    assert params == {"account_id": "00000000-0000-4000-8000-000000000123", "kind": "advisor"}
    with pytest.raises(ValueError):
        repository.record_activity(params["account_id"], "arbitrary")
    assert len(connection.calls) == 1
