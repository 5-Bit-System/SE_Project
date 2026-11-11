# HUS Vector Query V4 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, task by task.

**Goal:** Enable explicit vector queries with canonical prefiltering and scoped lexical fallback.
**Architecture:** A lazy vector retriever implements the existing search interface. A verified local runtime handles tokenizer/model/Chroma; per-call immutable trace records provenance and fallback without changing answer JSON.
**Tech Stack:** Python 3.11, existing E5/Chroma hash-locked optional venv, pytest.
**Spec:** `docs/superpowers/specs/2026-11-09-hus-vector-query-v4-design.md` (user approved).

## Global Constraints

- Work in place on user-selected `hus-embedding-chromadb`; no commit, push, deployment or new worktree.
- Lexical stays default and does not load optional ML. F2, canonical data, V1–V3 artifacts and receipts remain unchanged.
- No download/build in requests, no external provider, no new Recall claim.
- Execute the approved design now; no additional plan approval checkpoint (user explicitly requested implementation).

## Review Focus

- A malicious/out-of-scope hit must invalidate the whole vector result, not silently shrink top-k.
- Canonical corruption must escape fallback handling.
- Duplicate parent passages must not create duplicate citations.
- Concurrent calls must not share mutable trace or tokenizer state.
- Missing configuration or optional packages must preserve scoped BM25 without creating a new index.

## Task 1 — Query boundary and scoped retriever

Files: new `app/hus/vector_query.py`, `tests/hus/test_vector_query.py`.
Interfaces: `HUSVectorRetriever(data, runtime_factory=...)`, `search(...) -> tuple[RetrievalHit, ...]`, `search_with_trace(...) -> VectorSearchResult`.
- [x] Write failing tests for prefilter, canonical scope, F3 opt-in, malformed hits, fallback reasons, dedup, canonical failure and per-call trace.
- [x] Run tests RED, then implement immutable trace/result and lazy verified runtime boundary.
- [x] Verify GREEN for successful/failing vector paths and lexical fallback with identical arguments.

## Task 2 — Real encoder and verified runtime

Files: new `app/hus/vector_runtime.py`, `tests/hus/test_vector_runtime.py`.
Interfaces: `LocalVectorRuntime(settings, data).query(query, where, top_k)`; typed vector failures carry stable reason codes.
- [x] Write failing tokenizer boundary tests (prefix/special/512/513), missing-index noncreation and malformed result identity checks.
- [x] Use existing verified V3 encoder's token graph/model/pooling without editing V3 artifacts or inference implementation.
- [x] Verify pinned index before opening existing collection, bind collection identity/config and verify query metadata. Serialize ML calls with a lock.
- [x] Run focused GREEN; real smoke uses the existing optional venv and cache with no downloads.

## Task 3 — Service/configuration integration

Files: `app/hus/retrieval_config.py`, `app/services/hus_service.py`, `app/hus/answering.py`, `.env.example`, config/service tests.
- [x] Update tests first: vector becomes available, hybrid reserved; lexical import guard and F2 bypass remain.
- [x] Add explicit optional vector paths/expected index ID, injectable retriever and lazy factory in service.
- [x] Prove canonical load failure is never swallowed and invalid mode remains a configuration error.

## Task 4 — Verification and handoff

Files: new V4 report/receipt, progress plan and project memory.
- [x] Run HUS and appropriate full offline/API/browser/Node/Ruff regression, record exact commands and outcomes.
- [x] Real query/reopen smoke and separate copied-index tamper/fallback checks; compare protected source/artifact hashes against HEAD.
- [x] Fresh technical review of the V4 diff; fix confirmed problems and rerun affected checks.
- [x] Record limitations, mark design implemented and leave all changes local.

## Execution Ledger

- Start: HEAD `586e460`; only approved design untracked. Historical V1/V2 IDs and V3 split preserved.
- Ruling: preserve existing checkout per explicit branch scope and local model/index resources; no extra worktree.
- Ruling: native inline execution follows the user's implementation instruction; final independent review only, no implementation delegation.
- RED/GREEN: query module 29 failing/1 fixture skip -> 29 passing/1 skip; expanded coverage removes the fixture skip and adds edition/concurrency cases. Runtime RED6 -> GREEN6, then 8 live tamper guards added. Service/config RED5 -> GREEN14. Combined scoped suite: 60 passed.
- Real acceptance: 8 F1/F3 queries in two processes, identical parent rankings; over-budget and copied-manifest tamper fallback verified. Original V3 index hashes (8 files) unchanged. HTTP service smoke: 12 answered cases, 8 vector calls, zero F2 vector calls, F3 opt-out blocked.
- Independent technical AI review: no confirmed Critical/Important/Minor; no implementation edits from reviewer.
- Environment ruling: default Python lacks argon2; use existing CI venv without installing into core. Initial full default-Python collection failed with 26 import errors; default-Python HUS run had 12 import-related failures. Correct CI venv run on original HEAD: 2167 passed/2 skipped (not the final new-base result).
- Checkout changed externally at 2026-11-10 00:08+07:00 from 586e460 to 1ad85e3, discarding tracked V4 integration. User said continue; retained current HEAD, reapplied only V4 integration and reran final checks on that base. Did not restore/rewrite branch history.
- Scratch API helper initially used `.chunk` on a RAGChunk; fixed helper assertion. A subsequent HTTP503 was traced to the checkout reset removing vector mode availability, and resolved by reapplying the approved integration. Final HTTP smoke passed.

- Final current-base verification: HEAD1ad85e3+WIP,2067passed/2skipped/90deselected;50Chromium,5Node,Ruff and diff checks passed. Protected data/model/lock inputs unchanged; current mode default remains lexical.
