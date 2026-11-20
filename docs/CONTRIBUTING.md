# Contributing

Read [active project memory](../.agent/AGENTS.md) and [ADR 0001](adr/0001-hus-runtime-and-rollback.md) before changing storage. HUS `ai07` is the active catalog runtime; the root Alembic/Compose setup is retained legacy rollback. Never apply one migration history to the other database. Keep catalog source changes and review evidence explicit.

## GitHub workflow

Start work from a GitHub issue with a clear scope and testable acceptance criteria. Create a focused branch such as `fix/123-short-name` or `feat/123-short-name`, keep commits related to that issue, and reference the issue number in commit messages. Open a PR with `Closes #123`, verification results, and any API/UI/database impact. Do not create empty or unrelated commits to inflate the count. See [GitHub collaboration workflow](GITHUB_WORKFLOW.md) for Project status, review, and teamwork expectations.

From a clean checkout, install the dependencies with `python -m pip install -r requirements-dev.txt -c requirements-lock.txt`. Run offline tests with `python -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"` and lint with `python -m ruff check .`. Legacy PostgreSQL tests need `TEST_DATABASE_URL` and `-m postgres`. HUS integration needs a disposable local `ai07`, `HUS_TEST_DATABASE_URL`, migrated and published source, then `-m hus_postgres`. See [HUS operations](../database/HUS_RUNTIME.md).

The `full_catalog_acceptance` marker requires separately reviewed official source data; synthetic fixtures do not certify it. Update current README, operations and checklist when behavior changes. Put dated handoff history in archive. Keep `.env`, credentials, backups, cache and `.venv` outside Git. Never include passwords, cookies, tokens, or real student records in issues, comments, screenshots, test fixtures, or commits. Request a review from a teammate who can actually inspect the change; discuss decisions in the linked issue or PR. Do not commit or push unless requested by the maintainer.
