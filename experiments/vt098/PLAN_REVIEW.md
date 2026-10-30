# VT-098: pre-patch plan and review

Student: Duong Van Tai / 23001925 / SE2026-T25 / AI-07.
Baseline: `7b387a394e334e217733a571ee76a573157a24f2`.
Feature branch: `vt098/23001925-idempotency`. Never merge without team review.

## Why an executable harness

The current machine has no running Docker engine or configured disposable HUS
PostgreSQL database. Importing the complete API also requires unavailable runtime
dependencies such as argon2. Do not weaken the production gates or invent a green
production test. The authorized fallback is an isolated SQLite experiment.

The real `SemesterPlanInput` class is loaded by AST from `app/api/academic.py`.
Only that class declaration executes; other imports, routes and side effects do
not. This characterizes its actual defaults, strict integers and extra-field
rejection. The loader must fail visibly if the declaration gains dependencies.

Only empty synthetic drafts with the fixture basis are accepted for creation.
Nonempty courses are explicitly rejected: no course eligibility is invented.
The test provides an already verified account; this does not implement sessions,
CSRF or VNU authentication. Status values are result codes, not evidence of HTTP.

## Plan before the corrective patch

1. Preserve a runnable duplicate-create scaffold, two weak AI test drafts, and a
   meaningful red assertion on ID/result stability. Commit the actual red log.
2. Replace the status-only test with JSON/version and independent DB count
   assertions. Replace the duplicate happy path with deterministic rollback
   injection. Add the eight pairwise scenarios and explicit boundary cases.
   Run and commit reviewed tests while the scaffold is still red.
3. Change only `harness.py`: hash the key, canonicalize the real schema-normalized
   body, use an account/operation/key-scoped receipt, and serialize lookup/write
   with SQLite `BEGIN IMMEDIATE`. Check the receipt before current basis/quota.
4. Keep plan, business audit and receipt in one transaction; call failure hooks
   after each write and after commit. Return the durable receipt on retry.
5. Review the diff, run exactly the same reviewed tests, record exit code/output,
   interpreter/database versions and source hashes. Commit only the isolated
   experiment, evidence and instructions. Publish the feature branch for review.

## Repository-backed changes to the original AI plan

- Reject deduplication by title or whole body: `docs/SEMESTER_PLANS.md:24-25`
  permits multiple alternatives with identical titles. Distinct keys are distinct
  create intentions, even if bodies match.
- Reject process dictionaries and caching after `save_plan`:
  `app/services/semester_plan_service.py:90-157` commits plan and audit inside
  its transaction. A worker can die after that commit and before cache storage.
  The harness uses persistent receipts in the same transaction instead.
- Preserve account verification before replay in any future production patch:
  `app/auth/portal.py:33-40` and the service's `portal.bound(..., lock=True)`.
  The harness deliberately does not claim to test this security boundary.

## Assumptions and limits

SQLite's writer serialization is not PostgreSQL's account-row lock behavior.
Two-thread races and reopen checks establish only this harness's behavior.
No PostgreSQL migration, production API patch, browser E2E, process-kill crash,
coverage, mutation or 150-task/p95 experiment is part of requirement 3.
Tests planned as API/E2E in the report are still unexecuted at those levels.
Agent-generated code and the agent's self-review require the student's own
review; no independent human review is claimed.
