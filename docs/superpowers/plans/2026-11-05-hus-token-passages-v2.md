# HUS token passages V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans, task-by-task, with one fresh final review.

**Goal:** Prepare reproducible token-bounded embedding passages from the frozen V1 parents without losing source content or changing chatbot behavior.

**Architecture:** Load the hash-verified local native E5 tokenizer lazily in an offline preparation tool. Split original canonical body strings, count complete prefixed inputs, retain parent provenance, and write a separate immutable V2 artifact. Runtime stays lexical.

**Tech Stack:** Python 3.11, stdlib, optional locked tokenizers 0.23.3; pytest, existing API/UI checks.

**Spec:** User-selected V2 row and section 6 of `docs/RAG_PROGRESS_AND_NEXT_PLAN.md` (05/11/2026).

## Global Constraints

- V1 contract/profile/lock and old data/evaluation runs remain byte-identical; F2 remains structured lookup.
- Count actual tokens including `passage: `, context (V1: empty), and special tokens; limit 512 total, target <=400 content, overlap <=64 actual content tokens.
- Preserve every original character, including trailing content/whitespace; no decoding/reconstruction or silent truncation.
- Each child belongs to exactly one parent; scope/review/generated opt-in metadata and source hashes remain bound.
- Body offsets are local Unicode character offsets, never source offsets; citation and gold resolve against canonical parent.
- No weights, vectors, Chroma, online provider, source promotion, commits, push, or deployment in V2.
- Use the existing user-selected crawldata WIP; protect before-images instead of moving unrelated work.

## Review Focus

- Unicode normalization, emoji, repeated/zero token offsets: preserve literal text and terminate or explicitly fail.
- Prefix/context alone exhausting the window: fail explicitly, never truncate the evidence.
- Trailing whitespace and long unbroken text: retain complete coverage, including final character.
- Self-rehashed tampered metadata/counts/offsets: rebuild against current canonical parents and tokenizer bytes.
- Optional dependency absent, wrong version, corrupt cache, redirected output: fail preparation without affecting lexical startup.

## Task 1: Verified local tokenizer and lossless splitting

Files: create `app/hus/passage_tokenizer.py`, `app/hus/passages.py`, `tests/hus/test_passages.py`, `tests/hus/test_passage_tokenizer.py`.

- [x] Freeze old files/environment in ignored `backups/vector_passages_v2_20261105`.
- [x] Write tests for actual counting contract, preservation, overlap, prefix/context budgets, invalid offsets, missing/corrupt cache; observe RED.
- [x] Implement lazy native adapter and original-string splitter; observe GREEN.
- [x] Explicitly fetch pinned tokenizer JSON into a separate cache; verify SHA/size. Bootstrap only locked native wheel in an ignored isolated runtime, with wheel hash provenance; keep core environment unchanged.
- [x] Run real-tokenizer Unicode/boundary tests in isolated runtime; document that Transformers/inference compatibility remains V3.

## Task 2: Parent-bound preparation artifact

Files: extend new passages module; create `tools/prepare_hus_passages.py`, `tests/hus/test_passage_artifact.py`.

- [x] RED tests for complete parent coverage, unchanged metadata/locator, local offset semantics, immutable output, tamper rejection, CLI.
- [x] Build/verify V2 manifest and passages JSONL deterministically from V1 and canonical data; GREEN.
- [x] Prepare fresh `data/hus/vector_passages/e5_small_v2_20261105`; verify every input token count and complete source body coverage with the real tokenizer.

## Task 3: Review, regression and evidence

- [x] One fresh technical review; re-grade findings; one RED/GREEN fix pass for confirmed Critical/Important issues.
- [x] Run offline project pytest (report external DB/catalog exclusions), Node and Chromium UI checks, Ruff, real-tokenizer checks.
- [x] Verify protected old files, V1 contract and core installed packages unchanged. No new quality claim from unchanged lexical metrics.
- [x] Write `docs/RAG_TOKEN_PASSAGES_V2_2026_11_05.md`, a JSON acceptance receipt, and update progress/memory: V2 done, V3 next, with actual counts and limits.

## Execution ledger

- Start: branch crawldata, HEAD1287e2a, existing WIP retained; V1 is frozen and runtime remains lexical.
- Ruling: Cache only the pinned `tokenizer.json` needed by native Tokenizers, rather than downloading unrelated configs/weights. The full fast-tokenizer graph is sufficient for V2 counts; V3 must verify the selected inference wrapper produces identical IDs before indexing. Cost if wrong: V3 must regenerate passages under a new policy, never silently reuse incompatible inputs.
- Ruling: Retain ignored verification before-images/logs because changes are uncommitted user WIP. Delete-on-commit workspace cleanup does not apply before a commit exists; cost is local disk usage only.
- Completed: Passage Set ID `bc9c992887f33f16b7c53a0a5b3b905b046fe24af497972f56e0fdc3987231fb` (`data/hus/vector_passages/e5_small_v2_20261105`), 935 parents -> 939 passages (4 F1 split), max input 392/512, max content 388/400, max overlap 64/64; 55 new tests (54 passed, 1 skipped), 1980 total offline passed / 2 skipped / 90 deselected, 50 Chromium, 5 Node, Ruff passed; 1094 protected old files and core environment unchanged; 349-file archive at `data/hus/evaluation/vector_passages_v2_snapshot`.
