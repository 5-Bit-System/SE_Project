# Project Memory and Contributor Guidelines

## Session close — 2026-10-23: UI published and port 8000 agreed

This section supersedes earlier notes below saying the UI changes are local,
uncommitted or not authorized for push. User requested commit, then explicitly
requested push to GitHub `main`. Both commits were successfully published:
`0a2f76c` (semester transcript and gradient themes) and `e170950`
(appearance label and Vietnamese/English interface switching). Verified remote
`refs/heads/main` and local HEAD both equal
`e170950fdd13931d3041910809be5ccb3d571ab8`; local `main` tracks `origin/main`
with no ahead/behind. Working tree was clean before this memory-only update.

User explicitly agreed to **port 8000** for running, viewing and testing the
system in subsequent sessions: **http://127.0.0.1:8000/**. Use this as the
standard frontend/API address; ports 18080 and Chrome DevTools ports in older
evidence are historical test helpers, not the user-facing runtime address.
Docker PostgreSQL remains at `127.0.0.1:5433`, database `ai07`. Keep the existing
credential files and HUS runtime configuration. Start the app when needed with:

```powershell
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The app was last verified ready with PostgreSQL during this session. Check
`/health` and `/ready` when resuming; a previous background process is not proof
the app is still running. Existing startup logs are ignored under
`backups/semester_ui_20261023/`. The visible browser was refreshed with English
UI while preserving its transcript/term/source-preview/chat session in memory.

Delivered UI: Sổ học tập branding without visible AI-07, actual academic
year/semester transcript groups newest first, gradient light/dark selector
labelled “Giao diện”, and Vietnamese/English UI selection. Appearance and
language preferences alone persist in localStorage. Source course names without
name_en, source grades and conversation content retain their original language;
the English UI explains the course-name fallback. Portal connector and source
review/apply remain unimplemented. Personal transcript sample stays ignored
under backups and must not be committed or automatically applied to ranking.

Latest language/browser regression passed; theme and semester browser evidence
is recorded below. No new Python/PostgreSQL test run, metadata publication,
live portal connection or live LLM conversation occurred at session close.
User requested memory update and close; leave this memory-only change local
until a later commit/push request. No further implementation is requested now.

## Latest UI fix — 2026-10-23: language selection and appearance label

User explicitly requested commit of the existing UI followed by fixes.
Created local commit `0a2f76c` containing the semester UI and gradient themes.
Then changed visible “Giao diện gradient” to “Giao diện” (including accessible
light/dark names), and expanded the selector from course-name language to UI
language. This correction is being recorded in a separate local commit; verify
the resulting hash with Git. No push was requested.

Root cause: selector only changed course names; the live first major exposed
65 courses with zero name_en values, so all names fell back to Vietnamese.
New `app/static/i18n.js` translates known UI copy/templates, including dynamic
renders, reversibly through WeakMap originals and MutationObserver. Language
preference alone is stored as `study-workspace-language`. Source course names
without English metadata, source grades and user/LLM chat remain unchanged;
the UI displays an explicit source-name fallback note. No runtime catalog
publication or invented course translations. Corrected what-if “Chế độ” encoding.

Committed browser regression source is `tests/frontend/check_language.mjs`;
it passed VI/EN switching, persistence, async major/API renders, name_en and
fallback branches, synthetic source preservation, recommendation/what-if,
chat window labels, theme compatibility and 390px containment, with no JS
exceptions. English screenshot inspected; JS syntax and diff checks passed.
No Python/PostgreSQL rerun or live LLM conversation for this frontend fix.
Details: `docs/LANGUAGE_UI_FIX_2026_10_23.md`. Real sample remains ignored.

## Latest UI update — 2026-10-23: selectable gradient themes

User requested gradient light/dark interfaces with regular progress reports.
Applied the GitHub frontend-design skill and local project-toolkit guidance.
Header now has an accessible Sáng/Tối selector. `app/static/theme.js` restores
the validated light/dark preference before CSS paints; first visit follows OS.
Only `study-workspace-theme` is stored in localStorage. Blocked storage still
allows switching for the session, and storage events synchronize other tabs.
Transcript/chat remain session-only and unchanged by theme switching.

`app/static/themes.css` defines light blue/lavender and dark navy/indigo/teal
gradients plus matching surfaces for transcript tables, rules, recommendation
results/forms, notices and advisor chat. Semester/year/source preview behavior
from the previous correction remains in place. No backend/data changes.

Headless Chrome checks passed for both themes, persistence, OS default versus
explicit choice, blocked storage, Enter activation, transcript preservation,
36-row source preview, 5 recommendation results per mode and chat controls.
No page overflow at 390px or JS exceptions. Ten main text/background palette
pairs measured above 4.5:1; screenshots inspected. JS syntax and diff checks
passed. No Python/PostgreSQL rerun or live LLM test for this visual change.
Report: `docs/GRADIENT_UI_2026_10_23.md`; evidence remains ignored under
`backups/semester_ui_20261023/gradient-*`. Changes local; no commit/push requested.

## Latest UI correction — 2026-10-23: actual academic terms

User rejected the fixed semester 1–12 design and provided portal screenshots
for a table grouped by actual academic year/semester/code, newest first.
This supersedes the earlier semester UI description below. Frontend now has
a continuous source preview table with STT, course code/name, credits, source
10-point/letter/4-point grades, grouped by academic year, semester and source
term code. Manual entry creates actual year/semester groups instead of a
fixed sequence. Unassigned records retain an explicit unassigned group.

User explicitly allowed their transcript as a UI sample. It exists only in an
ignored local JSON under backups, without name/student ID; do not commit real
transcript data. The browser reads a selected local JSON file into session
memory via “Mở bảng điểm mẫu”. It is a read-only preview, separate from manual
transcript, GPA/KPI and recommendations. No portal connector or review/apply
flow was implemented, no catalog matching or grade conversion was invented.
Retakes are retained as distinct source rows. Refresh clears the preview;
select the local file again to reopen it. Major change clears preview and terms.

Browser checks passed for file loading, newest-first grouping, preservation
of source grades, duplicate attempts, text escaping, invalid input rollback,
manual academic terms, major isolation and mobile containment; no JS errors.
Screenshots were inspected. Updated evidence is ignored under
`backups/semester_ui_20261023/portal-*`. A visible browser was opened with the
sample at http://127.0.0.1:8000; PostgreSQL readiness returned ok. Uvicorn was
launched as a hidden background process with local logs in that backup folder.
Syntax and diff checks passed; Python tests were not rerun after this UI-only
correction. Changes remain uncommitted; no push requested.

## Session update — 2026-10-23: semester transcript UI

User requested removal of visible AI-07 branding and a redesigned interface
using the local GitHub frontend-design skill and project-toolkit. Local changes
rename the UI to “Sổ học tập”, replace the logo/favicon and introduce actual
HTML transcript tables grouped by user-assigned semester. Course selection is
a separate collapsible catalog table. Users can add, grade, move and remove
courses. Semester metadata exists only in browser session state; API contracts
and academic catalog facts are unchanged. Records with no actual semester are
shown under “Chưa xếp học kỳ”; do not infer actual semesters from catalog order.
Year sample controls are hidden when year metadata is absent, and year filters
explicitly reject null. Switching major resets transcript, term and filters.

Chrome headless checks passed for grouping, grading, moving/removing courses,
filtering, four majors (65/67/90/68), five recommendation results and chat window
controls; no JavaScript exceptions or page overflow at 390px. Desktop/mobile
screenshots were inspected. Evidence is ignored under
`backups/semester_ui_20261023/`; design/behavior report is
`docs/SEMESTER_UI_2026_10_23.md`. JavaScript syntax and diff checks passed.
Changes remain local; no commit/push requested in this session.
Offline regression including HUS PDF acceptance: 302 passed, 35 deselected,
one existing Starlette/httpx warning. PostgreSQL tests were not rerun.

## Latest session close - 2026-10-23: main rename and PDF path correction

This section supersedes older branch names, publication targets and PDF-path failure status below. The user renamed the GitHub default branch from `codebase` to **`main`**; all future publication/integration targets are `main` unless the user says otherwise. Remote HEAD and `refs/heads/main` were verified at `e98f59c4d111c487358f2d018f6c5d997b97e62e`; remote `codebase` was absent. The earlier frontend/specification commit `e98f59c` was successfully pushed before the rename.

Local branch is now `main`, tracking `origin/main`, at the same commit with zero ahead/behind. The old local `main` at `bfcbcbc` was preserved as `archive/main-before-rename-20261023-bfcbcbc`; do not delete/reset it as part of ordinary synchronization. Local `origin/HEAD` now points to `origin/main`. A stale `origin/codebase` remote-tracking ref can remain until an explicit fetch/prune; do not treat it as the publication target. Other local branches were preserved.

All five original PDFs live in **`docs/pdf/`**; keep names, bytes and provenance intact. `tests/support/hus_acceptance.py` was updated locally to search that directory relative to the HUS expectations root, preserving exactly-one-file and SHA-256 assertions. The acceptance README and PDF review report now reference the new location. No catalog facts, PDF contents or expected academic values were changed.

Validation after the path correction: **302 passed, 35 deselected, no skipped tests**, using `python -m pytest tests -q -m "not postgres and not hus_postgres" --full-catalog-root docs/acceptance/hus_2022`. This includes all ten full_catalog_acceptance cases; the previous five missing-PDF failures are resolved locally. Ruff for the changed helper passed. One existing Starlette/httpx warning remains. No local PostgreSQL rerun or new whole-suite 337-pass claim is warranted.

Live GitHub Actions audit before this local correction confirmed run **39831744395** on `main` at `e98f59c`: offline, postgres and hus_postgres all succeeded; the final job completed at **01:29:52 Asia/Saigon on 2026-10-23**. The screenshot's yellow 2/3 did not establish a failure. That workflow excludes full_catalog_acceptance; adding an explicit acceptance job is still planned. Remote CI has not validated the uncommitted path correction yet.

`docs/KE_HOACH_CI_VA_NGHIEM_THU_MODULE.md` records verified CI evidence, module acceptance gates and the remaining roadmap. It is a local untracked plan, not implemented workflow changes. The audit plan has a current-status note marking the PDF fix complete locally. Outstanding items remain preference normalization/fallback, text/form limit precedence, null-year sample buttons, what-if baseline, advisor constraints, detailed progress UI, portal integration owned by the user's teammate, and corpus/RAG implementation. Module work remains Markdown specifications/plans only; OCR transcript is removed from scope, source PDF OCR may still be required. Catalogs remain draft_unverified and no runtime publication occurred.

At the initial close the changes were left local. The user subsequently explicitly requested **commit and push** of this PDF-path correction, related documentation, CI/module plan and memory to `origin/main`. That request supersedes the earlier instruction to leave this set uncommitted. Publication preparation starts from `e98f59c`; use Git to verify the resulting commit and remote outcome. No implementation of the remaining module/workflow plans is included in this publication.

## Session update - 2026-10-23: frontend and module documentation publication

The user requested commit and push to `origin/codebase` after the frontend redesign and documentation work. Publication preparation started from `1f95c3e`; verify Git for the resulting head and push outcome. The frontend remains FastAPI/static HTML/CSS/JavaScript and now uses a light academic workspace, responsive navigation and improved accessibility. Applied local project-toolkit and the user's `.github/skills/frontend-design` skill. Browser evidence in ignored `backups/frontend_redesign_20261023/` covers four majors (65/67/90/68 courses), tabs/keyboard/search/manual completion, recommendations/what-if and chat open/maximize. No JavaScript exceptions were observed; desktop/mobile screenshots were inspected. JavaScript syntax and diff whitespace checks passed.

The user explicitly limited module work to Markdown specifications and plans, not feature implementation. `modules/README.md` links 11 updated module specifications. Transcript OCR specification was removed and replaced by module 09 portal import; the user's teammate owns portal login/SSO/CAPTCHA/OTP and retrieval. The main system will normalize/review/apply its output; no URL or credentials are needed to continue independent planning. Modules 10/11 specify corpus release and HUS RAG. Portal import, RAG serving and the planned fixes are not implemented. Manual entry remains the fallback; transcript/chat use stays session scoped. OCR for scanned HUS source PDFs can still be needed and is separate from removed transcript OCR.

Current plans/reports: `docs/KE_HOACH_XU_LY_DATA_RAG_HUS.md`, `docs/RA_SOAT_MODULE_VA_KE_HOACH_CHINH_SUA_2026_10_23.md`, and `docs/FRONTEND_REDESIGN_2026_10_23.md`. The five original PDFs have moved from `docs/` to `docs/pdf/`; all five were compared byte-for-byte via SHA-256 with their Git originals and match. Source documents must be preserved.

Latest audit validation: **297 passed, 5 failed, 35 deselected**, with `tests --full-catalog-root docs/acceptance/hus_2022 -m "not postgres and not hus_postgres"`; Ruff on app/tests passed. All five failures arise because `tests/support/hus_acceptance.py` still searches for PDFs directly in `docs/`. This resolver fix remains planned, not performed. Do not claim current acceptance is green based on historical 337-pass runs. Other reproduced issues: preference validation on 201-character goals or 40 credits; text-derived count has no explicit precedence with form limits; year-based sample buttons operate on null years. What-if baseline revision, portal attempt policies and detailed progress UI remain planned. No PostgreSQL rerun, runtime catalog publication or live portal/LLM test occurred in this audit.

## Latest session close - 2026-10-22: crawler candidate fetched and pushed

Local `codebase` and `origin/codebase` are at `1f95c3e39f2a17453c8bf2957f7c5a35ef94c6d5` (`data: add HUS crawl candidate snapshot`), pushed successfully to GitHub. The commit contains only the crawl candidate data; `.agent/AGENTS.md` was left uncommitted and is the sole working-tree modification after the push. The fetched `origin/crawldata` snapshot is `3a45aae1732eccbb011f43428bee48add9bb718a`.

Copied the branch's crawl output into `data/hus/releases/2026-10-22-3a45aae-candidate/`: `processed/catalog.json`, 106 processed Markdown files, 101 raw HTML files, `manifest.json`, and a README. The manifest records the source commit and catalog SHA-256. This is a **candidate only**, not an approved/active release. The application does not read this path; no active pointer, crawler code merge, RAG serving integration, runtime publication, or scheduled crawl was introduced. Preserve this snapshot as immutable and create a new versioned directory for future releases.

Review findings retained in the candidate manifest: six catalog documents are `pending_ocr`; all 106 have `academic_year=null`; `data/hus/README.md` says sources are empty while `config/sources.json` contains enabled sources, which must be reconciled before any official crawl/release. The data-only commit did not run tests. `git diff --check` reports trailing whitespace in original raw HTML; keep source HTML unchanged.


## Session close - 2026-10-22: PDF-backed HUS acceptance (prior state)

This section supersedes historical Git/test status below. Local `codebase` and `origin/codebase` match commit `46e02f765d0c41ddd8d286413f5ea397cc8a362d` (`test(database): add PDF-backed HUS acceptance and remove unused schema`). The user authorized the commit/push and it succeeded. The working tree was clean before this memory-only update; leave this update local until another commit/push request.

All five technical tasks in `docs/DATABASE_TEST_IMPROVEMENT_PLAN.md` are complete. Five original PDFs, the independent 297-occurrence code/page inventory, HUS acceptance expectations, test changes and cleanup are published in that commit. Latest full combined validation after cleanup: **337 passed, zero skipped**, Ruff passed, with the existing Starlette/httpx warning. Before commit, two newly added Vietnamese strings in the source group were corrected for encoding; the 10 acceptance cases plus the inventory test were rerun: **11 passed**, Ruff passed. No full-suite rerun after that text-only correction. JUnit evidence remains under ignored `backups/catalog_acceptance_20261022/`.

Read `docs/DATABASE_TEST_IMPROVEMENT_PLAN.md` for completed work, `docs/VINH_DATABASE_TEST_REPORT.md` for test evidence, and `docs/HUS_PDF_ACCEPTANCE_REVIEW.md` for scope and unresolved academic issues. Run acceptance with an explicit tests path and `--full-catalog-root docs/acceptance/hus_2022`; without the option the ten cases still skip by design. Both legacy JSON and HUS acceptance paths remain supported.

The user confirmed cohort 2022, is the final reviewer, and does not know whether later amendments exist. Catalogs remain `draft_unverified`: automated acceptance covers the recorded assertions, not every field of every PDF row or academic validity. MAT3402 definition, MAT3325 differing prerequisites, PHI1002 effective-source confirmation and later amendments remain open. Do not invent resolutions or treat the user volunteering to review as completed sign-off.

The source export now preserves Data Science parent group V.2 with summary 28/63 versus subgroup total 57, with a PDF locator. This change has **not been published to runtime ai07**. No schema migration or runtime publication occurred in this work. Database test resources were cleaned; accounts/students/course_attempts remained empty at the last check. Cleanup removed only the unused HUS schema module and regenerable artifacts/caches (about 54 MiB); original PDFs, OCR TXT/TSV, CSV/JUnit and rollback dumps remain. No new work is requested at session close.

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
