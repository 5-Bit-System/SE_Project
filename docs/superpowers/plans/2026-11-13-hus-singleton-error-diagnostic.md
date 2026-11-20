# Singleton error diagnostic — offline repair

> **For agentic workers:** Use superpowers:executing-plans inline with a final read-only code review. No Git publication or provider calls.

**Goal:** Recognize the observed top-level singleton error array while retaining fixed-label privacy and fallback contracts.

**Architecture:** Normalize exactly one dictionary in a top-level list before the existing allowlisted classifier. Keep object handling, HTTP status gates, body/message bounds and completion parsing unchanged.

**Tech Stack:** Python 3.11, Pydantic, HTTPX MockTransport, pytest.

**Spec:** User-selected roadmap item “Thay key bị chặn, sửa diagnostic rồi L5/L6”, and sealed Google diagnostic r2 describing singleton-array/PERMISSION_DENIED/key_reported_leaked. No raw live body is available or reconstructed.

## Constraints and review focus

- Existing `hus-llm-rag` WIP, local-only; no stage/commit/push/PR/Actions/deploy.
- No secret/template/env/key/billing/account/DB access, no network/provider calls or new live budget. Synthetic test values only.
- Exactly singleton dictionary arrays; reject empty/multiple/non-object/nested arrays. Do not recursively search arbitrary content or select one error from multiple entries.
- Retain fixed statuses/access labels only; never error text/unknown IDs/headers. Existing 16KiB body and 8192-character message guards remain.
- Preserve unrelated-status behavior, controls, canonical answers/citations and bounded circuit/budget fallback. A JSON array on HTTP200 is still an invalid completion.
- This changes diagnostic classification, not provider permissions or model quality. Old artifacts/gold/reviews remain immutable; changed runtime pins become stale.

## Steps

1. [x] Snapshot protected inputs; add RED regressions for singleton class/privacy, malformed arrays, message/body bounds, HTTP status gate, success array rejection and measurement budget/fallback.
2. [x] Apply minimal normalization in `app/hus/llm/diagnostics.py`; GREEN focused tests, then relevant LLM suite. Final fresh-context code review and scoped Ruff/diff checks.
3. [x] Verify old hashes/cached replay, explicitly record stale A7/L5 pins; no new inference/cohort. Seal separate QA receipt; update diagnostic doc/roadmap/project memory and operator next steps.

Ruling: User supplied the complete narrow repair and selected it explicitly; proceed without repeated design/worktree/permission questions. Key rotation and any live validation remain separate operator/budget steps.
