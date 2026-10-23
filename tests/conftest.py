"""The default suite is offline and never depends on local .env secrets."""

import os

# Set before collection, including imports of app.main and settings consumers.
os.environ["STORAGE_BACKEND"] = "json"
os.environ["DATABASE_MODEL"] = "hus"
os.environ["DATABASE_URL"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["RECOMMENDATION_LLM_ENABLED"] = "false"

import httpx
import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch, catalog_root, profiles_path):
    monkeypatch.setattr("app.catalog.DATA_ROOT", catalog_root)
    monkeypatch.setattr("app.profiles.PROFILES_PATH", profiles_path)
    monkeypatch.setenv("STORAGE_BACKEND", "json")
    monkeypatch.setenv("DATABASE_MODEL", "hus")
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


@pytest.fixture(scope="session")
def catalog_root(tmp_path_factory):
    from tests.support.catalog_fixtures import create_catalog_fixture

    root, _ = create_catalog_fixture(tmp_path_factory.mktemp("offline_catalogs"))
    return root


@pytest.fixture(scope="session")
def profiles_path(catalog_root):
    return catalog_root.parent / "demo_profiles.json"


@pytest.fixture
def toy_catalog():
    from tests.support.catalog_fixtures import get_toy_catalog

    return get_toy_catalog()


def pytest_addoption(parser):
    parser.addoption(
        "--full-catalog-root",
        type=str,
        default=None,
        help="Explicit root for legacy four-catalog files or HUS PDF expectations",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--full-catalog-root") is None:
        skip = pytest.mark.skip(reason="Full source acceptance requires --full-catalog-root")
        for item in items:
            if "full_catalog_acceptance" in item.keywords:
                item.add_marker(skip)


@pytest.fixture
def full_catalog_root(request):
    from pathlib import Path

    value = request.config.getoption("--full-catalog-root")
    if value is None:
        pytest.skip("Full source acceptance requires --full-catalog-root")
    root = Path(value).resolve()
    if not root.is_dir():
        pytest.fail(f"Explicit full catalog root does not exist: {root}")
    return root
