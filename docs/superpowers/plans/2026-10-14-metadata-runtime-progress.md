# Nghiệm thu phần A — Metadata/runtime và nền kiểm thử

Phần A đã hoàn thành. Kế hoạch triển khai chi tiết đã được gỡ khi dọn tài liệu; bản này giữ kết quả nghiệm thu, quyết định kỹ thuật và giới hạn kiểm chứng.

## Pre-flight

- A1 → A2 → A3 share source contract and normalization. A4 supplies independent synthetic fixtures for all layers; A5 operates on domain Course/catalog rules.
- User authorized parallel agents and a high-capability strategist. Ownership: root A1/A2/integration; fixture agent A4; progress agent A5; strategist read-only design/final review. No automatic commit/push.
- Ruling: preserve actual seed keyword `source_root`, not planned `data_root`, for backward compatibility. Cost if wrong: callers using the plan's new keyword must use the documented actual signature.
- Ruling: typed Course fields require a minimal scoring/LLM metadata accessor compatibility update in A1; topic matching and ranking features remain phase B. Cost if wrong: existing metadata-dependent behavior would regress until B.
- Ruling: retain legacy ingestion as explicitly identified branch; enforce new evidence contract on envelope inputs, never claim legacy evidence verified. Cost if wrong: old DB data would cease being readable.
- Ruling: source revision stays separate from DB content hash; no schema replacement is planned. New JSONB payload can preserve envelope/vocabulary.
- Ruling: implement in current `codebase` working branch; preserve pre-existing memory edit and planning docs, no commit or worktree churn.

## Acceptance status

- A1: complete — strict envelope plus common normalizer, full field evidence, versions/identity/null preservation and explicit legacy branch. Real sample loads 65 courses. Typed metadata remains visible to existing scoring/LLM adapters.
- A2: complete — runtime invokes shared validator; invalid OR/cycles/external mappings and inconsistent group/path/block memberships rejected. Unknown/conflict cannot unlock courses. Builder derives quotas, preserves advisory metadata/evidence/envelope extensions and blocks additions/removals/prerequisite changes requiring review.
- A3: complete — JSON/Postgres catalog/profile round-trip and eligibility equivalence verified on isolated PostgreSQL 16. Raw source bundle hash includes envelope/vocabulary/evidence/source rows/profiles; idempotence/history/rollback/FKs and migration cycle pass. No new schema migration needed.
- A4: complete — independent synthetic 4×14-course/12-profile fixtures replace copied backup catalogs. Unit/integration roots isolated; full source acceptance is explicit and absent-source failure is not hidden. CI split offline/Postgres; remote CI not verified.
- A5: complete — excluded credits/GPA fixed, duplicates rejected without guessing retake policy, typed progress exposed by both transcript-summary APIs with optional track/path selectors and draft warnings.

## Review of Gemini handoff — 2026-10-15

Initial rerun: **66 passed, 14 failed, 13 skipped**; Ruff and sample builder passed, but this did not establish A1/A2 completion. Important holes reproduced as tests before fixing: missing prerequisites/counting fields silently defaulted; hours union bypassed negative validation; missing/invalid source/evidence/vocabulary accepted; runtime bypassed structural validator; builder discarded courses and retained stale prerequisite status/evidence. The restored fixtures were replaced with small invented data, not retained as source datasets.

Independent adviser (GPT-6 Astra/high) checked design and final implementation without editing. Original seven issues were addressed. Final review found prerequisite conflict evidence/status contradiction and reciprocal-membership omissions; both reproduced with failing entrypoint tests and fixed in one pass. No remaining Important/Critical finding was reported in the reviewed code.

## Fresh final verification — 2026-10-15

- Default `.venv/Scripts/python.exe -m pytest -q --tb=short`: **108 passed, 26 skipped**, one Starlette/httpx deprecation warning. Skips = 16 PostgreSQL tests without explicit URL + 10 full-source acceptance tests.
- Same command with explicit TEST_DATABASE_URL targeting a separate temporary PostgreSQL container at 127.0.0.1:55432: **124 passed, 10 skipped**, same warning. Only missing full-source acceptance skipped; every PostgreSQL integration test executed.
- `.venv/Scripts/python.exe -m ruff check .`: pass.
- `.venv/Scripts/python.exe -X utf8 tools/build_catalogs.py --check`: pass, retained 65-course sample.
- Same builder command with `--root tests/support/fixtures/catalogs`: pass, four synthetic 14-course catalogs.
- `git diff --check`: pass; repository line-ending warnings only. Source JSON under `data/` unchanged.
- Builder `--write` tested only on temporary copied sample, preserving full advisory/evidence/header extensions.

## Rulings and remaining work

- Ruling: prerequisite/code-set changes in envelope builder require source review rather than generating new unreviewed records silently. Cost if wrong: intentional source changes need a separate reviewed data update; this protects existing evidence and revision identity.
- Ruling: metadata vocabulary travels on domain Catalog so standalone validation uses the same version/labels as initial import. It is not injected into Program metadata. Cost if wrong: Catalog serialization includes the vocabulary document; public course/program endpoints keep their existing boundaries.
- Ruling: reject duplicate course codes across terms until an explicit retake/GPA policy is provided. Cost if wrong: retake transcripts cannot yet be represented; no arbitrary grade is selected.
- No automatic commits, pushes, source restoration, product seeding or product DB migration were performed. Pre-existing project memory edit retained.
- Phase B/C/D, full four-program source review and 12 product demo profiles remain outside completed A. Ten full-source acceptance tests remain unverified, not passed. Browser/model-provider and remote CI checks were not performed.
- Deferred minor: dependency emits Starlette/httpx deprecation warning; no dependency upgrade in this scope.

Stop condition: difficult blocker without a credible fix or repeated timeouts → stop dependent work and report evidence to the user.
