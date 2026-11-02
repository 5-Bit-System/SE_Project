# VT-100 — revised specification and AI plan

Student: Thái Việt Trung, 23001946; SE2026-T25; AI-07.
Repository: https://github.com/5-Bit-System/SE_Project
Branch: `bt3/23001946-vt100`. Original baseline: `5239b7333a8f8cdf0f919e6b0505af0def99fe23`.
Revision baseline: `e54f4bc095c056cd24c6af3f4ec38928ceb63390`.
This specification supersedes the generic-only version; original plans and logs remain in Git.

## Problem and scope

Bulk import of synthetic student grades should accept valid records despite an
invalid row, preserve an existing transcript and feed the existing eligibility
module correctly. The repository lacks a domain CSV importer, but DOES contain
`TranscriptRecord`, `StudentTranscript` and `evaluate_eligibility`. Reuse these
models through a small in-memory adapter; no new institutional grade rule,
production endpoint, persistence schema or authorization flow is introduced.

## Five acceptance criteria

- **AC1:** CSV columns are exactly `course_code,grade,term`, in that order. Each
  valid row becomes one real `TranscriptRecord`; existing normalization, numeric
  grade 0..10, term 1..12 and passing rules apply. Blank term means None; grade is
  required. This schema is the adapter contract, not the university export format.
- **AC2:** Invalid row data only rejects that row; later valid rows are accepted.
  Existing and accepted rows are never overwritten by duplicate course codes.
  Return a deep-copied `StudentTranscript`; original input and selections remain
  unchanged even if the returned model is later mutated. Retakes remain unsupported.
- **AC3:** Malformed/empty/over-limit CSV, blank/duplicate/wrong headers and row
  width mismatch are batch errors before callbacks. Program mismatch or foreign
  courses already in the transcript also reject the batch. Input cap: 1 MiB
  as measured by the existing UTF-8-sig encoding; 5,000 data rows.
- **AC4:** `PARTIAL` iff imported > 0 AND rejected > 0; `FAILED` iff rejected > 0
  AND imported == 0; otherwise `COMPLETED`, including a header-only 0/0 batch.
  Counts sum to the number of outcomes; source line numbers are retained.
- **AC5:** Output is accepted by the existing eligibility consumer. Imported grade
  4.9 does not unlock a prerequisite; 5.0 does, on a synthetic reviewed catalog.
  Import does not promote unreviewed catalog metadata or alter the original
  transcript's eligibility result.

## Constraints and invariant

1. No new dependencies: generic parser uses stdlib; adapter reuses installed
   Pydantic and project models. No network, real student data or database writes.
2. Expected row validation errors are isolated. Unexpected OSError/system errors
   propagate; process crashes and DB durability are not guaranteed by this adapter.
3. Measure 200 overlapping synthetic tasks with barrier and locked counters;
   nearest-rank p95 of submit-to-completion must be compared with 5,000 ms.
   Overlap includes barrier wait, not simultaneous CPU execution or HTTP users.

Invariant: a rejected data row never deletes prior valid input or prevents a later
valid row from being accepted. Batch structural errors occur before row effects.
A real persistence adapter must implement per-row transaction and retry semantics.

## Plan and AI review evidence

The first generic plan preceded commit `91d4cd8`; its collection RED remains
`deliverables/evidence/test-first-red.txt`. Student-confirmed challenge:
“Repo có sẵn CSV importer — tôi bác bỏ: tìm kiếm không thấy API/domain importer”.

The earlier conclusion that this prevented ALL domain integration was too broad:
`app/transcript.py` already has reusable models. The revision plan was recorded
before code in `docs/assignment/REVISION_PLAN.md`, followed by assertion RED in
`a1afd93` and GREEN in `68b99df`. Other rejected assumptions: catch every
Exception (can hide outage); 200 queued jobs prove overlap (barrier needed);
local parser latency proves service NFR (no HTTP/storage in the harness).

Original user request is preserved verbatim in `docs/assignment/ORIGINAL_USER_PROMPT.txt`.
The exact NEW revision instruction is quoted in `REVISION_PLAN.md`; it is not a
reconstruction of a missing original internal prompt. Initial internal plan text
was recorded only as a summary and remains labelled accordingly.

Files: `app/importing/{batch,transcript}.py`, three files in `tests/importing/`,
`tools/check_vt100_mutation.py`, `tools/measure_vt100_lines.py`, docs/evidence/PDF.
Existing transcript/rules source, APIs, DB, auth and catalog data are unchanged.
Do not merge before team review.
