# VT-100 risk-based test strategy

**Highest risk:** partial success is accidentally converted into all-or-nothing behavior, losing valid records. Secondary risk: malformed batch input causes side effects before rejection. Protect unchanged product behavior because the repository has no import feature to extend: scope the code to a new isolated harness and run the pre-existing offline suite.

## Levels

- **Unit (primary):** CSV shape/limits, state outcomes, counts and independent row handling. Fast and deterministic.
- **Integration/API:** an API test is deliberately not applicable: no import endpoint, target entity, auth contract or persistence schema was specified. Adding one would manufacture a product contract. If a real importer is later specified, test per-row DB transaction boundaries and response contract with the real test database.
- **E2E:** not applicable to this backend-only harness; there is no user workflow or import UI. Do not create a UI solely for this assignment.
- **Regression:** existing offline suite checks unrelated behavior after adding an isolated package.
- **Load:** synthetic in-process 200 concurrent import tasks; records p95 but does not model HTTP, DB, real payload/network or deployment resources.

## State-transition model and data selection

Per row: `PENDING → IMPORTED` or `PENDING → REJECTED`; terminal outcomes cannot transition again. Batch: `VALIDATING → REJECTED_BATCH` on malformed/over-limit structure before a handler call; otherwise `PROCESSING → COMPLETED` (all imports), `PROCESSING → PARTIAL` (mixed outcomes), or `PROCESSING → FAILED` (zero imports). Test data explicitly covers every terminal batch state, a valid row before and after a rejected row, zero rows, and a malformed batch with a handler spy. This checks ordering and side effects as well as values. Invalid row payload and handler error are separate rejection causes.

## Test cases

| ID | Risk / criterion | Level | Precondition / input | Expected | Priority |
|---|---|---|---|---|---|
| T01 | AC1 all valid | Unit | Two valid CSV rows | Both handler calls once, `completed`, 2 imported | P1 |
| T02 | AC2 partial success | Unit | Valid, handler-rejected, valid | First/last persist; middle rejected; `partial` | P0 |
| T03 | AC4 no successes | Unit | Every handler call rejects | `failed`, rejected count exact | P1 |
| T04 | State boundary | Unit | Empty CSV | `REJECTED_BATCH`, no calls | P1 |
| T05 | State boundary | Unit | Header-only CSV | Completed with 0 rows; no false failures | P2 |
| T06 | Negative: ambiguous schema | Unit | Duplicate or blank header | Reject before first handler call | P0 |
| T07 | Negative: malformed CSV | Unit | Parser-detectable malformed quoting | Reject before handler calls | P1 |
| T08 | Failure path: oversized | Unit | >1 MiB UTF-8 input | Reject before row processing | P1 |
| T09 | Failure path: row limit | Unit | 5,001 data rows | Reject before handler processing | P1 |
| T10 | AC2 order/duplicate safety | Unit | One row with validation failure between successes | No duplicate call; later valid row attempted | P0 |
| T11 | AC4 summary invariant | Unit | Mixed result set | Counts sum to rows; status agrees with counts | P1 |
| T12 | NFR3 load target | Synthetic load | 200 independent tasks, 100 rows/task, deterministic handler | Record p95; compare to 5.0s, qualify scope | P1 |
| T13 | Unrelated behavior risk | Regression | Existing offline suite | No unrelated regressions | P0 |

## Not needed

No external network/API mocks (the harness has no network dependency); no browser test or DB integration until a production import contract exists; no random/fuzz seed in the required suite because it would weaken repeatability. A future property-based parser test may add value after a real format contract is agreed.

## Flaky-test review

1. **Clock/performance:** load test uses `perf_counter`, avoids sleep and asserts completion/collected p95 with a tolerance only against the stated target; host contention can vary latency, so report machine/env and treat a near-threshold result as inconclusive.
2. **Shared state/order:** each task receives its own batch, rows and outcome list; no global counters, database or fixture mutation. Repeat serial test in reversed test order to detect leakage.
3. **Network/randomness:** no outbound requests or random test data; deterministic IDs/rows. Thus network and random flake risks are removed for this harness, not for a future HTTP/DB importer.
