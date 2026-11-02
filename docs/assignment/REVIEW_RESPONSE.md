# VT-100 — response to the supplied trial review

The supplied score is unofficial; this revision addresses findings with runnable
evidence rather than promising a new score. Branch stays unmerged for team review.

| Finding | Revision | Evidence |
|---|---|---|
| Generic-only import | Real TranscriptRecord/StudentTranscript adapter and existing eligibility consumer | D tests; AC5 T20/T21; 68b99df |
| Weak collection RED | Second iteration starts from executable placeholder, failing expected2 vs actual0 | a1afd93; transcript-red.txt |
| Mutation not direct inversion | Direct `not (imported and rejected)` mutation; exact source restored | mutation-boolean-negation.txt;3 assertion failures |
| Blank-header/width not directly tested | Explicit whitespace header cell; narrow/wide row after valid input; also invalid Unicode | T06/T14/T15 in B; focused GREEN |
| T10 mismatch / 0/0 ambiguity | T10 now consistently means OSError abort; AC4 failed requires rejected>0 | spec, strategy, evidence and PDF aligned |
| p95 index / overlap / queue omission | rank index189; 200 workers meet barrier; locked peak200; submit-to-complete E2E | P tests; canonical45.781ms; repeats64.690/58.773ms |
| Coverage without instrumentation | Stdlib line trace93.5%/94.6%, limitations and untested branches explicit | revised-line-coverage.txt and annotated source |
| Current counts inconsistent | Current focused36, offline647/90; old logs labelled historical | revised-summary.json; evidence docs |
| Missing current CI proof | Verified revised code SHA68b99df has offline/postgres/hus_postgres success | verified-revision-ci.json; run41472036185 |
| Prompt only summarized | Original full user assignment saved; exact new revision instruction recorded before code | ORIGINAL_USER_PROMPT.txt; REVISION_PLAN.md; PDF appendix |
| Reflection over limit | 305 whitespace words in source AND extracted PDF | REFLECTION.md; report-validation.json |
| Sparse forced page sections | Continuous main layout;5 main pages and2 appendix pages; tables repeat headers | HTML/PDF; inspected page renders |

Residual scope: no import HTTP endpoint, durable DB writes, authorization,
per-row transaction/retry/idempotency or production HTTP-load claim. Existing
PostgreSQL CI jobs test existing persistence, not writes by this in-memory adapter.
Historical internal AI prompt cannot be reconstructed exactly; it stays labelled
as a summary. New exact instruction is explicitly agent-authored, not a fabricated
student quotation. Student should review the AI-assisted reflection before submission.
