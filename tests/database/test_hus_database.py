"""Offline tests for the HUS/Neon database module.

These tests never touch a database or the network: they exercise the pure
configuration, rendering and verification helpers with synthetic data.
"""

from __future__ import annotations

import pytest

from database.hus_db.config import (
    ENV_VAR,
    HusDatabaseConfig,
    HusDatabaseConfigError,
    is_postgres_url,
    load_config,
    redact_url,
    with_ssl_required,
)
from database.hus_db.connection import create_engine_for
from database.hus_db.introspect import (
    CORE_TABLES,
    OFFICIAL_TABLES,
    VIEW_NAMES,
    ColumnInfo,
    SchemaSnapshot,
    TableInfo,
    read_row_counts,
    render_schema_markdown,
    render_schema_text,
)
from database.hus_db.verify import (
    CheckResult,
    check_min_rows,
    check_required_objects,
    summarize,
)
from database.tools.apply_sql import scan_dangerous_statements

SAMPLE_URL = "postgresql://user:secret@example.neon.tech/ai07?sslmode=require"


def _complete_snapshot() -> SchemaSnapshot:
    tables = [
        TableInfo(name=name, columns=(), primary_key=(), unique=(), foreign_keys=(), checks=(), indexes=())
        for name in (*CORE_TABLES, *OFFICIAL_TABLES)
    ]
    views = {name: "SELECT 1" for name in VIEW_NAMES}
    return SchemaSnapshot(tables=tables, views=views, row_counts={})


# --- config -----------------------------------------------------------------


def test_redact_url_masks_password():
    masked = redact_url(SAMPLE_URL)
    assert "secret" not in masked
    assert "user:***@example.neon.tech" in masked


def test_redact_url_without_credentials_is_unchanged():
    assert redact_url("postgresql://example.neon.tech/ai07") == "postgresql://example.neon.tech/ai07"


def test_is_postgres_url():
    assert is_postgres_url(SAMPLE_URL)
    assert is_postgres_url("postgresql+psycopg2://host/db")
    assert not is_postgres_url("mysql://host/db")
    assert not is_postgres_url("")


def test_with_ssl_required_adds_and_preserves_sslmode():
    assert with_ssl_required("postgresql://host/db") == "postgresql://host/db?sslmode=require"
    already = "postgresql://host/db?sslmode=verify-full"
    assert with_ssl_required(already) == already


def test_load_config_requires_env_var():
    with pytest.raises(HusDatabaseConfigError):
        load_config({})


def test_load_config_rejects_non_postgres():
    with pytest.raises(HusDatabaseConfigError):
        load_config({ENV_VAR: "mysql://host/db"})


def test_load_config_reads_from_mapping():
    config = load_config({ENV_VAR: SAMPLE_URL})
    assert config.url == SAMPLE_URL
    assert "secret" not in config.safe_url
    assert config.engine_url().endswith("sslmode=require")


def test_create_engine_for_does_not_connect():
    engine = create_engine_for(HusDatabaseConfig(url=SAMPLE_URL))
    # str(engine.url) hides the password and building the engine opens no socket.
    assert "secret" not in str(engine.url)


# --- rendering --------------------------------------------------------------


def test_render_text_and_markdown_include_columns_and_views():
    snapshot = SchemaSnapshot(
        tables=[
            TableInfo(
                name="courses",
                columns=(ColumnInfo("course_code", "text", False, None),),
                primary_key=("course_code",),
                unique=(),
                foreign_keys=(),
                checks=(),
                indexes=(),
            )
        ],
        views={"v_student_transcript": "SELECT 1"},
        row_counts={"courses": 174},
    )
    text = render_schema_text(snapshot)
    assert "courses [174 rows]" in text
    assert "PK: course_code" in text
    assert "VIEW v_student_transcript" in text

    markdown = render_schema_markdown(snapshot)
    assert "## `courses` — 174 rows" in markdown
    assert "| `course_code` | text | no |  |" in markdown
    assert "```sql" in markdown


def test_read_row_counts_without_relations_returns_empty():
    assert read_row_counts(object(), ()) == {}


# --- verification -----------------------------------------------------------


def test_check_required_objects_all_present():
    results = check_required_objects(_complete_snapshot())
    assert all(result.passed for result in results)
    names = {result.name for result in results}
    assert "table:courses" in names
    assert "view:v_student_transcript" in names


def test_check_required_objects_flags_missing():
    results = check_required_objects(SchemaSnapshot())
    assert results
    assert not any(result.passed for result in results)


def test_check_required_objects_can_skip_official():
    snapshot = _complete_snapshot()
    snapshot.tables = [t for t in snapshot.tables if t.name not in OFFICIAL_TABLES]
    results = check_required_objects(snapshot, include_official=False)
    assert all(result.passed for result in results)


def test_check_min_rows():
    ok = check_min_rows({"majors": 4}, {"majors": 4})
    assert ok[0].passed
    bad = check_min_rows({"majors": 2}, {"majors": 4})
    assert not bad[0].passed
    missing = check_min_rows({}, {"majors": 4})
    assert not missing[0].passed


def test_summarize_counts_passed():
    results = [CheckResult("a", True, ""), CheckResult("b", False, ""), CheckResult("c", True, "")]
    assert summarize(results) == (2, 3)


# --- apply_sql safety -------------------------------------------------------


def test_scan_dangerous_statements_is_case_insensitive():
    assert scan_dangerous_statements("DROP DATABASE ai07;") == ["drop database"]
    assert scan_dangerous_statements("drop schema public;") == ["drop schema"]
    assert scan_dangerous_statements("CREATE TABLE t (id int);") == []


@pytest.mark.parametrize("sql", [
    "-- DOES NOT DROP database ai07\nSELECT 1;",
    "/* DROP SCHEMA public; /* nested */ */ SELECT 1;",
    "SELECT 'DROP DATABASE ai07', $$ALTER DATABASE ai07$$;",
    'SELECT "drop database" FROM t;',
])
def test_sql_guard_ignores_comments_and_quoted_content(sql):
    assert scan_dangerous_statements(sql) == []


def test_sql_guard_detects_keywords_separated_by_comments_and_newlines():
    assert scan_dangerous_statements("DROP/* reason */\nDATABASE ai07;") == ["drop database"]


def test_local_docker_url_keeps_explicit_ssl_setting():
    config = load_config({ENV_VAR: "postgresql://ai07:secret@127.0.0.1:5433/ai07?sslmode=disable"})
    assert config.engine_url().endswith("sslmode=disable")


def test_local_env_fallback_and_process_override(tmp_path, monkeypatch):
    from database.hus_db import config

    local_env = tmp_path / ".env.docker"
    local_env.write_text(f"{ENV_VAR}=postgresql://local/db?sslmode=disable\n", encoding="utf-8")
    monkeypatch.setattr(config, "LOCAL_ENV_FILE", local_env)
    monkeypatch.delenv(ENV_VAR, raising=False)
    assert config.load_config().url == "postgresql://local/db?sslmode=disable"
    monkeypatch.setenv(ENV_VAR, SAMPLE_URL)
    assert config.load_config().url == SAMPLE_URL
