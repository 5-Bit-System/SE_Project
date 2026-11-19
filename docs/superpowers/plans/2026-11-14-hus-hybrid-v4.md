# Hybrid v4 implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement inline, task by task.

**Goal:** Build a separate real E5/Chroma index for v4 and make demo hybrid selectable and verifiable.

**Architecture:** Reuse existing contract, passage, index and BM25/RRF implementations. A checked-in retrieval profile pins repository-relative artifact paths and expected index ID outside the database. Lexical stays the default; explicit hybrid uses the new profile and a local model cache. F2 stays structured. No Gemini calls.

**Tech Stack:** Windows64/Python3.11, pinned local E5 CPU/Chroma, FastAPI, existing pytest suite.

**Spec:** [Roadmap sections4–5](../../RAG_PROGRESS_AND_NEXT_PLAN.md).

## Global constraints

- Work in existing hus-llm-rag checkout; preserve all previous uncommitted work, old index/contracts, v4 and frozen evaluations.
- No stage/commit/push/PR/deploy, secret/template reads or live Gemini calls.
- Reuse verified local model and locked optional environment; do not weaken identity/token/filter checks.
- Hybrid must filter same scope/F3 consent; vector-to-lexical retrieval fallback differs from LLM offline-after429.
- Model/cache and binary index stay ignored; documentation supports relative paths and clean dependency installation.

## Review focus

- Wrong v3 artifact with v4 data must fail validation, not count as a hybrid success.
- Explicit hybrid must prove actual_mode=hybrid; requested mode alone is insufficient.
- Lexical must run without optional ML imports or a cache.
- Scope/F3 consent/F2 facts must remain intact with real index.
- Missing cache/dependencies or stale pins must give actionable preflight failure and preserve old outputs.

## Tasks

- [x] 1. Record old artifact hashes; verify existing model/dependencies; generate fresh v4 contract and token-bounded passages; build/reopen real Chroma index using existing tools. Outputs under data/hus/vector_contracts, vector_passages, vector_indexes with e5_small_v4_20261114 names; ledger under ignored backups/hus_hybrid_v4_20261114.
- [x] 2. TDD optional contract/passage paths in retrieval settings/runtime, retaining old defaults. Add profile loader/configuration in app/hus/retrieval_profile.py with pinned paths/ID, local default cache and lazy lexical path. Tests tests/hus/test_hybrid_v4_profile.py.
- [x] 3. TDD --retrieval lexical|hybrid and --model-cache plus no-key --check in tools/run_hus_llm.py and tools/run_hus_rag.py. Keep existing lexical check/wrapper behavior. Hybrid preflight proves both legs before serving; expose requested retrieval mode in /hus/config. Tests reuse launcher tests and new profile tests.
- [x] 4. Verify actual v4 hybrid retrieval/scopes/F2/F3 consent, restart and rollback using local CPU and current index; compare a small same-snapshot lexical/hybrid set without regrading old runs. Record trace/latency/limitations, not semantic acceptance.
- [x] 5. Run related regression and review. Update quickstart/README/roadmap with reproducible commands and remaining limits. No commits per user preference.

## Execution rulings / ledger

Inline execution authorized by the selected roadmap row. Use current workspace because the required baseline is its local uncommitted source and v4 artifacts. Existing model cache is backups/vector_index_v3_20261109/model, optional interpreter in its venv; no new network required. Runtime currently hardcodes v3 contract/passages, so new explicit profile-bound paths must be added without mutating old artifacts.
