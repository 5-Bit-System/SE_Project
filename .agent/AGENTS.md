# Project Memory and Contributor Guidelines

## Session update — 2026-10-27: project relocated to D; connections verified

The canonical workspace is now `D:/SE_Project`. The user copied the project,
recreated the main `.venv` there, and deleted the old `E:/SE_Project`; the final
PowerShell `Test-Path` returned false and the relocation audit reconfirmed it.
Use D for all future commands, editor folders, runtime and local maintenance.
Earlier E paths in dated session entries, archived logs and immutable source
receipts describe historical execution, not a current dependency. Do not recreate
the deleted E workspace or mass-edit byte-bound source/audit evidence.

The user explicitly authorized this memory update, repair of remaining project
path references and connection/regression checks. This authorizes relocation
maintenance, without resuming the unrelated pending RAG/source work below.
Root branch remains `chore/remove-old-crawl-markdown-20261026` at
`7650c123c67082f476af8f4f8c83cf72c0ce9708`; no commit, push, PR or merge occurred.
The existing 107 tracked crawl deletions, data README/manifest changes and
untracked `.vscode/` / `docs/rag_normalization/` were preserved. The RAG handoff's
two local paths were updated; `.vscode/settings.json` itself remains unchanged.

The new main venv now contains Playwright 1.64.1 and uses installed Google Chrome.
The earlier VNU 503 `browser_start/browser_unavailable/missing_dependency` was
caused by omitting `requirements-portal.txt` when rebuilding the venv, not a
removed VNU container. README setup now installs both dev and portal requirements
with the pinned core constraints and explains the Chrome requirement. VNU uses
a Python/Chrome worker; it has no separate Docker container.

Repaired local selection JSON/CSV/Markdown locators, current HUS run/handoff
paths and helper scripts. Helpers now derive their paths where practical.
The copied parser venv at `backups/crawldata_audit_20261026_28d61c4/venv` had E in
its activation/configuration and pip launchers; regenerated it at D, preserving
system-site-package access, and reinstalled its existing pip 24.0 from Python's
bundled local wheel. Its Python, pip, bs4 4.15.0 and soupsieve 2.9.1 were checked.
No global Python environment was upgraded.

The separate HUS feature checkout remains at
`backups/hus_pipeline_worktree_20261026`, HEAD `4b52f85accfad41460cf25c48b678bd11d43341a`,
branch `feat/hus-normalize-chunks-20261026`, unpushed/unmerged. Its former origin
pointed at an already-removed E baseline bundle; origin now points to the valid
local `D:/SE_Project` repository. `ls-remote` succeeded and both repositories
passed `git fsck`. Seven tracked files in this feature checkout (six run/handoff
documents plus the handoff generator) now have local relocation edits; the
original commit/authorship is preserved. The root GitHub origin was also checked
read-only successfully, without fetch or push.

Docker container `se_hus_db` was recreated from `database/docker-compose.yml`
on D because its Compose labels still referenced E. Its only mount remains
named volume `se_hus_pgdata`; the PostgreSQL cluster identifier matched before
and after, and the container is healthy. No migration, seed, catalog publication,
credential change or personal-table inspection was performed. The existing app
on port 8000 was verified through its D venv launcher and reused. Root `.env`,
`.env.auth`, `database/.env.docker` and `.vscode/settings.json` hashes are unchanged.
Process/user/machine environment checks and VS Code user settings found no old
SE_Project path. A scan of 156 active project/config/launcher files and filesystem
reparse targets found no current E project dependency.

Validation on D: 523 offline tests passed, 75 PostgreSQL tests deselected, zero
skipped, including the explicit existing HUS PDF expectation suite. One existing
Starlette/httpx deprecation warning remains. Root Ruff, changed-helper Python/JS
syntax, nested generator Ruff, four synthetic catalog fixture checks and Git
diff checks passed. Five existing Chrome regressions passed: portal auth,
collection, profile source, session and loading; their VNU pages/identities are
synthetic and intercepted. They did not overwrite historical screenshot evidence.

Live read-only checks: `/`, `/health`, `/ready`, `/auth/session`, `/programs`, all
15 referenced assets and the academic-policy PDF returned 200; readiness reported
PostgreSQL and four programs. Anonymous `/me/profile` and `/admin/users` correctly
returned 401. Chrome launched with no local-page JS errors and loaded the public
VNU login form with HTTP 200. SMTP EHLO/STARTTLS succeeded without authentication
or sending mail. LLM remains disabled and no paid provider request was made.
Real-account VNU login/grades and SMTP credentials/delivery were not tested;
these checks do not certify every product behavior or external-service uptime.

The offline HUS completion verifier passed at D with 1,381 records / 1,520 chunks.
Dataset manifest SHA-256 remains
`3dbdd56d0b8c7357bcd0711ec197716868c3f9ffa231b4847eb91af7482cbfae`.
All 106 local selection locators were relocated; the same known historical
`23a0c1df14a5708a` Markdown remains absent, not a new relocation failure. Raw
sources, derived dataset hashes, approval states and academic unknowns remain
unchanged. This verification does not approve or publish the HUS corpus.

Current evidence and rollback copies are ignored under
`backups/relocation_20261027/`: start with `REPORT.md`, `connections.json`,
`integrity.json`, `browser_checks.json`, `offline.xml`, Docker before/after
metadata, `baseline.json` and `originals/`. Originals contain historical paths
for rollback only; do not treat them as runnable current configuration.

## Session close — 2026-10-27: HUS completion and backup cleanup

The user closes this turn with a memory update only. Do not resume source work,
run tests, alter application/runtime/database state, create another commit, push
or merge as part of this close-out. The root project remains on
`chore/remove-old-crawl-markdown-20261026` at `7650c123c67082f476af8f4f8c83cf72c0ce9708`.
Preserve its pre-existing dirty crawl-corpus deletions, README/manifest and RAG
handoff work, and unexamined `.vscode/`; this session changed only this memory
file and ignored backup cleanup documentation/artifacts.

The HUS data-completion implementation is isolated at
`backups/hus_pipeline_worktree_20261026`, branch
`feat/hus-normalize-chunks-20261026`, local commit
`4b52f85accfad41460cf25c48b678bd11d43341a`, based on `5d0dacc`. It was clean at
close and remains unpushed/unmerged. Its outputs are ignored local files under
`backups/hus_completion_20261026/`; a fresh Git clone will not contain them.
Start with `START_HERE.md`, `CHATGPT_HANDOFF.md` and `DELIVERY_RECEIPT.json` there;
reproduction steps live in the feature checkout's
`docs/hus_pipeline/COMPLETION_RUN_V2.md`.

Final dataset manifest SHA-256 is
`3dbdd56d0b8c7357bcd0711ec197716868c3f9ffa231b4847eb91af7482cbfae`.
Results: 20 AI-verified capture metadata fields, 12 issuance facts, 297 visually
checked course occurrences across 22 table pages, 1,381 records and 1,520 chunks.
There are 30 offline descriptive AI-ready chunks, 383 source-checked PDF chunks
outside formal whole-document include, and 1,107 quarantined chunks. No human or
university approval, individual academic applicability, embedding, active release
or runtime/database change is asserted. Final offline suite evidence is 716
passed, zero skipped, 75 PostgreSQL tests deselected; the last full run predates
this cleanup. Independent component/aggregate replays matched 40/98/15 files.
No tests were run for backup cleanup or this memory update.

Five matching original attachments remain missing. The network probe for
`8afffd3cada3d048` failed with WinError 10013; four other URLs were not attempted.
The missing-file list is `backups/hus_completion_20261026/MISSING_SOURCE_REQUESTS.csv`.
Dedicated F3 sources for Mathematics and Data Science remain unavailable. Keep
current validity, remote equality, unresolved printed credit/code conflicts and
individual applicability unknown; preserve the absent historical ID
`23a0c1df14a5708a`. Do not represent the remaining data as full academic or
source acceptance.

On 2026-10-27 the user explicitly asked to remove unnecessary backup files. The
cleanup removed 3,299 files (~642 MiB): two clean nested VNU Git clones whose
commits are already in root history, generated test/cache folders, a byte-
identical completion replay, superseded aggregate builds and old review boards,
plus the stale `5d0dacc` bundle. Before removing the clones, 87 distinct UI
screenshots were moved to
`backups/vnu_eligibility_integration_20261026/visual_evidence_from_clone/` and
`backups/vnu_curriculum_review_20261026/visual_evidence_from_clone/`. The final
HUS completion output, pinned source audit, PDF/OCR assets, baseline, runtime
rollback dumps and unpushed feature checkout were kept. `backups/README.md` has
the inventory. At close, backups occupied about 0.75 GiB, E: had about 0.81 GiB
free, and the only nested Git repository in backups was the active HUS feature
checkout.

The old preservation JSON mishandled five Git-quoted Unicode PDF paths as null.
Close-out verified 547 recorded paths, and separately verified those five PDFs
match root Git `HEAD`; this is not a recovered pre-task hash for those five.
`backups/hus_pipeline_DELIVERY_20261026.json` is historical and refers to an old
ZIP that is no longer present; use the current delivery receipt instead.

## Session close — 2026-10-26: one-file normalization preview pending

User explicitly closes the session and requests a memory update. Stop the
normalization attempt here; this close performs only memory/document-state
recording. No commit/push/PR, application/runtime/DB changes or new source review.

Completed: data audit and F1/F2/F3 selection proposal; general-folder review;
portable handoff at `docs/rag_normalization/HANDOFF_2026_10_26.md` with
`source_selection.csv`, `inventory_snapshot.json`, `example_course_record.json`;
updated package `backups/rag_normalization_handoff_20261026.zip`. Section 1.1
and W2/W3 explicitly require reusing the crawldata metadata models/validators and
basic normalization. The MAT2502 JSON is an illustrative record with unverified
proposals, not a normalized copy of the full source document or an approved source.

The user's final work request before closing was to normalize ONE actual file
and show before/after. Target selected from their IDE context:
`backups/crawldata_audit_20261026_28d61c4/source/data/hus/processed/documents/`
`computer_science/tai-lieu-dinh-kem-4-kctdt-clc-mtkhtt-10082020-0-pdf--8afffd3c.md`
(document ID `8afffd3cada3d048`). Only read-only inspection was done. No preview
script, before/after files, demo directory or full normalized document was created.
If the user resumes, continue by producing a concrete, separate comparison for
that one file; do not claim the earlier MAT2502 example fulfills this request.

Inspection findings for that future preview: the current Markdown has 661 lines,
25 page markers and 19 table blocks. The main curriculum spans 7 table fragments,
with numbered course rows 1–66 and continuation cells across page markers 13,
14 and 16. Preserve fragments and provenance; joining them is an unverified
derived proposal until checked against raw. Do not indiscriminately remove
standalone numbers: `2015` in the final comparison section is a meaningful year.
Beyond the known 78-vs-81 credit discrepancy, the summary/table states 148 total
credits while section 5.3 states 154. Record conflicts rather than silently
repairing values. Original PDF remains missing. Source text/body matches catalog
after stripping only the outer frontmatter/newline wrapper.

Workset remains 12 proposed sources (7 core + 5 supplemental), with no formal
include/chunks. Unknown metadata stays unknown; normalization may create
candidates without assigning verified values or replacing runtime eligibility.
Current branch remains `chore/remove-old-crawl-markdown-20261026`; preserve the
prior old-crawl deletions, README/manifest/memory edits, untracked
`docs/rag_normalization/` and the now-present untracked `.vscode/` directory.
The latter was not created, inspected or modified by this task.

## RAG normalization handoff — 2026-10-26

Metadata clarification: remote crawldata was rechecked and still points to
28d61c4. It already implements MetadataField/ApplicabilityMetadata, proposal and
evidence validation, a 106-document applicability.json, basic text normalization
and corpus build/verify. Complete and verify existing metadata rather than
recreate those models. All nine applicability fields currently have zero
non-unknown verified values; program/variant/cohort/year/validity/effective-date
proposals are also all unknown. Handoff section 1.1 and W2/W3 now make reuse
explicit. The example's nested applicability uses the existing model and
high_quality vocabulary; its additional proposals are illustrative and do not
change source metadata. The portable inventory and handoff ZIP are refreshed.

User asks to consolidate the data state and normalization plan for assigning
work to a teammate. Prepared the shareable, local-only handoff at
`docs/rag_normalization/HANDOFF_2026_10_26.md`, with portable
`source_selection.csv` (106 records), `inventory_snapshot.json` and a real
Markdown-derived MAT2502 `example_course_record.json`. This is documentation
and an example, not implementation of the normalizer or a corpus approval.

Current selection: 7 core + 5 supplemental (3 CLC, 2 general F1) + 6 deferred OCR
+ 3 historical + 85 outside v1 = 106. Workset: 12 documents, 7 with raw HTML and
5 attachments without raw. All selected approved_for_rag flags remain false.
Source review baseline remains 100 needs_review / 6 pending_ocr / 0 include,
0 chunks and inactive. User reading Markdown does not create fabricated
reviewer, timestamp, raw-quality or effective-scope evidence.

Pinned audit tree: 28d61c4bc13ff32592c48ef890a087166494cc59; internal source
manifest still references hus-0404f37-20261026. Local audit has 105 Markdown
against 106 catalog records: the unselected historical 23a0c1df file is missing.
All 161 present manifest files match; do not implicitly restore that local file.
Other machines should obtain a complete isolated source at the pinned commit.
Backups are ignored and are not included in a fresh clone.

Normalization plan preserves sources, creates derived records and source maps,
records proposed/verified metadata and same-scope version decisions, recovers
raw/OCR sources, and leaves unresolved scope/logic unknown. Pipeline 1.4 currently
reviews whole documents; section records cannot bypass require_review or mark
an entire source include after checking only selected paragraphs. Embedding,
runtime publication, DB/catalog/eligibility changes are later work. No normalizer,
full corpus, commit/push/PR or app changes were requested in this handoff turn.

## HUS RAG source-version preference — 2026-10-26

The user selected F1 major overview, F2 curriculum frameworks and F3 course
descriptions for the first RAG source review. They now require the newest
published document when several versions cover the same scope, especially
curriculum frameworks because recommendations depend on them. Compare within
major, degree, program/track and document kind using the issuance evidence in
the source, not filenames or crawl/fetched timestamps. Keep older versions for
historical questions and older cohorts where still applicable. For a student's
course recommendations, the framework must additionally apply to that student's
cohort/program; a newer framework
for another cohort is not automatically applicable. If version/effective scope
is unknown, do not replace the existing verified catalog or eligibility rules
with crawl text.

Updated the ignored selection proposal at
`backups/rag_selection_f1_f2_f3_20261026/SELECTION.md` and its JSON policy.
Current examples: KHMTTT 2024 course descriptions may supersede overlapping
2023 descriptions only after same-scope verification; the 2023 Word framework
has a blank issuance line. Two CLC PDFs both show decision 3340 dated 2019;
`2020` in the filename does not establish a newer version. The 2015 frameworks
remain historical where newer sources are identified but not yet recovered or
OCR-verified. This is a selection rule, not approval of any source or a runtime
recommendation change. No commit/push/PR, database migration or publication.

## Old crawl Markdown removed — 2026-10-26

User explicitly requests deleting all old crawled Markdown data and will supply
replacement data later. This supersedes earlier immutable-snapshot and preserve
instructions for those files, including the preexisting whitespace-only edit to
the document ending `exh01-02-06...0a180289.md`.

On local branch `chore/remove-old-crawl-markdown-20261026`, removed all 106 `.md`
files (2,904,117 bytes) under
`data/hus/releases/2026-10-22-3a45aae-candidate/processed/documents/`.
All were tracked in Git. No commit/push/PR is requested. Preserve the preexisting
memory changes from `docs/session-close-20261026` carried into this branch.

Automatic approval review rejected the initial combined deletion because it
also removed `processed/catalog.json`, outside the explicitly requested `.md`
scope. That rejected command made no deletions. The narrower Markdown-only
deletion succeeded. The user then explicitly answered "Xóa luôn catalog.json
của bộ crawl cũ". Removed that exact catalog (3,232,362 bytes) after checking
its path and SHA-256 against the manifest. The prior review block is resolved;
no deletion approval remains pending. Total removal: 107 files / 6,136,479 bytes.

The 101 raw HTML files remain. SHA-256 checks verified 260 retained snapshot,
sample catalog, original PDF, database source, application and config files
unchanged through Markdown deletion; 259 retained files were checked unchanged
through the subsequent JSON deletion. Updated snapshot README/manifest and data README
record retirement; earlier crawl/chunk statistics are historical. No runtime/DB
change, crawler, preprocessing, index build or restart. New corpus work waits
for the user's replacement data.

## Session close — 2026-10-26: eligibility delivered; owner acceptance pending

User requests session close and memory update only. No new implementation,
commit/push/PR, database write or restart is authorized by this close-out.
Memory edits stay local on docs/session-close-20261026, based on main 7650c12,
to follow the permanent feature-branch/PR rule. Preserve the preexisting corpus
whitespace edit ending exh01-02-06...0a180289.md; do not publish it with memory.

Eligibility delivery is complete through PR #7:
https://github.com/5-Bit-System/SE_Project/pull/7.
Merged using Create a merge commit as 7650c123c67082f476af8f4f8c83cf72c0ce9708.
The genuine integration merge f9e7a0c has parents e781ab3 and teammate 5e1a9bf;
deb3fb0 adds original-owner checks after I/O. Teammate 5e1a9bf keeps author
huyvinh005 and is an ancestor of main and present in PR #7. A duplicate PR from
the old source branch is unnecessary; its existing contribution already has
the PR record and original history. No invented authorship or copied-only credit.

Final verification recorded below remains: 523 offline, 75 PostgreSQL, 35
targeted auth/binding/VNU rerun, 15 fixture Chrome scripts and one real-HTTP/
disposable-PG Chrome flow. PR checks 6/6 and post-merge main checks 3/3 passed.
No tests rerun for branch cleanup or this documentation-only close-out.

Runtime is served from E:/SE_Project at http://127.0.0.1:8000/#rules. Latest
read-only close-out /ready returns status=ok, storage=postgres. Last recorded
launcher PID 23348; verify command lines before any future stop. Health, 15
versioned assets, policy PDF and anonymous personal-route rejection were checked
after deployment. Logs/evidence: backups/vnu_eligibility_integration_20261026/.
RESULT.md there records exact commits, tests, integrity and rollout details.

The runtime backup was restored in isolation; 19 protected table fingerprints
matched before/after rollout. No runtime migration/seed/catalog publication,
password/SMTP changes, manual completeness upgrade or actual grades inspection.
Existing config and corpus hashes were unchanged. Subsequent owner-initiated
confirmation/synchronization may legitimately write binding/snapshots; do not
assume deployment-time fingerprints describe all later user activity.

User authorized deleting completed temporary branches. Removed ONLY
integration/vnu-eligibility-20261026 remotely and from the integration clone,
after full-ancestry verification; that clone is now on main 7650c12. Kept
feat/vnu-curriculum-planning and teammates' other branches. Removed temporary
PostgreSQL test container after verification. se_auth_mail and se_recommender_db
containers were also removed earlier by request; both DB volumes remain.

Latest owner screenshot shows selected program/cohort and consent checked, but
the confirmation form remains and all three columns state that program
confirmation is required. User asked for an answer only: explained that ticking
consent alone does not persist confirmation; press the confirmation/compare
button. If already pressed, the screenshot alone does not identify why the
request did not complete. No authenticated API, DB, logs or personal source was
inspected to diagnose that screenshot, and no fix was made. Do not assert that
the user never clicked, declare a confirmed bug, or mark real-account academic
acceptance complete. If asked to investigate later, check the confirmation
request/result and remaining readiness gates; do not reset seed, transfer owners,
rewrite source records or force verification flags to populate the columns.

## VNU eligibility integration — 2026-10-26

User authorizes implementation, tests and integration of the teammate's
eligibility flow while retaining all existing modules, with frequent progress.
Integration branch integration/vnu-eligibility-20261026 starts at main e781ab3
and uses a genuine merge of teammate commit 5e1a9bf, preserving its authorship.
Do not replace main with the old teammate checkout. Main delivery uses a PR
and Create a merge commit, with actual publication/CI/merge state in Git/PR.

Scope: personal course board, per-owner program/cohort confirmation, versioned
grade policy, source-completeness collector and 20-credit adjustable plan.
Keep current student/admin auth, study_app_session, CSRF/origin, one-to-one
ownership, DB session checks, RAM VNU cookies/resume/reauth and seven-day reminder.
No public curriculum reference/CSV/talented catalog, RAG, what-if or persistent
semester-plan expansion. Auth.js/workspace/analytics/recommendation_service and
migration files remain identical to the main base.

Binding uses existing portal_users.profile JSONB with binding_schema_version=1.
Account/session/link checks and owner generation/digest/scope lock share one
transaction, with a safe audit event. Refresh preserves binding and last_synced_at;
changed enrollment invalidates binding, confirmation does not advance sync time.
No schema migration, seed, catalog publication, password/SMTP change or manual
upgrade of old completeness. Unknown source and uncertain outcomes remain gated.

Independent integration checks: 523 offline passed / 75 deselected including HUS
PDF acceptance; 75 PostgreSQL passed on disposable container port 55433 including
legacy, HUS/auth and four new binding transaction tests. Ruff, both catalog builder
checks, all JS syntax and diff checks pass. Fifteen synthetic Chrome regressions
pass; real HTTP + disposable-PG Chrome proves sign-in, program confirmation,
track/path selection and board plus existing admin/session/sync/logout checks.
Screenshots desktop/mobile inspected. Existing Starlette/httpx warning remains.
No agent real-VNU login or personal grades inspection; real-account acceptance
must be performed by the owner after deployment. Catalogs remain draft_unverified.

Final ownership audit adds checks of the original source owner after I/O, including
when an account's link changes while program metadata is being read. Two new
regressions pass; binding/system-auth/VNU PostgreSQL group rerun: 35 passed.

Runtime backup at ignored backups/vnu_eligibility_integration_20261026/
before_runtime.dump restored successfully to isolated ai07_backup_verify_20261026.
Ignored test reports/screenshots/clone remain under the same integration directory.
Do not reset seed or restore the full DB to resolve a UI/source-gating issue.
Deployment restart loses VNU RAM cookies; app sessions retain their normal DB
lifecycle and the next update may require one reauth. See docs/COURSE_STATUS_BOARD.md
and docs/VNU_PERSONAL_ACADEMIC_2026_10_25.md for scope/limits.

The preexisting candidate corpus whitespace edit remains outside this work.
Previous temporary Docker cleanup removed se_auth_mail/se_recommender_db containers
only; both database volumes remain. Keep test infrastructure separate from se_hus.

## Session close/publication authorized — 2026-10-25

User explicitly requests closing memory update, commits for the accumulated work
and push to GitHub. This supersedes preceding no-commit/push notes for the VNU
session/reminder/auth/UI/docs and cleanup change set. Publish on the existing
feature branch feat/system-auth-email-20261025, based on fetched main 586d659;
HEAD/main/origin/main were equal before publication. Plan two genuine commits:
integrated VNU/student/admin feature with tests, then docs/workflow/cleanup/memory.
Feature commit created as 211cd0d (73 files); docs close-out follows separately.
Preserve the existing configured author identity; no history rewriting or main
push. Open a draft PR for review; merge remains a separate action using a merge
commit after CI and authorization. Do not start new implementation at close-out.

One preexisting whitespace-only edit to the immutable candidate corpus document
ending exh01-02-06...0a180289.md is outside this feature publication. Keep it local
unchanged; do not normalize/publish source bytes as part of auth or cleanup.
Ignored .env/.env.auth/backups/private handoffs/toolkit/.venv stay outside commits.
Local admin username is admin; chosen password remains only a local DB credential,
never in tracked memory/source. Gmail SMTP and local account data remain untouched.

Latest verification remains 440 offline passed / 71 deselected (HUS PDF acceptance),
Ruff/diff checks, Chrome VNU/admin and UI/session regressions, HUS PostgreSQL 54
full-group passes followed by 31 auth/VNU passes after final ownership guard.
Cleanup changes only ignored artifacts plus documentation; no extra test rerun
or backend change is implied by committing. Live health/ready and 13 local assets
were OK. Source completeness/policy binding, real new-login acceptance, official
SSO, RAG and production rollout remain unverified/deferred as described below.

Use Git/PR records for resulting commit hashes, remote delivery and CI state;
this entry records authorization and pre-publication evidence, not a claim that
an unverified push/PR or CI already succeeded. Finish with publication handoff.

## Workspace/backups cleanup completed — 2026-10-25

User requests review of unnecessary files throughout the project, particularly
backups. Audited sizes, Git status and code/test/doc references; cleanup removes
generated/redundant local files, not academic sources or uncommitted application
work. Deleted 5,869 files / 1,049,153,955 bytes (~1001 MiB); backups reduced from
~1008 MiB to ~10 MiB (about 99%). Historical artifact paths below may now be gone.

Removed inactive semester Chrome profiles/cache, obsolete separate trial browser
dependencies, old Git-reproducible auth-review checkout/archive (495 files matched
586d659 with CRLF normalization), superseded screenshots/logs/synthetic fixtures,
exact duplicate crawl files/archive and Python/pytest/Ruff caches. Preserved all
9 database dumps, legacy rollback environment, original 5 PDFs, audit/OCR/CSV/JUnit
evidence, distinct crawl/config variants, .env/.env.auth, .venv, toolkit, Git and
all preceding dirty code/source changes. Original handoff accounts.private.txt
remains historical and is not current admin credentials; never reset seed.

Kept latest VNU/admin screenshots under system_auth_20261025/browser_4e62b1e236/
and active vnu_signin_20261025/runtime.* logs. One old synthetic credential (248
bytes) in browser_f8654fdd83 and other tiny ACL-protected test credentials retained
without altering ACL. Removal of that folder partially failed due to its ACL;
remaining old screenshots were separately removed. No auto-review rejection.
Precise ignored inventory/results: backups/cleanup_20261025/. Backup index:
backups/README.md. Git-visible report: docs/BAO_CAO_DON_DEP_2026_10_25.md.

Validation: hash comparison confirmed 530 protected project/config files unchanged
before this report/memory update. 440 offline passed / 71 deselected with HUS PDF
acceptance, bytecode/pytest caching disabled; Ruff --no-cache and diff check passed.
Live health/ready/anonymous session and all 13 HTML-linked local assets returned
200. Existing Starlette/httpx warning remains. No new PG tests needed: no runtime
code/schema/DB changes. No server restart, source publication, real VNU request,
grade inspection, password/SMTP changes, commit or push. Disk savings are local
workspace hygiene, not an API performance or full code-audit claim.

## Admin credentials changed by explicit user request — 2026-10-25

User explicitly requested local administrator username `admin` and a chosen
replacement password. Applied only to the existing verified active admin account
previously identified by admin@sohoctap.test: username/hash changed, initial-change
flag cleared for the user-chosen password, auth_version incremented and old admin
sessions revoked, maintenance audit recorded. Account UUID, email, role, seed flag,
other users and source data retained. No students FK referenced the old username.
Do not record the password in memory, tracked files or logs, and do not rerun seed.

Checked fresh ignored backup under backups/vnu_signin_20261025/admin_change_*/.
Live /auth/login using username admin and /admin/users permission check succeeded;
verification session logged out. Original accounts.private.txt remains a historical
temporary-password handoff and does not contain the current credentials. User can
now choose Quản trị viên and sign in as admin. No runtime restart, code change,
SMTP change, commit or push was needed.

## VNU student sign-in replaces personal email login — 2026-10-25

User explicitly authorizes the proposed implementation and frequent progress:
students sign in directly with VNU; administrators retain local account/password.
This supersedes the earlier separate-email student flow below. Work stays on
feat/system-auth-email-20261025 with all preceding unpublished changes retained;
no commit/push/PR requested or performed. This is the existing student-portal
connector, NOT official OAuth/SSO. Official integration/access to grades is unproven.

New POST /auth/vnu uses fresh accepted VNU login evidence, creates/reuses one
student account and a DB app session, saves source when accepted and installs
per-session RAM cookies. No personal-email registration or separate app password.
POST /auth/login accepts admin username/email only; public register/resend/verify
return 410 use_vnu_login. Admin password rotation and role/status guards remain.
VNU-only students cannot change local passwords or become admins without separate
eligible admin credentials. Admin list/search includes VNU-only student accounts.

Additive hus_20261025_06 adds accounts.vnu_subject and sessions.auth_method.
Backfills only existing student-owned VNU links, preserving account IDs and all
original account fields; old student sessions revoked. Unlinked email accounts
remain stored, never auto-associated by email/name. Stable VNU identity survives
source deletion and prevents another account from claiming the deleted source.
Concurrent first logins serialize; admin-owned links cannot become student logins.
Fresh student-portal auth/menu is the current admission boundary, not a new
university affiliation API or proof of every VNU account type.

After proven fresh authentication, source fetch/layout errors may return a
source_unavailable warning and still enter app with old/empty source; never
create fake snapshots or advance successful-sync time. Identity conflicts and
CAPTCHA/OTP fail closed. Unknown changed snapshots retain existing rollback guard.
Session/ownership/rate-limit/origin/CSRF/no-store, reminder and academic gates stay.
UI defaults to Sinh viên VNU with a separate Quản trị viên tab; student gets no
email/signup/local-password flow and no second connection form after successful
sign-in. This change does not unblock academic recommendations or activate RAG.

Validation: 440 offline passed / 71 deselected including HUS PDF acceptance;
whole-repo Ruff, JS syntax and diff checks passed. HUS PG full group 54 passed,
then 31 auth/VNU checks passed after final ownership guard. Chrome app+disposable
DB proof passed single sign-in/no second connection, session reload, admin login/
password/disable, sync/logout, VI/EN/mobile. Source/profile/workspace/charts/loading/
reminder/reauth/resume and session expiry/late logout response regressions passed.
Two old expiry assertions expected the admin form; updated to student form and
reran successfully. Existing Starlette/httpx deprecation warning remains.
No real VNU login, personal grades inspection or external email by agent.

Docker/PostgreSQL were stopped at task start; started Docker Desktop and existing
se_hus_db volume without reset. Backup/check archive and transaction preservation
proof at backups/vnu_signin_20261025/run_20261025T050450Z/. Applied 06 to local ai07;
aggregate checksums preserve all old account fields, links, source and catalogs;
only new auth fields and permitted student session revocation differ. No publish.
Gmail SMTP/.env.auth/passwords/seed handoff unchanged. Never rerun seed to reset.

App started on 127.0.0.1:8000: launcher PID 22352, child 21140 (verify command lines
before future stops); health/ready OK, anonymous /auth/session false. Runtime logs
ignored under backups/vnu_signin_20261025/. User should Ctrl+F5 and test VNU through
the UI; old student sessions intentionally require login. Real-account acceptance
is pending, not implied by synthetic checks. Read docs/VNU_SIGNIN_2026_10_25.md.

## Normal VNU reauth no longer returns HTTP 409 — 2026-10-25

User reports red console /me/portal-sync 409 after a successful VNU update.
Screenshot shows reauth 202, completed polling/profile 200 and a new successful
sync timestamp: the red request was the earlier expected missing/expired VNU
RAM state, not a failed update. API now returns HTTP 200
{"state":"reauth_required"} for that specific pre-job condition, while accepted
jobs remain 202. UI opens the existing explicit password-only reauth form as a
normal step, starts no job/poll and does not advance last_synced_at before an
actual successful job. Worker-detected expiry still arrives via job status and
uses the same form. Genuine session/auth/ownership/technical errors retain their
error responses; do not blanket-convert failures to 200 or suppress the console.

Validation: 435 offline passed / 61 deselected; two targeted disposable-PG
checks passed (RAM loss/reauth and unique ownership/delete); Chrome reauth test
asserts no new console error or failed sync HTTP response on expected expiry,
no spurious polling/profile read, successful reauth and logout race protection.
Reminder/VI/EN/themes/mobile, Ruff, JS syntax and diff checks passed. Gmail SMTP,
approved ownership repair, passwords and stored source data were not changed.

Restarted app to load API changes, /ready OK and live JS verified. Current
launcher PID 14056, child 23668; verify before stopping. Logs ignored under
backups/system_auth_20261025/runtime_reauth_state.*. User should Ctrl+F5 to load
new UI/clear prior console history; restarting discards provider RAM, so the
next update may need one explicit VNU verification. No real portal login by agent.

## Approved VNU seed-link repair completed — 2026-10-25

User reports /me/portal-connection 409 after signing in as the now email-verified
real Gmail account. Read-only metadata confirms VNU 23001953 is already linked
to the development seed student@sohoctap.test; real account has no link. This
is the intended one-to-one ownership guard, not a bad-password/worker failure.
Do not relax that guard or expose another real user's account in public errors.

Prepared ignored repair: backups/system_auth_20261025/
relink_vnu_seed_to_verified_account.py. Exact old/target UUIDs are pinned in the
script; local ai07 only, eligibility checks, account/owner locks, transfer one
link, increment generation, revoke old seed sessions and audit; source/profile
checksum must remain unchanged. Dry-run passed, preserves one snapshot, no DB
changes made. Fresh ignored backup before_vnu_relink.dump (214546 bytes) created.
User explicitly replied "đồng ý" to the concrete ownership transfer. Applied
the prepared script with --apply. Link now belongs to the requested verified
Gmail account; old student seed has no VNU link or unrevoked app sessions.
Transactional checksum verified the one existing source snapshot and profile
were preserved. Owner generation incremented and two maintenance audit events
recorded. This is a specifically approved local repair, not a general automatic
transfer policy or an authorization to weaken ownership checks.

Restarted the identified app to discard old VNU RAM/jobs; /ready OK. Current
launcher PID 26764, child 26696; verify command lines before future stops.
Gmail SMTP/secret/passwords unchanged. User should refresh the profile page;
the next sync may need explicit VNU reauth because restart cleared provider RAM.
No real VNU login or reading personal grade values was performed by the agent.

## Gmail SMTP configured by user — 2026-10-25

User requests actual inbox delivery, creates a Google app password privately in
ignored .env.auth and explicitly asks the agent to complete that configuration.
Updated only SMTP fields to smtp.gmail.com:587/starttls, matching username/from;
normalized the user's existing app password by removing grouping whitespace.
Never print or copy its value into Git/logs/chat. AUTH_TOKEN_PEPPER and other
settings preserved. TLS SMTP authentication succeeded; no email was sent by
that credential check. User should use the app resend button to verify delivery.
Runtime now uses Gmail SMTP, superseding Mailpit as the live local mail target.
Do not switch it back to Mailpit during later tests; use isolated test overrides.

Cleared only resend:account rate bucket for the active pending sender/email
used in the user's earlier Mailpit test; all other rate limits retained. No
verification flags, passwords, tokens or source records changed. Restarted app,
/ready OK: launcher PID 26912, child 26844; verify command lines before stopping.
Gmail sending/inbox acceptance still awaits user's resend; SMTP login alone is
not end-to-end delivery proof. Mailpit remains available for isolated tests.

## Password minimum changed by user — 2026-10-25

User explicitly requests minimum password length 6 instead of 15. System
password validator, register/change/cross-device verification HTML constraints,
VI/EN hints/errors and current docs now use 6–128 characters. Existing password
hashes/seed credentials remain intact; no password reset or migration involved.
Boundary API test passed: 5 rejected / 6 accepted for registration, cross-device
verification and password change. Chrome/SMTP proof passed using a six-character
synthetic password; Ruff, JS syntax and diff checks passed. Restarted local app:
launcher PID 28492, child 27300; /ready 200 and live form minlength=6 confirmed.
These PIDs supersede the older runtime checkpoint below; verify before stopping.

## Separate system accounts implemented locally — 2026-10-25

User authorized implementation of the detailed system-auth plan, superseding
the planning-only checkpoint below. Work is on
`feat/system-auth-email-20261025`, retaining the preceding unpublished VNU
session/reminder work. No commit, push or PR authorized; future main changes
still require a feature branch, PR and merge commit preserving real authors.

Implemented email/password register, pending verification, one-use 30-minute
email tokens with same-browser registration proof / cross-device password
replacement, resend/rate limits in DB, Argon2id, persistent opaque app sessions,
2-hour idle / 12-hour absolute expiry, CSRF/origin/no-store, forced initial
password change, account/role/status guards and safe audit metadata. Session
family survives password rotation so simultaneous logout invalidates replacement.
Account-before-session locking and serialized admin updates are concurrency-tested.

System login is separate from VNU: retired POST /auth/portal returns 410;
/me/portal-connection requires verified local account. Unique account/VNU owner
claim needs fresh successful VNU evidence, including old unclaimed owners; never
assign legacy grades to seed users or by email/name. Provider cookies remain
per-app-session RAM only. DB session/account/link/generation rechecked before
source reads/writes and after workers. Disconnect/delete VNU preserves app account;
logout/password/role/disable revokes relevant VNU RAM and late work. Admin manages
accounts without default access to another user's grades. Legacy /profiles routes
are closed with 410; retained academic POST calculators require verified account
and CSRF. Domain tests remain; active UI still VNU-only, seven-day reminders kept.

Actual ai07 backup: ignored backups/system_auth_20261025/before_auth.dump.
Applied additive hus_20261025_04 and hus_20261025_05, runtime HEAD now 05.
Restored the pre-auth backup to a disposable DB and compared count/checksum of
all 17 original non-version tables (old accounts projected to original columns,
excluding new seeds): unchanged, including catalogs and source snapshots.
No catalog publication, invented student rows or source-owner reassignment.

Exactly two local bootstrap-verified DB accounts created with random temporary
passwords: admin@sohoctap.test/admin and student@sohoctap.test/student. Both start
must_change_password=true and seeded_for_dev=true, no VNU link. Private handoff:
backups/system_auth_20261025/accounts.private.txt, ignored, user-only file ACL;
never print its contents. Seed idempotent/no reset, rejects collisions and production.
Later user testing may change password/flags; do not reset them or regenerate handoff.

Ignored .env.auth configured for local SMTP and generated server secret; keep it.
Versioned .env.auth.example has placeholders only. Mailpit se_auth_mail is bound
to loopback 1025/8025; inbox http://127.0.0.1:8025/. Actual browser+SMTP proof used
disposable DB and synthetic .test accounts, not outside inboxes. Real SMTP/domain/
HTTPS/proxy and production deployment remain gates; production rejects active dev
seeds, fake/insecure SMTP and HTTP at startup/readiness. No password recovery or
weekly automatic crawl added. Multiple processes still need a VNU-state design.

Validation: 434 offline passed / 57 deselected before three additional PG-only
checks; 41 HUS PostgreSQL passed plus 3 additional concurrent/production checks
passed (44 total exercised). Chrome/SMTP, source UI, workspace/charts, loading,
session expiry/logout races, reminders, reauth/resume, identity/profile source,
VI/EN/themes/mobile passed. Existing Starlette/httpx deprecation warning remains.
Profile-source browser test exposed Playwright HTTP-redirect mock escape: an
anonymous source-page GET could leave the fixture; no real credentials were
submitted and no personal grades were read. It now uses networking-off contexts
and explicit fixture navigation, and passes. Do not claim an intercepted 302 proof.
No real VNU login for the new local-account link was performed by the agent;
previous user-reported VNU update acceptance applies to the earlier session flow.

Runtime restarted on 127.0.0.1:8000, /ready 200 with postgres and public
/auth/session returns authenticated:false without a cookie. Launcher PID 26284,
child 17420; verify command line before future stops. Ignored runtime logs and
synthetic screenshots under backups/system_auth_20261025/. User may now test;
do not silently change seeded roles/passwords during follow-up validation.

Implementation/runbook: docs/HUONG_DAN_TAI_KHOAN_HE_THONG.md and module 12.

## Separate system accounts architecture plan — 2026-10-25

User requests a detailed PLAN for Sổ học tập accounts: register, verify email,
login/logout, admin/ordinary user roles, and two seeded local DB accounts when
implemented. VNU becomes a data connection after system authentication. This
supersedes historical no-separate-local-password scope for the planned module;
VNU passwords/cookies still must not be persisted. Current turn is planning-only.

Plan: docs/KE_HOACH_TAI_KHOAN_HE_THONG_2026_10_25.md, new module 12. Proposes
extending existing accounts with UUID/email/verification and reusing student/admin
roles, DB-backed app sessions, explicit unique account-to-portal links and verified
claim of old VNU owners. No automatic assignment to seed users or based on email.
Mailpit local / configurable real SMTP, bounded single-use verification, explicit
bootstrap exceptions only for two local test users. No actual accounts, email,
DB migration, runtime/auth cutover, restart, commit or push in this planning turn.
Mail delivery/provider and production domain are future configuration gates, not
an excuse to skip verification. Preserve all existing unpublished session/reminder
work. Weekly automatic VNU sync remains deferred.

## VNU session reuse implemented locally — 2026-10-25

User explicitly requests implementation of the session-reuse plan and frequent
updates, superseding the planning-only checkpoint below for this task. No commit,
push or PR authorized. Work remains on fix/portal-session-diagnostics-20261025.

Implemented bounded, host-scoped cookie contract (64 cookies/64 KiB, stdin 72 KiB),
worker login/resume with fresh Chrome/context per job, private per-web-session
RAM state, versioned rotation and TTL, 30-second cleanup, logout/current-session
and delete/all-owner revocation, no password/cookie persistence. Existing fresh
login evidence remains required; resume state originates only from the server
session and conflicting source identity fails closed. API sync accepts no
credentials; explicit /me/portal-reauth accepts password only, subject from session.
UI sync runs immediately; only vnu_reauth_required opens a separate reauth form.
Technical failure does not force reauth. Seven-day reminder/source gates remain.

Automated Chrome proof: one synthetic password POST, two new-browser resumes,
cookie rotation, identity conflict, expired source and CAPTCHA. UI regressions
pass profile/VNU-only/workspace/charts/session/reminder/reauth, VI/EN/themes/mobile
and stale responses. Synthetic mobile screenshot inspected. No real portal
request or personal-record inspection by the agent. User subsequently confirms
"Cập nhật được, không hỏi lại mật khẩu" after the requested UI test. This is
user-reported real happy-path acceptance, not independent completeness or all-account
verification. Single-process RAM sessions only; restart
loses them. No new migration, catalog publication, .env edit or scheduled crawl.

Final offline verification: 434 passed / 40 deselected with explicit HUS PDF
acceptance root, whole-repo Ruff, JS syntax and diff checks passed; existing
Starlette/httpx warning. No new PostgreSQL run was needed for session-only changes.

Restarted the identified local Uvicorn; launcher PID 21908, health/ready 200 on
127.0.0.1:8000 with PostgreSQL. Logs/screenshots ignored in
backups/portal_reuse_20261025/. User confirmed the requested login/update flow.
The scoped local implementation and happy-path acceptance are complete; do not
claim full portal delivery, completeness acceptance or production readiness.
This acceptance update changes documentation only, with no new tests/restart.

## VNU session reuse plan — 2026-10-25

User requests a PLAN for updating grades within the app session without entering
the VNU password again. See docs/KE_HOACH_GIU_PHIEN_VNU_2026_10_25.md and module 09.
This request is planning-only: no runtime implementation, restart, credential
collection, live portal request, commit or push in this turn.

Design: VNU cookies in RAM scoped to each authenticated web session, short-lived
workers restoring an isolated context, explicit reauthentication only when VNU
requires it, TTL/rotation/logout/delete/expiry cleanup. Cookie-only restoration
on real VNU is NOT proven; retain a validation gate and never weaken identity.
The planned lifetime supersedes job-only cookie disposal only upon implementation;
it does not authorize password persistence or durable cookie storage. Weekly
automatic sync remains deferred; current button/seven-day reminder stay in scope.

## Portal update reminders — 2026-10-25

User targets a real multi-student server app, but explicitly defers automatic
weekly VNU sync until the system is nearly complete. Current scope is an explicit
“Cập nhật bảng điểm” button and an in-app reminder after seven days. No scheduled
crawl, email/push, password persistence or background reauthentication is added.
The global workspace bar replaces the curriculum warning on Dashboard/profile;
the draft-catalog warning remains on eligibility/recommendation pages.

Successful accepted sync stores server-owned `_last_synced_at` in existing
portal_users.profile JSONB, exposed separately as last_synced_at. Identical
current-snapshot reads refresh it; failed/rejected sync does not. Snapshot
payload/digest/fetched_at remain unchanged. Legacy profiles fall back to fetched_at.
Changes remain local on fix/portal-session-diagnostics-20261025, together with
the preceding session-status/502-diagnostics work; no commit/push authorized.

## Session close — 2026-10-23: team history preserved, temporary branches removed

User requests memory update and a permanent PR rule to keep each member's
original commits visible on main. This close-out changes documentation only;
do not start new implementation or publish these edits without a new request.

Latest verified main/origin/main is 8f77ce3, with no ahead/behind difference and
a clean working tree before this memory update. Login PR #2 merged as c73d08f;
crawler PR #3 merged as 8f77ce3, both using GitHub merge commits after all six
PR CI checks passed. Original added history: 33 commits under 23172c43 (login),
43 under Thang and 10 under Duong Van Tai (crawler), including merge commits.
Database setup/tests and Vinh branch tips were already ancestors of main.
All four fetched source tips were verified ancestors of final main, with zero
remaining commits in main..source. Original author/hash metadata is retained.

These were explicitly history-only ours merges; only contribution docs and
memory changed from 0b4b2fc. They did not adopt every source-branch feature.
Later login timestamp/schema changes, crawler activation and RAG/corpus serving
remain deferred. Future functional adoption needs explicit reapplication/review
because Git now regards these historical source tips as merged. Do not treat
this special reconciliation as the normal feature integration workflow.

User authorized deletion of ONLY integration/login-history-20261023 and
integration/crawler-history-20261023. First attempt did not execute because
automatic approval review hit a usage limit. On retry, both remote branches
were already absent; after ancestry verification, removed the two local branches
and pruned stale remote-tracking refs. Fetch also reported codebase,
feat/catalog-validation and fix/hus-metadata-vi-en-20261021 already deleted
remotely; this agent did not delete those remote branches. Keep teammates'
remaining branches. Deleting merged branch names does not remove main's commits
or the merged PR records.

Validation from the history work: 398 offline passed / 39 deselected, whole-repo
Ruff and diff checks passed; existing Starlette/httpx warning. No tests rerun
for branch cleanup or this documentation-only close-out. No portal access,
real-data inspection, DB migration, restart or crawler run. Main-branch CI
after final merge was not separately rechecked; six-check evidence is per PR.

## Permanent workflow — PRs and original team commits on main

- All future updates to main, including docs/memory, go through a feature branch
  and GitHub PR. Never push changes directly to main. Prior one-off direct-push
  authorizations are historical, not a standing exception to this rule.
- For new work, branch from current main. To integrate an existing teammate
  branch, preserve its genuine commit ancestry in the PR branch and resolve
  conflicts there. Do not silently replace original commits with an integrator's
  copy/import commit. Check which original commits are already in main first.
- Merge PRs using Create a merge commit (API merge_method=merge). Do not use
  Squash and merge or Rebase and merge, and do not rewrite/force-push main.
  Preserve original author identities and hashes; never manufacture commits,
  change authors to boost counts, or add fictitious co-author credit.
- Describe actual functionality, conflicts, deferred changes and verification
  in the PR. Run relevant checks and wait for required CI before merging. A
  history-only reconciliation requires explicit authorization and disclosure;
  never substitute it for requested functional integration.
- Verify source-tip ancestry and original commits in the resulting main after
  merge. GitHub attribution also depends on each original author email being
  linked to that member's GitHub account; commit history is not a grading promise.
- Existing publication rules still apply: do not commit/push/create or merge PRs
  without user authorization for that task. If only local edits are requested,
  leave them local and report their unpublished state. If publication is
  authorized, carry it out through this PR workflow.
- Delete temporary merged branches only when authorized; preserve branches
  teammates still use. This is a contributor rule, not a claim that GitHub branch
  protection/settings have been configured. Change hosting settings only when
  separately requested. Exceptions require an explicit new user instruction.

## Team history reconciliation — 2026-10-23

User explicitly authorizes PRs, merges and publication to main to preserve
teammates' original database, test, crawler and login commit histories. This
supersedes the previous close-out stop for this history task only. Starting
main is 0b4b2fc. Database setup/tests and Vinh branch tips are already ancestors.
Login fetched tip b3964ce has 33 missing commits; crawler tip 3a45aae has 53.
Use explicit history-only ours merges and GitHub merge commits, preserving the
current application tree and original author/hash metadata. PRs must state this
scope; do not claim new source-branch features are functionally integrated.
No new database migration, crawler activation, corpus publication, portal access
or real data inspection. See docs/TEAM_CONTRIBUTIONS_2026_10_23.md. Functional
changes skipped by the history merge need explicit review/reapplication later.
Login history PR #2: https://github.com/5-Bit-System/SE_Project/pull/2.
Crawler history PR #3: https://github.com/5-Bit-System/SE_Project/pull/3.
PR #2 merged as c73d08f after all six GitHub checks passed. Use the PR records
for final publication/CI state; crawler PR retains the original 53 commits.
Local verification: 398 offline passed / 39 deselected, whole-repo Ruff passed,
existing Starlette/httpx warning only. All runtime/source/dependency/CI files
are unchanged from 0b4b2fc; only memory/contribution documentation changes.

## Session close and main publication — 2026-10-23

User requests memory update, session close, commit and push all current project
work to main. This supersedes older no-commit/push notes for this change set.
Publication starts at main/origin/main 3129f7c (fetch verified 0/0 ahead/behind);
use Git to verify resulting commit/push. Do not begin new implementation, restart,
access VNU or inspect real DB data in this close-out. Credentials/.env/backups/
screenshots/toolkit stay ignored. Prospective changed/new files are text code,
tests/docs; token/contact-pattern scan found only commit-hash digit substrings.

User-provided local screenshots now show all name/program/cohort fields after
the source fixes. This confirms display, not independent completeness/policy
acceptance. Connector reads Hồ sơ sinh viên for name and Cập nhật hồ sơ sinh viên
for selected Lớp quản lý text, split as user-confirmed [numeric cohort] [program].
Never submit that VNU form or retain screenshot personal values in artifacts.

Active frontend has no manual grades/upload/demo/term entry or manual Dashboard
KPIs. No program picker/default catalog: sidebar program/cohort and top-strip
program come from saved VNU display fields. Duplicate header profile button is
removed. Language now uses VIE/EN buttons matching appearance control, with
pressed state, keyboard activation and preference restoration. Old language
select removed; active modules use workspace:language-change. Known credit/GPA
summary labels localize; source numeric values, names and snapshots stay intact.
Personal source UI clears on logout/expiry/delete; stale responses are ignored.

Staged authenticated AcademicContext backend exists, but cutover is partial:
unknown completeness, no reviewed program/policy binding, empty production policy
registry, incomplete what-if baseline/results UI. Rules/recommend screens wait;
old manual advisor/results flow is not loaded. Legacy public input APIs and
dormant app.js/dashboard.js remain for future retirement/reference. Do not claim
full academic integration or unblock it from display strings. Preserve changed-
unknown snapshot protection. RAG remains inactive; preserve retained source.

Final checks: 398 offline passed / 39 deselected with explicit HUS acceptance
root, whole-repo Ruff passed, one existing Starlette/httpx warning. Latest Chrome
VNU-only/profile/workspace/charts checks pass after VIE/EN changes, including
keyboard/reload persistence, VI/EN summary, source labels, themes/mobile/logout
races. JS syntax/diff checks pass; synthetic mobile screenshots inspected. No
new PostgreSQL run in close-out; earlier migration/store evidence is historical.
Migration hus_20261023_03 was already applied locally with backup; publishing
code does not apply it elsewhere or publish catalog changes. No real-data or
source-catalog changes in this close-out. Stop after publication handoff.

## Source-summary UI labels — 2026-10-23

User reports English UI still displays Vietnamese total-credit/GPA labels.
Added shared workspaceI18n.formatSourceSummary, used by Dashboard and profile.
Translates only allowlisted summary labels at the start of each cell (credits,
accumulated credits, cumulative/semester averages on source 4/10-point scales).
Numeric text/decimal separators, unknown labels, row arrays and persisted
snapshots remain unchanged; switching back to VI renders original labels.
Program/course names and personal source values remain untranslated. This is
the requested label localization exception to historical raw-summary UI text.
Chrome charts/profile regressions cover English labels, comma decimals,
multi-cell labels/values, unknown-text preservation and VI restoration; passed.
Ruff/JS syntax/diff checks passed; frontend only, no DB/portal/restart/commit/push.
Also removed duplicate header profile button per user's preceding request;
sidebar profile navigation remains, Chrome login/profile checks passed.

## Source-owned sidebar — 2026-10-23: program selector removed

User supplied local profile screenshot showing name/program/cohort now populated;
this is user-provided display acceptance, not independent source completeness or
policy acceptance. Do not retain the personal values in artifacts. User requested
removal of the four-program selector in favor of the VNU profile's program.

Removed sidebar selector and /programs fetch/default-first-program behavior.
Sidebar now shows read-only program/cohort from the authenticated saved profile;
top strip shows source program. Missing values show unavailable; signed-out
values show not signed in. Portal event carries only program/cohort display
fields in addition to existing snapshot/time, no new name/identifier/credentials.
Source strings are textContent and excluded from UI translation. Logout/expiry/
delete clears both sidebar/top strip; delayed profile responses cannot restore.

No source-name-to-catalog guess or academic binding was added. Without a reviewed
server binding, active UI no longer requests academic-context with an arbitrary
selected program: academic panels state pending conversion/binding and source
completeness from the saved snapshot. This supersedes the preceding UI checkpoint
about a reference dropdown and fetching context with its selected program.
Backend academic APIs are unchanged and remain gated.

Chrome check_vnu_only/check_workspace/check_charts/check_portal passed, including
source labels, missing-value cleanup, VI/EN, logout/delayed response, themes/mobile,
no /programs or guessed-context requests. Synthetic mobile screenshot inspected.
Ruff/JS syntax/diff checks passed. Frontend only: no new Python backend/DB tests,
portal access, real-data edits, restart, commit or push. Reload browser to load UI.

## VNU-only active UI — 2026-10-23: manual entry removed, academic tools gated

User explicitly challenged the remaining Nhập điểm screen, referring to the
agreed VNU-only direction. Removed manual tab, file preview, term/course/grade
controls, manual Dashboard KPIs/plan and all entry links from active index.html.
Old #transcript redirects to #profile. New workspace.js replaces loaded app.js
and dashboard.js; these legacy sources remain dormant for reference/rollback.
No hidden manual form or empty completed set is used by the active frontend.
Dashboard source charts and profile/login/sync/delete remain active. Sidebar
program selection is labelled reference only, not a verified account binding.

Rules/recommendation screens now fetch /me/academic-context using session and
program selection, display sign-in/readiness blockers, and do not run the old
manual eligibility/recommendation/what-if/advisor flow. Legacy advisor UI was
removed with that flow. Personal academic tools await completion of VNU
context readiness and frontend results implementation; do not claim full
cutover. Legacy public input APIs/backend/domain tests are retained, not removed
or secured by this UI-only change; backend retirement remains in the plan.
The earlier requirement to retain manual UI until replacement is superseded
for this UI removal request; safety gates remain and academic output is paused.

Chrome check_vnu_only.py passes old URL redirect, no manual DOM/legacy scripts
or personal-input requests, session-backed readiness, logout vs delayed-context
race, VI/EN/themes/mobile. Updated check_workspace.py/check_charts.py for removed
manual state and intercepted academic context; both pass, as does check_portal.py.
Initial chart run failed because its newly required context fixture was absent;
mocking that personal endpoint resolved it. Screenshots synthetic; mobile
inspected. Ruff, JS syntax and diff checks pass. No backend/DB/schema/.env edits,
runtime restart, live portal access, real data manipulation, commit or push.
Previous 398 offline tests are prior backend evidence, not a new UI-task rerun.

## Management-class source — 2026-10-23: name accepted, cohort/program retry pending

User confirms the prior fix now displays the student's name. New ORIGINAL VNU
screenshot locates enrollment details in Cập nhật hồ sơ sinh viên. User explicitly
defines the selected Lớp quản lý text as [numeric cohort] [program name]; use
that split for display, not the separate Khóa selector. Do not retain screenshot
personal values in code/tests/docs. This is display semantics, not academic
policy/program applicability approval.

Client now clicks that existing exact-label menu after preserving name/identity
texts, waits for Lớp quản lý, reads only its adjacent cell/selected option TEXT
(including disabled selects), and never fills/submits the update form. No guessed
module IDs/URLs. Parser splits a single unambiguous numeric prefix and program;
empty/malformed/conflicting class values remain unknown. Selected management
class is authoritative for these two display fields. Store/schema/digest and
changed-unknown rollback protection unchanged. Frontend renders the resulting
fields normally; VI/EN update button now includes both profile and transcript.

Validation: 398 offline passed / 39 deselected with explicit HUS acceptance root,
existing Starlette/httpx warning; Chrome source and profile UI fixtures passed
delayed module/frame navigation, disabled select with other unselected options,
name retention, source transcript, fields/VI-EN/mobile/logout. Ruff/JS syntax
passed. Synthetic mobile screenshot inspected. No live login/real-data read,
PostgreSQL rerun, schema/.env edits, restart, commit or push. Fresh worker on
next login/sync loads the fix; need user confirmation for actual cohort/program.

## Profile module/cell collection fix — 2026-10-23: live confirmation pending

User resumed the missing name/program/cohort bug and supplied a screenshot of
the ORIGINAL authenticated VNU profile page. It shows the exact navigation
label Hồ sơ sinh viên and a multi-column label/value table (including Họ và tên).
Program/cohort labels are not visible in the supplied region; do not guess them.
Do not copy any personal values from either screenshot into code/docs/tests.

Found two concrete code gaps: read_profile_texts only captured the default.asp
shell without invoking the student-profile menu; the text parser rejects rows
with multiple label/value pairs. Client now invokes the existing exact-label
profile menu handler, waits for a labelled name in the loaded page/frame, and
extracts allowlisted adjacent table cells into separate labelled lines. Visible
text inputs/selected option text are supported; hidden/nested/ambiguous cells
and family-name labels are excluded. No guessed module ID/URL or academic binding.
Existing landing-page support and source identity checks remain. Store and
snapshot/completeness/rollback behavior unchanged; no DB/schema changes.

Chrome intercepted synthetic regression passed module navigation, delayed
iframe, multi-column rows, controls, missing labels, hidden/family fields,
identity evidence and retained transcript. Auth Chrome regression and Ruff
passed. Full offline suite: 390 passed / 39 deselected, explicit HUS acceptance
root, existing Starlette/httpx warning. Health/ready both 200; no restart needed
because each sync/login spawns a fresh worker. No live portal login, personal
data inspection, PostgreSQL rerun, commit or push. User must try Update transcript
with the changed worker before calling the real-account issue resolved. If only
name appears, need source evidence for the actual program/cohort labels/layout.
This supersedes the older statement that no original-source screenshot exists;
it does not establish live field acceptance or snapshot completeness.

## Session close — 2026-10-23: VNU profile details STILL UNRESOLVED

User explicitly requests memory/status update and session close. Stop implementation
after this documentation handoff; no further restart, portal login or retry in
this close-out. Keep all local changes; no commit/push requested.

Latest user acceptance: login succeeds and saved source transcript displays,
but Họ và tên / Ngành học / Khóa học STILL show unavailable. User explicitly
confirmed they already logged in again after the fixes, not merely pressed F5.
Their screenshot is the local /#profile UI, not the authenticated VNU source.
Do not copy identifier, grades or source totals from that screenshot into docs,
tests or memory. Do not tell them the cause is just refresh/cache or an old
login, or keep asking for the same retry without new diagnostic evidence.

A minimal read-only aggregate database check confirmed no non-null name,
program or cohort values are stored. It printed no identifiers or individual
grades. Thus the gap is in source collection/parsing/persistence, not solely
frontend rendering; exact cause is NOT yet proven. No F12 errors is consistent
with a successful profile response containing missing fields, not proof of a
successful source extraction. Inspect possible save rejection/rollback as well
as parser/source layout before attributing the gap to one stage.

Previous code changes (dynamic UI fields, source_profile parser, transactional
metadata save, early default.asp capture) are implemented and synthetic tests
pass, but DID NOT resolve this real-account issue. The authenticated layout,
labels, frame/form controls and loading behavior at default.asp have not been
observed independently. Public access redirects to login. Last request to user
was a screenshot of the VNU source region with values redacted but labels/layout
visible; none supplied yet. Do not mistake their local app screenshot for it.

Resume with source-layout evidence or authorized minimal in-session diagnostics;
trace collection -> parser -> save/rollback -> API -> UI without logging personal
values, raw DOM, cookies or credentials. Do not add more speculative label rules,
infer name/program/cohort, or mark metadata/binding/completeness verified. Keep
existing transcript and changed-unknown snapshot protection intact. Display
metadata must not become a reviewed academic program/policy binding.

Historical checks: 390 offline passed / 39 deselected, 4 disposable PostgreSQL
portal tests, Chrome fixture checks; later landing-page change had its own Chrome
check and 17 focused tests. These are synthetic/code evidence, NOT real profile
field acceptance. Overall ~90% was an implementation estimate only; portal
delivery and this bug remain incomplete. Latest known server localhost:8000,
PID 28848 after verified restart; not rechecked at session close. Earlier auth/
completeness/alias/update/delete acceptance gates remain. Close-out changes are
documentation-only; no new app/DB regression claimed.

Handoff: docs/PORTAL_INTEGRATION_STATUS_2026_10_23.md (latest unresolved section),
docs/KE_HOACH_TICH_HOP_PORTAL_BANG_DIEM_2026_10_23.md and module 09 updated.

## VNU landing-page profile capture — 2026-10-23

User identifies https://daotao.vnu.edu.vn/dkmh/default.asp as location of profile
details. Public read redirects to login; authenticated structure is still not
independently observed. Found worker only captured body text AFTER open_transcript,
which can replace landing-page content. Added DaotaoClient.read_profile_texts:
read fixed authenticated default.asp after fresh login, before transcript click;
avoid reloading if already at exact URL. Combined early/later texts participate
in existing identity-conflict checks and source_profile parsing. No extra
URLs from client, no guesses about profile labels/academic binding, no raw text
logging or artifacts. Missing fields still unknown.

Chrome synthetic test tests/frontend/check_portal_profile_source.py passed both
login redirect and explicit default.asp navigation, profile removed by transcript
click, early source retention and preserved transcript reads. 17 focused worker/
snapshot tests and Ruff passed. No DB/schema/store change in this follow-up.
Worker launches fresh per login/sync, so new worker/client code applies on next
connection without restarting web server or revoking current session. Need user
retry Update transcript and, if still missing, redacted layout evidence; do not
claim real profile fields fixed based solely on fixtures. No commit/push.

## Profile display fields checkpoint — 2026-10-23

User reports successful login and visible real transcript, but name/program/
cohort all unavailable. This is user-reported live login/display evidence,
not independent completeness/update/delete acceptance. Found UI hardcoded all
three values as unavailable; worker did not collect them and store never wrote
portal_users.profile. Fixed rendering of source profile fields, cleared on
logout/expiry, preserved source text across VI/EN. Added source_profile parser
for exact labels with colon/tab and value on same line in existing authenticated
page/frame body inner_text; missing/ambiguous/conflicting values stay null.
No additional portal navigation or guessing from student ID, years or major.
This limited parser is not proof real portal supplies those labels there.
Asked user where these fields appear in VNU; answer pending at checkpoint.

Worker sends profile separately from immutable transcript; store.save writes
allowlisted name/program/cohort under owner lock in the same transaction,
including identical digest refresh. An incomplete changed transcript rolls back
metadata as well. Transcript digest/rows/completeness and academic bindings
unchanged. Existing JSONB column used; no migration/.env/catalog changes.
Source program/cohort strings are display-only, never reviewed policy bindings.

Validation: 390 offline passed / 39 deselected with explicit HUS PDF root;
4 portal PostgreSQL tests passed on disposable per-test databases, cleaned by
fixture, including metadata ownership/update/idempotency/rollback. Chrome
profile fixture regression passed rendering, VI/EN fallback and logout cleanup.
Ruff/JS syntax/diff checks passed; existing Starlette/httpx warning remains.

Correction to previous startup note: the attempted server launch had failed
with port already occupied; previous health checks reached existing Uvicorn.
Verified port PID 31036 command line is project Uvicorn and restarted this
specific process to load current backend. New server PID in log 28848, hidden,
access log disabled. Health/ready 200 and current HTML verified. Session needs
fresh login; persisted snapshots retained. Logs ignored under
backups/portal_resume_20261023/profile-server.*. No real portal request by agent,
real-data inspection, commit or push. Need user retry and source layout evidence
before claiming real profile fields resolved. Portal plan remains ~90%.

## Login continuation checkpoint — 2026-10-23

User explicitly resumed the portal/login plan, requested frequent progress,
and agreed to test credentials directly in localhost UI (never in chat).
This supersedes deferral of login work; academic policy/program/DB cutover
remains separate. No schema, .env, catalog, real data, commit or push changes.

Added session recheck after profile storage read and before sync save; expired
or revoked session does not return profile/start a save. Existing committing
transaction still finishes with its actual result. Logout revokes first and
clears even an expired/missing cookie, with origin checks unchanged. UI clears
personal state immediately on logout; epoch/sequence guards reject stale reads.
Explicit visible captcha/OTP controls return interaction_required (409), with
VI/EN text and no attempted bypass; hidden controls ignored. Recognition is
limited to tested selectors, not universal challenge detection or interaction.
Playwright timeouts map to timeout; malformed credential JSON/encoding is 400.

New verification: 386 offline passed / 38 deselected with HUS PDF acceptance
root; existing Starlette/httpx warning. Chrome synthetic portal auth, profile,
workspace and charts checks passed, including delayed response after logout,
expiry/relogin and challenge text. Ruff, JS syntax/diff checks passed. Dark
mobile fixture screenshot inspected. No new PostgreSQL tests (no store/schema
changes), real portal requests or real records in test artifacts.

No listener was present at 8000; started project Uvicorn hidden with access log
disabled. Health/ready returned 200. Ignored logs backups/portal_resume_20261023/.
User was invited to Ctrl+F5 and test /#profile; result still pending at this
checkpoint. Portal plan remains ~90%, completeness unknown, changed unknown
snapshots remain blocked, alias mapping unverified. Do not claim full live
acceptance. See docs/PORTAL_INTEGRATION_STATUS_2026_10_23.md for exact scope.

## Implementation checkpoint - 2026-10-23: staged VNU academic context (~30%)

User authorized the existing cutover plan with project-toolkit, superseding
the previous planning-only restriction. Then clarified program/cohort unknown
and login/database work should be done later. Keep those deferred: no auth flow,
schema, real data or .env changes in this implementation. Do not ask again for
program/cohort now or infer them from an identifier. No server restart/portal
access/commit/push. Existing dirty portal/frontend changes preserved.

Added app/academic_context.py: pure source-owned context, explicit reviewed
binding/policy, fail-closed readiness, exact code matching, raw row references,
retakes/unknown outcomes unresolved, no GPA conversion or legacy transcript
defaults. Source/schema/empty/unknown/duplicate rows and conflicting grades are
gated. No real policy registered; synthetic policies exist only in tests.

Added app/api/academic.py and router registration: /me/academic-context,
/me/eligibility, /me/academic-progress, /me/recommendations, /me/advisor/chat.
Owner comes only from existing session, snapshots from existing store.profile.
Reject browser owner/records/passed sets. Revision includes owner, session,
source, catalog content, binding, policy and selections. Slow recommendation/
advisor responses recheck source/revision/session before returning. Existing
origin/no-store middleware applies. /me/recommendations/what-if is only a staged
readiness/baseline guard; a ready context returns academic_baseline_not_available.
Server-owned baseline comparison NOT implemented yet.

Live readiness remains blocked: connector completeness=unknown, actual program/
policy binding unavailable, policy registry empty. Staged catalog revision is a
content fingerprint, NOT the future canonical DB revision FK. Do not manually
set completeness/review metadata for a real account to enable this feature.
Frontend and legacy input/public APIs remain unchanged until replacement gates
pass per the plan. This is not the full manual-removal completion.

42 new synthetic context/API tests, TDD red/green observed. Full offline suite:
377 passed, 38 deselected with explicit docs/acceptance/hus_2022 catalog root;
one preexisting Starlette/httpx warning. Ruff changed files/diff checks passed.
No PostgreSQL/browser/live acceptance for this staged backend-only change.
Inline review used toolkit entrypoint override; no subagents/worktrees/commits.
See docs/VNU_ACADEMIC_CONTEXT_STATUS_2026_10_23.md for verified scope and pending
work. Ignored execution ledger: backups/vnu_academic_cutover_20261023/progress.md.

## Planning checkpoint - 2026-10-23: retire manual grades after VNU academic-context cutover

User asked what Enter grades was for, agreed with the proposal to fully remove
it once VNU feeds eligibility/recommendations, then explicitly requested a PLAN.
Created docs/KE_HOACH_CHUYEN_SANG_BANG_DIEM_VNU_2026_10_23.md. This is planning
only, not authorization to start this implementation in the current request.
Added scope notes to modules/02-transcript-profile.md and modules/README.md.

Target: one source of academic results, owner-authenticated VNU snapshot;
retire manual entry/upload/demo/public APIs accepting client records/passed sets.
Keep pure domain tests/synthetic fixtures, immutable source snapshots and legacy
DB rollback resources. Do not delete those as part of UI removal. Need fresh
policy/program applicability evidence; do not infer cohort from screenshot ID.
Current legacy model rejects retakes, defaults missing grades to passed and
applies project grade thresholds/GPA conversion; raw portal data cannot be
fed straight into it. No matching by name/stripping E or best/latest retake
selection without source-backed policy.

Seven phases: evidence/policy, complete/safe sync, versioned AcademicContext,
server-owned authenticated academic endpoints, frontend cutover, remove manual
flow/old public personal-input APIs, end-to-end acceptance. Do not delete the
existing input path before replacement gates pass or serve recommendations from
an empty completed set when the real context is unavailable. Unresolved results
must neither satisfy prerequisites nor lead to unsafe repeat recommendations.
Snapshot/catalog/policy changes invalidate contexts, baseline what-if and chat.
Stored old data may be used only with valid session and sufficient readiness;
a VNU outage is not permission to bypass authentication. Sources stay unchanged.

No runtime/API/DB/.env changes, portal access, tests, restart, commit or push in
this planning request. Existing login/UI work remains local and unchanged.

## Dashboard charts checkpoint - 2026-10-23: VNU statistics and demo UI removed

User requested actual dashboard charts and removal of the obsolete Demo data
selector now that VNU login works. Continued GitHub frontend-design guidance.
Removed the demo profile selector, auto-loading /profiles and all associated
frontend profile-selection helpers/state. Removed year-based buttons that
generated invented sample grades. Test fixtures and backend compatibility APIs
remain; no real records were changed/deleted. Local-file preview still exists
as Open transcript file; it never injects sample grades automatically.

Dashboard now prioritizes DESCRIPTIVE charts from the authenticated saved VNU
snapshot: arithmetic mean of valid source 10-point grades by semester, source
letter-grade distribution, and sum of credits written on attempts by semester.
Every retake stays separate; missing/invalid values stay unknown (zero is valid).
Mean is explicitly NOT official GPA, attempt credit sum is NOT earned credits.
No catalog matching, grade conversion, pass inference, best-attempt selection
or source apply into eligibility/recommendations/manual transcript was added.
Unknown completeness and source fetched time remain visible. Official summary
text is displayed as supplied by the snapshot, without recalculation.

Charts have a shared academic-year filter, labelled points/legend, an accessible
data/calculation table, both themes/VI-EN/mobile and empty states. Source data
stays in JS memory only and is cleared from ALL chart DOM on logout/delete/
expiry. Existing manual KPI/progress/eligibility panel is under a collapsed
Study plan from manual data section. Source charts are independent of the
selected draft catalog; changing major still resets only the manual plan.

This supersedes the earlier no-profile-fetch-on-dashboard rule: initial page
now requests /me/profile ONCE to visualize the saved authenticated snapshot.
It never logs in/crawls VNU automatically. No session means charts show sign-in
empty states; the existing 401 auth semantics remain (login module still deferred).
Portal publishes snapshot/source_summary/fetched_at to chart subscribers via
in-memory events; identifiers and credentials are not passed into chart events.
No backend/API/worker/database/.env changes or server restart during this task.

Added app/static/analytics.js (pure aggregation + SVG/CSS charts), analytics.css,
tests/frontend/check_analytics.mjs and check_charts.py. Node aggregation tests
passed retakes/comma/zero/missing/invalid values/year filtering/no input mutation.
Three actual Chrome fixture regressions passed: check_charts.py, check_workspace.py,
check_portal.py. Checks include correct means/counts/credits, no bridging across
missing-grade semesters, filter changes, no demo API/UI, no source apply, source
preservation, logout chart cleanup, VI/EN, theme buttons and 390px containment.
Reviewed light/dark/mobile synthetic screenshots in ignored
backups/dashboard_charts_20261023/. Ruff frontend tests, JS syntax, diff checks
passed. Health/readiness 200. No Python/PostgreSQL rerun for frontend-only work.
All changes local; no commit/push. Existing portal identity/completeness gates
and preservation of original HUS/RAG sources remain in force.

## UI redesign checkpoint - 2026-10-23: Dashboard and dedicated profile page

User requested a polished frontend redesign using the GitHub frontend-design
skill: profile as its own navigation destination and Dashboard replacing the
initial transcript view. User explicitly deferred login-module/401 work until
later. Read/applied .github/skills/frontend-design/SKILL.md. Changes are frontend
only; no API/auth/worker/database changes, portal calls or backend restart.
Existing real user session should remain valid until its original expiry.

Dashboard is default /#dashboard; profile is /#profile, a full tab panel rather
than a dialog. Navigation has Dashboard, My profile, Enter grades, Eligibility,
Next semester, with hash/Back/Forward and existing keyboard tab controls.
Header is compact; program/demo selectors moved to sidebar. Dashboard uses
manual transcript metrics, credit progress, actual manually recorded terms,
up to four API-eligible courses and navigation actions. It never applies VNU
grades into academic calculations. Enter grades retains manual entry/preview.
Profile has identity/source/update information, unknown fields, full transcript,
source totals, code/name search, term filter and attempt counts. Source grades
and retakes are unchanged; logout/expiry still clears personal DOM/state.
Theme/VI-EN and 390px containment preserved. Dashboard does not probe profile
on initial load; unauthenticated profile access still returns 401 as designed.

The user's latest screenshot showed the real profile/transcript loaded after
the UTF-8 fix. This is user-supplied evidence of successful display, not proof
of identity aliases, completeness, pagination or changed-source sync policy.
Do not copy the identifier/individual grades from screenshots into artifacts.
Earlier zero-real-record observations are historical; do not assume runtime
portal tables are empty now. This redesign's screenshots/tests used synthetic
data only, with personal endpoints intercepted.

New app/static/dashboard.js and workspace.css; HTML/app.js/portal.js/i18n.js
updated. tests/frontend/check_workspace.py passed actual Chrome UI navigation,
manual edits and metric reflection, source/manual isolation, search/term filters,
VI/EN, both theme buttons, 1440/390px, all five tabs, ID/panel structure, major
reset isolation and no JS exceptions. Existing check_portal.py also passed,
including login/show password/logout clearing. Screenshots reviewed (desktop
light/dark and mobile). Evidence ignored under backups/workspace_redesign_20261023/.
Ruff frontend tests, JS syntax and diff checks passed. No Python/PostgreSQL
rerun for this UI-only change; do not claim historical backend counts as new.

Report: docs/WORKSPACE_DASHBOARD_PROFILE_2026_10_23.md. No commit/push requested
or performed; all earlier local portal changes remain. Resume login module only
when user asks, preserving identity/completeness/privacy rules below.

## Worker encoding fix - 2026-10-23: reproduced Windows cp1252 pipe failure

User retried and showed POST /auth/portal 502 (no credentials supplied in chat).
Investigated the real Windows Python child stdout: encoding is cp1252. A child
writing Vietnamese JSON with ensure_ascii=False failed with exit 1 and empty
stdout; parent json.loads(empty bytes) raised, causing the observed 502 path.
Worker now writes explicitly UTF-8 to sys.stdout.buffer; parent decodes UTF-8
and supplies PYTHONIOENCODING=utf-8. Nonzero exit/empty/malformed output becomes
a safe worker_failed/worker_output_invalid code with stage-only logging; raw
stdout/stderr, credentials and real grades are never logged. API distinguishes
technical 502/504 errors from identity 401. UI has technical error wording.

27 focused integration tests passed including a REAL subprocess roundtrip with
forced cp1252 stdio and synthetic Vietnamese course/term/password strings. It
verifies the production binary writer and parent collector, not only mocks.
Five malformed/failed worker cases also verify safe diagnostics. Ruff passed.
This fixes a reproduced transport defect; live account acceptance still needs
the user retry after restart. No database/catalog/.env change or commit/push.

Final encoding-fix checks: 335 offline passed / 38 deselected (explicit HUS PDF
acceptance root), profile browser fixture regression passed, Ruff/JS syntax/
diff checks passed. Restarted the identified local Uvicorn processes with this
fix; /health and /ready both returned 200. User still needs a live UI retry.

## Login fix checkpoint - 2026-10-23: fresh authentication evidence replaces mandatory label

User tried the UI and received identity_unverified. Cause: the new worker
required an unverified exact student-ID label in portal body text, even after
the existing connector reached the transcript. Do not record the user ID from
their screenshot. No credentials were supplied to the agent during this fix.

DaotaoClient.login now proves a fresh portal authentication transaction:
context has no portal cookies before login; initial page lacks authenticated
menu; form action is HTTPS on the reviewed host with POST; matching form POST
response is 2xx/3xx and its submitted username matches the field; authenticated
menu appears and login form disappears. It returns the account verified by
that transaction. Worker uses this evidence when no labelled ID is present;
an explicit conflicting portal ID still fails closed. This is not acceptance
based solely on a client username or a nonempty transcript. Common label
variants/separate cells are accepted. Alias-to-student-ID mapping remains open.
The button now says Sign in with VNU when logged out and My profile when loaded
(localized VI/EN), addressing the user's earlier discoverability problem.

Validation: 17 focused offline integration tests passed, Ruff passed, and
tests/frontend/check_portal_auth.py used Chrome with intercepted synthetic
portal HTML to prove successful POST login without an ID label and rejection
of invalid login/status, existing cookies/menu and foreign-host forms. No real
portal login performed by the agent for this correction; user must retry UI.
Completeness=unknown/update preservation gates are unchanged. All changes stay
local; no commit/push. See the integration status document for current gates.

Final fix verification: 325 offline passed / 38 deselected with explicit HUS
PDF acceptance root; existing synthetic profile UI browser regression passed,
Ruff/JS syntax/diff checks passed. Restarted only the local project Uvicorn;
health and readiness returned 200. User should refresh with Ctrl+F5 and retry
Sign in with VNU. No new PostgreSQL regression was needed for this auth/parser
and button fix; earlier 22-pass DB evidence remains historical.

## Implementation checkpoint - 2026-10-23: portal integration local; live acceptance pending

This section supersedes earlier statements that portal implementation has not
started. User explicitly requested implementation of the agreed portal plan,
use of the GitHub frontend-design skill, and one update per completed step.
Skill `.github/skills/frontend-design/SKILL.md` was read and applied. No commit,
push or branch merge was requested or performed. Existing local documentation
changes were preserved. Work remains in the existing workspace branch.

Implemented selective connector import from `b790d6af`, source snapshot parser,
separate HUS migration `hus_20261023_03`, transactional owner/snapshot/attempt
store, auth/profile/sync/cancel/delete APIs, isolated Playwright workers and
profile dialog with source tables, VI/EN and light/dark. Source grades remain
separate from manual transcript, GPA/progress/eligibility/recommendations/chat.
Optional Playwright 1.64.1 is now installed in the project venv; dependency is
in `requirements-portal.txt`. Worker uses installed Chrome, not a downloaded
Chromium. Credentials are stdin-only to a short-lived process, never persisted.
CLI now requires explicit `--show-transcript` to print personal table content.

Migration was applied to local runtime ai07 after a custom-format pg_dump to
ignored `backups/portal_integration_20261023/before-portal.dump`. Backup exists;
do not overwrite. Four active catalog revision IDs matched before/after; no
source/catalog publication or .env changes. Runtime portal_users count was zero
at verification; no real portal records were created. The HUS repository head
and catalog publisher compatibility checks were adjusted for the new revision.
Do not revert just the migration head while leaving runtime tables mismatched.

Uvicorn was restarted hidden on http://127.0.0.1:8000. Health/readiness returned
200, unauthenticated auth/profile returned 401 with no-store. Logs and synthetic
browser screenshots/JUnit are ignored under that backup directory. Check live
readiness again on resume. Web sessions expire after 30 minutes in RAM and are
lost on app restart; persisted snapshots require fresh VNU authentication.
UI removes personal DOM/state on logout/expiry; it does not use localStorage
for profile data. Saved data deletion removes portal owner and dependent data,
revokes its sessions and prevents pending sync from restoring deleted records.
Cancellation while reading never saves; once a DB commit begins, cancellation
waits for its real result instead of falsely reporting rollback.

Final automated evidence: 323 offline passed / 38 deselected with explicit HUS
PDF acceptance root; 22 HUS PostgreSQL passed / 337 deselected on the preceding
DB regression (including 3 portal tests; later changes covered by offline/job
checks). Ruff app/tests/new migration/CLI, JS syntax and whitespace checks
passed. Chrome fixture check passed source preservation/retakes/escaping,
newest-term ordering, VI/EN, both themes, 1440/390px, delete-confirm keep and
logout DOM cleanup, no JS exceptions. Dark mobile screenshot inspected. One
existing Starlette/httpx deprecation warning remains. No legacy PostgreSQL
rerun or live portal login through the new API was performed.

IMPORTANT remaining gates: the mandatory identity-label rule described in the
original implementation was replaced by the fresh-login checks in the newer
checkpoint above. Real identity/alias acceptance still needs a user retry.
Pagination/loading/filter completeness remains UNKNOWN.
Parser always marks completeness=unknown; first snapshot may save with warning,
same digest is idempotent, changed unknown data NEVER replaces a saved snapshot.
Consequently real changed-grade update is not accepted yet. CAPTCHA/OTP has no
dedicated interaction_required flow; generic safe error is returned. Do not
claim the first-delivery plan is fully achieved. Approximate implementation
progress reported to user: 90%, live acceptance pending.

Resume at `docs/PORTAL_INTEGRATION_STATUS_2026_10_23.md` and the original plan.
Have the user enter credentials directly into the local profile dialog, not into
chat/logs. Need an authorized live acceptance to verify actual identity source,
completeness, course/term/summary correspondence and persistent read/update/
delete/relogin. Never store credentials, cookies, raw DOM, traces/screenshots of
real grades in shared artifacts, or real records in tests/Git. Do not regenerate
retired RAG trials. Earlier RAG source-preservation instructions remain in force.

## Session close — 2026-10-23: VNU connector verified; persistent profile plan agreed

User requested review and a live trial of the teammate's `feat/login` branch.
Fetched `origin/feat/login` at `b790d6af5e3a2fa183e28dd9b08286489572c71a`.
The branch's `DaotaoClient` successfully logged into the real VNU portal,
opened student results and read 45 table rows, including 36 course rows with
grade text, using an account explicitly authorized by the user. Both synthetic
branch tests passed. A second permitted read displayed the transcript in chat.
Do not copy the credentials, student identifier or individual grades from the
conversation into memory, code, Git, fixtures or reports. Browser contexts were
closed. These trials do not establish completeness for all accounts, pagination,
CAPTCHA/OTP, or reliable authenticated identity binding for a persistent profile.

Trial runner and optional Playwright dependencies remain ignored under
`backups/login_trial_runtime/`. The runner loads the branch code using Git,
receives credentials via stdin and currently prints transcript rows if run;
do not run it into shared logs or persist its output. No credentials or real
transcript files were created. Keep future verification output minimal unless
the user explicitly asks to see their transcript. Dependencies were isolated
from the project venv requirements. No branch checkout/merge, runtime app code,
database schema/data, source catalog or .env change occurred.

The user requested an integration plan and explicitly selected:
- Localhost first, at http://127.0.0.1:8000; server deployment later.
- First delivery: VNU login, persistent account-owned profile and source
  transcript in PostgreSQL, plus a profile UI to view/update/delete that data.
- Authenticate through VNU each login; NO separate local password and NO
  storage of VNU passwords, including hashes used for reconnecting.
- No portal transcript apply into GPA/progress/eligibility/recommendations
  in this first delivery. Keep manual transcript and chat behavior separate.
- Use the user's `.github/skills/frontend-design/SKILL.md`, which was read;
  preserve existing Sổ học tập branding, light/dark and Vietnamese/English UI.
- Ask meaningful questions when needed and provide regular progress updates.

This explicit persistence request supersedes older blanket session-only rules
for portal profile/source transcripts. It does NOT authorize storing portal
credentials/cookies, chat history, or inserting real records during planning.
The existing accounts/students/course_attempts constraints require local password
hashes/catalog facts/academic outcomes that raw portal data does not provide;
the plan proposes separate owner/snapshot/attempt/session tables through a NEW
HUS migration, avoiding invented cohort mappings or password hashes.

Plan: `docs/KE_HOACH_TICH_HOP_PORTAL_BANG_DIEM_2026_10_23.md`.
Updated `modules/09-portal-transcript-import.md` and `modules/README.md` to link
the plan and reflect verified connector/new scope. All scope questions are now
answered. Implementation has NOT started; no auth/profile API, UI, migration or
persistence service has been delivered. Resume from the agreed plan when user
requests implementation; no need to ask the same scope/auth questions again.

At close, corrected Vietnamese encoding damage in the new plan and stale
pending-auth wording in module 09. Documentation link/encoding/whitespace checks
are the close-out verification, not a new app/database regression. Changes are
local/uncommitted: this memory, both module docs and the new plan. No commit/push
was requested for this session. Earlier RAG retirement/source-preservation
instructions below remain in force. User requested memory update and close.

## Session close — 2026-10-23: HUS RAG trial data removed; group plan pending

The user decided the trial chunking was not suitable and will discuss a new
approach with the team. At their request, all generated preparation data under
`backups/rag_preparation/` was deleted, including build01–07, reproduce builds,
normalized Markdown, document reviews, documents/chunks, evaluation cases and
the temporary retriage script. The generated annotation files under
`docs/acceptance/hus_preparation/` were also deleted. IDE tabs still pointing
to build06 are stale. Do not treat the former 6-document/10-chunk candidate as
an available corpus or regenerate it without a new request.

The original `crawldata` snapshot remains at
`data/hus/releases/2026-10-22-3a45aae-candidate/`: 210 files, with the
catalog SHA-256 matching its manifest. It is the retained source for the next
team discussion. The old build07 counts (6 include, 88 needs_review,
6 pending_ocr, 6 exclude) are historical observations only. In particular,
postgraduate sources may be useful, but their content and applicability have
not been verified. There is no active HUS RAG corpus, index or answering
service. No source snapshot, runtime catalog, database or `.env` was changed.

The project retains discussion material in
`docs/THONG_KE_VA_DANH_GIA_KHA_THI_RAG_HUS_2026_10_23.md` and the historical
`docs/KE_HOACH_TIEN_XU_LY_DATA_HUS.md`. The experimental
`tools/prepare_hus_corpus.py` and `tests/catalogs/test_hus_preparation.py`
remain in Git as reference code; their old review/case inputs and output
artifacts no longer exist, and their chunking configuration is not a selected
design. Do not present historical statistics as current generated data.

The user then requested a commit and push. Commit `3129f7c204da81eff74051a9d5d8fece4583b18f`
(`Document HUS RAG preparation and retired trial data`) was pushed to GitHub
`main`; remote `refs/heads/main` was independently verified at that hash.
The worktree was clean before this memory-only update. Six focused synthetic
tests, Ruff, staged diff checks and document-link checks passed for that
commit. This new memory update is local; do not claim it is already pushed.
The next substantive RAG step waits for the team's agreed data/chunking plan.

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
