# P1-1 Reviewer Holdout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Do not commit/push without a separate user request.

**Goal:** Prepare at least 40 source-grounded reviewer questions, including missing-evidence and out-of-scope cases, isolated from retrieval tuning.

**Architecture:** A 48-case prospective holdout candidate lives outside the runtime RAG directory. Questions, draft gold answers, evidence and pending review decisions are separate files, pinned by a manifest. A stdlib validator checks identities, source/value/quote integrity, split overlap and disclosure without calling the RAG stack.

**Tech Stack:** UTF-8/LF JSON/JSONL, Markdown, Python 3.11 stdlib, pytest.

**Spec:** `docs/RAG_PROGRESS_AND_NEXT_PLAN.md`, P1-1 in section 7.

## Constraints and decisions

- 48 questions: 12 per supported major; F1/F2/F3, abstention, opt-in and scope boundaries.
- AI-authored questions and draft gold are not independent human review. Keep reviewer/time null and status pending; P1-1 cannot be marked accepted on technical checks alone.
- Read pinned release records/captures directly; never use RAG predictions to author gold.
- No retrieval tuning, RAG queries on the candidate questions, production activation, or runtime/source/review edits.
- Existing regression/data-lookup question sets are development material, not holdout. Record their hashes and reject normalized exact overlap; semantic overlap and same-course overlap require human review.
- Exposing holdout cases to a future tuning session consumes them: move them to development and create a new holdout version before reporting holdout metrics.
- Human-readable reviewer packet plus separate answer/evidence files; no automatic loading by runtime or smoke/CI answer-generation.

## Tasks

- [x] Read source schemas and select evidence-backed coverage for all four majors.
- [x] Write failing integrity tests for tampering, unsupported gold, cross-major evidence, AI promotion, and duplicate/development questions.
- [x] Prepare questions/gold/evidence/review files, manifest and review instructions; label candidate/pending honestly.
- [x] Implement offline validator with no app imports or inference calls; pass integrity and mutation tests.
- [x] Check Ruff/diff and preserved source/release hashes; get a read-only technical review of the pack.
- [x] Update P1-1 progress to prepared, awaiting independent review; leave P1-2 metrics pending.

## Review focus

1. A correct fact paired with the wrong major/version/source must fail integrity checks.
2. AI reference answers must not claim official content, sources or assessment weights.
3. Null official/current-offering fields justify abstention, never invented numeric facts.
4. Hash-valid but semantically unrelated quotes still require a human reviewer; validator success is not gold acceptance.
5. No test run or technical subagent may be described as independent human approval or holdout performance.

## Execution record

- Initial integrity tests failed before the validator existed; implemented the candidate contract.
- Windows mutation fixtures initially wrote CRLF and hit the LF guard before reaching their target checks; changed only fixture serialization to UTF-8/LF.
- Technical review found two important gaps: generated evidence could hide behind a forged gold dataset label, and explicit F1 editions bypassed scope checks.
- Added mutations with refreshed payload hashes and review bindings; observed both fail before the fix, then pass after binding category/dataset to actual source and enforcing explicit editions.
- Final focused integrity suite: 12 passed. Human/semantic review and RAG performance remain pending; no holdout queries were sent to RAG, no retrieval tuning, commit, push or production activation.
