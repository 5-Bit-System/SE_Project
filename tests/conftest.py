"""The default suite is offline and never depends on local .env secrets."""

import os

# Set before collection, including imports of app.main and settings consumers.
os.environ["STORAGE_BACKEND"] = "json"
os.environ["DATABASE_URL"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["RECOMMENDATION_LLM_ENABLED"] = "false"

import httpx
import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "json")
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("RECOMMENDATION_LLM_ENABLED", "false")
    get_settings.cache_clear()
    network_attempts = []

    def blocked_network(*args, **kwargs):
        network_attempts.append("sync")
        raise AssertionError("Real outbound HTTP is forbidden in tests; mock the provider")

    async def blocked_async_network(*args, **kwargs):
        network_attempts.append("async")
        raise AssertionError("Real outbound HTTP is forbidden in tests; mock the provider")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked_network)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", blocked_async_network)
    yield
    get_settings.cache_clear()
    assert not network_attempts, (
        "A test attempted outbound HTTP, even if fallback swallowed the error"
    )
