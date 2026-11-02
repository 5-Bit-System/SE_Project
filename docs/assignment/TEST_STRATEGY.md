# VT-100 — risk-based strategy, revised

Main risk: partial import loses valid records or a small change corrupts an
unrelated behavior. The slice now connects CSV to real transcript models and
the existing eligibility consumer; all data/catalog fixtures are synthetic.

## Levels and state model

- Unit: parser, shape/limits, expected vs systemic error policy, counts/state.
- In-process integration: real TranscriptRecord/StudentTranscript and
  evaluate_eligibility; grade boundary, duplicates, preservation, major isolation
  and source-review gate. This does not prove API, DB commit or persistence.
- Existing offline regressions protect unrelated app behavior. Separate verified
  CI includes existing PostgreSQL suites; these are not import persistence tests.
- E2E/browser import test is inapplicable: no import UI/API has been added.
- Load: 200 worker tasks rendezvous at a shared barrier; peak inflight includes
  waiting. E2E timings start just before submit and include queue/start/barrier.

Row model: pending -> imported OR rejected; terminal once. Batch validation
failure -> rejected batch before effects. Otherwise processing -> completed,
partial or failed. Header-only 0/0 is completed; failed requires rejected > 0.
Only typed data rejection continues. Unexpected infrastructure failure aborts
processing; no false success is returned. This is distinct from T02 partial data
failure. Choose data for all terminal states, bad row between good rows,
normalization/duplicates, 4.9/5.0 grade boundary, unknown metadata and unsafe batch
structure after an initially valid row.

## Cases (logical cases, not pytest invocation count)

File keys: B=`tests/importing/test_batch.py`, D=`tests/importing/test_transcript_import.py`,
P=`tests/importing/test_batch_performance.py`; R=existing offline suite.

| ID | Requirement/risk | Level/file | Precondition/input | Expected | Priority |
|---|---|---|---|---|---|
| T01 | AC1 per-row | Unit B | Two valid rows | Handler once each, source lines 2/3; completed 2/0 | P1 |
| T02 | AC2 data rejection | Unit B | GOOD1, BAD, GOOD2; RowImportError on BAD | Both valid accepted; partial 2/1 | P0 |
| T03 | AC4 failed | Unit B | Every handler rejects | Failed 0/2 | P1 |
| T04 | AC3 empty input | Negative B | Empty text | Batch error, zero calls | P1 |
| T05 | AC4 empty data | Unit B | Header only | Completed 0/0 | P2 |
| T06 | AC3 schema | Negative B | Duplicate header, absent header, explicit `code, ,name` | Batch error before effects | P0 |
| T07 | AC3 malformed | Failure B | Unclosed quote | Batch error before effects | P1 |
| T08 | NFR cap | Boundary B | UTF-8 payload >1 MiB | Size error, zero calls | P1 |
| T09 | NFR cap | Boundary B | 5,001 rows | Row limit error, zero calls | P1 |
| T10 | Systemic error policy | Failure B | OK, DB_DOWN, LATER; OSError | OSError escapes; LATER not run; do not hide outage | P0 |
| T11 | AC4 state/count | Unit B | All-valid, all-rejected, mixed | States and counts agree | P1 |
| T12 | Load method | Load P | 200 tasks x100 rows; known percentile vector | peak=200; E2E p95<5s; rank190/index189 | P1 |
| T13 | Unrelated behavior | Regression R | Existing offline suite | All selected tests pass; markers reported | P0 |
| T14 | AC3 width | Negative B | Good first row then short/long row | Batch width error; no early side effect | P0 |
| T15 | AC3 Unicode | Negative B | Lone surrogate | invalid_unicode before effects | P1 |
| T16 | AC1/2 domain | Integration D | TOY101 grade8, TOY102 grade12, TOY102 grade6 | Two real model records; middle invalid; original empty | P0 |
| T17 | AC2 preservation | Integration D | Existing grade7, duplicate9, new8, duplicate9 | Existing7/new8 retained; rejects2; deep copy and selections preserved | P0 |
| T18 | AC1 validation | Integration D | -1,12,nan,inf,bad,blank grade; blank code, term13, foreign course | Rejected row; no record | P1 |
| T19 | AC3 program/schema | Integration D | Different program, old foreign record; wrong headers including header-only | Batch rejection, input unchanged | P0 |
| T20 | AC5 downstream | Integration D | Real model grade4.9 vs5.0; synthetic reviewed catalog | Prerequisite unlocked iff5.0; original result unchanged | P0 |
| T21 | AC5 review gate | Integration D | Grade9; unreviewed fixture | Import succeeds; eligibility remains blocked | P0 |
| T22 | AC1/4 boundaries | Integration D | Header-only; grades0/10, blank term/term12 | Empty completed; model boundary values kept | P1 |

T06 maps to `test_whitespace_header_cell_is_rejected_before_side_effects`
in addition to parametrized legacy header tests. T14 maps to
`test_row_width_mismatch_after_valid_row_has_zero_side_effects` (two cases).
T10 maps exclusively to `test_handler_system_failure_is_not_misreported_as_bad_data`;
it is NOT a recoverable row-validation error.
Domain tests' descriptive function names are in D; exact runnable commands and
results are in TEST_FIRST_EVIDENCE.md. 22 logical cases produce 36 pytest cases
because parameterizations/functions and the external regression case differ.

## Flaky risks and residual risk

- Time/concurrency: bounded barrier, Lock counters, no sleeps/randomness. Report
  E2E/service separately; three observed E2E p95 values vary with scheduling.
  Peak includes barrier waiters; CPU-bound parser execution remains GIL-limited.
- Shared state/order: deep-copy output; local batch/task state; two preservation
  tests run in both CLI orders (2 pass each). Test never mutates live fixtures.
- Network: blocked by default fixtures; no external services/model calls.
- Missing: production import endpoint, per-row DB transactions, retry/idempotency,
  crash recovery, actual university CSV/authorization and 200 HTTP clients.
  Exact cap boundary and broader multiline/BOM format acceptance need separate
  product requirements. Numeric line trace is informative, not proof of oracles.
