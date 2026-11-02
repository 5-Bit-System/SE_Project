> Historical snapshot before the 2026-10-17 structure improvement. Current instructions: [../AGENTS.md](../AGENTS.md).

# Project Memory and Contributor Guidelines

## HUS application cutover - 2026-10-17

- Latest scope overrides historical notes below: main app uses HUS ai07 on localhost5433, DATABASE_MODEL=hus and DATABASE_URL in ignored root .env. Offline ranking enabled; web port8000.
- Separate HUS Alembic head hus_20261017_02; source database/data/hus_source.json, four draft catalogs. Accounts/students/attempts remain empty. User deferred all new modules to conserve quota; no portal/login/OCR/chat module was implemented.
- Original 13 HUS tables retained/extended, plus hus_catalog_revisions and hus_alembic_version. Use database.tools.migrate/publish_catalogs; no root Alembic or SQL10 on HUS. No runtime fallback.
- Both databases backed up, restored and hash-compared; source and legacy rows preserved. Legacy config rollback verified. Credentials/evidence remain ignored in backups/hus_cutover_20261017.
- 173 passed, 10 reviewed-source skips. Ruff/JS/diff passed. Real API and Chrome verified all four majors, manual GPA/credits, eligibility, recommendations, major reset. Docker restart passed. See database/HUS_RUNTIME.md.
- Changes uncommitted; preserve prior Docker work. Do not commit/push unless requested.

## Session close - cleanup and handoff - 2026-10-17

- User asked to use `project-toolkit` for cleanup. Read `project-toolkit/SKILL.md`; source check passed (3 pinned repositories, 12 skills intact).
- Removed 219 generated Python/pytest/Ruff/hypothesis cache directories across the workspace, including regenerable bytecode under `.venv`. No source files, requirements, local environment settings, backup dumps, database data/volumes, or toolkit sources were deleted. `/ready` remained healthy after cleanup.
- Keep branch `feat/database-setup-and-tests`: it is the checked-out branch holding the active, uncommitted HUS runtime implementation. It is not a disposable cloned directory. Do not delete or reset it before its work is safely committed/merged or explicitly abandoned.
- `database/` is active runtime/migration code, not a redundant clone. No other source file was confidently identified as obsolete during this cleanup; do not delete historical docs/modules just because they are not part of the current runtime.
- Final local entrypoint: `http://127.0.0.1:8000`; HUS runtime and rollback details: `database/HUS_RUNTIME.md`. Changes remain uncommitted; no commit/push was requested.


## Docker HUS handoff — 2026-10-17

- User explicitly requested creating and testing the HUS database on Docker instead of Neon.
  Work is on `feat/database-setup-and-tests`, after `6ffcd62`; changes are uncommitted.
- Dedicated Compose `database/docker-compose.yml` uses existing `postgres:16-alpine`,
  container `se_hus_db`, volume `se_hus_pgdata`, database `ai07`, loopback port 5433.
  Existing `se_recommender_db` / `se_recommender_pgdata` and unrelated containers were untouched.
- Random local credentials are in ignored `database/.env.docker`. HUS config reads that file
  as a fallback; explicit process `HUS_DATABASE_URL` takes precedence. Do not print credentials.
- Both SQL scripts initialized successfully; verify_data passed 26/26. Counts: 174 courses,
  290 curriculum memberships, 279 prerequisites, 41 source groups, 297 source entries.
  Reapply preserved row counts; restart preserved data. Synthetic integration records rolled back.
- Full local test run with both PostgreSQL test URLs: 157 passed, 10 external-source skips,
  one existing Starlette/httpx warning. Ruff passed. See database/DOCKER_VERIFICATION.md.
- Fixed SQL guard's false positive on comments; added offline regression tests and 10 opt-in
  HUS PostgreSQL tests. HUS account/student/attempt tables remain empty. FastAPI runtime still
  uses its original storage; portal login/transcript synchronization is not implemented.
- Keep this local Docker task distinct from source-data acceptance, portal integration and
  whole-product completion. Do not commit/push unless requested.

## Historical Handoff — 2026-10-15

- Cleanup follow-up: removed unused `app/schemas/transcript.py` (re-export only, no repository consumers) and the completed Phase A implementation plan. Retained Phase A acceptance evidence, the historical audit with an explicit status note, and pending B/C/D plans. Removed 13 local cache directories (75 generated files); runtime environment, toolkit, backups and product data were preserved. Post-cleanup offline verification: 108 passed, 26 skipped; Ruff, sample/synthetic catalog validation and diff checks passed. PostgreSQL, browser, model provider and remote CI were not rerun in this cleanup. The user explicitly requested publishing these cleanup changes to `codebase`.
- Repository: `https://github.com/5-Bit-System/SE_Project.git`; working branch: `codebase`. Before this handoff, remote `codebase` was at `19c081c` after two documentation commits. Check Git history for the latest published commit; do not infer it from this memory file.
- Phase A (metadata, runtime, testing) is complete in code and local verification. Strict metadata 1.0 normalization/validation, safe builder, JSON/PostgreSQL round-trip, isolated synthetic test fixtures, progress, excluded-credit/GPA behavior, and CI job separation are implemented. See `docs/superpowers/plans/2026-10-14-metadata-runtime-progress.md` for acceptance evidence and decisions.
- Latest local verification: **108 passed, 26 skipped** with no test database URL; Ruff passed. An earlier isolated PostgreSQL run completed **124 passed, 10 skipped**. The ten remaining skips require the four reviewed source catalogs. CI on the remote branch and live browser/model-provider behavior have not been verified.
- `data/` still contains only the 65-course Data Science 2022 handoff sample; the other three catalogs and twelve product demo profiles were removed by user request. The original PDFs are not present. Do not recreate these product datasets without a new request. Test fixtures under `tests/fixtures/` are invented and must never be treated as academic source data.
- PostgreSQL product database/container/volume were not modified during Phase A. The earlier database may still contain four catalogs and twelve demo profiles, but its current availability was not verified because Docker API access was denied in this environment. A fresh clone cannot seed the four-program demo from the checked-in product data. Do not seed the existing product database merely to test the sample.
- The user wants to finish and publish the codebase foundation now. Recommendation/chatbot, frontend/What-if, and HUS Q&A module work (plans B/C/D) belongs to teammates later; do not implement those modules unless explicitly requested. Remaining foundation work includes reviewing backend ownership, source-data handoff when authorized, and remote CI/demo verification. Track these separately from Phase A acceptance in `docs/CODEBASE_CHECKLIST.md`.
- Local demo with the pre-existing database: from the repo, run `docker compose up -d db`, set `RECOMMENDATION_LLM_ENABLED=false` for offline recommendations, then run `.venv/Scripts/python.exe -m uvicorn app.main:app --reload` and visit `http://127.0.0.1:8000/ready` and `/`. Requires valid local `.env` and the retained database volume. Do not run `docker compose down -v`.
- Collaboration preferences: preserve requested scope, report task-scoped progress percentages, prefer one agent/minimal skill reads unless parallel agents are explicitly requested and useful. `project-toolkit/`, skill collections, secrets, environments, caches and backups stay local and outside Git. Do not automatically commit/push on future memory-only requests; this session's user explicitly requested publication.

## Project Context

This repository is the codebase for an Explainable Course Recommender (AI-07). The product helps students inspect a synthetic academic profile, transcript, curriculum progress, eligible courses, and ranked course recommendations. Use `docs/SYSTEM_SPECIFICATION.md` and `docs/DATABASE_DESIGN.md` for current implementation decisions; `.agent/KE_HOACH_DU_AN.md` remains a product/historical reference. The latest explicit user instructions take precedence over older plans.

The application uses FastAPI with a static frontend. On 2026-10-14 the user explicitly restored PostgreSQL to the project scope and requested reuse of the old project database where suitable, or replacement of its schema where unsuitable. Docker is available. JSON files under `data/curricula/` remain the versioned source/seed artifacts; the application must support PostgreSQL-backed catalog and synthetic profile reads. Alembic migrations and a reproducible Docker database setup are part of the infrastructure scope. The four-year roadmap and automatic major detection remain outside scope.

## Product Scope and Invariants

- Support four separate catalogs: Mathematics, Mathematics-Informatics, Computer and Information Science, and Data Science.
- The user must select exactly one major before selecting completed courses. Every catalog lookup, transcript validation, eligibility result, candidate set, progress calculation, and recommendation must stay within that major. Changing major clears the selected courses and recommendation chat context.
- Use only the curriculum-framework sections of the four source PDFs. Keep course code, name, credits, group/category, prerequisites, source page, and source status. Keep unresolved external prerequisite references marked as unverified; never use them to unlock a course.
- Use synthetic data only: 12 demo/test profiles, three per major. Do not add login, SIS/LMS integration, real student data, model training, or automatic major detection unless the user explicitly changes scope. PostgreSQL and Docker database infrastructure are authorized.
- The system recommends eligible courses only. It does not build timetables, check class conflicts, or confirm that a course is offered in the current semester. Every recommendation must state that course offerings and official academic rules are not fully verified by the PDFs.
- Eligibility violation rate must remain zero. Eligibility is deterministic and runs before ranking. It covers completed courses, AND/OR prerequisites, credits, elective groups, tracks, and graduation branches as represented in the catalog.

## Recommendation and LLM Pipeline

The recommendation flow is:

1. Receive the selected major, completed course codes, and the user's natural-language request.
2. Use the LLM to extract a validated structured preference, such as workload, difficulty, orientation, interest topics, career goal, target credits, target course count, course type, and prerequisite tolerance.
3. Run the backend eligibility engine against the selected major's catalog.
4. Enrich eligible courses with catalog metadata such as topics, orientation, workload, difficulty, and source status when those fields are available. Unknown values must remain unknown; the LLM must not invent them.
5. Use the LLM to rank only the eligible courses and return validated course codes, scores or ordering, and fit reasons.
6. Use the LLM to produce readable explanations grounded in facts supplied by the backend: eligibility reasons, preference matches, missing metadata, and offering uncertainty.
7. Validate every LLM output against the eligible set. Reject foreign, completed, duplicated, malformed, or blocked course codes. Use a deterministic code-based fallback when extraction, ranking, or explanation fails.

The LLM has three roles in this flow: preference extraction, ranking, and explanation. It never decides eligibility. API keys authenticate calls to the model provider; they must remain server-side, outside Git, and outside frontend responses.

What-if changes may affect preference weights or ranking, never eligibility or catalog data. Recommendation output should expose course code, name, credits, rank/score, eligibility reason, fit reason, source status, and a warning that offering status is unknown unless separately verified.

## Chatbot Scope

The chatbot is a floating button available on all frontend pages. The main page remains focused on profile, transcript, progress, eligibility, and recommendations; HUS information lookup is not a separate page or menu.

The chatbot has two intent branches:

- Recommendation advice: use the selected major, transcript, eligible set, and conversational preferences, then run the recommendation pipeline above.
- HUS information Q&A: answer only from a crawled/retrieved knowledge base limited to the training-information pages of the HUS Faculty of Mathematics, Mechanics and Informatics (Khoa Toán – Cơ – Tin học). Answers must cite URL/title/update information where available, refuse out-of-scope questions, avoid guessing, and direct unresolved or conflicting matters to the responsible university office.

The HUS Q&A work still needs its crawler, URL allowlist, document cleaning/chunking, retrieval index, citation model, intent router, and tests. Do not mix HUS FAQ documents with curriculum course data.

Chat history is session-scoped. It is cleared when the user changes major. Do not persist personal chat or student data for the demo.

## Active Repository Structure

Current data handoff state (2026-10-15): `data/` retains only the Data Science 2022 metadata sample after the user's removal of other product catalogs and profiles. The JSON loader, builder, validator and seed tool now support the metadata envelope, but seed preflight still requires four real catalogs and twelve product demo profiles. The existing PostgreSQL data was retained. Offline tests use independent synthetic fixtures; the ten full-source acceptance tests remain unverified until reviewed source data is supplied.

Publishing policy: exclude the entire local `project-toolkit/` and all local skill collections, secrets, environments, caches and backups from Git. Toolkit instructions apply only if it exists locally. The legacy one-time schema replacement script was removed after its authorized use; keep Alembic migrations and the current seed tool.

- `app/` — FastAPI backend, catalog loader, transcript handling, eligibility, ranking, advisor, and static frontend.
- `app/config.py` — centralized server settings; PostgreSQL is the default storage backend and JSON must be explicitly selected for offline work.
- `app/db/`, `app/infrastructure/` — relational schema, pooled connections and JSON/PostgreSQL storage adapters.
- `alembic/`, `docker-compose.yml` — schema migrations and the PostgreSQL 16 development service.
- `data/curricula/` — currently one Data Science metadata handoff sample; the four-catalog runtime dataset is no longer present in the repository.
- `data/README.md` — catalog data contract and provenance notes.
- `tools/build_catalogs.py` — validates and regenerates catalog files from source rows.
- `tools/seed_database.py` — validates and transactionally seeds four versioned catalogs and twelve product profiles; cannot seed from the intentionally incomplete product data currently checked in.
- `tests/` — catalog, transcript, eligibility, recommendation, and advisor tests.
- `docs/SYSTEM_SPECIFICATION.md` — detailed end-to-end product and architecture description.
- `.env.example` — non-secret database and LLM configuration template.

Keep `.agent/KE_HOACH_DU_AN.md` as a historical/product reference. `SE_Project.pdf` was removed at the user's request. Current implementation decisions are documented in `docs/SYSTEM_SPECIFICATION.md` and `docs/DATABASE_DESIGN.md`; module documents describe planned responsibilities, not proof of completed implementation. Do not restore removed roadmap or automatic major detection features merely to match older plans.

## Project Toolkit Invocation

When the user says "hãy dùng project-toolkit để làm yêu cầu sau", "dùng project-toolkit", or explicitly names this toolkit, read `project-toolkit/SKILL.md` and route the request to the relevant locally cloned skill. This is a project-local manual entrypoint, not a globally installed plugin or slash command. Read only the selected source skill and necessary references; preserve the user's advice/planning/execution mode and existing authorization. Default to inline execution/review without extra agents or automatic Git commits. `project-toolkit/sources.json` pins 12 source skills from Superpowers, Anthropic Skills and Supabase Agent Skills. Check sources with `python project-toolkit/scripts/sources.py --check`; restore missing clones with `--restore` only under normal network permissions. Do not silently update sources or install browser/development dependencies merely to invoke the toolkit.

## Progress Reporting and Database Changes

- The user requires progress updates expressed as a percentage during ongoing work. State the scope of that percentage and the completed/remaining milestones; do not describe the entire product as complete when only an infrastructure task is complete.
- Maintain a concrete infrastructure completion checklist in `docs/CODEBASE_CHECKLIST.md`. Count a milestone as complete only after its acceptance checks pass.
- Inspect existing project PostgreSQL schema/data before deciding to reuse or replace it. Reuse suitable infrastructure. Before replacing an unsuitable schema, take and verify a local backup and confirm the target is the SE_Project database. Do not delete unrelated Docker containers, databases, or volumes.
- Keep database credentials server-side and outside Git. Do not persist session transcripts, personal chat, or API keys merely because PostgreSQL is available.

## Development Commands

The commands below describe existing tooling. The metadata sample passes builder validation, while product seed and four-catalog acceptance remain blocked by the intentionally incomplete product data. Default tests use independent synthetic fixtures.

- `python -m pytest -q` — run the active backend and catalog tests.
- Install into the project `.venv` using `python -m pip install -r requirements-dev.txt -c requirements-lock.txt`. Do not start unrelated dependency upgrades while completing an infrastructure task. If package downloads delay work, distinguish the download delay from database/code failures in progress updates.
- `docker compose up -d db` — start the project PostgreSQL service; reuse the existing `se_recommender_pgdata` volume.
- `python -m alembic upgrade head` — apply versioned persistence migrations.
- `python -m tools.seed_database` — validate and seed PostgreSQL from the checked-in JSON sources.
- `python -m alembic check` — check for drift between database and application schema.
- Set `TEST_DATABASE_URL` explicitly to run PostgreSQL integration tests. They create/drop only random `se_test_*` schemas, never the user's public tables; default tests use JSON and mock outbound HTTP.
- `python -X utf8 tools/build_catalogs.py --check` — validate the retained product sample without rewriting it; run with `--root tests/fixtures/catalogs` for all four synthetic test catalogs.
- `python -X utf8 tools/build_catalogs.py --check --report` — print catalog validation details.
- `python -m uvicorn app.main:app --reload` — run the FastAPI app and static frontend.

When adding the HUS crawler or LLM adapter, add isolated tests with mocked network/model responses. Do not require an API key for the default test suite.

The old `se_recommender_db` container was inspected on 2026-10-14. It belongs to Docker Compose project `se_project` at `E:\SE_Project`, database `course_recommender`, volume `se_recommender_pgdata`. Its old `cced58321476` schema contained only catalog seed data and empty student/run tables. A verified custom-format backup was saved to `backups/se_project_before_pg_v2_20261014.dump` before replacing the legacy tables with migration `20261014_01`. Container, database and volume were retained. Catalogs have content-addressed revisions; runtime storage failures return a server error and must never silently fall back to JSON.

The PostgreSQL integration task completed on 2026-10-14: 54/54 tests passed in a fresh project `.venv`, Ruff and pip check passed, Alembic reported no schema drift and all four source catalogs passed validation. Runtime database contains 4 programs, 290 courses, 410 prerequisite options and 12 demo profiles. Docker binds PostgreSQL to 127.0.0.1:5432. Deeper backend ownership/schema refactoring and frontend splitting/stale-response protection remain listed in `docs/CODEBASE_CHECKLIST.md`; no claim is made that all module features or the whole codebase are complete.

## Coding and Testing Rules

Use typed Python with Ruff/Black-compatible formatting. Use `snake_case` for Python names, `camelCase` for JavaScript names, and `PascalCase` for classes/components. Keep eligibility, ranking, explanation, and HUS retrieval as separate responsibilities.

Add tests for major isolation, catalog validation, prerequisite DAG/AND/OR behavior, elective and graduation rules, preference extraction, topic matching, LLM output validation, fallback ranking, grounded explanations, HUS citations/guardrails, and What-if flows. Deterministic fixtures must reproduce rankings, and no test may allow a blocked course into an LLM candidate set or final response.

## Git and Security

Use imperative commits such as `Add structured preference extraction`. Pull requests must describe scope, list tests, update `docs/SYSTEM_SPECIFICATION.md` for architectural changes, and include UI screenshots when relevant.

Use synthetic or anonymized data only. Never commit `.env`, API keys, student identifiers, crawled secrets, or database credentials. Keep provider keys in environment variables and update `.env.example` instead.
