# Project Memory and Contributor Guidelines

## Project Context

This repository is the codebase for an Explainable Course Recommender (AI-07). The product helps students inspect a synthetic academic profile, transcript, curriculum progress, eligible courses, and ranked course recommendations. Use `docs/SYSTEM_SPECIFICATION.md` and `docs/DATABASE_DESIGN.md` for current implementation decisions; `KE_HOACH_DU_AN.md` and `SE_Project.pdf` remain product/historical references. The latest explicit user instructions take precedence over older plans.

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

Current data handoff state (2026-10-14): the user requested retaining only the Data Science 2022 metadata sample in `data/`. Other catalogs, synthetic profile fixtures and the old validation report were removed after a verified local ZIP backup. The sample uses the new metadata envelope and is not compatible with the existing JSON loader/builder/seed. Do not restore removed catalogs or silently treat it as runtime seed. Existing PostgreSQL data was retained. On publication, the default suite reports 22 passed, 21 failed and 11 PostgreSQL tests skipped because catalog-dependent tests still expect the previous dataset. The earlier 54/54 result below is historical, before this data change.

Publishing policy: exclude the entire local `project-toolkit/` and all local skill collections, secrets, environments, caches and backups from Git. Toolkit instructions apply only if it exists locally. The legacy one-time schema replacement script was removed after its authorized use; keep Alembic migrations and the current seed tool.

- `app/` — FastAPI backend, catalog loader, transcript handling, eligibility, ranking, advisor, and static frontend.
- `app/config.py` — centralized server settings; PostgreSQL is the default storage backend and JSON must be explicitly selected for offline work.
- `app/db/`, `app/infrastructure/` — relational schema, pooled connections and JSON/PostgreSQL storage adapters.
- `alembic/`, `docker-compose.yml` — schema migrations and the PostgreSQL 16 development service.
- `data/curricula/` — four independent JSON catalogs and source transcription/validation metadata.
- `data/README.md` — catalog data contract and provenance notes.
- `tools/build_catalogs.py` — validates and regenerates catalog files from source rows.
- `tools/seed_database.py` — validates and transactionally seeds four versioned catalogs and 12 synthetic profiles; repeated imports are idempotent.
- `tests/` — catalog, transcript, eligibility, recommendation, and advisor tests.
- `docs/SYSTEM_SPECIFICATION.md` — detailed end-to-end product and architecture description.
- `.env.example` — non-secret database and LLM configuration template.

Keep `KE_HOACH_DU_AN.md` and `SE_Project.pdf` as historical/product references. Current implementation decisions are documented in `docs/SYSTEM_SPECIFICATION.md` and `docs/DATABASE_DESIGN.md`; module documents describe planned responsibilities, not proof of completed implementation. Do not restore removed roadmap or automatic major detection features merely to match older plans.

## Project Toolkit Invocation

When the user says "hãy dùng project-toolkit để làm yêu cầu sau", "dùng project-toolkit", or explicitly names this toolkit, read `project-toolkit/SKILL.md` and route the request to the relevant locally cloned skill. This is a project-local manual entrypoint, not a globally installed plugin or slash command. Read only the selected source skill and necessary references; preserve the user's advice/planning/execution mode and existing authorization. Default to inline execution/review without extra agents or automatic Git commits. `project-toolkit/sources.json` pins 12 source skills from Superpowers, Anthropic Skills and Supabase Agent Skills. Check sources with `python project-toolkit/scripts/sources.py --check`; restore missing clones with `--restore` only under normal network permissions. Do not silently update sources or install browser/development dependencies merely to invoke the toolkit.

## Progress Reporting and Database Changes

- The user requires progress updates expressed as a percentage during ongoing work. State the scope of that percentage and the completed/remaining milestones; do not describe the entire product as complete when only an infrastructure task is complete.
- Maintain a concrete infrastructure completion checklist in `docs/CODEBASE_CHECKLIST.md`. Count a milestone as complete only after its acceptance checks pass.
- Inspect existing project PostgreSQL schema/data before deciding to reuse or replace it. Reuse suitable infrastructure. Before replacing an unsuitable schema, take and verify a local backup and confirm the target is the SE_Project database. Do not delete unrelated Docker containers, databases, or volumes.
- Keep database credentials server-side and outside Git. Do not persist session transcripts, personal chat, or API keys merely because PostgreSQL is available.

## Development Commands

- `python -m pytest -q` — run the active backend and catalog tests.
- Install into the project `.venv` using `python -m pip install -r requirements-dev.txt -c requirements-lock.txt`. Do not start unrelated dependency upgrades while completing an infrastructure task. If package downloads delay work, distinguish the download delay from database/code failures in progress updates.
- `docker compose up -d db` — start the project PostgreSQL service; reuse the existing `se_recommender_pgdata` volume.
- `python -m alembic upgrade head` — apply versioned persistence migrations.
- `python -m tools.seed_database` — validate and seed PostgreSQL from the checked-in JSON sources.
- `python -m alembic check` — check for drift between database and application schema.
- Set `TEST_DATABASE_URL` explicitly to run PostgreSQL integration tests. They create/drop only random `se_test_*` schemas, never the user's public tables; default tests use JSON and mock outbound HTTP.
- `python -X utf8 tools/build_catalogs.py --check` — validate all four catalogs without rewriting them.
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
