# HUS Hybrid Retrieval V5 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, task by task.

**Goal:** Implement pinned RRF hybrid retrieval and replayable three-mode measurements.
**Architecture:** A separate adapter consumes BM25 and verified V4 vector results. A new evaluator stores leg pools, final hits, response/source audits, pins and process resource measurements without modifying historical evaluators.
**Tech Stack:** Python3.11, pytest, existing optional E5/Chroma venv, standard-library resource APIs.
**Spec:** `docs/superpowers/specs/2026-11-10-hus-hybrid-retrieval-v5-design.md` (user approved).

## Global Constraints

- Current branch hus-embedding-chromadb, HEAD1ad85e3+V4WIP; no commit/push/deploy or new worktree.
- Policy: lexical20/vector20passages, parent rank after dedup, RRF60/equal weights/final5/tie parentID.
- Preserve source/model/index/lock, V4 implementation/evidence and old evaluators; only service/config integrate hybrid.
- Default lexical, same routing/gate/citation/F2 lookup, no provider or downloads.

## Review Focus

- Vector fallback must not double-count lexical votes.
- Candidate pool cannot silently become final Recall@5 input.
- Failed/no-call queries remain in metric denominators and cannot masquerade as live vector successes.
- Pin/replay mismatches and source/gold mutations fail before a run is sealed.
- Separate process resource accounting and identical 20-to-5 comparator budgets prevent misleading comparisons.

## Task 1 — Hybrid policy, adapter and service

Files: new app/hus/hybrid_retrieval.py, tests/hus/test_hybrid_retrieval.py; config/service/.env and focused tests.
Interfaces: frozen policy/trace/result, HUSHybridRetriever(data, vector=None, mode='hybrid').search/search_with_trace.
- [x] RED tests for RRF, dedup/rank/tie, fallback, canonical/scope/opt-in, pool/final trace and concurrency.
- [x] Implement adapter with canonical validation, pinned policy and V5 lexical/vector comparators.
- [x] Enable hybrid explicitly in config/service; lexical still avoids vector imports, F2 never starts ML.
- [x] Focused GREEN and code lint.

## Task 2 — Versioned metrics and evaluator

Files: new tools/hus_rag_metrics_v3.py, tools/evaluate_hus_hybrid.py and tests/hus/test_hybrid_evaluation.py.
- [x] RED tests proving final-only Recall/MRR, no-call misses, fallback accounting, trace corruption and replay/output guards.
- [x] Implement frozen-input run/replay, HTTP capture, source auditor reuse, gold-after-prediction boundary and process memory APIs.
- [x] Pin app/evaluator/model/index/pack/policy and reject drift before sealing new outputs.
- [x] Focused GREEN; preserve all historical evaluator bytes.

## Task 3 — Freeze dev pack and measure

Files: new V5 dev pack/run directories and ignored experiment helpers/logs.
- [x] Freeze36newdev cases (8permajor+1F2permajor), source-bound gold and exposure/tags before inference.
- [x] Run lexical/vector/hybrid separately on dev96/contracts/newpack under the same code/model/index/policy.
- [x] Replay results, compare parent-only final5 metrics and guards; record resources/fallbacks and semantic-review coverage honestly.
- [x] Keep lexical unless pinned results satisfy the proposed quality rule; no activation.

## Task 4 — Review, regression and handoff

- [x] Independent technical review (per requesting-code-review skill), one fix pass with RED/GREEN if needed.
- [x] Full appropriate offline regression, Chromium50, Node5, Ruff; protected file/index hashes unchanged.
- [x] New V5 report/receipt, update progress/memory/design/ledger, verify final pins and leave changes local.

## Execution Ledger

- Native inline execution follows explicit user command; no new approval checkpoint.
- User-selected existing checkout and local caches preserved. V4 WIP is baseline evidence, not a clean-tree requirement.
- TDD: hybrid14RED->14GREEN; configuration2RED->14GREEN; evaluator14RED->14GREEN; comparison4RED->4GREEN. Additional fixes bring evaluator/comparison22GREEN.
- Independent AI review found2Important/no confirmed Minor: suite order/multiplicity absent from pins, semantic-marker-only recommendation. Reproduced both; fixed with suite_sha256/duplicate-pack rejection/source reconstruction and complete semantic coverage/non-regression requirements. Additional self-audit RED test found nested fallback could masquerade as vector RRF; fixed strict nested/top-level consistency. No independent re-review claimed.
- Frozen36source-derived V5dev cases before inference, plus existing96dev/28contracts. Probe lexical36cases exposed5false refusals with16/16retrieval anchors; did not alter gold or gate after observing this. Probe is historical pre-fix evaluator evidence, excluded from final comparison.
- All final modes use same160cases, code/data/model/index/policy/environment pins and separate sequential processes; no concurrent heavy test suite during timing. Default lexical and original model/index retained.

- Final: 2103pytestpass/2skip/90deselected,50Chromium,5Node,Ruff;480predictions replay,12real hybrid HTTP plus fallback/canonical503. Default lexical because semantic review pending; no commit/push/deploy. Prototype probe preserved under ignored backups/probe_lexical_pre_review.
