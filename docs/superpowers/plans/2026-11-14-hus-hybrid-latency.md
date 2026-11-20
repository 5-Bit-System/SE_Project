# Hybrid latency profiling and optimization plan

> **For agentic workers:** Use superpowers:executing-plans inline; retain existing hus-llm-rag workspace, no Git publication.

**Goal:** Measure and reduce local hybrid latency without removing identity/scope checks or changing evidence/ranking.

**Architecture:** Measure nested spans in an external diagnostic process; optimize only demonstrated redundant canonical-copy work. Retain per-query full snapshot fingerprints, full persisted inventory read/serialization, index pin/config checks, E5/token budgets and RRF20+20→5. Compare legacy and optimized signature implementations on one warmed runtime with counterbalanced question order.

**Tech Stack:** Existing Windows/Python3.11, local E5/Chroma; no packages/downloads or Google calls.

**Spec:** User row4 latency profiling and new same-snapshot run. Source of questions remains AI-drafted exposed dev pack; no team questions supplied, no independent quality score.

## Constraints and review focus

- Keep all old run/gold/review/CSV/index/model/release artifacts unchanged.
- Do not skip pin/scope/identity/inventory checks, silently truncate query, cache away mutation checks or tune ranking.
- Report cold separately; do not mix no-search cases into search medians or claim Gemini latency.
- Do not attribute old/new content changes caused by router repairs to a retrieval speed refactor.
- New protected metadata fields/nested mutations must retain the same identity hash behavior.

## Task 1 — Profile unchanged runtime

- [x] Capture baseline spans for encoding, canonical_signature, index_check, inventory_read, inventory_json_serialization, Chroma query and result resolution on5 exposed search cases.
- [x] Verify actualhybrid and frozen v4/index; cold startup separate.
- [x] Findings: canonical signatures total4.88–5.27s of6.28–6.64s; encoder.039–.053s; inventory read.339–.382s/JSON.593–.648s. Keep inventory checks unchanged, optimize redundant recursive dataclass conversion.

## Task 2 — Preserve complete signature with less copying

- [x] Save original vector_query.py in ignored ledger before editing; pin old artifact hashes.
- [x] Add RED tests for `_canonical_payload(data)`: complete legacy-equivalent mapping, defensive isolation from snapshot metadata, and nested provenance mutation behavior.
- [x] Implement `_canonical_payload` via shallow dataclass field mapping over already-independent `data.chunks()` copies; use same digest_json serialization and release/chunk order. Keep existing `_canonical_signature` error boundary and both pre/post checks.
- [x] Run vector/hybrid/embedding/integrity regressions and verify old/new hash equivalence.

## Task 3 — New same-snapshot measurement and review

- [x] Reuse original20questions as exposed dev, freeze new measurement protocol/code and baseline function SHA; do not change gold or old scores.
- [x] In a fresh process warm native runtime once; collect lexical, legacy-hybrid and optimized-hybrid outcomes, counterbalance hybrid order. Record per-stage spans and report search/no-search groups separately; compare full response/hit IDs/trace scopes, not only timing.
- [ ] Fresh reviewer per requesting-code-review: attempted, unavailable because of service usage limit. Not completed; no independent review claim. Root inspected integrity and measurements instead.
- [x] Verify old artifact hashes, relevant tests and local lightweight --check; update report/quickstart/roadmap/memory with measured limits and no human quality claim.

## Execution record

- Before profile: data/hus/evaluation/runs/hybrid_latency_profile_before_20261114_r1. Cold139.074s; five warm retrieval queries6.276–6.644s. No runtime changes during capture.
- Ruling: focus canonical serialization only. Repeated dataclasses.asdict recursively clones nested metadata even though public chunks() already returns a deep independent snapshot. Eliminating that second copy preserves canonical bytes; don't optimize by reusing a cached digest or weakening full inventory verification.
- Completed 2026-11-15. Five new tests observed RED then green; final related suite 173 passed/1 skipped (Windows symlink permission), old Starlette warning. Ruff clean, lightweight lexical/LLM-off --check passed20API/2124menu/4sourcehash.
- Native paired run hybrid_latency_paired_20261114_r1:20exposed questions/60observations,10search+10no-search per mode. Median search RAG6.5908634->3.3273057s (-49.5164%). All20hybrid pairs exact response+trace equal;37protected logical files unchanged. Canonical4checks/query and full inventory verification retained. Cold56.484s recorded separately, not causal comparison with139.074s.
- Original source saved at .cache/hus/latency_profile_20261114/vector_query_before.py, SHA173a99f6b9c7328dbf28ff61385b989aa14fcd5534b75d30ee2dceaa61b9b361. Recreate legacy signature only in measurement context; production retains optimized code. Never restore whole workspace or overwrite historical artifacts.
- Diagnostic writers profile_before.py/measure.py/summarize.py EXECUTED once; do not rerun. New review CSV editable; creation receipt is not a reason to restore human edits. Google0, no secrets/config/key reads or publication. Group content review pending; old prepared live code pins stale after this code change, prepare a new revision before a future approved call.
- Report docs/RAG_HYBRID_LATENCY_2026_11_15.md; roadmap and quickstart updated. Fresh review failed due usage limit and is explicitly disclosed; no workaround retries.
