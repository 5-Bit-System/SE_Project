# Test-first and mutation evidence

## Baseline / red run

- Baseline: `5239b7333a8f8cdf0f919e6b0505af0def99fe23`.
- Branch: `bt3/23001946-vt100`.
- Command before implementation: `conda run --no-capture-output -n SE_Project python -m pytest -q tests/importing/test_batch.py`.
- Exit: 2 during collection. Observed: `ModuleNotFoundError: No module named 'app.importing.batch'`.
- Interpretation: the proposed isolated import boundary does not exist at baseline. The test fails for the intended missing feature. It does not yet demonstrate a business assertion against defective code; after creating the implementation, mutation testing below supplies that stronger evidence.
- Full captured console output: `deliverables/evidence/test-first-red.txt`.

## Mutation experiment

Mutation: temporarily invert the batch state decision that identifies a mixed success/error result (`if imported and rejected` to `if imported or rejected`). Run the partial-success and all-valid state assertions; the suite must fail because the mixed state is mislabeled (and/or all-valid status becomes wrong). Restore the source immediately, rerun the full unit suite, and record exact command/output and hashes here. No mutation is committed.

## Pass / coverage / load evidence

Added after implementation. Record exact test command, output, coverage tool/limitations, and the isolated synthetic 200-task p95 experiment here. A report must not claim a production SLA from an in-process harness.

## Mutation result (temporary, restored)

- Mutated rule: `if imported and rejected` → `if imported or rejected` when selecting `PARTIAL`.
- Command: pytest on `test_middle_row_failure_does_not_lose_valid_rows_before_or_after` and `test_all_valid_rows_reach_handler_once_and_complete`.
- Result: **1 failed, 1 passed**, exit 1. The all-valid case expected `COMPLETED` but mutation returned `PARTIAL`. The original file was restored in a `finally` block; evidence: `deliverables/evidence/mutation-killed.txt`.
- After restoration, import unit/performance suite: **12 passed**. The mixed valid-invalid-valid test asserts that both valid callbacks ran and the failed row alone is rejected.

## Green and regression result

- Import tests: `conda run --no-capture-output -n SE_Project python -m pytest -q tests/importing/test_batch.py tests/importing/test_batch_performance.py -s` → **12 passed**; synthetic p95 **0.317 ms** for 200 concurrent tasks × 100 rows/task, target 5,000 ms.
- Existing offline regression: `conda run --no-capture-output -n SE_Project python -m pytest -q tests -m 'not postgres and not hus_postgres and not full_catalog_acceptance'` → **623 passed, 90 deselected**, one existing Starlette/httpx deprecation warning.
- Order/shared state check: two import transition tests run in both CLI orders → 2 passed each run (0.08 s, 0.09 s).
- `ruff check app/importing tests/importing` passes. No coverage plugin/module is installed in Conda `SE_Project`; no numeric line/branch coverage is claimed. By reviewed control-flow branches, tests execute empty and valid input; blank/duplicate headers; malformed CSV; byte and row limits; width mismatch; imported/rejected/partial/failed states; typed row errors; and propagated systemic errors. Residual unmeasured branches include invalid Unicode and field-width mismatch are both covered (invalid Unicode isn't directly triggered); exceptionally large multiline fields are size-bounded before parsing.

## Traceability

| Requirement/risk | Tests | Code | Commits | Evidence |
|---|---|---|---|---|
| AC1 per-row outcome | T01 | `app/importing/batch.py` | implementation commit listed in final report | import green log |
| AC2 valid rows survive bad row | T02, T10 | row loop catches only `RowImportError` | implementation commit | T02 + mutation log |
| AC3 reject unsafe batch before side effects | T04, T06–T09 | `_parse_records` | implementation commit | import green log |
| AC4 honest terminal summary | T03, T05, T11 | `BatchStatus`, `BatchResult` | implementation commit | mutation log |
| NFR1 bounds | T08, T09 | `MAX_CSV_BYTES`, `MAX_ROWS` | implementation commit | import green log |
| NFR3 target exercise | T12 | synthetic concurrent harness | implementation commit | printed p95 above |
| unrelated regression | T13 | isolated new package | implementation commit | 623-pass offline run |
