# Compact LLM v3 implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline; user approved detailed design and offline implementation. No additional approval handoff or Google calls.

**Goal:** Implement source-leaf IDs and backend-controlled list layout for F1/F3 without weakening coverage or changing F2/canonical RAG.
**Architecture:** Build a versioned immutable document from validated v1 evidence. V3 wire carries each source leaf once; output has only ID/text. A new validator restores literal prefixes, validates each leaf against its original authority, then renders the original skeleton. Keep legacy evidence/output validation for historical/unit consumers and select v3 in the default adapter and new measurement preparation.
**Tech Stack:** Existing Python/Pydantic/HTTPX/pytest and current FastAPI demo; no dependencies.
**Spec:** [Approved compact-layout design](../specs/2026-11-11-hus-llm-compact-layout-design.md).

## Global constraints

- Work in existing user-named hus-llm-rag WIP; snapshot before changes. No commit/push/deploy, no branch migration, no env/template/key reads or provider calls.
- Keep CURRENT v4, source/retrieval/answerer/routing/UI/canonical facts/review unchanged; lexical and LLM default off. No repair of A7 baseline failures during this implementation.
- Fixed limits: 12,000 prompt chars, 8,192 raw chars, 1,024 output tokens; 64 leaves/128 coverage units/document, source and returned leaf text <=3,000 chars, HTTPX20s per phase, one in-flight/process, no retry/redirect/stream.
- F1/F3 retain every selected source unit with v2 word-order/atom/negation/condition/symbol checks. Backend owns citation IDs, offsets, literal indentation/list/heading prefixes and display order. No partial display or truncation.
- F2 still returns HUSF2Presentation and exact canonical content. Existing L2/API opt-ins/warnings and disabled response shape unchanged.
- Historical runs/gold/reviews/receipts immutable; old replay does not revalidate using v3. No claim that mock/exact-copy acceptance proves token feasibility, entailment or better phrasing.

## Review focus

- CR/Unicode line separators split a coverage unit or prefix stripping loses a symbol/number.
- Expanded local anchor grants neighboring leaf atoms or words can be borrowed across leaf/citation.
- Duplicate/missing/foreign IDs, model newlines or list syntax bypass backend layout.
- Diagnostic metadata leaks raw model/error content or old measurement prep hashes a different protocol from the adapter.
- Disabled/guarded paths or F2 accidentally call/use the new document pipeline; old A7 pins misreported as current after implementation.

## Tasks

- [x] 1. TDD immutable source document in `app/hus/llm/document.py`, evidence builder dispatch in `evidence.py`; tests `tests/hus/llm/test_compact_document.py`. Check LF/CRLF spans, every nonspace character/unit, literal prefixes/indentation, fresh payload copies, 64/128/3000 caps, all sources and privacy, F2 unchanged.
- [x] 2. TDD protocol-v3 prompt and strict output renderer in `prompts.py` / `output_v3.py`, dispatch from `output.py`; tests `test_compact_output.py`. Reject unknown/duplicate/missing IDs, stale text, numbers/conditions/negations omitted or borrowed, links/HTML/newlines/marker injection. Accept unordered complete output but render canonical order with individual bullets and local anchors. Reuse v2 lexical coverage; no20-point cap on v3. `HUSTextRewrite.reply` preserves indentation but still rejects whitespace-only strings.
- [x] 3. Connect default adapter to shared evidence dispatch; add safe enum/count-only envelope/validator diagnostics to client/errors and observed measurement trace. Update `tools/evaluate_hus_llm.py` / `evaluate_hus_llm_v4.py` preparation and payload export to build the exact adapter protocol, record protocol/limits in fresh pins, preserve cache-only replay. Add adversarial diagnostic and pipeline tests before code; adapt synthetic provider fixtures to v3 while retaining legacy validator tests.
- [x] 4. Verify saved four stress cases and Q022 with explicitly synthetic v3 output; keep existing gold/run/review results unchanged. Run focused/new/legacy LLM and UI/API rollback checks, one technical review, fix material findings with RED/GREEN, then appropriate full offline checks/Ruff/diff. Re-freeze/recollect A7 with final code pins and identical questions/gold/evidence in a NEW exposed artifact; preserve r1 failed result. Finish docs/roadmap/memory with limitations and next steps; no live LLM or enabling.

## Evidence

Ignored ledger/archive/logs: `backups/hus_llm_compact_20261111/`. Original A7 r1 and all L5 artifacts remain immutable. Use existing CI Python; tests block outbound. At completion report tests appropriate to this change, synthetic diagnostic outcomes separately from live model results, source/retrieval hashes and exact A7 disabled-response comparison. New Google cohort/budget remains unapproved.

Complete offline:647 broad related LLM/API/UI/contracts/rollback/A7 checks before final narrow prompt/ratio change; then480fullLLM checks on final code, including82newcompact tests. Single review0C/1I/0M; mixed operator corruption fixed RED→GREEN without changing v2. Appropriate full changed-subsystem coverage used, not a whole-repo green claim. Synthetic5devcases pass with complete source/bullets, not real model success. Historical2375data and45static files unchanged,4L5+2A7r1cached replays reproduced. Final A7r2 same48exactresponses and still19/24recall27/36complete, source/control checks pass, currentpinsmatch. Receipt [offline v3](../../../data/hus/qa/20261111/llm_compact_v3_r1/report.json); LLM remains disabled, no Google/commit/push/deploy.
