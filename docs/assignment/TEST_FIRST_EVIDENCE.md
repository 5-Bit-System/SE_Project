# VT-100 — verified execution evidence (revision)

Original baseline `5239b7333a8f8cdf0f919e6b0505af0def99fe23` and historical
collection RED are retained. Revision starts at `e54f4bc095c056cd24c6af3f4ec38928ceb63390`.
This section replaces old current-result claims; old logs are historical.

## Assertion RED -> GREEN

Plan/exact new prompt: REVISION_PLAN.md, recorded before code. Commit `a1afd93`
contains tests and an explicitly labelled placeholder. Run:

```bash
conda run --no-capture-output -n SE_Project python -m pytest -q tests/importing/test_transcript_import.py::test_invalid_grade_between_valid_rows_preserves_both_and_original
```

Observed **1 failed**, assertion `imported_count == 2`, actual **0**. It runs and
fails a business assertion rather than collection. Raw: `transcript-red.txt`.
Commit `68b99df` implements the adapter using existing models. Parser+adapter:
**34 passed** (`transcript-green.txt`); complete focused suite below: **36 passed**.
No rewrite of historical RED or commit history.

## Direct Boolean negation mutation (restored)

```bash
conda run --no-capture-output -n SE_Project python -m tools.check_vt100_mutation
```

Rule `imported and rejected` becomes `not (imported and rejected)` in PARTIAL
selection. All-valid, all-rejected and mixed tests: **3 failed**, exit1. Script
restores exact original bytes in finally; SHA256 recorded. Then focused GREEN
run passes. Full raw log: `mutation-boolean-negation.txt`. Previous and->or
experiment remains historical, not the sole mandatory mutation evidence.

## Current GREEN and regression

```bash
conda run --no-capture-output -n SE_Project python -m pytest -q tests/importing -s
conda run --no-capture-output -n SE_Project python -m pytest -q tests -m 'not postgres and not hus_postgres and not full_catalog_acceptance'
conda run --no-capture-output -n SE_Project python -m ruff check .
```

- Focused: **36 passed in 0.18s**; `revised-import-green.txt`.
- Offline: **647 passed, 90 deselected, 1 existing warning in 4.65s**;
  `revised-offline-regression.txt`. Sandbox run stalled at TestClient; stopped
  and rerun outside sandbox. Only the completed run is success evidence.
- Ruff: all checks pass; `revised-ruff.txt`.
- Two domain preservation tests in both orders: **2 passed** (0.09s/0.08s);
  `revised-order.txt`.

## Coverage

```bash
conda run --no-capture-output -n SE_Project python -m tools.measure_vt100_lines
```

Uses Python stdlib trace, no new dependency; excludes load timing. **34 passed**.
Reported raw line-entry coverage: batch **87/93 = 93.5%**, transcript adapter
**35/37 = 94.6%**. This tool counts some multiline function signature lines as
missing despite successful calls; percentages are its heuristic, not numeric
branch coverage. Batch real untriggered branches include non-text type guard
and skipping empty physical rows. Annotated outputs: `line-trace-batch.txt`,
`line-trace-transcript.txt`; summary `revised-line-coverage.txt`.

No pytest-cov/coverage package is installed; branch percentage is not claimed.
Risk coverage follows AC1 T01/T16/T18/T22; AC2 T02/T17; AC3 T04/T06–09/T14–15/T19;
AC4 T03/T05/T11/T22; AC5 T20/T21. T10 protects systemic failure policy, T13
unrelated behavior. Mutation detection tests oracle strength independently.

## 200-task overlap and corrected p95

All workers increment active under Lock before waiting at Barrier(201); the main
thread is participant201. The peak must be200, then all outcomes/counts checked.
Elapsed E2E starts immediately before pool.submit, so queue/start/barrier are
included. Service interval starts after the gate. For n=200, nearest-rank index
is `ceil(.95*200)-1 = 189`; deterministic vector test expects the 190th sample.

Canonical: **peak_inflight=200**, E2E p95 **45.781ms**, service p95 **0.260ms**,
200 x100 rows, target5000ms. Repeat E2E p95 **64.690ms** and **58.773ms**; each
repeat has 2 passing tests; `revised-load-repeat.txt`. These are separate observed
runs, not a pooled percentile or guaranteed production SLA. Peak counts barrier
waiters. GIL/preemption remain; there is no proof of 200 simultaneous parser CPU
executions, HTTP users, PostgreSQL performance or actual university payloads.

## Independently verified CI

Historical run [41469379892](https://github.com/5-Bit-System/SE_Project/actions/runs/41469379892)
at `e54f4bc` has `offline`, `postgres`, `hus_postgres` all success. Receipt:
`verified-historical-ci.json`. It protects existing behavior at that SHA, not
import persistence; it predates the revision. Revision run [41472036185](https://github.com/5-Bit-System/SE_Project/actions/runs/41472036185)
at `68b99df` independently has all three jobs success; receipt
`verified-revision-ci.json`. This validates the revised code plus existing DB
regressions, but still does not test import persistence. Do not label historical
CI as revised CI.

## Traceability / commits

| Requirement/risk | Logical cases | Source/test | Commits | Result |
|---|---|---|---|---|
| Domain AC1/AC2 | T16–18/T22 | importing/transcript.py; test_transcript_import.py | a1afd93 RED; 68b99df GREEN | 0->2 assertion, then pass |
| AC3 shape/major | T06/T14–15/T19 | batch.py/transcript.py; B/D tests | 68b99df | pass before effects |
| AC4 state | T01–05/T11/T22 | batch.py; B/D | 3443231 original; 68b99df revision | negation killed by3 tests |
| AC5 old rules | T20/T21 | existing transcript/rules; D | 68b99df | pass; original behavior preserved |
| Load | T12 | test_batch_performance.py | 68b99df | rank189, peak200, E2E45.781ms |
| Unrelated behavior | T13 | existing offline suite | 68b99df | 647 pass /90 deselected |

All raw files above live in `deliverables/evidence/`. No test accesses live
student data, runtime DB, credentials or VNU site. Branch remains unmerged.
