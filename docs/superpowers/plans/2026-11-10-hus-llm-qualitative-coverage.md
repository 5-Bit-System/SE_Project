# HUS LLM qualitative coverage repair

**Goal:** Reject omission of nonnumeric source ideas in F1/F3 through a general,
conservative source-unit coverage policy, preserving old runs/gold/review.
**Root cause:** v1 enforces citation/anchor/numeric atoms, not whether rendered text
retains each sentence/clause. DEV-Q025 keeps1993 andcitation1 while dropping a second
nonnumeric sentence. A fuller anchor or model-declared coverage alone cannot prove it.
**Approach:** Deterministic sentence/newline/semicolon units with original spans.
Every nonempty unit must be retained as ordered normalized word tokens in a rendered
point of its own citation whose anchor contains that whole unit. No stopword removal,
synonym assumptions, topic keywords, ratios or case-specific phrases. Existing
ID/anchor/atom/security/budgets still apply. Version the prompt to describe the policy;
keep wire output schema and F2 style-only contract.
**Tradeoff:** Conservative extract-preserving rewriting permits added neutral phrasing
but may reject valid synonyms/reordered paraphrases; uncertainty falls back. This
reduces lexical omissions, not proof of entailment/negation scope/completeness in
general. No LLM judge, external calls, default enable, source/retrieval or oldrun edits.

## Tasks

- [x] Freeze old L5/L6 manifest/input hashes and capture a reconstructed diagnostic
  JSON equivalent of saved DEV-Q025 B; label reconstruction, never provider raw.
- [x] RED regression for Q025-equivalent omission; synthetic F1/F3 numeric-free
  sentences/list/semicolon omissions, false full anchors, cross-citation coverage.
- [x] Add coverage.py deterministic unit/token checks, connect after v1 checks, promptv2.
  Verify complete evidence accepted, formatting/Unicode handled, F2 unchanged.
- [x] Pipeline tests prove HTTP200 but missing idea gives canonical fallback, not used;
  no additional HTTP/retry. Pin old outputs' new verdicts as diagnostic only, not newAB.
- [x] Independent review once; 0 Critical/0 Important/0 Minor, no findings to fix.
- [x] Full offline/Node/Ruff/diff, preserve old artifact hashes. New runtime pins make
  old L5 evidence stale; do not alter the L5/L6 assessor or expected old failure.
- [x] New repair report/receipt, update concise roadmap, README/spec/memory. Step1
  engineering complete; step2 fresh AB/content review and activation remain pending.

Outcome: 25 new regressions, 431 focused and 2485 full offline passed; 2 skipped,
90 deselected; 8 Node tests, Ruff/diff-check passed. Fifteen historical artifact
hashes unchanged. Diagnostic v1 accepts omission/v2 rejects it; complete source is
accepted by both. No new provider calls or activation. Lexical retention is not
semantic acceptance; fresh pinned L5 A/B remains the next step.
