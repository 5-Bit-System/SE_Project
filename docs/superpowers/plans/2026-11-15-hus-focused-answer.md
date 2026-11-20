# Focused answers implementation plan

> Execute inline with superpowers:executing-plans and TDD. User selected the existing design for implementation; retain current hus-llm-rag workspace and no Git publication.

**Goal:** Add an explicitly selected focused policy that resolves one source scope before retrieval and keeps every required paragraph in a strict new LLM protocol.

**Architecture:** Default legacy answering/v3 is unchanged. `HUSAnswerer(..., answer_policy='focused')` resolves F1 edition/variant/source from the eligible canonical inventory; ambiguous requests return real source choices. A pure focused planner selects definition paragraphs by bounded request/topic rules, keeps complete paragraphs and optional requested examples, and binds spans/hashes into immutable JSON before generation. A separate focused adapter validates every unit, lexical/math tokens and IDs, then renders citations/layout itself. F2 retains the existing facts protocol.

**Tech Stack:** Existing Python/FastAPI/JS/pytest, no new dependency, downloads or Google calls.

**Spec:** ../specs/2026-11-14-hus-focused-answer-design.md

## Constraints and rulings

- No historical run/gold/review/data/index edits, secret/env reads, live calls, Git operations or server restart.
- Caps remain1024 output tokens,12000 prompt chars,8192 raw output chars; never remove required units to fit.
- Keep legacy constructors/dispatchers/prompts by default; opt in with launcher `--answer-policy focused`, process setting `HUS_ANSWER_POLICY` and explicit adapter selection.
- Source identity is metadata source_id plus edition/variant/review/origin/package identity, never a target ID or year priority. Unknown stays unknown.
- Ruling: use optional backend parent-ID restriction in lexical/vector/hybrid so selected source family is filtered BEFORE scoring; existing index metadata/checks remain intact and default traces stay unchanged.
- Ruling: strict focused output initially preserves normalized word/operator sequence exactly (only case/neutral punctuation differences). This also rejects added negation/conditions; no free paraphrase claim.
- Ruling: attach immutable plan JSON to the prepared answer in an excluded internal field; public citations/facts/quotes remain canonical. Expose only source choices, not internal spans, in normal UI.

## Task1 — Source resolution and scoped retrieval

Files: app/hus/focused.py, app/hus/answering.py, app/schemas/hus.py,
app/hus/{retrieval,vector_query,hybrid_retrieval}.py; tests/hus/test_focused_answers.py.

- [x] Write RED tests: multiple F1 editions/sources clarify before search; explicit edition/variant/source selects exact family; wrong selector never borrows; unknown not standard; source selection independent of ranking. Parent restriction reaches both hybrid legs and vector filter before scoring, including fallback.
- [x] Implement constructor policy, safe source-choice schema/request selector and source resolver. Preserve F2 path and legacy defaults.
- [x] Run tests GREEN, existing scoped retrieval and source tests.

## Task2 — Bounded aspects and complete required spans

Files: app/hus/focused.py, app/hus/answering.py; tests/hus/test_focused_answers.py.

- [x] RED tests for overview grammar, two object/inheritance aspects, research question/scope, everyday overfitting alias; similar requests/other majors, title-only evidence, missing aspect, unknown tails/conditions/negation/always.
- [x] Resolve only supported topics from descriptive paragraphs, not keyword/title matches. Keep adjacent sentences in each paragraph; full chunk if context cannot close. Examples/whole requests require their full inventories, not top5 truncation. Other requests use the existing strict support guard.
- [x] Preserve canonical quote/locator/hash/review, record real relative spans and per-aspect coverage in plan JSON. GREEN tests, F3 consent and F2 facts regressions.

## Task3 — Focused protocol, adapter and UI opt-in

Files: app/hus/llm/focused.py, app/hus/llm/adapter.py,
app/services/hus_service.py, tools/run_hus_{llm,rag}.py, app/static/hus-rag-demo.js;
tests/hus/llm/test_focused_protocol.py and focused UI/API tests.

- [x] RED tests: exact units valid; missing/duplicate/unknown IDs/extra keys fail; added/moved negation, symbols/numbers, HTML/link, source mutation, mixed scope, budget fail. Context is copied before provider and frozen hash checked, no partial output. F2 schema unchanged.
- [x] Implement focused wire format and validator with trusted layout/citation rendering and allowlisted diagnostic stages. Default v2/v3 replay unchanged. No arbitrary connective insertions.
- [x] Opt in via launcher flag/service; wire clickable source choices using original question and scope epoch. Explicit API source_id is backend-validated, choice cannot change permissions. Existing flags/defaults and429-only offline policy preserved.
- [x] GREEN focused/integration/launcher/UI tests, then broad related suite/Ruff/lightweight --check.

## Task4 — Separate diagnostic and documentation

- [x] Save protected hashes before edits, run a new offline diagnostic for exposed cases; save plans/quotes/prompts and exact checked mock outputs separately, no accuracy/Google gain claim. Controls covered by tests, not regraded as a score.
- [x] Request final code review if service available; address important findings with regression. No retry workaround for service usage limits.
- [x] Verify integrity, update quickstart/roadmap/design status/memory with actual scope and limits. Human content review/live budget remain separate.

## Execution ledger

Plan follows selected design; no additional approval gate is inferred. No commits per persistent user instruction. Source/policy opt-in preserves historical behavior while enabling reviewable implementation offline.

- RED14 context +17 protocol tests before implementation. Later RED format prefilter/canonical tampering and context closure/numeric punctuation regressions fixed. Final broad related1072PASS506.21s; focused after final core fixes49PASS49.29s (overlap), one old Starlettewarning. Ruff17files clean; real mobile viewport/keyboard/source-choice browser tests passed. Service/launcher explicit mode and F2/auto429-only policy checked with synthetic completions, no Google.
- Reviewer review_focused_answer found numeric punctuation loss and optional-section context closure. Both fixed with observed RED->GREEN. Same-line component qualification edge also fixed; reviewer final static confirmation no material finding in fixes. Standalone illustrations remain optional only without description dependencies; nonstandard layout/qualification retains whole chunk.
- Nativehybrid v4 r2: five real scoped searches/indexpin correct/no retrievalfallback. Exposed006009014019 answered with1/2/1/1requiredunits;012clarifies with5choices/no search; separate explicit2023standard request answered. No accuracy or latency benchmark/Gemini gain; output copies are synthetic validation only.
- New run data/hus/evaluation/runs/focused_answer_offline_20261115_r2 SHAde6c82c2beb208a2cf9e8c12686955ea7ab24843ce8fc4f80d203eb2a423ea0a;84protected files unchanged. ReviewCSV6humanpending. r1helper used UI F2edition in F1context and correctly hit canonical guard before native; sealed failure separately, r2uses effective F1scope. No validator/source relaxation.
- .cache/hus/focused_20261115/diagnose.py EXECUTEDr1failed/r2complete; never rerun one-shot writer or overwrite frozen outputs/humanCSV. No root.env/template/key/provider config reads, downloads, Googlecalls or Git mutations. Existing server not restarted; default legacy/v3, focused explicit only. Google budgets closed; new live measurement requires fresh pins/preparation/agreement.
