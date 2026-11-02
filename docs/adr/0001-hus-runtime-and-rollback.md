# ADR 0001: HUS catalogs as the active runtime

Date: 2026-10-17
Status: accepted

## Decision

FastAPI uses versioned catalog snapshots backed by HUS PostgreSQL `ai07` when `DATABASE_MODEL=hus`. HUS has an independent migration history under `database/hus_alembic/` and a publication tool. The earlier `course_recommender` database, root `alembic/` history and root Compose configuration remain available for rollback. Never apply migrations from one history to the other database.

## Context and consequences

The HUS and legacy schemas model different records. Keeping both histories preserves rollback while catalog revisions allow repeatable publication. Four HUS catalogs currently have `draft_unverified` status. HUS profile and attempt tables contain no student records; manual transcripts remain session scoped. Official source review and portal integration are separate work.

See [HUS operations](../../database/HUS_RUNTIME.md) for commands and rollback steps.
