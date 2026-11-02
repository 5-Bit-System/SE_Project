# Contributing

Read [active project memory](../.agent/AGENTS.md) and [ADR 0001](adr/0001-hus-runtime-and-rollback.md) before changing storage. HUS `ai07` is the active catalog runtime; the root Alembic/Compose setup is retained legacy rollback. Never apply one migration history to the other database. Keep catalog source changes and review evidence explicit.

From a clean checkout, install the dependencies with `python -m pip install -r requirements-dev.txt -c requirements-lock.txt`. Run offline tests with `python -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"` and lint with `python -m ruff check .`. Legacy PostgreSQL tests need `TEST_DATABASE_URL` and `-m postgres`. HUS integration needs a disposable local `ai07`, `HUS_TEST_DATABASE_URL`, migrated and published source, then `-m hus_postgres`. See [HUS operations](../database/HUS_RUNTIME.md).

The `full_catalog_acceptance` marker requires separately reviewed official source data; synthetic fixtures do not certify it. Update current README, operations and checklist when behavior changes. Put dated handoff history in archive. Keep `.env`, credentials, backups, cache and `.venv` outside Git. Do not commit or push unless requested by the maintainer.
