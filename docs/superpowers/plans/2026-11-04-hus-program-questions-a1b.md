# HUS A1b structured program questions implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, following the user-selected A1b scope. Write failing tests first, verify results and request final scoped code review.

**Goal:** Answer program credit requirements and group lists/rules without requiring a course code.
**Architecture:** Exact scoped lookup of already validated portable `programs.jsonl` and `groups.jsonl`; no retrieval, source mutation or derived arithmetic. Preserve source values, notes and review. Canonical-source citations use hash and JSON pointer with pinned source URL; no invented PDF page.
**Tech stack:** Existing Python/FastAPI/Pydantic and standalone HUS demo.
**Spec:** User-approved A1b row in `docs/RAG_PROGRESS_AND_NEXT_PLAN.md` section 5.

## Constraints and decisions

- Remain on user-requested crawldata with existing WIP; no new checkout copying or commit/push/deploy.
- Q&A remains separate from course recommendations; no eligibility, graduation, scheduling or ranked choices.
- Keep release/CURRENT/raw/review/evaluation gold and all old runs immutable.
- New fields: program_credits, program_groups, group_rules; optional explicit group_key.
- Program questions require exact major/version, respect variant and official/current guards. Course fields preserve A1.
- Program credit value is recorded credits_required; groups retain min_credits_if_selected/offered_credits/group_note, nulls and parent-child distinctions. Never sum them.
- Ambiguous/missing group asks for key; unknown group returns no information. Multiple incompatible scopes/fields clarify without facts/citations.
- Legacy explicit loader has no portable program records, returns none; never reads a second data source.
- Add program entries within existing f2 menu only after API works; update menu tests for optional course_code.

## Steps

- [x] Freeze protected inputs, baseline program diagnostic cases and before outputs.
- [x] RED→GREEN loader defensive-copy lookup, routing/schema and structured answer/citations tests.
- [x] RED→GREEN API guards, group ambiguity/missing/conflict/null/notes and new catalog entries.
- [x] Real browser program-menu/source/scope/AI tests, then scoped peer review and fixes.
- [x] Pinned offline/API/UI/PDF regression, old dev96 and gate20 measurement with unchanged scorers.
- [x] New receipt and brief progress/memory update. No independent Recall claim from dev.

Execution notes: same existing feature branch/WIP, no commit. Explicit approved
A1b row is the binding spec; no additional design approval needed. Extra chat/HTML
help snapshots and one old UI test snapshot are recorded in local scope-extension
manifests. First full regression found10failures (career-group overmatching,
course-title conjunction, UI optionalcourse_code assumption); old tests served as
RED, focused243 passed after fixes. Additional career/program ambiguity test
RED→GREEN; final read-only review no Critical/Important. Final full run is separate
from the failed log, both preserved in backups/program_questions_a1b_20261104.
Final:1763offline/90deselected,50browser,5Node,Ruffpass;devv5 12/12,
olddev96 Recall39/40,F224/24,rawanchor60/64;gate20still20/20.758oldfilesunchanged.
