# Admin Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a role-protected HUS admin console for truthful system overview, curriculum and prerequisite governance, crawler and document review, user administration, and operational monitoring.

**Architecture:** Keep the existing FastAPI application and static JavaScript/HTML/CSS frontend. Add an admin shell that consumes explicit, permission-checked JSON APIs; separate read-only views from mutations. Treat curriculum imports and crawler output as immutable draft revisions that must pass validation and an authorized review before an atomic publication. Keep existing account administration safeguards and add audit records for privileged changes.

**Tech Stack:** FastAPI, Pydantic, existing database/repository patterns and migrations, static JavaScript/HTML/CSS, pytest with synthetic fixtures, and existing browser-test tooling where available.

**Spec:** Admin-console design approved in conversation on 2026-11-01; current admin and authentication behavior in `app/api/auth.py`, `app/auth/repository.py`, `app/static/auth.js`, `app/static/index.html`, and `app/static/auth.css`.

## Global Constraints

- Preserve the existing FastAPI/static frontend; do not introduce a frontend framework or a new runtime dependency for the console.
- Every admin endpoint must enforce admin authorization on the server. Frontend visibility is not an authorization boundary.
- Never report unavailable metrics as zero. Show the metric source, update time, and loading, empty, or error state.
- The current curriculum catalogs are `draft_unverified`; they must not be shown as approved or used to imply verified academic rules.
- Imports and crawls create drafts. They must not overwrite the active catalog until validation and an explicit authorized approval succeed.
- Keep audit records for privileged account, catalog, crawler, document, and announcement actions. Do not store passwords, VNU credentials, or secret values in audit logs.
- Keep changes on a feature branch. Do not merge or push unless separately requested. Commit each independently reviewable task with a focused message.
- Preserve existing data and untracked workspace files; database migrations must be additive and rollback-aware.

## Review Focus

- Non-admin users calling admin APIs directly must receive the existing authorization failure; cover every new API family with an authorization test.
- Empty, stale, partial, malformed, and unavailable metric sources must render as unknown/error and never as a misleading zero; cover dashboard API and UI states.
- Duplicate course codes, missing prerequisite references, prerequisite cycles, invalid credits, and malformed import rows must be reported before publication; cover validator boundaries with synthetic catalogs.
- Failed approval/publication must leave the currently active catalog unchanged; cover transaction rollback and concurrent publication.
- Repeated crawler actions and retries must not create overlapping jobs or lose terminal failure details; cover idempotency and state transitions.
- Unsafe Markdown/HTML, duplicate documents, and rejected documents must not become published content; cover rendering safety, deduplication, and review state transitions.

## File Structure

- Modify `app/static/index.html`, `app/static/auth.js`, and `app/static/auth.css` to add the admin shell and accessible page containers while following existing static-app conventions. Create focused admin modules only where the existing files become hard to maintain, and load them through the existing entry point.
- Add admin API routers/services under `app/api/` and `app/services/`; keep database operations in the existing repository/database layer rather than embedding them in route handlers.
- Add additive migrations and corresponding repository tests for durable revision, review, job, and audit data. Reuse current database abstractions and migration conventions.
- Add tests under the existing `tests/` feature layout: API authorization/contract tests, repository/service tests, deterministic import/crawler fixtures, and browser tests for critical admin flows.
- Keep source manifests and generated/imported large files in the established data/release storage conventions; do not commit secrets or unreviewed live data.

## Phase 1 — Admin foundation and currently supportable pages

### Task 1: Admin shell, navigation, and access states

**Files:** Modify `app/static/index.html`, `app/static/auth.js`, `app/static/auth.css`; add focused admin frontend tests using the repository's existing browser-test layout.

**Interfaces:** Preserve the existing auth/session contract. Add admin-only navigation for Overview, Curriculum, and Accounts. Future modules must not appear as actionable links until their API task is complete.

- [x] Test that signed-out, student, and admin sessions see the correct admin entry points; direct URL/DOM access does not grant API access.
- [x] Test keyboard navigation, focus retention after page changes, mobile layout, dark theme, and loading/empty/error states.
- [x] Implement responsive admin shell using existing theme tokens and semantic navigation, headings, table captions, and status announcements.
- [x] Run focused frontend tests and inspect desktop/mobile layouts; commit `feat(admin): add protected console shell`.

### Task 2: Truthful overview metrics API

**Files:** Add `app/api/admin.py` (or extend the established admin router), `app/services/admin_overview.py`, repository queries in the appropriate existing repository module, and tests under `tests/api/` and `tests/services/`.

**Interfaces:** `GET /admin/overview` returns named metrics with `value`, `status` (`available|unavailable`), `source`, and `updated_at`. Initial metrics: total accounts from the account repository; catalog/program count, course count, and verification state from the active catalog source; application readiness from the readiness service. Do not fabricate consultation, crawler, or error counts before those sources exist.

- [x] Test admin-only access and a non-admin rejection.
- [x] Test exact counts against synthetic account/catalog data and unavailable storage/catalog cases; unavailable values must not become zero.
- [x] Implement the response model and read-only service using existing data access patterns.
- [x] Run focused API/service tests; commit `feat(admin): expose sourced overview metrics`.

### Task 3: Overview dashboard UI

**Files:** Modify the admin frontend entry/modules and `app/static/auth.css`; tests in the existing frontend test layout.

**Interfaces:** Consume `GET /admin/overview`; render each metric with its source/update time and distinct loading, unavailable, empty, and error states.

- [x] Test render behavior for available, unavailable, stale, and failed responses; assert unavailable does not display `0`.
- [x] Implement KPI cards for accounts, programs, courses, and catalog verification plus service readiness. Add a small “needs review” indicator only when derived from a real catalog status.
- [x] Run focused frontend tests and verify responsive/dark presentation; commit `feat(admin): show sourced overview dashboard`.

### Task 4: Curriculum and cohort catalog read-only views

**Files:** Modify admin frontend; add or extend read-only admin catalog API/service only where existing `/programs` and `/courses` contracts do not provide required provenance/status; add tests under `tests/api/` and frontend tests.

**Interfaces:** Program list exposes program identity, cohort/version when present in source, verification status, course count, and source provenance. Course detail exposes code, name, credits, semester/group when known, and prerequisite/corequisite status. Unknown metadata remains unknown.

- [x] Test authorized access, draft/unverified badges, absent cohort/version fields, empty catalogs, and unknown prerequisite fields.
- [x] Implement a read-only program table with search/status filters and a detail view for courses. Do not add edit/import/publish buttons in this task.
- [x] Run focused tests and verify keyboard-accessible table/filter behavior; commit `feat(admin): browse curriculum by program and cohort`.

### Task 5: Account administration UX hardening

**Files:** Modify `app/static/auth.js`, `app/static/auth.css`, and focused frontend tests; API changes only if a test reveals a missing contract.

**Interfaces:** Continue using existing `GET /admin/users` and `PATCH /admin/users/{account_id}` behavior and its self/last-admin/session-revocation safeguards.

- [x] Test search, pagination, role change, lock/unlock, request failure, stale result handling, and focus retention after rerender.
- [x] Improve table typography and mobile overflow; show clear role/account status; confirmation names the target account and explains session revocation when disabling.
- [x] Run focused API regression and frontend tests; commit `fix(admin): clarify account changes and preserve focus`.

## Phase 2 — Safe curriculum edits and review workflow

### Task 6: Versioned curriculum draft and audit schema

**Files:** Add an additive migration, curriculum revision/review repositories, and migration/repository tests in `tests/database/`.

**Interfaces:** Introduce immutable revision identity, source manifest/checksum, creator/time, validation summary, review state, reviewer/time, and active revision pointer. State transitions are `draft -> validated -> approved -> published` or `rejected`; only one revision is active per catalog scope. Record privileged actions without secrets.

- [ ] Test migration upgrade/downgrade policy, uniqueness, immutable revision behavior, reviewer attribution, and active-pointer constraints.
- [ ] Implement schema/repositories using existing database/migration conventions; ensure the active catalog remains unchanged during draft creation.
- [ ] Run database-focused tests against the configured local test database; commit `feat(admin): persist curriculum revisions and review history`.

### Task 7: Curriculum import and validation preview

**Files:** Add import/validation service and API schemas/router operations; tests in `tests/services/` and `tests/api/`.

**Interfaces:** `POST /admin/catalog-revisions/import` accepts CSV/XLSX within documented size/row limits and returns a draft revision id. `GET /admin/catalog-revisions/{revision_id}/validation` returns row-level errors/warnings and aggregate checks. Validation covers duplicate codes, missing references, prerequisite cycles, invalid credits, malformed rows, and source manifest/checksum. No import operation publishes.

- [ ] Test valid/invalid files, size/row limits, encoding, duplicate codes, dangling prerequisites, cycles, out-of-range credits, and formula-like cell content.
- [ ] Implement parsing and validation into an isolated draft; reject unsupported formats and malformed inputs with actionable row/column errors.
- [ ] Run focused tests and verify the active catalog is unchanged; commit `feat(admin): preview and validate catalog imports`.

### Task 8: Curriculum diff, approval, publish, and rollback

**Files:** Add review/publish service and admin API; tests in `tests/services/`, `tests/api/`, and `tests/database/`.

**Interfaces:** `GET /admin/catalog-revisions/{revision_id}/diff`, `POST .../approve`, `POST .../publish`, and `POST /admin/catalog-revisions/{revision_id}/rollback` require admin authorization and a reason. Publish requires successful validation and explicit approval; approval and publication identities/timestamps are audited. Rollback atomically switches the active pointer to a prior immutable revision.

- [ ] Test missing reason, unvalidated/unapproved revision, concurrent publication, transaction failure, rollback, and unchanged active pointer on failure.
- [ ] Implement safe state transitions and atomic active-revision switch; preserve prior revisions.
- [ ] Add frontend diff/review screens with clear before/after values and explicit confirmation; do not make review decisions on behalf of the admin.
- [ ] Run relevant tests and verify readiness/catalog consumers read only the active published revision; commit `feat(admin): review and publish catalog revisions safely`.

### Task 9: Prerequisite and study-condition editor

**Files:** Add focused catalog rule editor UI and service/API operations backed by the revision workflow; tests under `tests/services/`, `tests/api/`, and frontend tests.

**Interfaces:** Prerequisite/corequisite edits create a new draft revision. Validation reports cycles, missing courses, self-reference, invalid alternatives, and cross-program references. The UI shows graph/list representation, rule status, source evidence, and the revision currently being edited.

- [ ] Test valid AND/OR conditions, missing targets, cycles, cross-program references, and inability to mutate the active revision directly.
- [ ] Implement editor against draft revisions only; show validation results before review.
- [ ] Run focused tests; commit `feat(admin): edit prerequisite rules in draft revisions`.

## Phase 3 — Crawler and document governance

### Task 10: Crawler source configuration and job lifecycle API

**Files:** Add crawler admin service/API and job/source persistence through additive migrations/repositories; tests under `tests/api/`, `tests/services/`, and `tests/database/`.

**Interfaces:** Support source list/create/update/disable, validated allowlisted URLs and crawl policy, and job lifecycle `queued|running|paused|completed|failed|cancelled`. Operations are idempotent; retries retain attempt/error history. Crawler output is always a draft document/catalog revision. Do not execute arbitrary URLs or shell commands supplied by clients.

- [ ] Test role enforcement, URL policy, schedule validation, duplicate start, pause/resume/cancel transitions, retry limits, and sanitized error persistence.
- [ ] Implement source/job contracts and connect only to the project's existing crawler capability if present; document a clear unavailable state if execution integration is absent.
- [ ] Run focused tests; commit `feat(admin): manage crawler sources and job state`.

### Task 11: Crawler monitoring UI

**Files:** Modify admin frontend and styles; frontend tests.

**Interfaces:** Consume the crawler source/job APIs from Task 10. Show source status, last run, progress, counters, next scheduled run when configured, and actionable sanitized failure details.

- [ ] Test empty, running, paused, failed, stale, and unavailable states; controls must reflect legal transitions.
- [ ] Implement source/job tables, details, and guarded run/pause/retry actions with confirmation where needed.
- [ ] Run focused tests and verify responsive accessibility; commit `feat(admin): monitor crawler jobs`.

### Task 12: Document review and deduplication API

**Files:** Add document review repository/service/API and any necessary additive migration; tests under `tests/services/`, `tests/api/`, and `tests/database/`.

**Interfaces:** Store source URL, content hash, metadata, crawl/revision identity, review state, reviewer/time, and version links. Provide paginated list, detail/preview data, metadata edits on a draft, approve/reject with reason, duplicate/version links, and sanitized Markdown rendering inputs. Rejected or pending content is not published into user-facing retrieval.

- [ ] Test duplicate hashes, near-duplicate linking policy, version history, review transitions, unsafe markup, pagination, and exclusion from published content.
- [ ] Implement review storage and API with strict ownership/scope validation and safe preview handling.
- [ ] Run focused tests; commit `feat(admin): review crawled documents before publication`.

### Task 13: Document review UI

**Files:** Modify admin frontend and styles; frontend tests.

**Interfaces:** Consume document review API. Provide filters for source/status/major, preview, metadata editing on draft, duplicate/version context, and approve/reject actions with required reason.

- [ ] Test accessible preview, escaped content, filters, review confirmation, and failed request recovery.
- [ ] Implement review queue and detail panel; distinguish crawl extraction from reviewer approval.
- [ ] Run focused tests; commit `feat(admin): add document review workspace`.

### Task 14: Catalog/document link and publication gate

**Files:** Connect reviewed documents and approved catalog revisions to the existing publication path; tests under `tests/services/`, `tests/database/`, and `tests/api/`.

**Interfaces:** Publishing accepts only approved, validated revision inputs and creates a provenance manifest; user-facing catalog/RAG readers consume only the active published snapshot. Preserve the prior active snapshot on any failure.

- [ ] Test end-to-end draft -> validation -> review -> publication, pending/rejected exclusion, failure rollback, and provenance/checksum verification.
- [ ] Implement the narrowest integration with current catalog publication and document serving paths.
- [ ] Run focused end-to-end tests; commit `feat(admin): gate publication on reviewed source data`.

## Phase 4 — Phase 2 operations

### Task 15: Admin action audit log API and UI

**Files:** Extend audit repository/service/API and admin frontend; tests under `tests/api/`, `tests/database/`, and frontend tests.

**Interfaces:** Paginated, filterable audit events include actor, action, target, timestamp, result, and safe summary. No passwords, tokens, credential payloads, or unrestricted document bodies.

- [ ] Test authorization, pagination/filters, redaction, and audit creation for account/catalog/crawler/document actions.
- [ ] Implement append-only audit listing and UI with clear event details.
- [ ] Run focused tests; commit `feat(admin): add privileged action audit log`.

### Task 16: API and consultation health monitoring

**Files:** Add or extend operational metrics service/API and admin frontend; tests in `tests/services/`, `tests/api/`, and frontend tests.

**Interfaces:** Expose only metrics the application actually records: request counts/latency/error rates by route group, consultation/recommendation failures, and user feedback counts/quality signals. Include time range, sample/window metadata, and unavailable status where instrumentation is missing. Avoid collecting student transcript content.

- [ ] Test metric windows, empty periods, missing instrumentation, and data minimization.
- [ ] Implement bounded aggregation and dashboard charts/tables with explicit time range and source.
- [ ] Run focused tests; commit `feat(admin): monitor API and consultation health`.

### Task 17: Synthetic recommendation preview

**Files:** Add admin-only preview service/API and a frontend page; tests in `tests/services/`, `tests/api/`, and frontend tests.

**Interfaces:** Accept synthetic profile inputs only, run the existing deterministic eligibility/recommendation path, and return eligible/blocked explanations plus catalog revision. Do not accept or persist real student identifiers/transcripts; do not allow preview to mutate catalog or eligibility state.

- [ ] Test synthetic profiles, required major/cohort scope, unverified catalog warning, no persistence, and parity with the normal recommendation engine.
- [ ] Implement preview against the existing domain services and visibly mark all inputs/results as simulated.
- [ ] Run focused tests; commit `feat(admin): preview recommendations with synthetic profiles`.

### Task 18: Announcements and expiry management (optional follow-up)

**Files:** Add announcement repository/API/UI and tests only after owner-facing announcement placement and content policy are agreed in the product spec.

**Interfaces:** Draft/publish/expire announcement with source link, audience scope, effective/expiry dates, and audit trail. No announcement is displayed as official without an attributable source.

- [ ] Confirm content/source fields in the product spec before implementation.
- [ ] Test date boundaries, audience scoping, permissions, and safe link rendering.
- [ ] Implement and verify the management UI; commit `feat(admin): manage sourced academic announcements`.

## Acceptance Gate

- All Phase 1 tasks pass focused API/frontend tests; admin access is enforced server-side.
- Catalog revisions can be imported, validated, reviewed, published, and rolled back without partial activation; prior active data survives failed transactions.
- Crawler and document operations expose real state and provenance, and pending/rejected data never enters published user-facing content.
- Phase 2 metrics show only recorded, sourced data; synthetic preview does not touch real student records.
- Run the relevant full offline test suite, migrations against the project test database, lint, JavaScript checks, and focused browser tests when available. Report any skipped database/browser checks explicitly.
- A reviewer checks each task diff before its commit and reviews the complete branch against this plan before any integration.
