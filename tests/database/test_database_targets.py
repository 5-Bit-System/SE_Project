"""Unsafe integration targets must fail before an engine can be created."""

import importlib

import pytest

from tests.support.postgres_targets import (
    validate_hus_test_target,
    validate_legacy_test_target,
)


@pytest.mark.parametrize(
    ("validator", "database"),
    [
        (validate_hus_test_target, "ai07"),
        (validate_legacy_test_target, "se_project_test"),
    ],
)
@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
@pytest.mark.parametrize("query", ["", "?sslmode=disable"])
def test_local_test_target_is_accepted(validator, database, host, query):
    target = validator(f"postgresql+psycopg2://user:secret@{host}:5433/{database}{query}")
    assert target.host == host
    assert target.database == database


@pytest.mark.parametrize(
    ("validator", "database"),
    [
        (validate_hus_test_target, "ai07"),
        (validate_legacy_test_target, "se_project_test"),
    ],
)
@pytest.mark.parametrize(
    "url_template",
    [
        "postgresql+psycopg2://user:secret@example.invalid:5433/{database}",
        "postgresql+psycopg2://user:secret@127.0.0.1:5433/production",
        "postgresql+psycopg2://user:secret@localhost:5433/{database}?host=example.invalid",
        "postgresql+psycopg2://user:secret@localhost:5433/{database}?hostaddr=203.0.113.1",
        "postgresql+psycopg2://user:secret@localhost:5433/{database}?dbname=production",
        "postgresql+psycopg2://user:secret@localhost:5433/{database}?service=remote",
        "postgresql+pg8000://user:secret@localhost:5433/{database}",
        "mysql+pymysql://user:secret@localhost:5433/{database}",
        "not-a-url",
    ],
)
def test_unsafe_test_target_is_rejected(validator, database, url_template):
    with pytest.raises(ValueError, match=f"local {database}"):
        validator(url_template.format(database=database))


@pytest.mark.parametrize(
    ("module_name", "fixture_name", "variable", "engine_name", "database"),
    [
        ("tests.database.test_hus_postgres", "hus_engine", "HUS_TEST_DATABASE_URL",
         "create_engine_for", "ai07"),
        ("tests.database.test_database", "postgres_engine", "TEST_DATABASE_URL",
         "create_engine", "se_project_test"),
    ],
)
def test_integration_fixture_rejects_redirect_before_engine(
    monkeypatch, module_name, fixture_name, variable, engine_name, database
):
    module = importlib.import_module(module_name)
    monkeypatch.setenv(
        variable,
        f"postgresql+psycopg2://user:secret@localhost:5433/{database}?host=remote.invalid",
    )

    def reject_engine_creation(*args, **kwargs):
        raise AssertionError("Engine created before test target validation")

    monkeypatch.setattr(module, engine_name, reject_engine_creation)
    with pytest.raises(ValueError, match=f"local {database}"):
        next(getattr(module, fixture_name).__wrapped__())
