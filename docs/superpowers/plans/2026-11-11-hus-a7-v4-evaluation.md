# A7 v4 evaluation implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. User selected the concrete A7 roadmap step; no extra product design or publication is in scope.

**Goal:** Freeze and measure 48 fresh exact questions, 12 per major, on unchanged submission demo v4.
**Architecture:** Source-authored targets are frozen before inference; request-only collection goes through the real standalone HTTP route. Observe effective F1 scope mapping without changing it. Reuse metrics v2 and the independent v4 citation oracle, then review exact saved responses and replay without inference.
**Tech Stack:** Existing Python/pytest/FastAPI TestClient; no dependencies or Google calls.
**Spec:** User-selected A7 row in [roadmap](../../RAG_PROGRESS_AND_NEXT_PLAN.md).

## Global constraints

- Existing `hus-llm-rag` WIP workspace is the requested branch; preserve it in place and hash protected files. No commit/push/PR/deploy or runtime/source/prompt/retrieval changes.
- Actual CURRENT `hus-data-20261111-v4`, lexical, LLM disabled; no vector/index or provider inference. Pin code/data/CURRENT/assets/environment/evaluator/model/prompt metadata. Never load env files or print keys.
- Exactly 48 cases, 12 per major: 3 F1/3 F2/3 F3 positives +3 controls; 24 F1/F3 retrieval cases and 12 F2 lookups scored separately. Controls include opt-out, unavailable assessment, basic/clarification/out-of-scope across the cohort.
- Fresh wording does not establish independent holdout: AI author has seen sources/runtime/prior topics. Record exact-overlap inventory and reviewer/exposure; human reviews remain 0. Any later tuning uses this cohort as dev.
- Freeze targets and alternatives before prediction. Keep every failure/no-call/false abstention in denominators; Recall@5 target >=90%, source integrity/facts/semantic completeness and controls reported separately.
- Runtime executor receives only frozen raw request. Record effective request after normal chat F1 mapping, with no gold passed to execution. Scoring may use only that observed mapping, bound to raw request.
- No old pack/run/gold/review modifications; no retry or case replacement after results. Google budget exhausted; no LLM evaluation authorized.

## Review focus

- Gold or source IDs accidentally enter requests; raw/effective request mutation hides a scope error.
- Missing search/HTTP failure disappears from Recall@5 or semantic denominators.
- V4 AI reference quotes or inherited PDF assets are checked using a v3-only oracle.
- Resealed/changed source targets or AI reviews bind a different exact response.
- Fresh exact wording is described as independent or human-approved despite known exposure.

## Tasks

- [x] 1. Add regression tests first for balance/exposure/freeze integrity, request-only execution, effective mapping limits, missing-search denominators, source/reference tampering and exact-response review/replay binding. Run RED, then add `tools/evaluate_hus_a7.py` and pure helpers using existing metrics/oracle. No app changes.
- [x] 2. Prepare 48 fixed source-backed declarations in `tools/hus_a7_cases.py`, including source identity and intent expected independently of outputs. Validate values directly from pinned release; freeze new pack under `data/hus/evaluation/a7_v4_candidate_20261111_r1`. Execute every raw request once through demo HTTP into a new sealed run, without targets entering executor; retain full response/status/traces/effective request/latency and audit binaries after collection.
- [x] 3. Read all saved responses/source targets, record exact-hash-bound AI entailment/completeness/control judgments and exposure. Score a new review overlay and cache-only replay; run appropriate old/new evaluator regressions, Ruff and scoped diff checks. One fresh technical review of A7 additions; fix material findings once with regression evidence. Update detailed report, roadmap and project memory, distinguishing technical thresholds from human/independent acceptance.

## Verification commands

Use the existing project CI Python at `backups/hus_integration/pr6-resolution-20261102/backups/pr6/ci-venv/Scripts/python.exe` with `-X utf8`.

```powershell
python -m pytest tests/hus/test_a7_evaluation.py -q
python -m pytest tests/hus/test_rag_evaluation.py tests/hus/test_chatbot_metrics_v2.py tests/hus/test_chatbot_evaluator_v2.py tests/hus/test_rag_layer_metrics.py tests/hus/test_diagnostic_evaluation.py tests/hus/llm/test_v4_measurement.py -q
python -m ruff check .
python -m tools.evaluate_hus_a7 --replay <new-reviewed-run>
```

Ledger/evidence: ignored `backups/hus_a7_20261111/`. If a listed old test filename differs, resolve with `rg --files`; do not invent a passing check. Run data integrity/pin checks before and after collection. No automatic runtime tuning if thresholds fail.

Pre-freeze technical review: 0 Critical/2 Important/0 Minor. Exception rows now retain latency/effective-request fallback and can seal/score the full cohort; control gates require independent audits and meaningful basic display. Both reproduced RED then GREEN; new A7 suite 40 passed. Additional source-run manifest binding regression fixed; source identity gate compares ID/SHA while separately recording selector format/state. No independent re-review; review before freeze avoids mid-run evaluator pin changes.

R1 measured and root reviewed all48 exact responses: Recall19/24, completeness27/36, F2/controls12/12; not accepted. During A7 user approved separate offline LLM-v3 implementation. After that work, r2 froze final code with identical questions/gold/evidence, all48 exact response/request/trace/audit bindings matched r1. Explicitly reused exposed AI judgments under new bindings, no new independent/human review. New r2 artifacts replay and current pins match; old r1 is immutable. Report [A7 v4](../../RAG_A7_V4_2026_11_11.md); baseline repair remains a separate next task.
