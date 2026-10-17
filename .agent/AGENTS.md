# Project Memory and Contributor Guidelines

## Current state — 2026-10-17

SE_Project is the Explainable Course Recommender (AI-07), a FastAPI application with a static web UI. The active local runtime reads four versioned HUS catalogs from PostgreSQL database `ai07` on Docker loopback port 5433. Set `STORAGE_BACKEND=postgres`, `DATABASE_MODEL=hus` and a matching `DATABASE_URL` in the ignored root `.env`. Offline ranking uses `RECOMMENDATION_LLM_ENABLED=false`. See [HUS operations](../database/HUS_RUNTIME.md) and the root [README](../README.md).

The four HUS catalogs are `draft_unverified`. The source export is `database/data/hus_source.json`; no reviewed PDF catalog acceptance is available. HUS accounts, students and course attempts are empty. Users enter grades manually in the browser; transcript and chat state are session scoped. There is no portal login/sync, OCR, or HUS document crawler/RAG. The existing course advisor is separate from that planned HUS Q&A feature.

The HUS schema uses its own migration head `hus_20261017_02`. Use `database.tools.migrate` and `database.tools.publish_catalogs`; never run root Alembic or the historical SQL import against the migrated HUS runtime. The legacy `course_recommender` database, root Alembic history, Compose service and volume remain available for rollback. Runtime storage failures do not fall back to JSON. Local credentials and backup evidence are ignored by Git.

The checked-in `data/curricula/` contains only a 65-course Data Science metadata sample. It is not the four-catalog HUS runtime source and cannot seed the whole product. Test data under `tests/support/fixtures/` is invented and must not be presented as academic source data. `.agent/KE_HOACH_DU_AN.md` is a historical plan. Dated handoffs are in [archive](archive/).

## Product invariants

- Exactly one major is selected. Catalog, transcript, eligibility, progress, candidate set and recommendation stay within that major. Switching major clears transcript and recommendation chat context.
- Eligibility is deterministic and runs before ranking. Completed, blocked, foreign-major and unverified-prerequisite courses must never enter recommendations, including LLM output.
- What-if changes preference weights or ordering, never eligibility or catalog facts. Unknown metadata remains unknown.
- Recommendations must warn that offerings and official academic rules have not been fully verified. Do not invent timetables or course availability.
- Do not persist manual transcripts, chat, real student records or provider keys for this demo.

## Repository ownership

- `app/`: API, domain behavior, repository adapters and static UI. `app/db/` and root `alembic/` represent the retained legacy persistence model.
- `database/`: HUS source, schema tooling, independent migrations, publication and operational evidence.
- `tests/`: feature-organized tests. Shared pytest fixtures live in `tests/conftest.py`; synthetic data and helpers live in `tests/support/`.
- `docs/SYSTEM_SPECIFICATION.md` and `docs/DATABASE_DESIGN.md`: architecture and product decisions. Dated plans and `modules/` describe proposed work, not proof of delivery. Track current acceptance in `docs/CODEBASE_CHECKLIST.md`.

## Commands and acceptance

From the repository root, use the project `.venv` and the pinned constraints:

```powershell
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
docker compose --env-file database/.env.docker -f database/docker-compose.yml up -d --wait
python -m database.tools.migrate upgrade
python -m database.tools.publish_catalogs --dry-run
python -m database.tools.publish_catalogs
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`/health` checks the process; `/ready` checks HUS storage and catalogs. Do not overwrite existing `.env` files or delete Docker volumes. For local rollback, follow `database/HUS_RUNTIME.md`.

Default tests use synthetic fixtures and block outbound HTTP. PostgreSQL tests require an explicit `TEST_DATABASE_URL`; HUS integration tests require `HUS_TEST_DATABASE_URL` for local Docker `ai07`. The ten `full_catalog_acceptance` cases require separately reviewed source data and remain skipped without `--full-catalog-root`.

```powershell
python -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"
python -m ruff check .
python -X utf8 tools/build_catalogs.py --check --root tests/support/fixtures/catalogs
```

Use typed Python, `snake_case` names and `camelCase` JavaScript. Keep tests deterministic and mock network/model calls. Report progress as a percentage of the requested task, with completed and remaining milestones. Do not claim the whole product is complete based on infrastructure checks.

## Git and local resources

Keep secrets, `.venv/`, backups, cache, `myproject/` and `project-toolkit/` outside Git. Do not commit or push unless the user requests it. Preserve existing uncommitted HUS and Docker work. The local toolkit is invoked only when the user names `project-toolkit`; then read `project-toolkit/SKILL.md` and the selected source skill without expanding task scope.

Historical session details and prior validation counts remain in [the archived handoff](archive/2026-10-17-pre-improvement-memory.md). This file records the current working rules.
