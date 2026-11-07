# Diagnostic career role routing and teaching exclusion implementation plan

> **For agentic workers:** Use superpowers:executing-plans, systematic-debugging, test-driven-development, requesting-code-review and verification-before-completion. Execute inline on the user-selected crawldata WIP. No commit/push/deploy.

**Goal:** Fix original dev6 C003 role-only enterprise routing and C007 teaching exclusion without changing historical questions/gold/runs or source eligibility.

**Spec:** User-selected step1a in `docs/RAG_PROGRESS_AND_NEXT_PLAN.md`, section3 diagnostic gaps. Source scope/review/AI opt-in and immutable quotes are mandatory.

**Architecture:** Two existing files: `question_routing.py` recognizes role questions only with workplace context and without explicit course/objective/content intent; shared bounded career-refusal parsing separates excluded teaching from active question clauses. `answer_support.py` drops whole F1-careers hits mentioning the explicitly excluded teaching topic before source-group coverage. Keep original canonical quotes and fail closed when remaining evidence is insufficient. Do not delete words from quotations, widen top-k, change BM25 or invoke vector/LLM.

**Tech stack:** Existing Python/FastAPI/Pydantic/pytest and pinned lexical v3 release; no new dependency.

## Constraints / review focus

- Preserve all old runtime files except these two, all existing tests/tools/gold/release/reviews/receipts/runs. New test module and immutable new exposed dev pack/runs only.
- Role in a course/program/objective must not become a career intent; preserve F2/program priorities and scope filters.
- Only explicit request exclusion (`không hỏi/cần/trích…giảng dạy/giảng viên/giáo viên/dạy học`) suppresses a topic. Factual negation, unknown topics, later affirmative clauses/numbers/official requests remain active.
- Filter complete source bodies, not titles; never use excluded passages to satisfy required evidence, or merge other source/edition/review groups to compensate.
- Mixed teaching/enterprise chunk cannot be silently edited. Without another clean supporting source, refuse instead of guessing or claiming no teaching careers exist.
- AI semantics is answer-level, exposed/non-independent; inherited judgments require identical request/response/gold/audit hashes. Re-read changed cases, report failures honestly.

## Task 1 — RED/GREEN on frozen diagnostic inputs

- [x] Snapshot current code, preserve protected hashes, freeze new exposed cases and record C003/C007 before responses.
- [x] Add `tests/hus/test_career_role_exclusion.py`: original cases, accentless/synonym/punctuation forms, objective/course priority, exclusion vs factual negation/later positive claims, mixed-quote fail-closed, source grouping and metadata-only exclusions.
- [x] Watch tests fail for the two actual bugs, then implement the smallest change in the two files and verify new/existing routing/support/F2/opt-in tests.

## Task 2 — review and new pinned measurements

- [x] Fresh scoped technical review, Critical/Important fixes by RED/GREEN in one pass; record rulings/minors.
- [x] Final full offline/Node/Chromium/API/source regression on stable code/data/tests/environment.
- [x] New runs: dev96,H2exposed56,F2contracts28,original dev6,r2dev6,new diagnostic pack. Reuse unchanged evaluator, no gold in requests; compare response/actual retrieval trace with prior runs.
- [x] Read changed/new responses; create bound AI overlays with explicit inheritance provenance for identical prior readings. Reproduce cached metrics, check protected old artifacts, archive code delta, write new receipt/report and update progress/memory.

## Ledger

- Setup: approved step1a already specifies intent and scope. Keep the explicitly selected crawldata WIP in place with before-images/hash protection; no new integration/worktree/commit. Both bugs reproduced in previous frozen diagnostics; now establish fresh before evidence.
- Task1: frozen dev7 before tuning14cases (12positive+2edition controls);968oldfiles protected. Initial RED23failed/17passed; initial GREEN313focused. Two production files only.
- Final review: no Critical/Minor findings;2Important (noncareer subjects misrouted,qualified refusal context promoted/globalized). One fix pass: nine added regression cases RED9failed/40passed →GREEN322focused;49newtests total,Ruffpass. Role inference now question-form and explicit course/program/corporate-subject guards. Refusal consumes its bounded workplace and preserves it as exclusion scope; requested school context must be supported. Mixed quotes remain intact or rejected,not edited.
- Final: Ruling: reviewer set aside unrelated WIP, general language/ranking/source/eligibility semantics, historical artifacts and broad regression — keep this bounded Q&A fix, retain all source validity/review/opt-in limits and let root verify full regression/hash/replay separately. Cost: no general semantic or institutional-validity guarantee; no completion until final checks pass.
- Task2 complete:1882offline/90deselected,50Chromium,5Node,Ruffpass;968oldfiles unchanged,only2runtimefiles differ. Sixfreshmeasurement+sixAIoverlay replays match. Dev96/H2/contracts responses+traces identical to post-Q027; originaldev6C003/C007 fixed,r2C007 fixed,AIcomplete8/8each. Dev7positive12/12,controls2/2. AIread17/inherit197 with exactfourhashbindings,human0,notindependent. Archive329files preservesWIPbytes; old A2/Q027 receipts and baselines retained. Full report/receipt and progress/memory updated; A3next,notstarted.
