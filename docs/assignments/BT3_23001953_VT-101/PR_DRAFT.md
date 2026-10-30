Add filtered course search with stable pagination while preserving the existing
GET /courses array contract. This is Nguyễn Công Việt's individual BT3 VT-101;
it awaits team review and must not be merged as part of this task.

The additive GET /courses/search endpoint filters one validated catalog snapshot,
orders by code/name/credits with code tie-breakers, then pages the result. Existing
Course fields, source status and 404/422/503/500 behavior remain in place.

Validation:619 offline tests passed (79 PostgreSQL cases deselected),46 focused
BT3 tests passed, Ruff/builders/analytics and real-browser API smoke passed.
The intentional swallowed-exception mutant was killed by3 assertions; the correct
branch remains green. Service coverage12/12lines and4/4branches; broader route
coverage and limits are explicitly reported.

Performance remains a known limitation:100 concurrent HTTP workers,6000 measured
requests per configuration, all responses correct. Default p95=3.535/1.698/2.590s;
8-thread experiment=3.294/2.501/2.743s. Both configurations fail the requirement
that every run remain≤3s. These synthetic JSON results do not establish production
PostgreSQL/VNU capacity. See docs/assignments/BT3_23001953_VT-101/README.md and REPORT.md
for commands, raw CSV, RED/GREEN, mutation and AI disclosure. No PDF, migration,
shared-data load test or main merge is included.
