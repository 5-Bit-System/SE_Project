"""Tests for document review sync lifecycle in FastAPI lifespan."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


def test_startup_sync_disabled_by_default(monkeypatch):
    """By default, auto_sync_document_reviews is False and startup sync is not invoked."""
    get_settings.cache_clear()
    settings = get_settings()
    assert hasattr(settings, "auto_sync_document_reviews"), (
        "Settings missing auto_sync_document_reviews"
    )
    assert settings.auto_sync_document_reviews is False

    with patch(
        "app.crawler.document_review_service.sync_crawled_documents_and_reviews"
    ) as mock_sync:
        with TestClient(app, base_url="http://127.0.0.1:8000"):
            pass
        mock_sync.assert_not_called()


def test_auto_sync_env_var_parsing(monkeypatch):
    """Verify AUTO_SYNC_DOCUMENT_REVIEWS environment variable parsing."""
    try:
        monkeypatch.setenv("AUTO_SYNC_DOCUMENT_REVIEWS", "true")
        get_settings.cache_clear()
        assert get_settings().auto_sync_document_reviews is True

        monkeypatch.setenv("AUTO_SYNC_DOCUMENT_REVIEWS", "1")
        get_settings.cache_clear()
        assert get_settings().auto_sync_document_reviews is True

        monkeypatch.setenv("AUTO_SYNC_DOCUMENT_REVIEWS", "false")
        get_settings.cache_clear()
        assert get_settings().auto_sync_document_reviews is False

        monkeypatch.delenv("AUTO_SYNC_DOCUMENT_REVIEWS", raising=False)
        get_settings.cache_clear()
        assert get_settings().auto_sync_document_reviews is False
    finally:
        get_settings.cache_clear()


def test_startup_sync_executes_when_flag_enabled(monkeypatch):
    """When auto_sync_document_reviews=True and storage_backend=postgres, sync runs on startup."""
    mock_conn = MagicMock()

    @contextmanager
    def fake_begin():
        yield mock_conn

    mock_engine = MagicMock()
    mock_engine.begin = fake_begin

    base_settings = get_settings()
    enabled_settings = Settings(
        storage_backend="postgres",
        database_model=base_settings.database_model,
        database_url="postgresql+psycopg2://user:pass@localhost:5432/testdb",
        gemini_api_key=base_settings.gemini_api_key,
        gemini_base_url=base_settings.gemini_base_url,
        gemini_model=base_settings.gemini_model,
        recommendation_llm_enabled=base_settings.recommendation_llm_enabled,
        auto_sync_document_reviews=True,
    )
    monkeypatch.setattr("app.main.get_settings", lambda: enabled_settings)

    with (
        patch("app.main.check_storage_ready"),
        patch("app.main.check_auth_ready"),
        patch("app.api.admin.engine", return_value=mock_engine),
        patch(
            "app.crawler.document_review_service.sync_crawled_documents_and_reviews",
            return_value={"seeded": 179, "total": 179, "reviews_applied": 30},
        ) as mock_sync,
    ):
        with TestClient(app, base_url="http://127.0.0.1:8000"):
            pass

        mock_sync.assert_called_once_with(mock_conn)


def test_startup_sync_skipped_when_not_postgres(monkeypatch):
    """When storage_backend is not postgres, startup sync is skipped even if flag is True."""
    base_settings = get_settings()
    json_settings = Settings(
        storage_backend="json",
        database_model=base_settings.database_model,
        database_url=base_settings.database_url,
        gemini_api_key=base_settings.gemini_api_key,
        gemini_base_url=base_settings.gemini_base_url,
        gemini_model=base_settings.gemini_model,
        recommendation_llm_enabled=base_settings.recommendation_llm_enabled,
        auto_sync_document_reviews=True,
    )
    monkeypatch.setattr("app.main.get_settings", lambda: json_settings)

    with patch(
        "app.crawler.document_review_service.sync_crawled_documents_and_reviews"
    ) as mock_sync:
        # check_storage_ready requires 4 catalogs for json backend, mock it if needed
        with patch("app.main.check_storage_ready"):
            with TestClient(app, base_url="http://127.0.0.1:8000"):
                pass
        mock_sync.assert_not_called()


def test_startup_sync_handles_exception_gracefully(monkeypatch, caplog):
    """When startup sync encounters an exception, it logs a warning without crashing."""
    mock_conn = MagicMock()

    @contextmanager
    def fake_begin():
        yield mock_conn

    mock_engine = MagicMock()
    mock_engine.begin = fake_begin

    base_settings = get_settings()
    enabled_settings = Settings(
        storage_backend="postgres",
        database_model=base_settings.database_model,
        database_url="postgresql+psycopg2://user:pass@localhost:5432/testdb",
        gemini_api_key=base_settings.gemini_api_key,
        gemini_base_url=base_settings.gemini_base_url,
        gemini_model=base_settings.gemini_model,
        recommendation_llm_enabled=base_settings.recommendation_llm_enabled,
        auto_sync_document_reviews=True,
    )
    monkeypatch.setattr("app.main.get_settings", lambda: enabled_settings)

    with (
        patch("app.main.check_storage_ready"),
        patch("app.main.check_auth_ready"),
        patch("app.api.admin.engine", return_value=mock_engine),
        patch(
            "app.crawler.document_review_service.sync_crawled_documents_and_reviews",
            side_effect=RuntimeError("database locked or unavailable"),
        ),
    ):
        with caplog.at_level("WARNING"):
            with TestClient(app, base_url="http://127.0.0.1:8000"):
                pass

        assert any(
            "Startup document review sync failed" in record.message for record in caplog.records
        )
