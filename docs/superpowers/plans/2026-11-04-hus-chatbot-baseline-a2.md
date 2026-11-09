# A2 pinned BM25/extractive chatbot baseline

> **For agentic workers:** Use superpowers:executing-plans inline; TDD and final scoped code review.

**Goal:** Measure the current Q&A baseline without runtime/data tuning, preserving historical scoring.
**Spec:** User-selected A2 row in RAG_PROGRESS_AND_NEXT_PLAN.md.
**Architecture:** New versioned scorer/runner reuse existing collector, trace, layered/raw metrics and source oracle. Persist observations before scoring; immutable measurement runs and separately bound AI review overlays. No vector/LLM calls.
**Stack:** Existing Python/FastAPI TestClient and offline source evidence.

## Decisions

- Stay on crawldata/WIP; no runtime, old tools/tests/gold/reviews/reports modifications.
- Measure legacy dev96 and corrected AI-reviewed H2 exposed56, plus new contract-only pack28 copied from already exposed A1/A1b dev cases. Never combine overlapping packs into an independent score.
- Preserve raw legacy metrics. V2 F2 source-contract assessment binds raw values/status to source; unknown [null] is not rewritten into [] and is not a generic normalization rule.
- Separate classifier route, observed filters, first actual top5 scoped recall, F2 course/program/group, source integrity, raw anchors, quote-coverage proxy, AI entailment/completeness, correct/false refusals and latency.
- AI semantic review is a distinct immutable artifact bound to response/request/gold/audit hashes and release/run identity. Missing review stays null; never relabel as human or infer entailment from quotes.
- Latency is warmed local TestClient HTTP wall time, excludes source audits/review/startup; record warmup and initialization separately, p50/p95 by major/category. Not production load testing.
- Preserve failed runs. CLI fresh-only; cached verification and review scoring perform no new inference.
- H2 remains exposed,25questions tuned,actual human reviews0; no independent Recall acceptance even if exposed Recall≥90%.

## Tasks

- [x] Freeze old inputs/runtime and contract-only targets before inference.
- [x] RED→GREEN metrics v2 including denominators, source-contract unknown, scoped top5, latency and strict review binding.
- [x] RED→GREEN collector/runner immutable outputs, source audits, replay verification, separate review overlays.
- [x] Scoped technical review, full applicable regression, collect all packs on final pinned code.
- [x] AI review observed source support/completeness, re-score in new overlays, verify replay, publish local report/update plan/memory.

Completed:31newtests,1794offline/90deselected,50Chromium,5Node,Ruffpass.850oldfiles
unchanged;all3measurement+3AIoverlay runsreplay. H2exposedRecall20/20,F2raw15/16
vs source16/16,AIcomplete36/36. DevRecall39/40,AIcomplete63/64:DEVQ027incomplete,
goldalreadyintop5; no runtimefixduringA2. Humanreviews0,H2tuned25,notindependent.
Important evaluator integrity/binding/filter/timing/releasefindings red-greenfixed
before finalcollection; technical+artifactreview finalnoCritical/Important.
Immutable codearchive327files preservesWIPbytes alongside source/dependencyhashes.
