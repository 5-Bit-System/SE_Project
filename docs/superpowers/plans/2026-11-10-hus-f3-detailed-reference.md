# Detailed F3 AI reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for code tasks. Independent content batches may use superpowers:dispatching-parallel-agents; no shared output files.

**Goal:** Produce a reproducible, isolated F3 v2 candidate for all four majors with richer content/objectives, no exercises or assessment suggestions.
**Architecture:** Immutable current-release identity inputs plus authored per-code JSON profiles feed a separate deterministic exporter. It produces AI-labelled records/documents/semantic chunks and a checksummed candidate manifest. Existing runtime, CURRENT, v1 builder/data, F2 facts and evaluation artifacts are untouched.
**Tech Stack:** Python, JSONL, pytest, existing HUSRAGRetriever with an explicit candidate snapshot for offline checks; no new dependencies/provider calls.
**Spec:** `docs/superpowers/specs/2026-11-10-hus-f3-detailed-reference-design.md`

## Global Constraints

- User correction removes exercises and assessment criteria entirely from new candidate.
- Preserve four-major/290-membership/174-code coverage and canonical F2 identity.
- Keep AI disclosure/opt-in, official fields null, academic_verified=false.
- Candidate only; no CURRENT/vector/default/provider/key/commit/push changes.
- No word-count or test-count claim substitutes for content review.

## Review Focus

- Duplicated or missing profiles must fail before any output is written.
- A chunk extracted alone must retain scope and AI disclosure.
- Long units must not be silently truncated or lose their example.
- Same-code memberships must not borrow facts/provenance from another major.
- Candidate assessment questions cannot fall through to old suggestions.

### Task 1: Independent authored content and preservation baseline

**Files:** Create `data/hus/qa/20261110/f3_reference_v2/inputs/profiles_{a,b,c}.jsonl`; ignored baseline/ledger in `backups/f3_detail_20261110`.
**Interfaces:** Each JSONL profile has `course_code`, `overview`, `units` (4–8 objects with `title`, `explanation`, `concepts`, `example`), `objectives` (4–6 strings), `references` (primary-source URLs actually checked for conceptual grounding, not HUS syllabus evidence).

- [x] Capture SHA of current F3/F2/selection/release/evaluation source artifacts (594 files).
- [x] Split distinct current-release codes into three disjoint batches; author subject-specific content. No generated filler or official teaching assertions.
- [x] Review/check each code has a meaningful overview, detailed explanations/examples and objectives; no exercises/assessment/rubric fields.
- [x] Leave all changes uncommitted per repository instructions.

### Task 2: Candidate builder/exporter and offline reader

**Files:** Create `app/hus/f3_detail.py`, `tools/prepare_hus_f3_detail.py`, `tests/hus/test_f3_detail.py`.
**Consumes:** Authored profile files + pinned current-release F2/F3 identity records.
**Produces:** `build_candidate(inputs: Path, source_root: Path) -> dict[str, bytes]`; `load_candidate(root: Path, *, allow_generated: bool) -> HUSRAGData` for explicit offline use only.

- [x] Write failing tests for schema/coverage/duplicates, no-assessment, identity preservation, semantic unit export/offset/hash, tampering, opt-in/scoping and current runtime remaining unchanged. Observed initial RED plus metadata/provenance/blank-content RED.
- [x] Implement strict profile validation and deterministic identity-preserving builder. Preserve all authored content in output, including examples; content/objectives are the only fields.
- [x] Export whole semantic units rather than slicing them. Record manifest input/builder hashes, generated labels and candidate status. CLI build refuses existing/protected output; verify compares exact expected bytes.
- [x] Explicit candidate reader verifies checksums and reconstructs original fields from records to reject fabricated chunk bindings; use original F2 through an immutable snapshot. Never read/change CURRENT implicitly or mix old F3 chunks.
- [x] Run focused tests including all four majors, exact opt-in and no old assessment hits; verify GREEN26. Leave uncommitted.

### Task 3: Full data, review and handoff

**Files:** Candidate `release/`, `README.md`, quality report; concise roadmap and project memory.

- [x] Build all 290 profiles and semantic chunks; byte-identical verify and hash-protection checks.
- [x] Offline retrieval checks across four majors for content/objectives and absent assessment; document sample outputs and measured size/budget limits without claiming live LLM quality.
- [x] One independent final review. Fix Important/Critical findings with RED→GREEN, no automatic repeat review.
- [x] Run relevant/full offline tests and Ruff; record results and remaining AI-review limitations. Update roadmap/README/memory with candidate status and next runtime integration step; do not activate it or call Google.
- [x] No commit/push/PR without user request.

## Outcome ? 2026-11-11

Candidate complete:174 codes/290 memberships/703 code-indexed units/704 objectives/1753 chunks; only content/objectives. Byte-identical build/verify and594 protected hashes passed.26focused/2511full offline passed,2skipped/90deselected,Ruff/diff-check passed. Independent AI spot review22profiles+174title inventories found1Minor, corrected with explicit hypotheses; no independent re-review or academic acceptance. Runtime and oldsource/data/evaluation untouched. New runtime integration/release and L5 A/B remain separate next steps. No commit/push.
