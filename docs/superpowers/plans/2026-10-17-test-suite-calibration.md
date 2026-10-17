# Test Suite Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make HUS migration tests fail closed unless they target the documented local test database, and make synthetic fixture coverage clearly distinguishable from real-source acceptance.

**Architecture:** Keep the safety check in test support code, before any database connection or DDL. Keep the offline eligibility regression test on synthetic fixtures and label it accordingly; full source acceptance remains a separate opt-in suite that requires reviewed catalog data.

**Tech Stack:** Python 3.11+, pytest, SQLAlchemy URL parsing, existing FastAPI/domain test fixtures.

**Spec:** `.agent/AGENTS.md`; `database/HUS_RUNTIME.md`; `docs/CODEBASE_CHECKLIST.md`.

## Global Constraints

- HUS integration tests require `HUS_TEST_DATABASE_URL` for local Docker `ai07`.
- The ten `full_catalog_acceptance` cases require separately reviewed source data and remain skipped without `--full-catalog-root`.
- Default tests use synthetic fixtures and block outbound HTTP.
- Preserve the existing legacy database, local configuration, and uncommitted work; do not commit or push.
- Do not present synthetic fixtures as academic source data or catalog acceptance evidence.

## Review Focus

- A mistaken or remote `HUS_TEST_DATABASE_URL` must be rejected before the test attempts a database connection or executes DDL.
- Offline eligibility coverage must be identified as synthetic-fixture coverage; no test may imply that unreviewed source catalogs were verified.

---

### Task 1: Guard the disposable HUS migration test target

**Files:**
- Modify: `tests/database/test_hus_migration_runtime.py`

**Interfaces:**
- Add `_validate_runtime_test_target(url: str) -> URL`; it returns a parsed PostgreSQL URL only when `host` is `127.0.0.1` or `localhost`, `database` is exactly `ai07`, and query parameters cannot redirect the connection (`sslmode` is allowed). Otherwise it raises `ValueError` before any connection is created.
- `runtime_engine` must call this validator before `create_engine` and before `CREATE DATABASE`.

- [x] **Step 1: Add offline URL safety tests and unmark them**

Add passing cases for `postgresql+psycopg2://user:secret@127.0.0.1:5433/ai07`, with and without `?sslmode=disable`. Add rejection cases for a non-loopback host, a local database name other than `ai07`, non-PostgreSQL URLs, and query parameters that can redirect host or database selection. Move `pytest.mark.hus_postgres` from module scope to `test_fresh_migration_publication_and_rollback` so the URL checks run without PostgreSQL credentials.

- [x] **Step 2: Run the focused tests and confirm the new cases fail**

Run: `.venv/Scripts/python.exe -m pytest tests/database/test_hus_migration_runtime.py -q`

Expected: the new validator tests fail because the validator is not implemented yet; the existing live database test skips without `HUS_TEST_DATABASE_URL`.

- [x] **Step 3: Implement target validation**

Implement `_validate_runtime_test_target` in the test module and call it before `create_engine` so invalid targets cannot reach connection setup or DDL.

- [x] **Step 4: Run the focused and default offline suites**

Run: `.venv/Scripts/python.exe -m pytest tests/database/test_hus_migration_runtime.py -q`

Expected: URL guard tests pass and the live migration test skips when `HUS_TEST_DATABASE_URL` is absent.

Run: `.venv/Scripts/python.exe -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"`

Expected: all default offline tests pass.

### Task 2: Label fixture-based eligibility coverage accurately

**Files:**
- Modify: `tests/eligibility/test_rules.py`

**Interfaces:**
- Rename `test_zero_eligibility_violation_rate_on_real_catalog` to `test_zero_eligibility_violation_rate_on_fixture_catalog`.
- Keep its assertions and fixture setup unchanged; source-catalog verification remains covered only by the separately marked acceptance suite when reviewed data is supplied.

- [x] **Step 1: Rename the test and its misleading comments**

Update the test name and comments to say it uses the isolated fixture catalog. Do not weaken or remove the existing eligibility assertions.

- [x] **Step 2: Run the focused test**

Run: `.venv/Scripts/python.exe -m pytest tests/eligibility/test_rules.py::test_zero_eligibility_violation_rate_on_fixture_catalog -q`

Expected: PASS against the synthetic fixture catalog.

- [x] **Step 3: Run the default offline suite**

Run: `.venv/Scripts/python.exe -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"`

Expected: all default offline tests pass; no claim is made that this run verifies the reviewed source catalogs.

## Acceptance

- Invalid HUS test targets are rejected before database connections or DDL.
- URL safety tests run in the default offline suite.
- The eligibility test name clearly identifies fixture data.
- Full catalog acceptance remains unclaimed until separately reviewed source data is provided and the opt-in suite passes.
