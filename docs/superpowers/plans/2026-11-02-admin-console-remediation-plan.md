# Admin Console Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Each task maps to one GitHub issue and one focused implementation commit. Follow TDD and verify each task before committing.

**Goal:** Close the catalog publication bypasses, admin-rendering injection risks, misleading crawler controls, and operational workflow gaps found in the 2026-11-02 admin review.

**Architecture:** Keep FastAPI, the existing curriculum/document repositories, PostgreSQL migrations, and static admin UI. Enforce review state transitions at the service/repository boundary, not only in the UI. Treat every catalog or document edit as invalidating prior validation/approval unless a new reviewed immutable revision is created. Render external and persisted content as text. Keep crawler controls honest until an executor exists. Preserve audit events in the same transaction as the action they describe.

**Tech Stack:** FastAPI/Pydantic, SQLAlchemy and existing HUS migrations/repositories, static JavaScript/HTML/CSS, pytest, existing Playwright browser checks.

**Spec:** Findings from the read-only admin audit (CodeGraph plus Backend Architect, Accessibility Auditor, and Application Security Engineer reviews) on 2026-11-02; relevant design in `docs/superpowers/plans/2026-11-01-admin-console-implementation-plan.md`.

## Global Constraints

- Keep all work on a dedicated feature branch; each issue is a separate commit. Do not merge or push without a separate request.
- Every mutation remains admin-only and CSRF-protected; retain the current session, self-demotion, and last-admin safeguards.
- A revision may be published only after its exact payload has passed validation and received explicit approval.
- Edits to approved/published catalog or document data must create a new draft or revoke prior approval and publication before any subsequent publish.
- Preserve prior published catalog/document snapshots and leave the current active version intact when a transaction fails.
- Treat crawled content, imported CSV values, database metadata, user identifiers, error strings, and URLs as untrusted display data.
- Never claim crawler work is running unless an executor is consuming jobs and updating progress.
- Tests must use synthetic data or an isolated test database. Never mutate the live academic database for these fixes.
- Preserve all existing untracked user data and workspace artifacts.

## Review Focus

- Import a malformed CSV, attempt approval and publication, and verify both are rejected while the active catalog remains unchanged.
- Edit an approved revision's prerequisite graph, then attempt publication with its old approval; verify the action is blocked until it is revalidated and reapproved.
- Attempt rollback to draft, rejected, and wrong-program revisions; verify only a prior eligible published revision can become active.
- Edit an approved or published document's title/major/type; verify the published snapshot cannot change without a new review.
- Put HTML payloads in CSV validation errors, document fields, crawler source names/URLs, job errors, catalog names, and account identifiers; verify they render as inert text.
- Simulate missing crawler executor, API timeouts, empty queues, more than one page of documents, and audit logger failure; verify the UI reports state without hiding records or actions.
- Request faculty-only announcements without authentication; verify the endpoint follows the explicitly selected audience policy.

## Issue and Commit Map

Each row is one issue draft and one planned implementation commit. The matching task contains the reproduction, acceptance criteria, files, and tests needed for the issue body. GitHub issue creation was attempted for all 12 drafts on 2026-11-02, but the connected GitHub integration rejected each create request with `403 Resource not accessible by integration`; no issues were created. Keep the issue titles and task details here until the repository integration permits issue creation.

| Order | Priority | Issue title | Planned commit | Depends on |
|---:|:---:|---|---|---|
| 1 | P0 | Block approval and publication of unvalidated curriculum revisions | `fix(admin): require successful validation before approval` | — |
| 2 | P0 | Revoke revision approval whenever curriculum rules change | `fix(admin): invalidate review after curriculum edits` | 1 |
| 3 | P0 | Restrict curriculum rollback to eligible published revisions | `fix(admin): reject rollback to unreviewed revisions` | 1 |
| 4 | P0 | Re-review document metadata changes before publication | `fix(admin): invalidate document review after metadata edits` | — |
| 5 | P1 | Render CSV import validation feedback as inert text | `fix(admin): escape catalog import preview content` | — |
| 6 | P1 | Safely render crawled documents and other admin data | `fix(admin): render external admin data as text` | — |
| 7 | P1 | Make crawler job state truthful when no executor is connected | `fix(admin): report crawler executor availability accurately` | — |
| 8 | P1 | Paginate the crawled-document review queue | `fix(admin): paginate document review queue` | — |
| 9 | P1 | Show crawler and document load failures in the admin UI | `fix(admin): surface crawler and document load errors` | — |
| 10 | P1 | Make admin audit coverage complete and transaction-safe | `fix(admin): audit every privileged mutation atomically` | — |
| 11 | P1 | Enforce the audience policy for public academic announcements | `fix(academic): restrict announcement audience responses` | — |
| 12 | P2 | Add admin browser regression evidence for the repaired workflows | `test(admin): capture remediation browser regression evidence` | 1–11 |

## Tasks

### Task 1: Require a successful validation record before approval or publication

**Issue:** Block approval and publication of unvalidated curriculum revisions.

**Files:** Modify `app/api/admin.py`, `app/curriculum/repository.py`, `app/curriculum/publication_gate.py`; add tests in `tests/api/test_admin_catalog_workflow.py` and `tests/database/test_curriculum_revisions.py`.

**Interfaces:** Import persists validation status and summary for both valid and invalid drafts. Approval accepts only a revision whose latest validation is explicitly `valid: true`, with no errors, and whose validation digest matches the current payload. Publication repeats the same invariant inside its transaction.

- [ ] Add a failing API/service test: malformed import -> approve returns a client error -> publish remains blocked -> active revision unchanged.
- [ ] Add a failing test for missing/empty validation summary and a stale payload digest.
- [ ] Implement a single validation predicate shared by approval and publication; fail closed when validation is absent or stale.
- [ ] Run focused tests and the relevant HUS PostgreSQL tests; commit `fix(admin): require successful validation before approval`.

### Task 2: Invalidate approval and validation after curriculum edits

**Issue:** Revoke revision approval whenever curriculum rules change.

**Files:** Modify `app/api/admin.py`, `app/curriculum/repository.py`, `app/curriculum/rule_service.py`; extend `tests/api/test_admin_prereq_editor.py` and `tests/database/test_curriculum_revisions.py`.

**Interfaces:** Curriculum edits may target drafts only. If compatibility requires editing an approved revision, the same transaction must clear `reviewed_by`, `reviewed_at`, approval decision, validation summary/digest, and return it to `draft`; no published revision is editable in place.

- [ ] Add a failing test for approve -> change prerequisite -> publish; assert publication is rejected and the old reviewer approval is not retained.
- [ ] Add a failing test that direct edits of a published revision are rejected or create a separate draft.
- [ ] Implement the minimal state transition and audit entry for the edit.
- [ ] Run focused tests plus publication-gate regressions; commit `fix(admin): invalidate review after curriculum edits`.

### Task 3: Allow rollback only to a prior eligible published snapshot

**Issue:** Restrict curriculum rollback to eligible published revisions.

**Files:** Modify `app/api/admin.py`, `app/curriculum/repository.py`; extend `tests/database/test_curriculum_revisions.py` and `tests/api/test_admin_catalog_workflow.py`.

**Interfaces:** Rollback target must belong to the requested program and have immutable published history with a valid provenance manifest. Draft, validated-only, rejected, approved-but-never-published, and cross-program targets are rejected. Switch the active pointer atomically and leave the current revision unchanged on failure.

- [ ] Add failing tests for draft, rejected, never-published, cross-program, and valid prior-published targets.
- [ ] Add a transaction-failure test asserting the previous active pointer remains active.
- [ ] Implement target-state checks inside the transaction to avoid a check/use race.
- [ ] Run focused database/API tests; commit `fix(admin): reject rollback to unreviewed revisions`.

### Task 4: Re-review document metadata changes before publication

**Issue:** Re-review document metadata changes before publication.

**Files:** Modify `app/api/admin.py`, `app/crawler/document_review_service.py`; extend `tests/services/test_document_review.py` and `tests/api/test_admin_document_review.py`.

**Interfaces:** Metadata updates are allowed only for pending drafts. If editing an approved document is supported, it must clear reviewer, review time/reason, and `is_published`, create a new version, and require review again. Metadata writes and audit records share one transaction.

- [ ] Add a failing test that edits title/major/type on an approved and a published document; assert the old published representation cannot silently change.
- [ ] Test pending draft edits remain possible and a subsequent approval applies to the edited version.
- [ ] Implement a draft-only guard or versioned replacement using existing document version fields.
- [ ] Run focused document/database tests; commit `fix(admin): invalidate document review after metadata edits`.

### Task 5: Render CSV import feedback as inert text

**Issue:** Render CSV import validation feedback as inert text.

**Files:** Modify `app/static/admin.js`; extend `tests/frontend/check_admin_import.py` or add a focused browser test.

**Interfaces:** Validation messages, filenames, revision IDs, and stats remain text. Static visual structure may use DOM elements, but imported values are inserted with `textContent` or a reviewed escaping helper.

- [ ] Add a failing browser test with `<img src=x onerror=...>` in a rejected CSV cell; assert it appears as text and no event/script runs.
- [ ] Add coverage for error, warning, filename, and revision identifier values.
- [ ] Replace unsafe HTML interpolation with text-node/DOM construction.
- [ ] Run the focused browser test and JavaScript syntax check; commit `fix(admin): escape catalog import preview content`.

### Task 6: Safely render crawled and persisted admin data

**Issue:** Safely render crawled documents and other admin data.

**Files:** Modify `app/static/admin.js`, `app/static/auth.js`; extend/add frontend tests for documents, crawler, curriculum, and users.

**Interfaces:** All dynamic text from APIs or crawled files is rendered using text nodes or a single tested escaping helper. Source links accept only `http:`/`https:` URLs and display rejected schemes as plain text. Preserve static badge markup without interpolating dynamic strings into it.

- [ ] Add failing browser cases for malicious document title/URL/major/type, crawler source name/base URL, job error text, program name/id, and account subject.
- [ ] Verify link activation cannot navigate to `javascript:` or other executable schemes.
- [ ] Replace the affected `innerHTML` interpolation sites while keeping fixed, trusted status templates readable.
- [ ] Run all focused frontend security tests; commit `fix(admin): render external admin data as text`.

### Task 7: Do not claim crawler execution without a worker

**Issue:** Make crawler job state truthful when no executor is connected.

**Files:** Modify `app/api/admin.py`, `app/crawler/service.py`, `app/crawler/repository.py`, `app/static/admin.js`; add tests under `tests/services/`, `tests/api/`, and `tests/frontend/`.

**Interfaces:** Until a production executor is connected, job creation must report an explicit unavailable/not-started response and must not insert a row as `running`. UI run/pause/resume controls reflect that state. A real worker is a separate follow-up that must claim jobs, crawl allowlisted sources, update progress, and finish/fail jobs.

- [ ] Add failing API/service tests showing run action cannot create a stuck `running` job without an executor.
- [ ] Test the UI clearly states that execution is unavailable and does not imply progress.
- [ ] Implement the smallest truthful status/control behavior; preserve stored historical job details.
- [ ] Run crawler service/API/UI tests; commit `fix(admin): report crawler executor availability accurately`.

### Task 8: Paginate the document review queue

**Issue:** Paginate the crawled-document review queue.

**Files:** Modify `app/static/admin.js` and the document review markup in `app/static/index.html`; extend `tests/frontend/check_admin_documents.py`.

**Interfaces:** Use API-supported `limit` and `offset`; expose total and accessible previous/next controls. Filter/search changes reset offset to zero. Preserve current filters when moving between pages.

- [ ] Add a failing browser/API test with at least 101 synthetic documents; verify page 2 can reach the final item.
- [ ] Test changing a filter from page 2 resets to page 1 and no duplicate/missing records appear.
- [ ] Implement pagination and result-count text with keyboard-accessible controls.
- [ ] Run focused tests and mobile layout check; commit `fix(admin): paginate document review queue`.

### Task 9: Show crawler/document loading errors and stale data

**Issue:** Show crawler and document load failures in the admin UI.

**Files:** Modify `app/static/admin.js`, `app/static/index.html`, `app/static/auth.css`; extend frontend crawler/document tests.

**Interfaces:** Each failed load shows an inline status message and retry button. Retained rows are marked stale with their last successful refresh time. Empty state is distinct from loading and failure.

- [ ] Add failing tests for timeout, 401/403, 500, empty response, and a failed refresh after a successful load.
- [ ] Implement separate loading/error/stale/empty states without clearing useful rows on transient failure.
- [ ] Test retry recovery and screen-reader status announcements.
- [ ] Run focused frontend tests; commit `fix(admin): surface crawler and document load errors`.

### Task 10: Make audit coverage complete and transaction-safe

**Issue:** Make admin audit coverage complete and transaction-safe.

**Files:** Modify `app/announcements/service.py`, `app/api/admin.py`; extend tests in `tests/services/test_announcements_service.py`, `tests/api/test_admin_announcements_api.py`, and `tests/api/test_admin_crawler_api.py`.

**Interfaces:** Audit failure must roll back the associated privileged mutation or return a failure; do not swallow it. Crawler source update and document metadata update record actor, target, changed fields, and reason where applicable. Do not log credential material or full sensitive content.

- [ ] Add failing tests that force audit insertion to fail during announcement create/publish/expire/delete and crawler source update; assert no unaudited mutation commits.
- [ ] Test redaction and presence of actor/target/action for successful mutations.
- [ ] Implement atomic audit writes and add the missing source-update event.
- [ ] Run focused API/service/database tests; commit `fix(admin): audit every privileged mutation atomically`.

### Task 11: Enforce academic announcement audience policy

**Issue:** Enforce the audience policy for public academic announcements.

**Files:** Modify `app/api/academic.py` and, if needed, account/audience resolution; extend `tests/api/` announcement tests.

**Interfaces:** Public callers may request only audience `all`. Audience-scoped announcements are returned only when the application has a verified identity and a supported matching audience; current account role `admin|student` does not establish a faculty identity. Until then, faculty-only content stays hidden from anonymous/public requests.

- [ ] Add failing tests for anonymous requests with `audience=faculty` and `audience=students`, plus public `all` content.
- [ ] Add an authenticated test for the supported student audience and verify unknown audience values are rejected.
- [ ] Implement authorization/policy checks without exposing whether hidden announcements exist.
- [ ] Run focused API tests; commit `fix(academic): restrict announcement audience responses`.

### Task 12: Browser regression evidence for admin remediation

**Issue:** Add admin browser regression evidence for the repaired workflows.

**Files:** Extend `tests/frontend/check_admin_workflow.py`, `check_admin_import.py`, `check_admin_documents.py`, `check_admin_crawler.py`, and `check_admin_audit.py`; keep screenshots in ignored `backups/admin_remediation_20261102/`.

**Interfaces:** Run the existing admin journeys against an isolated local test database and capture named screenshots for desktop light/dark and mobile views. Screenshots are evidence of rendered pages; assertions also verify state, access, and behavior.

- [ ] Add regression assertions covering blocked invalid publication, stale-review rejection, document pagination, visible load errors, inert hostile strings, and unavailable crawler state.
- [ ] Run the selected Playwright checks with the supported browser and isolated test fixtures; capture screenshots under the specified ignored evidence directory.
- [ ] Review each screenshot for clipped controls, unreadable tables, modal focus, stale/error affordances, and responsive overflow; fix only regressions introduced or uncovered by the issue tasks.
- [ ] Run the offline suite, HUS/PostgreSQL tests, Ruff, and JavaScript syntax checks; record commands and evidence locations in the PR description; commit `test(admin): capture remediation browser regression evidence`.

## Delivery Order and Acceptance

1. Complete Tasks 1–4 first. These protect data integrity and ensure approval always applies to the exact current catalog/document content.
2. Complete Tasks 5–6 before exposing more imported/crawled content in admin screens.
3. Complete Tasks 7–11 as independent fixes; crawler availability can be corrected without waiting for a new worker implementation.
4. Complete Task 12 after the behavior changes, then conduct a fresh whole-branch review against this plan.

The remediation is ready for a PR only when all P0 tasks pass their PostgreSQL transaction tests, each security issue has a failing-then-passing browser regression test, the crawler UI accurately reflects executor availability, the document queue reaches records beyond page 1, audit failures cannot silently commit privileged actions, and browser evidence has been reviewed. If a PostgreSQL service or browser is unavailable, mark that gate incomplete and report why; do not claim the corresponding flow verified.
