# HUS offline vector index V3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline with one fresh final technical review.

**Goal:** Produce and reopen an offline Chroma index of the frozen 939 V2 passages, using real local E5 embeddings with verified model/tokenizer provenance.

**Architecture:** Explicit download/preparation runs in an isolated hash-locked ML environment. A lazy CPU encoder verifies all model bytes and V2 token IDs, then attention-mask mean pools and L2-normalizes 384-dimensional float32 vectors. An offline index writer verifies V1/V2/canonical inputs, writes a fresh Chroma PersistentClient collection with explicit embeddings, and seals a manifest only after full coverage/readback. Verification in a separate process checks every stored vector/metadata/ID and deterministic probe results. Runtime remains lexical; V4/V5 are separate.

**Tech Stack:** Python3.11 WindowsAMD64; immutable requirements-rag-vector-lock.txt (torch2.15.0, transformers5.22.1, chromadb1.5.9, tokenizers0.23.3); pytest and existing UI regression.

**Spec:** User-selected V3 row and section6 of docs/RAG_PROGRESS_AND_NEXT_PLAN.md; frozen V1 contract and V2 passage manifest.

## Global Constraints

- User-selected crawldata checkout; no reset/stash/rebase, new worktree, commit, push or deployment. Preserve existing WIP.
- Freeze every existing app/test/tool/source/evaluation/profile/contract/passage/receipt/lock file before changes; preserve core installed environment.
- Model intfloat/multilingual-e5-small, revision614241f622f53c4eeff9890bdc4f31cfecc418b3; all9 artifact sizes/SHA256 must verify before inference.
- Every passage must match the actual fast AutoTokenizer input IDs from V2, including passage prefix/special tokens; truncation=false, max512. No remote model code or implicit downloads.
- Model eval/inference mode, CPUfloat32, masked mean then L2,384 dimensions, cosine; finite/nonzero/unit vectors; duplicate IDs forbidden (equal vector contents across different IDs are valid).
- Index only canonical F1/F3 passages; F2/QA/gold/transcripts excluded. Do not read evaluation packs during build.
- Metadata includes family, major, version, variant, course_code, field, review_status, content_origin, release identity, parent_id/source_id and opt-in requirement. Retain hashes needed for canonical revalidation.
- New index directory only; never overwrite/nest inside frozen index. Explicit embedding_function=None and telemetry disabled; no default Chroma embedding/model.
- Manifest binds release/V1/V2/model/dependencies/config/vector inventory; no CURRENT/default activation. Generated F3 remains needs_review and opt-in required.
- Reopen in another process and verify exact ID/metadata/vector inventory, cosine config and probe IDs/distances within recorded numeric tolerance. This is persistence verification, not Recall acceptance.

## Review Focus

- Wrong wrapper tokenizer IDs, truncation or pooling: detect before index creation.
- Partial index/build failure or reused path: no valid sealed manifest, no overwrites.
- Self-rehashed manifest or DB tampering: compare against current canonical inputs and sealed vector inventory.
- Missing/reordered/extra/duplicate passage IDs, metadata boolean/int substitutions, NaN/zero/wrong dimension vectors: fail closed.
- Optional modules absent, mismatched lock, model cache corruption or redirected root: lexical imports remain independent, preparation reports explicit failure.

## Task1: Real encoder and verified model cache

Files: new app/hus/embedding.py; tests/hus/test_embedding.py.

- [x] Freeze old files/environment in backups/vector_index_v3_20261109; record branch/HEAD and existing docs WIP.
- [x] RED unit tests for artifact checks, optional imports, token ID/budget and vector validity; actual tensor acceptance checks masked pooling.
- [x] Implement lazy loader/encoder; GREEN. Bootstrap isolated venv with the existing hash lock, never alter core venv.
- [x] Explicitly download pinned model files; verify all sizes/SHA. Run real wrapper-ID comparison over all939 passages and real encoder smoke.

## Task2: Immutable offline Chroma index

Files: new app/hus/vector_index.py, tools/build_hus_vector_index.py, tests/hus/test_vector_index_build.py; optional-runtime integration checks in ignored acceptance workspace.

- [x] RED tests for scoped scalar metadata and vector inventory, coverage, invalid vectors/IDs/provenance, fresh output and malformed/tampered manifests.
- [x] Implement pure validation plus real PersistentClient build/readback with explicit embeddings; GREEN.
- [x] Build fresh data/hus/vector_indexes/e5_small_v3_20261109 (or a new numbered attempt after failure, never overwrite). Keep large model/cache/ML venv outside Git in backups.
- [x] Verify saved index in another process, compare probe results with before-exit receipt; no runtime query integration.

## Task3: Review, regression and evidence

- [x] One fresh technical AI reviewer of complete V3 changes; one RED/GREEN fix pass for confirmed Critical/Important findings, record deferred minors.
- [x] Run core offline project pytest, Node5, Chromium50, Ruff; optional real model/index acceptance in isolated environment.
- [x] Verify every protected old file and core installed package unchanged; replay cached lexical runs, no new Recall claim.
- [x] Write docs/RAG_OFFLINE_VECTOR_INDEX_V3_2026_11_09.md, new acceptance receipt and reproducible archive/manifest; update progress/memory V3done,V4next with actual results and limitations.

## Ledger

- Start: crawldata HEAD884838b; existing 09/11 V2 recheck docs/memory/receipt retained.
- Ruling: Work in the explicitly user-selected crawldata checkout with before-image hashes rather than move existing work to a new worktree. Cost if wrong: isolation relies on hash checks; no concurrent edits to protected files can be accepted silently.
- Ruling: Preserve ignored logs/cache and before-images while the work remains uncommitted. Cost: local disk usage; no destructive cleanup without a committed record.
- Ruling: Chroma binary contents can vary across independent HNSW builds; V3 promises complete stored vector identity and stable results after reopening this sealed build, with numeric tolerance, not byte-identical databases across machines. Cost: V5 must measure retrieval quality separately.
- Ruling: Actual AutoTokenizer/XLMRobertaTokenizer in locked Transformers5.22.1 reconstructs the SentencePiece whitespace pre-tokenizer and drops a trailing token on passage235a29b3...#p000 (377 vs V2's378). Use PreTrainedTokenizerFast directly with the verified tokenizer.json graph; an explicit probe matches all939 V2 ID hashes. Preserve all V1/V2 data and record default AutoTokenizer incompatibility. Cost: future inference must keep this explicit wrapper and repeat the ID check; default AutoTokenizer is not interchangeable.
- Ruling: Actual Chroma1.5.9 restart configuration reports cosine/construction/search/neighbors/sync but omits num_threads and batch_size. Keep both as requested build controls, require all persisted settings, compare optional controls if exposed, and document that their restart persistence is not certified. Cost: restart thread/batch defaults may affect performance; stable results are checked by the eight actual probes instead of assuming identical configuration projection.
- Task1 complete: 17unit tests GREEN; all9 model artifacts hash-verified in separate cache,112locked packages installed in isolated venv; actual masked mean/padding tests and all939 wrapper ID hashes pass after observed AutoTokenizer RED.
- Task2 complete: index8dad2f0f719a5228403d87f2b0c36a95f64fada9b82bf26bf432d4fed2469f74,939vectors/935parents,F1=69/F3=870; separate-process exact inventory/8probe verification PASS. All old inputs retained.
- Final review: 0Critical,2Important,noMinor. Observed RED2/33 for NaN restart distance and unexpected stored documents; fixed both with finite-distance validation and document-free readback. GREEN35. Actual restart configuration projection regression RED2/20, then GREEN39 including default-embedding-function rejection. No re-review requested.
- Final: reviewer declined to certify pending build/restart/regression/archive evidence; these remain Task3 completion gates, not waived behavior. No new outside-scope functionality is required to satisfy them.
- Acceptance runner recovery: pytest2019passed/2skip/90deselected completed; scratch runner then tried to rewrite the exclusive commands.json after Node passed. Fixed scratch logging and resumed remaining commands into fresh logs/commands_complete.json; retained the original pytest/JUnit and Node evidence, no product test failure or whole-suite rerun.
- Task3 complete: 39newtests,2019offlinepassed/2skip/90deselected,50Chromium,5Node,Ruff; 5real copied-DB tamper cases rejected,3cachedlexicalreplays,1108oldfiles/coreenvironmentunchanged.357file code/inventory archive and new acceptance receipt written. Final read-only check PASS; runtime still lexical,V4next. No minor findings deferred.
