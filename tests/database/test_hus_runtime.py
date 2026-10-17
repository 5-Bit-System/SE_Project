"""Offline checks for HUS runtime selection and private profile boundaries."""

import sys
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.infrastructure.json_catalog_repository import list_catalogs
from app.main import app


def test_database_model_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("DATABASE_MODEL", "unknown")
    with pytest.raises(ValueError, match="DATABASE_MODEL"):
        get_settings()


def test_hus_mode_uses_hus_repository_and_hides_student_profiles(monkeypatch, catalog_root):
    calls = []

    class FakeHusRepository:
        def __init__(self):
            calls.append("construct")

        def ready(self):
            calls.append("ready")

        def list_catalogs(self):
            calls.append("list_catalogs")
            return list_catalogs(catalog_root)

        def load_catalog(self, program_id):
            calls.append("load_catalog")
            from app.infrastructure.json_catalog_repository import load_catalog

            return load_catalog(program_id, catalog_root)

        def read_profiles(self):
            calls.append("read_profiles")
            return []

    module = ModuleType("app.infrastructure.hus_repository")
    module.HusRepository = FakeHusRepository
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setenv("STORAGE_BACKEND", "postgres")
    monkeypatch.setenv("DATABASE_MODEL", "hus")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://user:secret@localhost/ai07")

    with TestClient(app) as client:
        assert client.get("/ready").json() == {"status": "ok", "storage": "postgres"}
        assert len(client.get("/programs").json()) == 4
        assert client.get("/courses", params={"program_id": "khdl"}).status_code == 200
        assert client.get("/profiles").json() == []
        assert client.get("/profiles", params={"program_id": "khdl"}).json() == []
        assert client.get("/profiles/student-1").status_code == 404
        assert client.get("/profiles/student-1/transcript/summary").status_code == 404
    assert {"ready", "list_catalogs", "load_catalog", "read_profiles"} <= set(calls)
