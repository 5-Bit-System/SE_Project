# Bounded request repair after A7R review

> **For agentic workers:** Use superpowers:executing-plans inline, TDD per task and one final fresh-context code review. No publication.

**Goal:** Repair the reviewed general routing and source/request syntax gaps while preserving factual/scope/coverage checks and historical results.

**Architecture:** Extend bounded request recognition in `question_routing.py` and `answer_support.py`. The answerer supplies trusted citation-format validation and the eligible source inventory only when requested. Whole-field coverage compares complete chunk identities within the exact existing source scope; no BM25/top-k changes or global neutral words.

**Tech Stack:** Python 3.11, pytest, existing immutable v4 lexical data/citation resolver, no LLM calls.

**Spec:** User-selected “Sau review: chọn sửa route/cú pháp có giới hạn”; `docs/RAG_A7R_FAILURE_REVIEW_2026_11_13.md`, `docs/HUS_F1_SOURCE_EDITION_POLICY.md`.

## Global constraints

- Existing `hus-llm-rag` WIP, no new worktree/stage/commit/push/PR/Actions/deploy; no secret/env/provider/DB access.
- Preserve all existing test/gold/run/review/data metadata; A7S/A7R are dev, historical20/24–18/36–12/12 unchanged.
- Q025/Q037/DEV-Q002 behavior remains unchanged pending separate contract decisions. No source-ID/QID patches, unknown relabeling, score/ranking manipulation or global token removal.
- F2 canonical facts, F3 labels/consent, negation/conditions, edition/variant/source review and exact citations remain authoritative.
- Google budgets exhausted; v4/lexical/LLMoff. Changes stale r5 pins; never edit sealed artifacts.

## Review focus

- Graduate titles/teaching versus institutional roles, course skills and current named faculty.
- Vietnamese course-name requests versus writing/naming topics; English requests cannot silently return Vietnamese, including explicit field hints and negation.
- Bare eligibility conditions must retain both conjuncts and negation in the same source; no condition inferred from possible further study alone.
- Source-format syntax must use available hash-bound resolver evidence with locators, never URL suffix/body/title alone; factual PDF/record/memory/aircraft terms remain required.
- Whole-field requests require the full eligible inventory in one source/edition/variant/field/review scope and render every continuation; missing inventory/fragment means refuse.

## Tasks

1. [x] Protect old files. Write failing routing/name integration regressions in `tests/hus/test_bounded_request_language.py`; implement bounded titles/work roles/teaching/further-study headings and language-aware course names in `question_routing.py`/`answering.py`. Run focused existing routing/support tests.
2. [x] Add RED guard syntax/condition/profile-locator regressions. Implement bounded source subject/AI locator/accompanying-condition handling and bare explicit condition recognition in `answer_support.py`; retain all negative/domain/scope checks. Run focused tests.
3. [x] Add RED tests in `tests/hus/test_source_format_coverage.py`. Add optional trusted `format_supported` and lazy `source_catalog` guard callbacks; wire answerer resolver/inventory. Verify missing/split/mixed scope/format/locator and full rendered continuations with synthetic and current-data cases.
4. [x] Fresh-context code review, fix important findings RED→GREEN; run appropriate HUS offline suite without hiding DEV-Q002. Verify protected file hashes and cached old scores; record stale pins. Document completion/limits and next≥48/12 source-first freeze on final code, not regrading old cohorts.

Completion:94newcases pass; HUS2442pass/1legacyDEV-Q002fail/2Windows-symlinkskip/1existingwarning. Suite not green; held contract is outside repair, no test/gold/guard relaxation.2955/2959protected unchanged, only authorized3runtime+initialREDnewtest changed; other newtest added separately. Old A7R replay reproduced, L5r5 stale on exactly3runtime artifacts. QA `data/hus/qa/20261113/bounded_request_repair_r1`, manifest `bc6e24374c051e596a20b9769c128024601f25c36b32990e140416dd8c318094`. Report/roadmap/memory updated; no provider/publication. New A7 freeze is a separate next stage.

Ruling: Detailed selected row and reviewed root causes supply the implementation scope; no repeated design approval. Work stays on the explicitly selected branch/WIP. Freeze/measure a separate successor as the next evaluation stage after final repair verification; do not blend it with regression/tuning.
