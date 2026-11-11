# V1 vector index contract implementation plan

> **For agentic workers:** Use superpowers:executing-plans, test-driven-development, requesting-code-review and verification-before-completion. User selected V1 from the existing approved A3 plan. Keep crawldata WIP; no commit/push/deploy.

**Goal / Spec:** Implement V1 in `RAG_PROGRESS_AND_NEXT_PLAN.md` section6: immutable contract binding selected release/corpus, metadata/chunk policies, model/tokenizer/pooling/prefix/dimension/cosine and an optional dependency lock. Lexical offline remains default without ML packages.

**Architecture:** Stdlib contract generator/validator plus small retrieval configuration; a fresh contract-only manifest is not a built/activatable index. Offline CLI emits a source-parent inventory and manifest under a dedicated vector_contracts tree, never release/evaluation/selector paths. Only default-mode validation touches hus_service; vector/hybrid are reserved and explicitly unavailable at V1, not silently advertised as active. No embedding/model/tokenizer/index load in requests or startup.

**Model choice:** Existing approved multilingual-e5-small at immutable Hub commit614241f622f53c4eeff9890bdc4f31cfecc418b3,384dimensions,512tokens,query:/passage: prefixes,masked mean+L2,cosine,CPUfloat32,safetensors,trust_remote_code=false. Use AutoModel/AutoTokenizer directly with torch/transformers; no sentence-transformers wrapper needed. Small configs are downloaded/hash-verified; weights/tokenizer large artifacts remain remote expected LFS hashes, explicitly not locally verified. V2 splitting/build pending.

**Dependencies:** Separate WindowsAMD64/CPython3.11 complete hash lock, constrained by existing requirements-lock, generated with a SHA-verified standalone uv in ignored backups. Resolve/download metadata only; no ML install,model weights or changes to core lock/environment. Compatibility here is resolver-level,not a claim of tested inference.

## Review focus / constraints

- Corpus exactly eligible F1/F3 parents from loaded canonical v3,including generated metadata without granting runtime opt-in; F2/evaluation QA/gold excluded. Inventory binds body/full metadata/provenance so scope/review changes invalidate identity.
- Optional imports unavailable or maliciously shadowed must not affect lexical startup/answering. Reserved/invalid mode must be explicit; never fake vector usage.
- Rebuild contract deterministically from trusted local inputs; reject edited manifest/inventory/stale locks/model profiles/release,not just a self-rehashed untrusted JSON.
- Writer allows fresh directory only under vector_contracts,not old artifacts/nested contracts/symlink escapes. No CURRENT or source review promotion.
- Chunk-policy names describe future tokenizer splitting; no fabricated passage count,token counts,index,local weight checksum or Recall improvement.

## Tasks

- [x] Freeze protected old files/environment and write failing contract/config/CLI tests.
- [x] Generate verified model profile and optional complete lock; implement contract/config/CLI minimally; GREEN targeted tests.
- [x] Scoped fresh technical review; fix Critical/Important via RED/GREEN in one pass.
- [x] Final offline/UI/API/source regression; verify contract reproducibility/tamper guards,model checksum provenance,optional-import isolation,old artifacts/environment unchanged; new receipt/report/archive and progress/memory update. V2 is next,not implemented.

## Ledger

- Setup: user selected V1 as bounded approved step. Small public metadata network read required sandbox escalation; no model/provider calls. Stay on user-named crawldata WIP with before-images/hashes. Browser verification uses official Hub/PyPI/docs; lock resolver is local helper,not an application dependency.
- Task1/2: protected1057oldfiles/environment. RED33missing-contract/config cases ->initialGREEN32pass/1skip. Root namespace redirection and stale resolver input probes RED4 ->fixed. Modelprofile9artifacts,6tinyconfigs hashchecked vsGit;3largeLFS hashes expectedonly,notdownloaded. Windows/CPython3.11 lock112packages,uv0.13.7SHAverified; metadata resolution only. Core source inputs3 and lock hashes bound; current environment unchanged.
- Final review:1Important JSON equality identity issue (False==0,int==float),noCritical/Minor. Added7cases RED7fail/25pass/1skip ->GREEN44pass/1skip,Ruffpass. Recompute unsigned digest and compare canonical JSON bytes for both manifest/inventory; no second review per skill.
- Final: Ruling: actual inference/tokenizer/V2splitting/Chroma integration and local large-artifact hashes remain deferred; expected remote metadata is not local verification. Actual Windows junction unavailable, guard covered with simulated resolution and real symlink test skipped. Root verifies full regression/old hashes separately. Cost: no readiness,quality or installed-dependency compatibility guarantee at V1; mode stays lexical and missing clean contract inputs fail closed.
- Final verification complete:1926passed/1skip/90deselected,50Chromium,5Node,Ruffpass;1057protectedoldfiles/environment unchanged. CLIprepared+verifiedsame935-parent contract IDb24679900bd835304dd5cf2bce285f531a241e7514ba51b02b568c801946f143;3freshlexicalruns180responses/traces identicalto1a. Archive341code/profile/contract/lockfiles,no modelweights. Report/receipt/progress/memory updated. No new semantic or vector-quality claim; V2next,notstarted.
