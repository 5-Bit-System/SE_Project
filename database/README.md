# HUS database

The active FastAPI runtime reads versioned course catalogs from PostgreSQL `ai07`. This database has its own schema, migration history and Docker Compose file. It is separate from the retained legacy `course_recommender` database.

## Current workflow

For first-time local setup (Conda, Neon/Docker, auth and catalog publication),
follow [docs/LOCAL_SETUP.md](../docs/LOCAL_SETUP.md). Do not overwrite existing
credentials, reset admin accounts or publish catalogs on every startup.

From the repository root with the intended `HUS_DATABASE_URL` in root `.env`:

```bash
conda activate SE_Project
python -m database.tools.migrate upgrade
python -m database.tools.migrate current
```

Current head: `hus_20261028_08`. The migration CLI loads root `.env`; other DB
CLIs still require process configuration, `database/.env.docker` or the explicit
dotenv wrapper documented in the setup guide. App `DATABASE_URL` must point to
the same HUS database. Back up existing data before migration.

Use [HUS_RUNTIME.md](HUS_RUNTIME.md) for environment variables, migration behavior, publication, validation and rollback. `database/data/hus_source.json` is the checked-in source for four `draft_unverified` catalogs. Official source review is still needed for full catalog acceptance. Test fixtures are synthetic.

The legacy root `alembic/`, root `alembic.ini` and root `docker-compose.yml` remain for rollback. Never run those migrations against `ai07`. Historical SQL and Neon instructions are preserved in [archive](archive/2026-10-17-sql-neon-guide.md).

The 2026-10-20 prerequisite PDF review added five reference-only honors courses
and 69 prerequisite relations to the source export (179 courses, 348 relations).
The four runtime memberships are unchanged. MAT3325 retains conflicting source
variants and MAT3423 remains unknown pending a definition for MAT3402. Use the
current export and publisher; the historical raw SQL import predates this review.
See [PDF review and verification](../docs/VINH_PDF_SOURCE_REVIEW.md).

## Recovery for missing revision hus_20261023_04 (2026-10-28)

Some deployed databases applied transcript-sync revisions that were later absent
from the main tree. Those original files (`hus_20261023_01`, `hus_20261023_04`)
are restored unchanged from Git. New merge revision `hus_20261028_07` joins that
history with VNU authentication head `hus_20261025_06`. Existing migrations are
not rewritten and no version row is manually relabeled. Databases at either
parent apply only missing migrations before reaching the single merged head.
Fresh databases also receive nullable `students.last_transcript_synced_at`.

The migration CLI now loads the root `.env` without overriding shell variables.
Set `HUS_DATABASE_URL` to the same intended HUS database as app `DATABASE_URL`.
Back up that database before upgrading, then run from the repository root:

```bash
conda activate SE_Project
python -m database.tools.migrate upgrade
python -m database.tools.migrate current
```

Expected head: `hus_20261028_07`. Then start Uvicorn normally. Do not use `stamp`,
change `hus_alembic_version` manually or reset the database to bypass this error.
This change does not make the portal service write the restored sync timestamp;
portal snapshots and existing synchronization logic remain separate.

## Semester plans (2026-10-28)

Migration `hus_20261028_08` adds account-owned `semester_plans`, with multiple
alternatives, optimistic versions, server-calculated credits and source/catalog
provenance. See [the feature guide](../docs/SEMESTER_PLANS.md). Back up existing
data and upgrade before starting the new app; historical recovery instructions
above describe the prior `hus_20261028_07` checkpoint, not the current head.
