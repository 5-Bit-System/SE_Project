# HUS database

The active FastAPI runtime reads versioned course catalogs from PostgreSQL `ai07`. This database has its own schema, migration history and Docker Compose file. It is separate from the retained legacy `course_recommender` database.

## Current workflow

From the repository root, with `HUS_DATABASE_URL` pointing to the intended HUS database (or defined in the ignored `database/.env.docker`):

```powershell
docker compose --env-file database/.env.docker -f database/docker-compose.yml up -d --wait
.venv\Scripts\python.exe -m database.tools.migrate upgrade
.venv\Scripts\python.exe -m database.tools.publish_catalogs --dry-run
.venv\Scripts\python.exe -m database.tools.publish_catalogs
.venv\Scripts\python.exe -m database.tools.verify_data
```

Use [HUS_RUNTIME.md](HUS_RUNTIME.md) for environment variables, migration behavior, publication, validation and rollback. `database/data/hus_source.json` is the checked-in source for four `draft_unverified` catalogs. Official source review is still needed for full catalog acceptance. Test fixtures are synthetic.

The legacy root `alembic/`, root `alembic.ini` and root `docker-compose.yml` remain for rollback. Never run those migrations against `ai07`. Historical SQL and Neon instructions are preserved in [archive](archive/2026-10-17-sql-neon-guide.md).

The 2026-10-20 prerequisite PDF review added five reference-only honors courses
and 69 prerequisite relations to the source export (179 courses, 348 relations).
The four runtime memberships are unchanged. MAT3325 retains conflicting source
variants and MAT3423 remains unknown pending a definition for MAT3402. Use the
current export and publisher; the historical raw SQL import predates this review.
See [PDF review and verification](../docs/VINH_PDF_SOURCE_REVIEW.md).
