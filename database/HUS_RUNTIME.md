# HUS runtime operations and historical cutover

## Current startup (2026-10-28)

Use [the local setup guide](../docs/LOCAL_SETUP.md) for Conda/venv, root `.env`,
auth `.env.auth`, Chrome and either Neon or Docker. Authentication and saved VNU
source data are now part of the application; the original manual-input cutover
below is historical. No automatic catalog publication is performed on startup.

```bash
conda activate SE_Project
python -m database.tools.migrate upgrade
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Back up existing DB data before upgrading. Current migration head is
`hus_20261028_08`. Migration reads `HUS_DATABASE_URL` from shell/root `.env`/local
Docker fallback; app uses `DATABASE_URL`, pointing to the same HUS database.
Other DB tools do not automatically load root `.env`. Use one worker; VNU
cookies/jobs are in process memory. Never overwrite existing credentials.
Docker-only startup: `docker compose --env-file database/.env.docker -f database/docker-compose.yml up -d --wait`.
Neon users do not need Docker. See the setup guide for first publication only.

Do not run root `alembic upgrade head` against HUS: that history belongs to legacy.
Legacy migrations and the raw SQL apply tool reject the migrated HUS runtime.
Compose starts PostgreSQL; it no longer runs the old destructive demo-import SQL.
Never use `docker compose down -v` to restart.

## Source and schema

`data/hus_source.json` is the catalog-only export of the eight existing HUS source
tables. It contains no student records. Stable program IDs are keyed by major,
cohort and curriculum version, with existing API aliases retained.
`hus_db/catalog_builder.py` prepares explicit group/track/graduation rules and
validated metadata 1.0 catalogs before publication; requests never parse source notes.
Source PDF names, pages, rows, prerequisite expressions and duplicate occurrences
remain in the export and snapshot. There are 174 shared courses, 290 curriculum
memberships and 297 source occurrences; catalogs contain 65/67/90/68 courses.

The original 13 tables remain. `curricula` gains `program_id` and `runtime_rules`;
`curriculum_courses` gains applicable credits, total/GPA inclusion, prerequisite
state and structured runtime metadata. `hus_catalog_revisions` stores hashed
snapshots and active pointers; `hus_alembic_version` records independent migrations.
Rules stored as JSONB are validated by the same domain validator used at read time.

```mermaid
erDiagram
    faculties ||--o{ majors : contains
    majors ||--o{ curricula : defines
    curricula ||--o{ curriculum_courses : includes
    courses ||--o{ curriculum_courses : shared_course
    curricula ||--o{ official_curriculum_groups : source_rules
    official_curriculum_groups ||--o{ official_curriculum_entries : source_rows
    curricula ||--o{ course_prerequisites : conditions
    curricula ||--o{ hus_catalog_revisions : snapshots
    students ||--o{ course_attempts : future_transcripts
```

Publication validates all four catalogs before any write, remaps numeric IDs through
natural keys, and activates all four in one transaction under an advisory lock.
Repeated imports reuse content hashes. Invalid bundles preserve active versions.
Removing existing source relationships requires explicit review and is rejected.
Historical snapshots are retained; the publisher never overwrites their payloads.
Readiness checks migration head `hus_20261028_08`, exactly four active catalogs,
identity, hashes and domain rules. There is no automatic legacy/JSON fallback.

The KHMTTT cohort-2022 catalog (`khmtt_7480113qtd_2022`, QD3568-2023) is now
`verified` from the user's explicit full-catalog sign-off recorded in
`database/data/hus_source.json`; the sign-off is bound to the source PDF SHA-256.
The other three catalogs remain `draft_unverified`. This is a project review
record, not an institutional certification or confirmation of class offerings.
Missing, complex, or conflicting prerequisite conditions still block affected
courses. Default source difficulty `2` is preserved as raw provenance only;
runtime advisory metadata stays unknown.

## Rollback

Application rollback: stop the HUS app, set `DATABASE_MODEL=legacy` and restore
the old `DATABASE_URL` from the ignored backup
`backups/hus_cutover_20261017/environment.legacy`. Start `se_recommender_db` if needed
and restart Uvicorn; verify `/ready`. Keep all passwords private.
Restore `DATABASE_MODEL=hus` and the `ai07` URL to return to HUS.
There is no need to downgrade or delete either database.

Per-program catalog rollback (previously published versions only):

```powershell
python -m database.tools.publish_catalogs --activate PROGRAM_ID REVISION_HASH
```

This only changes the active snapshot pointer; current source projections remain
available for inspection. Publishing a complete bundle activates all four together.

## Verified local acceptance

- Both pre-migration databases backed up with `pg_dump -Fc`, restored into temporary
  databases, and compared by every table's count/content digest: 13 HUS / 16 legacy tables.
- Existing HUS baseline adopted after structural comparison; fresh database migration
  and publication verified separately in a disposable database.
- All original HUS source rows/relationships and legacy table hashes preserved.
- Repeated publication stays at four revisions; invalid source rejected; historical
  activation and corrupt-content rejection tested in a disposable database.
- Accounts, students and course attempts remain empty. `/profiles` returns `[]`;
  individual profile endpoints return 404. No unauthenticated student-table exposure.
- Four real HTTP API flows verified: courses, summary/GPA, eligibility,
  recommendations and What-if. Unknown prerequisites never entered eligible results.
- Headless installed Chrome: all four majors, manual grades/GPA/credits, eligibility,
  recommendations, empty profiles and major-switch transcript/chat reset passed.
- HUS restart preserved catalogs. Legacy application rollback started successfully
  on port 18001 with its original four catalogs and twelve demo profiles.
- Regression: **173 passed, 10 skipped**. Skips require separately reviewed source
  catalogs/PDF acceptance data; these are not replaced by the HUS SQL export.
  One existing Starlette/httpx deprecation warning. Ruff, JS syntax and diff checks passed.

Local evidence and backups (ignored by Git): `backups/hus_cutover_20261017/`, including
`backup_evidence.json`, `runtime_evidence.json`, `browser_evidence.json`, `browser.png`,
the two custom-format dumps and the original local environment.
