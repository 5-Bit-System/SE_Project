# HUS request grammar and graduate role repair

> **For agentic workers:** Use superpowers:executing-plans inline; preserve the user's local-only branch and WIP.

**Goal:** Accept bounded source/presentation questions and graduate roles at schools/institutes while retaining factual qualifiers and source identity.

**Architecture:** Normalize only complete request constructions in `answer_support.py`. Extend the existing role-at-work intent with bounded workplace and subject detection in `question_routing.py`; workplace evidence remains mandatory in the guard. No retrieval ranking, response schema, data or thresholds change.

**Tech Stack:** Python 3.11, pytest, existing lexical RAG.

**Spec:** User-selected roadmap row and [four-case review](../../RAG_A7S_FOUR_CASE_REVIEW_2026_11_13.md).

## Constraints and choices

The user selected the general grammar/role-scope repair after diagnostic review.
Global ignored words and QID exceptions violate that scope; use bounded phrases.
Keep v4/lexical/LLM off, canonical quotes and conditions, source/edition identity,
AI opt-in and exclusions. No Google calls, secret reads, database, Git mutations
or publication. A7S becomes exposed development material; retain sealed scores
23/24–32/36–12/12. Current run/prepared pins will become historical after code changes.

## Review focus

- Factual presentation skills and aeroplane topics must still require evidence.
- A factual condition following request grammar must not disappear.
- School/institute as the actor is distinct from graduate roles at that workplace.
- Negation, independent fields, wrong edition/variant and excluded teaching remain guarded.
- Workplace phrases must occur in one scoped source; field routing alone is insufficient.

## Task 1: Grammar support

Files: `tests/hus/test_request_role_language.py`, `app/hus/answer_support.py`.
Interface: existing `supported_hits(question, hits, aliases=..., codes=...)`.

- [x] Add synthetic paired positive/negative tests for accompanying conditions,
  source-subject presentation, passive question tails, qualifiers and identity.
- [x] Run the new tests and retain expected assertion failures before runtime edits.
- [x] Implement bounded normalization without changing neutral word sets.
- [x] Verify new guard tests and existing support/wording regressions pass.

## Task 2: Graduate roles and workplace evidence

Files: same test module, `app/hus/question_routing.py`, `app/hus/answer_support.py`.
Interface: `question_intent(question)` and existing `supported_hits`.

- [x] Add role-at-school/institute and institution/course-role negative tests,
  plus source workplace, exclusion and multi-field integration cases; observe failures.
- [x] Extend role recognition with institution-subject exclusions; retain each
  requested workplace as a body requirement, including institutes.
- [x] Run new tests plus runtime/API, lexical and routing suites.

Task1/2 evidence:77 new regression cases;233 selected support/routing tests pass.
Four Important findings from fresh-context AI code review were reproduced by
13 failing cases, then fixed (15 review cases including positive controls).
Repository-wide offline run remains the final Task3 gate.

## Task 3: Integrity, review and reporting

- [x] Run repository offline test command from `.agent/AGENTS.md` and scoped Ruff.
  Report any failures by name; do not change unrelated behavior to hide them.
- [x] Check immutable data/run/gold/review hashes; cached replay old scores without
  inference, record changed current pins as expected. No regrading old A7S.
- [x] Review the scoped diff and update roadmap, memory and a new receipt/report.
  Retain existing receipts and other WIP. No stage/commit/push/PR/Actions/deploy.

Final verification:233 focused tests pass. Repository offline command completed:
3058 passed,2 skipped,90 deselected,1 pre-existing failure in
`test_routing_diagnostic.py::test_exposed_dev_requests_preserve_facts_scope_and_consent[DEV-Q002]`.
Reproduced that exact assertion on pre-repair source with matching hashes for
all three routing/answering/support files. It expects answered for a standard+
talent question, whereas the existing strict single-variant contract clarifies.
Do not weaken scope or change old gold/test to claim a green repository suite;
review that legacy-test contract separately. This plan's repair is focused-test
verified, not a claim of whole-repository green or independent A7 acceptance.
