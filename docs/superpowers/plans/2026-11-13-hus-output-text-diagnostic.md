# Output-text diagnostic implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline with TDD and one fresh-context final review. User local-only instructions override commit/worktree/publication steps.

**Goal:** Identify future compact-output text rejection branches without weakening validation or retaining provider content.

**Architecture:** Add optional strict `text_issue` labels to `HUSLLMDiagnostic`, emitted only for `output_text`. Split the existing combined predicate in the same order, preserving strip/double HTML decoding/NFKC, every rejection, code/stage/leaf and canonical fallback. Existing observed-adapter allowlist serializes the additive field; no new raw-output storage, prompt or runner changes.

**Tech Stack:** Python3.11/Pydantic/pytest, HTTPX MockTransport only.

**Spec:** User-selected roadmap diagnostic output_text then L5/L6: synthetic/offline only, unknown historical cause, no validator relaxation, 1024 output cap, all live budgets spent, L6 off.

## Constraints and review focus

- Keep existing branch hus-llm-rag/WIP local; no stage/commit/push/PR/Actions/deploy, env/key/DB/network/provider access.
- No old tests/gold/run/review/data/prompt changes. No new L5 cohort/preflight or academic/entailment/gain claims. R5 already stale after bounded repair.
- Fixed labels: blank, raw_line_break, decoded_line_break, structure, link_or_html, restored_length. Optional None preserves old serialized diagnostics; arbitrary text/extra fields/wrong-stage labels rejected.
- First rejection precedence remains unchanged, including trim versus internal break, double entities/NFKC, combined invalidities and restored prefix length. Empty/oversize items still schema errors first.
- Successful literal bullets/prefixes remain backend-owned. Non-text validation failures gain no text label. Trace preserves actual model/token/fallback, no rejected text in trace/exception/public response.

## Task 1: bounded diagnostic with regression and receipt

Files: modify app/hus/llm/diagnostics.py and output_v3.py; create tests/hus/llm/test_output_text_diagnostic.py. Docs: new diagnostic report, roadmap, historical Google diagnostic pointer, project memory.

- [x] Snapshot protected public files and original two modules; build synthetic tests for all six branches, boundaries, first-failure, schema/privacy/legacy and observed L5 trace/canonical fallback. Run RED, require missing detailed label behavior.
- [x] Add optional allowlisted text_issue and stage consistency; split predicate without normalization or acceptance changes. Run GREEN and differential original-versus-current decisions on the synthetic corpus.
- [x] Final fresh-context review; fix Critical/Important with RED/GREEN in one pass, ledger deferred minors. Run full affected LLM/UI offline suite, scoped Ruff and diff check. Do not rerun unrelated 22-minute HUS suite unless integration failures warrant.
- [x] Verify protected hashes and current bindings, seal new offline QA (not a quality run). Update docs/next steps and memory. Historical output_text/b001 remains unknown, all calls spent, L6 off, fresh budget/pins/prepare required for future L5.

Completion:43newtests,607affectedpass/1existingwarning,42synthetic differential cases unchanged, review0findings.2963/2965protected unchanged, only two authorizedruntime changes. QA `data/hus/qa/20261113/output_text_diagnostic_r1`, manifest `d63cd2c40c1923bfa3db9210bbb65ed02e71c29cfb665dd87764b31f10e5edbd`. R5stale5artifacts, no qualityscore/livecall/newprepare, L6off. Docs/nextsteps/memory recorded.

Ruling: the selected detailed row already authorizes this diagnostic-only behavior, so no repeated design approval. No behavior to accept model output is changed. Keep evidence workspace because publication/Git checkpoint is not authorized.
