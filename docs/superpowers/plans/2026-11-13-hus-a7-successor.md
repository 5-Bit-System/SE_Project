# A7 successor after request/role repair

> **For agentic workers:** Use superpowers:executing-plans inline, with one final fresh-context code review. No Git publication.

**Goal:** Review the DEV-Q002 scope conflict without changing its gold, then freeze, measure and review a new 48-request A7 pack.

**Architecture:** Reuse the sealed A7 evaluator and source auditor. Add one source-only candidate builder, register and pin it, freeze before API inference, and store AI review as a separate overlay of exact responses.

**Tech Stack:** Python 3.11, pytest, FastAPI TestClient, lexical retrieval, immutable v4.

**Spec:** User-selected roadmap row “Review test cũ và A7 kế nhiệm”; `docs/HUS_F1_SOURCE_EDITION_POLICY.md`.

## Global constraints

- Existing `hus-llm-rag` WIP; no stage/commit/push/PR/Actions/deploy.
- No app/runtime, old test/gold, release, run or review changes. Preserve A7S historical 23/24–32/36–12/12 and dev exposure.
- 48 questions, 12 per major, each with 3 F1/3 F2/3 F3 and 3 controls; source/gold before inference.
- Shared CURRENT v4, lexical, no vector index, LLM off, no external/provider calls or private configuration reads.
- Routed Recall@5 includes no-call; source integrity is distinct from relevance/completeness. AI review is exposed/nonblind, human0.

## Review focus

- Multi-variant enumeration versus incompatible filters: review separately; do not relax guard to match legacy gold.
- Wording novelty does not establish unseen concepts or independent evaluation; record reused identities and prior input hashes.
- F1 unknown scope stays unknown; no current applicability claims or web/DOCX equivalence.
- F2 canonical values/types and F3 unit text/AI label/consent remain source-bound.
- No inference during build/freeze, no changed pins after freeze, no overwritten artifacts, exact-response review and replay.

## Tasks and completion contract

1. [x] Protect existing data/source/test/tool files with SHA snapshot. Inspect DEV-Q002 source, historical manifest and guard; save a separate diagnostic and contract review, preserving the failing assertion.
2. [x] Add `tests/hus/test_a7_successor.py`: balance/exposure, source binding damage, prediction-free freeze, pinned builder/tests, overlap rejection. Observe RED, then add `tools/hus_a7_successor_cases.py` and evaluator registration/pins. Observe GREEN with related evaluator/metrics tests.
3. [x] Freeze `candidates/a7_request_role_20261113_r1` and check pins/source/gold/timestamp. Collect exactly 48 requests into a new run; read every exact response, citation and gold; write a separate bound AI review and sealed overlay. No fixes/tuning during measurement.
4. [x] Fresh-context code review; fix important evaluator issues before freeze if found. Verify old hashes, replay new/old runs, scoped lint/diff. Document scores, failures, exposure, known legacy test failure and next steps; update roadmap and project memory.

Ruling: The supplied row plus existing source-edition/evaluation contract fully specifies this work. Preserve current branch/WIP and proceed inline; no repeated design or publication approval. DEV-Q002 semantic ambiguity can remain open after evidence review; do not manufacture a policy verdict to make the suite green.
