# DEV-Q027 career context coverage implementation plan

> **For agentic workers:** Use superpowers:executing-plans, systematic-debugging, test-driven-development, requesting-code-review and verification-before-completion. Execute the selected progress-plan step inline; no commit/push/deploy.

**Goal:** Answer the exposed enterprise-career question with its source-backed roles instead of a passage naming unrelated workplaces; preserve A2 as measured.

**Spec:** User-selected step 1 in `docs/RAG_PROGRESS_AND_NEXT_PLAN.md`, sections 3 and 5.1. One scoped source must cover the request; no facts, source status or official validity may be invented.

**Diagnosis:** BM25 returns the generic 2015 PDF first, the enterprise-role web paragraph second, and its teaching continuation third. `supported_hits` strips all enterprise/context words as request grammar and takes the first eligible source group. This is post-retrieval context coverage, not a missing top-5 source.

**Architecture / choice:** Keep the existing lexical coverage gate and source grouping. For F1 careers only, preserve active question phrases `doanh nghiep` and `cong ty` as exact, accent-insensitive workplace requirements in source bodies. Check these across passages within one existing `_source_scope` group, never titles/metadata or different groups. Keep all continuations needed by the current specific-token coverage rule. Do not hardcode DEV-Q027 IDs, source IDs or job names. Alternative re-ranking alone would still accept a source without the requested workplace; replacing BM25/vector/LLM would confound the approved isolated fix.

**Global constraints:** Same crawldata WIP and v3 release; protect all 895 old files except the one authorized implementation file `app/hus/answer_support.py`. Add a new test module only. Freeze exposed dev cases before tuning. Keep A2 runs, gold, evaluator/scorer, reviews, source/release, F2 raw/status and both AI guards unchanged. Use new output paths. AI review remains AI, never independent human evidence. Current user-named branch/WIP is the integration target; no new worktree or commits, preserve a before-image and hash ledger instead.

## Review focus

- Context split across same-source passages must retain roles/continuations; a title alone cannot supply workplace evidence.
- Distinct source/review/edition/variant/major/field groups cannot complete each other.
- Negated clauses cannot add a positive workplace requirement; factual/number/skill requirements remain enforced.
- Explicit edition cannot borrow the enterprise paragraph from unknown edition; missing context fails closed.
- Real source quotations/citations, F2 contracts, F3 review/opt-in and no provider calls remain unchanged.

## Task 1 — Exposed regression and minimal coverage fix

- [x] Freeze a new exposed development case pack before runtime changes; capture code and protected-file hashes plus Q027 actual top-5 trace.
- [x] Add `tests/hus/test_career_context_coverage.py`: exact Q027 source roles and trace membership, enterprise/company phrasing, header-only/scattered-token rejection, negation, same-group multi-chunk completion, isolated source scopes, edition guards and existing domain requirements.
- [x] RED: run the new tests, inspect actual assertions failing because the generic group is selected or context omitted.
- [x] GREEN: change only `app/hus/answer_support.py`; extract active workplace phrases and require exact body support in one source group before its current token coverage check. Run new plus existing support/routing/chat contract tests.

## Task 2 — Review, measure and document

- [x] Fresh technical AI review of the scoped before-image diff and tests; handle Critical/Important findings by RED→GREEN, record any rulings/minors.
- [x] Final offline suite, Node and Chromium/API/source regression; pin final code/data/test/dependency/environment across commands.
- [x] New BM25 runs for dev96, full H2 exposed56 and contracts28, plus the new dev regression pack. Reuse the unchanged A2 evaluator. Persist source audits, layer metrics, latency and cached replay verification; report old-vs-new response changes.
- [x] Read/review changed answers with source/gold; use new strictly bound AI review records/overlays, not copied A2 decisions. Unchanged responses may be reported as byte-identical to previously AI-reviewed A2 outputs with explicit inherited provenance rather than claimed new independent review.
- [x] Verify protected hashes and A2 archive/run/receipt integrity, write a new report/receipt, update progress and project memory. No baseline rewrites, vector/LLM installation, source promotion or publication.

## Execution ledger

- Setup: user chose the existing approved defect-fix step. Diagnosis traced against actual selected v3; all-before ledger and 895 protected hashes captured in `backups/dev_q027_20261104/`. Implementation stays in the explicitly requested crawldata WIP; local history is not committed.
- Task 1: complete, scoped suite 263 passed. First corrected RED:21 failed/8 passed; retaining context citations then RED:2 failed/27 passed, GREEN in full scoped suite. An initial test used a nonexistent citation attribute; fixed before final RED. Domain isolation uses an unknown topic `alpha`, because the existing grammar also neutralizes tokens of `thống kê`; no unrelated grammar rewrite in this fix.
- Ruling: keep role-only routing probe C003 in its original frozen dev6 pack/run; freeze an r2 variant adding the career cue `công việc` before runtime tuning, without rewriting the original. The role-only route-to-introduction gap is pre-existing and outside this post-retrieval change; cost: that wording remains unsupported until a separate routing fix. Report both packs and do not claim all natural phrasings are covered.
- Final review: one Important introduced refusal/context regression, no other Critical/Important or Minor findings. Fixed by bounded workplace-refusal removal only for the new context extraction, not factual-token coverage: review regression RED9 failed/30 passed, final scoped GREEN273 passed (39 new). Factual negation and later positive requests retain their requirements. Initial full-suite attempt was interrupted to address the finding; it is not a passing run. Final verification uses a separate `verification_final` directory.
- Final: Ruling: reviewer set aside unrelated WIP and general Vietnamese negation semantics — retain the one-file fix and existing lexical contract, with final broad regression; cost: untested phrasings can still be unsupported, no claim of general language understanding.
- Final: Ruling: reviewer set aside baseline artifact integrity and full-suite results — root verifies protected hashes and runs final pinned regression/measurements rather than inferring them from the review; cost: no completion claim until those checks pass.
- Task 2: complete,1833offline/90deselected,50Chromium,5Node,Ruffpass;895protected unchanged. Four fresh measurements+AIoverlays replay8/8. Only Q027 changed in dev96; H2/contracts unchanged, allretrieval traces identical. New AIreading11/inherited179 with explicit hashes. Dev AIcomplete64/64; H2Recall20/20,F2raw15/16 vs source16/16. Source/data/oldgold/scorer/A2 artifacts remain unchanged.
- Ruling: AI review marks DEV6-C007 completeness/fulfillment fail despite complete positive enterprise quote because excluded teaching is still present. Keep this pre-existing general-exclusion behavior visible, along with the role-only routing gap, for a separate dev fix; cost: that exclusion phrasing remains imperfect. Dev6r2 semantic7/8,not10/10overall. No source/evaluator changes to improve the score.
