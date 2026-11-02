import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.errors import StorageDataError, StorageUnavailable
from app.main import app
from app.recommendation.llm import configured_adapters


def test_configuration_rejects_invalid_backend(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "unknown")
    with pytest.raises(ValueError, match="STORAGE_BACKEND"):
        get_settings()


@pytest.mark.parametrize("url", ["", "sqlite:///demo.db", "not-a-url"])
@pytest.mark.parametrize("model", ["hus", "legacy"])
def test_postgres_configuration_requires_postgres_url(monkeypatch, url, model):
    monkeypatch.setenv("STORAGE_BACKEND", "postgres")
    monkeypatch.setenv("DATABASE_MODEL", model)
    monkeypatch.setenv("DATABASE_URL", url)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        get_settings()


def test_offline_settings_override_local_env_and_disable_provider():
    settings = get_settings()
    assert settings.storage_backend == "json"
    assert settings.gemini_api_key == ""
    assert configured_adapters() == (None, None)
    assert "gemini" not in repr(settings).lower()


def test_json_readiness_and_liveness():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/ready").json() == {"status": "ok", "storage": "json"}


def test_postgres_outage_returns_503_without_json_fallback(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "postgres")
    monkeypatch.setenv("DATABASE_MODEL", "legacy")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://user:secret@127.0.0.1/demo")

    def unavailable(*args, **kwargs):
        raise StorageUnavailable("PostgreSQL chưa sẵn sàng")

    monkeypatch.setattr(
        "app.infrastructure.postgres_repository.PostgresRepository.load_catalog", unavailable
    )
    response = TestClient(app).get("/courses", params={"program_id": "khdl"})
    assert response.status_code == 503
    assert "secret" not in response.text
    assert "PHI1006" not in response.text


def test_server_data_error_is_not_a_client_validation_error(monkeypatch):
    def invalid(*args, **kwargs):
        raise StorageDataError("Internal detail must not be exposed")

    monkeypatch.setattr("app.api.routes.load_catalog", invalid)
    response = TestClient(app).get("/courses", params={"program_id": "khdl"})
    assert response.status_code == 500
    assert "Internal detail" not in response.text
