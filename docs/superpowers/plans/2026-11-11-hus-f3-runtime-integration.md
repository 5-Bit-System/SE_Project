# F3 v2 runtime integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans; use TDD and one final fresh review. User selected roadmap step1; no repeat design approval.

**Goal:** Integrate the detailed AI candidate into a validated portable release with content/objectives, real API/menu/citation/consent/fallback and rollback checks before selecting a shared runtime release.
**Architecture:** A new release derives from SHA-pinned v3 and the sealed F3 candidate. It inherits F1/F2/evidence unchanged; replaces only F3 records/chunks, unified chunks, release-local evaluation and quality metadata. A strict v4 validator reconstructs these derived artifacts, dispatching old releases through the unchanged v3 checks. Explicit preview root supports normal API use without changing shared CURRENT.
**Tech Stack:** Existing Python/FastAPI/pytest, portable JSONL; no new dependency, provider call or vector rebuild.
**Spec:** User-selected step1 in `docs/RAG_PROGRESS_AND_NEXT_PLAN.md`, and existing detailed-candidate design.

## Global Constraints

- Only F3 content/objectives; no exercises/assessment data or official-source promotion.
- Preserve F1/F2 facts, parent release, candidate, gold/run/review history; lexical and LLM-off defaults.
- Verify integration/rollback before selecting a shared release; prepare a separate root for review, leave canonical CURRENT unchanged in this step.
- Use existing feature branch/WIP; no commit/push/PR/deploy or private .env/template-key changes.

## Review Focus

- Resealed malformed releases must not mix old F3 or fabricated facts/chunks.
- Wrong/missing opt-in, absent assessment and canonical failure never call a provider.
- Same-source unit offsets and AI citation labels remain bound to the exact snapshot.
- Menu offers only available fields; F1/F2 menu entries and facts remain identical.
- Old vector/hybrid index cannot satisfy a new release binding; no silent index reuse.

### Task 1: Release builder and validation

**Files:** new `app/hus/f3_runtime_release.py`, `tools/prepare_hus_f3_runtime.py`, `tests/hus/test_f3_runtime_release.py`; small dispatch in `app/hus/release_validation.py`.
**Interfaces:** `build_release(parent: Path, candidate: Path) -> dict[str, bytes]`, `validate_detail_release(root: Path) -> dict`, `stage_preview(release: Path, out: Path) -> None`.

- [x] Save parent/candidate/history/runtime hashes before mutation; record decisions in ignored `backups/f3_runtime_20261111/progress.md`.
- [x] RED tests: derive exact F1/F2 preservation, 1753 F3 chunks/two fields, full quote offsets, standalone validation, resealed tampering, missing/mixed families, output safety and deterministic CLI.
- [x] Implement strict parent pin/inventory and candidate validation; include the sealed candidate and parent manifest as evidence. Preserve inherited aliases; rebuild only release-local evaluation with per-unit question IDs.
- [x] Add validator dispatch for a known v4 descriptor; v3 path remains intact. Run GREEN and old portable tests.

### Task 2: Real adapter/API/menu and rollback

**Files:** `app/hus/portable_adapter.py`, optional root selection in `app/services/hus_service.py`; new `tests/hus/test_f3_runtime_api.py`.
**Interfaces:** existing `HUSRAGData.load_current(root)`/`HUSAnswerer`/question_catalog; optional process env `HUS_RAG_ROOT` chooses an explicit validated preview root and requires cache clear/restart on change.

- [x] RED four-major content/objectives API tests, absent assessment, consent independence, exact F1/F2 facts/source comparison, no-information/basic/LLM-off and mocked quota/timeout fallback.
- [x] Preserve full candidate unit locators when adapting chunks; menu already follows present fields, prove two-field counts and consent-free requests without hardcoding totals.
- [x] Stage isolated v3/v4 selection and prove v3→v4→v3 restores exact responses/menu/facts after reload; cached/inflight snapshots retain own identity. Wrong index binding rejected.
- [x] GREEN API/old contracts; no shared pointer or env file changes.

### Task 3: Review and handoff

- [x] Additional candidate content spot review beyond prior22; state AI/human limits, fix supported factual findings without editing sealed candidate/history (record errata if any).
- [x] One fresh final technical review; fix material findings with regressions in one pass.
- [x] Full offline suite, relevant Node/browser checks, Ruff, deterministic build/verify, hash preservation and preview smoke. No live Gemini A/B.
- [x] Versioned release and preview commands/runbook/rollback receipt; update concise roadmap/memory. New L5 A/B remains next; canonical selection is not inferred from preparation.

## Outcome

Prepared portable v4 and explicit preview; shared CURRENT remains v3.54new regressions,2565offlinepass/2skip/90deselected,8Node and50browsercases passed. OneImportant review inventory finding fixed RED->GREEN; no independent rereview.10additional AI profile reviews, human0. Byte-identicalbuild/verify and783historicalhashes passed. No liveGemini/defaultenable/indexrebuild/commit/push/deploy. Controlledrelease selection and freshL5AB remain next.
