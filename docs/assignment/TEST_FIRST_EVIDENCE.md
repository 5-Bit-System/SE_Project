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
