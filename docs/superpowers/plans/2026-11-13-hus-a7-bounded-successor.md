# A7 after bounded request repair

> **For agentic workers:** Use superpowers:executing-plans inline, TDD and one fresh-context final code review before freeze. No Git publication.

**Goal:** Freeze and evaluate a different source-authored48-question/12-per-major A7 cohort on the repaired baseline, preserving historical scores and unresolved policy contracts.

**Architecture:** Add a source-only builder, register/pin it in the existing evaluator, keep scorer/retrieval/runtime unchanged. Freeze before prediction; save exact observations before source audit/scoring; bound nonblind AI review as a separate overlay.

**Tech Stack:** Python3.11, pytest, local FastAPI TestClient, immutable v4/lexical/LLMoff.

**Spec:** User-selected roadmap row “Freeze A7 khác sau sửa baseline”; docs/HUS_F1_SOURCE_EDITION_POLICY.md and prior Q025/Q037/DEV-Q002 contract reviews.

## Constraints and review focus

- Existing hus-llm-rag WIP, local only; no stage/commit/push/PR/Actions/deploy, DB/key/env-file reads or Google/network calls.
- No runtime, data, old tests/gold/run/review changes. A7S/A7R are exposed dev; their scores remain immutable.
- Q025 ambiguous source branch, Q037 history+orientation, DEV-Q002 enumeration-vs-comparison remain held. No new behavior accepted here; author unambiguous source/edition/variant requirements and retain a comparison control. This does not close the positive enumeration contract or count it as passed.
- Each major3F1/3F2/3F3+3controls. No gold-derived API hints. F2 canonical types/values and F3 AI label/consent/citation full required units; preserve no-information controls.
- Record normalized wording overlap, prior target/concept/record exposure and author/reviewer exposure. Source-only deterministic selection is not a new independent holdout. Don't inspect candidate predictions before freeze or cherry-pick by rank/pass.
- F1 scope chooses one source group, no broad unqualified gold branch or academic equivalence. Gold required ideas are declared before inference; never add alternatives after output.
- Pins include current code/data/config/index/model/prompt/builders/tests and policy. Freeze/run reject mismatches. Review is rootAI/nonblind/human0, never independent acceptance.

## Tasks

- [x] Protect old publicfiles, write separate held-contract disposition. Inspect sources only and author new declarations/selection. Write builder/freeze/source-binding/overlap/pins tests RED.
- [x] Implement tools/hus_a7_bounded_cases.py, register/pin cohort in tools/evaluate_hus_a7.py, add tests/hus/test_a7_bounded_candidate.py. GREEN with affected evaluator/candidate/metrics tests and scoped Ruff.
- [x] Fresh-context review attempted but unavailable(usage limit); author self-review after usercontinue, explicitly weaker and not independent. Freeze fresh pack, prove timestamp/pins/source/gold and no prediction before freeze; collect exactly48 local requests without external/provider, no fixes during measurement.
- [x] Read every exact response/gold/quote/audit, make separate bound AI review/overlay, replay and verify oldSHA/scores. Document routed Recall including no-call, facts/citation/completeness/controls/exposure/local latency and limitations; update roadmap/memory. No tuning/regrade in this run.

Completion:Recall22/24,F2facts12/12,complete27/36,automaticcontrols11/12; separate semanticcontrolreview10/12. NOTallgates/independentacceptance.2987/2988oldprotectedunchanged; onlyevaluator registration changed, newbuilder/test added. QA a7_bounded_request_r1 sealed. Afterfreeze newshape-test fixtureisolated followingRED1; affected113passagain, no runtime/gold/scorer/run edits or remeasure. CURRENTpins nowSTALE exactlynewtesthash, separatea7_bounded_test_isolation_r1receipt, oldQA pinmatchtruehistorical. Retainworkspace/markers/localWIP; nextreviewfailurecauses beforechoosingfix.

Ruling: preserve selected baseline and unresolved behavior rather than invent an academic policy verdict; new assessment is on explicitly declared source scope, not proof those old contracts pass. Existing branch/localonly preference overrides new worktree/commits; retain private evidence workspace.
