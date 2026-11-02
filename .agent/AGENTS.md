# Project Memory and Contributor Guidelines

## Current Handoff — 2026-10-28

- Publication authorized (2026-11-02): user explicitly requests committing/pushing
  current RAG changes to GitHub in fewer than20 new commits. Publish on crawldata;
  seven scoped commits planned from be76f50b, normal fast-forward push. This overrides
  older local-only/no-commit notes for this publication only. Main integration,
  production activation and merging other histories remain outside this request.
  Keep imported v3/validator provenance pinned to original a543cf8d (Viet Nguyen);
  import commits describe byte-exact vendoring, never claim copied work was authored
  by the integrator. Preserve local diagnostic HTML and HUS_MANUAL_TEST.md outside
  publication; backups/config/toolkit stay local. Verify Git/remote for actual outcome.

- Latest RAG scope correction (2026-11-02): user explicitly limits this branch to
  F1/F2/F3 and basic conversation, no course ranking/explanation. New app.hus.demo:app
  and app.hus.chat isolate execution/imports from the product academic stack. New
  hus-rag-demo UI selects real release majors/versions; no transcript, fake catalogs,
  account, eligibility or provider needed in local demo. Tracked command:
  python -m tools.run_hus_rag_demo; old ignored open_hus_rag_demo.py now aliases it.
  Basics use fixed greetings/thanks/help/goodbye; out-of-scope requests abstain.
  Academic citations/review/AI opt-in/source bytes unchanged. P04/P05 worktrees and
  receipts remain historical; their mixed advisor router is not the new RAG path.
  Before main publication, integrate a dedicated HUS endpoint with existing verified
  account/CSRF/Origin/binding/revision and obtain new commit/CI/acceptance evidence.
  No commit/push/production activation authorized here. See docs/HUS_RAG_MANUAL_DEMO.md,
  scope design/plan dated2026-11-02 and docs/acceptance/hus_rag_scope_report.json.
  Final local checks:18 scope tests (also newer FastAPI0.143), full crawldata717 pass/
  26 skip in crawler-complete p04 venv,5 Node legacy,50 Chromium questions4 majors,
  stale scope/PDF13+12 pass. First full attempt in p05 runtime venv lacked python-docx;
  complete rerun passed; no runtime venv/dependency mutation. P04/P05 outputs34/43,
  shared inputs77 each and63 data hashes verified unchanged. No commit/push.

- Historical manual RAG demo before scope correction (local 2026-11-02): ignored launcher
  backups/hus_integration/open_hus_rag_demo.py opens frozen p05-main in visible
  Chromium with synthetic in-memory account/context and real HUS RAG data. Uses
  p05-ci-venv, defaults data_science; --major selects other programs, --smoke checks
  real F2 answer/citation headlessly. No product auth/DB/VNU or frozen source changes.
  See docs/HUS_RAG_MANUAL_DEMO.md; keep terminal running, close app tab/Ctrl+C to stop.
  Follow-up fixed non-HUS prompts causing the harness's forbidden-provider500:
  launcher-only scoped fallback preserves scope guards and gives honest demo help,
  no synthetic-course recommendations.48 mixed Chromium cases across4 majors pass;
  fresh product regression672 Python/9 Node pass; frozen source/test hashes unchanged.
  Existing demo processes must restart; receipt docs/acceptance/hus_manual_demo_report.json.

- P0-5 preparation (local 2026-11-02): isolated p05-main worktree on main5239b733,
  branch integration/hus-rag-p05-20261102; root stays crawldata. Reviewable bundle
  integration/hus-rag-p05 has77 shared inputs/43 outputs; replay61 backend/9 Node pass.
  CI workflow/locked deps, build/data/test identity receipts and guarded activation/
  rollback implemented. Clean locked venv:672 Python/10 skips/80 DB deselected,
  9 Node,43 HTTP/14 Chromium pass;20 lifecycle cases and copied-selector drill pass.
  Canonical selector remains prepared/byte-identical. Dirty receipts are ineligible;
  strict rejects uncommitted code. Preserve genuine source authors/ancestry and main
  feature-branch PR/Create a merge commit. No commit/push/PR/merge, remote CI or real
  production activation: user explicitly requires a separate commit/push request.
  See docs/RAG_P05_RELEASE_PREPARATION.md and docs/acceptance/hus_p05_* reports.

- P0-4 (local 2026-11-02): main5239b733 fetched and integrated in isolated worktree
  backups/hus_integration/p04-main, branch integration/hus-rag-p04-20261102. Root
  remains crawldata with prior WIP. Adapter runs in /me/advisor/chat after existing
  operation/ready and rechecks ensure_current; strict AI opt-in, server-bound major.
  Keep verified account, CSRF/Origin/host, source/binding/session revision. Legacy
  HUS chat409, no public /hus/chat; source binaries account-protected. Active UI adds
  separate hus-chat module with generation/refresh race guards, no stored history.
  652 Python/10 skipped/80 DB deselected,9 Node,43 live HTTP/14 Chromium pass using
  synthetic auth stores/policies/catalogs and real HUS data; no product DB/VNU/provider.
  Reviewable replay package in integration/hus-rag-p04 plus prepare_hus_main_integration
  tool;77 shared inputs/34 source outputs verified, replay41 backend/9 Node pass.
  See docs/RAG_P04_MAIN_INTEGRATION.md and hus_p04_authenticated_report.json.
  Ready gate/review/source bytes unchanged. No commit/push/PR/merge or production
  activation; P0-5 owns publication, must retain feature-branch PR and team ancestry.

- P0-3 (local 2026-11-02): independent character-to-page ownership oracle for F1
  quotes; F2 oracle requires every source occurrence exactly once and PDF locators,
  never JSON as open target.29 new regression/API tests, including21 intentional
  citation corruptions. Node explicitly tests null-link AI responses. Chromium tests
  actual MAT3325 answer with two same-PDF sources at13/12 and opens both viewer pages.
  Receipt schema2.0 additionally pins24 test/fixture files and10 screenshots;2318 HTTP,
  47 Chromium pass;699 Python/26 skipped,5 Node. PDF viewer readiness waits for
  load success, physical page, zero unacked remote scrolls and matching inner-frame
  scroll, then two animation frames. See docs/RAG_P03_CITATION_TESTS.md and receipt.
  Runtime/data/review unchanged in P0-3; next scope is main API/UI/auth integration.

- P0-2 (local 2026-11-02): citations now have evidence kind/display label/open URL,
  expected document hash, physical page/span and availability. Generated F3 renders
  "kiến thức AI" without links, retains warnings/opt-in/review. Web opens original URL.
  data/hus/citation_assets contains12 PDFs+2 DOCX imported byte-exact from a543cf8d,
  registry bound to selected v3. /hus/sources/{sha256} GET/HEAD/range verifies actual
  bytes/hash/format/page; PDF inline, DOCX attachment; missing or changed files fail
  honestly. F1 page locations match quotes in hash-bound recovered text, not new
  academic/visual review. v3/legacy payloads and review unchanged. See
  docs/RAG_P02_CITATIONS.md; acceptance receipt hus_p02_citations_report.json.
  Verification:670 Python passed/26 skipped,4 Node,2318 HTTP,41 Chromium;14 binaries
  and28 emitted page URLs checked. Full Chromium channel is needed for PDF viewer;
  external web destinations are intercepted in browser tests, not health-certified.

- P0-1 (local 2026-11-02): runtime now strictly selects CURRENT -> portable
  hus-data-20261031-v3 (sha256 27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4).
  Imported exact release/validator bytes from a543cf8d; legacy 19 payloads retained.
  F1 69->65 is four resplits with the same63 units/source spans/edition/review; F2 tables
  unchanged, canonical source imports existing67 KHMTTT user sign-offs and223 draft,
  never institutional certification or F3 approval. API and retriever pin one snapshot;
  missing/corrupt CURRENT is503, no legacy fallback. Generated opt-in defaults false
  (allow_generated_reference in API, checkbox in legacy chat); each response includes
  release identity. See docs/RAG_P01_DATA_SELECTION.md and machine-readable diff.
  Older data/receipt statements below describe legacy snapshots, not current selection.
- End-to-end acceptance (local): `tools/verify_hus_e2e.py` runs real loopback Uvicorn
  and optional real Chromium with synthetic UI catalogs and the actual HUS handoff.
  Latest receipt: docs/acceptance/hus_e2e_report.json; 2310 HTTP and 25 browser cases pass,
  full membership/field and citation checks, cross-major/version refusals and stale-chat
  isolation. See docs/HUS_E2E_ACCEPTANCE.md. Exam weight/format fact requests now route
  to evidence checks before recommendation intent; major aliases consume specific names
  before contextual Math aliases. No product DB/provider/remote deploy or academic review.
- Answering addition (local work): `app/hus/answering.py` and `app/schemas/hus.py`
  provide extractive F1/F2/F3 answers with explicit sources/review/generated labels.
  `POST /hus/chat` exposes this; `/advisor/chat` routes clear HUS information intents
  before runtime catalog/provider calls, keeps recommendation/guardrails on the old path,
  and returns mode=hus_rag plus hus_answer. Unsupported/official-current/missing evidence
  returns no_information, incomplete identity needs_clarification; corrupt packages are
  503, not fabricated missing answers. The service lazy-caches one snapshot; reload after
  package changes. UI links HTTP(S) citations and rejects old-context chat responses.
  Raw-only unresolved prerequisite codes (MAT3423 -> MAT3402) now remain flagged without
  creating parsed eligibility edges. No LLM, product DB, remote deploy or academic review.
- Retrieval addition (2026-11-01, local work): `app/hus/retrieval.py` provides
  `HUSRAGRetriever.search()` over the loader's F1/F3 chunks. Major/version/field/variant
  and explicit/query course codes filter before BM25 scoring/top-k; no cross-scope
  fallback or qa/origin directory scan. Vietnamese accent-insensitive lexical ranking
  excludes repeated F3 warning/context from topic scoring but preserves output metadata.
  Deduplicate identical slices only within the same scope/source. No embeddings,
  generated answers or API integration; F2 remains the loader's structured lookup.
- Loader addition (2026-11-01, local work): `app/hus/rag_loader.py` provides
  `HUSRAGData.load()` for the shared package. It validates package files/checksums,
  reads F1/F3 chunks separately and looks up F2 by exact code/major/version, retaining
  reviews, provenance, generated warnings, raw prerequisites, duplicate source rows and
  unresolved/conflicting states. Results are defensive copies. This is an offline
  snapshot library, not retrieval/API integration, academic verification or a new raw
  review gate. Reload after rebuilding the package; do not assume it was published.
- Active data-preparation branch: `crawldata`. Base before this work was `38a5ddbd604469754e8e4de0c423a08e8976cdb6`. The user explicitly requested publication as **exactly 30 new commits**; inspect Git/remote history for the final publication state, never infer it from this note.
- Current shared handoff is `data/hus/rag/{f1,f2,f3}` with checksums/origin paths in its manifest. Keep the source/release artifacts under `data/hus/qa/20261028/` for reproducibility; index only one copy of each dataset.
- F1 currently has 15 sources / 69 chunks: 5 raw-HTML-compared sources plus 10 sources explicitly approved by the user for descriptive F1 from existing Markdown. The ten use `include_markdown`, selected-F1 scope and `raw_original_verified=false`; do not claim original PDF/DOCX or current academic validity was verified. The mixed Toan Co careers page was excluded by user request, pending is empty, and duplicate CLC narratives retain provenance without duplicate retrieval weight. The original raw review gate remains unchanged.
- F2 exists for all four majors on remote main at `cfb2ec4c7f3f8e80428abc3db535dad0cc5db41d`: `database/data/hus_source.json`, 290 course/program memberships and 297 source occurrences. A byte-identical pinned copy is retained in the F3 inputs and shared `rag/f2`. The local crawldata curriculum sample alone is not the complete repository-wide F2 inventory. Preserve source draft/unresolved/conflict states.
- F3 is a separate AI-generated reference dataset explicitly requested by the user: 290 records / 870 chunks, 174 in-scope codes, 154 authored concept blueprints. Keep disclosure labels, edition/major filters, and official syllabus/assessment/weight fields null. Do not insert generated F3 through the official-source review gate or present it as an official HUS syllabus.
- Latest local verification before publication preparation: **541 passed, 26 skipped**; Ruff, diff checks, all applicable release reproductions and shared payload checks passed. No embeddings/vector index, live chatbot/LLM, database publication, or remote CI verification is implied. Two diagnostic HTML files and `docs/HUS_MANUAL_TEST.md` were untracked before this task and remain outside its commits.
- Older statements below about missing product data/PDFs apply to the historical local foundation checkout. Current source limitations and the Markdown-only F1 exception are documented in `docs/HUS_QA_DATA_AUDIT.md` and the current dataset READMEs.

## Historical Foundation Handoff — 2026-10-15

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

Keep `KE_HOACH_DU_AN.md` and `SE_Project.pdf` as historical/product references. Current implementation decisions are documented in `docs/SYSTEM_SPECIFICATION.md` and `docs/DATABASE_DESIGN.md`; module documents describe planned responsibilities, not proof of completed implementation. Do not restore removed roadmap or automatic major detection features merely to match older plans.

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
