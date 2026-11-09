# P1-2 RAG Baseline Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. User chose P1-2; keep work on crawldata and do not commit/push without request.

**Goal:** Measure the frozen 48-question P1-1 candidate on unchanged RAG, with explicit denominators, observations and limitations.

**Architecture:** Collect predictions through the actual standalone HTTP handler using request-only inputs and trace its retriever calls. Score afterwards against frozen draft gold. Reuse the independent source oracle for answer-level citation integrity; gold anchors give a conservative automatic citation precision proxy, not human semantic acceptance.

**Tech Stack:** Python 3.11, stdlib JSON/JSONL, FastAPI TestClient, pytest, existing EvidenceOracle.

**Spec:** P1-2 in `docs/RAG_PROGRESS_AND_NEXT_PLAN.md`; P1-1 pack README.

## Constraints

- Do not modify retrieval, answering, intent rules, thresholds, source data, P1-1 gold, or review status.
- Human review of P1-1 is pending: results must remain provisional and non-certifying.
- Collect all predictions before loading gold into the scorer; executor receives only the original request, no category/dataset/field/expected IDs.
- Routed Recall@5 counts all 20 F1/F3 positives, including zero-hit/no-retriever-call failures. Twelve F2 lookups are measured separately.
- Source-supported success uses all 32 positive cases; guards use all 16 missing/out-of-scope/opt-in cases. False abstentions must remain in denominators.
- All 48 requests, errors, citations and retrieved hit identities are retained; no cherry picking or rerunning only successful cases.
- Candidate provenance/manifest remains immutable. A new run report records that inference is now performed; P1-1's false inference flag is a creation-time snapshot only.
- No tuning or production/provider/DB activity. If these cases later guide tuning, retire them from holdout status and make a new evaluation split.

## Tasks

- [x] Add failing metric tests for no-search denominators, zero citations, wrong scope, unsupported facts, AI labels and request-only execution.
- [x] Implement pure scoring helpers plus the standalone evaluator; retain predictions before scoring.
- [x] Run all 48 once, write a new immutable run directory, and record manifest/code/oracle hashes and failures.
- [x] Inspect errors without changing RAG; document provisional metrics and the pending semantic review queue.
- [x] Run regression/Ruff/diff checks and get read-only technical review of the measurement methodology.
- [x] Update progress and evidence report; no commit/push or holdout acceptance.

## Review focus

- Routing misses and over-abstention cannot improve retrieval/quality percentages by disappearing.
- A grounded citation from the wrong major/code/version cannot count as support.
- Alternative source citations outside the draft anchors remain unjudged, not automatically academically wrong.
- Source integrity is not the same as semantic entailment; keep human precision/support metrics null until reviewed.
- CI/regression requests are not holdout predictions; reports must distinguish their scopes.

## Execution record

- Metric tests initially failed before the module existed. Additional red/green checks fixed HTTP error versus abstention accounting and prevented correct-source/wrong-F2-value citations earning anchor credit.
- Ran the frozen48 once through the actual standalone route. Baseline routedRecall@5=8/20, F2 lookup=7/12, source-backed success=7/32; threshold90% not met.
- Read-only technical review found error capture lost actual status/trace for non-JSON HTTP500. Added a synthetic regression and captured body/status/trace before parsing; 48 original responses were HTTP200, so recorded metrics remain unaffected.
- Original artifact/code hashes were preserved; offline verifier replays every scored case and group without new inference, reporting collection-tool changes separately.
- Final measurement-tool tests11 passed; combined metric/candidate/chat/citation-oracle regression68 passed. Ruff and diff checks passed. No runtime/gold/source edits, human acceptance, tuning, commit/push or production activation.
