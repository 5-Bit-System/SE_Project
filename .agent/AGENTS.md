# Project Memory and Contributor Guidelines

## Current state — 2026-10-17

SE_Project is the Explainable Course Recommender (AI-07), a FastAPI application with a static web UI. The active local runtime reads four versioned HUS catalogs from PostgreSQL database `ai07` on Docker loopback port 5433. Set `STORAGE_BACKEND=postgres`, `DATABASE_MODEL=hus` and a matching `DATABASE_URL` in the ignored root `.env`. Offline ranking uses `RECOMMENDATION_LLM_ENABLED=false`. See [HUS operations](../database/HUS_RUNTIME.md) and the root [README](../README.md).

The four HUS catalogs are `draft_unverified`. The source export is `database/data/hus_source.json`; no reviewed PDF catalog acceptance is available. HUS accounts, students and course attempts are empty. Users enter grades manually in the browser; transcript and chat state are session scoped. There is no portal login/sync, OCR, or HUS document crawler/RAG. The existing course advisor is separate from that planned HUS Q&A feature.

The HUS schema uses its own migration head `hus_20261017_02`. Use `database.tools.migrate` and `database.tools.publish_catalogs`; never run root Alembic or the historical SQL import against the migrated HUS runtime. The legacy `course_recommender` database, root Alembic history, Compose service and volume remain available for rollback. Runtime storage failures do not fall back to JSON. Local credentials and backup evidence are ignored by Git.

The checked-in `data/curricula/` contains only a 65-course Data Science metadata sample. It is not the four-catalog HUS runtime source and cannot seed the whole product. Test data under `tests/support/fixtures/` is invented and must not be presented as academic source data. `.agent/KE_HOACH_DU_AN.md` is a historical plan. Dated handoffs are in [archive](archive/).

The current repository branch is `codebase`. Commit `26aeb39` (`Organize project structure and harden HUS tests`) was pushed to `origin/codebase` on 2026-10-17; the working tree was clean immediately after that push. The user explicitly designated `codebase` as the only publication target for that request. The local `origin/HEAD` still points to `main`, so do not infer the intended push target from it. See [the latest handoff](archive/2026-10-17-test-calibration-and-codebase-publish.md).

## Session update - 2026-10-21

`feat/vinh-database-tests` was merged and pushed into `origin/codebase`. Its data/source tests, prerequisite parser coverage and PDF-review evidence are included in merge commit `5dfcc0f`; the current remote head is `83a367c`.

The local HUS database was backed up to ignored `backups/vinh-database-tests-merge-20261021/`, then the four-catalog source was published. `verify_data` reported 26/26 checks and runtime read 65/67/90/68 courses. Catalogs remain `draft_unverified`.

Post-merge validation was 248 passed / 41 deselected offline, 31 passed / 258 deselected across PostgreSQL markers on a disposable PostgreSQL 16 container, and 24 passed for the HUS-only integration group. Ruff, `git diff --check`, synthetic fixture builders and prerequisite tests under `PYTHONHASHSEED=1` and `2` passed. One existing Starlette/httpx deprecation warning remains. The ten `full_catalog_acceptance` cases still require separately reviewed source data.

Database-test improvements are uncommitted: publisher mid-transaction rollback and concurrent-publication tests, deterministic prerequisite branch coverage, named integrity-check assertions, CI JUnit artifacts and test README updates. They modify only `.github/workflows/checks.yml` and `tests/database/`; they do not alter runtime code, source catalogs or schema. Do not overwrite, commit or push them unless the user requests it.

## Session close - 2026-10-22: HUS metadata plan review

Current local branch is `codebase` at `442819d`, matching `origin/codebase` at the last local check. The latest fetched `origin/feat/vinh-database-tests` is `8c60434` (`Improve source-backed HUS metadata and bilingual course names`); `origin/fix/hus-metadata-vi-en-20261021` pointed to the same commit. This newer metadata commit has **not** been merged into local `codebase`, committed here, pushed from this session, or published to the local HUS database by this session. Do not confuse this with the earlier database-test merge recorded above.

The user requested a read-only review of that branch against `docs/KE_HOACH_CAI_THIEN_METADATA_HUS.md`, then asked for the completed and remaining work to be written into that plan for Vinh. The plan now has a 2026-10-22 status section and an approximate **40%** overall progress estimate by phase acceptance criteria. That percentage is not academic data verification. The branch supplies `name_en` for 290/290 program-course memberships, `hours` for 282/290, source hashes/locators, selected PDF-backed name/group corrections, a draft advisory rubric, reports, and bilingual course-name UI. P0 MAT3402/MAT3325 remain unresolved; PHI1002 still needs effective-source confirmation. Full independent PDF row review, reviewer sign-off, reviewed-source acceptance data, most advisory metadata, and reproducible Git-visible runtime publication evidence remain outstanding. `row-audit.csv` has `human_review=pending`; its `core_source_consistency=matched` is assigned by the report generator from the same source export and is not independent PDF verification. Catalogs remain `draft_unverified`.

Review scope was Git code and checked-in reports. The PDFs were not independently reread; tests and the live database were not rerun. At session close, `git status` showed only `docs/KE_HOACH_CAI_THIEN_METADATA_HUS.md` modified before this memory update. The old 2026-10-21 note about uncommitted `.github/workflows/checks.yml` and `tests/database/` changes is historical; those files are currently clean. Keep both the plan update and this memory update local unless the user separately requests commit/push or a merge. `git diff --check` found no whitespace errors; Git only warned about possible LF-to-CRLF conversion.

## Session close - 2026-10-22: HUS crawler/RAG release plan

The user reviewed the `crawldata` branch and decided **not to merge it into `codebase` yet**. The fetched source snapshot is `origin/crawldata` at `cc239f0`; `origin/codebase` was `442819d` at the audit. The branches have diverged (26 commits on `codebase`, 49 on `crawldata` since merge base `0ad1f815`). The crawler code includes extraction and classification for four majors plus `general`, but no committed `data/hus/processed/catalog.json` or completed RAG serving path. A teammate showed the user a successful crawl result; this workspace has no run log, URL export, corpus or measured runtime. The user considered a full run potentially longer than 30 minutes and canceled the proposed clone/run. No isolated clone, crawler execution, code integration, merge, database publication or scheduler setup occurred in this session.

The current plan is [`docs/KE_HOACH_TICH_HOP_CRAWLER_RAG.md`](../docs/KE_HOACH_TICH_HOP_CRAWLER_RAG.md), with audit [`docs/HUS_CRAWLER_INTEGRATION_AUDIT.md`](../docs/HUS_CRAWLER_INTEGRATION_AUDIT.md). Both are local, untracked files. Audit completed 4/6 original checklist items: source commit/merge base, manifest, conflict review and config-level allowlist review. It still needs the teammate's run report and a real URL/content/major-label sample. Before any integration, review that evidence, offline tests and dry-run, then decide whether the crawler is ready; only then prepare a selective feature-branch integration for review. Do not merge the whole `crawldata` branch by default.

The user replaced scheduled crawling with a release model: run one official crawl to create the v1 corpus at release time, review it, then publish an immutable versioned snapshot. The application reads only the active published corpus and never crawls on startup, per request, or on a weekly schedule. Future source updates are deliberate v2/v3 releases, each with its own crawl, review and atomic switch of the active corpus; keep prior snapshots for rollback. A failed preparation or publication leaves the prior active version intact. Teammate's earlier trial run is evidence to review, not the official v1 release snapshot. The plan and audit now reflect this decision. No recurring scheduler should be introduced unless the user changes this requirement.

At this close, `git status --short` shows modified `.agent/AGENTS.md` and `docs/KE_HOACH_CAI_THIEN_METADATA_HUS.md`, plus the two untracked crawler plan/audit docs. Keep all changes local; no commit/push was requested.

## Session update - 2026-10-22: Vinh branch tested and merged locally

The user authorized a local merge of `origin/feat/vinh-database-tests` into `codebase`. The merge fast-forwarded `codebase` from `442819d` to `8c60434`; `origin/codebase` remained at `442819d` at the last check. No push or HUS runtime publication occurred. The earlier metadata-review and crawler notes above record their own audit-time state.

Commit `8c60434` was tested from an isolated Git archive: 263 passed / 41 deselected offline, 31 passed / 273 deselected across PostgreSQL markers, `verify_data` 26/26, Ruff, four synthetic fixture builders, JavaScript syntax, and `git diff --check` passed. The disposable migration databases were removed, and HUS accounts, students, and course attempts remained empty. One existing Starlette/httpx deprecation warning remains. Ten `full_catalog_acceptance` cases still need independently reviewed source data. These tests establish code and database behavior; the four catalogs remain `draft_unverified`.

## Session update - 2026-10-22: database test improvement

The five technical tasks in `docs/DATABASE_TEST_IMPROVEMENT_PLAN.md` are complete locally. P0 and activation rollback were pushed to `origin/codebase` in `7c9140e`; the distinct-bundle concurrency test was committed as `9327166`, and PostgreSQL metadata/repository/API tests as `2bf1e5c`. The latter two commits and the final report update are local until the user requests a push.

On commit `2bf1e5c`, local validation was 291 passed / 45 deselected offline, 16 passed / 320 deselected for legacy PostgreSQL, 19 passed / 317 deselected for HUS PostgreSQL; Ruff, four synthetic fixture builders and `verify_data` 26/26 passed. Ten `full_catalog_acceptance` tests were separately collected and skipped without independently reviewed source data. JUnit XML is in ignored `backups/database-tests-20261022-2bf1e5c/`; the Git-visible summary is `docs/VINH_DATABASE_TEST_REPORT.md`. PostgreSQL test database `se_project_test` remains for repeat runs; no disposable HUS database or legacy test schema remained, and HUS accounts, students and course attempts remained empty. No metadata publication to the runtime database occurred in this work.

## Session update - 2026-10-22: PDF-backed HUS acceptance

The user supplied five PDFs in `docs/`, confirmed cohort 2022, designated themself as final reviewer, and reported amendments unknown. Local work after pushed `66002cd` adds `docs/acceptance/hus_2022/hus_pdf_expectations.json`, an independent OCR/visual code-page inventory of 297 occurrences, and HUS support for the existing ten `full_catalog_acceptance` cases while retaining the legacy file-catalog path. Run with explicit `tests` path and `--full-catalog-root docs/acceptance/hus_2022`. Results: 302 offline passed (including ten source cases), 35 PostgreSQL passed, Ruff passed. Temporary HUS databases and legacy schemas were removed; accounts/students/course_attempts remain empty. Evidence/report: `docs/HUS_PDF_ACCEPTANCE_REVIEW.md` and ignored `backups/catalog_acceptance_20261022/`.

The new anomaly check found missing preservation of the Data Science summary 28/63 (PDF 105 page 8). `hus_source.json` now includes parent group V.2 (28 required, 63 offered) with locator/note; subgroup sum remains 57. This source change is local and has not been published to runtime. Catalogs remain draft_unverified: automated assertions do not certify every field or resolve MAT3402, MAT3325, PHI1002 effective-source questions or later amendments. These changes and the user PDFs are uncommitted; do not commit/push without a new user request.

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

The latest pre-publication offline run was **155 passed, 37 deselected**, with one existing Starlette/httpx deprecation warning. A full collection run was **155 passed, 37 skipped**; the skipped cases require database URLs or reviewed source data. Ruff and all four synthetic catalog builder checks passed. The HUS migration test now rejects non-local, non-`ai07`, non-PostgreSQL and redirecting-query URLs before connecting. The eligibility test formerly named `real_catalog` was renamed to identify its synthetic fixture correctly. These counts are a 2026-10-17 snapshot, not proof of current full-source acceptance.

```powershell
python -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"
python -m ruff check .
python -X utf8 tools/build_catalogs.py --check --root tests/support/fixtures/catalogs
```

Use typed Python, `snake_case` names and `camelCase` JavaScript. Keep tests deterministic and mock network/model calls. Report progress as a percentage of the requested task, with completed and remaining milestones. Do not claim the whole product is complete based on infrastructure checks.

## Git and local resources

Keep secrets, `.venv/`, backups, cache, `myproject/` and `project-toolkit/` outside Git. Do not commit or push future changes unless the user requests it. Preserve the published HUS and Docker work and do not update branches other than the one the user names. The local toolkit is invoked only when the user names `project-toolkit`; then read `project-toolkit/SKILL.md` and the selected source skill without expanding task scope.

Historical session details and prior validation counts remain in [the archived handoff](archive/2026-10-17-pre-improvement-memory.md). This file records the current working rules.

## Cleanup - 2026-10-22

User requested project-toolkit cleanup. Removed unused `database/hus_db/schema.py` (no import/reference; actual HUS DDL remains in migrations), 33 disposable rendered PDF PNGs, the inactive cutover test Chrome profile, and 29 project cache directories: 524 generated files, about 54 MiB. Original PDFs, OCR TXT/TSV, CSV/JUnit evidence, database dumps, legacy migration snapshots and local toolkit were preserved. Fresh combined run after code/artifact deletion: 337 passed, no skipped cases, Ruff passed; JUnit `backups/catalog_acceptance_20261022/cleanup-regression.xml`. No commit/push or runtime publication.
