# Router grammar repair implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline with TDD. User selected the bounded repair row; retain existing hus-llm-rag workspace and local-only scope.

**Goal:** Correct conditional-particle/exam routing and common careers, prerequisite and concept requests; clarify ambiguous major-level wording.

**Architecture:** Distinguish accented `thì` before lexical folding at question-grammar normalization, retaining the original request and all actual `thi`/exam terms. Add bounded semantic request patterns shared by field detection and routing. Scope/source/condition/negation checks remain; catalog arithmetic stays backend-owned.

**Tech Stack:** Existing Python3.11/regex/pytest; no dependencies or provider calls.

**Spec:** User's “Sửa cú pháp/router theo lỗi đã đo” row. HN20 is exposed dev evidence, not a new score or acceptance set.

## Constraints and review focus

- No Google calls, secret/template reads, Git stage/commit/publication or changes to v4/run/gold/review/CSV.
- True exams, unsupported official assessment, numeric facts and conditions must not become ordinary content.
- Course content/objectives need F3 consent; prerequisites never need F3 consent.
- Unknown domain topics, mismatched major/code/version and factual negation must remain unsupported.
- 001/017 ambiguity is resolved by asking the user, not selecting gold or altering ranking.

## Task 1: Reproduce and specify

- [x] Add tests/hus/test_conditional_question_language.py: positive natural paraphrases, real exams/unaccented exams, conditions/negation, concept vs objectives, major vs course, source guard and API outcomes.
- [x] Run and inspect RED before modifying production code; hash original natural20 pack/run/review to a local ledger.

## Task 2: Bounded correction

- [x] Modify question_routing.py normalization/intent/shared field recognition; preserve literal original question.
- [x] Modify answering.py for explicit major-ambiguity clarification, preserving scope-first checks and existing hints.
- [x] Modify program_catalog.py to recognize only explicit unique-code counting grammar, retaining required/filtered refusals.
- [x] Modify answer_support.py only for new bounded request grammar and conditional support where demonstrated; no domain-word stopword expansion.
- [x] Run focused tests and legacy language/routing/program/intent regressions offline.

## Task 3: Review and verification

- [x] Fresh scoped reviewer per requesting-code-review; fix demonstrated issues with regression tests.
- [x] Run related tests/Ruff and no-key --check; verify original pack/run/review hashes.
- [x] Update roadmap/report/memory with actual outcomes and remaining limits; do not regrade old observations.

## Execution record

- Root cause: `_clause_texts` folds accented conditional `thì` to exam token `thi`; missing `làm việc`, postposed “phải hoàn thành ... trước”, and conceptual-content request grammar. Previous intent fallback deliberately does not override known-but-wrong rule fields.
- Initial TDD32cases:18RED/14pass ->32pass. Extra observed RED regressions covered positive/negative conditional matching, hiding condition tails behind desire prefixes, concept grammar leaking into F1, and chuyên môn/bộ môn/liên môn mistaken for course markers.
- Final53new regression cases green. Root intermediate539PASS115.78s; final636PASS207.05s (overlap), existing Starlette warning only. Ruff5files clean. Public minimal-venv --check20API/2124menu/4source hashes PASS, no Google.
- Reviewer review_router_grammar_repair found2P2 (condition-prefix exemption and bare môn compounds), fixed with RED/GREEN; independent final53PASS, no important findings remaining. Parent also restricted concept grammar to actual F3/content hits and anchored source condition matching.
- Ruling: 001/017 are clarified as ambiguous major-level requests rather than choosing field from frozen gold. Explicit field hints still resolve them; wrong major checks run first.
- Ruling: consume only complete pure desire wrappers after known scope identifiers; any extra qualifier must remain literal source evidence. Never add generic concept or condition tokens to stopwords.
- Postfix one-shot diagnostic uses original6requests, not targets:001/017clarification,002F1careers/004F3content/005F2count/008F2prereq answered; no score/quality or latency claim. New local ledger .cache/hus/router_grammar_20261114; writer EXECUTED, do not rerun/overwrite.
- Original30pack/run/review files verified unchanged SHA256 before/after.44document links valid. No data/index/prompt/gold/observations/review mutation, secret/template read, provider call or Git publication.
