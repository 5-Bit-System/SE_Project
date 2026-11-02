# BT cá nhân 3 — Specification and AI-assisted plan

**Student:** Thái Việt Trung · 23001946 · **Variant:** VT-100  
**Team/project:** SE2026-T25 · AI-07 Explainable Course Recommender  
**Repository:** https://github.com/5-Bit-System/SE_Project  
**Baseline:** `5239b7333a8f8cdf0f919e6b0505af0def99fe23` (origin/main, 2026-11-02)  
**Branch:** `bt3/23001946-vt100`

## Problem statement

The application has no bulk-import endpoint or domain-specific CSV import service. This exercise implements and evaluates a small executable import boundary: process a batch of CSV records independently and report row-level failures without discarding successful records. It is a testable vertical slice, not a deployed student/course import feature; the target entity, authorization policy, persistence contract and CSV schema were not specified by the change request.

## Acceptance criteria

- **AC1 — Per-row outcome:** each well-formed data row is passed to the supplied row handler once and produces an imported or rejected result with its source line number.
- **AC2 — Partial success:** a row validation/save exception is isolated to that row; later valid rows are still attempted and their successes remain in the result.
- **AC3 — Batch-level input failures:** empty input, malformed CSV, duplicate/blank headers, oversized input and too many rows are rejected before any handler is called.
- **AC4 — Honest summary:** batch status is `completed` when all rows import, `partial` when imported and rejected rows coexist, and `failed` when no row imports; counts equal the row outcomes.

## Non-functional constraints

- **NFR1:** standard library only; cap UTF-8 CSV input at 1 MiB and rows at 5,000 before processing to bound memory and work.
- **NFR2:** no batch-wide rollback is implied. The row handler must commit each row transaction independently; unexpected `BaseException`/process failure is not swallowed. The harness itself keeps no shared mutable state and makes no network calls.
- **NFR3:** benchmark only the deterministic in-process harness with synthetic row handlers; do not infer API/DB/production latency from it.

## Invariant / contract

**A failure while handling row N must not cancel or roll back a previously successful row, and must not prevent later valid rows from being handled.** Each row has one terminal outcome. Batch-level parse/shape failures happen before side effects.

## AI-assisted plan (written before code)

**Prompt summary recorded by the agent (not a verbatim user prompt):** read the VT-100 request, Lecture 06/07, repository guidance and current import-related code; plan a test-first partial-success CSV slice; identify assumptions, files/interfaces, state transitions, negative/failure tests, mutation, flaky risks and 200-concurrent synthetic p95; do not invent a production API or schema. The exact user change request and required workflow are reproduced in the submitted assignment; this summary describes how the agent scoped its plan.

**Initial assumptions to challenge:** (A) a student-data import endpoint exists; (B) a row callback failure can be caught and the request can safely continue; (C) local 200-thread latency represents service performance. Repository search disproved A. B requires one transaction per callback and cannot be guaranteed by an in-memory harness. C is not a production measurement.

**Planned files:** `app/importing/batch.py` (bounded parser, row state/result, summary), `tests/importing/test_batch.py`, `tests/importing/test_batch_performance.py`, `docs/assignment/` evidence and `deliverables/BT3_23001946_VT-100.pdf`. No route, database migration, course eligibility, catalog, auth or existing import behavior will be changed.

**Student challenge of AI assumption (confirmed by the student):** “Repo có sẵn CSV importer” is rejected: searching the repository shows no API/domain importer. This is why the patch is an executable harness, not a production feature.

**Review corrections from repository evidence:** searched `app/`, `database/`, `tests/`; only metadata reports/acceptance helpers use CSV. No product importer or domain row schema exists. Therefore do not invent a route/table/authorization scheme. Use an injectable row handler as a runnable characterization/harness, label it non-production, and retain an explicit follow-up requirement to define entity/schema/auth/transaction ownership before integration. The current main is `5239b73` and has the HUS source/catalog constraints; importing academic rows without a reviewed schema would create unsupported facts.

## Review boundary

This plan follows Lecture 06's spec → plan → small diff → verify → review loop, and Lecture 07's contract, state, risk and independent test evidence. AI output remains a proposal; acceptance is based on observed test runs and inspected diff. No merge is authorized by the assignment; submit a branch/PR link for team review.
