# Project Memory and Contributor Guidelines

## Core Operating Rules: Subagent Usage, Progress Transparency, and Frequent % Reporting — 2026-11-11 (Pinned Top)
- **Báo cáo tiến độ (%) thường xuyên (BẮT BUỘC ở mọi lượt)**:
  - Trong **mỗi lượt phản hồi hoặc cập nhật trung gian** (kể cả khi đang thực thi tool, theo dõi tác vụ nền hay chốt kết quả cuối), agent **PHẢI mở đầu bằng tổng tiến độ phần trăm cụ thể** (ví dụ: `**Tiến độ tổng thể: 40%** — ...`).
  - Đối với công việc nhiều bước hoặc tác vụ chạy lâu, phải cập nhật tiến độ `%` đều đặn theo từng cột mốc hoàn thành, nêu rõ bước vừa xong, việc đang làm và phần còn lại; chỉ báo `100%` khi đã kiểm chứng hoàn tất toàn bộ.
- **Minh bạch hành động & Không treo trạng thái running**: Bất kỳ khi nào làm việc gì, agent phải hiển thị rõ ràng ra màn hình cho người dùng biết (các bước đang làm, lệnh/file đang thao tác), tuyệt đối không để im lặng hoặc hiển thị toàn bộ dưới dạng "running" mơ hồ.
- **Subagent Policy**: Chỉ dùng subagent khi thực sự cần thiết (cho các tác vụ nghiên cứu sâu độc lập hoặc tác vụ song song không chung state). Main agent phải trực tiếp kiểm soát, giám sát tiến trình liên tục, không để bị delay, và chủ động thực hiện trực tiếp các chỉnh sửa cụ thể để đảm bảo tốc độ cao nhất.

## Product Workspace and standalone HUS RAG

The main application serves the **Tra cứu thông tin** tab and the HUS routes,
including account-scoped chat history. Use the root README for application setup
and database migrations. The portable Windows launchers serve a loopback-only
demo and use the pinned v4 source and offline checks. The demo uses its own
backend-only Gemini settings and does not require the product database.
See [the HUS RAG quickstart](../docs/HUS_RAG_QUICKSTART.md) and
[the LLM operations guide](../docs/HUS_LLM_OPERATIONS.md).

Measurements below document the named branch, code and data snapshots.
All changes to main go through a feature branch and a pull request using
**Create a merge commit**, preserving original authors and commits.

## History-only reconciliation of `origin/hus-llm-rag` (`f61b0fd`) into `feat/workspace-hus-lookup-20261111` — 2026-11-11

With explicit user authorization, reconciled `origin/hus-llm-rag` (`f61b0fd`, 20 commits `cf3f87f..f61b0fd` authored by `Duong Van Tai <duongvantai2048@gmail.com>`) into `feat/workspace-hus-lookup-20261111` via history-only merge commit `8012f31` (`git merge -s ours`) ahead of opening the PR to `main`:
1. **Scope & Disclosed Boundaries:**
   - **Ancestry preserved:** Both `hus-embedding-chromadb` (`13fa6cd..1aca071`, 25 V1–V5 commits) and `origin/hus-llm-rag` (`cf3f87f..f61b0fd`, 20 LLM/F3-v4/A7 commits) are genuine ancestors of `feat/workspace-hus-lookup-20261111`, preserving original commit hashes and author identities without rewriting or manufacturing commits.
   - **Active tree unchanged from `85bd371`:** Keeps the Workspace Lookup tab (`#tab-lookup`, `app/hus/router.py`, `app/hus/chat_history_repository.py`), `app/hus/llm_answerer.py`, and `hus-data-20261031-v3` (`data/hus/rag/CURRENT.json`). The parallel `app/hus/llm/*` pipeline, `app/hus/f3_detail.py`, `app/hus/f3_runtime_release.py`, and `hus-data-20261111-v4` from `origin/hus-llm-rag` remain unmerged functionally.
   - **Local uncommitted exclusions:** Untracked `.vscode/`, `uv.lock`, `previews/`, and 4 dated markdown review notes in `docs/` remain outside Git.
2. **Pre-push Local Verification (matching `85bd371` product tree):**
   - `pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"`: **2537 passed, 2 skipped, 148 deselected** (1 existing Starlette `httpx` deprecation warning).
   - `PYTHONHASHSEED=1` and `PYTHONHASHSEED=2` on `tests/database/source/test_reviewed_prerequisites.py::test_optimization_requires_every_own_major_prerequisite`: **4 passed** each.
   - `ruff check app tests tools database`: **All checks passed** (untracked local `previews/admin-dashboard/build_data.py` excluded).
   - `tools/build_catalogs.py --check` (both `--root tests/support/fixtures/catalogs` and default retained sample): **passed**.
   - `node --test tests/frontend/chat.test.cjs`: **11/11 passed**.
   - `python -X utf8 -m tools.prepare_hus_corpus build` & `verify`: **Verified byte-identical reproduction (120 files)**.
   - PostgreSQL (`postgres`, `hus_postgres`), `rag_demo`, and `admin_console` jobs were verified on `85bd371` (5/5 GitHub Actions checks green) and re-verified on GitHub CI after push.

## GitHub Project #2 Status Synchronization (2026-11-03 to 2026-11-11) — 2026-11-11

Synchronized GitHub Project `#2` ("AI-07 · Sổ học tập — Kế hoạch, tiến độ và nghiệm thu", `https://github.com/orgs/5-Bit-System/projects/2`) via `backups/github_project_update_20261111/update_project_20261111.py` (using local `gh.exe` in `backups/github_project_setup_20261102/`):
1. **Board Totals & Status Breakdown (before -> after):**
   - Before (`2026-11-03` baseline on `main` `1a5a79c`): `82` items (`Done: 69`, `Todo: 7`, `Backlog: 6`).
   - After (`2026-11-11` baseline on `main` `1205fa9` + active feature branches): **`156` items** (`Done: 130`, `In Review: 15`, `Todo: 6`, `Backlog: 5`).
2. **Draft Items Progressed:**
   - `extract-ui`, `goals-decision` -> `Done` (`Delivery: Main`, `Verification: PR đã merge`; `PR #100`, `PR #132` at `c9694f4`).
   - `rag-f2` -> `Done` (`Delivery: Main và nhánh riêng`; `PR #146` + `feat/hus-rag-phase2-gemini-lite` at `276dd2f`).
   - `rag-account`, `rag-citations` -> `In Review` (`Delivery: Nhánh riêng`; integrated on `feat/workspace-hus-lookup-20261111` at `76184eb` and `feat/hus-rag-phase2-gemini-lite`).
3. **Pull Requests & Issues Added/Synced (`#100`–`#168`):**
   - Merged PRs (`#100`, `#108`, `#112`, `#113`, `#131`, `#132`, `#141`, `#146`, `#148`) and closed issues (`#78`–`#82`, `#101`–`#111`, `#114`–`#145`, `#147`, `#167`) -> `Done` (`Main` / `Main và nhánh riêng`); `#150`, `#151`, `#168` -> `Done` (`Nhánh riêng`).
   - Open `PR #149` (`hus-embedding-chromadb`) -> `In Review` (`Nhánh riêng`).
   - **Auto-close safety guard enforced:** All 16 open repository issues (`#69`, `#152`–`#166`) were kept `OPEN` on GitHub; items with branch/main code ready (`#152`–`#162`, `#165`) were set to `In Review` (never `Done` so GitHub Project automation does not close teammates' open issues), while remaining evaluation/rollout/holdout items were set to `Todo` (`#163`, `#164`) or `Backlog` (`#69`, `#166`).
4. **Project Metadata & Local Evidence:**
   - Updated Project `#2` `shortDescription` and `readme` with the `2026-11-11` status reconciliation note (`<!-- se-project-status-update:20261103 -->` section updated through `1205fa9`).
   - Before/after snapshots and update script preserved locally in gitignored `backups/github_project_update_20261111/` (`before_items.json`, `after_items.json`, `before_readme.md`, `after_readme.md`, `update_project_20261111.py`).
   - Session close-out only: no `git commit`, `git push`, `PR`, runtime restart, or code edits to product source/tests were performed.

## Natural Course Overview Routing, AI Reference Auto-Enable & CI Playwright Lock Alignment — 2026-11-11

Completed session updates on `feat/workspace-hus-lookup-20261111` (HEAD `76184eb`):
1. **AI Reference Auto-Enable & Minimalist Composer Footer:**
   - Updated `app/static/index.html`, `app/static/hus-lookup.css`, and `app/static/hus-lookup.js` so `allow_generated_reference` is permanently auto-enabled (`true`) across chat submissions, scope resets, and catalog questions (`item.requires_ai`).
   - Hidden the `#lookup-generated` checkbox and removed the visible "Cho phép kiến thức AI tham khảo (F3)" label row from `.lookup-composer-footer`.
2. **Natural Student Course Overview & Inquiry Intent Routing:**
   - Added `COURSE_OVERVIEW_TERMS` (`"nhu the nao"`, `"ra sao"`, `"biet ve"`, `"can biet"`, `"tim hieu"`, `"thong tin"`, `"gioi thieu"`, `"tong quan"`, `"mo ta"`, `"khai quat"`) and expanded prerequisite/content phrases in `app/hus/question_routing.py`.
   - Updated `question_intent` and `HUSAnswerer._answer` in `app/hus/answering.py` plus `ANCHOR_INTENTS` in `app/hus/semantic_routing.py` so natural student queries mentioning a course code or alias (e.g. `"tôi cần biết về học phần giải tích 3"`, `"học phần giải tích 3 như thế nào"`) route directly to `("f3", "content")` and return full course info cards + grounded explanations.
   - Added 7 parametrized regression cases in `tests/hus/test_phase2_topk_and_routing.py` (`test_natural_course_overview_queries_route_to_f3_content`).
3. **CI Dependency Constraint & Headless Browser Fallback:**
   - Aligned `requirements-portal.txt` (`playwright>=1.58,<2`) with `requirements-lock.txt` (`playwright==1.58.0`) so `pip install -r requirements-dev.txt -c requirements-lock.txt` resolves cleanly in GitHub Actions (`postgres` and `hus_postgres` CI jobs green) while preserving the pinned `requirements-lock.txt` SHA256 required by `app/hus/vector_contract.py`.
   - Added `_launch_browser(p)` in `tests/frontend/test_lookup_persistence.py` to prefer default headless Chromium before falling back to `channel="chrome"`.

## Workspace HUS Lookup Tab Integration, Zero-Scroll ChatGPT Layout & Account Chat History Persistence — 2026-11-11

Completed integration of the HUS RAG lookup system into the "Sổ học tập" academic workspace (`feat/workspace-hus-lookup-20261111`):
1. **Workspace Navigation & Lookup Tab (`#tab-lookup`):**
   - Added 5th navigation item "Tra cứu thông tin" (`#tab-btn-lookup`) in `app/static/index.html`, `app/static/workspace.js`, and `app/static/i18n.js` (VI/EN).
   - Mounted `/hus` router in `app/main.py` via `app/hus/router.py` (`/hus/config`, `/hus/chat`, `/hus/retrieve`, `/hus/questions`, `/hus/sources/{source_id}`).
   - Created `app/static/hus-lookup.js` and `app/static/hus-lookup.css` with auto-sync of student major from VNU portal profile (`workspace:portal-data`).
2. **Markdown Course Info Cards & ChatGPT-Style Zero-Scroll UI:**
   - Decoupled `renderSafeMarkdown` in `hus-lookup.js` so `### Thông tin học phần` cards and `[1]` badges render cleanly regardless of generation mode; aligned user messages to the right (`.rag-message-user`).
   - Redesigned `#tab-lookup` into a zero-scroll ChatGPT-style viewport (`calc(100dvh - 158px)`), compact header, pinned composer, and constrained sidebar height (`body:has(#tab-lookup.active) .workspace-sidebar`) so outer page scroll is `0px` on 1366x768 screens.
3. **Natural Student Phrasing Intent Routing:**
   - Expanded `COURSE_FIELD_TERMS["content"]` in `app/hus/question_routing.py` and `ANCHOR_INTENTS` in `app/hus/semantic_routing.py` to support natural queries (`"học như thế nào"`, `"học ra sao"`, `"dạy như thế nào"`).
4. **Two-Tier Persistent Chat History by Account (F5 & Cross-Session):**
   - Backend storage (`app/hus/chat_history_repository.py`): stores per-account, per-major history in `data/hus_chat_history/{account_id}.json` (ignored in `.gitignore`), with strict regex validation (`^[a-zA-Z0-9_\-]+$`) against path traversal, atomic `tempfile` + `os.replace` writes, `threading.Lock`, and 100-message cap per major.
   - REST endpoints in `app/hus/router.py` & schemas in `app/schemas/hus.py`: `GET /hus/chat/history`, `POST /hus/chat/history`, `DELETE /hus/chat/history` bound to authenticated session (`optional_account`).
   - Frontend (`app/static/hus-lookup.js`): zero-latency F5 restoration via `localStorage` (`hus_chat_history_${accountId}_${majorId}`) + async server sync, account switching isolation (`workspace:account-change`), and `+ Đoạn chat mới` (`#lookup-new-chat`) reset button.
5. **AI Knowledge Auto-Enable & Checkbox UI Streamline:**
   - Auto-enabled `allow_generated_reference: true` across all chat submissions, scope resets, and catalog selections.
   - Hidden the visible checkbox and label from the composer footer (`#lookup-generated` kept as hidden active input), allowing unrestricted lookup while maintaining a clean, minimalist UI.
6. **Verification & Regression Suites:**
   - `tests/hus/test_chat_history.py`: 22/22 unit & API tests passing.
   - `tests/frontend/test_lookup_persistence.py`: 2/2 Playwright browser tests passing (F5 reload retention + account A/B isolation).
   - `tests/frontend/check_workspace.py`, `tests/frontend/check_presentation.py`, `node tests/frontend/chat.test.cjs` (11/11), and `ruff check` all passing with 0 errors.

## Stage 3 refinement: UX layout, citation deduplication, prompt redesign, and prerequisite enrichment — 2026-11-11

Completed user-driven UX and RAG refinements on `feat/hus-rag-phase2-gemini-lite` (HEAD `276dd2f`):
1. **UI & Workspace Layout:**
   - Expanded `.rag-shell` container width (`min(1520px, calc(100% - 32px))`) and chat message height to `60vh` (`min 480px`, `max 720px`).
   - Cleaned up redundant instructions and notes below the chat input box.
2. **Citation Source Deduplication:**
   - Added `groupCitations(citations, origin)` in `app/static/hus-rag-demo.js`.
   - Deduplicates identical target URLs into single cards with merged citation IDs (e.g. `[2, 3, 4, 5]`), while preserving distinct URLs and differing PDF pages.
   - 10/10 Node.js unit tests passing in `tests/frontend/chat.test.cjs`.
3. **Prompt Redesign & Motif Elimination:**
   - Overhauled prompt template in `app/hus/llm_answerer.py` to adopt "Answer-First" principle.
   - Completely eliminated rigid 4-part numbered formula (`### 1, 2, 3, 4` / "Phần 1: Thông tin học phần", "Phần 2: Tổng quan", "Phần 3: Nội dung", "Phần 4: Lời khuyên học tập").
   - Now supports adaptive answering: concise (1-3 sentences) for credit/prereq lookups, natural and structured (200-350 words) for curriculum and course explanations.
4. **Authoritative Decision PDF Linking:**
   - Added `_resolve_f2_pdf_citation()` in `app/hus/llm_answerer.py` mapping program and course facts to official scanned PDF decisions (e.g. QĐ3569 `105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf`).
   - Generates clickable `/hus/sources/{sha256}?page={page}#page={page}` citations opening exact pages in new browser tabs.
5. **Prerequisite Normalization & Forward Prerequisite Enrichment:**
   - Eliminated misleading `(Chưa có thông tin cụ thể trong hệ thống)` for foundational courses without prerequisites (e.g. MAT2400, MAT2501).
   - Explicitly displays `Điều kiện tiên quyết: Không` when the official curriculum has no prerequisite requirement.
   - For courses with prerequisites (e.g. MAT3507), resolves both code and course title (`MAT2505 (Lập trình cơ bản)`).
   - Enriched two-way forward prerequisites (`dependent_courses`): shows follow-up courses unlocked by the current subject (e.g. MAT2400 is prerequisite for MAT2403, MAT2407, MAT3379, MAT3562).
6. **Testing & Code Quality:**
   - 18/18 tests passing in `tests/hus/test_llm_answering.py`.
   - 23/23 tests passing in `tests/hus/test_grounded_citations_and_schema.py` and `tests/hus/test_chat_scope.py`.
   - 10/10 Playwright UI tests passing.
   - `ruff check app/ tests/`: 0 errors.
   - All commits pushed to `origin/feat/hus-rag-phase2-gemini-lite`.

## Stage 3 complete: Grounded LLM answering, in-line citations, safe markdown UI, and security mock suite — 2026-11-11

Completed Stage 3 (LLM Grounded Answering) under Subagent-Driven Development on feat/hus-rag-phase2-gemini-lite.
Implemented:
- Decoupled settings in app/config.py: HUS_RAG_LLM_ENABLED (default true) and HUS_RAG_LLM_MODEL
  (default gemini-3.5-flash-lite), reading GEMINI_API_KEY from .env safely.
- In-line citations and synchronized schema:
  - app/hus/llm_answerer.py instructs model to cite [1], [2] matching Top-K chunk order.
  - app/hus/chat.py updates answer.citations and tracks generation_mode ('grounded_llm' vs 'extractive').
  - Enhanced security: switched to x-goog-api-key header (no API key in URL), added _redact_key helper
    preventing any token leaks in exceptions, httpx tracebacks, or warning logs.
- Safe Markdown & Course Card UI:
  - app/static/hus-rag-demo.js: escapeHtml XSS protection, renderSafeMarkdown parsing Course Info Cards,
    headings, bold, lists, and [1] badges; backward-compatible plain-text <p> for extractive mode.
  - app/static/hus-rag-demo.css: modern academic styles for .rag-course-card, .rag-badge-llm, and .rag-inline-cite.
- Verification & Test Coverage:
  - tests/hus/test_llm_answering.py: 16 comprehensive mock tests (direct API, OpenAI proxy, 503/timeout fallback,
    security key redaction, empty bypass, chat integration) with 100% network isolation.
  - tests/frontend/chat.test.cjs: 8 Node.js tests passing for XSS sanitization and markdown parsing.
  - Full Playwright UI regression (test_chat_contracts_ui, test_program_questions_ui, test_question_catalog_ui) passing.
  - Ruff linter 0 errors across app/ and tests/.

## Phase 2 Top-K retrieval, course aliases, and Gemini 3.5 Flash-Lite grounded generation — 2026-11-11

User authorized Phase 2 implementation and live Google AI Studio integration.
Work branched from hus-embedding-chromadb (bc545c5) to new feature branch
feat/hus-rag-phase2-gemini-lite; committed 39c191f and pushed to origin with PR ready.
New modules:
- app/hus/course_aliases.py: Scoped abbreviation resolver for GT1-GT3, CSDL, TTNT, ĐSTT, etc.
- app/hus/semantic_routing.py: 78 canonical anchor intents and multi-signal Top-K ranker.
- app/hus/llm_answerer.py: Google Generative Language API integration, grounded in F2 facts
  and Top-K chunks; smart fallback chain for Lite models (gemini-flash-lite-latest ->
  gemini-3.5-flash-lite -> gemini-3.1-flash-lite); prompt structured with course metadata
  upfront, pedagogical tone, and controlled length (~500-600 words).
Updated schemas and runtime:
- app/schemas/hus.py: HUSRetrievedChunk and HUSRetrievalBundle.
- app/hus/answering.py: retrieve_context() method, scoped alias support in _matched_course_codes.
- app/hus/chat.py: Grounded LLM generation with extractive answer fallback.
- app/hus/demo.py: Added POST /hus/retrieve endpoint.
- app/hus/answer_support.py: extra_neutral tokens support for alias resolution.
Testing and verification:
- 104 new/focused tests in tests/hus/test_course_aliases.py (57), test_semantic_routing.py (23),
  test_phase2_topk_and_routing.py (24) all pass in 14.67s.
- Outbound HTTP strictly forbidden and verified in pytest isolation (assert not network_attempts).
- Ruff linter 0 errors across all app/hus/ and tests/hus/ files.
- Live demo verified with gemini-3.5-flash-lite on MAT2503: 547 words, course info upfront, ~1.8s
  model latency (~3.5-7s full chat roundtrip with prompt assembly).
No leaks of GEMINI_API_KEY; .env, .vscode/, and internal review notes remain local/untracked.

## V1–V5 publication authorization — 2026-11-10

User now requests commit/push V1–V5 to hus-embedding-chromadb with25total
commits from26acab1:9original V1/V2+884838b documentation+5V3+5V4+5V5.
Reuse original five-way V3 split (tree equals1ad85e3), keep V1/V2 IDs/authors.
Remote observed1ad85e3; only this named branch may be pushed with an exact
lease after verification. No main update/PR/merge/deploy/default-mode change.
Earlier no-commit/push statements describe historical implementation receipts.
Preserve those receipts and all source/model/index data; pin checkout newline
rules for captured bytes. Publication mapping/remote verification logs belong
in ignored backups/publish_v1_v5_25_20261110. See
docs/HUS_VECTOR_V1_V5_PUBLICATION_2026_11_10.md for commit grouping and limits.

## V5 hybrid RRF and controlled measurements — 2026-11-10

User approved V5 implementation. Local hus-embedding-chromadb HEAD1ad85e3+
V4/V5WIP; no commit/push/deploy/default switch. HUS_RETRIEVAL_MODE=lexical
remains default; hybrid now explicit with same three HUS_VECTOR_* settings.
New hybrid_retrieval.py: lexical20parents/vector20passages, compact parent
dedup rank1+, equal RRF60, final5, tie parentID. Same prefilters/canonical;
F2 bypass ML. V4 core query/runtime and historical evaluators/evidence remain
unchanged. Nested vector fallback not counted as second lexical vote; canonical
errors fail closed. Frozen per-call trace distinguishes both legs/pool/final.
New evaluate_hus_hybrid.py/hus_rag_metrics_v3.py/compare_hus_hybrid.py, separate
mode processes, full ordered suite/policy/runtime/model/index/environment pins,
fresh-output sealing/cache replay.36V5devcases source-frozen before inference,
plus dev96/contracts28=160/mode (56retrieval/54F2/50controls). AI-prepared exposed
dev,0human; not A7/holdout. Probe36lexical in ignored backups, no gold/gate tuning.
Final3runs: Recall@5 lexical55/56,vector55/56,hybrid56/56;MRR .87649/.88690/.88155;
false-refusals5/6/5;F2source54/54,scope/audit/HTTPerrors0,vector/hybrid56live and
0fallback.480predictions replay equal. Hybrid recovers strict anchor DEV-Q050
already known to have a valid alternative source; vector loses answerDEV-Q052.
All4newparaphrases and math-negation still refused despite retrieved anchors;
do not relax gate merely because of vector scores. Semantic entailment/coverage
review pending: comparison recommends lexical, not automatic hybrid promotion.
Cold~1.3/20.1/28.4s;peakRSS323/1432/1431MiB for comparator pipeline,notproduction
SLO/nativeBM25 benchmark. No index rebuild/new build-time measurement/provider.
Review AI2Important (suite multiplicity pins, reviewed semantic regression)
RED->GREEN; self-audit nested fallback consistency RED->GREEN; no re-review.
Final2103pytestpass/2skip/90deselected,50Chromium,5Node,Ruff.12real hybridHTTP,
F2noML/F3optout,copied-index fallback no doublevote and canonical503 verified.
Evidence docs/RAG_HYBRID_V5_2026_11_10.md, acceptance/hus_hybrid_v5_report.json,
new evaluation/hybrid_v5_dev_20261110 and runs/hybrid_v5_*_20261110_r1.
Ignored backups/hybrid_v5_20261110 hold baseline/logs/recovery helpers.
Next: response-bound content review/A6/A7; LLM optional only on new selection.

## V4 vector query and guardrails — 2026-11-10

User approved V4 design and implementation, explicitly forbids push without a
new command. Work local on hus-embedding-chromadb. No V4 commit/push/deploy.
Checkout externally reset 586e460->1ad85e3 at00:08+07; retain current HEAD,
reapplied only lost V4 integration; do not restore/rewrite history implicitly.
New vector_query.py/vector_runtime.py; inject retriever into answerer/service,
extend retrieval_config/.env.example. Default remains lexical/no optional ML.
Explicit vector mode uses HUS_VECTOR_INDEX_PATH, HUS_VECTOR_MODEL_CACHE and
HUS_VECTOR_EXPECTED_INDEX_ID pinned outside DB. F2 never initializes ML;
hybrid unavailable until V5. No download/build/current selector changes.
Chroma where prefilters release/family/major/review/opt-in and canonical parent
allowlist plus requested version/variant/course/field. Query prefix+special
tokens<=512, pinned V3 encoder graph, local CPUfloat32 maskedmean/L2.
Verify full existing V3 index at startup; recheck manifest/inventory/collection
identity/config/full DB inventory every query. Reject malformed/nonfinite/
out-of-scope/tampered result wholesale; resolve parent canonical for citations,
dedup by best distance. Empty valid result stays empty. Vector faults fallback
BM25 with exact scope and stable reason; canonical faults fail closed outside
fallback. Immutable per-call trace plus INFO logger, no query/exception secrets;
locks serialize lazy runtime creation and model/tokenizer/index query operations.
60focused tests pass; final2067offlinepass/2skip/90deselected,50Chromium,5Node,
Ruffpass on1ad85e3+WIP. Existing CI venv required: default Python lacks argon2
(initial26collection errors/12HUS failures, not product regressions); no install.
Two ML processes8queries each match parent rankings;12HTTP answered with real
vector service, F2zero vector calls,F3optout blocked. Overbudget/copy-manifest
tamper fallback pass;8original index files hash unchanged;1060protected files
hashed and no data/hus/V1-V3code/locks changed in Git. Technical AI review clean.
Evidence docs/RAG_VECTOR_QUERY_V4_2026_11_10.md and acceptance/
hus_vector_query_v4_report.json; ignored backups/vector_query_v4_20261109.
Initial cold13-41s,warm~0.8-1s local,not production SLO. No new Recall evaluation,
no gate relaxation, no hybrid/LLM/source promotion; V5/A7 next if selected.

## Core/vector branch separation — 2026-11-09

User requests splitting V1-V3 into feat/hus-embedding-chromadb-v1-v3-20261109, rewriting crawldata
without those commits, then merging remaining core through a PR/merge commit.
Core starts26acab1 and retains all40 original core commits/authors. Vector
implementation/artifacts/optional lock are absent here; preserve main
dependency/admin/portal changes. Original full state is backed up locally.
No new source promotion/LLM/production deployment in this Git operation.

## V3 real CPU embeddings and offline Chroma index — 2026-11-09

User selected V3. Completed local crawldata HEAD884838b; existing V2 recheck WIP
retained. New app/hus/embedding.py,vector_index.py,tools/build_hus_vector_index.py,
tests/hus/test_embedding.py,test_vector_index_build.py. No old runtime/V1/V2/source/
lock/eval/receipt edits.1108protectedoldfiles/core54package environment unchanged.
112hashed lock packages installed only in backups/vector_index_v3_20261109/venv;
all9 model files downloaded/checksummed in its model cache,including470641600byte
safetensors SHA1a55775f53449dac10a2bcbc312469fac40b96d53198c407081a831f81c98477.
IMPORTANT actual Transformers5.22.1 AutoTokenizer/XLMRobertaTokenizer reconstructs
whitespace pre-tokenizer and differs from V2 (377vs378tokens on235a29...#p000).
Use PreTrainedTokenizerFast explicitly from verified tokenizer.json with special/
pad tokens,NOTdefault AutoTokenizer; all939V2input-IDhashesmatch,including batch
padding. Real AutoModel/eval/inference CPUfloat32,eager,2threads,maskedmean+L2,
384dim. Hand pooling and batch/single invariance verified. No remote code/download
in inference; model/optional imports lazy. No external LLM/provider API calls.
Index data/hus/vector_indexes/e5_small_v3_20261109:
ID8dad2f0f719a5228403d87f2b0c36a95f64fada9b82bf26bf432d4fed2469f74;
939vectors/935parents(F169/F3870),cosine,PersistentClient,scalar scope/provenance,
no documents/defaultEF/telemetry/F2/QA/gold/transcripts. Fresh-output-only; partial
build never sealed. Verify requires separately pinned expected-index-id.
Independentprocess reopens exact complete inventory and8family/majorprobes,tol1e-6.
Actual Chroma1.5.9 restart API omits num_threads/batch_size; record as requested
build controls only,require all other persisted settings and compare both if
exposed. Default EF remains disabled. No byte-identical HNSW cross-machine claim.
5fresh copied-index tamper cases rejected(document,metadata,vector,missingID,
self-rehashedmanifest); original index unchanged. AI technical review0Critical/
2Important/noMinor:NaN-distance and documents blindspot RED2/33->GREEN35; actual
configuration/default-EF regression RED2/20->GREEN39. One fix pass/no re-review.
Final2019pytestpass/2skip/90deselected,50Chromium,5Node,Ruffpass;3cachedlexical
replays verified,no new Recall measure. Scratch runner exclusive-write logging
error recovered preserving pytest/JUnit; final verification/commands_complete.json.
Evidence docs/RAG_OFFLINE_VECTOR_INDEX_V3_2026_11_09.md,
docs/acceptance/hus_offline_vector_index_v3_report.json,357file code/inventory ZIP
data/hus/evaluation/vector_index_v3_snapshot (no weights/Chroma binary).
Chroma binary local/ignored via new vector_indexes/.gitignore. Do not rerun
write-once build/finalize/regression/tamper helpers against existing outputs.
Runtime still lexical/vector-hybridreserved; V4filteredquery/fallback NEXT,
V5hybrid/LLM/sourcepromotion/officialF3/commit/push/deploy notdone. Existing source
blockers and exposed/H2/human0 limitations unchanged.

## V2 recheck and roadmap consistency — 2026-11-09

User asked to finish V2 first. Actual crawldata HEAD884838b already contains the
completed 05/11 V2 implementation/artifact; do not recreate it or run destructive
old execute.py. Read-only final_check verified V1/V2 identity, 1094 protected files,
349-file archive, core environment, and 3 cached lexical replays. Fresh V2 pytest:
54 passed/1 Windows-symlink skip. Real tokenizer suite rerun across all939 passages,
Unicode and token boundaries; pass, old helper result writes redirected to fresh
ignored backups/vector_passages_v2_recheck_20261109. New receipt only:
docs/acceptance/hus_token_passages_v2_recheck_2026_11_09.json. Historical 1980-test
regression was verified from its receipt/logs, NOT rerun. Progress date/status
updated, two stale V2-next lines in section5.1 fixed to V1–V2 done/V3 next.
No runtime/artifact/source/lock/environment edits, downloads, embeddings/index,
new Recall measurement, V3/V4/V5 implementation, commit/push/deploy this recheck.

## V2 token-bounded embedding passages — 2026-11-05

User asked to continue and complete V2 on crawldata/HEAD1287e2a/v3.
New app/hus/passage_tokenizer.py,app/hus/passages.py,tools/prepare_hus_passages.py,
3newtestmodules (tests/hus/test_passage_tokenizer.py,test_passages.py,test_passage_artifact.py).
ZERO runtime/lexical/V1/data/review/evaluation/environment files modified;
1094oldprotectedfiles unchanged. Explicit fetch_tokenizer caches ONLY pinned E5
tokenizer.json (17082730bytes,SHA256 0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39)
into backups/vector_passages_v2_20261105/tokenizer_cache; locked wheel
tokenizers-0.23.3-cp310-abi3-win_amd64.whl (2872101bytes,SHA256 1f0823bb00c5fdc98e487354d54dd55a03848d61a1a0bf29a68c77f24f3b26c3)
extracted only into ignored backups/vector_passages_v2_20261105/tokenizer_runtime;
core Python environment (54packages) untouched.
Passages data/hus/vector_passages/e5_small_v2_20261105:
ID bc9c992887f33f16b7c53a0a5b3b905b046fe24af497972f56e0fdc3987231fb,
bound to V1 contract b24679900bd835304dd5cf2bce285f531a241e7514ba51b02b568c801946f143.
935parents -> 939passages (F1 65->69 with 4split parents,F3 870->870,F2 excluded).
Actual native fast-tokenizer counts include passage: prefix,context(empty) and
<s>...</s>: max input_tokens 392<=512,max content_tokens 388<=400,max overlap 64<=64.
100% lossless character coverage of _body(chunk) including final chars/whitespace;
token-start grapheme-safe cuts (NFD/CCC=0 marks,ZWJ,skin-tone,flags,CRLF guarded)
prefer paragraph>sentence>line ends (>=half target) with raw token-start fallback
when trailing space inflates tokens at budget boundary. Each child keeps parent_id,
hashes,scalar metadata; body_start_char/body_end_char are local retrieval-body
codepoint offsets (source_offsets=null); parent_chunk() and collapse_to_parents()
enforce canonical parent citation and parent-level gold comparison.
stage=passages_only,embeddings_computed=false,index_built=false,activation=false,
transformers_inference_compatibility_tested=false.
55newtests:54pass,1Windows-symlink skip (simulated redirected-root guard passes).
Technical AI peer review 0Critical,4Important,2Minor fixed in one RED10->GREEN54/1skip
pass; real_tokenizer_tests+real_audit pass across all939passages and Unicode/boundary cases.
Final1980pass/2skip/90deselected,50Chromium,5Node,Ruffpass. Cached lexical replays
for dev96/h2/contracts verified without new inference or semantic review.
Archive349files at data/hus/evaluation/vector_passages_v2_snapshot.
Evidence docs/RAG_TOKEN_PASSAGES_V2_2026_11_05.md,acceptance/hus_token_passages_v2_report.json;
ignored backups/vector_passages_v2_20261105. Progress V1/V2done,V3 offline model
weights/embedding/Chroma build NEXT. No weights/Chroma/V4query/LLM/source promotion/
commit/push/deploy.

## V1 optional vector index contract — 2026-11-05

User selected V1 then said continue. Completed local crawldata/HEAD1287e2a/v3.
New app/hus/vector_contract.py,retrieval_config.py,tools/prepare_hus_vector_contract.py,
2newtestmodules; ONLYoldruntime hus_service.py checks lexical-default mode before
loading snapshot; .env.example adds HUS_RETRIEVAL_MODE=lexical. vector/hybrid are
reserved,V1explicitunavailable,not fake fallback; restart/cacheclear afterenvchange.
Nooptionalimports/index/model reads inlexical. Noanswer/gate/schema/review changes.
Contract data/hus/vector_contracts/e5_small_v1_20261105:IDb24679900bd835304dd5cf2bce285f531a241e7514ba51b02b568c801946f143,
935parents(F165/F3870),body/text/fullmetadata/package/projectionhashes,F2excluded.
contract_only/index_builtfalse/passagenull/activationfalse. Existingv3unchanged.
Modelprofile data/hus/vector_profiles/e5_small_v1:HFintfloat/multilingual-e5-small
commit614241f622f53c4eeff9890bdc4f31cfecc418b3,tokenizersamerev,384/512tokens,
query:/passage:prefix,maskedmean+L2,cosine,CPUfloat32,safetensors,no trust_remote_code.
6tinyconfig bytes verifiedGitblob/SHA256,3large LFSexpectedhashesONLY,notdownloaded
orlocallyverified. DirectAutoModel/AutoTokenizer,notSentenceTransformerswrapper.
Optional requirements-rag-vector.in/-lock.txt:112fullyhashed packages,target
WindowsAMD64/CPython3.11,coreconstraints unchanged;torch2.15.0,transformers5.22.1,
Chroma1.5.9. uv0.13.7 standaloneSHAverified inbackups,metadata resolution;3inputs+lock
bound inprovenance. NoMLinstall/currentenvironmentchange or inferencecompatclaim.
45newtests:44pass,1realWindows-symlinkskip; simulatedrootredirectguard tested.
InitialRED33,rootredirect/stale-resolution RED4fixed;AIreview Important bool/int or
int/float equality identity bypass RED7->GREEN44/1skip,canonicalJSON+unsignedhashfix.
Final1926pass/1skip/90deselected,50Chromium,5Node,Ruffpass.1057oldfilesprotected.
3freshvector_v1_lexical_{dev96,h2,f2}_20261105 runs:180responses/traces identical
to1a,no newsemanticreview. DefaultstillBM25,Recalldev39/40,H2exposed20/20,F2raw15/16
vs source16/16. H2still25tuned,human0,noindependentRecall90proof. Archive341files
code/contract/profile/locks:data/hus/evaluation/vector_contract_v1_snapshot.
Evidence docs/RAG_VECTOR_CONTRACT_V1_2026_11_05.md,acceptance/hus_vector_contract_v1_report.json;
ignored backups/vector_contract_v1_20261105. Networkescalationsmetadata/helperonly,
no auto-reviewrejection; modelweights/tokenizerlarge/provider notdownloaded/called.
ProgressV1done,V2tokenizer/token-count/passagesNEXT. V3build/V4query/LLM/source
promotion/officialF3/commit/push/deploy notdone. ExistingPDFendpointregressiononly,
notnewembeddedviewer/PostgreSQL/fullcatalogacceptance;sourceblockersunchanged.

## Diagnostic1a career roles and teaching exclusions — 2026-11-05

User selected step1a. Completed local crawldata,HEAD1287e2a/WIP/v3 unchanged.
Runtime changes ONLYquestion_routing.py+answer_support.py: bounded role-nao/gi
workplace career inference with noncareer course/program/company/objective guards;
shared clause boundaries, explicit teaching refusal retains optional workplace
scope; factual negation/later affirmative/official/numbers remain active. Drop
whole excluded F1careers bodies before source coverage,never edit canonicalquote.
Requested school context also body-supported; missing clean evidence refuses.
49newtests,322focused,1882offline/90deselected,50Chromium,5Node,Ruffpass.
968oldfilesprotected unchanged. TechnicalAIreview2Important (wrong role subject,
qualified-refusal scope),both fixed in one RED9/40->GREEN322pass; no confirmedminors.
New runs role_exclusion_dev96_20261105,h2_20261105,contracts_20261105,
dev6_original_20261105,dev6_r2_20261105,dev7_20261105 (allprefixrole_exclusion_).
Sixmeasurement+sixAIoverlay cachedreplays. Dev96/H2/contracts EXACTresponses+traces
same as Q027mốc. Dev96Recall39/40,AIcomplete64/64;H2Recall20/20,F2raw15/16 vs source16/16.
Originaldev6C003/C007 changed,r2onlyC007;bothAIcomplete8/8/control2/2. Dev7frozen14
beforetuning:positive12/12AIentail/complete,control2/2. NewAIreadings17,inherited197
ONLYequalrequest/response/gold/audit hashes+sourceimmutability;human0,H2exposed25,
noindependentRecall90proof. Beforecomparisons joined recorded fullrequesthashes
from post-Q027runs+newdev7-before,not fabricated uniformbeforemeasurement.
Archive329code/test/dependencyfiles at data/hus/evaluation/role_exclusion_snapshot_v1.
Evidence docs/RAG_ROLE_EXCLUSION_2026_11_05.md,acceptance/hus_role_exclusion_report.json;
ignored backups/diagnostic_role_exclusion_20261105. Progress1a done,A3/V1-V4next.
Old A2/Q027/dev6gốc/r2/gold/scorers/receipts preserved; scoped lexical grammar,
not all-language/independent semantic or institutional-source certification.
No sourcepromotion/officialF3/modeldownload/vector/LLM/provider/commit/push/deploy;
no newembeddedPDFviewer/PostgreSQL/fullcatalogacceptance. Sourceblockers unchanged.

## DEV-Q027 career context coverage — 2026-11-04

User chose progress step1 and requested Superpowers. Completed local on crawldata,
same HEAD1287e2a/WIP/v3. Only runtime change: app/hus/answer_support.py. Preserve
exact active doanh-nghiep/cong-ty body context in F1careers within one existing
source/scope/review group; keep context citations alongside specific continuations.
Bounded request-refusal handling only for the new context extraction; no BM25,
routing/schema/F2/release/review/evaluator/scorer changes.39new tests,273scoped,
1833offline/90deselected,50Chromium,5Node,Ruffpass.895oldfiles protected unchanged.
Fresh measurements dev_q027_dev_v1_20261104,dev_q027_h2_exposed_20261104,
dev_q027_contracts_20261104,dev_q027_career_context_r2_20261104 +AIoverlays,8replays.
Dev96 onlyQ027responsechanged:all4enterprise roles now present,unknown-edition web
scope retained; Recall39/40 unchanged,rawanchor61/64,AIcomplete64/64 vsA2old63/64.
All actualretrievaltraces unchanged; H2/contracts all responses identical toA2:
Recall20/20,F2raw15/16 vs source16/16;Q048raw[null]/unknown/guards unchanged.
AInewreadings11(Q027+10dev6r2),179old judgments inherited ONLYafter exact request/
response/gold/audit hashmatch and sourceimmutability; not new independent review.
Dev6r2quote8/8,controls2/2,butAIcomplete7/8: C007stillquotes teaching explicitly
excluded byuser. Originaldev6C003 role-only wording routesintroduction; original
pack/before-run retained,r2 adds cong-viec cue beforetuning to isolatecoverage.
Both pre-existing routing/exclusion gaps deferred explicitly,next separate devfix;
do not claim10/10semantics or general Vietnamese negation/synonym understanding.
TechnicalAIreview Important refused-workplace false-refusal fixed RED9->GREEN273;
initialfullattempt interrupted,finalrun separate. Receipt records actualJUnitpath
from command (verification/offline.xml), final logs inverification_final.
Evidence docs/RAG_DEV_Q027_COVERAGE_2026_11_04.md,acceptance/hus_dev_q027_coverage_report.json,
ignored backups/dev_q027_20261104. New code_changes.zip ties A2basearchive tobefore/
afteranswer_support+newtest; A2snapshot/runs/receipts unchanged. No vector/LLM/APIkey/
provider/modeldownload,officialF3promotion,commit/push/deploy. H2still25prior-tuned,
human0,noindependentRecall90proof; no newembeddedPDFviewer/PostgreSQL acceptance.

## A2 versioned pinned BM25 baseline — 2026-11-04

User selected A2. NO runtime/source/oldtool/test/gold/review/receipt modifications;
850oldfiles hashprotected unchanged. Newtools evaluate_hus_chatbot.py,
hus_rag_metrics_v2.py,hus_chatbot_source_audit.py,31newtests. Same crawldata/base
1287e2a/selectedv3. Threefresh runs data/hus/evaluation/runs/a2_dev_v1_20261104,
a2_h2_exposed_20261104,a2_contracts_20261104 plus *_ai_review separate overlays.
Contract-only a2_contracts_v1 frozen28copiesfromA1v4/A1bv5 (26F2+2clarification).
All code/data/tests/deps/env pinned, stable across commands; code_snapshot.zip
327files in data/hus/evaluation/a2_baseline_snapshot_v1 preservesWIPbytes, not a
commit or standalone data/fixturearchive. Sixcachedreplays matchcurrentpins.
1794offline/90deselected,50Chromium,5Node,Ruffpass. PDFhash/page/endpoint regression,
not newembeddedviewer/PostgreSQL/full-catalog/deploymentacceptance.
Dev96route64/64,Recall39/40,F2source24/24,integrity64/64,guard32/32,optin8/8,
falseabstention0,rawanchor60/64. AIentail64/64,complete63/64:DEV-Q027 has faithful
standard2015workplaces/teaching but lacks requested concrete enterprise roles;
goldalreadyintop5. Keep defect inbaseline,fixonlylaterdev/newrun,notinA2.
H2FULL56nowmeasured:route36/36,Recall20/20,F2raw15/16 vs sourcecontract16/16
(Q048raw[null]/unknown preserved vslegacy[]; no genericempty normalization),
integrity/AIentail/AIcomplete36/36,missing/OOS16/16,optin4/4,falseabstention0.
ContractsF2 26/26 inclprogram4/groups4/rules4/prereq14;clarify2/2. Allv2filter
errors0;actualsearchparamsalsocheckedwhenemptyhits. LatencyHTTPp50/p95ms dev
26.85/67.77,H232.01/88.64,contracts26.60/68.88;local sequentialwarmTestClient,
notproduction,JSON/tracecapture/sourceaudit/review/startupexcluded.
RootAIread180responsepackets (126positive,54control), fullalternatives/exception
cases; decisions in data/hus/review/a2_response_review_v1. ReviewerAI,human0,
notindependent. AcceptedQ004onlyexplicitTalent2015scope,Q049/050standard2023DOCX
objectivesforunversionedqueries;Q027incomplete. H2still25uniquepriorruntime-tuned,
all56exposed;noindependentRecall>=90proof despite20/20. A2didnottune runtime.
Semanticjudgments answer-level,notper-citationprecision. Proxyquote/anchor!=
entailment. Retainlegacycase.failure/scope_errors asrawdebug:contractprogram12
legacyfalse-scopeerrors (rawlegacyinapplicable),v2usesfilter_errors/f2_contract;
H2Q048retainslegacyfact_mismatch. Sourceauditexactrawstatusfacts independent.
Technicalreview foundenvelope/release/marker,boundreviewrunidentity,emptyhitfilter,
HTTPtiming,releasepreflightgaps;red-greenfixed,finalnoCritical/Important. Cached
reviewverify makesnoHTTP/RAGcalls and bindmeasurementID/request/response/gold/
audit/release/predictions/snapshot. Evidence docs/RAG_BASELINE_A2_2026_11_04.md,
docs/acceptance/hus_chatbot_baseline_a2_report.json;ignored backups/chatbot_baseline_a2_20261104.
ProgressA1/A1b/A2done;A3optionalvector/hybridexperimentusesfrozenbaseline;DEV027
source/coveragefollowupseparatebecausegoldalreadyintop5. NoLLM/vector/modeldownload,
officialF3promotion,commit/push/deploy.

## A1b Q&A program/group lookup — 2026-11-04

User selected A1b row. Completed local on same crawldata/WIP/HEAD/release; source,
review/gold/scorers/CURRENT immutable, advisor/product untouched. New fields
program_credits/program_groups/group_rules + optional hierarchical group_key.
Portable loads4programs42groups into exactmajor/version defensive-copy lookups.
Pure f2_data(canonical,input_manifest) in-memory verification binds full exported
records:values/coverage/scope/review/url/blob/pointer, no release/index writes.
Program credits135/132/129/127;groups12/9/9/12;program/group source review verified
forCS only,3othersdraft. Distinct required/min_if_selected/offered,keepnull/choice
notes/parent-child conflicts,never sum or authorizeeligibility. Canonicalweb JSON
citations exacthash/pointer/quotes, no guessedPDFpages/liveURLfetch. Names/mixed
scopes/fields/hints/variant text and refused group references guarded; missing
group askskey,unknownnoinfo. Group-course lists not implemented. F3strictoptin
and A1rawstatus preserved. Catalog+50 entries=2414;chat/HTMLhelp distinguish program
no coursecode vs coursefullcode/name. Two oldcatalog tests now accept optionalcode.
60newprogram+2browser tests;final1763offline/90deselected,50Chromium,5Node,Ruffpass.
758oldprotectedfiles unchanged;code/data/tests/environment stable across commands.
Devv5frozen12cases beforetuning0/12->12/12 contractonly. Olddev96freshRecall39/40,
F224/24,integrity64/64,guard32/32,optin8/8,falseabstention0,rawanchor60/64;gate20
still20/20. Initialregression10failures corrected(genericcareergroups,va in full
coursename,oldUIallF2requirescodeassumption),logs preserved,finalrun separate.
AIscopedpeerreview Important review/provenance,variant,mixed/negation findings
red-green fixed; finalnoCritical/Important. Humanreviews0,25uniqueH2tuned stays,
no fullH2rerun or independentRecallclaim. Evidence docs/RAG_PROGRAM_QUESTIONS_A1B_2026_11_04.md,
docs/acceptance/hus_program_questions_a1b_report.json;ignoredbackups/program_questions_a1b_20261104.
Progress nowA1/A1bdone,A2versionedevaluator+fullpinnedexposedbaseline NEXT. No new
PDFviewer/PostgreSQL/full-catalog acceptance, externalprovider/modelcalls,
officialF3promotion,commit/push/deploy.

## A1 Q&A source-status and single-turn contracts — 2026-11-04

User selected A1 from approved Q&A-only plan and said continue. Implemented local
on crawldata, same selected v3 release; advisor/product untouched. Six runtime/UI
files changed relative to snapshots in backups/chat_contracts_a1_20261104.
F2 facts add prerequisite_status unknown/present/conflict/unresolved; raw [null],
all source rows/citations, review and groups preserved. Priority conflict > missing
raw/unknown > unresolved parse/code > present. Actual 290 memberships:103unknown,
145present,41unresolved,1conflict (42 have unresolved codes, one also conflict).
Blank stays unknown even project verified; explicit warning no inference of no
prereqs/registration eligibility. Q048 copied to frozen dev_v4 before tuning;
legacy gold/scorer [] vs [null] untouched. MVP one course/one info type per turn:
detected multi-field requests clarify without facts/citations even explicit hints.
Shared router aliases, bounded negated-field handling, bare hoc nhung preservation;
actual required-earlier-study wording remains F2. No hidden prior-course state;
exact unique scoped course names still work. Help/UI note and status messages updated.
Frozen diagnostic_dev_v4_contracts16cases:old1/16,new16/16 contract-only not Recall.
65newunit+3browser tests; fresh1701offline/90deselected,50Chromium,5Node,Ruffpass.
744old protected files unchanged, runtime/test/data pins stable across commands.
Old dev96 fresh:Recall39/40,F224/24,integrity64/64,guard32/32,optin8/8,falseabstention0,
rawanchor60/64 unchanged. Dev3gate20 still route/answered/support20/20. Technical
AI peer review Important alias/negation/nhung findings fixed red-green and verified;
337reviewer fresh tests pass, final no Critical/Important. Humanreviews0. Exposure
now25uniqueH2tuned (24dev2/3 +Q048dev4), never independent holdout. FullH2notrerun.
New docs/RAG_CHAT_CONTRACTS_A1_2026_11_04.md and acceptance/hus_chat_contracts_a1_report.json;
progress updated A1done,A1bprogram/group structured lookup NEXT. New UI test opens
PDF binary endpoint; no new embedded viewer acceptance, PostgreSQL/full-catalog,
external provider/embedding calls, source promotion, commit/push/deploy.

## Q&A-only scope and comprehensive plan audit — 2026-11-04

User explicitly states HUS question-answering chatbot is unrelated to the course
recommendation chatbot. Keep scope F1/F2/F3/basic chat; never route through advisor,
reuse its provider flags/prompts,require transcripts/eligible sets or merge features.
User requested full audit and updated docs/RAG_PROGRESS_AND_NEXT_PLAN.md only;
runtime/source/gold unchanged. New plan includes unknown/multi-field contracts,
structured program/group lookup gap, baseline measurement, optional localE5+Chroma
hybrid, independent LLM rewrite optin, Q&A UI, final evaluation and demo/deployment.
Current program/group exports4+42 are not yet proper structured Q&A endpoints;
curriculum-credit question asks for course code, group question routes F1.
Additional probes:MAT2400 prereqvalue[null] no explicit status;multi-field only
credits field;implicit course followup clarifies. Record as dev,neverholdout.
Fresh894tests in tests/hus pass within1633offline/90deselected;50Chromium/5Nodepass.
14sourcebinaryhashes12PDF+2DOCX validated;oldgate artifactpins stillmatch. No new
PDFviewer/image acceptance,externalLLM/embeddingcalls,H2fullrun or sourcepromotion.
Evidence docs/acceptance/hus_chatbot_scope_audit_2026_11_04.json and local ignored
backups/chatbot_audit_20261104. Future vector/LLM files/config in plan do not exist.
Keep humanreviews0/reviewerAI,exposure24H2cases and raw60/64 anchors honest.

## Priority2 support gate — local 2026-11-03

User selected priority2. Frozen diagnostic_dev_v3_support copies20exposedH2
requests/gold/evidence before tuning:16gate refusals+4previouslyrouted previews.
Only runtime changes answer_support.py and removing[:2] in answering.py.
Explicit edition/QD checked against hitversion;arbitrary numbers remainfacts.
Bounded request phrases handled per activeclause;commandverbs onlyatclausestart,
never erase factual presentation skills. Peerreview found that Important issue;
redtests+fix+reviewer confirmation done. Same source/hash/package/major/version/
variant/course/field/origin/review required for grouped support;one sufficient
source,sourceorder excerpts,existingtop5unchanged. No retriever/router/data/review
or AIoptin change;officialF3 excluded.20answers0→20,allgoldquotes in citations20/20;
Q043twoobjectiveparts,Q044all4careergroups,4previewsgeneratedwithconsent only.
421protectedoldinputs unchanged;before/after only2artifactchanges,environment/
evaluator/runner equal. Finalrun dev_v3_support_after_command_guard;oldruns frozen.
78newgatetests;171gate+oldguard/routingpass.1633offline/90deselected,50oldChromium
+3newrealUIcases,5Node,scopedRuffpass;PDFhash/pages13/12,notnewPDFvieweracceptance.
Dev96fresh:Recall39/40,F224/24,guard32/32,optin8/8,integrity64/64,falseabstention0.
RAWanchor60/64vs61historical,notregraded.4missesQ004/Q027/Q049/Q050sourcealternatives
reviewedseparately:Q004talent2015narrowpopulationmustremainexplicit,Q027standard2015,
Q049/050standard2023DOCX. Q006nowquotescondition+Masters/PhDandcontinuationtogether.
Humanreviews0;AIoverlay support_gate_v3_response_review no sourcepromotion/goldedit.
H2full56notrerun;24uniqueH2casesnowruntime-tuned(dev2∪dev3),neverindependentholdout.
Priority3F2null/unknown and separatelyrecordedalternatives NEXT,thenfullpinnedmeasure.
No commit/push/deploy. See docs/RAG_SUPPORT_GATE_FIX_2026_11_03.md and matchingreceipt.

## Clickable question catalog — local 2026-11-03

User approved grouped clickable F1/F2/F3/help menu in standalone RAG demo.
New app/hus/question_catalog.py derives2364 request entries from selectedv3 only:
40F1 edition/variant scopes,1442F2,870generatedF3,12help across4majors/290memberships.
GET /hus/questions exactmajor+decisionversion;F1 entries retain sourceedition/hệ.
UI search supports unaccented names/codes;click reuses normalchat with field hints,
never grantsAIconsent;major switch clears menu/chat+AI and ignores late responses.
Two new basic help replies explain sources/AI;main/product/auth unchanged.
All2364menu requests exercised viarealchat;new9API+5Chromium tests,32targetedpass.
Final1555offline/90deselected,50oldChromium,5Node,scopedRuff pass;324protected
data/evaluation/review files unchanged;code/test pins stable across regression.
Read-only peer review2Minor resolved;noCritical/Important. No gate/routing/data
change,newH2inference,officialF3promotion,commit/push/deploy. Menu is finite
canonical templates with explicit fields,not proof of NL coverage/independentRecall.
Existing priority2preview supportgate remains NEXT. See docs/HUS_RAG_QUESTION_CATALOG.md
and docs/acceptance/hus_question_catalog_report.json;backups/question_catalog has
local screenshots/logs/pins. Progress and manual updated briefly.

## Priority1 routing name/preview fix — local 2026-11-03

User selected priority1 from concise progress plan. New diagnostic_dev_v2_routing
freezes8exposed H2requests/gold/evidence before tuning; parent H2/P11/P12/P2/dev,
review/source/release/CURRENT unchanged. Only runtime change question_routing.py:
name-of-code/course phrasing plus bounded preview disambiguation. Keep requested
clause boundaries, explicit content/objective/assessment goal and real required
study priority; requested_text output matches before across264evaluationqueries.
Four original name requests now source-backed F2;four previewrequests now search
F3/content with exactscope/consent. Final8case API route0→8,names0→4,search0→4;
all4original previewanswers still rejected by unchanged answer_support gate.
Priority2 gate is NEXT;do not claim global Recall90% or full answer success.
Finalrun dev_v2_routing_after_need_guard;before run retained and intermediate
runs frozen too.357protected old input hashes unchanged,only router differs
among111artifact/runtime pins;environment/evaluator unchanged. New62tests red
then green;194routing/guard/devpass. Full final1541offline/90deselected,5Node,
50Chromium pass on111artifact/138testpins;UTF8 inherited by child Python processes.
Peer review boundary findings resolved;no Important findings in finalslice.
Raw56case H2metrics80% remain historical pre-fix;no new fullH2inference. Update
exposure interpretation:8H2cases NOW usedforruntime tuning via devcopy;never
recertify as independent. No source/review/optin/gate/UI changes,commit/push/deploy.
See docs/RAG_ROUTING_NAME_PREVIEW_2026_11_03.md and matchingreceipt.

## Source scope review v2 — local 2026-11-03

User requested continued source/image/identity/edition/raw/blocker review and
explicit release scope, official F3 kept out of defaults. New p13_release_scope_v2
is an AI-only overlay; old packs,302protected inputs,CURRENT/registry/release,
canonical/source reviews,runtime and RAG runs unchanged. Keep selected v3 only:
15F1 source metadata/65chunks (14primary citation sources,one dedup provenance),
290F2records/297occurrences/four hash-bound PDFs,870generated F3chunks opt-in only;
106official syllabus candidates excluded.106source decisions/21dependencies
explicitly distinguish historical URL identity from same-binary F2 dependencies.

Actual image comparison now covers all297 F2occurrences across22tablepages,
252beyond old45;194nonblank prereq rawcells match ignoring whitespace,103blank
unknown. English MAT3554E singular Language vs canonical Languages recorded;
MAT3360tone variant and unusual source hours preserved,no data correction.
All4canonical decision PDFs p2 directly declare from admissions cohort2022;
this does not verify later amendments/current validity/individual applicability.
Three of4original identity proposals technically supported as candidates;
MAT3561 2021→2023link deferred due prereq conflict. Reject embedded headerMAT1202
as OOP;TOCp2+continuation support MAT1208errata candidate only. Additional
KHMTTT2024TOCMAT2505→p4/headerMAT2316 mismatch prevents whole-document approval.
No mapping applied,official F3 still excluded.

Seven priority exact original HTTP URLs successfully fetched after sandbox
escalation:4scanURL bindings match3existing F2PDFhashes;3matrix/map captures add
3newhashes.7URLcaptures/6unique binaries total;30outside-scope originals not
retried. Frozen historical missing37 unchanged;do not call30 HTTPfailures.
Current URL-binding facets resolved4;all6full historical blockers remain open
for residual historical-byte/current-validity/applicability evidence. New captures
and images remain ignored local backups;metadata/hash proof is in the new pack.
48unique PDFpages observed this pass,19overlap old19 and29outside it;not whole
72OCR-page/1788low-confidence acceptance.34source/OCR/supplement tests pass.
See docs/RAG_SOURCE_SCOPE_REVIEW_2026_11_03.md and matching receipt. No new RAG
inference,source promotion,commit/push/deploy. Next source work is discrepancy
resolution in a new data version or authoritative applicability for selected
official fields;do not gate fixed existing scope on all37missing originals.

## AI review policy override — local 2026-11-03

Latest explicit user instruction: "thế thì bỏ qua người thật review chỉ cần AI review là được".
This supersedes the human-signature prerequisite in older notes below for this
round. Complete AI source/gold/overlap/alternative review and pinned measurement;
do not block this work on human decisions. Keep reviewer_kind=ai and actual human
reviews=0; never relabel AI as human or certify semantic independence. Preserve
frozen holdout_v2_candidate, original human worksheet/validator, P11/P12/P2 baseline,
runtime/source/review and AI opt-in. New AI-only artifacts belong in
holdout_v2_ai_review_v1; corrected evaluation data in ai_reviewed_exposed_v1.
Report exposed evaluation separately from independent Recall@5 acceptance.
Publication/deployment and official F3/source approval remain separate.

AI review now complete56/56:53 original gold adequate,3revised in derivative
ai_reviewed_exposed_v1 before inference (Q043 objectives complement,Q044 all4
career groups,Q048 blank prerequisite unknown).52high/4moderate semantic-exposure
risks; no independent holdout claim. Pinned H2 exposed run:route28/36,search16/20,
routedRecall16/20=80%,conditional16/16,F2strict11/16,integrity16/16,true refusal16/16,
opt-in4/4,false refusal20/36.111artifact/environment pins and144protected inputs
unchanged;cache reproduced. Failure diagnosis25cases:16overliteral support gate,
4name phrasing unrecognized,4figurative before-course misrouted to prereq,1[]/[null]
representation mismatch. No runtime tuning from H2 yet. Preserve pack/run for
measurement; copy exposed cases to new dev before next fix, never recertify as
independent. Dev3case AI review:Q006partial,Q049/Q050supported2023DOCX. See
docs/RAG_AI_REVIEW_AND_MEASUREMENT_2026_11_03.md and matching new artifacts.
Fresh regressions AFTER H2:1479offline pass/90deselected,5Node,50Chromium,realPDF
viewer13/12 pass first attempt.108regression/111H2artifact/136Python+1Node test
pins+environment unchanged. AI semantic response overlay56cases:16/16citations
entail returned facts,12/16relevant,11/36positives fully correct,Q048partial,
20controls correct. No delivered F3generated answers in this run. Original raw
metrics stay unchanged; new semantic report is AI-only. No commit/push/deploy.

## Pinned RAG remeasurement — local 2026-11-03

User requested separate routing/retrieval/F2/citation-support/abstention metrics
and fresh API/UI/PDF/scope/AI regression. H2 still0/56 accepted,so NOT run. New
dev_pinned_remeasurement_v1 observes classifier before guards,then actual search;
64/64 positive routes,39/40 scopedRecall,F224/24,integrity64/64,anchor61/64,
true refusals24/24,opt-in8/8,false refusals0/64. Semantic metrics null; independent
90%target remains unproven.111 code/UI/data pins+actual Python/distributions match
before/after/cache. No runtime/data/gold/review change; evaluator/helper only.
Fresh1479 offline pass/90 deselected,50Chromium,5Node;actual PDF viewer13/12 loaded
and screenshots/hash/scroll checked.108 regression pins and136 test sources unchanged.
See docs/RAG_PINNED_REMEASUREMENT_2026_11_03.md and matching receipt. No commit/push/deploy.

## HUS holdout/review preparation — local 2026-11-03

User will personally perform real independent review; no per-case decisions or
signatures yet. New holdout_v2_candidate has56 questions/44 evidence IDs; root AI
completed draft after isolated author hit usage limit, so author independence is
NOT claimed. Do not run H2 or tune runtime from it before human review/freeze>=40.
holdout_v2_review has CSV/JSONL pending forms,source alternatives and lexical/AST
overlap audit;0 exact/strong lexical flags does not establish semantic independence.
validate_hus_holdout_review only validates declared decisions,never verifies human
identity or certifies independence. Source followup p13_scope_followup_20261103:
19 images/45 OCR-missed occurrences technically inspected,106-source scope sheet,
37 missing/6 blockers still open; official F3/release unchanged. See
docs/RAG_REVIEW_RELEASE_GATES_2026_11_03.md and source followup report. User requires
measurement on pinned final snapshot,API/UI/PDF/scope/AI regressions,publication
and production only after acceptance. No commit/push/deploy yet;target still unknown.

## HUS RAG routing fixes — local 2026-11-03

Root remains crawldata at1287e2a with existing P1/P2 WIP. Diagnostic/dev v1 has96
requests/88 texts and exposes old P1-1 for development; never certify it as final
independent holdout. New question_routing/answer_support plus scoped F2 name lookup
fix intent/field/negation/gates while preserving source/review/AI/citation. Explicit
name/code/QD conflicts cannot borrow facts. Dev before→after Recall@5:6/40→39/40,
F2:0/24→24/24,guard:20/32→32/32; source anchors61/64,three cases need human semantic
review. Final1444 offline pass/90 deselected,50 Chromium,5 Node; Ruff app/tools/tests
passes; full-repo lint has two pre-existing errors in P13 generation artifact.
Frozen P11/P12/P2,release/CURRENT/review unchanged. See docs/RAG_ROUTING_FIXES_2026_11_03.md
and receipt hus_routing_fixes_report.json. No commit/push/DB/VNU/provider/production.

## Main contributor context preserved

## Intake refinement publication authorized — 2026-11-04

User now explicitly requests commit/push of the changes immediately below on
the CURRENT branch, with about ten commits. Use exactly ten non-empty commits
on feat/recommendation-conversation-ui from c823aa5; remote branch was fetched
and is at the same base. This supersedes the preceding local-only restriction
for these seven scoped source/test/doc/memory files, not for configuration or
ignored runtime records. Preserve all original 19 commits and configured author.

Commit plan: workload range helpers; cohort window helpers; custom-direction UI
and wrapping; final-only chat; bounded workload controls/payload; graduation UI,
cohort invalidation and precise readiness; model boundary tests; browser intake
regressions; source/runtime report; contributor checkpoint. Stage related file
increments while preserving the verified working files and their runtime content.
No empty commits, invented authors, squash/rebase or force-push. Publish only
the existing feature ref; no main merge or database operation in this publication.

The implementation already passed the 621-case suite including PDF acceptance,
five Chrome suites, Node model checks and lint/syntax/diff checks in the immediately
preceding task. No code changes are introduced just to obtain more commits.
Verify final tree against the pre-publication file hashes, ten new commits,
upstream equality and exclusion of .vscode/settings.json, credentials, AD-102,
PDF copies, video/logs/backup data. Publication preparation is recorded here;
Git and the ignored publication receipt establish the actual resulting hashes.

## Recommendation intake refined and catalog restored — 2026-11-04

User requests custom direction input, chat only at the end, workload budgets
light 14–17/moderate 18–20/heavy 21–30, HK1/HK2 graduation goals within six years
from enrollment cohort, and checking the supplied 2023/K67 ZIP for the curriculum
notice. Edits remain LOCAL on feat/recommendation-conversation-ui at published
c823aa5; no new commit/push authorized for this refinement. Preserve untracked
.vscode/settings.json and all ignored configuration/credentials/AD-102/backups.

recommendation-model.mjs now owns credit ranges/clamping and a cohort-based goal
window. K68=2023 admission, last academic year 2028–2029; on 04/11/2026 choices
are 2026/2027/2028 starts. The UI rolls academic years in August; it does not
adjudicate exact legal deadlines. Unknown/future/expired cohort has no invented
choices. Graduation semester 3 is rejected. The six-year cap is the user's
requested selector constraint; source PDF104 states a normal four-year program.

recommendation-workspace.js/css add Tự chọn with a dedicated nonempty 120-char
input; official track selection remains mandatory where the catalog requires it.
Chat appears only after all 3 intake stages plus any required graduation-path
stage, and hides while editing earlier steps. Mode changes clamp budgets; both
number/slider and generation payload enforce ranges. Cohort refresh invalidates
old goals/results. Long directions wrap on mobile. Readiness distinguishes
unresolved outcomes/rules from unverified metadata; no server gates bypassed.

Opened the exact user ZIP and matched archive + all five PDF hashes against
hus_source.json. Read PDF104 pages 1–3: QD3568 on decision page, application
from 2022/K67 on page 2, nominal four years on page 3. Page 3's QD3569 caption
differs from decision page; source scan unchanged. No claim to a fresh independent
full-field review of all PDFs; existing user sign-off covers KHMTTT hash
bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab.

Found local runtime still using old draft KHMTTT revision 7aafa016... despite
that reviewed source in Git. After source/PDF preflight and diff, called existing
publish_catalogs on the loopback APP database engine in its normal atomic four-
catalog transaction. KHMTTT restored to verified revision
c46163d1629819649f9bc8d54db59156d8a46ee40deec6c6d1fdb923c731e1da.
All 67 source/prerequisite states verified under existing sign-off; three other
programs remain draft. No code/name/credit/prerequisite/type changes. KHDL adds
the already-curated parent V.2 source locator/28–63 discrepancy note only.
No source JSON/review record/account binding/transcript edits. Old immutable
revisions retained for rollback; backup contains public catalog before/after.
If a real account binding points at the old fingerprint, its owner must confirm
the current program/cohort through the existing review UI; do not auto-bind.

Verification: 621 pytest passed/80 DB deselected including PDF acceptance;
existing Starlette warning and two Windows stdout-decode warnings. Both affected
builder cases rerun with PYTHONUTF8=1 passed without decode warnings. Node model
checks and five synthetic Chrome suites passed: recommendation intake, saved
plans, VNU-only, presentation, study desk. New browser coverage includes custom
directions with/without required track, empty input, final-only chat in 3/4 stages,
all credit-range boundaries, K68/K69/cohort refresh/missing cohort, long mobile
text, existing compare/save/lost-response/logout, themes/VI-EN/reduced motion.
Actual active catalog + invented transcript gives strict context/board ready,
without preview. No real VNU credentials, personal-record inspection or model call.

Report docs/RECOMMENDATION_INTAKE_2026_11_04.md; ignored evidence and publication
receipt backups/recommendation_refinement_20261104/. App remains running without
restart at http://127.0.0.1:8000/#recommend; listener PID 9328 observed, verify
identity before stopping. Health/ready/homepage 200, 22 HTML assets + imported
model match disk, personal anonymous routes 401. Ruff/JS syntax/diff pass.
## Publication authorized — 2026-11-04: metadata-aligned intent extraction

User explicitly requests 20 content commits, push, PR and merge into main for
the current shared preference vocabulary, real-provider terminal tool and
fallback corrections. Use a feature branch and Create a merge commit, preserve
all teammate commits. Main advanced to 1a5a79c (51 reachable commits since local
86479f4); feature branch starts at origin/main with all local changes carried
forward because none overlap. No teammate history is rewritten.
Earlier local-only restrictions are superseded for this scoped publication.
No provider spending, DB/catalog publication, secrets or runtime restart is
included. Integrated validation on 1a5a79c plus local changes: 1347 offline
passed/117 deselected, one existing warning in 50.56s; Ruff, four synthetic
catalog checks, recommendation-model and chat Node checks passed.
Remote PR/CI/merge outcomes must be verified, not inferred from this note.

## Local fallback fixes — 2026-11-04

User authorizes fixing reviewed fallback bugs. preference.py ignores negated
numeric amounts and lower bounds, recognizes upper-bound phrases, conservatively
takes the smallest remaining limit unless an explicit correction replaces it.
Out-of-range numbers do not match valid trailing digits. Vietnamese đ folds to d
so “đổi thành” is recognized. Course-type matching uses negation handling;
career_goal remains null for study-only requests and is bounded to 200 characters
for supported explicit career-intent patterns. These are bounded heuristics, not
semantic validation of successful LLM responses. 19 regression cases added;
41 focused cases pass, full SE_Project offline rerun 1261 passed/90 deselected,
one existing warning in 47.65s; Ruff/diff checks pass. Sandbox run interrupted
because internal HTTP tests stalled; completed outside-sandbox run is evidence.
No model/provider call, DB write, commit, push or runtime restart performed.

## Local preference vocabulary correction — 2026-11-04

User requests extraction aligned with project metadata and explicitly confirms
shared canonical labels, including software_engineering for software development.
app/recommendation/vocabulary.py derives the version-1.0 intent label set from
COURSE_METADATA_SPECIFICATION.md section 5, union selected-catalog extensions.
Extractor, service validation and fallback use those intent labels; this does
not change course metadata, catalog validation, HUS builder/revision or DB.
Existing API preference field names remain compatible. Terminal tool additionally
prints metadata_preferences mapping interest_topics→topics and
course_type→requirement_type; it is not a CourseMetadata record. No real provider
call, catalog publication, commit/push/PR/merge or runtime restart requested here.
22 focused offline cases and Ruff pass; full Conda SE_Project offline regression
1242 passed, 90 deselected, one existing Starlette/httpx warning in 42.73s.
First sandbox run stalled and was interrupted; completed rerun outside sandbox
is the regression evidence. Earlier empty-catalog-means-empty-intent
notes describe the superseded behavior; course facts still require field evidence.

## PR #97 merge authorized — 2026-11-03

User now explicitly requests creating a PR and merging LLM feature extraction
into main. This supersedes the preceding branch-only/no-merge restriction for
this feature. PR #97 retains the 15 original commits at 519ab38. Main advanced
to 05ffe0f with the team's recommendation UI and standalone HUS RAG changes.
Merge main into the feature branch, preserve both contributor note blocks and
all team/source ancestry, validate the combined tree, then use Create a merge
commit on GitHub after CI passes. Do not squash or rebase. No production DB,
metadata publication, provider call, runtime restart or BT3 merge is requested.

Integrated verification: Conda SE_Project dependencies were synchronized with
requirements-dev/requirements-lock after the newly merged HUS modules exposed
missing PDF/DOCX dependencies. Completed rerun: 1237 offline passed,90 deselected
in39.22s; Ruff, both catalog checks and recommendation-model/chat Node checks
passed. First collection attempt failed for missing dependencies; it is not
success evidence. Only contributor notes conflicted; retained both sides.
HUS/UI/data/dependency/workflow files match origin/main byte-for-byte.

## Publication authorized — 2026-11-03: LLM feature extraction

User explicitly requests returning to the unfinished branch, creating exactly
15 meaningful commits and pushing feat/llm-feature-extraction. This supersedes
the local-only/no-commit notes below for this scoped change set. Baseline is
5239b7333a8f8cdf0f919e6b0505af0def99fe23. Keep the separate BT3 assignment
branch/worktree out of this publication; do not change main or merge a PR.

Commit groups: preference/ranking models; safe keyword fallback; catalog-scoped
extractor; metadata scoring; runtime adapter factory; recommendation limits;
advisor response schema; shared advisor integration; compatibility API routes;
authenticated academic API; extractor/validation tests; service integration
tests; feature documentation; README navigation; contributor checkpoint.
No empty commits or invented authorship. Preserve the reviewed final code/test
bytes while staging these groups; use Git to verify exactly 15 new commits.

Publication preflight in Conda SE_Project: 17 focused cases passed; 628 offline
passed, 90 DB/source deselected in 3.56s; Ruff and diff checks passed. Existing
Starlette/httpx warning remains. Synthetic/fake-provider tests do not establish
real-provider language accuracy. No paid API, runtime restart, DB/catalog write,
new chat UI or metadata publication is included. Publication outcome must be
verified from Git/GitHub, not inferred from this preparation checkpoint.

## Local implementation — 2026-11-02: shared LLM feature extraction

User explicitly selects full integration into advisor and recommendation from
an attached extraction proposal. Work is on feat/llm-feature-extraction; no
commit/push, API spending, production DB/catalog writes or runtime restart.
CatalogFeatureExtractor validates strict StructuredPreference fields against
selected catalog vocabulary and falls back to current-message keywords on
provider/schema/label failure. Advisor uses bounded user-only history, exposes
preference JSON and rejects suggested bundles over extracted limits. Current
intent overrides old topics via prompt rather than unconditional history union.
No-provider fallback intentionally uses current message without guessing history.
Recommendation takes min(request limits, extracted limits); topic IDs and career
IDs match directly, and default soft-feature weights are positive. Existing
eligibility/auth/context/source checks and ranker interfaces remain in place.
HUS builder vocabulary is still empty; this does not publish topics/careers or
invent course metadata. No active chat UI or new ranking algorithm is claimed.
Conda SE_Project: 628 offline passed, 90 DB/source cases deselected; 17 new
synthetic extraction/integration tests; Ruff and diff checks pass. Existing
Starlette/httpx warning remains. Tests use fake providers, not real language
accuracy/paid-API acceptance. See docs/LLM_FEATURE_EXTRACTION.md.

## PR #6 conflict resolution - 2026-11-02

User explicitly requests fixing conflicts of crawldata -> main PR #6. This authorizes
merging current main into crawldata, scoped fixes/tests, a merge commit and push to
update the PR; it does not authorize merging the PR into main or production activation.
Main baseline af8d4db and crawldata642706c. Preserve main API/auth/UI exactly and retain
HUS data/pinned validator bytes. Standalone app.hus.demo owns RAG/basic chat; main does
not register public HUS demo endpoints. Legacy HUS HTTP/Node tests target the active
standalone contract after merge. The old snapshot preparation helper from main lives
in tools/hus_snapshot_preparation.py; reviewed tools.prepare_hus_corpus retains its
original bytes and build identity. Main database jobs retained, separate RAG browser CI
added. Keep original local diagnostic HTML/HUS_MANUAL_TEST and frozen P04/P05 worktrees.
No product DB/VNU/provider access. See docs/HUS_PR6_CONFLICT_RESOLUTION_2026_11_02.md.


## Current Handoff — 2026-10-28

- Publication authorized (2026-11-02): user explicitly requests committing/pushing
  current RAG changes to GitHub in fewer than20 new commits. Publish on crawldata;
  seven content commits plus one byte-preservation fix (8 total) from be76f50b,
  normal fast-forward push. This overrides
  older local-only/no-commit notes for this publication only. Main integration,
  production activation and merging other histories remain outside this request.
  Keep imported v3/validator provenance pinned to original a543cf8d (Viet Nguyen);
  import commits describe byte-exact vendoring, never claim copied work was authored
  by the integrator. Preserve local diagnostic HTML and HUS_MANUAL_TEST.md outside
  publication; backups/config/toolkit stay local. Verify Git/remote for actual outcome.

- Latest RAG scope correction (2026-11-02): user explicitly limits this branch to
  F1/F2/F3 and basic conversation, no course ranking/explanation. New app.hus.demo:app
  and app.hus.chat isolate execution/imports from the product academic stack. New
  hus-rag-demo UI selects real release majors/versions; no transcript, fake catalogs,
  account, eligibility or provider needed in local demo. Tracked command:
  python -m tools.run_hus_rag_demo; old ignored open_hus_rag_demo.py now aliases it.
  Basics use fixed greetings/thanks/help/goodbye; out-of-scope requests abstain.
  Academic citations/review/AI opt-in/source bytes unchanged. P04/P05 worktrees and
  receipts remain historical; their mixed advisor router is not the new RAG path.
  Before main publication, integrate a dedicated HUS endpoint with existing verified
  account/CSRF/Origin/binding/revision and obtain new commit/CI/acceptance evidence.
  No commit/push/production activation authorized here. See docs/HUS_RAG_MANUAL_DEMO.md,
  scope design/plan dated2026-11-02 and docs/acceptance/hus_rag_scope_report.json.
  Final local checks:18 scope tests (also newer FastAPI0.143), full crawldata717 pass/
  26 skip in crawler-complete p04 venv,5 Node legacy,50 Chromium questions4 majors,
  stale scope/PDF13+12 pass. First full attempt in p05 runtime venv lacked python-docx;
  complete rerun passed; no runtime venv/dependency mutation. P04/P05 outputs34/43,
  shared inputs77 each and63 data hashes verified unchanged. No commit/push.

- Historical manual RAG demo before scope correction (local 2026-11-02): ignored launcher
  backups/hus_integration/open_hus_rag_demo.py opens frozen p05-main in visible
  Chromium with synthetic in-memory account/context and real HUS RAG data. Uses
  p05-ci-venv, defaults data_science; --major selects other programs, --smoke checks
  real F2 answer/citation headlessly. No product auth/DB/VNU or frozen source changes.
  See docs/HUS_RAG_MANUAL_DEMO.md; keep terminal running, close app tab/Ctrl+C to stop.
  Follow-up fixed non-HUS prompts causing the harness's forbidden-provider500:
  launcher-only scoped fallback preserves scope guards and gives honest demo help,
  no synthetic-course recommendations.48 mixed Chromium cases across4 majors pass;
  fresh product regression672 Python/9 Node pass; frozen source/test hashes unchanged.
  Existing demo processes must restart; receipt docs/acceptance/hus_manual_demo_report.json.

- P0-5 preparation (local 2026-11-02): isolated p05-main worktree on main5239b733,
  branch integration/hus-rag-p05-20261102; root stays crawldata. Reviewable bundle
  integration/hus-rag-p05 has77 shared inputs/43 outputs; replay61 backend/9 Node pass.
  CI workflow/locked deps, build/data/test identity receipts and guarded activation/
  rollback implemented. Clean locked venv:672 Python/10 skips/80 DB deselected,
  9 Node,43 HTTP/14 Chromium pass;20 lifecycle cases and copied-selector drill pass.
  Canonical selector remains prepared/byte-identical. Dirty receipts are ineligible;
  strict rejects uncommitted code. Preserve genuine source authors/ancestry and main
  feature-branch PR/Create a merge commit. No commit/push/PR/merge, remote CI or real
  production activation: user explicitly requires a separate commit/push request.
  See docs/RAG_P05_RELEASE_PREPARATION.md and docs/acceptance/hus_p05_* reports.

- P0-4 (local 2026-11-02): main5239b733 fetched and integrated in isolated worktree
  backups/hus_integration/p04-main, branch integration/hus-rag-p04-20261102. Root
  remains crawldata with prior WIP. Adapter runs in /me/advisor/chat after existing
  operation/ready and rechecks ensure_current; strict AI opt-in, server-bound major.
  Keep verified account, CSRF/Origin/host, source/binding/session revision. Legacy
  HUS chat409, no public /hus/chat; source binaries account-protected. Active UI adds
  separate hus-chat module with generation/refresh race guards, no stored history.
  652 Python/10 skipped/80 DB deselected,9 Node,43 live HTTP/14 Chromium pass using
  synthetic auth stores/policies/catalogs and real HUS data; no product DB/VNU/provider.
  Reviewable replay package in integration/hus-rag-p04 plus prepare_hus_main_integration
  tool;77 shared inputs/34 source outputs verified, replay41 backend/9 Node pass.
  See docs/RAG_P04_MAIN_INTEGRATION.md and hus_p04_authenticated_report.json.
  Ready gate/review/source bytes unchanged. No commit/push/PR/merge or production
  activation; P0-5 owns publication, must retain feature-branch PR and team ancestry.

- P0-3 (local 2026-11-02): independent character-to-page ownership oracle for F1
  quotes; F2 oracle requires every source occurrence exactly once and PDF locators,
  never JSON as open target.29 new regression/API tests, including21 intentional
  citation corruptions. Node explicitly tests null-link AI responses. Chromium tests
  actual MAT3325 answer with two same-PDF sources at13/12 and opens both viewer pages.
  Receipt schema2.0 additionally pins24 test/fixture files and10 screenshots;2318 HTTP,
  47 Chromium pass;699 Python/26 skipped,5 Node. PDF viewer readiness waits for
  load success, physical page, zero unacked remote scrolls and matching inner-frame
  scroll, then two animation frames. See docs/RAG_P03_CITATION_TESTS.md and receipt.
  Runtime/data/review unchanged in P0-3; next scope is main API/UI/auth integration.

- P0-2 (local 2026-11-02): citations now have evidence kind/display label/open URL,
  expected document hash, physical page/span and availability. Generated F3 renders
  "kiến thức AI" without links, retains warnings/opt-in/review. Web opens original URL.
  data/hus/citation_assets contains12 PDFs+2 DOCX imported byte-exact from a543cf8d,
  registry bound to selected v3. /hus/sources/{sha256} GET/HEAD/range verifies actual
  bytes/hash/format/page; PDF inline, DOCX attachment; missing or changed files fail
  honestly. F1 page locations match quotes in hash-bound recovered text, not new
  academic/visual review. v3/legacy payloads and review unchanged. See
  docs/RAG_P02_CITATIONS.md; acceptance receipt hus_p02_citations_report.json.
  Verification:670 Python passed/26 skipped,4 Node,2318 HTTP,41 Chromium;14 binaries
  and28 emitted page URLs checked. Full Chromium channel is needed for PDF viewer;
  external web destinations are intercepted in browser tests, not health-certified.

- P0-1 (local 2026-11-02): runtime now strictly selects CURRENT -> portable
  hus-data-20261031-v3 (sha256 27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4).
  Imported exact release/validator bytes from a543cf8d; legacy 19 payloads retained.
  F1 69->65 is four resplits with the same63 units/source spans/edition/review; F2 tables
  unchanged, canonical source imports existing67 KHMTTT user sign-offs and223 draft,
  never institutional certification or F3 approval. API and retriever pin one snapshot;
  missing/corrupt CURRENT is503, no legacy fallback. Generated opt-in defaults false
  (allow_generated_reference in API, checkbox in legacy chat); each response includes
  release identity. See docs/RAG_P01_DATA_SELECTION.md and machine-readable diff.
  Older data/receipt statements below describe legacy snapshots, not current selection.
- End-to-end acceptance (local): `tools/verify_hus_e2e.py` runs real loopback Uvicorn
  and optional real Chromium with synthetic UI catalogs and the actual HUS handoff.
  Latest receipt: docs/acceptance/hus_e2e_report.json; 2310 HTTP and 25 browser cases pass,
  full membership/field and citation checks, cross-major/version refusals and stale-chat
  isolation. See docs/HUS_E2E_ACCEPTANCE.md. Exam weight/format fact requests now route
  to evidence checks before recommendation intent; major aliases consume specific names
  before contextual Math aliases. No product DB/provider/remote deploy or academic review.
- Answering addition (local work): `app/hus/answering.py` and `app/schemas/hus.py`
  provide extractive F1/F2/F3 answers with explicit sources/review/generated labels.
  `POST /hus/chat` exposes this; `/advisor/chat` routes clear HUS information intents
  before runtime catalog/provider calls, keeps recommendation/guardrails on the old path,
  and returns mode=hus_rag plus hus_answer. Unsupported/official-current/missing evidence
  returns no_information, incomplete identity needs_clarification; corrupt packages are
  503, not fabricated missing answers. The service lazy-caches one snapshot; reload after
  package changes. UI links HTTP(S) citations and rejects old-context chat responses.
  Raw-only unresolved prerequisite codes (MAT3423 -> MAT3402) now remain flagged without
  creating parsed eligibility edges. No LLM, product DB, remote deploy or academic review.
- Retrieval addition (2026-11-01, local work): `app/hus/retrieval.py` provides
  `HUSRAGRetriever.search()` over the loader's F1/F3 chunks. Major/version/field/variant
  and explicit/query course codes filter before BM25 scoring/top-k; no cross-scope
  fallback or qa/origin directory scan. Vietnamese accent-insensitive lexical ranking
  excludes repeated F3 warning/context from topic scoring but preserves output metadata.
  Deduplicate identical slices only within the same scope/source. No embeddings,
  generated answers or API integration; F2 remains the loader's structured lookup.
- Loader addition (2026-11-01, local work): `app/hus/rag_loader.py` provides
  `HUSRAGData.load()` for the shared package. It validates package files/checksums,
  reads F1/F3 chunks separately and looks up F2 by exact code/major/version, retaining
  reviews, provenance, generated warnings, raw prerequisites, duplicate source rows and
  unresolved/conflicting states. Results are defensive copies. This is an offline
  snapshot library, not retrieval/API integration, academic verification or a new raw
  review gate. Reload after rebuilding the package; do not assume it was published.
- Active data-preparation branch: `crawldata`. Base before this work was `38a5ddbd604469754e8e4de0c423a08e8976cdb6`. The user explicitly requested publication as **exactly 30 new commits**; inspect Git/remote history for the final publication state, never infer it from this note.
- Current shared handoff is `data/hus/rag/{f1,f2,f3}` with checksums/origin paths in its manifest. Keep the source/release artifacts under `data/hus/qa/20261028/` for reproducibility; index only one copy of each dataset.
- F1 currently has 15 sources / 69 chunks: 5 raw-HTML-compared sources plus 10 sources explicitly approved by the user for descriptive F1 from existing Markdown. The ten use `include_markdown`, selected-F1 scope and `raw_original_verified=false`; do not claim original PDF/DOCX or current academic validity was verified. The mixed Toan Co careers page was excluded by user request, pending is empty, and duplicate CLC narratives retain provenance without duplicate retrieval weight. The original raw review gate remains unchanged.
- F2 exists for all four majors on remote main at `cfb2ec4c7f3f8e80428abc3db535dad0cc5db41d`: `database/data/hus_source.json`, 290 course/program memberships and 297 source occurrences. A byte-identical pinned copy is retained in the F3 inputs and shared `rag/f2`. The local crawldata curriculum sample alone is not the complete repository-wide F2 inventory. Preserve source draft/unresolved/conflict states.
- F3 is a separate AI-generated reference dataset explicitly requested by the user: 290 records / 870 chunks, 174 in-scope codes, 154 authored concept blueprints. Keep disclosure labels, edition/major filters, and official syllabus/assessment/weight fields null. Do not insert generated F3 through the official-source review gate or present it as an official HUS syllabus.
- Latest local verification before publication preparation: **541 passed, 26 skipped**; Ruff, diff checks, all applicable release reproductions and shared payload checks passed. No embeddings/vector index, live chatbot/LLM, database publication, or remote CI verification is implied. Two diagnostic HTML files and `docs/HUS_MANUAL_TEST.md` were untracked before this task and remain outside its commits.
- Older statements below about missing product data/PDFs apply to the historical local foundation checkout. Current source limitations and the Markdown-only F1 exception are documented in `docs/HUS_QA_DATA_AUDIT.md` and the current dataset READMEs.


## Main contributor context preserved during PR #6 resolution

## Recommendation UI integration preflight — 2026-11-02

User explicitly requests integrating feat/recommendation-conversation-ui into
the current system, with regular progress, commits, a GitHub PR and an issue.
Issue #67 tracks this integration. Use a PR and Create a merge commit; preserve
all 19 original source commits/authors at c823aa5 and the current main 5239b73.
Local integration branch integration/recommendation-conversation-ui-20261102
contains merge 93167bd, with no conflict and an identical source application tree.

Fixed only a browser-test isolation issue: check_vnu_only now serves HTML/static
through common_route rather than requiring a real server on port 8000. Existing
assertions and intercepted API behavior are retained. Added frontend test commands
and integration evidence in docs/RECOMMENDATION_UI_INTEGRATION_2026_11_02.md.

Validation: 621 offline/PDF passed, 80 PostgreSQL deselected; seven synthetic Chrome
suites, Node model/analytics, Ruff, JS syntax, catalog builders and diff checks pass.
One existing Starlette/httpx warning remains. No backend/schema/catalog change,
new LLM extraction/ranker, RAG, real VNU login, personal-record read or paid model.
Main integration and runtime activation are pending publication at this checkpoint;
verify their eventual outcome from Git/GitHub and the ignored integration receipts.

Root had a separate uncommitted 2026-11-02 admin/issues memory note; its original
bytes and patch are saved in backups/recommendation_integration_20261102. Keep that
unrelated note local and restore it when updating root. Preserve .vscode, previews,
configuration and HUS v3. Do not merge the admin branch or activate HUS v3 here.

## Recommendation UI publication authorized — 2026-11-01

User now explicitly requests a NEW branch without a personal name and 15–20
meaningful commits, followed by a GitHub push. This supersedes the local-only
restriction for the recommendation UI source/tests/docs/memory immediately below.
Target feat/recommendation-conversation-ui, base 5239b73 from origin/main;
19 non-empty commits separate request/model rules, model tests, planning bridge,
conversation, roadmap/details, comparison, API/save lifecycle, desktop/responsive
styles, HTML integration, book clearance, existing browser regressions, new
browser coverage, implementation report and this contributor checkpoint.

Preserve working files while staging logical increments; leave the full UI
unmounted until its JS/CSS dependencies have been added. Keep source ancestry
and configured author identity. Push only the new ref, without force; do not
change main or the earlier feature branch. Do not include .vscode/settings.json,
credentials/configuration, AD-102, logs, previews, videos or other backups.

The implementation/tests are the verified local version described below. No
backend, data or application restart is required for publication. Verify the
final tree against the pre-publication snapshot, exactly 19 non-empty commits,
remote head and tracking state. This is authorization/preparation; actual commit
and push results must be established from Git and the ignored publication receipt.

## Local recommendation conversation UI — 2026-11-01

User accepted the proposed full recommendation UI and requested pulling GitHub
first. Root feat/vnu-curriculum-planning fast-forwarded from fba94de to fetched
origin/main 5239b73, preserving team ancestry. This task has no new Git commit,
push, PR or deployment. Existing untracked .vscode/settings.json and ignored
credentials, AD-102 and backups remain local. Prior publication notes below
describe historical work, not publication authorization for these new UI edits.

Implemented recommendation-workspace.js/css and pure recommendation-model.mjs;
index.html mounts them in #recommend. course-status.js provides a small shared
planning-state/configure/draft bridge without changing academic rules or data.
Retained source review, planning controls and saved alternatives inside
#academic-plan-tools; browser fixtures open the real summary before using them.
motion.js keeps the existing background book clear of the new conversation,
roadmap and headings. No new dependencies, backend/schema/catalog edits.

Guided preferences cover direction, workload, editable default 20 credits,
graduation goal and real applicable track/path choices. Desktop has a live
roadmap, mobile a native dialog sheet. Three alternatives use the verified
/me/academic-context revision and /me/recommendations, with explicit required
course preference and differing topic/type/workload weights. Real catalog
metadata only; no claimed future offerings, graduation ETA or fabricated
differences. Strict planning/source gates still apply. Details show actual
AND/OR prerequisites; compare/save use real codes and existing server APIs.

Saving is explicit, CSRF-protected and basis-checked. A lost response/60-second
timeout does not show false success or permit an immediate duplicate POST;
the UI directs the user to check saved alternatives. This is not server-side
idempotency. Session/revision changes discard stale results and private dialog
content; conversation is not persisted in browser storage. Motion uses WAAPI/
CSS, pauses while hidden and honors reduced motion. See implementation report
docs/RECOMMENDATION_WORKSPACE_2026_11_01.md for contracts, timings and limitations.

Verification: 611 offline passed, 90 deselected, existing Starlette/httpx warning.
Node model checks plus frontend-payload-to-real-backend-scoring smoke passed.
Seven synthetic Chrome suites passed: recommendation workspace, course map,
saved plans, VNU-only, presentation, study desk and motion. New checks include
three variants, quota/budget gates, details/compare, save success/409/lost response,
logout race, VI/EN, 1440/1024/390, themes and reduced motion. Presentation contrast
now samples the actual existing login gradient; the former helper treated its
transparent backgroundColor as white. The 4.5 threshold is unchanged. Ruff,
affected JS syntax and diff checks pass. No real VNU credentials, personal-record
inspection, model call, DB acceptance/load/FPS benchmark or Firefox/Safari test.

Started Docker Desktop and existing se_hus_db; storage/auth preflight succeeded,
no migration/seed/catalog publication. Local tools.run_local runs hidden without
reload at http://127.0.0.1:8000/#recommend. Launcher PID 20012/server PID 14416
are observed launch/session records; verify identity before stopping. Health,
ready and homepage 200; 22 HTML assets and imported model match disk, JS module
MIME correct; anonymous course-status/plans remain 401. Screenshots/video/JUnit
are ignored under backups/recommendation_workspace_20261101 and local_runtime.
Keep the app running for review. New uncommitted frontend/tests/docs/memory must
remain local until the user authorizes publication for this work.

## Publication authorized — 2026-11-01: current course map and planning UI

User explicitly requests many meaningful commits and publishing the current
version into main. This authorizes the existing scoped source/tests/docs/memory
edits, superseding their local-only notes below for this publication. Use the
current integration branch, GitHub PR and Create a merge commit; retain original
source/team ancestry. Do not include .vscode, previews, backups or configuration.

Current UI keeps completed/available/blocked columns and search in Điều kiện học;
planning controls, progress and saved alternatives are in Gợi ý kỳ tới. Removed
the generic unresolved-results map sentence because a planning-only pause also
set progress_is_lower_bound. Actual course facts and validation are unchanged.

Publication preflight: 621 offline/PDF cases passed, 80 DB cases deselected;
three current Chrome regressions passed (map, saved plans, VNU-only). Previous
80-case disposable PostgreSQL and study-desk evidence is recorded below; no new
runtime DB changes or restart requested. Ruff, JS syntax and diff checks passed.
Remote main was fetched at 94b7d05; no divergence requiring conflict resolution.
This is an authorization/preparation note. Verify PR, CI, merge and final remote
hashes from Git/GitHub and the ignored publication receipt, not this checkpoint.

## Local UI refinement — 2026-11-01: map and planning tabs separated

User tested the local integration and requested that Điều kiện học contain
only completed/available/blocked courses and search. Moved saved semester plans,
track/graduation-path and credit-budget controls, progress summaries and source
review/confirmation panels into Gợi ý kỳ tới. Removed the framed transcript and
planning notices from the course map; retain short source/error/preview status
when necessary. Both views share the existing source, draft and validated APIs.
Direct #recommend loading, navigation/focus, plan motion, logout cleanup and
sessionStorage remain functional. Existing source data and catalog rules unchanged.

Updated course-status.js, index.html and the affected docs/browser regressions.
Four synthetic Chrome suites passed: course status, saved plans, VNU-only UI and
study desk. Ruff, JS syntax and diff checks passed. Static files are served live
on port 8000 with content-based script versioning; no restart, VNU credentials,
personal-record inspection, DB operation or new commit/push in this UI refinement.
Keep the source/docs/test edits and prior dirty files local. Prior integration
HEAD remains b13181b. Refresh the page to see the new layout.

## Local integration completed — 2026-11-01: VNU curriculum planning

User requested reviewing feat/vnu-curriculum-planning, integrating it into the
current local system if sound, making meaningful commits and reporting percent
progress. Reviewed fetched source fba94de5893a108246555a48d8b8ea767767fc08;
preserved all 13 original source commits/authors and the previous local HEAD
5d60a38. Root now runs integration/vnu-curriculum-planning-20261101 at b13181b.
Seven new local commits cover two ancestry-preserving merges, three scoped
fixes/features and two documentation changes. No push, GitHub PR/main update,
squash, rebase, source-branch change or manufactured authorship occurred.

Fixed a reproduced budget bug: hidden excluded-credit courses consumed the
suggestion budget before filtering. Recompute suggestions from visible,
planning-eligible rows, retaining quota, budget and global gates. Added Restore
suggestions for the draft after per-card checkboxes were removed; it does not
write saved plans. Semantic merge of the older local academic commit re-added
review lookup before identity validation; removed that duplicate to retain
PR #22's repaired builder behavior. View-only prerequisite chains remain barred
from same-term plan selection; no academic facts or catalog approvals changed.

Verification: source baseline 609 offline passed/90 deselected. Integrated
offline including existing PDF acceptance: 621 passed/80 deselected. All 80
PostgreSQL tests passed on a separate disposable PostgreSQL 16 container at
127.0.0.1:55441, which was then stopped/removed. Three synthetic Chrome suites,
Ruff, JS syntax, analytics and both catalog builder checks passed. Root board
and saved-plan Chrome suites passed again after activation. Existing Starlette/
httpx warning remains; use PYTHONUTF8=1 for subprocess encoding on Windows.

Existing index.html notice edit is restored byte-for-byte; .vscode and previews
remain unchanged/untracked. This memory retains both source notes and the entire
preceding local memory. Config and HUS v3 payload hashes are unchanged. Original
tracked edits are also retained in stash 7ea5214e1233e08cc7c0a01e7448df05234ca1fa;
do not pop it onto the already restored workspace. Do not commit old dirty work
implicitly. Report: docs/VNU_CURRICULUM_PLANNING_REVIEW_2026_11_01.md.

Docker/app were initially stopped. Started Docker Desktop and existing se_hus_db
with its volume; no runtime migration, seed or catalog publication. Started root
tools.run_local hidden after successful public VNU form probe without credentials.
Launcher PID 28328, server PID 26772 are launch-time records; verify identity
before stopping. App remains at http://127.0.0.1:8000. Homepage/health/ready pass
with PostgreSQL; all 20 served assets match disk; anonymous map/plans return 401.
No real VNU login, personal-record inspection or model call. Detailed receipts,
JUnit, original files and runtime logs: backups/curriculum_planning_review_20261101/.
HUS v3/RAG remains separately prepared and is not integrated by this work.

## Publication target corrected by user — 2026-10-31

User explicitly requests removing the just-created course-map branch and
publishing the same work to feat/vnu-curriculum-planning instead. This overrides
the new-branch-only restriction in the checkpoint below. Preserve all 12 original
commits/hashes/authors ending at 962b8617bbfe081bacb3201eb3e97039453e2402;
do not recreate, squash, rebase or force-push them. The target fast-forwards from
local main baseline 94b7d05, preserving the previously pulled team history.
This contributor-note correction adds one documentation commit, making 13
course-map commits relative to main, still within the requested 10–15 range.

GitHub's temporary branch currently has the name
feat/course-map-improvements-20261031 at the exact original tip 962b861;
the earlier feat/vinh-course-map-improvements-20261031 remote name is absent.
Push and verify the requested target first, then remove the temporary remote
branch only while its head still matches that original tip, and remove the
local temporary branch after confirming its history is retained on the target.
Do not change main or feat/vinh-database-tests. Existing untracked
.vscode/settings.json is user-local and must stay unstaged and unchanged;
credentials, AD-102 and ignored backups remain local. Application/test sources
are byte-identical to the verified 12-commit publication, so the 609-test and
Chrome evidence below remains applicable. No runtime/DB work or test rerun is
needed for moving refs and this note. Verify the outcome from Git; this is the
authorization/preparation checkpoint, not a claim that the push already finished.

## Course map publication authorized — 2026-10-31

User explicitly requests committing/pushing current map work to a NEW branch
in 10–15 separate commits. Target: feat/vinh-course-map-improvements-20261031,
based on current main ancestor 94b7d05988d4118df283ad09a12ff75cef3161fc.
Plan 12 non-empty focused commits: display filtering; prerequisite reachability;
review-gate seeds; plan validation/unit coverage; API/name contracts; frontend;
obsolete checkbox CSS; board browser checks; saved-plan browser checks; motion
browser compatibility; product documentation; contributor checkpoint.
This authorization supersedes the preceding local/uncommitted/no-publication
notes for these 11 reviewed files. Do not force-push, rewrite teammate history,
or publish main, feat/vnu-curriculum-planning or feat/vinh-database-tests.

Fresh publication preflight: 609 offline tests passed, 90 deselected, one existing
Starlette/httpx warning. Whole-repo Ruff, affected JS syntax, Node analytics,
both catalog builder checks and two synthetic Chrome regressions (course board,
saved plans) passed. Earlier study-desk Chrome validation remains applicable.
No PostgreSQL/full-source acceptance rerun, real VNU login or data migration in
this publication. AD-102, .env/.env.auth, DB backups, logs and screenshots remain
ignored/local. Preserve disk content while staging focused backend increments.
Only the new branch ref may be pushed. Verify exactly 12 commits against the
base, final tree equality, remote head and clean worktree after push. This note
records authorization/preparation; use Git to establish the publication outcome.

## Prerequisite labels include names — 2026-10-31

User requests code: course name inside prerequisite parentheses. Both yellow
follow-up explanations and red missing-prerequisite reasons now use shared DOM
formatting, preserving AND/OR and bolding only the course name. /me/course-status
adds prerequisite_courses with code -> name/name_en from the same catalog;
lookup includes referenced courses hidden from the columns. UI falls back to
all unfiltered board rows for older responses, and retains bare code for unknown
external references rather than inventing names. Names use textContent, never
HTML; EN prefers name_en with Vietnamese fallback. No classification/GPA/plan
rule, source record or catalog state changed. MAT3533 was read from current
KHMTTT catalog as Hoc may (Vietnamese accents retained in product).

35 focused academic API tests and synthetic Chrome board regression passed,
covering both groups, bold literal HTML-like names, hidden/unknown references,
search, VI/EN, mobile/themes and logout. Ruff/JS syntax/diff passed. Local server
restarted through tools.run_local, launcher PID 20212; verify identity before
stopping. Health/ready 200 and all 20 assets match disk. No reload, real VNU
credentials, personal-record inspection, database writes or publication.
All preceding uncommitted map changes are preserved and remain uncommitted.

## Follow-up availability regression fixed — 2026-10-31

User clarifies again: if prerequisite A can be in the available column, dependent
B must be there too, including longer chains. Found a concrete bug in the prior
display projection: reviewed_course_board moves otherwise rule-eligible courses
to academic_review_required when planning pauses or their own outcome is pending.
The projection restored missing-prerequisite rows only, so those seed courses
stayed red and broke the entire chain. Reproduced with invented A completed,
B requires A, C requires B: a planning-only pause left both B/C red.

course_board_display now restores ONLY academic_review_required-only rows before
following missing-prerequisite clauses to a fixed point. They already passed
the underlying source/prerequisite/track/quota engine. Restored rows have
eligibility_basis=completed_prerequisites; dependent rows remain
available_prerequisites. Both get planning_eligible=false, suggested=false;
validators and saved-plan validity honor the flag. Completed results, progress,
strict eligibility/recommendations, source evidence and global planning gates
remain unchanged. Continue omitting excluded credits from all three columns
and showing no plan checkbox. Do not reinstate either removed UI behavior.

Five new regression cases prove planning selection, outside-code, program-rule,
metadata-preview and own-result review cannot shrink the displayed available
sequence for the same completed facts. 609 offline tests passed, 90 deselected,
existing Starlette/httpx warning only. Course-board and saved-plan synthetic
Chrome scripts passed; Ruff/JS syntax/diff passed. Read-only current KHMTTT
catalog with invented completed MAT1202/MAT3507 also verified MAT3374/MAT1207
available and no reachable prerequisite-only row left red. No real student
profile/grades, VNU credentials, DB writes, catalog publication or Git publication.
Updated local runtime restarted through tools.run_local, launcher PID 19568;
verify identity before stopping. /health and /ready 200, all 20 served assets
match disk, and anonymous course status remains 401. No reload mode.
All source/tests/docs edits from this and the preceding map task stay uncommitted.

## Course map display changed by user — 2026-10-31

Current root is feat/vnu-curriculum-planning at 94b7d05 after the user's explicit
pull from origin/main (fast-forward, clean before this task). Older branch/PID
claims below describe other sessions. This task is local only; no publication.

User supersedes the earlier excluded-course default: remove per-course next-term
checkboxes; omit courses excluded from earned program credits from ALL THREE
map columns; show follow-up courses as available when each missing prerequisite
AND/OR clause has an alternative already in the available column, transitively.
Keep actual completed facts, GPA/earned credits and source records unchanged.
Explain on follow-up cards that prerequisites must still be completed first.

Implemented course_board_display as a read-only projection at /me/course-status.
Excluded rows do not seed reachability or enter new suggested bundles. Only
missing-prerequisite blockers can be promoted; other source/unknown/conflict,
track/path/quota constraints and global planning gates remain. No unseeded cycle
self-unlocks. Conditional rows use eligibility_basis=available_prerequisites,
prerequisite_clauses and suggested=false. Strict academic APIs and plan assembly
retain real passed prerequisites; validation rejects conditional rows even if a
display board is accidentally supplied. Saved-plan UI remains, with automatic
suggestions and removal of courses; no replacement per-card selection control.
Frontend column counts/search also filter excluded rows; VI/EN copy updated.
Docs: docs/COURSE_STATUS_BOARD.md, latest section supersedes historical defaults.

Verification: 604 offline tests passed, 90 DB/full-acceptance deselected; existing
Starlette/httpx warning only. Three synthetic Chrome scripts passed: course board,
saved semester plans, study desk/motion (including real observed book turns).
Reviewed synthetic desktop screenshot; scripts cover mobile/themes, VI/EN,
search, no checkboxes, excluded rows, conditional messaging and logout races.
Whole-repo Ruff, JS syntax and diff checks passed. No real student data, VNU
credentials, sync or personal-account acceptance test was used.

Local updated server restarted through tools.run_local, launcher PID 18720;
verify process identity before stopping it. No reload. /health and /ready 200;
all 20 served assets match disk; anonymous map/plans remain 401. Before this
task, starting the pulled main required installing its new core dependencies,
creating a missing ignored .env.auth (random secret never printed), and upgrading
local DB hus_20261023_03 to hus_20261028_08. Backup was restored and migrated in
an isolated DB first; original-column hashes of all 17 original data tables
matched before/after. Restore-check DB removed; recovery evidence retained at
backups/local_runtime/restart_main_20261031_ccfaf22d67/. Existing .env and volume
were preserved; no seed or catalog publication. Current map task needs no schema
or data changes. Code, tests, docs and this checkpoint remain UNCOMMITTED.

## Session close - 2026-10-31: team assignments and local system relaunched

The user now requests session close and memory update only. This close-out
changes only this already-dirty root memory file locally. Do not resume backend,
RAG, admin, UI, algorithm work, tests, runtime operations or publication as part
of closing. No commit/push/PR/merge is requested.

The user clarified two target product flows: (1) LLM extracts structured features,
an algorithm scores/ranks eligible courses, then LLM explains the calculated
result; (2) RAG retrieves existing HUS evidence and LLM produces grounded answers
with citations and generated-content disclosure. Eligibility remains deterministic
and precedes ranking. A normalized fit score is not a calibrated probability.
This clarification describes the intended architecture, not completed delivery.

Final team assignments explicitly confirmed by the user and their screenshots:
- Vinh: recommendation chat UI and guided collection of student preferences,
  including direction, desired load, graduation path and target completion term.
- Trung: LLM extraction of structured features from student messages.
- Tai: HUS RAG retrieval/answering, citations to PDF/web sources and clear labels
  for AI-generated references. The screenshots confirm assignment; no teammate
  RAG implementation, deployed index or end-to-end delivery was verified here.
- Thang: complete the admin flow. The user explicitly chose this assignment;
  do not redirect him to tester work or the user's ranking/explanation tasks.
- The user: ranking/scoring algorithm and recommendation explanations.

A backend task for academic goals/effective constraints was proposed but NOT
assigned or implemented. It would reconcile form selections with extracted
preferences, expose validation/conflicts, reuse existing academic context,
progress and eligibility, and pass versioned inputs to the user's algorithm.
Treat a target graduation term as a goal, not a supported promise of completion.
No inferred assignment or permission to implement follows from that suggestion.

Read-only code audit found these current gaps: recommendation_service can use
LLMRanker directly; scoring.py provides a deterministic weighted keyword baseline;
explanation.py currently produces templates rather than an LLM prose step.
Extracted target_credits/target_course_count do not drive selection limits yet;
selection uses request.max_credits/request.limit. AcademicOperation has no target
graduation-term fields. The active recommendation tab only shows readiness and
a link to the VNU profile. /me/recommendations/what-if explicitly returns 409
academic_baseline_not_available. Existing semester-plan CRUD, source/binding,
progress and eligibility should be reused rather than assigned as missing work.
Plan comparison was another proposed extension, not a delivered feature.
The 17/10 checklist and many module/spec status sections are stale; prefer latest
memory plus code evidence. This audit did not run tests or change source code.

Earlier in this session the user explicitly requested running the local system.
Docker Desktop was stopped; started it in an approved execution context, then
started the existing se_hus_db container with its existing volume. PostgreSQL
ai07 on 127.0.0.1:5433 accepted connections. The public VNU form probe succeeded
outside the sandbox without credentials. Started the root venv with
python -X utf8 -m tools.run_local as a hidden background process at
http://127.0.0.1:8000. Launcher PID 25588; server PID 24320. Verify current
process identity before any later stop; these are launch-time records.
Homepage returned HTTP 200; /health and /ready returned ok, storage postgres.
Logs: backups/runtime_launch_20261031/app-5220ead6.stdout.log and .stderr.log.
No migration, seed/catalog publication, config/credential change, real VNU login
or personal-record inspection occurred. The app was left running; no further
restart or live checks were performed during this memory-only close-out.

Root remains feat/login-redesign-20261031 at 5d60a38, one commit ahead of its
remote-tracking branch. Preserve modified app/static/index.html, the existing
memory changes, and untracked .vscode/ and previews/. No branch/main update or
GitHub operation occurred. HUS v3 remains the separately published data release
recorded below; do not describe it or the teammate's RAG as integrated here.
Keep this memory update local until publication is explicitly requested.

## Session close — 2026-10-31: HUS data v3 published; RAG is the next phase

The user requests session close and a memory update only. This close-out changes
only this already-dirty root memory file locally; no further implementation,
tests, commit/push, PR/merge, runtime/database work or app restart is requested.

The completed data work is published as a543cf8d1fac273db41a65a14fb7ae0a05b2d965 on
origin/feat/hus-data-ready-20261031. Source clone:
`D:/SE_Project/backups/hus_data_ready_20261031/source`. No PR was created and no
merge into main occurred. The publication receipt records remote verification;
remote CI after this push has not been verified. Do not describe the feature
branch's old app as integrated into the current VNU/auth/UI runtime.

For the next session, start with
`backups/hus_data_ready_20261031/START_HERE.md` and the published
`data/hus/rag/CURRENT.json`, pointing to releases/hus-data-20261031-v3.
The user's IDE currently has this release's chunks.jsonl open. It contains
1,271 chunks: F1 65, F2 336, F3 870; index the unified file once, not alongside
its family copies or historical releases. The v3 data/reader kit and source ZIPs
remain under backups; GitHub contains the actual v3 files and supporting code.

The user asked whether this is sufficient for RAG. Answered yes for building and
testing descriptive/source-cited HUS Q&A with optional disclosed generated F3.
This is readiness for the next phase, not authorization to implement it during
close-out and not evidence of a production chatbot. Next work is retrieval with
major/program/cohort/version filters, grounding/citations and end-to-end answer
evaluation; no embedding/index/LLM answering path has been deployed yet.
F3 generation requires explicit opt-in; its official syllabus/assessment fields
stay unknown. Keep the 67-course KHMTTT user sign-off, three unsigned catalogs,
unresolved prerequisites/conflicts and 37 out-of-default-F1 historical source
gaps distinct. Never fill official academic facts by generating them.

Verified evidence remains 581 offline passed / 26 deselected without warnings,
40 staged-snapshot release tests, byte-identical v3 and 19-file recovery replay,
1,466 scoped lookups, 24 negatives and five critical cases. No new tests ran at
session close. Root checkout remains on feat/login-redesign-20261031 at 5d60a38;
its existing index.html edit and untracked .vscode/previews are preserved.
Keep this close-out memory local until another publication request.

## HUS data committed and pushed — 2026-10-31

The user explicitly requested commit and GitHub push of the completed HUS data.
Committed 100 scoped files in the isolated data clone as
`a543cf8d1fac273db41a65a14fb7ae0a05b2d965`
(`feat(hus): prepare reviewed portable data release v3`) using the existing
configured author identity. Pushed and verified remote
`feat/hus-data-ready-20261031` at that exact hash:
https://github.com/5-Bit-System/SE_Project/tree/feat/hus-data-ready-20261031.
The original crawldata 312a6e1 is its parent; remote crawldata remains 312a6e1
and main remains 94b7d05. No main push, PR creation or merge occurred.

Publication includes only release v3, its canonical/recovery inputs, source PDFs,
data adapter/build/review tools, tests and documentation. Internal v1/v2 builds
remain untracked locally; ZIPs/backups/configurations stay outside Git. The exact
staged-tree export reproduced v3 and passed all 40 release tests before commit.
Credential-pattern and size checks passed. Code/metadata diff checks passed with
byte-preserved source HTML exempted from whitespace normalization. The prior
581-pass offline result remains valid; no new remote CI success is claimed.

Source clone tracks origin/feat/hus-data-ready-20261031 with no tracked changes;
only its v1/v2 review releases are untracked. Root remains on the existing login
branch with its prior dirty/untracked files; only this local memory is updated.
Runtime/database/credentials were not changed. Publication receipt is in
`backups/hus_data_ready_20261031/PUBLICATION_RESULT.json`. The older data handoff
below records the pre-publication state and is superseded for Git delivery only.

## HUS data prepared and reviewed — 2026-10-31

The user explicitly requested planning, implementation, full data review and
generated supplementation while they sleep, so they can start the next HUS step.
Completed the technical data handoff for descriptive/source-cited and disclosed
generated-reference retrieval. This does not certify all official academic facts.

Start at `backups/hus_data_ready_20261031/START_HERE.md`. Work is in an isolated
Git clone `backups/hus_data_ready_20261031/source`, branch
`feat/hus-data-ready-20261031`, based on crawldata commit
`312a6e16fee4c5deb427fd224c20e8a1092989a5`. Original branch ancestry is preserved;
new changes are uncommitted, unpushed, with no PR or merge requested/performed.
The clone origin now points to GitHub. Do not replace the main app/auth/UI with
this older crawldata app when integrating the data adapter later.

Final prepared pointer is `source/data/hus/rag/CURRENT.json`, pointing to
`hus-data-20261031-v3`, release SHA-256
`27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`.
It has 1,271 chunks: 65 F1, 336 F2 (290 memberships/42 groups/4 programs), and
870 generated F3. Canonical F2 is main 94b7d05, with the existing 67-course KHMTTT
user sign-off retained; other catalogs and unresolved prerequisites stay gated.
There are 174 generated search-alias records, restricted to retrieval metadata.

Recovered 15 public sources through existing robots/allowlist/HTTP-fallback policy,
including all ten selected F1 attachments and two syllabus PDFs. All 24 selected
F1 Markdown prose spans match recovered text under declared normalization. The
15 F1 sources now have originals available. Captures yield 749 text pages; 106
syllabus candidates include 84 exact code/title matches, with identity faults
quarantined from default retrieval. There are still 37 missing historical originals
outside default F1 dependencies. Keep source capture, historical-byte equality,
selected-prose comparison and academic approval distinct. Generated F3 still
does not supply verified official syllabus/assessment weights or current offerings.

Independent review fixed lost raw-only MAT3402 references, retained MAT3325's
conflicting rows, and corrected overly broad security aliases that matched defence/
physical education. LF-normalized metadata pins are explicit; actual capture and
release bytes are protected by gitattributes. Final verification: 581 offline
passed / 26 deselected, no warnings, including 40 new release cases and a real
CRLF-checkout rebuild. Ruff/diff, 1,466 scoped lookup cases, 24 negative cases,
five critical cases, byte-identical release replay and 19-file recovery replay
passed. Portable validation/lookup also passed using the root venv with stdlib
only. These are data checks, not live LLM/vector or official academic acceptance.

Final archives: `HUS_DATA_READY_20261031_v3.zip` and
`HUS_SOURCES_20261031_v3.zip` under that backup directory; checksums are in
`DELIVERY_RECEIPT.json`. Earlier v1/v2 files are internal review artifacts.
Detailed scope/remaining academic unknowns: the clone's
`docs/HUS_DATA_HANDOFF_2026_10_31.md`. Backups are ignored and absent from a fresh
GitHub clone until separately authorized publication. No model API calls, personal
VNU login/record inspection, DB change or app restart occurred. Root remains on
feat/login-redesign-20261031 at 5d60a38; main/origin/main stay 94b7d05. Preexisting
index.html, .vscode and previews work is preserved; this handoff adds memory only
to the root checkout. Runtime has not been switched to the data feature branch.

## Session close - 2026-10-31: PRs 21 and 22 merged; eligibility CI repaired

The user authorized merging the pending work, then explicitly requested fixing
PR #22's CI and merging it into main. PR #21 (redesigned sign-in portal) was
merged with merge commit `626aa03ff4e182d58746b6b3da77e64b85953cdc`:
https://github.com/5-Bit-System/SE_Project/pull/21. PR #22 (verified KHMTTT
eligibility) was subsequently merged with merge commit
`94b7d05988d4118df283ad09a12ff75cef3161fc`:
https://github.com/5-Bit-System/SE_Project/pull/22. Both used GitHub's merge
method, with all six PR checks successful before their respective merges.
Earlier notes saying these PRs were absent or unmerged are historical.

Local `main` and `origin/main` are synchronized at `94b7d05`. The PR #22 merge
has parents `626aa03` and `bf0711c`. Original login commit `d08ff28`, academic
commit `0412d03`, and CI repair commit `bf0711c` were verified as ancestors of
main; original authors and commit history are retained. No direct push to main,
squash, rebase, force push, or branch deletion occurred.

PR #22 initially had three offline failures: two tests still expected all four
catalogs to be drafts, and malformed curriculum identity caused a `KeyError`
because review lookup ran before identity validation. Commit
`bf0711c505e924d891743b74fefbdf90172b36f1`
(`fix(catalog): align signed-off catalog checks and validate identities first`)
moves review lookup after identity validation, updates the source and PDF
acceptance expectations, and adds 12 regression cases for source/identity
binding, complete sign-off, unsigned catalogs and unknown prerequisites.
Only four files changed in this repair: `database/hus_db/catalog_builder.py`,
`tests/catalogs/test_hus_catalog_builder.py`,
`tests/catalogs/test_curriculum_data.py`, and
`tests/database/source/test_four_majors.py`. The workflow was not weakened.
PR #22's placeholder description was replaced with actual scope and checks.

Local verification on the repaired branch: 589 offline tests passed, 90
deselected; 10 PDF-backed acceptance cases passed, 669 deselected, using an
explicit `tests` argument and the `--full-catalog-root` option pointing to
`D:/SE_Project/docs/acceptance/hus_2022`. The prerequisite regression passed all
four cases for each of PYTHONHASHSEED=1 and 2. Ruff, git diff --check, four
synthetic catalog builders and the retained 65-course sample passed. The
existing Starlette/httpx deprecation warning remains. GitHub's push and PR
workflows passed all six offline/postgres/hus_postgres checks on `bf0711c`.
Local PostgreSQL tests, runtime migration/publication, app restart, browser
acceptance and real-account data inspection were not performed in this task.
Account curriculum confirmation remains the user's action from prior handoff.

The clean repair worktree is
`D:/SE_Project/backups/pr22_merge_20261031/source`, on
`feat/academic-eligibility-20261031` at `bf0711c`, synchronized with its remote.
Ignored evidence is in `backups/pr22_merge_20261031/`: `offline.log`,
`offline-fixed.xml`, `merge-result.json`, PR request bodies and `github.ps1`.
The older temporary academic worktree at `0412d03` was preserved.

Root working tree remains on `feat/login-redesign-20261031` at `5d60a38`, one
commit ahead of its remote. Updating the local main ref did not switch this
checkout or apply the four CI repair files to the running root checkout.
Existing dirty `.agent/AGENTS.md` and `app/static/index.html` (notice moved to
section bottoms), plus untracked `.vscode/` and `previews/`, were preserved.
Do not assume the running app was restarted or now runs from main.

Although gh and a connected GitHub plugin were unavailable, GitHub REST access
worked in an approved network execution context using the existing Git
Credential Manager credential in memory. The ignored helper supports that
workflow without printing or persisting credential values. Earlier statements
that a plugin connection was required to finish merging are superseded.

The user now requests session close and memory update only. This close-out
changes this already-dirty memory file locally; do not resume implementation,
tests, runtime/database work or publication without a new request. No commit,
push, PR or merge is requested for this memory addition.

## Session close - 2026-10-31: redesigned login pushed to feature branch

The user approved integrating the redesigned sign-in screen into the main
portal. The standalone preview was refined to fit one viewport, use the main
portal's animated gradient background, support light/dark themes, and enlarge
the left-side copy and top controls. The design is now integrated in
`app/static/index.html`, `app/static/auth.js`, and `app/static/login-scene.css`.
The portal on `http://127.0.0.1:8000` served the updated design successfully.
Visual review at 1536x732 and 1280x720 found no page overflow or JavaScript
errors; student/admin tabs and light/dark switching worked. No credentials
were entered and no automated test suite was run.

Commit `d08ff28ca7e5007f7b57078f7c8ac1da7a42ed0a`
(`feat(login): apply redesigned sign-in portal`) was pushed to
`origin/feat/login-redesign-20261031`. `origin/main` remains at
`c4f1e586a25532eadff8e0bea8da4f2088cd357f`. Repository instructions require
all changes to `main` to go through a feature-branch pull request and a merge
commit, so there was no direct push to `main`. The PR has not been created or
merged: `gh` is unavailable and the GitHub connector is not connected. The
feature branch PR page is
https://github.com/5-Bit-System/SE_Project/pull/new/feat/login-redesign-20261031.

Existing local changes were preserved and excluded from the feature commit:
this memory file was already modified, while `.vscode/` and `previews/` are
untracked. The standalone preview is at `previews/login-redesign/index.html`.
This close-out only updates memory and remains local/uncommitted. No further
implementation or publication was requested.

## Session close - 2026-10-31: login intro copy finalized

The user selected the Vietnamese login intro: “Bảng điểm và thông tin học tập
của bạn, gọn trong một không gian.” Restored it below the left-side headline in
`app/static/index.html`; `app/static/auth.js` supplies the selected Vietnamese
copy and its English equivalent, “Your transcript and study information,
together in one place.”

The change was committed on `feat/login-intro-copy-20261031` as `19eda3c`
(`style(login): restore intro description copy`) and merged through PR #20:
https://github.com/5-Bit-System/SE_Project/pull/20. All six CI checks passed.
Merge commit is `c4f1e586a25532eadff8e0bea8da4f2088cd357f`; local `main` and
`origin/main` are synchronized there. `git diff --check` passed before commit;
no local test suite was run. The existing untracked `.vscode/` directory was
left untouched.

This close-out changes only this memory file and remains local/uncommitted. No
further implementation, tests, runtime/database work, or publication requested.

## GitHub main integrated into local system — 2026-10-29

User explicitly requested checking teammates' GitHub PRs on main and merging
that work into this local system. GitHub main was fetched at
`7bde36e482af3c16e5b31761ee7575f5d6e2ba1b`. Newly merged PRs by 23172c43:
#9 recovers missing migration history and fixes sidebar scrolling; #10
standardizes local setup; #11 adds persistent account-owned semester plans,
session drafts and session restoration. Crawler PR #6 remains open and was not
integrated; retirement PR #8 is closed without merge. No GitHub write occurred.

Root workspace is now on `integration/sync-main-20261029` at local merge commit
`5d7a4df27d855ca4606c75932dd39bcff176062e`, with parents original local
`65d981f` and GitHub main `7bde36e`. Both original histories/authors are retained.
Original branch and local main refs are preserved. Existing retired crawl
Markdown/catalog stay retired. No new commit includes the preceding dirty work.
Do not push this integration branch or merge a GitHub PR without a new request.

All 18 preceding dirty/untracked files were separately backed up and restored
through a tested overlay; README and memory keep both local and main updates.
Existing VNU network fixes, cleanup changes, RAG handoff and .vscode are retained.
Three test compatibility fixes remain uncommitted: Windows-safe screenshot path,
explicit UTF-8 catalog reading in the new plan PG fixture, and the exact new
GET /me/semester-plans fixture in the existing session browser regression.
The original stash is deliberately retained as an additional backup only;
do not pop it onto the already restored files.

Verification: 555 offline tests passed with explicit HUS PDF root; all 80
PostgreSQL cases ultimately passed on a separate disposable container, with no
skips. The first PG run passed 66; 14 cases needed a prepared test-only catalog
or the UTF-8 fixture fix and then passed on rerun. Seven synthetic Chrome scripts
passed: semester plans, session restoration, course board, portal session/auth,
resume and profile source. Ruff, all static JS syntax, analytics assertions,
four synthetic builders and the 65-course sample passed. Existing Starlette/httpx
warning remains. These tests do not establish real-account academic acceptance.

Docker Desktop was initially stopped; starting it resumed existing se_hus_db
with its original volume. Runtime ai07 was backed up, restored in isolation and
migrated there first. Runtime then upgraded transactionally from
hus_20261025_06 to hus_20261028_08: all 24 original table count/content
fingerprints, projecting original columns, matched before/after; semester_plans
starts empty. No seed, catalog publication, source/grade edit, password or SMTP
change. .env, .env.auth, database/.env.docker and .vscode hashes are unchanged.
The exact disposable test container has been removed; se_hus_db remains running.

No app process was initially running. Public VNU form check passed in normal
approved execution context without credentials. App now runs from D through
tools.run_local at http://127.0.0.1:8000, launcher PID 14264; verify process
identity before any later stop. /health and /ready are OK with PostgreSQL, all
15 served assets match disk, and anonymous profile/admin/semester-plan routes
reject with 401. No real VNU login, personal transcript inspection or email.

Evidence is ignored under `backups/sync_main_20261029/`: RESULT.md,
verification.json, baseline.json, originals/, before_runtime.dump,
runtime_before.json, backup_restore_verified.json, runtime_after.json,
offline.xml, postgres.xml and postgres-rerun.xml, plus runtime logs. The
459-file/20-overlay integrity receipt predates this memory-only addition.
Catalogs remain draft_unverified; RAG is inactive. Earlier stop/no-merge notes
are historical scope restrictions superseded only by this explicit local merge.

## Session close — 2026-10-29: systematic cleanup completed locally

User explicitly requests closing the session and updating memory. This close-out
changes only this memory file; do not resume implementation, cleanup, tests,
runtime/database work or publication. No commit, push, PR or merge requested.

Actual root HEAD is `65d981f` (`chore: retire old HUS crawl markdown`) on
`chore/remove-old-crawl-markdown-20261026`; that commit predates this cleanup.
Its remote-tracking branch is marked gone. Older entries recording root HEAD
`7650c12` or 107 pending crawl deletions are historical; the retirement is already
in this local HEAD. Do not recreate those files or infer remote publication.

The user requested project-toolkit and a five-stage project audit/cleanup.
Completed the safely verifiable scope: inventory, classification, small cleanup,
verification and a report at
[`docs/BAO_CAO_DON_DEP_2026_10_29.md`](../docs/BAO_CAO_DON_DEP_2026_10_29.md).
Removed 360 untracked generated cache files: 353 Python bytecode files, two
pytest cache files and five Ruff cache files, totaling 5,403,157 bytes (~5.15 MiB).
This is gross removed payload, not net free-space gain; the audit evidence also
uses disk. Cache README and two cache .gitignore files were retained. No tracked
source file, dependency, PDF, SQL, academic source or configuration was deleted.

Only two source files were changed by cleanup: removed the unused `require_admin`
helper from `app/auth/dependencies.py`, and combined identical KeywordRanker/
LLMRanker call branches in `app/services/recommendation_service.py`. Existing
admin route/repository guards, custom-ranker behavior and fallback remain.
Diff: one insertion, 15 deletions (14 fewer lines). Changes remain uncommitted.

Before/after offline pytest both passed: 537 passed, 76 PostgreSQL cases
deselected, no skipped cases, using explicit HUS PDF acceptance root. Whole-root
Ruff, Python syntax for 168 files, Node syntax for 11 JS/MJS files, local import
module/resource checks, all 15 HTML assets, four synthetic catalog builders,
the 65-course metadata sample, analytics assertions and pip check passed. Three
synthetic Chrome scripts passed: portal auth, resume and profile-source capture.
One existing Starlette/httpx deprecation warning remains. No PostgreSQL tests,
real VNU login/grade inspection, email delivery, app restart or Docker action.

At cleanup completion, hash checks covered 3,406 unique protected files; only
the two intended source changes differed. Pre-existing dirty files/untracked
work and both nested checkout Git statuses were preserved. That integrity
snapshot predates this explicitly requested memory addition. Keep the existing
VNU network edits, README, RAG handoff, untracked local launcher/startup test and
.vscode work; do not overwrite, bundle into a commit or reset them implicitly.

Full local evidence is ignored under `backups/cleanup_20261029/`: start with
`deleted-files.csv`, `verification.json`, `baseline-offline.xml` and
`final-offline.xml`. Inventory/import/definition and duplicate-candidate files
are audit data, not deletion instructions. `originals/app/` holds the exact
pre-cleanup copies of the two edited source files. No credentials were printed.

Keep unresolved candidates: dormant app.js/dashboard.js and their styles,
legacy CDP language test, retired email helpers/SMTP configuration and associated
test setup, demo-profile validation, old RAG preparation reference code, all HUS
delivery/source/PDF/OCR/manifest evidence, and the two unpublished feature
checkouts. 815 baseline duplicate-hash groups were retained because equal bytes
do not prove equal lifecycle/provenance. Further retirement needs its own scope;
do not delete these merely because the active UI does not load them. RAG remains
inactive and catalogs remain draft_unverified; cleanup does not change acceptance.

## Local VNU launch — 2026-10-28

VNU login 502 was reproduced as Chrome `net::ERR_NETWORK_ACCESS_DENIED` when the
app inherited the agent's restricted execution session. The identical public
login-form probe returned HTTP 200 outside that session. Restarting the verified
D-workspace app in an approved normal execution context restored login; the user
explicitly confirmed success. A worker restart inside the blocked parent context
does not remove the restriction. Do not retry credentials automatically.

Before future VNU app launches, use `.venv/Scripts/python.exe -m tools.run_local`
from the repository root in a context with network access. `--check-only` probes
the public form without credentials or another server. An agent must request the
appropriate approved execution context when its sandbox blocks networking.
`/health` and `/ready` do not prove VNU access. Keep the existing host/port
`127.0.0.1:8000`, local configuration, volumes and account data.

The local preventive change classifies this failure as `network_access_denied`
(503) with safe UI text and a startup check. Verification: 224 offline integration
tests passed, 41 database cases deselected; three synthetic Chrome scripts passed.
The startup check rejects the restricted context and succeeds outside it. No
agent real-account login or personal transcript inspection was performed.

Feature source is uncommitted on `fix/vnu-login-network-20261028` in
`backups/vnu_login_network_20261028/source`, based on main `7650c12`; the verified
changes are also applied locally to the root runtime checkout. No commit, push,
PR or merge. Existing RAG handoff edits and `.vscode/` are preserved. The restored
running app was not restarted again after user acceptance; the added API/runtime
diagnostics load at its next planned restart. Evidence and caveats are in
`backups/vnu_login_network_20261028/RESULT.md`.

## Semester plans — 2026-10-28, local implementation

User explicitly requests durable multiple semester plan alternatives. Branch
feat/semester-plans adds account-owned CRUD and migration hus_20261028_08.
This supersedes older scope exclusions about persistent semester plans only.
Source readiness, program binding, deterministic eligibility and session/CSRF
remain required. No real DB migration, portal login, seed/publication or push
was authorized for the initial implementation turn. User authorized 15 commits,
push of feat/semester-plans and a PR into main on 2026-10-29; merge is not
authorized in this publication turn. See docs/SEMESTER_PLANS.md.
Local checks in Conda SE_Project: 531 offline passed / 89 deselected; 23
PostgreSQL migration/plan checks passed on disposable localhost:55439; synthetic
Chrome plan lifecycle/mobile/VI-EN/logout passed. Existing Starlette/httpx warning.
Follow-up user request keeps draft choices/filter/plan selection across F5 in
sessionStorage keyed by verified account and app-session IDs (not token). Only
draft metadata and course codes are stored, never transcript/grades/cookies.
Startup/F5 now renders a session-restoration loader until /auth/session resolves,
avoiding the login-form flash. Delayed valid/expired/error Chrome checks pass.
Repeated same-source portal events no longer reset the board; source changes
revalidate while preserving the draft. Logout/expiry/session change clears it.
No real VNU acceptance or production migration is implied. Plans are keyed by
account UUID, not transient portal cookies, and never become completed courses.

## Session update — 2026-10-27: project relocated to D; connections verified

The canonical workspace is now `D:/SE_Project`. The user copied the project,
recreated the main `.venv` there, and deleted the old `E:/SE_Project`; the final
PowerShell `Test-Path` returned false and the relocation audit reconfirmed it.
Use D for all future commands, editor folders, runtime and local maintenance.
Earlier E paths in dated session entries, archived logs and immutable source
receipts describe historical execution, not a current dependency. Do not recreate
the deleted E workspace or mass-edit byte-bound source/audit evidence.

The user explicitly authorized this memory update, repair of remaining project
path references and connection/regression checks. This authorizes relocation
maintenance, without resuming the unrelated pending RAG/source work below.
Root branch remains `chore/remove-old-crawl-markdown-20261026` at
`7650c123c67082f476af8f4f8c83cf72c0ce9708`; no commit, push, PR or merge occurred.
The existing 107 tracked crawl deletions, data README/manifest changes and
untracked `.vscode/` / `docs/rag_normalization/` were preserved. The RAG handoff's
two local paths were updated; `.vscode/settings.json` itself remains unchanged.

The new main venv now contains Playwright 1.64.1 and uses installed Google Chrome.
The earlier VNU 503 `browser_start/browser_unavailable/missing_dependency` was
caused by omitting `requirements-portal.txt` when rebuilding the venv, not a
removed VNU container. README setup now installs both dev and portal requirements
with the pinned core constraints and explains the Chrome requirement. VNU uses
a Python/Chrome worker; it has no separate Docker container.

Repaired local selection JSON/CSV/Markdown locators, current HUS run/handoff
paths and helper scripts. Helpers now derive their paths where practical.
The copied parser venv at `backups/crawldata_audit_20261026_28d61c4/venv` had E in
its activation/configuration and pip launchers; regenerated it at D, preserving
system-site-package access, and reinstalled its existing pip 24.0 from Python's
bundled local wheel. Its Python, pip, bs4 4.15.0 and soupsieve 2.9.1 were checked.
No global Python environment was upgraded.

The separate HUS feature checkout remains at
`backups/hus_pipeline_worktree_20261026`, HEAD `4b52f85accfad41460cf25c48b678bd11d43341a`,
branch `feat/hus-normalize-chunks-20261026`, unpushed/unmerged. Its former origin
pointed at an already-removed E baseline bundle; origin now points to the valid
local `D:/SE_Project` repository. `ls-remote` succeeded and both repositories
passed `git fsck`. Seven tracked files in this feature checkout (six run/handoff
documents plus the handoff generator) now have local relocation edits; the
original commit/authorship is preserved. The root GitHub origin was also checked
read-only successfully, without fetch or push.

Docker container `se_hus_db` was recreated from `database/docker-compose.yml`
on D because its Compose labels still referenced E. Its only mount remains
named volume `se_hus_pgdata`; the PostgreSQL cluster identifier matched before
and after, and the container is healthy. No migration, seed, catalog publication,
credential change or personal-table inspection was performed. The existing app
on port 8000 was verified through its D venv launcher and reused. Root `.env`,
`.env.auth`, `database/.env.docker` and `.vscode/settings.json` hashes are unchanged.
Process/user/machine environment checks and VS Code user settings found no old
SE_Project path. A scan of 156 active project/config/launcher files and filesystem
reparse targets found no current E project dependency.

Validation on D: 523 offline tests passed, 75 PostgreSQL tests deselected, zero
skipped, including the explicit existing HUS PDF expectation suite. One existing
Starlette/httpx deprecation warning remains. Root Ruff, changed-helper Python/JS
syntax, nested generator Ruff, four synthetic catalog fixture checks and Git
diff checks passed. Five existing Chrome regressions passed: portal auth,
collection, profile source, session and loading; their VNU pages/identities are
synthetic and intercepted. They did not overwrite historical screenshot evidence.

Live read-only checks: `/`, `/health`, `/ready`, `/auth/session`, `/programs`, all
15 referenced assets and the academic-policy PDF returned 200; readiness reported
PostgreSQL and four programs. Anonymous `/me/profile` and `/admin/users` correctly
returned 401. Chrome launched with no local-page JS errors and loaded the public
VNU login form with HTTP 200. SMTP EHLO/STARTTLS succeeded without authentication
or sending mail. LLM remains disabled and no paid provider request was made.
Real-account VNU login/grades and SMTP credentials/delivery were not tested;
these checks do not certify every product behavior or external-service uptime.

The offline HUS completion verifier passed at D with 1,381 records / 1,520 chunks.
Dataset manifest SHA-256 remains
`3dbdd56d0b8c7357bcd0711ec197716868c3f9ffa231b4847eb91af7482cbfae`.
All 106 local selection locators were relocated; the same known historical
`23a0c1df14a5708a` Markdown remains absent, not a new relocation failure. Raw
sources, derived dataset hashes, approval states and academic unknowns remain
unchanged. This verification does not approve or publish the HUS corpus.

Current evidence and rollback copies are ignored under
`backups/relocation_20261027/`: start with `REPORT.md`, `connections.json`,
`integrity.json`, `browser_checks.json`, `offline.xml`, Docker before/after
metadata, `baseline.json` and `originals/`. Originals contain historical paths
for rollback only; do not treat them as runnable current configuration.

## Session close — 2026-10-27: HUS completion and backup cleanup

The user closes this turn with a memory update only. Do not resume source work,
run tests, alter application/runtime/database state, create another commit, push
or merge as part of this close-out. The root project remains on
`chore/remove-old-crawl-markdown-20261026` at `7650c123c67082f476af8f4f8c83cf72c0ce9708`.
Preserve its pre-existing dirty crawl-corpus deletions, README/manifest and RAG
handoff work, and unexamined `.vscode/`; this session changed only this memory
file and ignored backup cleanup documentation/artifacts.

The HUS data-completion implementation is isolated at
`backups/hus_pipeline_worktree_20261026`, branch
`feat/hus-normalize-chunks-20261026`, local commit
`4b52f85accfad41460cf25c48b678bd11d43341a`, based on `5d0dacc`. It was clean at
close and remains unpushed/unmerged. Its outputs are ignored local files under
`backups/hus_completion_20261026/`; a fresh Git clone will not contain them.
Start with `START_HERE.md`, `CHATGPT_HANDOFF.md` and `DELIVERY_RECEIPT.json` there;
reproduction steps live in the feature checkout's
`docs/hus_pipeline/COMPLETION_RUN_V2.md`.

Final dataset manifest SHA-256 is
`3dbdd56d0b8c7357bcd0711ec197716868c3f9ffa231b4847eb91af7482cbfae`.
Results: 20 AI-verified capture metadata fields, 12 issuance facts, 297 visually
checked course occurrences across 22 table pages, 1,381 records and 1,520 chunks.
There are 30 offline descriptive AI-ready chunks, 383 source-checked PDF chunks
outside formal whole-document include, and 1,107 quarantined chunks. No human or
university approval, individual academic applicability, embedding, active release
or runtime/database change is asserted. Final offline suite evidence is 716
passed, zero skipped, 75 PostgreSQL tests deselected; the last full run predates
this cleanup. Independent component/aggregate replays matched 40/98/15 files.
No tests were run for backup cleanup or this memory update.

Five matching original attachments remain missing. The network probe for
`8afffd3cada3d048` failed with WinError 10013; four other URLs were not attempted.
The missing-file list is `backups/hus_completion_20261026/MISSING_SOURCE_REQUESTS.csv`.
Dedicated F3 sources for Mathematics and Data Science remain unavailable. Keep
current validity, remote equality, unresolved printed credit/code conflicts and
individual applicability unknown; preserve the absent historical ID
`23a0c1df14a5708a`. Do not represent the remaining data as full academic or
source acceptance.

On 2026-10-27 the user explicitly asked to remove unnecessary backup files. The
cleanup removed 3,299 files (~642 MiB): two clean nested VNU Git clones whose
commits are already in root history, generated test/cache folders, a byte-
identical completion replay, superseded aggregate builds and old review boards,
plus the stale `5d0dacc` bundle. Before removing the clones, 87 distinct UI
screenshots were moved to
`backups/vnu_eligibility_integration_20261026/visual_evidence_from_clone/` and
`backups/vnu_curriculum_review_20261026/visual_evidence_from_clone/`. The final
HUS completion output, pinned source audit, PDF/OCR assets, baseline, runtime
rollback dumps and unpushed feature checkout were kept. `backups/README.md` has
the inventory. At close, backups occupied about 0.75 GiB, E: had about 0.81 GiB
free, and the only nested Git repository in backups was the active HUS feature
checkout.

The old preservation JSON mishandled five Git-quoted Unicode PDF paths as null.
Close-out verified 547 recorded paths, and separately verified those five PDFs
match root Git `HEAD`; this is not a recovered pre-task hash for those five.
`backups/hus_pipeline_DELIVERY_20261026.json` is historical and refers to an old
ZIP that is no longer present; use the current delivery receipt instead.

## Session close — 2026-10-26: one-file normalization preview pending

User explicitly closes the session and requests a memory update. Stop the
normalization attempt here; this close performs only memory/document-state
recording. No commit/push/PR, application/runtime/DB changes or new source review.

Completed: data audit and F1/F2/F3 selection proposal; general-folder review;
portable handoff at `docs/rag_normalization/HANDOFF_2026_10_26.md` with
`source_selection.csv`, `inventory_snapshot.json`, `example_course_record.json`;
updated package `backups/rag_normalization_handoff_20261026.zip`. Section 1.1
and W2/W3 explicitly require reusing the crawldata metadata models/validators and
basic normalization. The MAT2502 JSON is an illustrative record with unverified
proposals, not a normalized copy of the full source document or an approved source.

The user's final work request before closing was to normalize ONE actual file
and show before/after. Target selected from their IDE context:
`backups/crawldata_audit_20261026_28d61c4/source/data/hus/processed/documents/`
`computer_science/tai-lieu-dinh-kem-4-kctdt-clc-mtkhtt-10082020-0-pdf--8afffd3c.md`
(document ID `8afffd3cada3d048`). Only read-only inspection was done. No preview
script, before/after files, demo directory or full normalized document was created.
If the user resumes, continue by producing a concrete, separate comparison for
that one file; do not claim the earlier MAT2502 example fulfills this request.

Inspection findings for that future preview: the current Markdown has 661 lines,
25 page markers and 19 table blocks. The main curriculum spans 7 table fragments,
with numbered course rows 1–66 and continuation cells across page markers 13,
14 and 16. Preserve fragments and provenance; joining them is an unverified
derived proposal until checked against raw. Do not indiscriminately remove
standalone numbers: `2015` in the final comparison section is a meaningful year.
Beyond the known 78-vs-81 credit discrepancy, the summary/table states 148 total
credits while section 5.3 states 154. Record conflicts rather than silently
repairing values. Original PDF remains missing. Source text/body matches catalog
after stripping only the outer frontmatter/newline wrapper.

Workset remains 12 proposed sources (7 core + 5 supplemental), with no formal
include/chunks. Unknown metadata stays unknown; normalization may create
candidates without assigning verified values or replacing runtime eligibility.
Current branch remains `chore/remove-old-crawl-markdown-20261026`; preserve the
prior old-crawl deletions, README/manifest/memory edits, untracked
`docs/rag_normalization/` and the now-present untracked `.vscode/` directory.
The latter was not created, inspected or modified by this task.

## RAG normalization handoff — 2026-10-26

Metadata clarification: remote crawldata was rechecked and still points to
28d61c4. It already implements MetadataField/ApplicabilityMetadata, proposal and
evidence validation, a 106-document applicability.json, basic text normalization
and corpus build/verify. Complete and verify existing metadata rather than
recreate those models. All nine applicability fields currently have zero
non-unknown verified values; program/variant/cohort/year/validity/effective-date
proposals are also all unknown. Handoff section 1.1 and W2/W3 now make reuse
explicit. The example's nested applicability uses the existing model and
high_quality vocabulary; its additional proposals are illustrative and do not
change source metadata. The portable inventory and handoff ZIP are refreshed.

User asks to consolidate the data state and normalization plan for assigning
work to a teammate. Prepared the shareable, local-only handoff at
`docs/rag_normalization/HANDOFF_2026_10_26.md`, with portable
`source_selection.csv` (106 records), `inventory_snapshot.json` and a real
Markdown-derived MAT2502 `example_course_record.json`. This is documentation
and an example, not implementation of the normalizer or a corpus approval.

Current selection: 7 core + 5 supplemental (3 CLC, 2 general F1) + 6 deferred OCR
+ 3 historical + 85 outside v1 = 106. Workset: 12 documents, 7 with raw HTML and
5 attachments without raw. All selected approved_for_rag flags remain false.
Source review baseline remains 100 needs_review / 6 pending_ocr / 0 include,
0 chunks and inactive. User reading Markdown does not create fabricated
reviewer, timestamp, raw-quality or effective-scope evidence.

Pinned audit tree: 28d61c4bc13ff32592c48ef890a087166494cc59; internal source
manifest still references hus-0404f37-20261026. Local audit has 105 Markdown
against 106 catalog records: the unselected historical 23a0c1df file is missing.
All 161 present manifest files match; do not implicitly restore that local file.
Other machines should obtain a complete isolated source at the pinned commit.
Backups are ignored and are not included in a fresh clone.

Normalization plan preserves sources, creates derived records and source maps,
records proposed/verified metadata and same-scope version decisions, recovers
raw/OCR sources, and leaves unresolved scope/logic unknown. Pipeline 1.4 currently
reviews whole documents; section records cannot bypass require_review or mark
an entire source include after checking only selected paragraphs. Embedding,
runtime publication, DB/catalog/eligibility changes are later work. No normalizer,
full corpus, commit/push/PR or app changes were requested in this handoff turn.

## HUS RAG source-version preference — 2026-10-26

The user selected F1 major overview, F2 curriculum frameworks and F3 course
descriptions for the first RAG source review. They now require the newest
published document when several versions cover the same scope, especially
curriculum frameworks because recommendations depend on them. Compare within
major, degree, program/track and document kind using the issuance evidence in
the source, not filenames or crawl/fetched timestamps. Keep older versions for
historical questions and older cohorts where still applicable. For a student's
course recommendations, the framework must additionally apply to that student's
cohort/program; a newer framework
for another cohort is not automatically applicable. If version/effective scope
is unknown, do not replace the existing verified catalog or eligibility rules
with crawl text.

Updated the ignored selection proposal at
`backups/rag_selection_f1_f2_f3_20261026/SELECTION.md` and its JSON policy.
Current examples: KHMTTT 2024 course descriptions may supersede overlapping
2023 descriptions only after same-scope verification; the 2023 Word framework
has a blank issuance line. Two CLC PDFs both show decision 3340 dated 2019;
`2020` in the filename does not establish a newer version. The 2015 frameworks
remain historical where newer sources are identified but not yet recovered or
OCR-verified. This is a selection rule, not approval of any source or a runtime
recommendation change. No commit/push/PR, database migration or publication.

## Old crawl Markdown removed — 2026-10-26

User explicitly requests deleting all old crawled Markdown data and will supply
replacement data later. This supersedes earlier immutable-snapshot and preserve
instructions for those files, including the preexisting whitespace-only edit to
the document ending `exh01-02-06...0a180289.md`.

On local branch `chore/remove-old-crawl-markdown-20261026`, removed all 106 `.md`
files (2,904,117 bytes) under
`data/hus/releases/2026-10-22-3a45aae-candidate/processed/documents/`.
All were tracked in Git. No commit/push/PR is requested. Preserve the preexisting
memory changes from `docs/session-close-20261026` carried into this branch.

Automatic approval review rejected the initial combined deletion because it
also removed `processed/catalog.json`, outside the explicitly requested `.md`
scope. That rejected command made no deletions. The narrower Markdown-only
deletion succeeded. The user then explicitly answered "Xóa luôn catalog.json
của bộ crawl cũ". Removed that exact catalog (3,232,362 bytes) after checking
its path and SHA-256 against the manifest. The prior review block is resolved;
no deletion approval remains pending. Total removal: 107 files / 6,136,479 bytes.

The 101 raw HTML files remain. SHA-256 checks verified 260 retained snapshot,
sample catalog, original PDF, database source, application and config files
unchanged through Markdown deletion; 259 retained files were checked unchanged
through the subsequent JSON deletion. Updated snapshot README/manifest and data README
record retirement; earlier crawl/chunk statistics are historical. No runtime/DB
change, crawler, preprocessing, index build or restart. New corpus work waits
for the user's replacement data.

## Session close — 2026-10-26: eligibility delivered; owner acceptance pending

User requests session close and memory update only. No new implementation,
commit/push/PR, database write or restart is authorized by this close-out.
Memory edits stay local on docs/session-close-20261026, based on main 7650c12,
to follow the permanent feature-branch/PR rule. Preserve the preexisting corpus
whitespace edit ending exh01-02-06...0a180289.md; do not publish it with memory.

Eligibility delivery is complete through PR #7:
https://github.com/5-Bit-System/SE_Project/pull/7.
Merged using Create a merge commit as 7650c123c67082f476af8f4f8c83cf72c0ce9708.
The genuine integration merge f9e7a0c has parents e781ab3 and teammate 5e1a9bf;
deb3fb0 adds original-owner checks after I/O. Teammate 5e1a9bf keeps author
huyvinh005 and is an ancestor of main and present in PR #7. A duplicate PR from
the old source branch is unnecessary; its existing contribution already has
the PR record and original history. No invented authorship or copied-only credit.

Final verification recorded below remains: 523 offline, 75 PostgreSQL, 35
targeted auth/binding/VNU rerun, 15 fixture Chrome scripts and one real-HTTP/
disposable-PG Chrome flow. PR checks 6/6 and post-merge main checks 3/3 passed.
No tests rerun for branch cleanup or this documentation-only close-out.

Runtime is served from E:/SE_Project at http://127.0.0.1:8000/#rules. Latest
read-only close-out /ready returns status=ok, storage=postgres. Last recorded
launcher PID 23348; verify command lines before any future stop. Health, 15
versioned assets, policy PDF and anonymous personal-route rejection were checked
after deployment. Logs/evidence: backups/vnu_eligibility_integration_20261026/.
RESULT.md there records exact commits, tests, integrity and rollout details.

The runtime backup was restored in isolation; 19 protected table fingerprints
matched before/after rollout. No runtime migration/seed/catalog publication,
password/SMTP changes, manual completeness upgrade or actual grades inspection.
Existing config and corpus hashes were unchanged. Subsequent owner-initiated
confirmation/synchronization may legitimately write binding/snapshots; do not
assume deployment-time fingerprints describe all later user activity.

User authorized deleting completed temporary branches. Removed ONLY
integration/vnu-eligibility-20261026 remotely and from the integration clone,
after full-ancestry verification; that clone is now on main 7650c12. Kept
feat/vnu-curriculum-planning and teammates' other branches. Removed temporary
PostgreSQL test container after verification. se_auth_mail and se_recommender_db
containers were also removed earlier by request; both DB volumes remain.

Latest owner screenshot shows selected program/cohort and consent checked, but
the confirmation form remains and all three columns state that program
confirmation is required. User asked for an answer only: explained that ticking
consent alone does not persist confirmation; press the confirmation/compare
button. If already pressed, the screenshot alone does not identify why the
request did not complete. No authenticated API, DB, logs or personal source was
inspected to diagnose that screenshot, and no fix was made. Do not assert that
the user never clicked, declare a confirmed bug, or mark real-account academic
acceptance complete. If asked to investigate later, check the confirmation
request/result and remaining readiness gates; do not reset seed, transfer owners,
rewrite source records or force verification flags to populate the columns.

## VNU eligibility integration — 2026-10-26

User authorizes implementation, tests and integration of the teammate's
eligibility flow while retaining all existing modules, with frequent progress.
Integration branch integration/vnu-eligibility-20261026 starts at main e781ab3
and uses a genuine merge of teammate commit 5e1a9bf, preserving its authorship.
Do not replace main with the old teammate checkout. Main delivery uses a PR
and Create a merge commit, with actual publication/CI/merge state in Git/PR.

Scope: personal course board, per-owner program/cohort confirmation, versioned
grade policy, source-completeness collector and 20-credit adjustable plan.
Keep current student/admin auth, study_app_session, CSRF/origin, one-to-one
ownership, DB session checks, RAM VNU cookies/resume/reauth and seven-day reminder.
No public curriculum reference/CSV/talented catalog, RAG, what-if or persistent
semester-plan expansion. Auth.js/workspace/analytics/recommendation_service and
migration files remain identical to the main base.

Binding uses existing portal_users.profile JSONB with binding_schema_version=1.
Account/session/link checks and owner generation/digest/scope lock share one
transaction, with a safe audit event. Refresh preserves binding and last_synced_at;
changed enrollment invalidates binding, confirmation does not advance sync time.
No schema migration, seed, catalog publication, password/SMTP change or manual
upgrade of old completeness. Unknown source and uncertain outcomes remain gated.

Independent integration checks: 523 offline passed / 75 deselected including HUS
PDF acceptance; 75 PostgreSQL passed on disposable container port 55433 including
legacy, HUS/auth and four new binding transaction tests. Ruff, both catalog builder
checks, all JS syntax and diff checks pass. Fifteen synthetic Chrome regressions
pass; real HTTP + disposable-PG Chrome proves sign-in, program confirmation,
track/path selection and board plus existing admin/session/sync/logout checks.
Screenshots desktop/mobile inspected. Existing Starlette/httpx warning remains.
No agent real-VNU login or personal grades inspection; real-account acceptance
must be performed by the owner after deployment. Catalogs remain draft_unverified.

Final ownership audit adds checks of the original source owner after I/O, including
when an account's link changes while program metadata is being read. Two new
regressions pass; binding/system-auth/VNU PostgreSQL group rerun: 35 passed.

Runtime backup at ignored backups/vnu_eligibility_integration_20261026/
before_runtime.dump restored successfully to isolated ai07_backup_verify_20261026.
Ignored test reports/screenshots/clone remain under the same integration directory.
Do not reset seed or restore the full DB to resolve a UI/source-gating issue.
Deployment restart loses VNU RAM cookies; app sessions retain their normal DB
lifecycle and the next update may require one reauth. See docs/COURSE_STATUS_BOARD.md
and docs/VNU_PERSONAL_ACADEMIC_2026_10_25.md for scope/limits.

The preexisting candidate corpus whitespace edit remains outside this work.
Previous temporary Docker cleanup removed se_auth_mail/se_recommender_db containers
only; both database volumes remain. Keep test infrastructure separate from se_hus.

## Session close/publication authorized — 2026-10-25

User explicitly requests closing memory update, commits for the accumulated work
and push to GitHub. This supersedes preceding no-commit/push notes for the VNU
session/reminder/auth/UI/docs and cleanup change set. Publish on the existing
feature branch feat/system-auth-email-20261025, based on fetched main 586d659;
HEAD/main/origin/main were equal before publication. Plan two genuine commits:
integrated VNU/student/admin feature with tests, then docs/workflow/cleanup/memory.
Feature commit created as 211cd0d (73 files); docs close-out follows separately.
Preserve the existing configured author identity; no history rewriting or main
push. Open a draft PR for review; merge remains a separate action using a merge
commit after CI and authorization. Do not start new implementation at close-out.

One preexisting whitespace-only edit to the immutable candidate corpus document
ending exh01-02-06...0a180289.md is outside this feature publication. Keep it local
unchanged; do not normalize/publish source bytes as part of auth or cleanup.
Ignored .env/.env.auth/backups/private handoffs/toolkit/.venv stay outside commits.
Local admin username is admin; chosen password remains only a local DB credential,
never in tracked memory/source. Gmail SMTP and local account data remain untouched.

Latest verification remains 440 offline passed / 71 deselected (HUS PDF acceptance),
Ruff/diff checks, Chrome VNU/admin and UI/session regressions, HUS PostgreSQL 54
full-group passes followed by 31 auth/VNU passes after final ownership guard.
Cleanup changes only ignored artifacts plus documentation; no extra test rerun
or backend change is implied by committing. Live health/ready and 13 local assets
were OK. Source completeness/policy binding, real new-login acceptance, official
SSO, RAG and production rollout remain unverified/deferred as described below.

Use Git/PR records for resulting commit hashes, remote delivery and CI state;
this entry records authorization and pre-publication evidence, not a claim that
an unverified push/PR or CI already succeeded. Finish with publication handoff.

## Workspace/backups cleanup completed — 2026-10-25

User requests review of unnecessary files throughout the project, particularly
backups. Audited sizes, Git status and code/test/doc references; cleanup removes
generated/redundant local files, not academic sources or uncommitted application
work. Deleted 5,869 files / 1,049,153,955 bytes (~1001 MiB); backups reduced from
~1008 MiB to ~10 MiB (about 99%). Historical artifact paths below may now be gone.

Removed inactive semester Chrome profiles/cache, obsolete separate trial browser
dependencies, old Git-reproducible auth-review checkout/archive (495 files matched
586d659 with CRLF normalization), superseded screenshots/logs/synthetic fixtures,
exact duplicate crawl files/archive and Python/pytest/Ruff caches. Preserved all
9 database dumps, legacy rollback environment, original 5 PDFs, audit/OCR/CSV/JUnit
evidence, distinct crawl/config variants, .env/.env.auth, .venv, toolkit, Git and
all preceding dirty code/source changes. Original handoff accounts.private.txt
remains historical and is not current admin credentials; never reset seed.

Kept latest VNU/admin screenshots under system_auth_20261025/browser_4e62b1e236/
and active vnu_signin_20261025/runtime.* logs. One old synthetic credential (248
bytes) in browser_f8654fdd83 and other tiny ACL-protected test credentials retained
without altering ACL. Removal of that folder partially failed due to its ACL;
remaining old screenshots were separately removed. No auto-review rejection.
Precise ignored inventory/results: backups/cleanup_20261025/. Backup index:
backups/README.md. Git-visible report: docs/BAO_CAO_DON_DEP_2026_10_25.md.

Validation: hash comparison confirmed 530 protected project/config files unchanged
before this report/memory update. 440 offline passed / 71 deselected with HUS PDF
acceptance, bytecode/pytest caching disabled; Ruff --no-cache and diff check passed.
Live health/ready/anonymous session and all 13 HTML-linked local assets returned
200. Existing Starlette/httpx warning remains. No new PG tests needed: no runtime
code/schema/DB changes. No server restart, source publication, real VNU request,
grade inspection, password/SMTP changes, commit or push. Disk savings are local
workspace hygiene, not an API performance or full code-audit claim.

## Admin credentials changed by explicit user request — 2026-10-25

User explicitly requested local administrator username `admin` and a chosen
replacement password. Applied only to the existing verified active admin account
previously identified by admin@sohoctap.test: username/hash changed, initial-change
flag cleared for the user-chosen password, auth_version incremented and old admin
sessions revoked, maintenance audit recorded. Account UUID, email, role, seed flag,
other users and source data retained. No students FK referenced the old username.
Do not record the password in memory, tracked files or logs, and do not rerun seed.

Checked fresh ignored backup under backups/vnu_signin_20261025/admin_change_*/.
Live /auth/login using username admin and /admin/users permission check succeeded;
verification session logged out. Original accounts.private.txt remains a historical
temporary-password handoff and does not contain the current credentials. User can
now choose Quản trị viên and sign in as admin. No runtime restart, code change,
SMTP change, commit or push was needed.

## VNU student sign-in replaces personal email login — 2026-10-25

User explicitly authorizes the proposed implementation and frequent progress:
students sign in directly with VNU; administrators retain local account/password.
This supersedes the earlier separate-email student flow below. Work stays on
feat/system-auth-email-20261025 with all preceding unpublished changes retained;
no commit/push/PR requested or performed. This is the existing student-portal
connector, NOT official OAuth/SSO. Official integration/access to grades is unproven.

New POST /auth/vnu uses fresh accepted VNU login evidence, creates/reuses one
student account and a DB app session, saves source when accepted and installs
per-session RAM cookies. No personal-email registration or separate app password.
POST /auth/login accepts admin username/email only; public register/resend/verify
return 410 use_vnu_login. Admin password rotation and role/status guards remain.
VNU-only students cannot change local passwords or become admins without separate
eligible admin credentials. Admin list/search includes VNU-only student accounts.

Additive hus_20261025_06 adds accounts.vnu_subject and sessions.auth_method.
Backfills only existing student-owned VNU links, preserving account IDs and all
original account fields; old student sessions revoked. Unlinked email accounts
remain stored, never auto-associated by email/name. Stable VNU identity survives
source deletion and prevents another account from claiming the deleted source.
Concurrent first logins serialize; admin-owned links cannot become student logins.
Fresh student-portal auth/menu is the current admission boundary, not a new
university affiliation API or proof of every VNU account type.

After proven fresh authentication, source fetch/layout errors may return a
source_unavailable warning and still enter app with old/empty source; never
create fake snapshots or advance successful-sync time. Identity conflicts and
CAPTCHA/OTP fail closed. Unknown changed snapshots retain existing rollback guard.
Session/ownership/rate-limit/origin/CSRF/no-store, reminder and academic gates stay.
UI defaults to Sinh viên VNU with a separate Quản trị viên tab; student gets no
email/signup/local-password flow and no second connection form after successful
sign-in. This change does not unblock academic recommendations or activate RAG.

Validation: 440 offline passed / 71 deselected including HUS PDF acceptance;
whole-repo Ruff, JS syntax and diff checks passed. HUS PG full group 54 passed,
then 31 auth/VNU checks passed after final ownership guard. Chrome app+disposable
DB proof passed single sign-in/no second connection, session reload, admin login/
password/disable, sync/logout, VI/EN/mobile. Source/profile/workspace/charts/loading/
reminder/reauth/resume and session expiry/late logout response regressions passed.
Two old expiry assertions expected the admin form; updated to student form and
reran successfully. Existing Starlette/httpx deprecation warning remains.
No real VNU login, personal grades inspection or external email by agent.

Docker/PostgreSQL were stopped at task start; started Docker Desktop and existing
se_hus_db volume without reset. Backup/check archive and transaction preservation
proof at backups/vnu_signin_20261025/run_20261025T050450Z/. Applied 06 to local ai07;
aggregate checksums preserve all old account fields, links, source and catalogs;
only new auth fields and permitted student session revocation differ. No publish.
Gmail SMTP/.env.auth/passwords/seed handoff unchanged. Never rerun seed to reset.

App started on 127.0.0.1:8000: launcher PID 22352, child 21140 (verify command lines
before future stops); health/ready OK, anonymous /auth/session false. Runtime logs
ignored under backups/vnu_signin_20261025/. User should Ctrl+F5 and test VNU through
the UI; old student sessions intentionally require login. Real-account acceptance
is pending, not implied by synthetic checks. Read docs/VNU_SIGNIN_2026_10_25.md.

## Normal VNU reauth no longer returns HTTP 409 — 2026-10-25

User reports red console /me/portal-sync 409 after a successful VNU update.
Screenshot shows reauth 202, completed polling/profile 200 and a new successful
sync timestamp: the red request was the earlier expected missing/expired VNU
RAM state, not a failed update. API now returns HTTP 200
{"state":"reauth_required"} for that specific pre-job condition, while accepted
jobs remain 202. UI opens the existing explicit password-only reauth form as a
normal step, starts no job/poll and does not advance last_synced_at before an
actual successful job. Worker-detected expiry still arrives via job status and
uses the same form. Genuine session/auth/ownership/technical errors retain their
error responses; do not blanket-convert failures to 200 or suppress the console.

Validation: 435 offline passed / 61 deselected; two targeted disposable-PG
checks passed (RAM loss/reauth and unique ownership/delete); Chrome reauth test
asserts no new console error or failed sync HTTP response on expected expiry,
no spurious polling/profile read, successful reauth and logout race protection.
Reminder/VI/EN/themes/mobile, Ruff, JS syntax and diff checks passed. Gmail SMTP,
approved ownership repair, passwords and stored source data were not changed.

Restarted app to load API changes, /ready OK and live JS verified. Current
launcher PID 14056, child 23668; verify before stopping. Logs ignored under
backups/system_auth_20261025/runtime_reauth_state.*. User should Ctrl+F5 to load
new UI/clear prior console history; restarting discards provider RAM, so the
next update may need one explicit VNU verification. No real portal login by agent.

## Approved VNU seed-link repair completed — 2026-10-25

User reports /me/portal-connection 409 after signing in as the now email-verified
real Gmail account. Read-only metadata confirms VNU 23001953 is already linked
to the development seed student@sohoctap.test; real account has no link. This
is the intended one-to-one ownership guard, not a bad-password/worker failure.
Do not relax that guard or expose another real user's account in public errors.

Prepared ignored repair: backups/system_auth_20261025/
relink_vnu_seed_to_verified_account.py. Exact old/target UUIDs are pinned in the
script; local ai07 only, eligibility checks, account/owner locks, transfer one
link, increment generation, revoke old seed sessions and audit; source/profile
checksum must remain unchanged. Dry-run passed, preserves one snapshot, no DB
changes made. Fresh ignored backup before_vnu_relink.dump (214546 bytes) created.
User explicitly replied "đồng ý" to the concrete ownership transfer. Applied
the prepared script with --apply. Link now belongs to the requested verified
Gmail account; old student seed has no VNU link or unrevoked app sessions.
Transactional checksum verified the one existing source snapshot and profile
were preserved. Owner generation incremented and two maintenance audit events
recorded. This is a specifically approved local repair, not a general automatic
transfer policy or an authorization to weaken ownership checks.

Restarted the identified app to discard old VNU RAM/jobs; /ready OK. Current
launcher PID 26764, child 26696; verify command lines before future stops.
Gmail SMTP/secret/passwords unchanged. User should refresh the profile page;
the next sync may need explicit VNU reauth because restart cleared provider RAM.
No real VNU login or reading personal grade values was performed by the agent.

## Gmail SMTP configured by user — 2026-10-25

User requests actual inbox delivery, creates a Google app password privately in
ignored .env.auth and explicitly asks the agent to complete that configuration.
Updated only SMTP fields to smtp.gmail.com:587/starttls, matching username/from;
normalized the user's existing app password by removing grouping whitespace.
Never print or copy its value into Git/logs/chat. AUTH_TOKEN_PEPPER and other
settings preserved. TLS SMTP authentication succeeded; no email was sent by
that credential check. User should use the app resend button to verify delivery.
Runtime now uses Gmail SMTP, superseding Mailpit as the live local mail target.
Do not switch it back to Mailpit during later tests; use isolated test overrides.

Cleared only resend:account rate bucket for the active pending sender/email
used in the user's earlier Mailpit test; all other rate limits retained. No
verification flags, passwords, tokens or source records changed. Restarted app,
/ready OK: launcher PID 26912, child 26844; verify command lines before stopping.
Gmail sending/inbox acceptance still awaits user's resend; SMTP login alone is
not end-to-end delivery proof. Mailpit remains available for isolated tests.

## Password minimum changed by user — 2026-10-25

User explicitly requests minimum password length 6 instead of 15. System
password validator, register/change/cross-device verification HTML constraints,
VI/EN hints/errors and current docs now use 6–128 characters. Existing password
hashes/seed credentials remain intact; no password reset or migration involved.
Boundary API test passed: 5 rejected / 6 accepted for registration, cross-device
verification and password change. Chrome/SMTP proof passed using a six-character
synthetic password; Ruff, JS syntax and diff checks passed. Restarted local app:
launcher PID 28492, child 27300; /ready 200 and live form minlength=6 confirmed.
These PIDs supersede the older runtime checkpoint below; verify before stopping.

## Separate system accounts implemented locally — 2026-10-25

User authorized implementation of the detailed system-auth plan, superseding
the planning-only checkpoint below. Work is on
`feat/system-auth-email-20261025`, retaining the preceding unpublished VNU
session/reminder work. No commit, push or PR authorized; future main changes
still require a feature branch, PR and merge commit preserving real authors.

Implemented email/password register, pending verification, one-use 30-minute
email tokens with same-browser registration proof / cross-device password
replacement, resend/rate limits in DB, Argon2id, persistent opaque app sessions,
2-hour idle / 12-hour absolute expiry, CSRF/origin/no-store, forced initial
password change, account/role/status guards and safe audit metadata. Session
family survives password rotation so simultaneous logout invalidates replacement.
Account-before-session locking and serialized admin updates are concurrency-tested.

System login is separate from VNU: retired POST /auth/portal returns 410;
/me/portal-connection requires verified local account. Unique account/VNU owner
claim needs fresh successful VNU evidence, including old unclaimed owners; never
assign legacy grades to seed users or by email/name. Provider cookies remain
per-app-session RAM only. DB session/account/link/generation rechecked before
source reads/writes and after workers. Disconnect/delete VNU preserves app account;
logout/password/role/disable revokes relevant VNU RAM and late work. Admin manages
accounts without default access to another user's grades. Legacy /profiles routes
are closed with 410; retained academic POST calculators require verified account
and CSRF. Domain tests remain; active UI still VNU-only, seven-day reminders kept.

Actual ai07 backup: ignored backups/system_auth_20261025/before_auth.dump.
Applied additive hus_20261025_04 and hus_20261025_05, runtime HEAD now 05.
Restored the pre-auth backup to a disposable DB and compared count/checksum of
all 17 original non-version tables (old accounts projected to original columns,
excluding new seeds): unchanged, including catalogs and source snapshots.
No catalog publication, invented student rows or source-owner reassignment.

Exactly two local bootstrap-verified DB accounts created with random temporary
passwords: admin@sohoctap.test/admin and student@sohoctap.test/student. Both start
must_change_password=true and seeded_for_dev=true, no VNU link. Private handoff:
backups/system_auth_20261025/accounts.private.txt, ignored, user-only file ACL;
never print its contents. Seed idempotent/no reset, rejects collisions and production.
Later user testing may change password/flags; do not reset them or regenerate handoff.

Ignored .env.auth configured for local SMTP and generated server secret; keep it.
Versioned .env.auth.example has placeholders only. Mailpit se_auth_mail is bound
to loopback 1025/8025; inbox http://127.0.0.1:8025/. Actual browser+SMTP proof used
disposable DB and synthetic .test accounts, not outside inboxes. Real SMTP/domain/
HTTPS/proxy and production deployment remain gates; production rejects active dev
seeds, fake/insecure SMTP and HTTP at startup/readiness. No password recovery or
weekly automatic crawl added. Multiple processes still need a VNU-state design.

Validation: 434 offline passed / 57 deselected before three additional PG-only
checks; 41 HUS PostgreSQL passed plus 3 additional concurrent/production checks
passed (44 total exercised). Chrome/SMTP, source UI, workspace/charts, loading,
session expiry/logout races, reminders, reauth/resume, identity/profile source,
VI/EN/themes/mobile passed. Existing Starlette/httpx deprecation warning remains.
Profile-source browser test exposed Playwright HTTP-redirect mock escape: an
anonymous source-page GET could leave the fixture; no real credentials were
submitted and no personal grades were read. It now uses networking-off contexts
and explicit fixture navigation, and passes. Do not claim an intercepted 302 proof.
No real VNU login for the new local-account link was performed by the agent;
previous user-reported VNU update acceptance applies to the earlier session flow.

Runtime restarted on 127.0.0.1:8000, /ready 200 with postgres and public
/auth/session returns authenticated:false without a cookie. Launcher PID 26284,
child 17420; verify command line before future stops. Ignored runtime logs and
synthetic screenshots under backups/system_auth_20261025/. User may now test;
do not silently change seeded roles/passwords during follow-up validation.

Implementation/runbook: docs/HUONG_DAN_TAI_KHOAN_HE_THONG.md and module 12.

## Separate system accounts architecture plan — 2026-10-25

User requests a detailed PLAN for Sổ học tập accounts: register, verify email,
login/logout, admin/ordinary user roles, and two seeded local DB accounts when
implemented. VNU becomes a data connection after system authentication. This
supersedes historical no-separate-local-password scope for the planned module;
VNU passwords/cookies still must not be persisted. Current turn is planning-only.

Plan: docs/KE_HOACH_TAI_KHOAN_HE_THONG_2026_10_25.md, new module 12. Proposes
extending existing accounts with UUID/email/verification and reusing student/admin
roles, DB-backed app sessions, explicit unique account-to-portal links and verified
claim of old VNU owners. No automatic assignment to seed users or based on email.
Mailpit local / configurable real SMTP, bounded single-use verification, explicit
bootstrap exceptions only for two local test users. No actual accounts, email,
DB migration, runtime/auth cutover, restart, commit or push in this planning turn.
Mail delivery/provider and production domain are future configuration gates, not
an excuse to skip verification. Preserve all existing unpublished session/reminder
work. Weekly automatic VNU sync remains deferred.

## VNU session reuse implemented locally — 2026-10-25

User explicitly requests implementation of the session-reuse plan and frequent
updates, superseding the planning-only checkpoint below for this task. No commit,
push or PR authorized. Work remains on fix/portal-session-diagnostics-20261025.

Implemented bounded, host-scoped cookie contract (64 cookies/64 KiB, stdin 72 KiB),
worker login/resume with fresh Chrome/context per job, private per-web-session
RAM state, versioned rotation and TTL, 30-second cleanup, logout/current-session
and delete/all-owner revocation, no password/cookie persistence. Existing fresh
login evidence remains required; resume state originates only from the server
session and conflicting source identity fails closed. API sync accepts no
credentials; explicit /me/portal-reauth accepts password only, subject from session.
UI sync runs immediately; only vnu_reauth_required opens a separate reauth form.
Technical failure does not force reauth. Seven-day reminder/source gates remain.

Automated Chrome proof: one synthetic password POST, two new-browser resumes,
cookie rotation, identity conflict, expired source and CAPTCHA. UI regressions
pass profile/VNU-only/workspace/charts/session/reminder/reauth, VI/EN/themes/mobile
and stale responses. Synthetic mobile screenshot inspected. No real portal
request or personal-record inspection by the agent. User subsequently confirms
"Cập nhật được, không hỏi lại mật khẩu" after the requested UI test. This is
user-reported real happy-path acceptance, not independent completeness or all-account
verification. Single-process RAM sessions only; restart
loses them. No new migration, catalog publication, .env edit or scheduled crawl.

Final offline verification: 434 passed / 40 deselected with explicit HUS PDF
acceptance root, whole-repo Ruff, JS syntax and diff checks passed; existing
Starlette/httpx warning. No new PostgreSQL run was needed for session-only changes.

Restarted the identified local Uvicorn; launcher PID 21908, health/ready 200 on
127.0.0.1:8000 with PostgreSQL. Logs/screenshots ignored in
backups/portal_reuse_20261025/. User confirmed the requested login/update flow.
The scoped local implementation and happy-path acceptance are complete; do not
claim full portal delivery, completeness acceptance or production readiness.
This acceptance update changes documentation only, with no new tests/restart.

## VNU session reuse plan — 2026-10-25

User requests a PLAN for updating grades within the app session without entering
the VNU password again. See docs/KE_HOACH_GIU_PHIEN_VNU_2026_10_25.md and module 09.
This request is planning-only: no runtime implementation, restart, credential
collection, live portal request, commit or push in this turn.

Design: VNU cookies in RAM scoped to each authenticated web session, short-lived
workers restoring an isolated context, explicit reauthentication only when VNU
requires it, TTL/rotation/logout/delete/expiry cleanup. Cookie-only restoration
on real VNU is NOT proven; retain a validation gate and never weaken identity.
The planned lifetime supersedes job-only cookie disposal only upon implementation;
it does not authorize password persistence or durable cookie storage. Weekly
automatic sync remains deferred; current button/seven-day reminder stay in scope.

## Portal update reminders — 2026-10-25

User targets a real multi-student server app, but explicitly defers automatic
weekly VNU sync until the system is nearly complete. Current scope is an explicit
“Cập nhật bảng điểm” button and an in-app reminder after seven days. No scheduled
crawl, email/push, password persistence or background reauthentication is added.
The global workspace bar replaces the curriculum warning on Dashboard/profile;
the draft-catalog warning remains on eligibility/recommendation pages.

Successful accepted sync stores server-owned `_last_synced_at` in existing
portal_users.profile JSONB, exposed separately as last_synced_at. Identical
current-snapshot reads refresh it; failed/rejected sync does not. Snapshot
payload/digest/fetched_at remain unchanged. Legacy profiles fall back to fetched_at.
Changes remain local on fix/portal-session-diagnostics-20261025, together with
the preceding session-status/502-diagnostics work; no commit/push authorized.

## Session close — 2026-10-23: team history preserved, temporary branches removed

User requests memory update and a permanent PR rule to keep each member's
original commits visible on main. This close-out changes documentation only;
do not start new implementation or publish these edits without a new request.

Latest verified main/origin/main is 8f77ce3, with no ahead/behind difference and
a clean working tree before this memory update. Login PR #2 merged as c73d08f;
crawler PR #3 merged as 8f77ce3, both using GitHub merge commits after all six
PR CI checks passed. Original added history: 33 commits under 23172c43 (login),
43 under Thang and 10 under Duong Van Tai (crawler), including merge commits.
Database setup/tests and Vinh branch tips were already ancestors of main.
All four fetched source tips were verified ancestors of final main, with zero
remaining commits in main..source. Original author/hash metadata is retained.

These were explicitly history-only ours merges; only contribution docs and
memory changed from 0b4b2fc. They did not adopt every source-branch feature.
Later login timestamp/schema changes, crawler activation and RAG/corpus serving
remain deferred. Future functional adoption needs explicit reapplication/review
because Git now regards these historical source tips as merged. Do not treat
this special reconciliation as the normal feature integration workflow.

User authorized deletion of ONLY integration/login-history-20261023 and
integration/crawler-history-20261023. First attempt did not execute because
automatic approval review hit a usage limit. On retry, both remote branches
were already absent; after ancestry verification, removed the two local branches
and pruned stale remote-tracking refs. Fetch also reported codebase,
feat/catalog-validation and fix/hus-metadata-vi-en-20261021 already deleted
remotely; this agent did not delete those remote branches. Keep teammates'
remaining branches. Deleting merged branch names does not remove main's commits
or the merged PR records.

Validation from the history work: 398 offline passed / 39 deselected, whole-repo
Ruff and diff checks passed; existing Starlette/httpx warning. No tests rerun
for branch cleanup or this documentation-only close-out. No portal access,
real-data inspection, DB migration, restart or crawler run. Main-branch CI
after final merge was not separately rechecked; six-check evidence is per PR.

## Permanent workflow — PRs and original team commits on main

- All future updates to main, including docs/memory, go through a feature branch
  and GitHub PR. Never push changes directly to main. Prior one-off direct-push
  authorizations are historical, not a standing exception to this rule.
- For new work, branch from current main. To integrate an existing teammate
  branch, preserve its genuine commit ancestry in the PR branch and resolve
  conflicts there. Do not silently replace original commits with an integrator's
  copy/import commit. Check which original commits are already in main first.
- Merge PRs using Create a merge commit (API merge_method=merge). Do not use
  Squash and merge or Rebase and merge, and do not rewrite/force-push main.
  Preserve original author identities and hashes; never manufacture commits,
  change authors to boost counts, or add fictitious co-author credit.
- Describe actual functionality, conflicts, deferred changes and verification
  in the PR. Run relevant checks and wait for required CI before merging. A
  history-only reconciliation requires explicit authorization and disclosure;
  never substitute it for requested functional integration.
- Verify source-tip ancestry and original commits in the resulting main after
  merge. GitHub attribution also depends on each original author email being
  linked to that member's GitHub account; commit history is not a grading promise.
- Existing publication rules still apply: do not commit/push/create or merge PRs
  without user authorization for that task. If only local edits are requested,
  leave them local and report their unpublished state. If publication is
  authorized, carry it out through this PR workflow.
- Delete temporary merged branches only when authorized; preserve branches
  teammates still use. This is a contributor rule, not a claim that GitHub branch
  protection/settings have been configured. Change hosting settings only when
  separately requested. Exceptions require an explicit new user instruction.

## Team history reconciliation — 2026-10-23

User explicitly authorizes PRs, merges and publication to main to preserve
teammates' original database, test, crawler and login commit histories. This
supersedes the previous close-out stop for this history task only. Starting
main is 0b4b2fc. Database setup/tests and Vinh branch tips are already ancestors.
Login fetched tip b3964ce has 33 missing commits; crawler tip 3a45aae has 53.
Use explicit history-only ours merges and GitHub merge commits, preserving the
current application tree and original author/hash metadata. PRs must state this
scope; do not claim new source-branch features are functionally integrated.
No new database migration, crawler activation, corpus publication, portal access
or real data inspection. See docs/TEAM_CONTRIBUTIONS_2026_10_23.md. Functional
changes skipped by the history merge need explicit review/reapplication later.
Login history PR #2: https://github.com/5-Bit-System/SE_Project/pull/2.
Crawler history PR #3: https://github.com/5-Bit-System/SE_Project/pull/3.
PR #2 merged as c73d08f after all six GitHub checks passed. Use the PR records
for final publication/CI state; crawler PR retains the original 53 commits.
Local verification: 398 offline passed / 39 deselected, whole-repo Ruff passed,
existing Starlette/httpx warning only. All runtime/source/dependency/CI files
are unchanged from 0b4b2fc; only memory/contribution documentation changes.

## Session close and main publication — 2026-10-23

User requests memory update, session close, commit and push all current project
work to main. This supersedes older no-commit/push notes for this change set.
Publication starts at main/origin/main 3129f7c (fetch verified 0/0 ahead/behind);
use Git to verify resulting commit/push. Do not begin new implementation, restart,
access VNU or inspect real DB data in this close-out. Credentials/.env/backups/
screenshots/toolkit stay ignored. Prospective changed/new files are text code,
tests/docs; token/contact-pattern scan found only commit-hash digit substrings.

User-provided local screenshots now show all name/program/cohort fields after
the source fixes. This confirms display, not independent completeness/policy
acceptance. Connector reads Hồ sơ sinh viên for name and Cập nhật hồ sơ sinh viên
for selected Lớp quản lý text, split as user-confirmed [numeric cohort] [program].
Never submit that VNU form or retain screenshot personal values in artifacts.

Active frontend has no manual grades/upload/demo/term entry or manual Dashboard
KPIs. No program picker/default catalog: sidebar program/cohort and top-strip
program come from saved VNU display fields. Duplicate header profile button is
removed. Language now uses VIE/EN buttons matching appearance control, with
pressed state, keyboard activation and preference restoration. Old language
select removed; active modules use workspace:language-change. Known credit/GPA
summary labels localize; source numeric values, names and snapshots stay intact.
Personal source UI clears on logout/expiry/delete; stale responses are ignored.

Staged authenticated AcademicContext backend exists, but cutover is partial:
unknown completeness, no reviewed program/policy binding, empty production policy
registry, incomplete what-if baseline/results UI. Rules/recommend screens wait;
old manual advisor/results flow is not loaded. Legacy public input APIs and
dormant app.js/dashboard.js remain for future retirement/reference. Do not claim
full academic integration or unblock it from display strings. Preserve changed-
unknown snapshot protection. RAG remains inactive; preserve retained source.

Final checks: 398 offline passed / 39 deselected with explicit HUS acceptance
root, whole-repo Ruff passed, one existing Starlette/httpx warning. Latest Chrome
VNU-only/profile/workspace/charts checks pass after VIE/EN changes, including
keyboard/reload persistence, VI/EN summary, source labels, themes/mobile/logout
races. JS syntax/diff checks pass; synthetic mobile screenshots inspected. No
new PostgreSQL run in close-out; earlier migration/store evidence is historical.
Migration hus_20261023_03 was already applied locally with backup; publishing
code does not apply it elsewhere or publish catalog changes. No real-data or
source-catalog changes in this close-out. Stop after publication handoff.

## Source-summary UI labels — 2026-10-23

User reports English UI still displays Vietnamese total-credit/GPA labels.
Added shared workspaceI18n.formatSourceSummary, used by Dashboard and profile.
Translates only allowlisted summary labels at the start of each cell (credits,
accumulated credits, cumulative/semester averages on source 4/10-point scales).
Numeric text/decimal separators, unknown labels, row arrays and persisted
snapshots remain unchanged; switching back to VI renders original labels.
Program/course names and personal source values remain untranslated. This is
the requested label localization exception to historical raw-summary UI text.
Chrome charts/profile regressions cover English labels, comma decimals,
multi-cell labels/values, unknown-text preservation and VI restoration; passed.
Ruff/JS syntax/diff checks passed; frontend only, no DB/portal/restart/commit/push.
Also removed duplicate header profile button per user's preceding request;
sidebar profile navigation remains, Chrome login/profile checks passed.

## Source-owned sidebar — 2026-10-23: program selector removed

User supplied local profile screenshot showing name/program/cohort now populated;
this is user-provided display acceptance, not independent source completeness or
policy acceptance. Do not retain the personal values in artifacts. User requested
removal of the four-program selector in favor of the VNU profile's program.

Removed sidebar selector and /programs fetch/default-first-program behavior.
Sidebar now shows read-only program/cohort from the authenticated saved profile;
top strip shows source program. Missing values show unavailable; signed-out
values show not signed in. Portal event carries only program/cohort display
fields in addition to existing snapshot/time, no new name/identifier/credentials.
Source strings are textContent and excluded from UI translation. Logout/expiry/
delete clears both sidebar/top strip; delayed profile responses cannot restore.

No source-name-to-catalog guess or academic binding was added. Without a reviewed
server binding, active UI no longer requests academic-context with an arbitrary
selected program: academic panels state pending conversion/binding and source
completeness from the saved snapshot. This supersedes the preceding UI checkpoint
about a reference dropdown and fetching context with its selected program.
Backend academic APIs are unchanged and remain gated.

Chrome check_vnu_only/check_workspace/check_charts/check_portal passed, including
source labels, missing-value cleanup, VI/EN, logout/delayed response, themes/mobile,
no /programs or guessed-context requests. Synthetic mobile screenshot inspected.
Ruff/JS syntax/diff checks passed. Frontend only: no new Python backend/DB tests,
portal access, real-data edits, restart, commit or push. Reload browser to load UI.

## VNU-only active UI — 2026-10-23: manual entry removed, academic tools gated

User explicitly challenged the remaining Nhập điểm screen, referring to the
agreed VNU-only direction. Removed manual tab, file preview, term/course/grade
controls, manual Dashboard KPIs/plan and all entry links from active index.html.
Old #transcript redirects to #profile. New workspace.js replaces loaded app.js
and dashboard.js; these legacy sources remain dormant for reference/rollback.
No hidden manual form or empty completed set is used by the active frontend.
Dashboard source charts and profile/login/sync/delete remain active. Sidebar
program selection is labelled reference only, not a verified account binding.

Rules/recommendation screens now fetch /me/academic-context using session and
program selection, display sign-in/readiness blockers, and do not run the old
manual eligibility/recommendation/what-if/advisor flow. Legacy advisor UI was
removed with that flow. Personal academic tools await completion of VNU
context readiness and frontend results implementation; do not claim full
cutover. Legacy public input APIs/backend/domain tests are retained, not removed
or secured by this UI-only change; backend retirement remains in the plan.
The earlier requirement to retain manual UI until replacement is superseded
for this UI removal request; safety gates remain and academic output is paused.

Chrome check_vnu_only.py passes old URL redirect, no manual DOM/legacy scripts
or personal-input requests, session-backed readiness, logout vs delayed-context
race, VI/EN/themes/mobile. Updated check_workspace.py/check_charts.py for removed
manual state and intercepted academic context; both pass, as does check_portal.py.
Initial chart run failed because its newly required context fixture was absent;
mocking that personal endpoint resolved it. Screenshots synthetic; mobile
inspected. Ruff, JS syntax and diff checks pass. No backend/DB/schema/.env edits,
runtime restart, live portal access, real data manipulation, commit or push.
Previous 398 offline tests are prior backend evidence, not a new UI-task rerun.

## Management-class source — 2026-10-23: name accepted, cohort/program retry pending

User confirms the prior fix now displays the student's name. New ORIGINAL VNU
screenshot locates enrollment details in Cập nhật hồ sơ sinh viên. User explicitly
defines the selected Lớp quản lý text as [numeric cohort] [program name]; use
that split for display, not the separate Khóa selector. Do not retain screenshot
personal values in code/tests/docs. This is display semantics, not academic
policy/program applicability approval.

Client now clicks that existing exact-label menu after preserving name/identity
texts, waits for Lớp quản lý, reads only its adjacent cell/selected option TEXT
(including disabled selects), and never fills/submits the update form. No guessed
module IDs/URLs. Parser splits a single unambiguous numeric prefix and program;
empty/malformed/conflicting class values remain unknown. Selected management
class is authoritative for these two display fields. Store/schema/digest and
changed-unknown rollback protection unchanged. Frontend renders the resulting
fields normally; VI/EN update button now includes both profile and transcript.

Validation: 398 offline passed / 39 deselected with explicit HUS acceptance root,
existing Starlette/httpx warning; Chrome source and profile UI fixtures passed
delayed module/frame navigation, disabled select with other unselected options,
name retention, source transcript, fields/VI-EN/mobile/logout. Ruff/JS syntax
passed. Synthetic mobile screenshot inspected. No live login/real-data read,
PostgreSQL rerun, schema/.env edits, restart, commit or push. Fresh worker on
next login/sync loads the fix; need user confirmation for actual cohort/program.

## Profile module/cell collection fix — 2026-10-23: live confirmation pending

User resumed the missing name/program/cohort bug and supplied a screenshot of
the ORIGINAL authenticated VNU profile page. It shows the exact navigation
label Hồ sơ sinh viên and a multi-column label/value table (including Họ và tên).
Program/cohort labels are not visible in the supplied region; do not guess them.
Do not copy any personal values from either screenshot into code/docs/tests.

Found two concrete code gaps: read_profile_texts only captured the default.asp
shell without invoking the student-profile menu; the text parser rejects rows
with multiple label/value pairs. Client now invokes the existing exact-label
profile menu handler, waits for a labelled name in the loaded page/frame, and
extracts allowlisted adjacent table cells into separate labelled lines. Visible
text inputs/selected option text are supported; hidden/nested/ambiguous cells
and family-name labels are excluded. No guessed module ID/URL or academic binding.
Existing landing-page support and source identity checks remain. Store and
snapshot/completeness/rollback behavior unchanged; no DB/schema changes.

Chrome intercepted synthetic regression passed module navigation, delayed
iframe, multi-column rows, controls, missing labels, hidden/family fields,
identity evidence and retained transcript. Auth Chrome regression and Ruff
passed. Full offline suite: 390 passed / 39 deselected, explicit HUS acceptance
root, existing Starlette/httpx warning. Health/ready both 200; no restart needed
because each sync/login spawns a fresh worker. No live portal login, personal
data inspection, PostgreSQL rerun, commit or push. User must try Update transcript
with the changed worker before calling the real-account issue resolved. If only
name appears, need source evidence for the actual program/cohort labels/layout.
This supersedes the older statement that no original-source screenshot exists;
it does not establish live field acceptance or snapshot completeness.

## Session close — 2026-10-23: VNU profile details STILL UNRESOLVED

User explicitly requests memory/status update and session close. Stop implementation
after this documentation handoff; no further restart, portal login or retry in
this close-out. Keep all local changes; no commit/push requested.

Latest user acceptance: login succeeds and saved source transcript displays,
but Họ và tên / Ngành học / Khóa học STILL show unavailable. User explicitly
confirmed they already logged in again after the fixes, not merely pressed F5.
Their screenshot is the local /#profile UI, not the authenticated VNU source.
Do not copy identifier, grades or source totals from that screenshot into docs,
tests or memory. Do not tell them the cause is just refresh/cache or an old
login, or keep asking for the same retry without new diagnostic evidence.

A minimal read-only aggregate database check confirmed no non-null name,
program or cohort values are stored. It printed no identifiers or individual
grades. Thus the gap is in source collection/parsing/persistence, not solely
frontend rendering; exact cause is NOT yet proven. No F12 errors is consistent
with a successful profile response containing missing fields, not proof of a
successful source extraction. Inspect possible save rejection/rollback as well
as parser/source layout before attributing the gap to one stage.

Previous code changes (dynamic UI fields, source_profile parser, transactional
metadata save, early default.asp capture) are implemented and synthetic tests
pass, but DID NOT resolve this real-account issue. The authenticated layout,
labels, frame/form controls and loading behavior at default.asp have not been
observed independently. Public access redirects to login. Last request to user
was a screenshot of the VNU source region with values redacted but labels/layout
visible; none supplied yet. Do not mistake their local app screenshot for it.

Resume with source-layout evidence or authorized minimal in-session diagnostics;
trace collection -> parser -> save/rollback -> API -> UI without logging personal
values, raw DOM, cookies or credentials. Do not add more speculative label rules,
infer name/program/cohort, or mark metadata/binding/completeness verified. Keep
existing transcript and changed-unknown snapshot protection intact. Display
metadata must not become a reviewed academic program/policy binding.

Historical checks: 390 offline passed / 39 deselected, 4 disposable PostgreSQL
portal tests, Chrome fixture checks; later landing-page change had its own Chrome
check and 17 focused tests. These are synthetic/code evidence, NOT real profile
field acceptance. Overall ~90% was an implementation estimate only; portal
delivery and this bug remain incomplete. Latest known server localhost:8000,
PID 28848 after verified restart; not rechecked at session close. Earlier auth/
completeness/alias/update/delete acceptance gates remain. Close-out changes are
documentation-only; no new app/DB regression claimed.

Handoff: docs/PORTAL_INTEGRATION_STATUS_2026_10_23.md (latest unresolved section),
docs/KE_HOACH_TICH_HOP_PORTAL_BANG_DIEM_2026_10_23.md and module 09 updated.

## VNU landing-page profile capture — 2026-10-23

User identifies https://daotao.vnu.edu.vn/dkmh/default.asp as location of profile
details. Public read redirects to login; authenticated structure is still not
independently observed. Found worker only captured body text AFTER open_transcript,
which can replace landing-page content. Added DaotaoClient.read_profile_texts:
read fixed authenticated default.asp after fresh login, before transcript click;
avoid reloading if already at exact URL. Combined early/later texts participate
in existing identity-conflict checks and source_profile parsing. No extra
URLs from client, no guesses about profile labels/academic binding, no raw text
logging or artifacts. Missing fields still unknown.

Chrome synthetic test tests/frontend/check_portal_profile_source.py passed both
login redirect and explicit default.asp navigation, profile removed by transcript
click, early source retention and preserved transcript reads. 17 focused worker/
snapshot tests and Ruff passed. No DB/schema/store change in this follow-up.
Worker launches fresh per login/sync, so new worker/client code applies on next
connection without restarting web server or revoking current session. Need user
retry Update transcript and, if still missing, redacted layout evidence; do not
claim real profile fields fixed based solely on fixtures. No commit/push.

## Profile display fields checkpoint — 2026-10-23

User reports successful login and visible real transcript, but name/program/
cohort all unavailable. This is user-reported live login/display evidence,
not independent completeness/update/delete acceptance. Found UI hardcoded all
three values as unavailable; worker did not collect them and store never wrote
portal_users.profile. Fixed rendering of source profile fields, cleared on
logout/expiry, preserved source text across VI/EN. Added source_profile parser
for exact labels with colon/tab and value on same line in existing authenticated
page/frame body inner_text; missing/ambiguous/conflicting values stay null.
No additional portal navigation or guessing from student ID, years or major.
This limited parser is not proof real portal supplies those labels there.
Asked user where these fields appear in VNU; answer pending at checkpoint.

Worker sends profile separately from immutable transcript; store.save writes
allowlisted name/program/cohort under owner lock in the same transaction,
including identical digest refresh. An incomplete changed transcript rolls back
metadata as well. Transcript digest/rows/completeness and academic bindings
unchanged. Existing JSONB column used; no migration/.env/catalog changes.
Source program/cohort strings are display-only, never reviewed policy bindings.

Validation: 390 offline passed / 39 deselected with explicit HUS PDF root;
4 portal PostgreSQL tests passed on disposable per-test databases, cleaned by
fixture, including metadata ownership/update/idempotency/rollback. Chrome
profile fixture regression passed rendering, VI/EN fallback and logout cleanup.
Ruff/JS syntax/diff checks passed; existing Starlette/httpx warning remains.

Correction to previous startup note: the attempted server launch had failed
with port already occupied; previous health checks reached existing Uvicorn.
Verified port PID 31036 command line is project Uvicorn and restarted this
specific process to load current backend. New server PID in log 28848, hidden,
access log disabled. Health/ready 200 and current HTML verified. Session needs
fresh login; persisted snapshots retained. Logs ignored under
backups/portal_resume_20261023/profile-server.*. No real portal request by agent,
real-data inspection, commit or push. Need user retry and source layout evidence
before claiming real profile fields resolved. Portal plan remains ~90%.

## Login continuation checkpoint — 2026-10-23

User explicitly resumed the portal/login plan, requested frequent progress,
and agreed to test credentials directly in localhost UI (never in chat).
This supersedes deferral of login work; academic policy/program/DB cutover
remains separate. No schema, .env, catalog, real data, commit or push changes.

Added session recheck after profile storage read and before sync save; expired
or revoked session does not return profile/start a save. Existing committing
transaction still finishes with its actual result. Logout revokes first and
clears even an expired/missing cookie, with origin checks unchanged. UI clears
personal state immediately on logout; epoch/sequence guards reject stale reads.
Explicit visible captcha/OTP controls return interaction_required (409), with
VI/EN text and no attempted bypass; hidden controls ignored. Recognition is
limited to tested selectors, not universal challenge detection or interaction.
Playwright timeouts map to timeout; malformed credential JSON/encoding is 400.

New verification: 386 offline passed / 38 deselected with HUS PDF acceptance
root; existing Starlette/httpx warning. Chrome synthetic portal auth, profile,
workspace and charts checks passed, including delayed response after logout,
expiry/relogin and challenge text. Ruff, JS syntax/diff checks passed. Dark
mobile fixture screenshot inspected. No new PostgreSQL tests (no store/schema
changes), real portal requests or real records in test artifacts.

No listener was present at 8000; started project Uvicorn hidden with access log
disabled. Health/ready returned 200. Ignored logs backups/portal_resume_20261023/.
User was invited to Ctrl+F5 and test /#profile; result still pending at this
checkpoint. Portal plan remains ~90%, completeness unknown, changed unknown
snapshots remain blocked, alias mapping unverified. Do not claim full live
acceptance. See docs/PORTAL_INTEGRATION_STATUS_2026_10_23.md for exact scope.

## Implementation checkpoint - 2026-10-23: staged VNU academic context (~30%)

User authorized the existing cutover plan with project-toolkit, superseding
the previous planning-only restriction. Then clarified program/cohort unknown
and login/database work should be done later. Keep those deferred: no auth flow,
schema, real data or .env changes in this implementation. Do not ask again for
program/cohort now or infer them from an identifier. No server restart/portal
access/commit/push. Existing dirty portal/frontend changes preserved.

Added app/academic_context.py: pure source-owned context, explicit reviewed
binding/policy, fail-closed readiness, exact code matching, raw row references,
retakes/unknown outcomes unresolved, no GPA conversion or legacy transcript
defaults. Source/schema/empty/unknown/duplicate rows and conflicting grades are
gated. No real policy registered; synthetic policies exist only in tests.

Added app/api/academic.py and router registration: /me/academic-context,
/me/eligibility, /me/academic-progress, /me/recommendations, /me/advisor/chat.
Owner comes only from existing session, snapshots from existing store.profile.
Reject browser owner/records/passed sets. Revision includes owner, session,
source, catalog content, binding, policy and selections. Slow recommendation/
advisor responses recheck source/revision/session before returning. Existing
origin/no-store middleware applies. /me/recommendations/what-if is only a staged
readiness/baseline guard; a ready context returns academic_baseline_not_available.
Server-owned baseline comparison NOT implemented yet.

Live readiness remains blocked: connector completeness=unknown, actual program/
policy binding unavailable, policy registry empty. Staged catalog revision is a
content fingerprint, NOT the future canonical DB revision FK. Do not manually
set completeness/review metadata for a real account to enable this feature.
Frontend and legacy input/public APIs remain unchanged until replacement gates
pass per the plan. This is not the full manual-removal completion.

42 new synthetic context/API tests, TDD red/green observed. Full offline suite:
377 passed, 38 deselected with explicit docs/acceptance/hus_2022 catalog root;
one preexisting Starlette/httpx warning. Ruff changed files/diff checks passed.
No PostgreSQL/browser/live acceptance for this staged backend-only change.
Inline review used toolkit entrypoint override; no subagents/worktrees/commits.
See docs/VNU_ACADEMIC_CONTEXT_STATUS_2026_10_23.md for verified scope and pending
work. Ignored execution ledger: backups/vnu_academic_cutover_20261023/progress.md.

## Planning checkpoint - 2026-10-23: retire manual grades after VNU academic-context cutover

User asked what Enter grades was for, agreed with the proposal to fully remove
it once VNU feeds eligibility/recommendations, then explicitly requested a PLAN.
Created docs/KE_HOACH_CHUYEN_SANG_BANG_DIEM_VNU_2026_10_23.md. This is planning
only, not authorization to start this implementation in the current request.
Added scope notes to modules/02-transcript-profile.md and modules/README.md.

Target: one source of academic results, owner-authenticated VNU snapshot;
retire manual entry/upload/demo/public APIs accepting client records/passed sets.
Keep pure domain tests/synthetic fixtures, immutable source snapshots and legacy
DB rollback resources. Do not delete those as part of UI removal. Need fresh
policy/program applicability evidence; do not infer cohort from screenshot ID.
Current legacy model rejects retakes, defaults missing grades to passed and
applies project grade thresholds/GPA conversion; raw portal data cannot be
fed straight into it. No matching by name/stripping E or best/latest retake
selection without source-backed policy.

Seven phases: evidence/policy, complete/safe sync, versioned AcademicContext,
server-owned authenticated academic endpoints, frontend cutover, remove manual
flow/old public personal-input APIs, end-to-end acceptance. Do not delete the
existing input path before replacement gates pass or serve recommendations from
an empty completed set when the real context is unavailable. Unresolved results
must neither satisfy prerequisites nor lead to unsafe repeat recommendations.
Snapshot/catalog/policy changes invalidate contexts, baseline what-if and chat.
Stored old data may be used only with valid session and sufficient readiness;
a VNU outage is not permission to bypass authentication. Sources stay unchanged.

No runtime/API/DB/.env changes, portal access, tests, restart, commit or push in
this planning request. Existing login/UI work remains local and unchanged.

## Dashboard charts checkpoint - 2026-10-23: VNU statistics and demo UI removed

User requested actual dashboard charts and removal of the obsolete Demo data
selector now that VNU login works. Continued GitHub frontend-design guidance.
Removed the demo profile selector, auto-loading /profiles and all associated
frontend profile-selection helpers/state. Removed year-based buttons that
generated invented sample grades. Test fixtures and backend compatibility APIs
remain; no real records were changed/deleted. Local-file preview still exists
as Open transcript file; it never injects sample grades automatically.

Dashboard now prioritizes DESCRIPTIVE charts from the authenticated saved VNU
snapshot: arithmetic mean of valid source 10-point grades by semester, source
letter-grade distribution, and sum of credits written on attempts by semester.
Every retake stays separate; missing/invalid values stay unknown (zero is valid).
Mean is explicitly NOT official GPA, attempt credit sum is NOT earned credits.
No catalog matching, grade conversion, pass inference, best-attempt selection
or source apply into eligibility/recommendations/manual transcript was added.
Unknown completeness and source fetched time remain visible. Official summary
text is displayed as supplied by the snapshot, without recalculation.

Charts have a shared academic-year filter, labelled points/legend, an accessible
data/calculation table, both themes/VI-EN/mobile and empty states. Source data
stays in JS memory only and is cleared from ALL chart DOM on logout/delete/
expiry. Existing manual KPI/progress/eligibility panel is under a collapsed
Study plan from manual data section. Source charts are independent of the
selected draft catalog; changing major still resets only the manual plan.

This supersedes the earlier no-profile-fetch-on-dashboard rule: initial page
now requests /me/profile ONCE to visualize the saved authenticated snapshot.
It never logs in/crawls VNU automatically. No session means charts show sign-in
empty states; the existing 401 auth semantics remain (login module still deferred).
Portal publishes snapshot/source_summary/fetched_at to chart subscribers via
in-memory events; identifiers and credentials are not passed into chart events.
No backend/API/worker/database/.env changes or server restart during this task.

Added app/static/analytics.js (pure aggregation + SVG/CSS charts), analytics.css,
tests/frontend/check_analytics.mjs and check_charts.py. Node aggregation tests
passed retakes/comma/zero/missing/invalid values/year filtering/no input mutation.
Three actual Chrome fixture regressions passed: check_charts.py, check_workspace.py,
check_portal.py. Checks include correct means/counts/credits, no bridging across
missing-grade semesters, filter changes, no demo API/UI, no source apply, source
preservation, logout chart cleanup, VI/EN, theme buttons and 390px containment.
Reviewed light/dark/mobile synthetic screenshots in ignored
backups/dashboard_charts_20261023/. Ruff frontend tests, JS syntax, diff checks
passed. Health/readiness 200. No Python/PostgreSQL rerun for frontend-only work.
All changes local; no commit/push. Existing portal identity/completeness gates
and preservation of original HUS/RAG sources remain in force.

## UI redesign checkpoint - 2026-10-23: Dashboard and dedicated profile page

User requested a polished frontend redesign using the GitHub frontend-design
skill: profile as its own navigation destination and Dashboard replacing the
initial transcript view. User explicitly deferred login-module/401 work until
later. Read/applied .github/skills/frontend-design/SKILL.md. Changes are frontend
only; no API/auth/worker/database changes, portal calls or backend restart.
Existing real user session should remain valid until its original expiry.

Dashboard is default /#dashboard; profile is /#profile, a full tab panel rather
than a dialog. Navigation has Dashboard, My profile, Enter grades, Eligibility,
Next semester, with hash/Back/Forward and existing keyboard tab controls.
Header is compact; program/demo selectors moved to sidebar. Dashboard uses
manual transcript metrics, credit progress, actual manually recorded terms,
up to four API-eligible courses and navigation actions. It never applies VNU
grades into academic calculations. Enter grades retains manual entry/preview.
Profile has identity/source/update information, unknown fields, full transcript,
source totals, code/name search, term filter and attempt counts. Source grades
and retakes are unchanged; logout/expiry still clears personal DOM/state.
Theme/VI-EN and 390px containment preserved. Dashboard does not probe profile
on initial load; unauthenticated profile access still returns 401 as designed.

The user's latest screenshot showed the real profile/transcript loaded after
the UTF-8 fix. This is user-supplied evidence of successful display, not proof
of identity aliases, completeness, pagination or changed-source sync policy.
Do not copy the identifier/individual grades from screenshots into artifacts.
Earlier zero-real-record observations are historical; do not assume runtime
portal tables are empty now. This redesign's screenshots/tests used synthetic
data only, with personal endpoints intercepted.

New app/static/dashboard.js and workspace.css; HTML/app.js/portal.js/i18n.js
updated. tests/frontend/check_workspace.py passed actual Chrome UI navigation,
manual edits and metric reflection, source/manual isolation, search/term filters,
VI/EN, both theme buttons, 1440/390px, all five tabs, ID/panel structure, major
reset isolation and no JS exceptions. Existing check_portal.py also passed,
including login/show password/logout clearing. Screenshots reviewed (desktop
light/dark and mobile). Evidence ignored under backups/workspace_redesign_20261023/.
Ruff frontend tests, JS syntax and diff checks passed. No Python/PostgreSQL
rerun for this UI-only change; do not claim historical backend counts as new.

Report: docs/WORKSPACE_DASHBOARD_PROFILE_2026_10_23.md. No commit/push requested
or performed; all earlier local portal changes remain. Resume login module only
when user asks, preserving identity/completeness/privacy rules below.

## Worker encoding fix - 2026-10-23: reproduced Windows cp1252 pipe failure

User retried and showed POST /auth/portal 502 (no credentials supplied in chat).
Investigated the real Windows Python child stdout: encoding is cp1252. A child
writing Vietnamese JSON with ensure_ascii=False failed with exit 1 and empty
stdout; parent json.loads(empty bytes) raised, causing the observed 502 path.
Worker now writes explicitly UTF-8 to sys.stdout.buffer; parent decodes UTF-8
and supplies PYTHONIOENCODING=utf-8. Nonzero exit/empty/malformed output becomes
a safe worker_failed/worker_output_invalid code with stage-only logging; raw
stdout/stderr, credentials and real grades are never logged. API distinguishes
technical 502/504 errors from identity 401. UI has technical error wording.

27 focused integration tests passed including a REAL subprocess roundtrip with
forced cp1252 stdio and synthetic Vietnamese course/term/password strings. It
verifies the production binary writer and parent collector, not only mocks.
Five malformed/failed worker cases also verify safe diagnostics. Ruff passed.
This fixes a reproduced transport defect; live account acceptance still needs
the user retry after restart. No database/catalog/.env change or commit/push.

Final encoding-fix checks: 335 offline passed / 38 deselected (explicit HUS PDF
acceptance root), profile browser fixture regression passed, Ruff/JS syntax/
diff checks passed. Restarted the identified local Uvicorn processes with this
fix; /health and /ready both returned 200. User still needs a live UI retry.

## Login fix checkpoint - 2026-10-23: fresh authentication evidence replaces mandatory label

User tried the UI and received identity_unverified. Cause: the new worker
required an unverified exact student-ID label in portal body text, even after
the existing connector reached the transcript. Do not record the user ID from
their screenshot. No credentials were supplied to the agent during this fix.

DaotaoClient.login now proves a fresh portal authentication transaction:
context has no portal cookies before login; initial page lacks authenticated
menu; form action is HTTPS on the reviewed host with POST; matching form POST
response is 2xx/3xx and its submitted username matches the field; authenticated
menu appears and login form disappears. It returns the account verified by
that transaction. Worker uses this evidence when no labelled ID is present;
an explicit conflicting portal ID still fails closed. This is not acceptance
based solely on a client username or a nonempty transcript. Common label
variants/separate cells are accepted. Alias-to-student-ID mapping remains open.
The button now says Sign in with VNU when logged out and My profile when loaded
(localized VI/EN), addressing the user's earlier discoverability problem.

Validation: 17 focused offline integration tests passed, Ruff passed, and
tests/frontend/check_portal_auth.py used Chrome with intercepted synthetic
portal HTML to prove successful POST login without an ID label and rejection
of invalid login/status, existing cookies/menu and foreign-host forms. No real
portal login performed by the agent for this correction; user must retry UI.
Completeness=unknown/update preservation gates are unchanged. All changes stay
local; no commit/push. See the integration status document for current gates.

Final fix verification: 325 offline passed / 38 deselected with explicit HUS
PDF acceptance root; existing synthetic profile UI browser regression passed,
Ruff/JS syntax/diff checks passed. Restarted only the local project Uvicorn;
health and readiness returned 200. User should refresh with Ctrl+F5 and retry
Sign in with VNU. No new PostgreSQL regression was needed for this auth/parser
and button fix; earlier 22-pass DB evidence remains historical.

## Implementation checkpoint - 2026-10-23: portal integration local; live acceptance pending

This section supersedes earlier statements that portal implementation has not
started. User explicitly requested implementation of the agreed portal plan,
use of the GitHub frontend-design skill, and one update per completed step.
Skill `.github/skills/frontend-design/SKILL.md` was read and applied. No commit,
push or branch merge was requested or performed. Existing local documentation
changes were preserved. Work remains in the existing workspace branch.

Implemented selective connector import from `b790d6af`, source snapshot parser,
separate HUS migration `hus_20261023_03`, transactional owner/snapshot/attempt
store, auth/profile/sync/cancel/delete APIs, isolated Playwright workers and
profile dialog with source tables, VI/EN and light/dark. Source grades remain
separate from manual transcript, GPA/progress/eligibility/recommendations/chat.
Optional Playwright 1.64.1 is now installed in the project venv; dependency is
in `requirements-portal.txt`. Worker uses installed Chrome, not a downloaded
Chromium. Credentials are stdin-only to a short-lived process, never persisted.
CLI now requires explicit `--show-transcript` to print personal table content.

Migration was applied to local runtime ai07 after a custom-format pg_dump to
ignored `backups/portal_integration_20261023/before-portal.dump`. Backup exists;
do not overwrite. Four active catalog revision IDs matched before/after; no
source/catalog publication or .env changes. Runtime portal_users count was zero
at verification; no real portal records were created. The HUS repository head
and catalog publisher compatibility checks were adjusted for the new revision.
Do not revert just the migration head while leaving runtime tables mismatched.

Uvicorn was restarted hidden on http://127.0.0.1:8000. Health/readiness returned
200, unauthenticated auth/profile returned 401 with no-store. Logs and synthetic
browser screenshots/JUnit are ignored under that backup directory. Check live
readiness again on resume. Web sessions expire after 30 minutes in RAM and are
lost on app restart; persisted snapshots require fresh VNU authentication.
UI removes personal DOM/state on logout/expiry; it does not use localStorage
for profile data. Saved data deletion removes portal owner and dependent data,
revokes its sessions and prevents pending sync from restoring deleted records.
Cancellation while reading never saves; once a DB commit begins, cancellation
waits for its real result instead of falsely reporting rollback.

Final automated evidence: 323 offline passed / 38 deselected with explicit HUS
PDF acceptance root; 22 HUS PostgreSQL passed / 337 deselected on the preceding
DB regression (including 3 portal tests; later changes covered by offline/job
checks). Ruff app/tests/new migration/CLI, JS syntax and whitespace checks
passed. Chrome fixture check passed source preservation/retakes/escaping,
newest-term ordering, VI/EN, both themes, 1440/390px, delete-confirm keep and
logout DOM cleanup, no JS exceptions. Dark mobile screenshot inspected. One
existing Starlette/httpx deprecation warning remains. No legacy PostgreSQL
rerun or live portal login through the new API was performed.

IMPORTANT remaining gates: the mandatory identity-label rule described in the
original implementation was replaced by the fresh-login checks in the newer
checkpoint above. Real identity/alias acceptance still needs a user retry.
Pagination/loading/filter completeness remains UNKNOWN.
Parser always marks completeness=unknown; first snapshot may save with warning,
same digest is idempotent, changed unknown data NEVER replaces a saved snapshot.
Consequently real changed-grade update is not accepted yet. CAPTCHA/OTP has no
dedicated interaction_required flow; generic safe error is returned. Do not
claim the first-delivery plan is fully achieved. Approximate implementation
progress reported to user: 90%, live acceptance pending.

Resume at `docs/PORTAL_INTEGRATION_STATUS_2026_10_23.md` and the original plan.
Have the user enter credentials directly into the local profile dialog, not into
chat/logs. Need an authorized live acceptance to verify actual identity source,
completeness, course/term/summary correspondence and persistent read/update/
delete/relogin. Never store credentials, cookies, raw DOM, traces/screenshots of
real grades in shared artifacts, or real records in tests/Git. Do not regenerate
retired RAG trials. Earlier RAG source-preservation instructions remain in force.

## Session close — 2026-10-23: VNU connector verified; persistent profile plan agreed

User requested review and a live trial of the teammate's `feat/login` branch.
Fetched `origin/feat/login` at `b790d6af5e3a2fa183e28dd9b08286489572c71a`.
The branch's `DaotaoClient` successfully logged into the real VNU portal,
opened student results and read 45 table rows, including 36 course rows with
grade text, using an account explicitly authorized by the user. Both synthetic
branch tests passed. A second permitted read displayed the transcript in chat.
Do not copy the credentials, student identifier or individual grades from the
conversation into memory, code, Git, fixtures or reports. Browser contexts were
closed. These trials do not establish completeness for all accounts, pagination,
CAPTCHA/OTP, or reliable authenticated identity binding for a persistent profile.

Trial runner and optional Playwright dependencies remain ignored under
`backups/login_trial_runtime/`. The runner loads the branch code using Git,
receives credentials via stdin and currently prints transcript rows if run;
do not run it into shared logs or persist its output. No credentials or real
transcript files were created. Keep future verification output minimal unless
the user explicitly asks to see their transcript. Dependencies were isolated
from the project venv requirements. No branch checkout/merge, runtime app code,
database schema/data, source catalog or .env change occurred.

The user requested an integration plan and explicitly selected:
- Localhost first, at http://127.0.0.1:8000; server deployment later.
- First delivery: VNU login, persistent account-owned profile and source
  transcript in PostgreSQL, plus a profile UI to view/update/delete that data.
- Authenticate through VNU each login; NO separate local password and NO
  storage of VNU passwords, including hashes used for reconnecting.
- No portal transcript apply into GPA/progress/eligibility/recommendations
  in this first delivery. Keep manual transcript and chat behavior separate.
- Use the user's `.github/skills/frontend-design/SKILL.md`, which was read;
  preserve existing Sổ học tập branding, light/dark and Vietnamese/English UI.
- Ask meaningful questions when needed and provide regular progress updates.

This explicit persistence request supersedes older blanket session-only rules
for portal profile/source transcripts. It does NOT authorize storing portal
credentials/cookies, chat history, or inserting real records during planning.
The existing accounts/students/course_attempts constraints require local password
hashes/catalog facts/academic outcomes that raw portal data does not provide;
the plan proposes separate owner/snapshot/attempt/session tables through a NEW
HUS migration, avoiding invented cohort mappings or password hashes.

Plan: `docs/KE_HOACH_TICH_HOP_PORTAL_BANG_DIEM_2026_10_23.md`.
Updated `modules/09-portal-transcript-import.md` and `modules/README.md` to link
the plan and reflect verified connector/new scope. All scope questions are now
answered. Implementation has NOT started; no auth/profile API, UI, migration or
persistence service has been delivered. Resume from the agreed plan when user
requests implementation; no need to ask the same scope/auth questions again.

At close, corrected Vietnamese encoding damage in the new plan and stale
pending-auth wording in module 09. Documentation link/encoding/whitespace checks
are the close-out verification, not a new app/database regression. Changes are
local/uncommitted: this memory, both module docs and the new plan. No commit/push
was requested for this session. Earlier RAG retirement/source-preservation
instructions below remain in force. User requested memory update and close.

## Session close — 2026-10-23: HUS RAG trial data removed; group plan pending

The user decided the trial chunking was not suitable and will discuss a new
approach with the team. At their request, all generated preparation data under
`backups/rag_preparation/` was deleted, including build01–07, reproduce builds,
normalized Markdown, document reviews, documents/chunks, evaluation cases and
the temporary retriage script. The generated annotation files under
`docs/acceptance/hus_preparation/` were also deleted. IDE tabs still pointing
to build06 are stale. Do not treat the former 6-document/10-chunk candidate as
an available corpus or regenerate it without a new request.

The original `crawldata` snapshot remains at
`data/hus/releases/2026-10-22-3a45aae-candidate/`: 210 files, with the
catalog SHA-256 matching its manifest. It is the retained source for the next
team discussion. The old build07 counts (6 include, 88 needs_review,
6 pending_ocr, 6 exclude) are historical observations only. In particular,
postgraduate sources may be useful, but their content and applicability have
not been verified. There is no active HUS RAG corpus, index or answering
service. No source snapshot, runtime catalog, database or `.env` was changed.

The project retains discussion material in
`docs/THONG_KE_VA_DANH_GIA_KHA_THI_RAG_HUS_2026_10_23.md` and the historical
`docs/KE_HOACH_TIEN_XU_LY_DATA_HUS.md`. The experimental
`tools/prepare_hus_corpus.py` and `tests/catalogs/test_hus_preparation.py`
remain in Git as reference code; their old review/case inputs and output
artifacts no longer exist, and their chunking configuration is not a selected
design. Do not present historical statistics as current generated data.

The user then requested a commit and push. Commit `3129f7c204da81eff74051a9d5d8fece4583b18f`
(`Document HUS RAG preparation and retired trial data`) was pushed to GitHub
`main`; remote `refs/heads/main` was independently verified at that hash.
The worktree was clean before this memory-only update. Six focused synthetic
tests, Ruff, staged diff checks and document-link checks passed for that
commit. This new memory update is local; do not claim it is already pushed.
The next substantive RAG step waits for the team's agreed data/chunking plan.

## Session close — 2026-10-23: UI published and port 8000 agreed

This section supersedes earlier notes below saying the UI changes are local,
uncommitted or not authorized for push. User requested commit, then explicitly
requested push to GitHub `main`. Both commits were successfully published:
`0a2f76c` (semester transcript and gradient themes) and `e170950`
(appearance label and Vietnamese/English interface switching). Verified remote
`refs/heads/main` and local HEAD both equal
`e170950fdd13931d3041910809be5ccb3d571ab8`; local `main` tracks `origin/main`
with no ahead/behind. Working tree was clean before this memory-only update.

User explicitly agreed to **port 8000** for running, viewing and testing the
system in subsequent sessions: **http://127.0.0.1:8000/**. Use this as the
standard frontend/API address; ports 18080 and Chrome DevTools ports in older
evidence are historical test helpers, not the user-facing runtime address.
Docker PostgreSQL remains at `127.0.0.1:5433`, database `ai07`. Keep the existing
credential files and HUS runtime configuration. Start the app when needed with:

```powershell
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The app was last verified ready with PostgreSQL during this session. Check
`/health` and `/ready` when resuming; a previous background process is not proof
the app is still running. Existing startup logs are ignored under
`backups/semester_ui_20261023/`. The visible browser was refreshed with English
UI while preserving its transcript/term/source-preview/chat session in memory.

Delivered UI: Sổ học tập branding without visible AI-07, actual academic
year/semester transcript groups newest first, gradient light/dark selector
labelled “Giao diện”, and Vietnamese/English UI selection. Appearance and
language preferences alone persist in localStorage. Source course names without
name_en, source grades and conversation content retain their original language;
the English UI explains the course-name fallback. Portal connector and source
review/apply remain unimplemented. Personal transcript sample stays ignored
under backups and must not be committed or automatically applied to ranking.

Latest language/browser regression passed; theme and semester browser evidence
is recorded below. No new Python/PostgreSQL test run, metadata publication,
live portal connection or live LLM conversation occurred at session close.
User requested memory update and close; leave this memory-only change local
until a later commit/push request. No further implementation is requested now.

## Latest UI fix — 2026-10-23: language selection and appearance label

User explicitly requested commit of the existing UI followed by fixes.
Created local commit `0a2f76c` containing the semester UI and gradient themes.
Then changed visible “Giao diện gradient” to “Giao diện” (including accessible
light/dark names), and expanded the selector from course-name language to UI
language. This correction is being recorded in a separate local commit; verify
the resulting hash with Git. No push was requested.

Root cause: selector only changed course names; the live first major exposed
65 courses with zero name_en values, so all names fell back to Vietnamese.
New `app/static/i18n.js` translates known UI copy/templates, including dynamic
renders, reversibly through WeakMap originals and MutationObserver. Language
preference alone is stored as `study-workspace-language`. Source course names
without English metadata, source grades and user/LLM chat remain unchanged;
the UI displays an explicit source-name fallback note. No runtime catalog
publication or invented course translations. Corrected what-if “Chế độ” encoding.

Committed browser regression source is `tests/frontend/check_language.mjs`;
it passed VI/EN switching, persistence, async major/API renders, name_en and
fallback branches, synthetic source preservation, recommendation/what-if,
chat window labels, theme compatibility and 390px containment, with no JS
exceptions. English screenshot inspected; JS syntax and diff checks passed.
No Python/PostgreSQL rerun or live LLM conversation for this frontend fix.
Details: `docs/LANGUAGE_UI_FIX_2026_10_23.md`. Real sample remains ignored.

## Latest UI update — 2026-10-23: selectable gradient themes

User requested gradient light/dark interfaces with regular progress reports.
Applied the GitHub frontend-design skill and local project-toolkit guidance.
Header now has an accessible Sáng/Tối selector. `app/static/theme.js` restores
the validated light/dark preference before CSS paints; first visit follows OS.
Only `study-workspace-theme` is stored in localStorage. Blocked storage still
allows switching for the session, and storage events synchronize other tabs.
Transcript/chat remain session-only and unchanged by theme switching.

`app/static/themes.css` defines light blue/lavender and dark navy/indigo/teal
gradients plus matching surfaces for transcript tables, rules, recommendation
results/forms, notices and advisor chat. Semester/year/source preview behavior
from the previous correction remains in place. No backend/data changes.

Headless Chrome checks passed for both themes, persistence, OS default versus
explicit choice, blocked storage, Enter activation, transcript preservation,
36-row source preview, 5 recommendation results per mode and chat controls.
No page overflow at 390px or JS exceptions. Ten main text/background palette
pairs measured above 4.5:1; screenshots inspected. JS syntax and diff checks
passed. No Python/PostgreSQL rerun or live LLM test for this visual change.
Report: `docs/GRADIENT_UI_2026_10_23.md`; evidence remains ignored under
`backups/semester_ui_20261023/gradient-*`. Changes local; no commit/push requested.

## Latest UI correction — 2026-10-23: actual academic terms

User rejected the fixed semester 1–12 design and provided portal screenshots
for a table grouped by actual academic year/semester/code, newest first.
This supersedes the earlier semester UI description below. Frontend now has
a continuous source preview table with STT, course code/name, credits, source
10-point/letter/4-point grades, grouped by academic year, semester and source
term code. Manual entry creates actual year/semester groups instead of a
fixed sequence. Unassigned records retain an explicit unassigned group.

User explicitly allowed their transcript as a UI sample. It exists only in an
ignored local JSON under backups, without name/student ID; do not commit real
transcript data. The browser reads a selected local JSON file into session
memory via “Mở bảng điểm mẫu”. It is a read-only preview, separate from manual
transcript, GPA/KPI and recommendations. No portal connector or review/apply
flow was implemented, no catalog matching or grade conversion was invented.
Retakes are retained as distinct source rows. Refresh clears the preview;
select the local file again to reopen it. Major change clears preview and terms.

Browser checks passed for file loading, newest-first grouping, preservation
of source grades, duplicate attempts, text escaping, invalid input rollback,
manual academic terms, major isolation and mobile containment; no JS errors.
Screenshots were inspected. Updated evidence is ignored under
`backups/semester_ui_20261023/portal-*`. A visible browser was opened with the
sample at http://127.0.0.1:8000; PostgreSQL readiness returned ok. Uvicorn was
launched as a hidden background process with local logs in that backup folder.
Syntax and diff checks passed; Python tests were not rerun after this UI-only
correction. Changes remain uncommitted; no push requested.

## Session update — 2026-10-23: semester transcript UI

User requested removal of visible AI-07 branding and a redesigned interface
using the local GitHub frontend-design skill and project-toolkit. Local changes
rename the UI to “Sổ học tập”, replace the logo/favicon and introduce actual
HTML transcript tables grouped by user-assigned semester. Course selection is
a separate collapsible catalog table. Users can add, grade, move and remove
courses. Semester metadata exists only in browser session state; API contracts
and academic catalog facts are unchanged. Records with no actual semester are
shown under “Chưa xếp học kỳ”; do not infer actual semesters from catalog order.
Year sample controls are hidden when year metadata is absent, and year filters
explicitly reject null. Switching major resets transcript, term and filters.

Chrome headless checks passed for grouping, grading, moving/removing courses,
filtering, four majors (65/67/90/68), five recommendation results and chat window
controls; no JavaScript exceptions or page overflow at 390px. Desktop/mobile
screenshots were inspected. Evidence is ignored under
`backups/semester_ui_20261023/`; design/behavior report is
`docs/SEMESTER_UI_2026_10_23.md`. JavaScript syntax and diff checks passed.
Changes remain local; no commit/push requested in this session.
Offline regression including HUS PDF acceptance: 302 passed, 35 deselected,
one existing Starlette/httpx warning. PostgreSQL tests were not rerun.

## Latest session close - 2026-10-23: main rename and PDF path correction

This section supersedes older branch names, publication targets and PDF-path failure status below. The user renamed the GitHub default branch from `codebase` to **`main`**; all future publication/integration targets are `main` unless the user says otherwise. Remote HEAD and `refs/heads/main` were verified at `e98f59c4d111c487358f2d018f6c5d997b97e62e`; remote `codebase` was absent. The earlier frontend/specification commit `e98f59c` was successfully pushed before the rename.

Local branch is now `main`, tracking `origin/main`, at the same commit with zero ahead/behind. The old local `main` at `bfcbcbc` was preserved as `archive/main-before-rename-20261023-bfcbcbc`; do not delete/reset it as part of ordinary synchronization. Local `origin/HEAD` now points to `origin/main`. A stale `origin/codebase` remote-tracking ref can remain until an explicit fetch/prune; do not treat it as the publication target. Other local branches were preserved.

All five original PDFs live in **`docs/pdf/`**; keep names, bytes and provenance intact. `tests/support/hus_acceptance.py` was updated locally to search that directory relative to the HUS expectations root, preserving exactly-one-file and SHA-256 assertions. The acceptance README and PDF review report now reference the new location. No catalog facts, PDF contents or expected academic values were changed.

Validation after the path correction: **302 passed, 35 deselected, no skipped tests**, using `python -m pytest tests -q -m "not postgres and not hus_postgres" --full-catalog-root docs/acceptance/hus_2022`. This includes all ten full_catalog_acceptance cases; the previous five missing-PDF failures are resolved locally. Ruff for the changed helper passed. One existing Starlette/httpx warning remains. No local PostgreSQL rerun or new whole-suite 337-pass claim is warranted.

Live GitHub Actions audit before this local correction confirmed run **39831744395** on `main` at `e98f59c`: offline, postgres and hus_postgres all succeeded; the final job completed at **01:29:52 Asia/Saigon on 2026-10-23**. The screenshot's yellow 2/3 did not establish a failure. That workflow excludes full_catalog_acceptance; adding an explicit acceptance job is still planned. Remote CI has not validated the uncommitted path correction yet.

`docs/KE_HOACH_CI_VA_NGHIEM_THU_MODULE.md` records verified CI evidence, module acceptance gates and the remaining roadmap. It is a local untracked plan, not implemented workflow changes. The audit plan has a current-status note marking the PDF fix complete locally. Outstanding items remain preference normalization/fallback, text/form limit precedence, null-year sample buttons, what-if baseline, advisor constraints, detailed progress UI, portal integration owned by the user's teammate, and corpus/RAG implementation. Module work remains Markdown specifications/plans only; OCR transcript is removed from scope, source PDF OCR may still be required. Catalogs remain draft_unverified and no runtime publication occurred.

At the initial close the changes were left local. The user subsequently explicitly requested **commit and push** of this PDF-path correction, related documentation, CI/module plan and memory to `origin/main`. That request supersedes the earlier instruction to leave this set uncommitted. Publication preparation starts from `e98f59c`; use Git to verify the resulting commit and remote outcome. No implementation of the remaining module/workflow plans is included in this publication.

## Session update - 2026-10-23: frontend and module documentation publication

The user requested commit and push to `origin/codebase` after the frontend redesign and documentation work. Publication preparation started from `1f95c3e`; verify Git for the resulting head and push outcome. The frontend remains FastAPI/static HTML/CSS/JavaScript and now uses a light academic workspace, responsive navigation and improved accessibility. Applied local project-toolkit and the user's `.github/skills/frontend-design` skill. Browser evidence in ignored `backups/frontend_redesign_20261023/` covers four majors (65/67/90/68 courses), tabs/keyboard/search/manual completion, recommendations/what-if and chat open/maximize. No JavaScript exceptions were observed; desktop/mobile screenshots were inspected. JavaScript syntax and diff whitespace checks passed.

The user explicitly limited module work to Markdown specifications and plans, not feature implementation. `modules/README.md` links 11 updated module specifications. Transcript OCR specification was removed and replaced by module 09 portal import; the user's teammate owns portal login/SSO/CAPTCHA/OTP and retrieval. The main system will normalize/review/apply its output; no URL or credentials are needed to continue independent planning. Modules 10/11 specify corpus release and HUS RAG. Portal import, RAG serving and the planned fixes are not implemented. Manual entry remains the fallback; transcript/chat use stays session scoped. OCR for scanned HUS source PDFs can still be needed and is separate from removed transcript OCR.

Current plans/reports: `docs/KE_HOACH_XU_LY_DATA_RAG_HUS.md`, `docs/RA_SOAT_MODULE_VA_KE_HOACH_CHINH_SUA_2026_10_23.md`, and `docs/FRONTEND_REDESIGN_2026_10_23.md`. The five original PDFs have moved from `docs/` to `docs/pdf/`; all five were compared byte-for-byte via SHA-256 with their Git originals and match. Source documents must be preserved.

Latest audit validation: **297 passed, 5 failed, 35 deselected**, with `tests --full-catalog-root docs/acceptance/hus_2022 -m "not postgres and not hus_postgres"`; Ruff on app/tests passed. All five failures arise because `tests/support/hus_acceptance.py` still searches for PDFs directly in `docs/`. This resolver fix remains planned, not performed. Do not claim current acceptance is green based on historical 337-pass runs. Other reproduced issues: preference validation on 201-character goals or 40 credits; text-derived count has no explicit precedence with form limits; year-based sample buttons operate on null years. What-if baseline revision, portal attempt policies and detailed progress UI remain planned. No PostgreSQL rerun, runtime catalog publication or live portal/LLM test occurred in this audit.

## Latest session close - 2026-10-22: crawler candidate fetched and pushed

Local `codebase` and `origin/codebase` are at `1f95c3e39f2a17453c8bf2957f7c5a35ef94c6d5` (`data: add HUS crawl candidate snapshot`), pushed successfully to GitHub. The commit contains only the crawl candidate data; `.agent/AGENTS.md` was left uncommitted and is the sole working-tree modification after the push. The fetched `origin/crawldata` snapshot is `3a45aae1732eccbb011f43428bee48add9bb718a`.

Copied the branch's crawl output into `data/hus/releases/2026-10-22-3a45aae-candidate/`: `processed/catalog.json`, 106 processed Markdown files, 101 raw HTML files, `manifest.json`, and a README. The manifest records the source commit and catalog SHA-256. This is a **candidate only**, not an approved/active release. The application does not read this path; no active pointer, crawler code merge, RAG serving integration, runtime publication, or scheduled crawl was introduced. Preserve this snapshot as immutable and create a new versioned directory for future releases.

Review findings retained in the candidate manifest: six catalog documents are `pending_ocr`; all 106 have `academic_year=null`; `data/hus/README.md` says sources are empty while `config/sources.json` contains enabled sources, which must be reconciled before any official crawl/release. The data-only commit did not run tests. `git diff --check` reports trailing whitespace in original raw HTML; keep source HTML unchanged.


## Session close - 2026-10-22: PDF-backed HUS acceptance (prior state)

This section supersedes historical Git/test status below. Local `codebase` and `origin/codebase` match commit `46e02f765d0c41ddd8d286413f5ea397cc8a362d` (`test(database): add PDF-backed HUS acceptance and remove unused schema`). The user authorized the commit/push and it succeeded. The working tree was clean before this memory-only update; leave this update local until another commit/push request.

All five technical tasks in `docs/DATABASE_TEST_IMPROVEMENT_PLAN.md` are complete. Five original PDFs, the independent 297-occurrence code/page inventory, HUS acceptance expectations, test changes and cleanup are published in that commit. Latest full combined validation after cleanup: **337 passed, zero skipped**, Ruff passed, with the existing Starlette/httpx warning. Before commit, two newly added Vietnamese strings in the source group were corrected for encoding; the 10 acceptance cases plus the inventory test were rerun: **11 passed**, Ruff passed. No full-suite rerun after that text-only correction. JUnit evidence remains under ignored `backups/catalog_acceptance_20261022/`.

Read `docs/DATABASE_TEST_IMPROVEMENT_PLAN.md` for completed work, `docs/VINH_DATABASE_TEST_REPORT.md` for test evidence, and `docs/HUS_PDF_ACCEPTANCE_REVIEW.md` for scope and unresolved academic issues. Run acceptance with an explicit tests path and `--full-catalog-root docs/acceptance/hus_2022`; without the option the ten cases still skip by design. Both legacy JSON and HUS acceptance paths remain supported.

The user confirmed cohort 2022, is the final reviewer, and does not know whether later amendments exist. Catalogs remain `draft_unverified`: automated acceptance covers the recorded assertions, not every field of every PDF row or academic validity. MAT3402 definition, MAT3325 differing prerequisites, PHI1002 effective-source confirmation and later amendments remain open. Do not invent resolutions or treat the user volunteering to review as completed sign-off.

The source export now preserves Data Science parent group V.2 with summary 28/63 versus subgroup total 57, with a PDF locator. This change has **not been published to runtime ai07**. No schema migration or runtime publication occurred in this work. Database test resources were cleaned; accounts/students/course_attempts remained empty at the last check. Cleanup removed only the unused HUS schema module and regenerable artifacts/caches (about 54 MiB); original PDFs, OCR TXT/TSV, CSV/JUnit and rollback dumps remain. No new work is requested at session close.

## Current state — 2026-10-17

SE_Project is the Explainable Course Recommender (AI-07), a FastAPI application with a static web UI. The active local runtime reads four versioned HUS catalogs from PostgreSQL database `ai07` on Docker loopback port 5433. Set `STORAGE_BACKEND=postgres`, `DATABASE_MODEL=hus` and a matching `DATABASE_URL` in the ignored root `.env`. Offline ranking uses `RECOMMENDATION_LLM_ENABLED=false`. See [HUS operations](../database/HUS_RUNTIME.md) and the root [README](../README.md).

The four HUS catalogs are `draft_unverified`. The source export is `database/data/hus_source.json`; no reviewed PDF catalog acceptance is available. HUS accounts, students and course attempts are empty. Users enter grades manually in the browser; transcript and chat state are session scoped. There is no portal login/sync, OCR, or HUS document crawler/RAG. The existing course advisor is separate from that planned HUS Q&A feature.

The HUS schema uses its own migration head `hus_20261017_02`. Use `database.tools.migrate` and `database.tools.publish_catalogs`; never run root Alembic or the historical SQL import against the migrated HUS runtime. The legacy `course_recommender` database, root Alembic history, Compose service and volume remain available for rollback. Runtime storage failures do not fall back to JSON. Local credentials and backup evidence are ignored by Git.

The checked-in `data/curricula/` contains only a 65-course Data Science metadata sample. It is not the four-catalog HUS runtime source and cannot seed the whole product. Test data under `tests/support/fixtures/` is invented and must not be presented as academic source data. `.agent/KE_HOACH_DU_AN.md` is a historical plan. Dated handoffs are in [archive](archive/).

The current repository branch is `codebase`. Commit `26aeb39` (`Organize project structure and harden HUS tests`) was pushed to `origin/codebase` on 2026-10-17; the working tree was clean immediately after that push. The user explicitly designated `codebase` as the only publication target for that request. The local `origin/HEAD` still points to `main`, so do not infer the intended push target from it. See [the latest handoff](archive/2026-10-17-test-calibration-and-codebase-publish.md).

## Session update - 2026-10-21

`feat/vinh-database-tests` was merged and pushed into `origin/codebase`. Its data/source tests, prerequisite parser coverage and PDF-review evidence are included in merge commit `5dfcc0f`; the current remote head is `83a367c`.

The local HUS database was backed up to ignored `backups/vinh-database-tests-merge-20261021/`, then the four-catalog source was published. `verify_data` reported 26/26 checks and runtime read 65/67/90/68 courses. Catalogs remain `draft_unverified`.

Post-merge validation was 248 passed / 41 deselected offline, 31 passed / 258 deselected across PostgreSQL markers on a disposable PostgreSQL 16 container, and 24 passed for the HUS-only integration group. Ruff, `git diff --check`, synthetic fixture builders and prerequisite tests under `PYTHONHASHSEED=1` and `2` passed. One existing Starlette/httpx deprecation warning remains. The ten `full_catalog_acceptance` cases still require separately reviewed source data.

Database-test improvements are uncommitted: publisher mid-transaction rollback and concurrent-publication tests, deterministic prerequisite branch coverage, named integrity-check assertions, CI JUnit artifacts and test README updates. They modify only `.github/workflows/checks.yml` and `tests/database/`; they do not alter runtime code, source catalogs or schema. Do not overwrite, commit or push them unless the user requests it.

## Session close - 2026-10-22: HUS metadata plan review

Current local branch is `codebase` at `442819d`, matching `origin/codebase` at the last local check. The latest fetched `origin/feat/vinh-database-tests` is `8c60434` (`Improve source-backed HUS metadata and bilingual course names`); `origin/fix/hus-metadata-vi-en-20261021` pointed to the same commit. This newer metadata commit has **not** been merged into local `codebase`, committed here, pushed from this session, or published to the local HUS database by this session. Do not confuse this with the earlier database-test merge recorded above.

The user requested a read-only review of that branch against `docs/KE_HOACH_CAI_THIEN_METADATA_HUS.md`, then asked for the completed and remaining work to be written into that plan for Vinh. The plan now has a 2026-10-22 status section and an approximate **40%** overall progress estimate by phase acceptance criteria. That percentage is not academic data verification. The branch supplies `name_en` for 290/290 program-course memberships, `hours` for 282/290, source hashes/locators, selected PDF-backed name/group corrections, a draft advisory rubric, reports, and bilingual course-name UI. P0 MAT3402/MAT3325 remain unresolved; PHI1002 still needs effective-source confirmation. Full independent PDF row review, reviewer sign-off, reviewed-source acceptance data, most advisory metadata, and reproducible Git-visible runtime publication evidence remain outstanding. `row-audit.csv` has `human_review=pending`; its `core_source_consistency=matched` is assigned by the report generator from the same source export and is not independent PDF verification. Catalogs remain `draft_unverified`.

Review scope was Git code and checked-in reports. The PDFs were not independently reread; tests and the live database were not rerun. At session close, `git status` showed only `docs/KE_HOACH_CAI_THIEN_METADATA_HUS.md` modified before this memory update. The old 2026-10-21 note about uncommitted `.github/workflows/checks.yml` and `tests/database/` changes is historical; those files are currently clean. Keep both the plan update and this memory update local unless the user separately requests commit/push or a merge. `git diff --check` found no whitespace errors; Git only warned about possible LF-to-CRLF conversion.

## Session close - 2026-10-22: HUS crawler/RAG release plan

The user reviewed the `crawldata` branch and decided **not to merge it into `codebase` yet**. The fetched source snapshot is `origin/crawldata` at `cc239f0`; `origin/codebase` was `442819d` at the audit. The branches have diverged (26 commits on `codebase`, 49 on `crawldata` since merge base `0ad1f815`). The crawler code includes extraction and classification for four majors plus `general`, but no committed `data/hus/processed/catalog.json` or completed RAG serving path. A teammate showed the user a successful crawl result; this workspace has no run log, URL export, corpus or measured runtime. The user considered a full run potentially longer than 30 minutes and canceled the proposed clone/run. No isolated clone, crawler execution, code integration, merge, database publication or scheduler setup occurred in this session.

The current plan is [`docs/KE_HOACH_TICH_HOP_CRAWLER_RAG.md`](../docs/KE_HOACH_TICH_HOP_CRAWLER_RAG.md), with audit [`docs/HUS_CRAWLER_INTEGRATION_AUDIT.md`](../docs/HUS_CRAWLER_INTEGRATION_AUDIT.md). Both are local, untracked files. Audit completed 4/6 original checklist items: source commit/merge base, manifest, conflict review and config-level allowlist review. It still needs the teammate's run report and a real URL/content/major-label sample. Before any integration, review that evidence, offline tests and dry-run, then decide whether the crawler is ready; only then prepare a selective feature-branch integration for review. Do not merge the whole `crawldata` branch by default.

The user replaced scheduled crawling with a release model: run one official crawl to create the v1 corpus at release time, review it, then publish an immutable versioned snapshot. The application reads only the active published corpus and never crawls on startup, per request, or on a weekly schedule. Future source updates are deliberate v2/v3 releases, each with its own crawl, review and atomic switch of the active corpus; keep prior snapshots for rollback. A failed preparation or publication leaves the prior active version intact. Teammate's earlier trial run is evidence to review, not the official v1 release snapshot. The plan and audit now reflect this decision. No recurring scheduler should be introduced unless the user changes this requirement.

At this close, `git status --short` shows modified `.agent/AGENTS.md` and `docs/KE_HOACH_CAI_THIEN_METADATA_HUS.md`, plus the two untracked crawler plan/audit docs. Keep all changes local; no commit/push was requested.

## Session update - 2026-10-22: Vinh branch tested and merged locally

The user authorized a local merge of `origin/feat/vinh-database-tests` into `codebase`. The merge fast-forwarded `codebase` from `442819d` to `8c60434`; `origin/codebase` remained at `442819d` at the last check. No push or HUS runtime publication occurred. The earlier metadata-review and crawler notes above record their own audit-time state.

Commit `8c60434` was tested from an isolated Git archive: 263 passed / 41 deselected offline, 31 passed / 273 deselected across PostgreSQL markers, `verify_data` 26/26, Ruff, four synthetic fixture builders, JavaScript syntax, and `git diff --check` passed. The disposable migration databases were removed, and HUS accounts, students, and course attempts remained empty. One existing Starlette/httpx deprecation warning remains. Ten `full_catalog_acceptance` cases still need independently reviewed source data. These tests establish code and database behavior; the four catalogs remain `draft_unverified`.

## Session update - 2026-10-22: database test improvement

The five technical tasks in `docs/DATABASE_TEST_IMPROVEMENT_PLAN.md` are complete locally. P0 and activation rollback were pushed to `origin/codebase` in `7c9140e`; the distinct-bundle concurrency test was committed as `9327166`, and PostgreSQL metadata/repository/API tests as `2bf1e5c`. The latter two commits and the final report update are local until the user requests a push.

On commit `2bf1e5c`, local validation was 291 passed / 45 deselected offline, 16 passed / 320 deselected for legacy PostgreSQL, 19 passed / 317 deselected for HUS PostgreSQL; Ruff, four synthetic fixture builders and `verify_data` 26/26 passed. Ten `full_catalog_acceptance` tests were separately collected and skipped without independently reviewed source data. JUnit XML is in ignored `backups/database-tests-20261022-2bf1e5c/`; the Git-visible summary is `docs/VINH_DATABASE_TEST_REPORT.md`. PostgreSQL test database `se_project_test` remains for repeat runs; no disposable HUS database or legacy test schema remained, and HUS accounts, students and course attempts remained empty. No metadata publication to the runtime database occurred in this work.

## Session update - 2026-10-22: PDF-backed HUS acceptance

The user supplied five PDFs in `docs/`, confirmed cohort 2022, designated themself as final reviewer, and reported amendments unknown. Local work after pushed `66002cd` adds `docs/acceptance/hus_2022/hus_pdf_expectations.json`, an independent OCR/visual code-page inventory of 297 occurrences, and HUS support for the existing ten `full_catalog_acceptance` cases while retaining the legacy file-catalog path. Run with explicit `tests` path and `--full-catalog-root docs/acceptance/hus_2022`. Results: 302 offline passed (including ten source cases), 35 PostgreSQL passed, Ruff passed. Temporary HUS databases and legacy schemas were removed; accounts/students/course_attempts remain empty. Evidence/report: `docs/HUS_PDF_ACCEPTANCE_REVIEW.md` and ignored `backups/catalog_acceptance_20261022/`.

The new anomaly check found missing preservation of the Data Science summary 28/63 (PDF 105 page 8). `hus_source.json` now includes parent group V.2 (28 required, 63 offered) with locator/note; subgroup sum remains 57. This source change is local and has not been published to runtime. Catalogs remain draft_unverified: automated assertions do not certify every field or resolve MAT3402, MAT3325, PHI1002 effective-source questions or later amendments. These changes and the user PDFs are uncommitted; do not commit/push without a new user request.

## Product invariants

- Exactly one major is selected. Catalog, transcript, eligibility, progress, candidate set and recommendation stay within that major. Switching major clears transcript and recommendation chat context.
- Eligibility is deterministic and runs before ranking. Completed, blocked, foreign-major and unverified-prerequisite courses must never enter recommendations, including LLM output.
- What-if changes preference weights or ordering, never eligibility or catalog facts. Unknown metadata remains unknown.
- Recommendations must warn that offerings and official academic rules have not been fully verified. Do not invent timetables or course availability.
- Do not persist manual transcripts, chat, real student records or provider keys for this demo.

## Repository ownership

- `app/`: API, domain behavior, repository adapters and static UI. `app/db/` and root `alembic/` represent the retained legacy persistence model.
- `database/`: HUS source, schema tooling, independent migrations, publication and operational evidence.
- `tests/`: feature-organized tests. Shared pytest fixtures live in `tests/conftest.py`; synthetic data and helpers live in `tests/support/`.
- `docs/SYSTEM_SPECIFICATION.md` and `docs/DATABASE_DESIGN.md`: architecture and product decisions. Dated plans and `modules/` describe proposed work, not proof of delivery. Track current acceptance in `docs/CODEBASE_CHECKLIST.md`.

## Commands and acceptance

From the repository root, use the project `.venv` and the pinned constraints:

```powershell
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
docker compose --env-file database/.env.docker -f database/docker-compose.yml up -d --wait
python -m database.tools.migrate upgrade
python -m database.tools.publish_catalogs --dry-run
python -m database.tools.publish_catalogs
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`/health` checks the process; `/ready` checks HUS storage and catalogs. Do not overwrite existing `.env` files or delete Docker volumes. For local rollback, follow `database/HUS_RUNTIME.md`.

Default tests use synthetic fixtures and block outbound HTTP. PostgreSQL tests require an explicit `TEST_DATABASE_URL`; HUS integration tests require `HUS_TEST_DATABASE_URL` for local Docker `ai07`. The ten `full_catalog_acceptance` cases require separately reviewed source data and remain skipped without `--full-catalog-root`.

The latest pre-publication offline run was **155 passed, 37 deselected**, with one existing Starlette/httpx deprecation warning. A full collection run was **155 passed, 37 skipped**; the skipped cases require database URLs or reviewed source data. Ruff and all four synthetic catalog builder checks passed. The HUS migration test now rejects non-local, non-`ai07`, non-PostgreSQL and redirecting-query URLs before connecting. The eligibility test formerly named `real_catalog` was renamed to identify its synthetic fixture correctly. These counts are a 2026-10-17 snapshot, not proof of current full-source acceptance.

```powershell
python -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"
python -m ruff check .
python -X utf8 tools/build_catalogs.py --check --root tests/support/fixtures/catalogs
```

Use typed Python, `snake_case` names and `camelCase` JavaScript. Keep tests deterministic and mock network/model calls. Report progress as a percentage of the requested task, with completed and remaining milestones. Do not claim the whole product is complete based on infrastructure checks.

## Git and local resources

Keep secrets, `.venv/`, backups, cache, `myproject/` and `project-toolkit/` outside Git. Do not commit or push future changes unless the user requests it. Preserve the published HUS and Docker work and do not update branches other than the one the user names. The local toolkit is invoked only when the user names `project-toolkit`; then read `project-toolkit/SKILL.md` and the selected source skill without expanding task scope.

Historical session details and prior validation counts remain in [the archived handoff](archive/2026-10-17-pre-improvement-memory.md). This file records the current working rules.

## Cleanup - 2026-10-22

User requested project-toolkit cleanup. Removed unused `database/hus_db/schema.py` (no import/reference; actual HUS DDL remains in migrations), 33 disposable rendered PDF PNGs, the inactive cutover test Chrome profile, and 29 project cache directories: 524 generated files, about 54 MiB. Original PDFs, OCR TXT/TSV, CSV/JUnit evidence, database dumps, legacy migration snapshots and local toolkit were preserved. Fresh combined run after code/artifact deletion: 337 passed, no skipped cases, Ruff passed; JUnit `backups/catalog_acceptance_20261022/cleanup-regression.xml`. No commit/push or runtime publication.


## Session close - 2026-10-31: KHMTTT eligibility sign-off and publication

The user explicitly attested that the supplied KHMTTT cohort-2022 catalog under QD3568-2023 had been fully verified and requested enabling the eligibility flow. `database/data/hus_source.json` now records this as `explicit_user_attestation`, bound to PDF SHA-256 `bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab`. The builder validates program, cohort, decision, manifest status, timestamp, reviewer and source hash before promoting the catalog and evidence. KHMTTT has 67 verified courses and 67 verified prerequisite states; KHDL, Mathematics and Math-IT remain draft. This is the user's project-level sign-off, not an institutional certification.

The HUS publisher activated all four snapshots in one transaction. Current revisions: KHDL `1e16f3026204940695f12fd980609f069f74d16292d0c9c2113fa63a4cf7d6df`; KHMTTT `c46163d1629819649f9bc8d54db59156d8a46ee40deec6c6d1fdb923c731e1da`; Mathematics `c3fd78deb82af8112bb293d73b70bc7155bf4d88949f13a9ecc0e2e0b459013e`; Math-IT `c91f63613772c7262164711be47a6614fe8ccf8390d35f7e1bb71f12566885ff`. Previous active revisions remain in history for rollback: KHDL `530723e8ba2d63f1e63d3bd3688249e5133ac05a56fafc897fb59b4e70928e87`; KHMTTT `b0ceec6056d5e7ca64be6d8de8a713fae90306e05f8ae3fd490facd836830481`; Mathematics `00ca88f12b446a07b2f4678351bc75ac955e626f4a7fcb654cfc64d5ae15b945`; Math-IT `3e764a62f3a4fb5a82a7b8a121dc157e334f6aeb2e63daa9b86167fd788eeeef`.

Four KHMTTT courses still have prerequisite codes outside that catalog: MAT2407, MAT3452, MAT3533 and MAT3539. Such prerequisite fulfillment and unresolved VNU transcript rows are separate from catalog verification. No account transcript or grade data was inspected.

After publication, the course board showed `program_binding_unverified`: the account-specific VNU binding must match the new catalog revision. The API now supplies program-selection options for this blocker, and the client falls back to GET `/me/academic-program` if older API output omits them. `index.html` uses a versioned `course-status.js` URL. The updated static asset was served successfully. The user has not yet completed the account confirmation; the browser form flow remains unverified. Do not bind the account or inspect transcript data for the user. The local app on port 8000 remained running (listener PID 26092, Python 3.11; `/ready` returned `ok`); it was not restarted to preserve in-memory VNU session state. User should refresh and confirm the displayed curriculum in the UI.

Commit `5d60a38` (`feat(academic): enable verified KHMTTT eligibility`) was created on local `feat/login-redesign-20261031`, which is now one commit ahead of `origin/feat/login-redesign-20261031`. To keep the earlier login redesign commit out, the academic commit was cherry-picked onto main base as `0412d03` and pushed to `feat/academic-eligibility-20261031`. Direct push to `main` was rejected by automatic review because repository instructions require a feature branch and PR; do not retry or bypass. `main` remains `c4f1e586a25532eadff8e0bea8da4f2088cd357f`. No PR was created because `gh` and a GitHub connector were unavailable. PR creation URL: https://github.com/5-Bit-System/SE_Project/pull/new/feat/academic-eligibility-20261031.

The isolated worktree remains at `C:/Users/viet cong/AppData/Local/Temp/se_project_academic_main_20261031` on local branch `codex/academic-main-20261031` at `0412d03`; it contains the pushed feature commit and is not the root working tree. Root `.agent/AGENTS.md` was already dirty before this close-out and now includes this note; `.vscode/` and `previews/` are untracked and were excluded from the commit. The scoped 12-file commit passed `git diff --check`; catalog publisher dry-run, `/ready`, `/programs`, Python compilation and JS syntax checks passed. No automated test suite was run.

## Session close - 2026-10-31: eligibility notice moved to section bottoms

The user asked to move “Dữ liệu điều kiện học có thể thay đổi; kết quả là
thông tin tham khảo. Hãy xác nhận lịch mở lớp với nhà trường.” from the top to
the bottom of the relevant page content. In `app/static/index.html`, the notice
now follows the course-status board in “Điều kiện học” and follows the readiness
message and action button in “Gợi ý kỳ tới”. Its wording and styling are
unchanged. No tests or browser visual check were run, and no app restart was
performed.

This session adds the `app/static/index.html` change to the existing dirty root
workspace on `feat/login-redesign-20261031`; no commit, push, PR or merge was
requested. `.agent/AGENTS.md` was already modified before this session, and the
untracked `.vscode/` and `previews/` directories were left untouched. This
close-out updates memory only; keep all workspace changes local unless the user
requests publication.

## Standalone HUS RAG branch history

## Authorized ten-commit feature-branch publication — 2026-11-15

User explicitly requested pushing pending changes to GitHub in10commits.
This supersedes earlier local-only/stage/commit/push restrictions for this
publication, on hus-llm-rag ONLY. Base f61b0fd matches fetched origin branch;
do not merge/rebase/forcepush/main/PR/deploy. Preserve configured genuine Git
author and previous history. Partition runtime/tests, hybridartifacts, Windows
launchers, A7 evidence, L5 evidence, source reviews, student checks, latency,
focused/intent receipts and finaldocs into10nonempty commits.

Pre-publication inventory713files~85MiB before publication safeguards. Automated
secret scan prints paths/labels only; sampleHUS_LLM_API_KEY cleared, actualbackend
.env neverread/modified. Preserve measured source/QAbytes via scoped.gitattributes
rules, no data/run/gold/checksumrewrites. One blankline import-order fix in
test_a7_successor.py; fresh38A7successor/package/launcher tests PASS, prior1072
related tests remain historical. No newGooglecalls. Fetch under approvednetwork
scope succeeded using percommand safe.directory for this repo only (sandboxGit
owner differs); no globalsafe-directory/credentialsettingschanges. Publication
plan/inventory/safetyreceipts remainignored .cache/hus/publish_20261115; final
commit count/remote equality must be verified before claiming push complete.

## Roadmap clarifies runnable legacy versus focused validation — 2026-11-15

Docs-only user update after asking whether LLM can run despite remainingsteps.
RAG_PROGRESS_AND_NEXT_PLAN.md now opens with runnable status, legacy historical
realGemini F1/F2/F3 versus focused offline/synthetic/nativehybrid-only table,
saved-key onecommand and explicit remaininglivefocused gap. Prioritize fresh
budgeted focusedlive confirmation, keep knownpronoun/IF2 fixes and groupreview/
report steps; these do not block trying existingdemo. Correct stale sentence
claiming intent/count notimplemented. No newtests/providercalls/key/envreads,
runtime/default/source/index/artifact changes or Git operations. All oldbudgets
closed and pins/runs immutable; user has NOTapproved a newlivecohort in this task.

## Focused source/context protocol implemented opt-in — 2026-11-15

User selected existing focused design row3 for implementation. Localhus-llm-rag,
no Git operations/key/env/template/providerconfig reads/downloads/Googlecalls.
Plan docs/superpowers/plans/2026-11-15-hus-focused-answer.md. New app/hus/focused.py
source resolver +boundedtopics+wholeparagraphspans; app/hus/llm/focused.py new
focused_rewrite_v1 builder/strictvalidator. HUSAnswerer(answer_policy='focused'),
serviceHUS_ANSWER_POLICY and launcher --answer-policy focused. DEFAULTlegacy/v3
unchanged; flags do notwrite.env. APInewsource_id onlyusefulinfocused, unknown/
conflictingselectionfailclosed. source_choicesrealmetadata/epochsafeUIbuttons
replayoriginalquestion/currentpermissions, noimplicitF3grant. CSSmobilewrap.

F1inventoryscope before retrieval version/variant/source/review/origin identity;
multiple scopesclarify, unknownstaysunknown, no top1/latest/CLCborrowing. Optional
parent_idtuplefilter appliedbeforeBM25/vector/hybridscoring; vectorwhereexisting
parentfilter narrows, fallbacklexical retains. No index/datacontractchanges or
skippedcanonical/inventory/indexpinchecks. F2path/facts/schema unchanged. Focused
topicdefinitions by descriptivephrases, noQID/chunkIDs/goldranking. Object+inherit,
researchquestion+scope, boundedoverfitrelatedconceptwarning andoverviewgrammar.
Missingaspect/top5definition/titleonlyfailsclosed; fullfieldusesfullscopeinventory.
Optionalkeywords/examplesonlywhen safe; unfamiliarstructure/componentconditions
(even sameline) orforwardreferencekeepwholechunk. Whole/example requestsnotcut.

Plan JSONexcludedinternalHUSAnswer.focus_plan: originalquestion/release/scope/
source, everyaspectrequiredunit, canonicalcitationrelativeoffset/hash. Citation/
quote/locator/review/factsremainoriginal. Wireomitsprivatepaths/history/key,
keepsrequiredspans; contextcopiedbeforeprovider. StrictID/schema/budgets+exact
normalizedword/operatorsequence +_atoms +orderednumericliterals (incl leading
.1)rejectextra/movednegation/conditions/universalclaims and decimalpunctuation
changes. Backendlayout/citationrendering, onlytypedHUSTextRewrite. No arbitrary
synonyms/newconnectives/freeparaphraseclaim; schema/hashnotentailmentproof.
1024outputtokens/12000promptchars/8192outputchars/capacityunchanged;429onlyoffline,
othererrorsAPI502. F3consent/AIlabelseparate. Defaultoldv2/v3readersunchanged.

Newtests test_focused_answers/retrieval/runtime +llm/test_focused_protocol/pipeline.
RED14+17 then scopedextraREDs. Broad1072PASS506.21s; focusedafterlastfix49PASS
49.29s(overlap), oldStarlettewarning. Ruff17filesclean. Browser460pxkeyboardchoice/
permission/scoperesetPASS. Minimalvenvfocused--check20API/2124menu/4hashPASS,
CSintroclarificationexpected. Reviewer review_focused_answer staticfound2important:
decimalpunctuation andconditionclosure;regressions+fixes, finalnomaterialfinding
infixedareas. No human/liveacceptanceclaim. Oldempronoun/IF2issuesNOTfixed.

NativeE5/Chroma5searchesactualhybrid/index1188901040ec83539b3c0ffe72991bd6feb8cf2737610d9ece922ebaa60d43c6
correct/no fallback. Newrun data/hus/evaluation/runs/focused_answer_offline_20261115_r2
manifestSHAde6c82c2beb208a2cf9e8c12686955ea7ab24843ce8fc4f80d203eb2a423ea0a.
Exposeddev006009014019answered1/2/1/1units;012needsclarification5choices/nosearch.
Separateexplicit2023standard012demoanswered, NOTupdatedscore. Lexicallegacy/focus
comparison samecurrentcode/snapshot, no newgold. SyntheticcopyvalidationONLY,
Google0/no latency/gainclaim.84protectedhistoricalfilesunchanged incl data/index/
CURRENT/oldruns/CSV. Review data/hus/review/focused_answer_offline_20261115_r2
CSV6humanpendingEDITABLE/receiptcreationhashonly. r1helperinvalidUIversionF2inF1
correctlyrejectedbefore native; failuresealed separately, neveroverwrite.
.cache/hus/focused_20261115/diagnose.py EXECUTEDr1failed/r2complete, NEVERrerun.
Protected.json84files/read-onlyverification. Docs/RAG_FOCUSED_ANSWER_2026_11_15.md,
quickstart/designcurrentstatus/roadmapupdated. ExistingserverNOTrestarted;
user canchooseflag. AllGooglebudgetsclosed/unusedIF2callNOTreusable; anylive
needsfreshagreement/preparedpins. Oldprotocol/runs/gold/reviews unchanged; all
oldpreparedcodepinsnowstaleafternewcorecode, donotupdateinplace.

## Intent/F2 live content review completed separately — 2026-11-15

User selected row2 REVIEW IF2-002/004 andall12, not implementation/live retry.
New data/hus/review/intent_f2_content_20261115_r1 review.json/sourcechecks/
responses_and_sources.json/AI_review.csv/manifest plus editablehumanCSV12pending.
Read frozen12live observations and preflight, currentcanonicalv4sources only;
NOinference/mockprovider/Googlecalls/env/key reads. Sixused answers facts/citations/
warnings/release/reply matchpreflight; counts90Math/67CS, lists68Toantin/65DS exact
codes/names/allreplylines, MAT1204CS/MAT3533DS3credits sourceequal. Controls4
equalpreflight/0calls.19protected pack/live/oldreview/RC24files unchangedhash.
No oldCSVedits, tests/ranking/prompt/runtimechanges or newscore/acceptanceclaim.

002oneintentpassedthenonegenHTTP200 rejected output_coverage/fact_keys. Expected
ROOTfactskeysfield/program_id/review_status/value, citation1; nestedvaluekeys
catalog_course_count/student_required_course_count/courses NOTrootkeys.90list
isbackendcapability NOTactualanswer002. NOrawoutput: don'tinferwhichmissing/
extra/duplicatekey/nestedconfusion/modelcountwrong or reconstructfrom176chars/
71tokens. Future explicitrequiredrootkeys/IDs promptproposal ONLY, notprovedfix.
004oneintentHTTP200,0gen,needsclarification; interpretation.used!=countsuccess.
BackendToantin68 andmockpreflightknown, NOTactual004answer. No rawintentJSON,
no reasonforclarifyproved. Proposed boundedimperativecountrule or examples+more
focusedclarification, keeprequired/filters/negationdistinct; NOTimplemented.

Historical11calls4intent7gen/6used0fallback unchanged, cohortclosedunused1NOT
retry/rollover. AllGooglecallsneednewagreement. FutureprepareNEWrevision:
onlychangedcodepinvsold74isvector_querylatencyrefactor; intent/prompt/validator
stillmatchlivepins. DoNOTmodifyoldpacktoupdatepins. .cache/hus/intent_f2_review_
20261115/review.py EXECUTEDone-shot, neverrerunwriter/overwritehumanCSV.
docs/RAG_INTENT_F2_CONTENT_REVIEW_2026_11_15.md androadmaprow2updatedtohuman
review/chooseimprovement, no independentreviewclaim or broadtest rerun.
No Gitstage/commit/push/PR/Actions/deploy/defaultchanges.

## Post-router content review packet completed offline — 2026-11-15

User selected row1 contentcheck, not runtimefix. Prepared NEW24AI-exposed dev
questions before inference (4career/4concept/4prereq/4ambiguous/8negative), source
inventories21F1career+21F3content+4F2 and app/hus codepins. Lexical/v4/LLMoff,
no key/env/template/providerconfig reads, Google0; realclient+socketconnect
blocked during24run. Directchat/backend review, NOTUI/hybrid/Gemini test.
11answered/7noinfo/6clarify. Function-contract23/24 NOTaccuracy/qualityscore.
31citationquote/locator/review matchcanonical;4F2raw prerequisite valuesexact.
MAT2300null remainsunknown/not-no-prereq;MAT1202Toantin/CSrawMAT2505;MAT3533DS
rawMAT2406/\nMAT2323 andunresolved preserved, noAND/ORinference. F2consentfalse,
F3AIlabel/optinkept.001017and2paraphrases clarifycurrentcontract, humanUXpending.

NewbugRC24-002 careersToantin: routecorrect/rawtop5sourcespresent, guardspecific
onlyem absentbody. Supplementarytrace originalfails; removeONLYem =>answered;
previousworkingstyleanswered. No runtimefix/stopwordaddition/validatorrelaxation.
Nextifchosen boundedpronounsyntax+positive/negative regression.018barethi still
assessmentroute, retrievalempty missingfield; currentcheckcoursepromptnotspecific.
019020negativeeligibilityguardsreject,021scope,022F3permission,023unsupported
filter,024unknownconceptsafe. F3long butin-topic; noofficial/fullcoverageclaim.

Pack data/hus/evaluation/router_content_dev_20261115_r1 manifestSHA
9aa9028e4538a00a32b80db7692b3560cbed43281d031a44b4dcf0c32fd347e7.
Run data/hus/evaluation/runs/router_content_dev_20261115_r1 manifestSHA
2bed42ef7d5902e85193d1d0250107521f4bed1d2bc03744950b8d3037466e2c.
63protected oldlogicalfilesunchanged incl latency/IF2live/current/data/index.
Review data/hus/review/router_content_dev_20261115_r1 has diagnosis/AI_review
JSON+CSV+manifest, humanreview_group_return.csvEDITABLE/24pending fieldsblank.
Receiptcreationhashonly, neverrestore humanedits. No independentreviewclaim.
docs/RAG_ROUTER_CONTENT_REVIEW_2026_11_15.md and _RESPONSES_... exactanswers;
roadmaprow1updated togroupreview/choosenarrowpronounfix, NOTallcompleted.
.cache/hus/router_content_20261115/{prepare,run,diagnose,finish_review}.py
EXECUTEDoneshot, NEVERrerunwriters/overwrite artifacts. Noproductioncodechange,
nobroadtestrerun; old53/636countsremainhistorical. AllGooglebudgetsclosed,
newcallneedsagreement, unusedIF2callNOTrollover. NoGitmutations/publication.

## Hybrid latency optimized and paired locally — 2026-11-15

User selected row4 profiling/optimization and continued. Same hus-llm-rag dirty
workspace, local only. Only production edit app/hus/vector_query.py: canonical
payload uses all dataclass fields over already-deepcopied data.chunks(), avoiding
second recursive asdict copy. Same complete hash bytes/order and mutation checks;
NOcached digest/check skipping. Four canonical checks/search, full DBinventory
read+JSON comparison, external index pin/scope/review/F3consent/E5/RRFunchanged.
No prompt/ranking/data changes. Tests5RED->green, final related173PASS/1SKIP
(Windows symlink permission), existing Starlette warning; Ruff2files clean.
Lightweight lexical/LLMoff --check20API/2124menu/4hashPASS. Google0, no downloads.

Native before profile hybrid_latency_profile_before_20261114_r1 warm6.28–6.64s,
canonical4.88–5.27s, encoding.04–.05s. Paired run data/hus/evaluation/runs/
hybrid_latency_paired_20261114_r1 manifestSHA
65589a3b6cee18c9d05c83ae65a805374d9369fd92a13e3afd4a71bc0ac60c6b.
Same v4/index1188901040ec83539b3c0ffe72991bd6feb8cf2737610d9ece922ebaa60d43c6,
currentrouter inBOTHvariants, old/new signature counterbalanced onone warmed
native runtime.20AI-exposed devquestions/60observations;10search+10no-search
eachmode. Search medianRAG6.5908634->3.3273057s (-49.5164%), lexical.0104346s.
All20old/newhybrid response/fulltraces equal;37protected logical files unchanged.
13answered/4noinfo/3clarify is statuscount NOTquality/newscore. Original20run9/6/5
unchanged. Coldnew56.484s vsbefore139.074s NOTcausal comparison; OS cache varies.
No Gemini latency/Recall gain/othermachine guarantee/humanacceptance claimed.

Summary/group CSV data/hus/review/hybrid_latency_paired_20261114_r1;20humanpending,
CSVEDITABLE, receipt creationhash only. .cache/hus/latency_profile_20261114/
profile_before.py,measure.py,summarize.py EXECUTED one-shot, NEVERrerun/overwrite
frozenruns or human CSV. protected_hashes.json37files, savedvector_query_before.py
SHA173a99f6b9c7328dbf28ff61385b989aa14fcd5534b75d30ee2dceaa61b9b361.
Future verification read-only. Reviewer review_hybrid_latency couldnotcomplete
because service usage limit; no independentreviewclaim/retryworkaround. Root
checkedcode/tests/nativeequality. Report docs/RAG_HYBRID_LATENCY_2026_11_15.md,
quickstart/roadmap/plan updated. Restart existingserver toloadcode, notdonebyagent.

Guard/editionfocuseddesign stillPROPOSAL, unimplemented. Historical IF2live result
unchanged; its preparedcodepins NOWstale duevector_querychange. Prepare NEWrevision
before futureapprovedlivecall; neverupdate oldpacket. IF2cohortclosed11/12calls,
unused1NOTrollover. All newGooglecalls needfreshagreement. No provider/config/
key/env/template reads, billing/Gitstage/commit/push/PR/Actions/deploy changes.

## Guard/edition review + focused design; intent/F2 live completed — 2026-11-14

LATEST budget supersedes previous pending entry: user explicitly approved max12
new calls in reply to question call_cb70e4fe73904ec1883ee17acd4862ca. Executed
exact pinned IF2cohort ONCE with11calls (4interpretation/7generation), allHTTP200,
actualmodelgemini-3.5-flash-lite. 6/8positive generationused,1outputerror and1
clarification;4controls0calls,0offlinefallback.21,316in/653out/21,969total tokens;
15.3919504s sumprovider time excludespacing.6used canonical/facts/citations/review/
warnings/release and reply equal preflight. No claim improved F2 prose/accuracy.

IF2-002 interpretation passed validation (generation was called), then rejected
generation output_coverage/fact_keys. Do NOT call it an intent failure. No raw
rejectedJSON saved, unknown which keys missing/extra/duplicate. API502/nooffline.
IF2-004 oneintentcall ->needs_clarification/clarification_required; nogen call,
not a successful count. report.interpretation_used=3 counts returned replymetadata
only, not actualcallcount4 (002latererrorlostresponsemetadata). Keep result honest.

Live run data/hus/evaluation/runs/intent_f2_student_live_20261114_r1 manifestSHA
3618cebce80c052b4969633da6f591ad2830cb2678dbab01b0a9f3a109e9c2f3.
12preflightpacketunchanged SHA48b8a53f77112054f5a46196d10308620d9413d2b0a2b3dcb41bc91a497b560e.
Backend helper .cache/hus/intent_f2_student_20261114/live.py --execute-once
EXECUTED; authorization.json/live_started.json/checkpoint exist. NEVERrerun or
overwrite oldrun. Runner mocked max/401/403/429/2x503 stops beforelive, no external
calls inmock. Runtime configure loaded savedbackendkey inprocess only after
explicitapproval; agentneverviewedkey/env/templates; no rawkey/errorbody/rejected
textsaved. Networkexec had approved escalation; no autoreviewrejection.

Cohort finished with1unusedcall: do NOTretry or rollover it to guard/newtask.
NewtaskGooglecalls need new agreement; no model-list/tokenizer/smoke calls.
>=5s monotonic reservationpacing enforced incode, no independentHTTPsendtimestamps.
Reviewer review_intent_f2_live_receipt independentlyverified manifests/74pins/
12prepared+11observedprompts/model/tokens/6canonicalpairs/controls/runnerauthhash;
no importantintegrityissues. No additionalprovider call byreviewer. Reviewpacket
data/hus/review/intent_f2_student_live_20261114_r1 CSVhumanfieldsblank/pending12;
CSVEDITABLE/creationhashreceipt only, neverrestore humanedits. Docs
RAG_INTENT_F2_PRACTICAL_LIVE_2026_11_14.md and _RESPONSES_... exactoutputs, roadmap
updated. No productioncode/default/key/billing/data/index/Gitpublicationchanges.

ACTIVE userrow3 asked review006019guard/012edition/009014conciseness THENdesign.
Completed review/design only, NOTnewruntime/prompt/validator. New AIreviewpacket
data/hus/review/guard_edition_design_20261114_r1 diagnostic.json/analysis.json/
review_template.csv/receipt.json;5humanpending. Trace currentlexical selected
request words/sourceinventories with sys.settrace inhelperonly, not code changes;
read historicalhybrid, NOnewhybrid/providercalls. 42quotehashes/21uniquechunks
checkedcanonical by reviewer review_guard_edition_design, noimportantfindings.

Findings:006specificonlykhai/quat, bounded overviewgrammar needed (notglobal
stopwords).019kem/thuoc absentrawtop5; unitKhái quát và điều chuẩn contains
qualified memorization/noise/train/new-data claim. Need curatedtopiccandidate,
not assert all badpredictionisoverfit.009neutralcourse_name wordset discards
doi/tuong evenwhenquestiononlyusesMAT1202, specificonlythua; unionanyword selection
misses directobjectsunit0 andaddscomposition/overview.014anypartialword selects
all5units despite directunit0 definition.012inventory5includes2015standard,
2023standard,2019high_quality,unknown/high_quality,unknown/unknown. Not justyear
ambiguity; NEVERborrowCLC/inferF1standardfromF2UI or2015==2023 equivalent.

Proposed design policy: resolvesourceedition/variant/sourcefamily beforegen;
explicitselectorfilterspreretrieval, unpinnedmultiplescopesclarify, unknownstays
unknown. Focused AnswerPlan backend-requiredaspect/fullparagraphspan closure,
noID/QID/goldbased ranking, noirrelevantunitsjustpartialtokenhits, keepconditional
exceptions/negation/modality/facts/symbols and allrequestedideas. Wholerequest or
requestedexampleskeepfullrequiredinventory; budgetnotreason tocut. Candidate
focused_rewrite_v1 keeps strict lexical/atoms coverage over requiredselected
spans, backendlayout/citation/immutablecontext, addednegative/conditions forbidden,
legacyv2/v3replayunchanged. NOTfreeparaphrase/semanticentailmentproof. Userwanted
basic-medium; firstproposal focusesanswercontext ratherthan unchecked freegen.
SourceJSONscope includesprogram_variant/source_id perreviewminorfix.

Docs RAG_GUARD_EDITION_REVIEW_2026_11_14.md and
docs/superpowers/specs/2026-11-14-hus-focused-answer-design.md clearlyPROPOSAL,
notimplemented/accepted. Runtime006019stillguardreject,012stillrankingchoice,
009014stillbroad. Next chooseimplementationoffline/newregressions thennewbudget
iflive. No claimproposalfeaturealreadyexists. .cache/hus/guard_edition_20261114/
review.py and finish.py EXECUTED one-shot, doNOToverwrite/rerunwriters. Keep old
natural20pack/run/review and preflight/usedlive artifacts immutable. No newbroad
test run for docs/data; previous636tests historical, not a new testcount here.

## Practical intent/F2 packet prepared; live budget pending — 2026-11-14

User selected roadmap row2 practical testing after router repairs. Prepared
data/hus/evaluation/intent_f2_student_20261114_r1 with cases/planned_calls/
offline_observations/preflight/review_template.csv/manifest. Manifest SHA256
48b8a53f77112054f5a46196d10308620d9413d2b0a2b3dcb41bc91a497b560e.
12cases=8F2positives/4controls across4majors, AI authored/exposed regression
wording, NOTteam-authored/independent acceptance. Synthetic provider ONLY,
Google0/no new auth yet; human/live columns blank. No production code changes.

Preflight actual AutoLLMPolicy + HUSIntentInterpreter + HUSGroundedAdapter/strict
validators with injected synthetic client, no real HUSLLMClient transport.
12planned calls=4intent+8generation;4controls0. Mathcount/list90;Toantincount/list68;
CS count67/MAT1204credits3;DS list65/MAT3533credits3. Source scoped F2 records,
not menu; studentrequiredcountnull. Controls wrongmajor, requiredcount, F3optout,
unknowncourse correctly no provider. Raw unknown phrases trigger intent4cases;
synthetic JSON chosen by expected intent, does NOTprove Gemini understanding.
F2 structured lookup, no vector/embedding/hybrid inference for this cohort.

Pins74app/hus+schema/service files, v4releaseSHA;5packet files/prompt digests,
64,137promptchars/12calls and blank human/live fields verified independently.
Proposed gemini-3.5-flash-lite, max1024outputtokens/call (12288total), input tokens/
cost unknown, >=5s between all calls, noretry/modelswitch; stop401403429 or2
consecutive503. No tokenizer/model-list/smoke calls. Key untouched/unread; any
later approved execution must use backend runtime memory only and new live out,
recheck pins, record stages/model/usage/latency/errors separately, no rejected
text/error-body/key persistence. Existing auto429-only offline policy stays.

Approval question sent via request_user_input_async: max12newcalls vs offline
packet only, because user row explicitly requires fresh agreed budget and old
budgets exhausted. At this memory write status PENDING; do not infer authorization.
Read any subsequent user reply before live work. No live runner executed or
auth marker created. .cache/hus/intent_f2_student_20261114/prepare.py one-shot
EXECUTED; don't rerun/overwrite packet. If code/pins change, create new revision.
Report docs/RAG_INTENT_F2_PRACTICAL_PREFLIGHT_2026_11_14.md and roadmap updated.
No runtime/data release/old run/gold/review edits, secret/template reads, provider
calls, Git stage/commit/push/PR/Actions or deploy. Do not rerun broad tests just
for doc/data prep; previous636runtime tests remain historical verification.

## Router grammar repair complete locally — 2026-11-14

User selected roadmap row1, bounded general syntax/router repair from natural20.
Same hus-llm-rag workspace; plan docs/superpowers/plans/2026-11-14-hus-router-
grammar-repair.md. No secret/env/template reads, Google calls, Git mutations or
data/index/prompt/output-validator/old evaluation changes.

question_routing._clause_texts NFC-normalizes and consumes ONLY accented thì
particle before folding. Original question preserved; bare thi/exams remain.
Added shared prerequisite request patterns (can/phai hoan thanh...truoc, truoc
khi hoc...phai hoc), bounded concept requests and lamviec careers. Shared field
detection prevents multi-field bypass. Bare môn is a course marker except complete
chuyen mon/bo mon/lien mon compounds (only marker context, originals kept).
ambiguous_major_request => f1/None; answering asks which major-level information
for broad orientation or major studying fields/courses, after scope checks and
only auto/no explicitfield. 001/017 NOTforced to target/gold; explicit hints kept.

program_catalog recognizes complete prefix 'neu tinh moi ma hoc phan mot lan'
as unique-code counting grammar. Other filters/negation/required-count remain
unsupported/clarify. Counts backend-owned; Math90catalog !=studentrequired.
answer_support consumes new generic concept grammar ONLY actual F3/content hits,
not domain terms/unknown topics. Raw neu...accentedthi conditions retained as
literal scoped source conditions (neu/khi/voi dieu kien prefix, including negation).
Only FULL pure study-desire wrapper exempt after established scope names/codes;
qualifier tails cannot disappear. No generic stopword/source guard relaxation.

TDD32initial18RED/14pass->green; later observed REDs for positive condition borrowing
negative source, desire tails, F1 concept-neutral leak and mon compounds. Final
53new regressions incl actual API4cases, true/unaccented exams, official facts,
conditions/negation, F3consent, named F2prereq and filters. Root final636PASS207.05s,
intermediate539PASS115.78s overlap; old Starlettewarning only. Ruff5files clean;
minimal .venv tools.run_hus_llm --check20API/2124menu/4sourcehash PASS/LLMoff/Google0.
Reviewer review_router_grammar_repair found2P2, both fixed with regression;
independent final53PASS, no important findings remaining.

New separate dev diagnostic retains original6requests:001/017 needsclarification;
002answeredF1careers;004answeredF3content/MAT2300;005F2count90;008F2prereqMAT1202
Toantin/QD3567-2023 rawMAT2505/present/draft_unverified. F2noF3consent; F3still
requiresoptin. NOTnew score, acceptance, semanticquality/latency comparison or
liveGemini proof. All30files original natural20pack/run/review SHAunchanged.
Ledger .cache/hus/router_grammar_20261114 original_hashes.json + postfix_diagnostic.
json; diagnose.py one-shot EXECUTED, don'toverwrite/rerunwriter.44doclinksvalid.
Report docs/RAG_ROUTER_GRAMMAR_REPAIR_2026_11_14.md and roadmap updated; nextgroup
contentreview, guard006019/edition012/overbroad009014, liveintent/F2 check only
with new agreedGooglebudget. Existing budgets still exhausted. No publish/deploy.

## Free intent + F2 catalog implemented locally — 2026-11-14

User selected roadmap row2: backend-validated JSON intent when rules insufficient,
count/list F2 courses by selected major/version, distinguish catalog vs required.
Plan docs/superpowers/plans/2026-11-14-hus-intent-f2-catalog.md. Local existing
hus-llm-rag workspace retained; no env/template/key reads or Google calls, Git
publication, data/release/old run/gold/review/CSV changes.

New app/hus/program_catalog.py: program_course_count/list fields, unique scoped
F2 codes (Math QD3565-2023=90), stable code/name list. Never count menu. Required
course count remains null; explicit warning not all catalog courses compulsory.
Filtered/required/elective/group/semester/topic/condition requests clarify; bounded
unfiltered request grammar. Citation quote is extracted code identities, metadata
calculation plus official_curriculum_entries pointers/release/review; not a
fabricated PDF quote of derived arithmetic. F2 evidence allowlist extended; list
of all four majors fits old prompt cap, model still selects presentation ONLY.

New app/hus/llm/intent.py: strict JSON5keys kind/dataset/field/major/course_code,
duplicate/extra/type/operation/code checks; prompt question+selectedscope+public
code/name catalog+operations only. 16k prompt chars/2048 output chars, same client
1024token cap. No question rewriting/version/permission/fact values/tools/URLs.
Codes need explicit question code or exact unique full title; existing course
hint cannot be replaced. F1 UI decision version cleared only absent explicit
edition. Raw-unknown F2 conditions/negation/conversions clarify even when JSON
selects plain facts; validated course title consumed before qualifier checks so
"ung dung" is not a prohibition. F2/rawunknown-course textual/request variant
checked against selected program BEFORE provider; no CLC->standard facts.

AutoLLMPolicy invokes interpreter only if HUS_LLM_INTENT_ENABLED=true, auto
request, no field/basic/known rule intent, baseline diagnostic routing_unknown.
Known scope/action/permission/evidence failures not reinterpreted. Gemini launcher
sets flag in PROCESS; legacy/manual/offline unchanged. May use2calls: intent then
presentation. Separate optional interpretation metadata (HUSGeneration shape),
used intent NOTproof final generation. Existing single call slot protects both;
quota rechecked after preparation and429 latched before slot release. Nonquota
errors API502, no offline substitution. Intent429 returns original offline path,
which may still clarify unknown query. UI checks both metadata for quota banner
and discloses public catalog sent for interpretation. No startup network I/O.

TDD new catalog10RED/9oldboundariespass, then intent25RED; observed regressions
for credit/count ambiguity, catalog hints blocked, unsupported qualifier/variant,
existing code hint overwrite, title mistaken for negative, UI intent429 banner.
Fixed with assertions, no validator loosened to accept model facts. Root related
177PASS125.44s, old Starlettewarning; Ruff13files clean. Minimal runtime public
tools.run_hus_llm --check passed20API/2124menu/4source hashes with LLMoff/Google0.
Reviewer review_intent_f2_catalog found3P2 (catalog lexical blockade, variant/
qualifier bypass, hint overwrite), all fixed; independent64PASS and no remaining
important issues. Minor title-token false clarification fixed with new RED test.
Final root focused/browser/scope140PASS111.88s (65new,28browser,47scope; overlap
with177, do notsum), existingwarningonly. Includes title-token RED->GREEN fix.

Docs RAG_INTENT_F2_CATALOG_2026_11_14.md, quickstart, llm README, roadmap updated.
Feature NOTliveGemini-tested; all budgets still spent. No claim all out-of-menu
questions work: raw recognized-but-wrong field, evidence guard, editions, multiple
fields, missing sources and hybrid latency remain separate tasks. Keep student
scope, Windows/Python3.11; no Git changes published. Restart launcher to use new
profile; any live test needs fresh agreed budget including intent calls.

## Natural20 lexical/hybrid diagnostic COMPLETE — 2026-11-14

User selected20naturalquestions/latency row then saidcontinue. No actualgroup
question list supplied: Codex(AI) drafted20/5permajor, explicitly NOTgroupauthored/
holdout/acceptance. Saved expectedscope/targets/sourcepacket BEFORE inference:
data/hus/evaluation/hybrid_natural20_20261114_r1 manifest
124005b9776f0882bb23c80b7ed995ddd1979a35dd5085a6354ed04731d9eb74.
One paired pass, alternating modeorder, samev4/code/index, no retry/tuning/runtime
changes. Normallexicaltop5 vs hybrid20+20->5 operationalcomparison, NOTmatched-
budgetsemanticablation. LLM OFF BY DESIGN, Google0, notquota/fallback/liveGemini.
Cold155.332819s separate;20questions40observations,9actualhybridretrievalcalls.
Run data/hus/evaluation/runs/hybrid_natural20_local_20261114_r1 manifest
a316e67ed207af1e0bb5e5417613aa0069e45ad07df2ceab91cc526f2b9ff53d.

Both9answered/6no_information/5needs_clarification.9search each/11nosearch
(3successfulF2+8blocked). SearchcaseRAG latencyLmin.0030404/median.0074816/
max.0324985s;Hmin5.7336681/median6.0581338/max6.5661236s. Same9rawtop5sets,
orderchanges009012014019; no newanswered fromhybrid; noaccuracy/Recallclaim.
Only012finalreplydiff: lexicalDOCX2023 listslevels+fields; hybridPDF2015only
levels. No editionpinnedinquestion; needsourcepolicy/contentreview, notforced
ranking/goldequivalence. Allother19repliesidentical, one observation/mode only.

Findings:002005008 conditional"thi"(accented thì) folds toexam thi androutes
F3assessment;002/005askcode,008wronglyasksF3consentforF2prereq. Separatepost-run
diagnostic removing ONLYaccentedparticle stillrouteNone, NOTafix-all.004concept
wordingunknown;001expectedobjectivesvsactualintro needswordingreview;017whole
majorwordingroutesF3/content, clarificationambiguity.005count90uniqueMathv4
catalogcodes storedexpectedonly, nochatcountimplemented/notallrequiredcourses.
006targetrank1 and019rank3foundbutguardrejects; doNOTblamevector.009rank1->2,
finalsame butoverbroadcomposition;014requestedunitpresentbutallcourseunits.
003/013/018correct4/3/3credits withsourcewarnings;008prereqNOTtestedthroughF2.
010scope/015F3optout/020missingcourseboundariesreasonable.007sourcewhitespace,
016source"du ieu"typoskept;F1unknown/F3referenceconstraintsremain.

AIreview draft data/hus/review/hybrid_natural20_20261114_r1:
analysis.json/summary.json/review_group_return.csv;20humanpending/name/dateblank.
CSV EDITABLE; sources edition derivedfromcanonical metadata, correction during
draftpreparation ONLY, no rawrun/question/expected/humanfieldchange. Nohuman
authorship/reviewinvented; CSVhashinreceipt creationonly, don'trestoreafteredits.
Docs RAG_HYBRID_NATURAL20_2026_11_14.md and
RAG_HYBRID_NATURAL20_RESPONSES_2026_11_14.md have20AIcomments/exactresponses/
rawtop5IDs. Roadmap updated: nextsyntax/router, F2count/NLunderstanding, guard/
edition/prompt, latencyprofiling andgroupreview. No runtimefix performed now.

QA data/hus/qa/20261114/hybrid_natural20_r1 manifest
9259cf84031b16ac6de23ec3b076dafa583d51e799f4c2744bbd41eb04979c05:
40pairs/9nativecalls/pins/frozenquestions/medians/sourceeditions verified,
priorhybridreceipt+13oldartifactsunchanged. Reviewer
review_hybrid_natural20_report independenthash/aggregatecheck,noimportantissues,
no inference/network/secretreads. Productiontestsnotrerun(no sourcechange).
AllGooglebudgetsstillspent, no .env/template/keyread. NoGitpublication or old
run/gold/score changes. One-shot scripts in ignored
backups/hus_hybrid_natural20_20261114 EXECUTED; doNOTrerunwriters or measure run.

## Hybrid v4 prepared/verified locally COMPLETE — 2026-11-14

User selected hybrid preparation row. Existing workspace/branch retained, no
Git publication/provider/key/env/template reads. Inline plan docs/superpowers/
plans/2026-11-14-hus-hybrid-v4.md; ledger backups/hus_hybrid_v4_20261114.
New contract/passages/index all e5_small_v4_20261114:1818parents1822passages/
vectors,4split,max392tokens. Contract7091615c6a2e8527e0eb6db362d8329c581d3c70dbfb4de24c3e4f6cac2433eb,
passages35bc48dd66d71d7cee040de95b1967c6d596f496addfd58f41ed9ac981085ef7,
INDEX1188901040ec83539b3c0ffe72991bd6feb8cf2737610d9ece922ebaa60d43c6.
New public profile data/hus/vector_profiles/hybrid_v4_20261114.json pins paths,
releaseSHA and expectedID OUTSIDE DB. Do not change old artifacts or reuse their
index with v4. Model same pinned E5 CPU384/cosine; Chroma defaultEF/telemetry off.

Runtime settings optional contract_path/passage_path (old defaults preserved);
new retrieval_profile.py configure/check/preflight. Both launchers --retrieval
lexical|hybrid (defaultlexical), --model-cache, --check. Gemini normal profile
preserves autoLLM policy, prewarms actualhybrid before serving; --check bypasses
dotenv/key and forcesLLMoff. Preflight checks release/pin/bothlegs actualhybrid,
not fallback-as-success. API /hus/config retrieval_mode is REQUESTED mode;
trace proves actualmode. Cached answerer reused after warmup. F2 exact/F3 consent
and LLM offline-only-after429 intact. No semantic routing/count fixes included.

Local .venv-hybrid and .cache/hus/multilingual-e5-small created/ignored. Seeded
from old locked optionalenv (112packages verified),9model files hashverified,
pipcheckclean; NOTcleanPyPI install. Two uv offline cache attempts lackedwheels,
did not modify lightweight .venv. Newvenv bootstrap setuptools65.5.dist-info
removed ONLYafter resolvedpath checked inside new .venv-hybrid (duplicate with
copied84.2). Existing oldenv/cache unchanged. Weights/nativeDB remainignored;
other machines need install/fetch/build or fullartifact transfer, no clone-ready
claim. Quickstart covers fresh output rebuild + profile pin update.

Real verification: existingenv freshCLI preflight actualhybrid2lexical/2vector,
cold64.749s. Same-snapshot16pairs across4majors allanswered with actualbothlegs;
4F2exact/4F3optout zero vector; wrongpin/oldcontract rejected index_identity.
Newseededenv public CLIcheck +REALloopback5HTTPchats passed; serverSTOPPED.
Cold66.560s(oldenv),156.493s(newenv); warm16queryRAG min2.966/median7.8675/
max9.262s, noGoogle. LatencyNOToptimized; not semantic/Recall/LLM quality proof.
Rollback lightweight .venv tools.run_hus_rag --check20API/2124menu/4sourcehash
PASS.13oldartifact/CURRENT hashes unchanged. Google0/modeldownloads0.

TDD7RED ->40relatedpass; expanded retrieval/runtime/query/hybrid/launcher/
package104PASS136.23s. Later profile/API/auto/diagnostic44PASS19.22s (overlap),
old Starlettewarning. Reviewer review_hybrid_v4_activation no importantfindings,
independent17pass; metadata/API/startuporder/forceoff coverage minoritems fixed.
QAdata/hus/qa/20261114/hybrid_v4_r1 manifest
312d2a67134b0a703a4e93f7d19a2da99b8e143617aa6f94f5a9cda9463d83d1,
report/bindings/comparison/newruntimeHTTP/lexicalrollback/oldhashes. New code
and artifact creationhashes bound; QAdoesnotbind later docs edits.
Doc docs/RAG_HYBRID_V4_2026_11_14.md,quickstart/README/roadmap updated. Next
naturalquery/latencycheck, semanticrouting/F2count/prompt redesign and groupreview.
All one-shot build/seed/verify/finalize scripts EXECUTED in ignored ledgerfolder;
do NOT rerunwriters/overwrite artifacts. Old budgetsexhausted, no live Gemini.
Command currentmachine:
./.venv-hybrid/Scripts/python.exe -X utf8 -m tools.run_hus_llm --retrieval hybrid
Wait Hybrid ready (can take1–3min),then127.0.0.1:8011;F3optin stillneeded.

## Block-stage diagnostics complete; hybrid chosen for next step — 2026-11-14

User selected implement diagnosis row, then asked whether BM25+Chroma hybrid is
reasonable and explicitly reminded roadmap update. Implemented diagnostics only,
NOT hybrid runtime/build. New app/hus/diagnostics.py allowlists generation codes,
safe messages and log_block. HUSDiagnostic optional in schema/HUSAnswer, omitted
whenNone; failed answers get exact branch code and optional suggested_major.
Wrongmajor names selected/requested majors and asks UI selector change, no auto
switch. Unknown routing vs unsupported program course count vs raw retrieval
empty vs supported_hits rejection distinguished. Preserve support algorithm:
snapshot bool raw hits, still call supported_hits/source_catalog as before.
F2 facts/source data unchanged; permission/clarification/evidence-unavailable
codes cover other refusals. AutoLLMUnavailable includes safe diagnostic, API502
detail {diagnostic,message}; UI only renders allowlisted local messages, not raw
body. User-facing stage label/action; manual fallback reasons still preserved.
Launcher enables hus.diagnostics INFO handler only; logs fixed
hus_chat_block code=..., no question/key/prompt/model/rawexception. Auto429
policy/concurrency guard remains. No Google/key/env/template access/edits.

TDD diagnostic7RED/1pass->8green; selected UI wrongscope/invalidoutput/timeout
regressions3green. Initial UI red run interrupted after missinglabel failure;
no full red3 claim. FINAL combined155PASS86.83s, old Starlettewarning. Ruff8files
passed. Skill-requested reviewer /root/review_block_diagnostics static review:
no important issues; reviewer could not run pytest in minimal .venv, no false
independent test claim. Root used dev interpreter under backups/hus_integration/
pr6-resolution-20261102/backups/pr6/ci-venv. Update roadmap/quickstart complete.

Hybrid direction user chose documented: F1/F3 BM25+Chroma/E5 local, sharedscope,
RRF; F2 exactstructured/counts. Existing hybrid_retrieval.py policy20+20->top5,
constant60. vector_runtime.py still points contract/passages20261105, needs v4
matching new artifacts (do not overwrite old). Both launchers STILL forcelexical;
changing .env mode alone cannot enable hybrid. Next prep contract/passages/index
v4, verify modelcache/deps/expectedID, add launcher selection, compare same15–20
natural questions. No embedding downloads/build/config switch in this turn.
Vector->lexical retrieval fallback is distinct from LLM->offline429 policy.
Roadmap now prioritizes hybrid prep; routing/count/semantic prompts still pending.
Old run/gold/review/score/data unchanged, local only no Git publication.

## Automatic Gemini; offline only on429 — 2026-11-14

NEW USER preference supersedes old manual rewrite opt-in for Gemini launcher.
User explicitly chose: other network/503/key/invalid-output errors must REPORT,
not return offline. tools.run_hus_llm sets HUS_LLM_AUTO=true; backend demo forces
rewrite regardless client flag; UI hides rewrite checkbox and discloses automatic
Google use. F3 consent remains separate/reset on major change; auto remains.
New app/hus/llm/auto.py AutoLLMPolicy perprocess Event: observed429 latches
offline until restart; no model calls afterward.429mayRPMorRPD, not proof whole
quota exhausted. Guarded rewriter checks latch under existing llm_call_slot and
sets latch before releasing slot on429, closing concurrent preparation race.
Nonquota failure => AutoLLMUnavailable ->HTTP502 generic safe error, no canonical
answer returned. Clarification/basic/noevidence unchanged/no provider. Legacy
direct chat/manual and tools.run_hus_rag offline remain; no .env/defaultdisk edit.
UI quota notice clears after a successful response (tab kept through restart).

TDD: auto12RED missingmodule/flag ->17pass incl5launcher; UI3RED ->green;
race RED unexpected extra call ->fixed. FINAL relevant group77PASS75.50s,
existing Starlettewarning; Ruff5files pass. APItests force auto despite false
client flag for success/429/503; quota calls stop, facts remain, errors nooffline.
Skill-requested reviewer /root/review_auto_quota_policy spotted race, confirmed
provider-boundary fix; no important remaining findings. Minor stale notice fixed.
Quickstart/README/manualdemo/report/roadmap updated; 69doclinks/4PowerShell
blocks verified before final minor doc additions (no command changes afterward).
No actual key/env/template read or provider call; all old budgets remain spent.
Semantic/freequestion routing/count operation still pending; auto does not
remove source/field/scope guards. Local only, no stage/commit/push/PR/deploy.
Restart Ctrl+C then ./.venv/Scripts/python.exe -X utf8 -m tools.run_hus_llm,
Ctrl+F5. Older evaluation runs/score/receipt remain historical, not rewritten.

## Free-question limitations diagnosed; roadmap updated — 2026-11-14

User asks why outside-menu queries fail despite LLM and requests roadmap update,
not runtime implementation. Screenshot selects DS but asks CS course count.
Offline diagnostic in backups/hus_free_question_diagnostic_20261114.py (no
provider construction permitted) reproduces DS scope_conflict; same question
correctly scoped CS still intent(None,None)/unsupported before model. No Google
or key/env read. Docs sections3–5 now explain menu hints vs keyword parser,
missing program count, single-code/field restrictions, BM25 limitations, lexical
support gate, verbatim F1/F3 prompt/coverage and F2 style-only, no history.
Do not blame this case on BM25 or imply model ran; no all-query failure stats.
Proposed not implemented: safe LLM JSON intent fallback, explicit major change
clarification, structured counts/lists, backend-owned F2 facts, question-directed
F1/F3 synthesis + redesigned validators, bounded optional generalAI F3 distinction,
paraphrase/multi-intent handling. Keep BM25 first; semantic/hybrid if measured
retrieval gaps; ChromaDB alone cannot fix routing/operations/strict prompts.
Next steps revised for student scope,15–20natural questions, teamreview pending.
No runtime/data/run/gold/score/default/Git publication changes. All Google budgets
remain exhausted; new routing call costs must be included in future grant.

## Hide generated-AI citation clutter on UI — 2026-11-14

User explicitly requests no evidence display for AI-generated material (F3
screenshot repetitive AI cards and inline [N]). JS presentation now strips
ONLY known AI citation markers/footer lines; no backend/schema/validator/prompt/
facts/data/run/review changes. Real-source markers/links remain, including mixed
reference case and F1/F2 Gemini rewrites. One .rag-ai-notice per answer replaces
AI cards. AI-only used label "AI dien dat", note no source-below instruction;
AI-only fallback "Noi dung AI tham khao", API error reason kept. Canonical reply
and citations remain intact in API for validation; only UI text changes.
Three browser RED failures -> UI/menu26PASS, presentation/citation15PASS (41
disjoint tests total), old Starlette warning. Ruff3testfiles PASS. Helpers now
check complete source quote preservation in AI UI instead of rawreply equality.
Mixed reference test preserves real [2]/PDF, numerical42/4 and unknown [99].
Quickstart/roadmap aligned. Google0/key0, no Git publication. Ctrl+F5 refresh
loads static change; no server restart needed for this UI-only change.

## Natural course overview routing fixed — 2026-11-14

User screenshot KHDL + bothconsents: "toi muon tim hieu ve mon thi giac may tinh"
was refused before retrieval: question_intent None. New COURSE_OVERVIEW bounded
positive opening (timhieu/gioithieu/tongquan +mon/hocphan/code), after explicit
fields, routes F3/content. Shared regex removes only that request opening in
support guard, preserving name/code/qualifiers. No global token removal. Scoped
full title resolves MAT3562; consent, wrongmajor, unknowncourse, facts priority
remain intact. tests/hus/test_course_overview_request.py RED9fail/9pass ->18pass;
with routing_name_preview/routing_guards/chat_scope 129PASS, one existing
Starlette warning; Ruff3files passed. No Google/key/env access/edits, frozen data/
run/gold/review unchanged. Quickstart/roadmap updated. User running server needs
Ctrl+C then .venv/Scripts/python.exe -X utf8 -m tools.run_hus_llm (no reload).
Live Gemini with this new query not tested; no fresh budget. Local only.

Prior screenshot scope error for CS question was NOT reproduced: live API +
fresh browser correctly answered with computer_science selected, Google0.
Do not claim cache/UI cause established. Diagnostics in ignored backups.

## One-command saved-key Gemini launcher — 2026-11-14

User explicitly wants one command using already-saved key. Added
tools/run_hus_llm.py: default ROOT/.env, dotenv_values interpolate=False;
export only HUS_LLM_API_KEY/BASE_URL/MODEL, inherited env wins. Explicit launcher
forces process enabled=true/lexical/project RAG root; local settings validation
and direct Google HTTPS required. Server loopback8011, no provider startup call,
no key logging, safe generic errors. --env-file/--port supported. No saved env,
templates or actual key read by agent, no live Google, no persistent default
change. requirements-rag adds python-dotenv using existing lock1.2.4.
Five fake-env launcher tests RED5 missingmodule -> GREEN5; with existing package
tests32PASS. Quickstart/roadmap updated. Command:
.venv/Scripts/python.exe -X utf8 -m tools.run_hus_llm
Users enable UI rewrite checkbox; F3 also requires generated reference consent.
Old offline run_hus_rag remains unchanged. Local only, no Git publication.

## Student report/demo prepared locally — 2026-11-14

User selected report/demo consolidation for student scope. Added
docs/HUS_RAG_PROJECT_REPORT.md; replaced docs/HUS_RAG_MANUAL_DEMO.md with portable
Windows quickstart-based 5–7 minute script (old copy in ignored
backups/hus_report_demo_20261114/old_manual_demo.md). README/roadmap linked.
Report keeps historical23used/1fallback/6controls separate from successful
newF2singlecall; team30 stillpending, no invented names/acceptance/quality score.
Six direct-chat demo cases passed offline with socket/provider construction
forbidden; not a new browser/other-machine check. Two PowerShell blocks parsed.
QA: data/hus/qa/20261114/student_report_demo_r1, manifest
0245ac3ef04474113abda62981159b6f132cdb450c0b541d148deead4c3b6ce2:
3101 existing protected files unchanged, 39 local links checked. No provider/key/env access,
runtime/data/default changes or suite rerun; v4/lexical/off retained. All Google
budgets exhausted. Local only, no stage/commit/push/PR/Actions/deploy.
Next team fills actual course/member/contribution details and review CSV;
another member tries full source and records environment/errors in demo checklist.
Human/academic acceptance and remote-clone/other-machine checks remain pending.
One-shot dry_run.py already executed; do not rerun or overwrite saved evidence.

## Student30 preliminary AI review COMPLETE; human30 stillpending — 2026-11-14

User selected groupreview30 row. RootREADall30exactlivereplies+F1F2quote/rawfacts,
F3selectedvsreturnedunitmapping;createdSEPARATEAIannotatedgroup-returncopy,
NOTfakehumanreview. OriginalCSVall30pending/no names,verifiedbeforewrite.
Output data/hus/review/student_content_ai_draft_20261114_r1:
review_group_return.csv (EDITABLEforgroup),ai_preliminary_review.json,summary,
README. Humanfieldsblank/pending;ai_* authorCodex(AI),date2026-11-14. Source
observationhashbindingsretained. Noaggregateaccuracyregrade ornewscore. Oldrun
23used/1fallback/6controlsunchanged;newMAT2300successonlyseparatenote003.

Authoredfindings:005/011/017/023 requestedF3unitpresentbutextraoverview/neighbor
units (005extraunit4,011otherunits0/2/3,017other0/2/3,023other1/4). Enoughrequested
materialbutoverbroadanswer; doNOTcallthismissingidea/hallucination.005projection
example shouldclarifyplane-through-origin forlinearprojection/kernel;017research
example"vi"causalwording shouldclarifyillustrativeassumption/possibility. These
areAIreviewnotes,notexpertverdict/newsourceedits.001/002/007/008hardwrap/citedensity;
007"cac viec nghiencuu"and019"du ieu"typosalreadyinsource. F2credits4/3/3/3and
rawprereqnull,MAT2505,MAT3507\nMAT3514,MAT2502\nMAT2403match; noNULL=>noneorAND/OR
inference.027clarificationappropriate,versionalreadyprovidedsoaskonlymissingcode
wouldbebetterUX. Allcontrolsreasonable/no calls. F1DSunknownscope/F3AIacademic
limitsretained. NofullPDF/DOCX/webrevalidation inthisreview.

Doc docs/RAG_STUDENT30_AI_REVIEW_2026_11_14.md +roadmapupdated groupconfirmation
pending withnewcopylinks. QAdata/hus/qa/20261114/student_content_ai_review_r1
manifest e43dcc03dae7f6014ad95761a19cf6ebccf39fbb5a28ecc276e58e32b11f8f16:
3095oldfilesunchangedSHA,32F1F3quotes/8F2factschecked;newdraftfilescreationhashes
inreceiptONLY. HumanmayeditreturnCSVlater;don'trestore/overwriteuseredits orclaim
creationhashstillmatchesafterhumanreview. No realmembernamesinvented,0human
accepted/30pending,NOTindependentacademicapproval.0newGoogle/key/env/network/
runtime changes,suite notrerun,noGitpublication. Budgetsexhausted/defaultoff.
Oneoff backups/hus_student30_ai_review_20261114/prepare_review.pyEXECUTED,sealed
QAexists;DO NOTrerunwriter. No skill-driven new eval/run or runtimefix performed.

## Dedicated F2 prompt LIVE confirmation COMPLETE: usedtrue — 2026-11-14

UserAPPROVEDmax1NEWcall via call_f5bbb55748f2440f9a1543ff9dd929bd. DONE1/1,
remaining0. MAT2300NEWprompt2599charsSHA below:HTTP200,actualgemini-3.5-flash-lite,
USEDTRUE/no fallback/no validationerror,775prompt/53out/828total,1623.8128ms.
4credits/facts/citation/publichus_answerUNCHANGED,replyendswithcanonicalblock.
SinglecallconfirmsacceptedF2undernewprompt,NOTallF2reliability/academicreview/
exactoldcausality. Backend.envkeymemoryonlyAFTERgrant,no logs/keybilling/default
changes,NOretry/modelSwitch/runtimechange/suitererun. AllbudgetsSPENT.

QAdata/hus/qa/20261114/f2_prompt_confirmation_r1manifest
67569dcd6aa77fcc1e8366dbf577e9e1260b65cf2f6b44e042511d33f2264a92.
Verificationf2_prompt_confirmation_verification_r1manifest
c7af2d9bb9bd882cf7e8c7cfbd570a31dd9cf9dbbe75daadb0ec5e36f244542a:
3091oldfilesunchangedSHA/currentpinsmatch,0verificationGoogle/keyread. Old30run
23used/1fallback/6controlsandCSV/reviewunchanged,oldkindfailurekept,oldrawcause
unknown. Human30pending. DocRAG_F2_PROMPT_CONFIRMATION_2026_11_14.md,newstatusin
roadmap/README/promptdoc. Nextteamreview/reportdemo,defaultoff/v4lexical;
noGitpublication. Helperscheck.pyexecute+verify.pyunder
backups/hus_f2_prompt_confirmation_20261114_r1 EXECUTED,authorizationand
attempt_reserved.jsonEXIST;DO NOT rerunwriters/clearorreusemarkers. Newcalls
neednewexplicitbudget. DoNOTregradeoldrunbasedonnewcall.

### Preflight before approval (historical snapshot)

User selected confirmationwhenbudgeted. Freshrunner/preflight
backups/hus_f2_prompt_confirmation_20261114_r1/check.py --prepare-no-key DONE.
Source/baselineunchangedSV30-003,4credits/citations,NEWprompt2599charsSHA
018be31d2d504cbb228be18decbccd0029f68353d9a46587f6dc414360f5dcc4,
currentcodepinssaved(includeslatestUI/launcherupdates). Newasyncmax1Googlegrant
questionPENDING; NOkeyread/Googlecall. AUTH/attempt_reserved.jsonABSENT.
Ifexplicitlyapprovedrecordnewauthorization.json max_new_calls1/preflight_sha256,
then --execute-authorized-one EXACTLYONCE; no retry/model switch/cap1024/default
change,backend.envkeymemoryonly. OUTdata/hus/qa/20261114/f2_prompt_confirmation_r1.
DoNOTrerunprepareoroldrunners/markers;allpriorbudgetsSPENT. Newresultcannotprove
exactoldcause. Keepoldrun/gold/review/CSVunchanged,23/24historicremainshistoric.

## UI/Windows quickstart COMPLETE LOCAL — 2026-11-14

User selected UIAI/APIlabels,major/source flows,Windows3.11deps/keyinstructions,
--check+localchat. DONE JSfixed401/403permission,503temporary;429/timeout/source
fallbackkept. tools/run_hus_rag.py changedONLYlimitsmetadata removedstalehardcoded
A7scores,no launcherprofilechange. New3browsercases inexistingtest_llm_rewrite_ui
RED3fail->browsergroup29PASS72.40s includesmajor/late/mobile/keyboard/consents.
Citation14PASS19.16s/wrapperpackage27PASS5.55s,Ruff2pass,oldStarlettewarning.
No backend/validator/prompt/datachanges,Google0,realkey/env/templatereads0.

docs/HUS_RAG_QUICKSTART.md rewritten: Windows64/Python3.11venv,minimalreqs,
offline launcherforcesLLMoff/nodotenv; optional Gemini via processHUS_LLM_* and
uvicornapp.hus.demo:app. SecureReadHost->NetworkCredentialPasswordenvonly,
finallyremoveskey/setsflagfalse. DocsPowerShell2blocksparsedVALID(no realkey
entry/livecall). No newlauncherflag/python-dotenvdependency. READMEHUSsection
aligned,removedstale3OS/current403claims,defaultv4lexicaloffunchanged. Source
stilllocalnotremoteclone/publication. Newdoc RAG_UI_QUICKSTART_2026_11_14.md,
roadmapUIdone,nextteamreview/F2newbudget/report.

Freshminimalvenv inbackups/hus_ui_quickstart_20261114/minimal-venv Python3.11.9,
25packagesinstalledfromexistinglocalwheelhouseusingrequirements-rag.txt+lock,
pipcheckclean,NOonlinePyPIdownloadtest. Publicruntime214files copiedto
portable-source(subset,notfullclone),noenv/DB. ChildPYTHONPATH/HOMEremoved,
bogusoldroot/vector/LLMtrueoverriddenbylauncher. --checkPASS20API/2124menu/4
sourcefilehashes,0provider. ACTUALseparateloopbackserverfreshvenv/copiedsource
5HTTPchatsF1F2F3/consent/math4creditsvsDS3 passed,sourcebyteshashed,serverstopped.
Browsertoolingusesexistingdevvenv; movedruntimeusesnewminimalvenv. SAMEWindows
machine,NOTdifferentmachine/cleanOS/GitHubclone/Actions/publicdeployment.

QA data/hus/qa/20261114/ui_quickstart_r1manifest
6560d2ffddeda6118e745f36493236ffb68eff1fb9dd4b0cc198e9db98874e8e.
3083oldfilesunchangedSHA;protectedchangesONLYapp/static/hus-rag-demo.js,
tests/hus/test_llm_rewrite_ui.py,tools/run_hus_rag.py. Docs/README/memoryupdated
separately. Olddata/gold/run/review/CSVunchanged. Freshcontextreviewer no
substantivebehavior/security/instructionfindings. No trueGemini/profilekeytest
ornewqualityacceptance;human30pending,latestF2promptnotliveverified,budgetsall
spent,defaultoff. NoGitstage/commit/push/PR/Actions/ZIP/deploy.
Oneoffhelpers backups/hus_ui_quickstart_20261114/{portable.py,check_portable.py,
http_smoke.py,verify.py}ALREADYEXECUTED;sealedoutputs/inventoryexist;don'trerun
writers. Minimalvenvandportablepublicsourceleftlocalforinspection,notGitpayload.

## F2-only prompt clarification COMPLETE OFFLINE — 2026-11-14

User selected promptF2split/kindfacts/regressionfirst. DONEonlyruntimechange
app/hus/llm/prompts.py: dedicatedSYSTEM_PROMPT_F2 (F2presentationprotocolv1),
mandatoryliteral"kind":"facts",4requiredfields,style direct/explain_source,
allfactkeys/citeIDs,noextra/prose/values,untrusteddata/noactions. build_prompt
dispatchesF2HUSEvidenceBundle separately; compactF1F3 and legacyF1F3 byte/hash
unchanged. Validator/schema/facts/citation/fallback/limitsNOTchanged. Source
payloadall8F2casesunchanged. MAT2300prompt3932->2599chars,newSHA
018be31d2d504cbb228be18decbccd0029f68353d9a46587f6dc414360f5dcc4.

Newtest tests/hus/llm/test_f2_dedicated_prompt.py: TDD3fail/8pass->11pass,then
2additionalrequiredkind/budgetboundarycasesFINAL13pass. Relatedfinal42pass
(incl29diagnostic). LLMgroup680pass/1oldStarlettewarning202.97s,collectedbefore
last2tests;42group reranfinal. Ruff2filespass. Freshcontextreviewagent same
/root/review_f2_diagnostic_20261114: no substantivepromptselection/contract/
privacyfindings. Mockvalid/invalidMAT2300outputkeeps4credits/canonicalfallback.
NOnewliveGoogle/key/envcalls,NOprooflivefailurefixed; observedkindbranchdoesNOT
prove mixedpromptcausality/exactbadkind/pastcallcause. No oldrun/gold/review/CSV
edits; livebudgetsexhausted,defaultoff/v4lexical,noGitpublication.

QA data/hus/qa/20261114/f2_dedicated_prompt_r1manifest
355e9b5c3af1fdb726ac07c2fd27a3abecab0a1d0b7376e008910b1060fb74d9:
3080oldfilesunchanged,onlyprompts.pychanged,newtestadded.4F1F3wirecomparisons
identical,8F2userpayloadsidenticalandnewprompthashes. PriorpinsSTALEafterprompt
change;don'toverwrite/resealoldpins. DocRAG_F2_DEDICATED_PROMPT_2026_11_14.md,
roadmapupdated nextteamreview/newbudgetF2confirmation/UI/report. Newliveonly
withseparateexplicitbudget/currentcode/newprompt. Helpers
backups/hus_f2_prompt_20261114/{compare.py,verify.py}EXECUTED,outputssealed,
doNOTrerunwriters. old_prompts.py is prechange snapshot only.

## Fresh F2 live check COMPLETE: output_schema/kind — 2026-11-14

UserAPPROVEDmax1NEWcall via call_0c39a5692f6d47a99df6a2764b1dddaa. DONE1/1,
remaining0. NewMAT2300callHTTP200 actualgemini-3.5-flash-lite,usedfalse,
invalid_output,validation{stage:output_schema,facts_issue:kind}. Newresponsekind
missing/invalidtypeorvalue;exactrejectedvaluenotretained,don'tinferwhatitwas or
thatotherfieldsvalid. OldSV30-003branchSTILLunknown,doNOTbackfilloldrun/CSV.
Usage1058prompt/158out/1216total,2180.7372ms,prompt3932/hashUNCHANGEDbelow,
4credits/citation/canonicalfallbackEXACT. No prompt/schema/runtime/defaultchange,
no retry/modelSwitch/suitererun. Keybackend.envmemoryonlyAFTERgrant,nolog/save.

LiveQAdata/hus/qa/20261114/f2_live_check_r1manifest
19dd1599b530d2592b0e01e4d7f10e55717e56d7bedfe73c08f75a5e6ed64517.
Verification f2_live_check_verification_r1manifest
b50fd87684eb01f10d2f5c85252a356041d8fed6ab95b94128c16cdbae1efe78:
3077oldfilesunchangedSHA,currentpinsmatch,0newverificationGoogle/keyread,
oldstudent30still23used/1fallback/pendinghuman30. DocRAG_F2_LIVE_CHECK_2026_11_14.md
androadmapupdated:nextF2-onlypromptclarity/regrtest BEFOREpromptfix; currently
NOTimplemented/proven. Kindlabeljustifiesfocussedpromptclarity,doesNOTprove
mixedpromptcausedfailure. Newliveafterfixneedsnewbudget,ALLoldbudgetsSPENT.
backups/hus_f2_live_check_20261114_r1/check.py --execute-authorized-one and
verify.pyALREADYEXECUTED,sealedoutputs+authorization/attempt_reserved.jsonEXIST;
neverrerunorclear/reusemarker. PersistentLLMoff/v4lexical/noGitpublication.

### Preflight before new approval (historical snapshot)

User selected newdiagnosticlivecheckwhenbudgeted. Preparedoneoffrunner
backups/hus_f2_live_check_20261114_r1/check.py --prepare-no-key EXECUTEDONCE.
PreflightJSONcurrentpins/exactbaselineequaloldSV30-003,4credits/citations;
prompt3932chars/hashunchanged9519e93ca040b1169416f4e7a888d6bb134564b4a0d60b06e3dda32f30caf5c7.
No keyread/Googlecall;newexplicitmax1questionaskedviaasync,approvalPENDING.
DoNOTexecuteunlessnewgrantarrives. AUTH/attempt_reserved.json currentlyABSENT.
Ifapproved,recordauthorization.json max_new_calls1/preflight_sha256/userreply
before --execute-authorized-one; usecurrentbackend.envkeymemoryonly,noretry/model
switch,cap1024,defaultunchanged. OUTdata/hus/qa/20261114/f2_live_check_r1.
Don'treuseolderbudget orrerunprepare;historicalcauseunknownregardlessnewresult.

## F2 facts diagnostics COMPLETE OFFLINE; historical branch unknown — 2026-11-14

User selected offlineSV30-003MAT2300invalid_outputdiagnosis +safe diagnostic/tests,
NOnewlivebudget. DONE3runtimefiles app/hus/llm/{output,diagnostics,adapter}.py and
NEWtests/hus/llm/test_f2_output_diagnostic.py. FactsIssuefixedenum11labels bound
tooutput_json/schema/coverage/budget; labelkind/style/schema,duplicatefact/cite,
fact/cite mismatch,presentation/credentialecho,JSON/budget. No rawvalues/unknown
keys inmetadata; oldexclude_none serialization unchanged,publicgeneration/facts/
citation/fallback/errorcodesunchanged. F1/F3 pathunchanged. Prompt/schemaNOTchanged.

Confirmedcodegap: F2 json/schema/result failures and adapter echo had no stage;
coveragechecks merged reasons. Historicalrawresponseabsent,tracevalidationNone.
HistoricHTTP200finishstop695chars/255outtokens ->nottransport/outputcap; specific
pastJSON/schema/echobranchstillUNKNOWN. DoNOT claim exactcause/fixLLMquality or
reconstruct oldoutputfromnewfake. FakeMAT2300schemafailureproves4credits/exact
reply/canonicalcitationsretainedwithnewsafetracelabelonly.

TDD18fail/8pass->26pass; expandedfinal29regressionsPASS. LLMsuite668pass/1existing
Starlettewarning(191.19s,collectedbeforeminorlastmodel-echo parameter;29targeted
ranagain). Ruff4filespass. Differential61fakeoutputs oldsnapshotvsnew:4accepted,
57rejected,ALLdecisions/errorcodes/resultspreserved. Freshcontextcode reviewer
/root/review_f2_diagnostic_20261114 no substantivefindings;minormodel-echo gap
addressedbyparameterizedtest. Code review is NOThumancontent/academicreview.

QA data/hus/qa/20261114/f2_output_diagnostic_r1 manifest
fea0285646e0df21074d6746f32149f413c70ef550c791dbf985a05522790ee0.
3069/3072oldfilesunchangedSHA,only3expectedruntimechanged,newtestadded. ALLold
data/gold/runs/reviews/CSVunchanged;student30still23used/1fallback/6controls,
allhumanreviewspending. OldpinssnapshotSTALEafter3runtimeedits;don'tbackfillpins,
regradeoroverwrite artifacts.0Google/key/env/template/DB/defaultchanges,
v4lexicalLLMoff,noGitstage/commit/push/PR/deploy. Alloldbudgets spent;oldunused1
notnewtaskbudget. Nextliveonlynewexplicitbudget/currentpins/prompt;recordsafe
newbranchorusedoutput,never infer exactoldcausefromnewcall.
Doc RAG_F2_OUTPUT_DIAGNOSTIC_2026_11_14.md + roadmapupdated offlinepartdone,
nextteamreview/newbudgetdiagnostic/UI/report. One-shothelpers
backups/hus_f2_output_diagnostic_20261114/{differential.py,verify.py} EXECUTED,
outputssealed;DO NOT rerunwriters. Snapshotold_output.py isprechangevalidator,
notproductioncode. No fullHUS/repo suite or newqualitymeasurementclaimed.

## Student30 source-first/offline + LIVE24 COMPLETE; team review pending — 2026-11-14

User selected student~30contentcheck,then explicitlyAPPROVEDmax24NEW Googlecalls
(call_29c126baae8b4e68b7549d03ce1a9b39). DONE24/24/SPENT0remaining,no retry/model
switch. Model actualgemini-3.5-flash-lite all24HTTP200. F1used8/8,F2used7/8,F3used8/8,
23used/1positivefallback,6controls0calls. SV30-003MAT2300credits invalid_output
WITHOUTsafevalidationleaf/stage,rawrejectedtextNOTsaved. Fallbackexactcanonical4
credits; doNOTinfer modelchangedfactsorwhichJSONkeyfailed. NextdiagnosticOFFLINE,
newlivebudget needed,doNOTreruncase/run/markers. No runtimedata/env/default changes.
PublicRAGpromptchars99342total,cap1024/call;usage27409prompt/5761out/33170total,
allusageknown/capschecked,costunknown. Provider median1553.8343ms,min971/max2968;
singlelocalsequentialmeasurement,notbrowser/SLO. Budgetspacing>=5s byBudget,
stop401/403/429 or2consecutive503(didnottrigger). Keyrootbackend.envmemoryonly
AFTERgrant,notprinted/saved/templates/billingedited. Oldunused1callnotreused.

Sourcefirstpack data/hus/evaluation/student_content_20261114_r1 manifest
e767b24efff4e5305ef7a6470706f87184c67ee57e410b894154c3e5a60a20c6:
30questions(24positive,2F1/2F2/2F3permajor+6controls),expectationsBEFOREinference.
CoursesMAT2300Math/MAT1202MathTin/MAT1204CS/MAT2034DS. F1Math/Tin2015standard,
CS2023standard,DSunknowneditionANDvariant preservedNOTinferredstandard.
ExposedfunctionaldevnotA7/newholdout,no oldgold/run/review/scorechanges.
Offline run runs/student_content_offline_20261114_r1 manifest
b2c65c35461341264f829a412cd9cf984270655299aa0fc15928c4a724079e71:
30autochecksno flags,24SYNTHETICsourcecopyused,0fallback,0Google. Sourceaudit
32quotes/16F1F3casesALLpinnedrefscovered,F2source rows8exact. OfflineQA
qa/20261114/student_content_offline_r1 manifest
6eb27bf98a2896dad7ca2c815c30de0df927bfb0fdde717e8772eebd5ce9a0be.

LIVE run runs/student_content_live_20261114_r1 manifest
7790d63e69b6d46d7e58f040a1bb10123560c11f2dc627b3b2ae54bd0ff96980.
LiveQA qa/20261114/student_content_live_r1 manifest
000b69f6006c9ff4621ce45e47cacaf745d681d6e4e1b611aa62eb7eeaf45ca0;
verification student_content_live_verification_r1 manifest
ddc100c11e0c600ce9afef72b3556e596a6c2adc9e8caeb7b8e175efeae03b49:
3043oldfilesunchangedSHA,pinscurrent,all30canonicalunchanged,CSV/hashpendingchecks
passed,0additionalGoogle/keyread. AllhumansemanticreviewsPENDING30/human0,
no independentcontent/academic/paraphraseacceptance/defaultenableclaim.

User-facing docs RAG_STUDENT_CONTENT_30_LIVE_2026_11_14.md fullrealresponses+sources,
RAG_STUDENT_CONTENT_30_2026_11_14.md OFFLINEhistorical; roadmapupdated nextteam
review+offlineF2diagnostic+UI/README/report. TeamCSV/template/exactresponses in
data/hus/review/student_content_live_20261114_r1 (preferred) andoffline sibling
student_content_20261114_r1. Copybeforehumanedit,don'toverwrite sealedoriginals.
Livepacketmanifestfe7d4d22021a2d1e491e524f2313b66ab299a7641ff0268cfed1075dfe611177.
No newproductioncode/tests/suitererun,onlyone-offartifacthelpers. Firstfinish
asserttuplesource_rows!=JSONlist; diagnosedsameJSON/listnormalizationfixedhelper,
no runtime/expecteddatachanges. Helpersinbackups/hus_student_content_20261114
ALREADYEXECUTED: review30.py freeze/run/render,finish.py,live24.py record/execute,
live_review.py,verify_live.py. Neverrerunwriters/delete live_started.json orreuse
budget. Progressledgerlocal; noGitpublication/DB/templateaccess. Studentbasic
scope remains; successused23/24 is usability evidence,NOTteamreviewfinished.

## F1/F2/F3 evidence-first integration COMPLETE OFFLINE — 2026-11-14

User selected complete F1/F2/F3 evidence->LLM/common phrasing forstudent scope.
DONE runtime4files answer_support.py/answering.py/chat.py/question_routing.py,
4NEWtestfiles,66newtests. HUSPreparedAnswer(evidence,render_reply),prepare_evidence
selects/validates scopedF1F3sources withreplyempty; chatoptin generatesBEFORE
materialize canonicalforpublichus_answer/fallback. F2canonicalfacts/textunchanged,
statusansweredstill meansqualifiedevidence; NOunsafe bypassofsupport/sourcegates.
Legacyducktypedanswerers supported,offresponsepreserved. Nosources/ambiguity/basic/
F3optout nevercallmodel. No newmodelprotocol/validator/semanticgainclaims.

Boundedfixes:vaonam/timequestiontag;furtherstudyheadings/basisrecognition;
courseprofilelocator/muctieuhoc tap; sourceintrovsgraduate role; programmecontent
vs missingcourse; fullgreeting+benignwish; boundedstudentopenings/puregreeting
clauses. KnownF3unit titles comparedWITHSCOPEDsourceunit_index firstline before
fielddisambiguation; originalquestionretainedforretrieval/support, extraassessment
requestsremainactive,wrongcourse/optoutcannotgranttitleoverride. Matchingtitle
usesliteralcaseinsensitiveaccentedtext,notuniversalsynonymresolution.

Tests: broadLLM/language1057pass BEFOREfinaltopic/openingrefinements; subsequent
API/scope/topic/F3release181pass; fourmajoractualAPI+mockprovider24pass including
prerequisites/textconsent;FINALsupport/language/topic/evidenceflow256pass.
GroupsOVERLAP,don'tsum orclaimfullrepo. OneoldStarlettewarning,Ruff8filespass.
DEV-Q002/oldsourcepolicyquestions remainopen,oldrun/gold/reviewuntouched.
QA data/hus/qa/20261114/evidence_first_integration_r1 manifest
7d92548660e18ebe326b64d5fede6acda0c402a126f826614ccc6b7dad294800.
3032oldfilesunchangedSHA,only4expectedruntimechanged,newtest4filesadded.
DocsRAG_F1_F2_F3_INTEGRATION_2026_11_14.md + concise roadmapupdated next~30
functionalquestions/teamcontentcheck. NoGooglecalls/key/envreads/DB/defaultchange
orGitpublication. AllproviderstransportSYNTHETIC thisturn; previousF1livehistorical,
newliveF2F3notverified. LLMoff/v4lexical. Lastgrantstoppedonsuccess2/3,don'treuse
unusedone; freshlivecountneedsagreement. F3longmaybudgetfallback,wordretention
stillconservative. DoNOTrerunone-shotverify.py inbackups/hus_evidence_flow_20261114.

## Step1 F1 LIVE ACCEPTED; nested prefix fixed — 2026-11-14

User selected step1 and approved max3NEW calls (call_d50c4325fe494b15a230b111d1a872e3).
DONE2/3,STOPPEDonSUCCESS,1unused; doNOT callthird orreuseunused fornewtask.
Call1 HTTP200/output_text/b001/structure,0used. Sourceheading"## 4. ..." left
"4. ..." inprovidertext because document._PREFIX consumedone marker; exactcopy
wouldreject. Generalfix consumesrepeatedformatmarkers, restoresliteralprefix;
NOvalidator/source/fact/citation edits. Newtest_nested_source_prefix.py14cases,
TDD8fail/6pass->14pass,affectedcompact/diagnostic139pass/1oldStarlettewarning,
Ruff2filespass. RuntimeONLYapp/hus/llm/document.py changed(plusnewtest).

Call2HTTP200 actualgemini-3.5-flash-lite,generate_replyUSEDTRUE,935prompt/243out
1178total tokens,1885.2714ms,canonicalunchanged,citation1. PublicF1L5V4-Q001same
question/evidence,derivedpromptSHA38b63a525ec4f657b7cbfec13775646560a530b48df9055add328d4fae87a594.
No rawrejectedoutput/keylogs/keybilling/defaultchange. Baselinepreparedr6immutable
nowSTALEafterdocumentfix. Per-callcurrentpins/prompthashstored, sourcepackand
singlebaselineauditchecked. Firstcall2commandabortedbeforekey/marker/network
onoldpromptpreflight; correctedhelperchecksbaselinewithoutmutatingoldprepared.

QA data/hus/qa/20261114/f1_live_attempt_1 manifest
afb05c725bb8d90de13311ab11ecb3af31a6a4f00897f017304395f31bb8a39b;
attempt2manifest
70fcd599f48004d5115404ad68d9d246cce8a8598bc421af97b9a53559750ff0.
Verification f1_live_verification_r1 manifest
48029ff619e545c3fa149a0e9e9d3e69d88bfd9115cba0e4d7526919b7965508:
3027oldfilesunchangedSHA,onlydocument.pyexpectedchange. POST/hus/chat LOCAL
TestClient replay usescachedtypedacceptedliveresult:200,usedtrue,replymatcheslive,
hus_answer/citationunchanged;NOthirdGooglecall/keyread/browsercheck. Initial
socketblockpreventedWindowsasynciointernalpair; helperallowsloopbackonlyand
blocksproviderinit/externalconnect,rerunpassed. No wideroldscore/suiteclaims.
DocsRAG_F1_LLM_WORKING_2026_11_14.md,roadmapstep1done,nextF1F2F3integration.
OneF1works,NOTallF2F3orparaphrasegain; outputlargelysourcecopybycurrentcontract.
DoNOTrerunwriters backups/hus_f1_live_20261114/live.py/verify.py ormarkers.
No autoRetry/modelSwitch/defaultenable/Gitpublication. Student-scoperesetbelow
stillapplies. Followupnewlivebudgetmustbeagreed;oneunusednotpermissiontokeepcalling.

## Scope reset: student F1/F2/F3 RAG+LLM chatbot — 2026-11-14

LATEST user explicitly wants basic-to-medium student project, focused on four
MathFaculty majors/F1F2F3 answered throughLLM usingRAG. Roadmap rewritten to70
lines in docs/RAG_PROGRESS_AND_NEXT_PLAN.md. This new scope supersedes mandatory
48-case freshA7/multirunL5/L6/independentacademicreview gates for basic delivery;
old evaluation/source packets remain historical/reference, never alter scores.
Next: get one accepted liveLLM answer, then evidence->LLM integration (current
answered-first gate still IMPLEMENTED; redesign only planned), preserveF2facts,
F3AIlabel/permission,citations/scope,clarification/no-evidence/fallback. About30
functional questions(24positive+6controls), team source checking and Windows
quickstart/report sufficient basic plan. No vector/production/multiOS/DB scope.
Only roadmap+memory edited, no runtime/env/livecalls/defaultchange. Existing
budgets spent; new livecall count still needs agreement. No Gitpublication.

## New authorized1call RAG smoke COMPLETE:503/UNAVAILABLE — 2026-11-13

User requested testLLM then explicitly approved max1NEW Googlecall via question
call_f7bb326bbc82456fa8ac6520e0e33986. DONE1/1,remaining0. DoNOTretry/list/tokenizer
without newbudget. PublicF1L5V4-Q0013607chars/samefrozenprompt, requested
gemini-3.5-flash-lite/directGoogle/cap1024/no retry/model switch. HTTP503,
provider_http/UNAVAILABLE/access_issueunspecified,1985.1292ms,actualmodel/usage
unknown,0used,exactcanonicalfallback. DoNOT infer key/quota cause orLLMquality.
Backend.envHUS_LLM_API_KEY readmemoryonly AFTERgrant, no templates/body/keylogs,
key/billing/persistentdefaults unchanged. LLMoff/v4lexical/no Gitpublication.

Fresh36audit/preparedr6 currentpins match, allrecordsidenticalr5exceptbaseline
latency; r5stale remainsunchanged. r6manifest
d0bfe7a95addc56cbd735fb225ff0f2dcfefafa1cdd732f874f41ef8f97175ca.
LiveQA data/hus/qa/20261113/llm_smoke_r1 manifest
93ecbaa3754a516fd7b903f6fd5f3a3d34e3de6025bf1d94497523708a976224.
VerificationQA llm_smoke_verification_r1 manifest
9f3e7664be4c57eae337080ecb213fb8abb8c7240754219ce1a20c7915c82bfd.
3020protectedfiles unchangedSHA/currentpinsmatch. ExplicitlySYNTHETICofflineL2
generate_reply replay withfakekey/503 verifiesusedfalse/http_error/status503,
exactreply/answer; no secondlivecall/keyread. Directliveadapter smoke withprepared
baseline, NOT browser/endtoendAPI/cohortL5/L6acceptance. No runtimemutation orsuite
rerun. Doc RAG_LLM_SMOKE_2026_11_13.md +roadmap/Google diagnostic updated.
Ignoredworkdir backups/hus_llm_smoke_20261113_r1: prepare.py/live_one.py/verify.py
ALREADYexecuted,sealedoutputsandattempt_reserved.jsonEXIST. Neverrerunwriters,
execute ordelete/reusemarker. proposal/preflight pending-budgetfalse fields are
historicalpregrant snapshots; separateauthorization.json recordsnewgrant spent.
Nextliveonlywithnewbudget/currentpins;503wasnotoutput_textreject,oldb001cause
stillunknown. Allpriorbudgets includingthisone SPENT.

## A7B11failure review COMPLETE read-only; choose bounded grammar/context next — 2026-11-13

LATEST user selected review9refusals+2semanticcontrols BEFOREchoosefix. DONE
read-only rootcause review; NO runtime/test/data/gold/scorer/run/oldreview edits.
Doc docs/RAG_A7B_FAILURE_REVIEW_2026_11_13.md, roadmap nextboundedphrases/context
regression-first IFimplementationselected, NOTalreadyfixed. NewQA
data/hus/qa/20261113/a7b_failure_review_r1 manifest
a5976b33d87c9bcf51f2751b02099b3d8079a221b0372840d524099182b1898d.
3014protectedfiles unchangedSHA. No endtoendRAG/API/search/provider/socket/key/
env/DBcalls; no testsuite rerun, newscore, Googlebudget, Gitpublication. Pure
classifier/guard/directcached evidence probes only, rootAI/exposed/nonblind/human0.

Confirmedgroups:
Q001CLCunknown2018targetrank1, specific{tuyen,vao}, missingvao; editedvao->tu
samecachedhit passes. Don'tgloballyneutralizevao orborrow2012/unknownstandard.
Q009/021/033/045objectives F3specific{ho,so,tap}; missingvaries. Permissionclause
then“ho so mon CODE” isn't AI_PROFILE_LOCATOR trong/theo/tu ho so AI thamkhao.
4editedexplicitAIlocator guards pass. DoNOT letselfassertedpermission override
strictAPIboolean; topics“lap ho so”,sohoc/hoc tap requireevidence, no globaldrops.
Q014graduate_role excludesgioithieu even as “Nguon gioithieu” locator ->F1intro.
Originalquestion+goldcareershit DIRECTGUARD passes, NOTnewretrievalsuccess.
Q015routeracceptshoctapnangcao, guardretains tap absentquote; hoctiepvariantpasses.
Q027routerrecognizesnewphrase but learning_basisonlyoldFURTHER_STUDY_TERMS =>false
despite“dua tren”question/“la tien de”source; residualdua/tren. FormatPDFproofvalid.
4additionalbasisprobes preservePDF/edition2015/standard, editedhoctiep passes;
syntheticnosourcebasis/negatedbasis/wrongeditionreject. Don'tjustdropdua/tren.
Q032contenttitle“Du bao va kiem tra mo hinh” globallymatchesassessment,2fields,
presearchclarification. Quotedtitlealsofails. Keepgenuinecontent+assessmenttwofield
guard; no globalkiemtradrop/contentpriority/QIDpatch.
Q012basic_reply exactstringset, greeting+benignwishmiss. Don'tprefixmatchand
swallowlaterRAG/action/eligibilityrequest. Q036programmecomparison“noi dung”
routesF3content; no-codecheck line121 beforeF1variantguard133, wrongclarification
reason. Needprogramme/coursecontext distinction, NOTautomaticcomparisonanswer
orpositiveenumerationpolicyresolution. OldQ025/Q037/DEV-Q002 remainOPEN.

Evidence:11originalrouter/cachedtraces,8originalguard;7editedguard,1directgoldguard,
14additionalrouter,6basic,5guardboundary,4basis-scopeprobes. Editedquestions/
syntheticinmemorycounterexamples NOTregressions/fixverification/newscore; some
initialprobe deliberatelyremovedPDF locator, laterbasisprobe keptALLlocatorproof.
Don'trerunone-shotwriters backups/hus_a7b_failure_review_20261113/{diagnose.py,
probes.py,basis_boundary.py,finish_qa.py}, outputsALREADYsealed. Protectmarkers.

CachedA7B/A7Rreplay unchanged: A7BRecall22/24,F2facts12/12,complete27/36,
automaticcontrols11/12 vsboundAIsemantic10/12. DoNOTeditscoreroroldjudgments;
futureclarification-reasonmetric needscontract/pins BEFOREfreshmeasurement.
A7BstillSTALEexacttests/hus/test_a7_bounded_candidate.py frompreviousfixturefix,
runtimecode matchfrozen, L5r5stale5runtimefiles. AllGooglebudgetsspent,LLMoff,
v4/lexical/no currentvalidity/academicpromotion.80F3expertreviewpacketpending.
A7Bnowusedfordiagnosticrepairdesign=>keepasexposeddevforfuturetuning; afterfix
DIFFERENT>=48/12source-firstfreeze, no regrading. Nextchooseboundedrepair with
similar/negative regression andscope/negation/consent/basis/topic/programme checks.

## A7B48 measured/reviewed; Recall22/24, complete27/36, NOT accepted — 2026-11-13

ACTIVE user selected freshA7 afterboundedrepair and later asked continue; also
asked “a7 là cái gì” answered as RAG evaluationstage (not model). DONE sourcefirst
freeze48/12eachmajor,3F1/3F2/3F3+3controls, lexical/v4/LLMoff. OnlyAPIrequest, no
gold/chunk/field/dataset hints. RootAI/nonblind/sourceexposed/human0, NOTindependent.
Plan docs/superpowers/plans/2026-11-13-hus-a7-bounded-successor.md; doc
docs/RAG_A7_BOUNDED_REQUEST_2026_11_13.md; roadmapupdated nextreviewbeforefix.

Pack candidates/a7_bounded_request_20261113_r1 manifest
d3bf687366e7e07e60f8b9499535679ffae2510275647737a3ca3413ed556d81;
freeze2026-11-13T16:36:58.820858UTC (23:36:58Bangkok), collection
16:37:08.274302–16:37:29.413501UTC. Measurement
runs/a7_bounded_request_lexical_20261113_r1 manifest
f86649c3fddbd51443d3f5b2247f3a8c992bf8ca065e314d647327d03c364e18;
exact48observations stored BEFOREaudit/scoring. Review
reviews/a7_bounded_request_ai_20261113_r1.json; overlay
runs/a7_bounded_request_ai_review_20261113_r1 manifest
52850c206bda6c786d19f941417dccefe887c9e6e53f01fd9fe8ee71e14e9025.
QA qa/20261113/a7_bounded_request_r1 manifest
99343a1befa247563215e7aba3b8a1a58e98264cfc40cefeeea90b63dd7a6607.

Metrics RoutedRecall22/24=91.67%(incl1nocall), conditional22/23DIAGNOSTIConly,
F2sourcefacts12/12(allcredits/name/prereqs4each), completeness27/36, integrity
27/27answered/relative-sourceentailment27/27NOTacademictruth.9positive refusals:
Q001CLCintro2018targetrank1;Q014roleatunits trường,viện routesintroduction;
Q015/Q027furtherstudy has target;Q009/Q021/Q033/Q045objectives has target;
Q032contenttitle“Dự báo và kiểm tra mô hình” routesassessment/multifield,nocall.
BasicchatQ012greeting rejected. MACHINEcontrols11/12, BUT EXACTAIsemanticcontrols
10/12:Q036programmecomparison clarifies by asking coursecode, wrongreason though
statuspasses. KEEPscorer/automatic11/12 unchanged, separateboundsemantic_controls
inQA10/12; never claim controlscomplete. No scopefilter/HTTP/providererrors.
BymajorRecall6/6,5/6,5/6,6/6; complete7/9,6/9,6/9,8/9. p50~35.7ms/p95~74.2ms,
max83.5mslocalTestClient;answererpreloaded,coldfirstHTTPretained,no separatewarmup,
audit/reviewexcluded.15localbinaryroutebyte/hash/MIMEchecks9files8PDF1DOCX,
NOTnewexternaldownloads/fullvisualacademicreview.0external/provider calls.

Exposure0normalizedwordingoverlap131files incl95ASTregressionliteral inputs,
10F1targetreuse,0F2/F3recordreuse inpriorA7targets; dynamicallyassembled inputs
andsemanticconcepts NOTcertifiedunseen. FixedsourceF1/digestorderingF2/F3, no
predictionselection. HeldA7R-Q025branch/Q037history+orientation/DEV-Q002enumvcompare
remainOPEN/behaviorunchanged. NewQ025PDF2015standard/NewQ037narrowhistoryrequest
DO NOT fixoldgold orproveoldcasepass. OldA7R20/24–18/36–12/12 andA7S unchanged.

Implementationtools/hus_a7_bounded_cases.py, tests/hus/test_a7_bounded_candidate.py,
ONLYevaluate_hus_a7.pycohortregistration/pins/CLI additive.8RED->8GREEN,
113affectedevaluator/metrics tests pass,1existingStarlettewarning,scopedRuffpass.
2987/2988protected unchangedSHA, onlyoldA7evaluator file authorizedchanged;
runtime/oldtests/data/gold/runs/reviews unchanged. No broadHUSrerun, DEV-Q002fail
stillunresolved. FreshcontextcodeagentFAILEDUSAGELIMIT withoutreviewevidence;
usercontinue => AUTHORSELFREVIEW beforefreeze, NOTfreshreviewpass. Selfreview
foundnoissues/minors; assuranceweaker, no independentclaims.

IMPORTANTPOSTFREEZETESTCORRECTION: newshape test usedrealpriorwording then asserted
zerooverlap, so onceownpackexists it fails. ObservedRED1fail, fixedONLYnewtest
fixture knownstrings=set() forshapesourcecheck. Dedicatedsamecohort/exposure/
duplicatefreeze tests andPRODUCTIONBUILDERUNCHANGED. Postfixaffectedsuite113PASS,
1warning74.81s. NOmeasurementrerun/regrade/pinsrewrite. OriginalQA pinmatchtrue
isHISTORICALatseal; CURRENT A7BpinsSTALE EXACTLYtests/hus/test_a7_bounded_candidate.py
hashafterfixturefix. Runtime/scorer/data frozenunchanged. SeparateQA
qa/20261113/a7_bounded_test_isolation_r1 recordscorrectionandcachedreplay;
doNOTeditoldQA orpretendcurrentpinsmatch. L5r5 stillstaleEXACT5runtimefiles,
no extra L5prep/cohort or Google rights. Allbudgets spent,LLMoff.

Ignored backups/hus_a7_bounded_successor_20261113 contains before/logs/ledger/
freeze_measure.py --freeze-only and--measure-once BOTHalreadyDONE, marker
measurement_reserved.json EXISTS; DO NOT rerun/delete/reuseone-shotwriters.
review_exact.py,finish_qa.py,postfreeze_test_receipt.py done/newsealedoutputs,
preserveexistingbytes. No stage/commit/push/PR/Actions/deploy/privateenvkeyDBaccess.
Nextseparatestage:review9refusals +Q012/Q036semanticcontrols BEFOREchoosingfix;
don'ttuneinmeasurement. If tuningA7B, retiretodev/freshdifferent>=48/12afterfix.
80sentenceF3expertpacketstillpending/human0. No academic/currentvaliditypromotion.

## Roadmap synchronized with reviewer-packet decision — 2026-11-13

User requested docs/RAG_PROGRESS_AND_NEXT_PLAN.md update after packet preparation.
Clarified explicit no-reviewer/prepare-first choice, all80sentences pending,
fourprofile-only scope (not174/290), direct reviewer template,3flagged examples,
separate returned exact-hash review/entailment versus HUS applicability. Added
localbackups capture portability limit. Labeled oldA7R17refusals as frozen outputs,
not currentruntime after16devrepairs. Retained4nextsteps, oldscores/DEV-Q002 failure,
v4/lexical/LLMoff/r5stale5artifacts/allbudgets spent/localonly. Docs/memory only;
no new source fetch/inference/provider/key/prepare/tests or sealedartifact edits.
Companion page_id/document_view null is no connected page/account evidence or
authorization. No stage/commit/push/PR/Actions/deploy.

## Reviewer packet80sentences + official2023/cohort evidence READY — 2026-11-13

LATEST user selected sentence/example/applicability review row, then explicitly
answered NOexpertrevieweryet, preparepacketfirst. DONE preparation, NOT expert
acceptance or full entailment certification. No contact messages sent to others.
New review data/hus/review/sentence_edition_20261113_r1 manifest
5c9755787347a55663c95c774f485db63e369f7767fb01cd9df8747fca8e7203;
QA data/hus/qa/20261113/sentence_edition_r1 manifest
765e281376bcb39b241496ded68273c8643ac023b74154084bab3451ca11e3a8.
Doc docs/RAG_SENTENCE_EDITION_REVIEW_2026_11_13.md guides humanworkflow/template.

Scope FOURpreviousprofiles only:MAT1204computer_science/MAT2034data_science/
MAT2300mathematics/MAT1202mathematics_informatics.58fields=4overview18explanation
18example18objective;80sentences exactpointer/range/field-record-filehash.
51oldreferenceanchors checked source/text/rangehash;36oldcore statuses unchanged.
Allhuman/expertstatuses pending, expert0/human0, academicfalse/notapproved. Links
are fieldanchor bundles, NOT entailment of every clause. 18unitsconcepttags
separate; not all174codes/290profiles reviewed.12limitedanalytic illustrations
rootAI, not semanticregression/sourcequote/expertapproval; oldtests not rerun.
3flagged examples need wording/assumption decision, not automatic error labels:
MAT1204unit1example “because groups/measures” hypothetical attribution;
MAT2300unit2example needs nonzerogenerator; unit4projection needs plane through
origin/linear projection and specifiedcodomain. Otherconditions perfieldnotes.
NOcandidate/runtimecontent edits; futurechanges require separatecandidate,
integration/rollback. Keepv4,AI/needs_review/noacademicverification; don't mangle
oldgold/run/review for score. MAT3372 and another-majorMAT1202 are not substitutes.

NEWpublicevidence: correctHUSpage /dao-tao/bac-dai-hoc/toan-toan-ung-dung-va-tin-hoc
links4officialPDFs under /DATA/IMAGES/2024/06/. DirectGET200 all4 and EXACTBYTEequal
docs/pdfexistingcopies (19-21MB each). Viewedphysical1-2 all4,8images total;
decision3568CS/3565Math/3567MathTin/3569DS allQD-DHKHTN dated2023-10-18,
Article2 fromadmissionscohort2022. Signature/stamp visuallypresent, NOTcrypto
verification/fullPDFreview/latestvalidity. This supersedes missingdirect2023/
cohortedge in earlierreports ONLY as new evidence; no runtimeF2/F3 promotion.
IMPORTANT3568/QD-DHQGHN/2014organisation differs3568/QD-DHKHTN/2023curriculum.
S06reusehash56d751... confirmed; viewedoldcover/indeximages1-2, text52-54reread.
Cover2385/QD-DHKHTN2024-07-31 references3568/2023, indexMAT1204page52.
Stillpartialfields: publication/authorship/databases/presentation/teamwork/
autonomy notfullmapped. Other3 no approvedexactscope detailedsyllabus here.

New H26VNU2012capture has direct “2012 firstintake” INDUSTRYsentence anchored,
but NOexplicitstandardvariant=>Q001existingunknownUNCHANGED. Historicalstandard
2012node+2023cohortnode do NOT provecomplete2012->2023revision/renamechain,
firststandardintakebinding orlatestvalidity. Don'tinferfromCLC2018/noamendments.
Admissions2021stillweb502/directConnectError, indexedleadonly.6newcaptures200
(4PDF2HTML),1networkerror;7initialsandboxConnectErrors preservedseparately.
WebtoolPDFsizelimit notsitefailure; publicnetworkescalation approved/directGET
used onlypublicsources, no auth/Gemini/APIkey. Supplementaryeditionsremainseparate.

2971protectedfiles unchangedSHA; no runtime/oldtests/data/gold/runs/reviews edits.
CachedA7Rscore reproduced, LLMcodebindings matchdiagnosticreceipt; r5stillstale
5artifacts, v4/lexical/LLMoff, ALLGooglebudgets spent. No newRAG/Googleinference,
prepare/cohort/score/Gitstage/commit/push/PR/Actions/deploy or kit.
Ignored backups/hus_sentence_edition_review_20261113:before/captures/originalPDF
copies/images/build_packet.py/illustrations.py/finish_packet.py. AllwritersDONE/
SEALED; DON'Trerun/delete oldmarkers or edit sealedpacket. Initialbuild tried
LLMread_sealed on oldreviewcustomschema and stopped before writing; corrected
localhelper to verify oldschema/hash, NEVERchangedoldmanifest.
Human fills COPYofhuman_review_template.json separately with actualname/expertise/
exposure/date/manifesthash+sentencehash decisions, sourceentailment vsHUSscope
separate. Captures inbackups local NOTautomaticallyinclone/packet; URLs/hash
available, transfercapturekit separately if needed. Nextassignexpert,resolve
flaggedwording/applicabilitychain; no invented expert identity/acceptance.

## Output-text subreason diagnostic COMPLETE offline; no new Google budget — 2026-11-13

LATEST user selected diagnostic output_text then L5/L6 row. DONE diagnostic-only
runtime patch, NOT historical cause/model quality fix. Added optional strict
text_issue in HUSLLMDiagnostic only for stage output_text: blank,raw_line_break,
decoded_line_break,structure,link_or_html,restored_length. output_v3 splits same
predicates in SAMEorder with unchanged strip/doubleHTMLdecode/NFKC/schema/length/
coverage/atoms/symbol checks; code/stage/knownleaf/canonicalfallback unchanged.
Existing ObservedAdapter forwards via validated allowlist; no runner/prompt edits,
raw provider text retention, public diagnostic field, real env/key/DB/network.
Legacy missing-label exclude_none dumps unchanged. No global validator relaxation.

New tests/hus/llm/test_output_text_diagnostic.py: TDD29fail/14pass ->43pass.
Full affected tests/hus/llm + test_llm_rewrite_ui.py:607pass/0fail/0skip,
1existingStarlettewarning,168.02s. ScopedRuffpass. Original-vs-current validator
differential42synthetic cases identical decisions/results/errors ignoring additive
label:5accepted/37rejected. Finitecorpus, NOTqualitygain/entailment/liveprovider
verification. Freshcontext read-only code review0Critical/Important/Minor; no
tests independently rerun by reviewer, no academic/live/historicalcause judgment.
No broadHUS rerun needed for metadata-only change; prior2442pass/1legacyDEV-Q002
fail/2Windowssymlinkskip remains historical, suite NOT declaredgreen. Newmetadata
test verifies exact F1/F3 fallback/model/token, F2presentation unchanged, no raw
text/label in public response, no secret or rejectedtext in trace/error/traceback.

QA data/hus/qa/20261113/output_text_diagnostic_r1 manifest
d63cd2c40c1923bfa3db9210bbb65ed02e71c29cfb665dd87764b31f10e5edbd.
2963/2965protectedfiles unchanged, only app/hus/llm/{diagnostics.py,output_v3.py}
changed; newtest added separately. Oldtests/data/gold/runs/reviews untouched,
cachedA7Rscore reproduced unchanged. Currentr5 stale EXACTLY5runtime artifacts:
prior3boundedrequestfiles +these2diagnosticfiles. No newprepare/preflight/cohort.
ALLbudgets still SPENT; no live/provider/retry/modellist/tokenizer. v4/lexical/
LLMoff. HistoricalHTTP200 invalid_output/output_text/b001 reason STILLUNKNOWN:
rawoutput notretained; six futurelabels do not backfill it or prove factsreview.

Plan docs/superpowers/plans/2026-11-13-hus-output-text-diagnostic.md completed;
report docs/RAG_OUTPUT_TEXT_DIAGNOSTIC_2026_11_13.md, roadmap/Googlediagnostic
updated. Ignored backups/hus_output_text_diagnostic_20261113 preserves before
hashes/originalmodules/logs/ledger/differential; differential.py and finish_qa.py
ALREADYEXECUTED one-shot, do not rerun writers. First affected command used wrong
test_rag_ui.py path collected0tests; corrected actualpath, no product/testfix for
harness typo. LocalWIP retained, no stage/commit/push/PR/Actions/deploy.
Next L5 only with NEWbudget and freshpins/prepare/preflight; sameA/retrieval/
snapshot, actualmodel/token/latency/used/fallback +exactresponse review,1024cap,
noretry/modelswitch. L6off until actualgain/preservation/latency+operator. NextA7
separatefresh>=48/12 freeze; Q025/Q037/DEV-Q002 contracts unchanged.

## Bounded request repair after A7R COMPLETE; old contracts held — 2026-11-13

LATEST selected bounded route/syntax row IMPLEMENTED locally on hus-llm-rag WIP.
Plan docs/superpowers/plans/2026-11-13-hus-bounded-request-repair.md all4tasks done;
report docs/RAG_BOUNDED_REQUEST_REPAIR_2026_11_13.md and roadmap updated. No new
Google/key/env/DB access, data/metadata/ranking change, stage/commit/push/PR/CI/deploy.
Windows64/Py311,v4/lexical/LLMoff; ALLGooglebudgets SPENT, no new permission.

Changed3runtime: question_routing.py bounded graduate titles/workroles/teaching,
further-study heading, requested_name_languages including suffix/hintedcode and
active/refused clauses; answer_support.py bounded condition/source-subject/AI
locator/format/wholefield syntax, bare explicit ANDcondition, no global tokens;
answering.py rejects unavailableEnglishname and wires trusted resolver + lazy
eligible inventory. Format needs available source/hash/MIME/locator, PDFphysical
page. Wholefield requires all eligible stored physical-source chunks; review/origin
must not be merged OR hide other eligible parts. No academic full-source claim.
Newtests test_bounded_request_language.py + test_source_format_coverage.py =94pass.
TDD RED/GREEN logs/ledger in ignored backups/hus_bounded_request_repair_20261113.
Freshcontext review2Important suffixEnglish/crossclausenegation fixed with9RED
then94GREEN;0Critical/Minor. Reviewer did not judge academic/DOCXequivalence/
historicalgain/eacholdWIPline inside changedfiles; no such claims.

HUSoffline suite completed:2442pass/1fail/2skip/1existingStarlettewarning,
1347.59s. Command tests/hus -q -m "not postgres and not hus_postgres and not
full_catalog_acceptance"; NOTwhole repository. Solefail unchanged
test_routing_diagnostic.py::test_exposed_dev_requests_preserve_facts_scope_and_consent[DEV-Q002]
needs_clarification vs answered gold. Two skips Windows symlinkpermission.
Do NOT xfail/skip/editgold/relaxguard to call suitegreen. ScopedRuff/diffcheckpass.

One-shot finish_qa.py ALREADYEXECUTED/SEALED, don't rerun writers.
QA data/hus/qa/20261113/bounded_request_repair_r1 manifest
bc6e24374c051e596a20b9769c128024601f25c36b32990e140416dd8c318094.
2955/2959protectedfiles unchanged; ONLY3runtime + initialREDnewtest changed,
newformat test addedseparately. Oldtests/data/gold/runs/reviews immutable.
QA code_bindings + integrity + devprobe; oldA7R replay exact20/24–18/36–12/12.
Newdevprobe16exposedrequests answered, Q025/Q037 entireoldresponses identical,
DEV-Q002 stillclarifies. F2helper canonicalfactcheck, not JSONquote-in-reply.
No newscore/qualityacceptance/humanreview. A7S/A7R remainexposeddev.

IMPORTANT supersedes prior r5current statement: L5preparedr5 NOWSTALE exactly
3runtime artifacts afterthisrepair. HistoricalHTTP200access+output_text/b001
fallback remainsimmutable,0validatedused; no qualitygain/defaultactivation.
Nextseparatestage: chotseparatecontractsQ025/Q037/DEV-Q002 before newbehavior;
source-first freeze DIFFERENT>=48questions/12permajor on finalcode/config,
recordexposure/reviewer thenmeasure RoutedRecall inclnocall>=90% +facts/citation/
completeness/controls. Do not regradeA7R/dev16 or modify oldgold/receipts.
NextLLM offline output_text subreason diagnostics; rawsample not retained so
exactsubcheck unknown, no guess/relaxation. Futurelive requiresNEWbudget and
freshpins/prepare/preflight. L6off until actualgain/preservation/latency+operator.

## Rotated-key access check HTTP200, invalid_output fallback; max1 SPENT — 2026-11-13

LATEST user 'tôi vừa thay khóa' satisfied operator-replacement confirmation for
alreadyapproved conditionalmax1accesscheck. EXECUTED EXACTLY1call, now SPENT;
all oldbudgets also spent. NO additionalGooglecall/retry/smoke/tokenizer/modellist
without NEWbudget. Do not ask again if rotation happened; don't redo this call.
Independent oldkeyrevocation NOTverified, onlyoperatorreport+successfulaccess.

Fresh prepared runs/llm_v3_v4_prepared_20261113_r5 manifest
b63724a77396f582d29a75fcf17ada48a16592ecdd3bb5b7870215aed76b35b6.
36/36sourceaudits,ALL36 A/request/effective/retrieval/gold/prompt/audits exactr4,
onlypins/timing differ.0socket/provider/keyaccess duringprepare. SameF1Q001
3607prompt/SHA d0acd06dae285c783aed132cef10aab754124088bc5bbc8826a979699e0fb329,
payloadmanifest860dca... unchanged. Pinsr5 matchbefore/after/cachedverify.

Onecall directGoogle returned HTTP200, actualmodel gemini-3.5-flash-lite,
934prompt/245completion/1179total tokens, provider2738.0594ms, finishstop,
contenttext866chars/no tools. BUT invalid_output, validation output_text/b001,
0validatedrewrite,exactcanonicalfallback. NOT L5quality/gain/L6acceptance.
Output_text groups blank/linebreak/structure/linkHTML/restoredlength. Rawoutput
NOTretained=>exact subcheck unknown, don't guess bullet/newline, relax guard,
claim facts/entailment reviewed, or retry. Capoutput1024 satisfied(245), costunknown.

Live qa/20261113/google_access_after_rotation_r1 manifest
48432218a7e8d6abbfb382b7ed5179fba9b9492e65597768eae25ea1d6ad7017;
verification qa/20261113/google_access_after_rotation_verification_r1 manifest
a5525e600db9e5d903f5094d172f03eceeccec4941491338ba92355736d3b72f.
2949protectedoldfiles unchanged, runtime/data/tests/oldgold/runs/reviews untouched.
No testsrerun; prior564LLM/UI result historical/codebindings same. No newA7score;
A7R/r4stale, r5current onlyaslastverified. No L5cohortbudget/defaultactivation.

Ignored workdir backups/hus_google_access_after_rotation_20261113:
prepare.py,preflight.json,rotation_confirmation.json,public_payloads,live_one.py,
verify.py. ALLone-shotstagesALREADYdone/sealed; DO NOT rerun. attempt_reserved.json
EXISTS andmustnotdelete/reuse. Newgrantusageledger
backups/hus_llm_access_readiness_20261113/conditional_authorization_usage.json
marks1used/0remaining; originalconditional_authorization.json remains grant-time
snapshot0attempted, NOT a secondbudget. Backendroot.env updatedafterpriorfailedcall;
livehelperread HUS_LLM_API_KEY via dotenv_values(interpolateFalse) in memoryonly,
preferredupdatedfile over inheritedkey. Nevertemplates/print/edit/persistkey,
bodyerror/message/headers/privateIDs; no actualkeyfingerprintstored. Explicit
network-sandbox escalation approved/executedonce, no sandboxfail+retry.
HUSLLMSettings.enabledTrue onlyexplicitclient; processflagfalse, no keyenv/persistent
default/billing edits. No Git/stage/push/PR/Actions/deploy.

Docs roadmap/Googlediagnostic updated HTTP200+fallback+spentbudget, old403history
kept. Next: offline output_text diagnostic/syntheticreasoncoverage with no raw
sample; any newGooglecall/cohort needsfreshbudget and currentpins/prepare after
codechanges. L6off until actualgain/facts/citation/completeness/latency+operator.

## Roadmap refreshed with key-rotation reason and conditional grant — 2026-11-13

User requested roadmap update after asking why key replacement needed. Added
actual historical403/PERMISSION_DENIED/key_reported_leaked receipt/reason, origin
unknown, parser doesn't restore access, offlinelexical/F3 needsnokey. Corrected
cachedreadiness row as pre-budget historical snapshot; current max1 conditional
grant alreadyapproved/unused after keyrotation, no reapproval. Pinned model in
nextstep, no retry/1024cap; fournextsteps retained. Docs-only, no keyread/livecall/
newprepare/code/data/oldreceipt/Git changes or suite rerun. Conditional grant
and unmet keyrotation condition remain as next entry, not new authorization.

## User granted max1 access call AFTER rotation, but key NOT changed — 2026-11-13

LATEST async answers: key question='Chưa thay key'; budget='Cho phép tối đa 1
call sau khi thay key'. Supersedes pending-budget notes below. NEWmax1budget
APPROVED CONDITIONALLY and UNUSED:0reserved/0attempted/1remaining conditional,
currentlyeligible0 until operator confirms key installed and oldkey disabled.
Do NOT ask again for this max1budget or infer rotation from generic 'tiếp tục',
empty external_codex_apps companion snapshot(page_idnull/document_viewnull), or
elapsed time. No key read/call/prepare r5 while condition unmet. Don't selfrotate
key/billing or retry lastknownblockedkey. Defaultoff unchanged; oneaccesscheck is
NOT newL5cohort/defaultactivation acceptance. User enablewhenneeded permission
persists independently.

Grant saved at ignored backups/hus_llm_access_readiness_20261113/
conditional_authorization.json (public scope only, no actualkey). Binds F1L5V4-Q001,
3607chars/promptSHA d0acd06dae285c783aed132cef10aab754124088bc5bbc8826a979699e0fb329,
gemini-3.5-flash-lite/directGoogle/1024outputcap/noretry/switch, inputtokens/cost
unknown. Readyreceipt a9b8a... is historicalpending state, DON'T edit its seal.
Future after explicitrotationconfirmation: fresh r5/preflight/currentpins,
exactsameprompt/baseline/source checks, new exclusiveattemptmarker for THISgrant,
onecall/newreceipt/modelusageHTTPdiagnosticlatencyusedfallback, stopafter1attempt.
Old twoonecallmarkers remain SPENT, never reuse/delete them. L5cohortbudget
still separatelyneeded; no key in chat/templates/logs/artifacts.

User said tiếp tục after nullcompanionpage; continuing permitted documentation/
authorization bookkeeping only; no authenticatedpage/keyrotation evidence.
Roadmap and Google diagnostic nowreflect conditionalgrant/waitingkey, not still
awaiting budget. No runtime/test/data/oldartifact changes, testsrerun or Google.
User nextaction: createkey in ownAIStudio, updatebackendHUS_LLM_API_KEY, disableold
and report done without key. Existing hus-llm-rag/localonly/Windows64Py311 intact.

## L5 cached access readiness prepared; key/budget confirmations pending — 2026-11-13

ACTIVE user selected key/preflight/L5/L6 row. Asked async TWO questions: (1)
has backend HUS_LLM_API_KEY been replaced and oldkey disabled, no key in chat;
(2) approve max1 NEWaccesscheck after keyconfirmed, F1L5V4-Q001/public3607chars/
gemini-3.5-flash-lite/1024outputcap/noretry/switch, inputtokens/costunknown,
NOT24callL5cohort. BOTH pending at this entry. Do not infer approval from row
or elapsed time, re-ask already pending questions, read key/call flaggedkey.
User's permission to enable LLM when needed persists; defaultoff untouched.

Independent cached readiness DONE only, NOT newprepare/preflight: validated36
r4sourceaudits, pins differ solely app/hus/llm/diagnostics.py; targetprompt exact
d0acd06dae285c783aed132cef10aab754124088bc5bbc8826a979699e0fb329/3607chars.
Currentpins captured, publicproposal has distinct oldpreparedfile/baselineresponse/
payload/currentpins hashes. Proposed r5 directory DOES NOT EXIST.2945protected
oldfiles unchanged.0newRAG/search/provider/socket/key/env/DB access, no testsrerun
or runtime changes. New qa/20261113/llm_access_readiness_r1 manifest
a9b8a0e7fb6aa1d88cfed4c144ed6d89472b17163e9b18b96447c39c14036382,
contains report/proposal/integrity, explicit pending/notauthorized statuses.
Ignored backups/hus_llm_access_readiness_20261113; seal_readiness.py alreadysealed,
don't rerun. Proposal/readiness artifacts historicalpending snapshots, not rights.

When BOTH answers approve: fresh prepare r5 + preflight under blockedprovider/
socket, preserve r4, compare all A/request/effective/retrieval/gold/prompt/audits
with r4 (only pins/timing should differ). Verify newpins/exactpublicprompt then
ONEaccesscheck with newly authorized backend key in memory only; never templates,
print/edit/storekey or rawerrorbody/message/headers/privateIDs. Newexclusivecall
marker/newreceipt, do not reuse prior two spent one-shot helpers/markers. Record
actualHTTP/allowlisteddiagnostic/model/usage/latency/validatedused/fallback, stop1
attempt withoutretry/switch; no cohortbudget inferred. AdditionalL5cohort needs
separatebudget. Keyreplacement unverified until operatorreply, lastknownkeyblocked.
If either answer declines/unconfirmed, no dependentwork; give ownerinstructions/
readiness status. Docs roadmap/Googlediagnostic nowshowwaiting state. Localonly,
Windows64/Py311,v4/lexical/LLMoff,oldgold/run/review unchanged.

## A7R18 failure review complete, runtime not changed — 2026-11-13

User selected review before choose repair. DONE read-only review of17refusals+
Q025, no app/tests/retrieval/data/oldgold/run/review changes. New doc
docs/RAG_A7R_FAILURE_REVIEW_2026_11_13.md, roadmap updated proposed boundedfix
and separate contracts, not runtime implementation. Ignored helpers/snapshots
backups/hus_a7r_failure_review_20261113 (one-shot writers already sealed, don't
rerun).2939protectedfiles unchanged SHA.0newend-to-endRAG/search/provider/socket,
no env/key/DB/Gitpublication. New qa/20261113/a7r_failure_review_r1 manifest
2a899923a8b119a9d3920cd343da93d099fbb361637ac175a94dcf5f4dd6ac1b.

Router gaps:Q014 chucdanh absent CAREER_TERMS;Q026 cohoi giangday absent;
Q039 graduate-role regex requires vaitro nao/gi adjacency, misses cong tac;
Q027 hoctap nangcao absent furtherstudy terms -> introduction/emptysearch;
Q006/018/030/042 ten tiengViet cua ma hocphan not name form.7similarpositive
router probes reproduce gaps;5negative/control classifier probes observed.

Cached-hit guard trace:Q002 residual bo/pdf;Q038 pdf. Q003 residual kem due
nonadjacent ghi...kem syntax AND second issue: recognized question grammar
still rejects bare source Sinhvien du dieukien va co nhucau... se cothe hoctiep.
CONDITION_SOURCE only if/when/with/tuy forms, not that bareconditional. Keep both
condition conjuncts/negation/parenthesis placement/source scope; don't accept
source lacking actual condition or infer registration eligibility.
Q015 Ban nguon prefix outside source-subject syntax leaves bay. Q009/021/033/045
ho so AI thamkhao locator leaves ho/so; do not globally neutralize these factual
words. Q037 residual dinh from dinhhuong: source supports history1993/formername/
updates inITcontext, not unambiguoustrainingorientation. Removing phrase changes
meaning, not proven grammar fix. HOLD Q037 semantics rather than drop dinh.

Q025 correct unknowneditionfilter leaves talent+unknownvariant samepage groups;
specific empty, bothpurpose density1, existingBM25 rank3talent vs4goldunknown
breakstie. No crossscope merge, outputlabels talent. Question doesn'tuniquely
select frozenbranch: hold contract/authoring, no rankingpatch/post-outputgold
alternative/equivalence. Surrounding source has standard2023 LINK label before
goldquote, talentlink beforeotherquote; placementcue ONLY, no verifiededition
or automaticmetadatarelabelling.3quote spans/hashes verifiedinclDEV-Q002.
2PDFresolvermetadata available/hashbound/pages4-5/include_markdown,
raw_original_verifiedfalse; no newGET/fullvisual/academicPDFreview.

DEV-Q002 remains multiqualifier presearch clarification vs oldanswered gold;
samequote explicitly lists bothprogrammes, scopeunknown. Enumeration versus
comparison/selectorconflict needs revieweddesign, no skip/xfail/guardbypass.
Review olddocs unchanged. Future separate data candidate if revisingmetadata.

18saved-router/10cachedguard/9editedquestionguard/12additionalrouter/5condition
detector/12guardboundary probes are DIAGNOSTIC, NOT regression or newscore.
Known barecondition mismatches retained. No pytest/fullsuite rerun for readonly
review. Cached A7R20/24–18/36–12/12 reproduced; A7R/L5r4 pins remainstale due
prior singletondiagnosticfix, code router/guard/answerer matchfrozenA7Rhashes.
A7R used for diagnostic repairdesign => keep dev/exposed for futuretuning; after
actualfix freeze different>=48/12major. RootAI nonblind/nonindependent/human0,
not academicacceptance. Google budgets spent/keyreplacement unverified,
LLMdefaultoff,Windows64/Py311/localonly unchanged. No new test-green claims.

## Roadmap synchronized after singleton diagnostic repair — 2026-11-13

User requested docs/RAG_PROGRESS_AND_NEXT_PLAN.md update. Added latest-status
summary: parser offline fixed/564tests, key replacement/access unverified, no new
Google/quality measurement, A7R/L5r4 stale. Labeled historical verification/pins
so pre-patch receipts don't imply current code match. Kept scores/legacy failure,
four next priorities, v4/lexical/LLMoff, Windows64/Py311 and local-only scope.
Documentation only; no suite rerun, runtime/data/old receipt/secret/Git changes.

## Singleton Google error parser fixed offline; access not restored — 2026-11-13

User selected key/diagnostic/L5 row. Offline repair DONE on hus-llm-rag WIP;
no key/template/env/billing/account/DB/network/provider or Git publication access.
Only app/hus/llm/diagnostics.py adds4lines: unwrap list len1 dictionary before
existing allowlisted HTTP-error classifier. Empty/multiple/nonobject/nested arrays
unspecified; HTTP200 completion-array remains invalid. Fixed enums only, no raw
body/message/headers/privateIDs;16KiB errorbody/8192message/HTTP403gates unchanged.
No fallback/retry/circuit/model/1024budget/consent/canonical facts/citations changes.

Plan docs/superpowers/plans/2026-11-13-hus-singleton-error-diagnostic.md; ignored
ledger/helper backups/hus_singleton_diagnostic_20261113 (finish_qa.py one-shot,
already sealed, don't rerun). Added tests/hus/llm/test_singleton_error_diagnostic.py;
parameterized existing test_access_failures.py for object/singleton privacy/status/
one-call circuit fallback.23additional cases total. TDD53tests:7FAIL/46pass before,
53PASS after. Full relevant LLM+rewriteUI564PASS,1Starlette warning,168.44s.
Scoped Ruff/diff checks pass. Fresh-context AI code review found0critical/
important/minor, independently53tests pass. No full-repo rerun: historical
3058pass/1fail/2skip/90deselected/3warnings/DEV-Q002 unresolved, not all-green.

NEW qa/20261113/singleton_diagnostic_r1 manifest
2b3c13b1b470234aa006f0e7c1e9ccb900459c054351440804cb649a2e3356c0.
2932/2934protectedfiles unchanged; allowed2diagnostic+access tests, new boundary
test added. Data/releases/oldgold/runs/reviews/Google diagnosticr1r2 unchanged.
Cached A7R and historical L5 replay reproduce old metrics; current A7R and L5
preparedr4 pins now STALE solely app/hus/llm/diagnostics.py hash change. Don't edit
oldpins/overlays or call oldprepared current. No new inference/cohort/prepare.

Docs Google diagnostic/roadmap/A7R current-pin note updated. Call1 body shape
unknown (not retained); only call2 proved singleton array, avoid claiming shape
same for call1. Safe parser classifies observed synthetic shape now; does NOT
restore Google access, replace key or prove model quality. Google key last known
provider-reported leaked/blocked; operator replacement unverified. All budgets
SPENT,0newlivecalls; don't retry flagged key. User permission to enable LLM when
needed persists but is not new call budget/default activation. Operator rotates
key in own AIStudio/backend HUS_LLM_API_KEY and disables oldkey, never sends key
chat/templates. After replacement/newbudget: newdirectory prepare/preflight,
limitedaccesscheck then separatelyauthorizedA/B cohort/exactreview. L6off until
gain/facts/citations/completeness/latency+operatoracceptance. Local-only and
Windows64/Py311 unchanged, no stage/commit/push/PR/Actions/deploy.

## DEV-Q002 reviewed; A7R successor frozen/measured, not accepted — 2026-11-13

User selected legacy-test review then new48/12major A7. DONE local, no app/runtime,
old test/gold/run/review/data/secret/DB/provider/Git publication changes. Existing
hus-llm-rag WIP retained. New plan docs/superpowers/plans/2026-11-13-hus-a7-successor.md;
ignored ledger/helpers backups/hus_a7_successor_20261113 (one-shot writers, don't rerun).

DEV-Q002 source P11-E001/v3 e7864... quote/span0–105/hash verified: explicitly
lists standard/talent programmes, metadata unknown. Old gold not proven wrong;
enumeration versus incompatible-filter contract gap remains OPEN. Exact old
pytest assertion still FAILS; no skip/xfail/gold change/guard relaxation. V4 probe
clarifies before search, no facts/citation. Prior pre-repair proof retained.
Doc docs/RAG_DEV_Q002_CONTRACT_REVIEW_2026_11_13.md. Future enumeration feature
needs reviewed policy/positive+negative regressions, not a QID exception.

New tools/hus_a7_successor_cases.py + tests/hus/test_a7_successor.py registered/pinned
in evaluate_hus_a7.py. TDD initial5fail; fresh-context AI code review found same-
cohort skip hid duplicate wording/hashes. Fixed before freeze, assertion RED→GREEN;
production repeated freeze rejected before output.105 focused evaluator/metrics
tests PASS,1Starlette warning. Ruff tools pass; test has minor I001 missing blank
between local json/tools imports, recorded and retained in frozen code. No claim
full lint/suite clean; clean style only in a later code revision with new pins.

Pack candidates/a7_request_role_20261113_r1 manifest
771b0722f3d2983ea17c700f0e7545a184cf17197ed15169ab9daeff9a1263f8,
freeze11:16:21UTC before inference11:18:28–47UTC.48questions,12/major,3F1/3F2/3F3
+3controls each.34priorinputs/0wording overlap/8F1targets reused; rootAI author/
reviewer exposed/nonblind/nonindependent,human0. Not independent holdout.
V4/lexical/LLMoff,indexnull,dormantmodel pinned,actualmodelnull/0provider.

Measurement runs/a7_request_role_lexical_20261113_r2 manifest
dbc4e28a876b727041dbd4dbd1b7423cefc1b79d2fb160863414d04d97efd8af;
overlay runs/a7_request_role_ai_review_20261113_r1 manifest
f7d3c0baee840c86329df4ea504a1b1e7a13a10500a6d3a90ef4e5b6c3a3048a.
Review reviews/a7_request_role_ai_20261113_r1.json covers exact48responses.
RoutedRecall20/24=83.33% FAIL(<90), conditional20/21 diagnostic only,
complete18/36,F2sourcecontract8/12(credits4,prereqs4,names0),controls12/12.
17refusals+Q025wrong branch retained. Sourceintegrity/relativeentailment19/19 is
NOT relevance/fullscope/complete19/19. Q025 goldunknown objectives vs outputtalent
samewebpage/unknownedition; wording not uniquely selecting branch. Keep fail,
review contract/authoring limitation, don't force ranking or add gold alternative.
F1nocall Q014/Q026/Q039; wrongfieldemptysearch Q027; F2name refusalsQ006/018/030/042;
9targettop5refusalsQ002/003/009/015/021/033/037/038/045. Runtime NOTfixed in this turn.

Aborted r1 preserved sealed: Windows socket guard blocked asyncio socketpair
self-pipe before TestClient startup,0API/RAG/provider. R2 harness allows only
socketpair loopback with no external connects; same frozen pack.0externalHTTP/
provider,6binaryroutes/4PDF bytehash checked, no new full visual PDF review.
API local p50/p95≈27/65ms, excludes init/audit/review, not browser/demo latency.

QA qa/20261113/a7_request_role_r1 manifest
1453043e5df5ed5d40ab75d633a7e31a42708f7ea48c868f9128eec58342aec1.
2908/2910protectedfiles unchanged; allowed2 evaluator/newtest from RED snapshot,
all old runtime/test/data/gold/run/review unchanged. Cached A7R run/overlay replay
reproduces/currentpins true; old A7S23/24–32/36–12/12 reproduces,pins stale/dev;
L5preparedr4pins still match. Old fullrepo3058pass/1fail/2skip/90deselected/3warnings
not rerun or made green. New report docs/RAG_A7_REQUEST_ROLE_2026_11_13.md, roadmap
updated nextreview before choose repair. If A7R used tuning mark dev/newfreeze;
AI review never independent acceptance. Google budgets all SPENT/keyblocked,
no new calls; local-only and Windows64/Py311 scope unchanged.

## Roadmap refreshed after Windows-only decision — 2026-11-13

User requested docs/RAG_PROGRESS_AND_NEXT_PLAN.md update. Clarified Windows64/
Python3.11 acceptance in header, added YAML-local-only CI status/currentquickstart,
direct Google diagnosticr2 receipt and 589/575ms results. All2one-call budgets
spent, provider-reported leakedkey known, access/productionarrayparser NOTfixed,
actualmodel/usage/costunknown. R4current onlyatlastverifiedpins. Next actions
ownerkeyreplacement+offlinearrayparser/newbudgetL5 and currentWindowscheckout
before newhandoff clarified. Preserve F3r2 concept-only36, Q001unknown, fullrepo
1legacyfailure and oldA7scores/dev status; no oldartifact changes. Documentation
only; no runtime/data/secret/Google/Git mutations or test rerun. First whole-file
patch failed validation before any edit; corrected with scoped updates.

## Checkout/handoff scope narrowed to Windows only — 2026-11-13

User explicitly said "bỏ Linux/macOS đi" after checkout/handoff explanation.
Current acceptance scope is Windows64-bit/Python3.11 only; no pending requirement
to install/test Linux/macOS or promise three-OS CI. Updated roadmap, quickstart,
README quickstart link and prepared .github/workflows/hus-rag.yml to a single
windows-latest runner/Python3.11 x64, no OS matrix. No runtime OS gate added.
No Actions run, stage/commit/push/PR/deploy, provider/key/DB access or new kit.
Historical receipts/docs/old six-file patch remain immutable evidence of their
original scope, not a current publication bundle. Refresh that patch only when
handoff/publication is requested. Recheck affected Windows paths when relevant
code/dependencies/config change; no blanket claim old checkout verifies new code.
Source remains independent of demo/submission machine. This doc/workflow-only
change needs static checks, not another runtime suite/menu/HTTP rerun.

## Source gaps supplemented in immutable r2; admission/applicability still open — 2026-11-13

User selected source21gap closure. Completed new review/field_edition_20261113_r2
manifest77b49fd7bb847b568416cd8336733055e0b467c583a80383016eee813e6f57a1;
qa/20261113/field_edition_r2 manifest
a44a270c56ad3e95c14bffe2fab94039e514b462e2bc83d6d5cb2781a017cc4e.
21rows previously19partial/2open now have directcore anchors:CS6,DS4,Math5,MI6;
15priorcore rows identical,36snapshotitemhashes same, status definitions copied
unchanged.36core_supported is CONCEPT support ONLY, NOT fullsentence/example,
learnerability, officialHUS or independentacademicacceptance. All290F3remain
generated/needs_review/academicfalse/officialfieldsnull. No data candidate,
integration, retrieval/index/release/runtime/gold/oldreview changes. Human0/rootAI
exposed; don't sell newcounts as qualityscore or independentreview.

24public HTTPcaptures:21success,3fail (R12CornellwrongURL404,R14GMUHTML502,
L14guessedcoordinates404). Alternative correctCornell/GT HTML and GMUofficially
linkedPDF captured200.24new+29old anchors=53,36pointers allchecked. Render12PDF
pages, actuallyview6 (O11p1/13,L11Pp3/4,L13Pp2,R17p1), not whole5PDFreview.
3exactarithmeticexampleschecked(coordinatebasis,scaling/rotation,affineline),
NOTallAIexamples/independentreview. Primaryrefs Purdue/Cornell/GMUfooter2024
(filename2018),OpenStaxPsychology2e,SciPy1.18bisect,FNCRunge,MIT2011/6.005-2014/
2016,GeorgiaTechMargalitRabinoff2019,LiskovWing1994,Martin2014. Allsupplemental,
noHUSedition/languagerequirementpromotion. Limits documented (GMUwritingrules
notuniversalresearchcriteria; correlationaloneinsufficient not allobservational
causalityforbidden; localNewton/finiteprecision/finiterealmatrixassumptions).

Q001new HUS2014listing/VNU2012fundingconsultation support2012historicalcontext,
NOTfirststandardintake. Mathstandard/talentlabel elsewhere inarticlecannot
transfer toCS; financialsupport!=programmevariant. H13department-likeURL200
servedbroadundergraduatecontent=>rejectpath/titleidentityproof. Existing2012
standardPDF+2022incompleteissuance stilldon'testablishsigned2023/cohort/amendment
chain. Keepchunkunknown/oldgoldpoints, noabsence-of-amendmentclaim.
2893protectedpriorfilesunchangedSHA;cachedA7Sreplayreproduces oldscore/pinsstale,
L5preparedr4pinsstillmatch. No repotestsadded/rerun (source-onlyreview);previous
fullrepo1legacyfailure retained. Sources helpers/captures under ignored
backups/hus_source_gap_review_20261113;one-shotwriterssealedDONOTrerun.
Newdocs/RAG_SOURCE_GAP_CLOSURE_2026_11_13.md,roadmapandhistoricalr1note updated.

SeparateauthorizedsecondGooglediagnostic performed duringturn (see nextsection):
HTTP403singletonarray/PERMISSION_DENIED/key_reported_leaked, no rawsecrets.
Google docs/roadmap nowreflectknownprovider-reportedcause; two1callbudgetsspent,
no pendingextraapproval. Ownerneedsreplacekey; no selfkey/billing/defaultchange.
No appdiagnosticparserfix yet; possibleofflinefollow-upseparatefromsourcework.
No stage/commit/push/PR/Actions/deploy. Nextsource:fullclaim/example/academic
review+adoptionchain; anydata/referencechange requiresnewcandidate/integration,
neveroverwritev4 orregradeoldscore. LLMsourcecontentreviewcalls0.

## Active source-gap review + second diagnostic now identifies blocked key — 2026-11-13

ACTIVE user selected source matrix19partial/2open gap closure, first standard
admission/cohort applicability chain. Workdir backups/hus_source_gap_review_20261113,
protected_before2893files. setup.py printed21snapshotitems; capture.py fetching
13primaryreferences+MITpdfs (source GET only), execute session99055 pending.
No runtime/data integration allowed by this task; preservev4/oldreviews/gold.

While source work active, user answered prior async approval: "Cho phép thêm tối
đa 1 call chẩn đoán". Executed exactly1 additional call via next_one.py with
exclusive next_attempt_reserved.json marker (DO NOT rerun). Same3607prompt/model/
1024cap, no retry/switch. HTTP403, response JSON top-level ARRAY singleton error
object. Safe shape identifies PERMISSION_DENIED and key_reported_leaked. Thus
Google REPORTED this backend key leaked/blocked; prior parser expectedobject and
couldn't recognize array. No rawbody/message/key/projectID retained. New sealed
qa/20261113/google_diagnostic_r2 manifest
4c3f36f6cdc5356e0a194a2deb2d5ea677063b1a4435ce9df23eb2d6fe2a9ec4.
No validatedrewrite; key/billing/default unchanged, currentr4pinsmatch. Both
separate1-call diagnostics nowSPENT; no furthercalls/cohort authorized. Do not
ask again about these alreadygranted permissions; don't call flaggedkeyagain.
Notfixedaccess: user must replace/revoke key in ownAIStudio/backend, never send
key in chat. Already told user in commentary. Official Google api-key#leak-response
checked; no authenticatedprojectsession/accountmanagementavailable. No appcode
change yet for singletonarraydiagnostic, not part of source matrix integration.
Need update Google diagnostic doc/roadmap with NEW rootcause/outcome while
finishing source work; priorsealedr1reports remainhistoricalunchanged.

## One Google diagnostic spent; HTTP403 unspecified, no access fix — 2026-11-13

Authorized user max1 diagnostic performed, no retry/model switch: F1L5V4-Q001,
3607chars exact reviewed hash d0acd06dae285c783aed132cef10aab754124088bc5bbc8826a979699e0fb329,
gemini-3.5-flash-lite/Google endpoint,1024output cap. ActualHTTP403/http_error,
provider_statusother/access_issueunspecified,589.4326ms,actualmodel/usage/cost
UNKNOWN.0validatedrewrite,canonicalF1fallback preserved. Access NOTFIXED,
rootcause NOTidentified, no runtimebug proven; don't infer quota/key leak/billing
from403 or previousbandwidthbanner. Request matches officialOpenAI endpoint/
Bearer form. No rawbody/message/headers/unknownIDs saved, can't recover shape.
No connecteddocument/browser sessions on refreshedtoolcheck; no cookies/account.

NEWprepared runs/llm_v3_v4_prepared_20261113_r4,manifest
d473a280adbf4564304ddef99333fefcfd4444bfa28f912d2a18b5b49a6b4f68:
36sourceaudits/24prompts/12controls;ALL36A/request/effective/gold/retrieval/prompt/
audits exactr3; currentpinsmatch before/after call. r3historicalstale unchanged.
NEWqa/20261113/google_diagnostic_r1 manifest
b5171aadcf823f331d16d9ccadc60f9ae494fab2bf7f59afca089e67d6e8727a.
2885priorfilesunchangedSHA.30accessfailuretests pass,1existingwarning;7offline
safe-shapeprivacychecks pass. No app/runtime/data/gold/oldreceipt modification,
newtestsrepo/fullsuite rerun. Previouswhole-suite1legacyfailure still disclosed.

Keyexistingbackend.env used in memory underusercallauthorization; never templates,
print/edit/persistkey. No billing/keychange/defaultchange/Gitpublication.
One-shot helpers backups/hus_google_diagnostic_20261113; live_one.py marker
attempt_reserved.json exists=>NEVERrerun or delete to retry. Max1budgetSPENT.
Asyncquestion sent for ADDITIONALmax1safe-envelopeprobe (sameprompt/model/token,
JSON/HTML/object/array+allowlistedstatusfromstatus/type/code only), currently
UNAPPROVED; no secondcall/cohort allowed untilresponse. safe_shape.py has7offline
checks but not a provenproductionfix; no appdiagnosticchangebasedonguess.
Docs/RAG_GOOGLE_DIAGNOSTIC_2026_11_13.md+roadmap updated. LLMtemporaryenable
permission persists; no repeat enablepermission question. Preservev4/lexical/
defaultoff and allotherlocalonly constraints. No newL5quality/L6acceptance claim.

## Google diagnostic call authorized by user — 2026-11-13 (in progress)

User pasted the max1-call diagnostic roadmap and explicitly said
"bạn được phép gọi để test và fix lỗi". Authorization now granted for that
one diagnostic, overrides earlier unapproved1call notes. No need ask again.
Keep1.024 output tokens, same model/endpoint, no retry/model switch/key/billing
changes. Not authorization for new24-call cohort or permanent default activation.
Prepared current pins in NEW llm_v3_v4_prepared_20261113_r4,36records/24payloads;
manifest d473a280adbf4564304ddef99333fefcfd4444bfa28f912d2a18b5b49a6b4f68.
TargetL5V4-Q001 exactsame reviewed3607char prompt hash as prior proposal.
Offlineprepare0socket/provider, oldfilesunchanged. Ignored workdir
backups/hus_google_diagnostic_20261113 contains authorization and one-shot helper.
Use existing backend environment or .env HUS_LLM_API_KEY in memory only for
authorized call; never template files, print/edit/save key. Endpoint/model pinned,
not copied from private config. Helper --live-one reserves exclusive marker before
HTTP, max1 attempt via existing observed client/adapter. Do not rerun after marker.

## User authorizes enabling LLM when needed — 2026-11-13

User explicitly said "cho phép bật llm khi cần thiết". This grants permission
to enable the existing LLM path for a task that needs it; do not ask again for
the enable/disable action itself. Preserve per-request allow_llm_rewrite opt-in,
RAG-only evidence, canonical facts/citations, validation/fallback and server key.
This is conditional use, not a request to change the persistent default or
academic/content acceptance: default stays off until deliberately selected.
No runtime/config/private env change or Google call made in this authorization
turn. Existing separate live-call budget condition remains: both24-call budgets
spent; no new numeric live-call/cohort allowance supplied in this message.
Before a live diagnostic/measurement, pin/prepare current code and obtain only
the missing call allowance, not permission to enable LLM again. Avoid blanket
"LLM enabling unauthorized" statements; distinguish activation permission from
unallocated external-call budget. Local-only Git/publication constraints persist.
Roadmap updated; sealed historical receipts/scores and L6 assessment unchanged.

## Request grammar / graduate-role repair implemented; legacy full-suite conflict — 2026-11-13

User selected implementation after four-case A7S review. Modified ONLY old
app/hus/answer_support.py and app/hus/question_routing.py; added
tests/hus/test_request_role_language.py (77 regression cases). Bounded accompanying
condition questions, source-subject/passive presentation grammar, school/institute
graduate roles. No global ignored kem/bay, source/ranking/schema/threshold changes.
Keep factual presentation/aeroplane, conditions including negative suffix,
institution/course actor distinction, literal workplaces including comma lists.
Disambiguate personnel vien/institute vien and market/environment truong for
workplace evidence only; preserve canonical body/quote. Opt-in/exclusions/scope
still checked. User's detailed selected repair supplied spec; worked in existing
hus-llm-rag WIP, no new worktree/commit. Plan
docs/superpowers/plans/2026-11-13-hus-request-role-repair.md; ignored ledger/helpers
backups/hus_request_role_repair_20261113. No provider/API/key/env/DB/Git publication.

TDD initial24fail/28pass; institute4fail/2pass; negation3fail/2pass; review13fail/
2pass. Fresh-context AI code review found4 Important (market-school, comma lists,
institution determiners, negative conditions), all fixed with failed-then-passing
regressions. Final focused support/routing233 pass (includes77 new, not additive).
Scoped Ruff/diff checks pass. Full repository offline command from guidelines:
3058 PASS,1 FAIL,2 SKIP,90 deselected,3 warnings,1141.77s. NOT all-green.
Failure tests/hus/test_routing_diagnostic.py::
test_exposed_dev_requests_preserve_facts_scope_and_consent[DEV-Q002]: old frozen
dev gold expects answered for simultaneous standard+talent introduction, strict
single-variant contract clarifies before search. Reproduced exact assertion on
pre-repair source copy backups/hus_scope_assessment_fix_20261113/fresh checkout λ,
three runtime file hashes match before snapshot. Preserve old test/gold/run/review
and strict scope; review legacy contract separately, never patch QID/lower guard
to turn suite green. Two Windows symlink-permission skips (passage artifact/vector
index contract); other path guards covered. Warnings Starlette/httpx plus2
subprocess reader UnicodeDecodeError in catalogs/test_metadata_builder, not fixed.
Superseded earlier full run interrupted after reviewer code changes, not a pass.

NEW qa/20261113/request_role_repair_r1 manifest
f98e47800fc79bb255bdf81e28059f4169aac4df600dda6fd1cd7c5900583cd4.
Report/integrity/code bindings/baseline failure/dev checks sealed; don't overwrite.
2876/2878 prior files unchanged SHA, other2 are allowed runtime files; all data,
old gold/runs/reviews unchanged. Cached A7S replay reproduces old23/24--32/36--12/12.
Four exposed requests now answered in separate dev-only diagnostic, canonical
quotes retained, Q013ability condition retained. Q015 includes broader careers
quotes, not a claim of concise output. NO new A7 score/independent acceptance.
A7S used tuning -> dev; current A7S and L5 preparedr3 pins now STALE as expected.
Don't rewrite old pins; next new A7 freeze>=48/12 each and L5prepare/preflight
only when selected. Google1call/cohort still UNAPPROVED, both old budgets spent.
Keepv4/lexical/LLMoff. Docs repair report/roadmap/A7/preflight historical notes
updated. Local-only decision persists: no stage/commit/push/PR/Actions/deploy.

## Field/edition source matrix reviewed; v4 unchanged — 2026-11-13

User selected source review by field/edition, not data integration. New sealed
review/field_edition_20261113_r1 manifest
c31f9eb00b25083e7f44be985da51338363aed224cd3dd1ab46dacfaae68ad44;
qa/20261113/field_edition_r1 manifest
882ae7a4dcf7e2fba498fed54e4c0956379904098df42b38be2e2b7a7a8899e4.
36 item mappings (18 content/18 objectives), same four profiles as prior source
review: CS MAT1204, DS MAT2034, Math MAT2300, MI MAT1202. 15 core_supported,
19 partial, 2 open (CS literature methods). Core means selected central concept,
NOT whole sentence/example coverage, official HUS equivalence or academic pass.
29 normalized reference range/hash anchors checked. MIT2011/Oracle JDK8 are
supplemental different editions, not replacements for runtime references/HUS.
No MAT3372-to-MAT1202 transfer. All 290 AI profiles remain needs_review/unverified.

26 new public HTTP captures successful, 1 ConnectError (2021 admissions binary),
2 old FNC captures reused with hash. Obtained actual 10-page standard2012 PDF
from files.vnu.edu.vn, SHA
56bad5aa1a09217baca356d8a61a5e28bb791c517133341c7376b15bae3a89d0.
Viewed pages1-2: standard code52480105, decision4115/QD-DT 2012-11-30.
Different URL from old HUS09_0.pdf404; no byte-identity proof with that file.
2022 programme14-page binary obtained; p1 decision number/day/month blank,
not signed issuance/current applicability proof. 8 PDF pages rendered, 6 images
actually viewed (H01p1/2,H03p1/2,MIT basis p1/3); MIT4-page text read.
Q001 first-standard-intake link/adoption chain still open, original chunk unknown.

2867 protected prior files unchanged SHA; cached A7S replay and A7S/L5r3 pins
match. No runtime/data/gold/old run/review edits, new tests, provider/API calls,
env/key/DB access, kit, stage/commit/push/PR/Actions/deploy. Google diagnostic
1-call budget still UNAPPROVED. AI reviewer exposed/nonindependent, human0.
Helpers/captures in ignored backups/hus_field_edition_review_20261113;
one-shot writers must not rerun/overwrite. New doc
docs/RAG_FIELD_EDITION_REVIEW_2026_11_13.md and roadmap updated; historical source
doc has a follow-up link. Next: close19partial/2open and admissions/adoption chain;
any data change needs fresh candidate/integration, never overwrite v4/regrade old.

## A7S four-case root-cause review complete; runtime unchanged — 2026-11-13

User selected REVIEW4A7S BEFOREchoosingfix, conditionalregressions ifimplemented.
Completed cachedexactoutput/source/trace+pureguard/routerdiagnostics; NO runtime
or source/gold/run/review changes, newA7inference/provider/env/key/DB/Gitpublication.
Keepv4/lexical/LLMoff; Google1callstillUNAPPROVED. Don't triggerfix/newcohort
automatically from measurement/review; nextrow nowgeneralrepairwhenchosen.

Rootcauses proven withlocal sys.settrace of supported_hits, savedhitIDs/scores/
matchedterms reconstructedfromimmutablev4(no search):
Q013wrongrequiredtokenkem from 'nêu kèm điều kiện', NOTneu (nêu folds like nếu,
alreadyneutral). Targetrank1/scopeunknown retained; removeonlykemword=>samehits
accepted. Sourceabilityconditionmustremain.
Q027/Q037missingbay fromnoninitialsource-subject/passivepresentation wording.
COMMAND_SYNTAX only startactiveclause, _presentation_syntax lacksboundedF1forms;
directrequest/imperativecontrasts pass on samehits. Don'tglobalignorebay/kem:
factualpresentation/reportingskill and 'lập trình máy bay' needbodyevidence.
Q015CAREER_TERMSmissingrolepattern, role_at_work limitedto company/business,
school/institutefallsbackintroduction. Introhitsacceptedguard butwrongfield/
incomplete. Frozenexactcareerstargetdirectguard supports; this is diagnostic
intervention NOTretrieval or prediction. Institutionrole/course-role negatives
mustnotbecomegraduatecareers bybroadtermaddition.

20guardprobes+11routerprobes+8additionaldirectguardchecks (39, NOTnewregression
tests or newA7score). Wrongedition/CLC/quantum/997/ISO/experience/skill/maybay
negatives preserved. Allanswerer/search/provider/networkattempts0. SavedA7S
score23/24--32/36--12/12 immutable; AIexposed/human0/nonindependent. Diagnostic
use disclosedseparately; futuretuningmustretainthisasdev/freezenewafterfix.

NEWqa/20261113/a7s_four_case_review_r1 manifest
cf32c1c557daf0bcccdb65fb4ae2044442aa25954b92f355a7879e2d198aa599.
diagnostic.json/negative_probes/regression_requirements/cohort_exposure/report/
integrity/replays.2859/2859priorfilesunchangedSHA, cachedA7Smeasurement/overlay+
A7Foverlayreproduced, A7S/L5preparedr3pinsstillmatch. No runtimechange=>no
repositorytestsadded/rerun; probesexplicitnotfulltestpassclaim. Ignorehelpers
backups/hus_a7s_four_case_review_20261113 one-shotwritersnotrerun/overwrite.
NEW docs/RAG_A7S_FOUR_CASE_REVIEW_2026_11_13.md, roadmapandA7reportnote updated.
NEXTgeneralboundedgrammar/graduate-role scope repair withpositive/negativeTDD;
noQIDpatch/goldchange/thresholdlowering, no datasetregrade. Otherlocalonly/
sourcevalidity/Googlebudget constraints persist unchanged.

## Roadmap consolidated after source review — 2026-11-13

User explicitly requested docs/RAG_PROGRESS_AND_NEXT_PLAN.md update. Consolidated
repeated checkout/status paragraphs into current-state/check-receipt/next-step
tables. Current priorities: review4A7Sfailures before choosingfix; boundedGoogle
diagnostic ONLYafternewbudget thenL5/L6; source/editionreview; otherOS/conditional
handoff. Preserves A7S23/24--32/36--12/12, oldA7F24/24--34/36--11/12 immutable,
preflightL5r3current/off/nolivebudget, source4profiles8fields18topics18objectives,
Q001unknown/106candidateexcluded/290AI, localonlyGitHubdecision. No envfile/key
read despite IDE tabs; no runtime/data/sealedreceipt change or tests rerun for
documentation edit. No stage/commit/push/PR/Actions/deploy/Googlecall.

## Source review follow-up + handoff scope — 2026-11-13

User selected source/F3/validity/Q001+conditionalkit/target work. Completed bounded
source review, NO runtime/data/release/gold/priorreview modifications, key/env/DB/
Google calls, source integration, kitbuild, stage/commit/push/PR/Actions/deploy.
Keepv4/lexical/LLMoff. Onecall diagnostic stillUNAPPROVED; don't ask again while
user steers to sources. Source checkout independent of demo/target machine.

NEW review/source_scope_20261113_r1 (underdata/hus) manifest
25e05ab52c58b5b15155ed33309cacd1edaacc4e24fb3b5c7800b90448d83162;
qa/20261113/source_scope_r1 manifest
315885f767f867df4bbbca9302ad4abefed718619dfbdc762718308e8d9b87be.
Ignored backups/hus_source_scope_20261113 helpers/captures/text/images/JUnit;
one-shotseal notrerun/overwrite. 2848protectedoldfiles unchanged;70existing
source_review_audit/f3_runtime_release/f3_runtime_api tests pass248.64s,
oneexistingwarning. CachedA7S/A7F/L5v3replays pass; currentA7S/L5preparedr3pins
remainmatch. No needrerunfullsuite, LLMquality/academicacceptance unproven.

Publicsourcecapture11success/1HTTP404. Initial9 sandboxConnectError recorded
separately; requiredescalation approved read-onlynetworkretry, no evasion/key.
N01newHUS28/12/2020standardprogrammeconference: explicitstandardcontext,
2012trialapproval,2018CLCaddition,ninecohorts. Usefulhistoricalscopebridge BUT
not explicit firstadmissionstandarddate or automaticoldchunkrelabel. N02VNU
2012admissionsD480105listing, chinhquy!=automaticallystandard. N03same2012
09_0.pdf direct404;webindexed10pagetext available,2screenshotcachemiss, no fresh
PDFbinary/images. Keepchunkf526a537e9132345485d15b065a5697bvariantunknown,
nochangeA7V4-Q001gold/status/score. Need futureintegrationreview/adoptionchain.

Read4newprogrammeprofiles/8fields/18topics18objectives: MAT1204CS,
MAT2034DS,MAT2300Math,MAT1202MI. All290generated/needs_review/disclosure/
academic_verifiedfalse/officialfieldsnull;106candidatesdefaultretrievalexcluded.
CSMAT1204matchesS06PDF2024code/declaredQD3568-2023candidate butscopevalidity
unverified. Images52-54showpublication/authorship/database/reporttools/teamwork
goalsnotfullycoveredbyAI. ORIreferencesonlyintegrity/data-managementgrounding.
DSMAT2034FNCconditioning/stabilitychecked;otherunitsneedspecificsectionmapping,
noofficialcandidate. MathMAT2300MITcalendarconceptschecked,notalltheorems/
examples/HUS; noofficialcandidate. MIMAT1202Python/UMLreferencesbounded,
S07PDF2021OOPp168belongsheaderMAT3372SoftwareComponentsp167,NOTMAT1202:
rejectasofficialidentity/assessment/prerequisitetransfer. No syllabuslinkcandidate.
S06/S07cached12/11PDFshaunchanged, NOTrefetchedthisturn.7pagesrendered,
rootviewed5images(S06p52/53/54,S07p167/168);p169/170textonly,notwholePDFreview.
ReferencepagescapturedpublicwURLs/time/bytes/hash; no humanreview,nonindependentAI.

NEW docs/RAG_SOURCE_SCOPE_REVIEW_2026_11_13.md +roadmapupdated. Kit notneeded
forordinarycheckout andnotrequestednewhandoff; no newkit. Historicalkits
pre-scopefix immutable, actualotherWin64/Py311targetunverified. Publicdeployment
wouldneedseparateAPI/secret/load/health/log/rollbackacceptance, NOTrequested.
NEXTtargetedsource/adoption/fieldreview; changeswouldneedfreshcandidate/release
integration,neveroverwritev4 or regradeoldrun. OtherOScheckoutstillpending.

## L5 r3 preflight complete; agent access check/no live budget — 2026-11-13

User selected L5new->L6 and replied 'bạn hãy tự kiểm tra' to request for actual
AIStudio project/key status beyond near-bandwidth banner. Agent checked available
tools/documentcontrol list_document_sessions: NO connected sessions, no
authenticated browser/account tool available. Didn't access browser cookies,
privateenv/template/key/DB/account. User request to inspect is NOT explicit new
Google call budget: both24budgets spent, max1 diagnostic stillUNAPPROVED.
No Google/model-list/tokenizer/newinference, Gitpublication/deploy/activation.

Completed offline prepare on currentpostCLC/assessmentruntime:
runs/llm_v3_v4_prepared_20261113_r3,36audits/24prompts8F1+8F2+8F3/12controls,
98268promptchars,output1024.36A/request/effective/gold/evidence/audit/retrieval/
prompt exactequalr2 AND oldlivev3prepared;36A exactliveobservationsA.24payload
byteequalpreviousfullyreviewed, privacyreviewreusedbyequality (notreadkey).
R3pinscurrentmatch, r2stale. Preparedmanifest
a18e1ca9924e71ad4bfc112f3b976dfe39c03c953dd60b04040a2cf443760587;
pinshash a13f21c4883707ac4be51c1260e70cc5c8efbae33bf864128dad4214c3bc3982.
Sourcepackllm_v3_v4_dev_20261113_r1 unchanged. No source/runtime/gold changes.
61tests(test_v4_measurement+test_access_failures)pass39.06s,existingwarning,
notfullsuite/newtests.2841priorfilesunchangedSHA,3oldL5cachedreplaysreproduce,
prepare/export/replay0socket/providerattempts. Ignorehelpersone-shot in
backups/hus_l5_v3_preflight_20261113_r3; do notoverwrite receipts/prepared.

Newqa/20261113/llm_preflight_r3 manifest
8069afba50b966fa6d04e28765e7e3e667736935cff7743041e6c7a86788aede.
Report/comparison/historical403/proposed_diagnostic/test/replay/integrity.
Oldlivev3traces24HTTP403/http_error allprovider_errornull/actualmodelmissing,
noerrorbodyretained=>causeunknown. Banneralonecan'tprovequota/billing/leakedkey.
PublicGoogletroubleshooting#project-unavailable checked (notkeyAPIcall): several
403causes and model-list200doesn'tproveinferenceaccess; don'tretry/switch/bill.

Proposedonecall (not authorized): preparedr3/L5V4-Q001F1,3607promptchars,
gemini-3.5-flash-lite existingGoogleendpoint,1024maxoutput,no retry/model-switch,
oneattemptthenstop,backendexistingkeyonly/noin-or-editkey,onlyfixederrorcategories
logged,no rawbody/header/projectID. Inputtokens/costunknown. Purpose bounded
diagnostic foractualstatus, NOTL5quality; full24cohortneedsownbudgetafteraccess
resolved. KeepLLMoff/L6keep_disabled. Need explicitapproval BEFOREanyGooglecall.
Newdocs/RAG_LLM_V3_PREFLIGHT_R3_2026_11_13.md +roadmap/runbook/historynote updated.
User'slocal-onlyGitHubdecisionpersists; nostage/commit/push/PR/Actions/deploy.

## A7S frozen candidate measured/reviewed; recall95.83%, incomplete — 2026-11-13

User selected measure48frozen candidate/review exactoutput/source/completeness/
controls/exposure. Completed measurement + rootAIall48review + overlay/receipt,
NO runtime/data/retrieval/gold changes, Google/env/key/DB access, stage/commit/
push/PR/Actions/deploy. Keepv4/lexical/LLMoff; localonly decision persists.

Pack candidates/a7_scope_assessment_20261113_r1 frozen04:43:52.414931UTC;
collection08:17:29.448762--08:17:49.788360UTC pinsmatchbefore/after.
NEW runs/a7_scope_assessment_lexical_20261113_r1 manifest
0a800e1b456406d006aafa6b6bf2ad9f750c1ad013c0aa197a2a399a2113a25f;
NEW reviews/a7_scope_assessment_ai_20261113_r1.json exactrequest/response/
gold/audit hashes,48notes; NEW runs/a7_scope_assessment_ai_review_20261113_r1
manifest52b11aab7a53080ffccd1ad2315b98805bc516d5205c4dc1fef6e41656f737cb.
Receipt qa/20261113/a7_scope_assessment_r1 manifest
878fe4ae3d263be82df17d6b346b122c54f6d70d841ea4e485c55ce20ef99547.

RESULT RoutedRecall23/24=95.83% meets90%, no-call0/search24/24, classifier35/36,
F2sourcefacts12/12,answeredsourceintegrity33/33,audits48/48,source-relative
AIentailment33/33 BUT AIcomplete32/36=88.89%,controls12/12. Alltechnicalfalse,
independentfalse. Q013KHDLcareers,Q027Toan furtherstudy,Q037Toantin objectives
targetrank1butno_information; no newguardprobes/rootcause claim. Q015routes
introductioninsteadofcareers/targetfiltered; replyrealintroquote so source-relative
entailmentpass BUT relevance/completefail. No claim33/33meansanswerscorrect.
Permajorcomplete CS9/9 DS7/9 Math8/9 MI8/9;recall6/6,5/6,6/6,6/6.
TestClientHTTPp50/p9530.2289/74.462ms,48samplesfirstchatretained,noaudit/review.
F3sometopicquestionsreturnextracoursecontext,complete!=concise;AI/unverified
labels remain. F2MAT2300Mathraw[null]/unknown preserved,noeligibilityclaim.

Exposure0wordingoverlap31inputs BUT6reusedF1targetIDs andconceptreuse
(MAT1202contentacrossmajors). AIrootauthor/source/runtimeexposed/nonblind/
nonindependent,human0. Noacademicacceptance/independentholdout. OldA7Fscore
24/24--34/36--11/12 unchanged; Q003newsource-scopedpassdoesnotregradeoldeval
orproveacademicweb/DOCXequivalence. Packgold unchangedafterinference.

61focused tests test_a7_evaluation/test_a7_scope_candidate/test_chatbot_metrics_v2
pass, existingStarlettewarning. No runtimechange, nofullruntime/LLMrerun.
2819/2819protectedpriorfilesunchangedSHA; cachedreplaynewmeasurement/overlay
andoldA7Foverlayreproduced withanswerer/retrieval/provider/networkattempts0.
Newrunpinsstillmatch; oldA7Fpinshistoricalstaleexpected. Manifest/currentpins
checked. Ignoredhelpers/JUnit under backups/hus_a7_scope_measure_20261113;
one-shotwritersmustnotrerun/overwrite. ReviewdisplayhelperNonehusanswerbasic
case corrected, no savedoutput alteration. Docs RAG_A7_SCOPE_ASSESSMENT_2026_11_13,
roadmap/README updated. NEXT review4failuresbeforechoosinggeneralfix; if used
fortuning retirethispacktodev/freezeanother; DON'T changegold/run/review or
patchQIDs. Linux/macOScheckoutstillpending; L5newbudget+prepare,L6off.

## Checkout local-only verification complete — 2026-11-13

User selected checkout row, retain explicit local-only decision. Verified real
standard CLI (-m tools.run_hus_rag) from existing HEAD+six scoped publicfiles
export, using previously clean minimaldependency Windows3.11venv, no reinstallation.
20API/menu2124pass; actual loopbackserver customport9HTTPchecks pass (4static,
4chat F1/F2/F3 optin and one hashchecked citationbinary). Invalidport0 exit2;
inherited badroot/vector/LLMtrue overridden. Server terminatedfinally,224source
files hashunchanged/indexstill empty. NoGoogle/env/key/DB/publication actions.
NEW QA/20261113/checkout_local_only_r1 manifest
dee993385ea113bab8902c23952154b1eda620d5cd7e8a4354aa8b64326a5623.
Ignored helper backups/hus_checkout_ci_20261113/verify_local_only.py one-shot,
don't overwrite receipt. Roadmap marks Windows localcomplete; do not repeat
without changes/failures. Linux/macOS/remoteclone/fullbrowser/academic/LLMquality
remain unverified by this smoke. Oldreceipt/patch/candidate source unchanged.
Next useful work is frozenA7 measurement or otherOS when environment available;
NO stage/commit/push/PR/Actions/deploy until explicit newuserrequest.

## Checkout decision: local only; roadmap updated — 2026-11-13

User answered explicit publication question: 'Chỉ chuẩn bị và kiểm local,
chưa đưa lên GitHub'. This supersedes pending-permission wording below.
NO stage/commit/push/PR/Actions/deploy authorized. Don't ask the same question
again unless user requests publication. Six-file preparation/proofs remain;
Windows20API/menu2124passed, Linux/macOS/remoteclone not verified. Historical
checkout_ci_preparation_r1 receipt still records question pending AT SEAL TIME;
keep bytes unchanged, interpret with this subsequent decision.
Updated docs/RAG_PROGRESS_AND_NEXT_PLAN.md on user request: local-only status,
six-file proof/limits/next steps, key-free lexical vs separate Gemini key.
No runtime/data/env/key/Google/tests or sealed receipts changed this update.

## Checkout CI scoped publication prepared; explicit permission pending — 2026-11-13

User selected roadmap item checkout for everyone, wording 'feature branch/PR
when requested' and 'do not automatically publish/deploy'. Prepared concrete
six-file patch against HEAD excluding ALL unrelated local WIP. Async question
requests explicit commit/push/PR permission; NO answer as of this checkpoint.
Do not push until permission arrives. No stage/commit/push/PR/Google/deploy yet.

Ignored backups/hus_checkout_ci_20261113: publication_plan.json,
portable-checkout.patch (SHA c84174d393fecc805da95298702c62ec883a0f0dfbd5ea9b6b6f5877fde41c1a),
pr-body.md, candidate_proof.json. Exact scope: requirements-rag.txt,
tools/run_hus_rag.py, tools/run_hus_submission.py, .github/workflows/hus-rag.yml,
docs/HUS_RAG_QUICKSTART.md + portable-only README insertion based on HEAD.
DO NOT commit whole current README or whole working tree (unrelated priorWIP).
git apply --check --cached passes, index untouched. Initialpatch CRLF rendering
failure corrected via normalize_patch.py, no source runtime changes. Candidate
README separate has only quickstart addition, no unpublished WIPdoclinks.

HEAD publicRAG218files + those6 run20API/menu2124pass using previously created
clean minimaldependency Windows3.11venv, isolatedimport from candidate source,
bad inherited vector/LLMtrue/root overridden. No dependency on uncommitted
CLC/assessment/LLM tuning. Source export, NOT remoteclone/otherOS. NEWreceipt
data/hus/qa/20261113/checkout_ci_preparation_r1 seals plan/proof/report.
OtherOSCI remains pending. No gh CLI/GitHubconnector currently available;
historical memory notes GCM in-memory GitHub REST helper (around priorNov4
publication) if approved; NEVER print/store credential values. No secrets or
envfiles in six-file candidate. Leave existing WIP/oldreceipts intact.

## Portable checkout + CLC/assessment repair — 2026-11-13

LATEST USER: anyone downloading project must be able to test RAG independently
of demo machine. Primary path is source checkout/minimal requirements/generic
launcher. Historical Win64/Py311 target acceptance is optional submission work,
NOT prerequisite for ordinary RAG. Still hus-llm-rag/basef61b0fd + priorWIP,
NO commit/push/deploy/Google/env/key/DB/account access. Both24call budgets spent;
1call diagnostic unapproved. CURRENTv4/lexical/LLMoff, L6keep_disabled.

NEW requirements-rag.txt five deps with existing lock; tools/run_hus_rag.py
canonical source-relative launcher --check or loopback8011. Overrides inherited
badroot/vector/LLMtrue. Old run_hus_submission compatibility wrapper; packager
allowlist includes new launcher/requirements. No oldkits rebuilt/modified.
NEW docs/HUS_RAG_QUICKSTART.md, README/roadmap source-first. NEW workflow
.github/workflows/hus-rag.yml PR/manual Win/Linux/macOS/Python3.11 no secret/
DB/provider, read-only. Structure checked, not remotely executed; newfileslocal,
remoteclone won't get them before publication. Do not autonomously commit/push.

Portable proof: publicsource215files export to Unicode path and differentcwd,
fresh localWindows3.11.9 venv,25cachedverifiedwheels offline,pipcheck20API/
menu2124pass. No .git/.env/backups/DB required; providerblocked/bad inherited
settings overridden. Not remoteGitclone or otherOS proof. Initial install via
pipindex or OS-matchedwheelhouse; lexicalruntime/citationbinaries offline.

Prior authorized task completed: runtime3 question_routing/answering/
answer_support CLC scope alias->high_quality exactmetadata + F1filter before
search, conflictsclarify/unknownnotCLC. Dependent assessment content onefield,
perclause/conjunction; independent requests stillclarify,missingassessment
no_information.47newtests test_scope_assessment_language.py. Admission negative
instrumentation now records searchcalls despiteemptyfilteredhits; stilldenies,
unknowninventoryretained. Initialruntime655pass1instrumentationfail preserved,
corrected withoutlowercriterion. Final656runtime/RAG/API,525LLMoffline,
98evaluator/packagepass; groups overlap, don'tsum/full-repo. RED25fail22pass kept.

Dev48 only Q002/Q011changed; Q002answered high_quality filter/citations,
Q011no_informationmissingassessment.46others/Q003/12F2exactunchanged.
OldA7Fnowdev, NOTregrade: Recall24/24,complete34/36,controls11/12unchanged.
NEW HUS_F1_SOURCE_EDITION_POLICY prospective source/edition, noacademic
equivalence/rankingpatch/posthocgoldexpansion. NEW hus_a7_scope_cases builder,
evaluatorcohort/pins +5newcandidate tests. Frozen candidate
data/hus/evaluation/candidates/a7_scope_assessment_20261113_r1:
48/12major,36evidence,manifest
623c8d3185e6651fffddd3fc11a52fe39f5f6b9a34d0ff4c5daa192edcc19f9a.
NO predictions; freeze0answerer/retrieval/provider/networkattempts.31inputs,
0wordingoverlap BUT6reusedF1targetIDs; AI/runtime/sourceexposed,human0,
notindependent. PinsmatchatQA. Don'trerunfreeze/overwritecandidate.

QA data/hus/qa/20261113/scope_assessment_portable_r1 manifest
70d59d2ec34e739e5611c465229ec8babd32463cd5e0e6d58a58b1d465a12a9e.
2810/2817protectedpriorfilesunchanged; onlyruntime3/evaluator/packager/
compatlauncher/admissiontestchanged. Alldata/run/gold/review/oldkitsunchanged.
NEW docs/RAG_SCOPE_ASSESSMENT_PORTABLE_2026_11_13.md + roadmap/README/reviewnote.
Ignoredhelpers/proofs/JUnit backups/hus_scope_assessment_fix_20261113,
one-shotQA/source/freezewriters notrerun/overwritten.

IMPORTANT runtimefix makes preparedL5r2 STALE; reprepare beforeapprovedcalls.
Oldreadiness/kits historical/pre-fix; cannotclaimexactcurrent or enableLLM.
NEXT actual3OSCI afterrequestedpublication/featurePR; measurefrozen48with
fixedgold/review/exposure. SeparateGoogleaccess/newbudget+prepare forL5,
realcontent/latency/operator beforeL6enable. Source/F3effectiveness review
continues withoutrelabelingunknown. Ordinary clone testing doesn'tneed a ZIP.

## A8 current-code kit + clean local rehearsal verified, other machine pending — 2026-11-13

User selected A8 newZIP/checker/hash/receipt thenactualothermachineWin64/Py311/
operatorchecks. Completed allwork possiblelocally; actualothermachine has no
access/results yet. Do NOT call A8 target/operatoraccepted. Keep CURRENTv4/
lexical/LLMoff; noGoogle/env/template/key/DB/account,commit/push/publish/deploy.
Stillhus-llm-rag/basef61b0fd+priorWIP; Q002/Q011baselinefixes notimplemented.

CHANGED tools/package_hus_demo.py: latestA7/L5/L6 statusdocs/README + allowlist,
new --transfer/--wheel-zip builds freshkit withZIP/checker/pinnedZIPhashes/
README/TRANSFER_MANIFEST; verifies25wheelinventory/SHA,no downloads. Existing
out refused. CHANGED tools/run_hus_submission.py ONLYlatestA7 limitstring:
Recall24/24,complete34/36,controls11/12,Q002/Q003/Q011 remain. No false3refusals.
NEW tools/check_hus_submission_target.py standardlib templateARCHIVESempty,
rendered CHECK_TARGET.py pinsactual2ZIPs. Freshroot,WinAMD64/CPython311/64bit,
archivepaths/orig_filename/symlink/count/sizeguard,offlinevenv/pipcheck/20API,
safeenvironment/log/manifest evenfailure. Unpinnedtemplate intentionallyfails;
use renderedchecker. --run-demo optional loopback, NOTpublicdeploy.

Newimmutable kit backups/hus_submission_20261113_r1:
hus-rag-demo.zip211payloads/67097215bytes/SHA
fa0ebcc27a041c348ee0f36c543d469e546a133a278318c544fd0bfeba3c71cc;
wheelhouse-win-py311.zip25wheels BYTESAME r2 SHA
b176282aeeba6bcc48fa5fc62af8e14be18bc3bfc6e00411d25d102c04234b9b;
CHECK_TARGET.py SHA0e8da83d641ea549829815137fe0ea3ad616ebfef8b9054d005d2d7834fa024b;
README-MAY-NOP.md SHAa698961d777bac60684c71752dbd37f9b8f889eb4c2446b3d7001c5d04fd8622;
TRANSFER_MANIFEST binds4files. Oldr1/r2 ZIP/checker/allreceipts unchangedSHA.
Kitfrozenafterbuild; don'tedit included HUS_RAG_SUBMISSION/packager/launcher/
allowlist docs and pretendZIP still exactcurrentpayloads; buildnewrevisionifneeded.

Exactdeliveredchecker ranfreshlocal root backups/hus_a8_local_install_20261113_r1:
newdemo/.venv/25wheelofflineinstall/pipcheck/20API/menu2124pass,CPython3.11.9/
WindowsAMD64currenthost reused,usersite/systemsitefalse/appimportextracted.
Target-receiptstatus checks_passed_manual_operator_review_pending is LOCAL
rehearsal despiteitsname, NOT actualothermachine. Existingrootnegativeprobe
exit2/oldreporthash preserved. No fileoverwrite or executionpolicychange.

Cleanvenv actualHTTP3phasesv4->v3->v4 each12PDF+2DOCX GETbytes/SHA+HEADpass,
F2MAT3533=3/LLMfalse eveninheritedon/vector/badroot; selectoronlyEXTRACTED copy,
restoredexact/211payloadsverify,allserversstopped.48latestA7 exactresponses
matchfrozenA7F(newfollowup):Q002no_information,Q003answered,Q011clarification
preserved, NOTnewgold/review/score. BrowserheadlessChromium1380/390 menuF2,
EnterF3/AIlabel/optin/LLMdisabled/majorreset/F1newscope/nooverflowpass,
rootviewed2screenshots. NotfullA6/manual/remotewebhealth/load/publicsecurity.

CHANGED tests/hus/test_submission_package.py11new cases;27pass0.91s,Ruffpass.
Initial2testruns failedrawbackslashZIPcase: ZipInfo Windowsnormalizesnames;
checker now validatesorig_filename beforeextract, finalpass. Originalfailure
JUnit files retainedignored, no loweredboundary. No fullsuite rerun (runtime
unchanged).3008/3011protectedoldfiles unchanged; ONLYpackager/launcher/test
changed, plusNEWchecker. Source/runtime/UI/gold/run/review/oldkits untouched.
PreparedL5r2stillpinsmatch; oldL5/A7cachedreplay pass.

NEW QA/20261113/submission_repackage_r1 report/environment/API/browser/HTTP/
48compatibility/installer/negativeprobe/operatorpendingtemplate sealed:
manifest51f6fbac9d6de22f140474cf0f648b90461a26412a7db65f7dc42ade47b74b60.
Ignored backups/hus_a8_repackage_20261113 helpers/proofs/JUnit/screenshots;
one-shotseal/installwriters notrerun/overwrite. New docs/RAG_A8_REPACKAGE_2026_11_13.md,
roadmap/rootREADME updated; HUS_RAG_SUBMISSION frozeninsidekit. OldA8doc
annotatedasr2historywithoutchangingreceipts. No agents/toolkit.

NEXT: copy entire newkit toactualotherWin64/Py311 machine, run
python -X utf8 -I -B CHECK_TARGET.py --root .\hus-demo-target --run-demo
fromkitdirectory. rootmustnew. Retain target-receipt evenfailure; operator
checks browser/menu/naturalinput/PDFDOCXwebAI/consent/majors/rollback there and
createsNEWmanualreceipt. Actualtarget/operatorpending; no needaskOSagain.
A7still24/24Recall34/36complete11/12controlsAI/human0; L5last24HTTP4030used,
both24budgets exhausted/1callproposalunapproved; L6keep_disabled. Packaging/
localinstallation mustnotpromote academicvalidity, LLMquality or targetacceptance.

## L6 keep-disabled rechecked; user AI Studio near-limit banner — 2026-11-13

User selected L6 keepoff: actualgeneratedfacts/citations/completeness/gain/
demo latency + fallback/rollback/operator acceptance beforedefaultenable.
Completed currentreadonlyassessment+focusedofflineAPIrollback checks and
pendingoperatorworksheet. NOdefaultactivation/newGoogle/env/key/billing/account
access or serverrestart/commit/push/deploy. CURRENTv4/lexical/LLMoff profile.

NEW runs/llm_l6_v3_readiness_20261113_r2 on original livev3AIreview = keep_disabled,
eligiblefalse,used0/fallback24, gain0/usedlatencycount0/p50p95null. Reasons
latency_unavailable,no_generated_output,no_supported_readability_gain,
no_used_output_f1/f2/f3,observed_model_changed(EMPTYactualmodel not proven switch),
pins_changed(c8b580a... recorded vs33ab82ee... current). Originalassessmentr1/
live/gold/review unchanged. NEWassessmentmanifest
8486f8c1333de047d1677b070e88d575722b7f4232ceffa6d33e9cefd9da80a5.
Preparedllm_v3_v4_prepared_20261113_r2 STILLcurrentpinsmatches; thisturnonly
testchange doesn'taffectruntimepins. No rerunRAG A7 or changedscore.

CHANGED tests/hus/llm/test_rollback.py ONLY: addpermission403/authentication401
to3families (6newAPIregressions), synthetickey/bodyecho/projectprivacy and
http_error fallback canonicalunchanged; afterdisable no additionalHTTP.
Focused activation+readiness_v4+rollback60pass40.29s, oneexistingStarlettewarning,
Ruffpass. Includes4majorsx3familiesoff/on(mock)/off, failures/consent/source503.
Notactualmodel quality/latency or operator/demo/targetmachine acceptance.
Prior519tests overlaps; DO NOTsum60+519/full-repo or claim525fullsuite rerun.
2777/2778protectedoldfiles unchangedSHA, ONLYrollbacktest changed. OldL5v3
live/review+v4review andA7cachedreplay pass; actualA7pinsstillstale asprevious.
Read-onlychecker verification socket/provider/answerer/searchattempts ALL0.

Duringwork USERreplied to earlierstatusquestion call_61ceb10b35f1423ea344d18ba97b761e:0:
"You are approaching a bandwidth limit. Configure your billing to increase your
limits and support the development of your projects." This is near-limit UI
warning, NOTinference403body, notexplicitproject/key-specificstatus. Official
Google rate-limits/troubleshooting checked; no basis to diagnosebilling/quota/
blockedkey or guaranteebillingfix. Do NOTenablebilling/changekey or infer
newlivebudget fromthisanswer. Both24callbudgets exhausted; proposed1call
diagnosticUNAPPROVED. Nextcheckactualproject/key status distinctfrombanner.
No newuserquestion needed justto repeat previousrequest.

NEW QA/20261113/l6_keep_disabled_r1 has report/operator_acceptance_template.json/
reported_ai_studio_banner.json/manifest. OperatorfieldsNULL/pending,acceptance
false, notactivationtool; futureoperator usesNEWreceipt, don'toverwrite sealed.
Manifest1258cd84c9e45e1c98875ad63ca9003471e3993889f5c136e9eee32b9af145a2.
Ignored backups/hus_l6_keep_off_20261113 snapshot+JUnit+one-shotseal helper.
Docs/RAG_L6_KEEP_DISABLED_2026_11_13.md new; roadmap/ops/accessdiagnostic updated
forassessmentr2/tests/pendinggates/banner. L6technicalkeepoffwork complete,
livecontent/latency/operatoracceptance remains unavailable, defaultstaysOFF.
Q002/Q011fixes,Q003equivalence,A8newpackage/othermachine stillpending.

## L5 access diagnostic/circuit implemented offline; actual403 unresolved — 2026-11-13

User selected roadmap2: real AI Studio key/project status, limited diagnosis,
stop repeatedpermission errors, freshpins/run ONLY after accessfix+newbudget.
Implemented all independent offline work; no Google inference/model-list/
tokenizer, env/template/key/account read/edit or billing/model changes. Async
asked for actual AI Studio message WITHOUT key; no response/status available
at completion. Do NOT claim actual403 resolved or key leaked/billing cause.
Both prior24-call budgets exhausted; NO new live approval from selectedrow.

CHANGED app/hus/llm/client.py + diagnostics.py: HTTP error diagnostic stage
provider_http, finite Literal provider_status/access_issue only. Bounded JSON
inspection16384bytes/message8192chars/details16, no retained raw text/header/
unknown code/project ID/key. Groups key_reported_leaked/verification_required/
project_access_denied ONLY from provider reported markers; generic403 remains
unspecified. Inspectioncap is NOT totaldownload/body memory cap. Existing
HUSLLMError code/status/fallback contract retained, no startup connection.

CHANGED tools/evaluate_hus_llm.py Budget/ObservedTransport: stopafter2consecutive
HTTP403, immediate401/429, beforebody read; otherHTTP or transporterror breaks
403streak. No retry/model switch. This is BATCH circuit, not global chatbot
circuit. Remainingeligible pairs retain A/canonical and evaluation_stop reason;
controls0calls. Traceprovider_error safeenum, reportfailure_policy/stop_reason.
Replay verifies newpolicy/circuit ifmarker present; historicruns withoutmarker
retain oldbehavior/results. No hus_llm_measurement metric/schema change.

NEW tests/hus/llm/test_access_failures.py30tests. Full tests/hus/llm519pass
134.12s incl30new, oneexistingStarlettewarning. Then fixtureimport lintcleanup
only,30newpass2.71s/Ruffpass; NOT549/full-repo. Initial focused127 hadone
testassertion expectingcircuit but preexistingmetadata check fired first;
testisolated intendedcircuit andfinalpassed. No productionfailure hidden.
Ignored logs/JUnit in backups/hus_llm_access_20261113.

NEW prepared runs/llm_v3_v4_prepared_20261113_r2, same existing sourcepack
llm_v3_v4_dev_20261113_r1.36sourceaudits/24validprompts/12controls,98268chars.
ALL36A/request/effectiverequest/gold/evidence/retrieval/sourceaudit/prompthash
EXACT13/11r1.24payloads BYTEIDENTICAL priorreviewed export; reused privacyreview,
not claimed newmanualread or actualkeycomparison.0socket/providerconstruction
attempts inprepare/export. Currentpinsmatch r2; allpreviouspreparedpinsSTALE.
Preparedmanifestf8c5fbd0808343c91220d20798410f93483336bb08a22a557fdf8f5948d6fd52;
pinssha33ab82eefad8ee70028abe084a729ce9331dd2111a1596cb0e38240877972e4f.
Payloadmanifest860dca2adecd6b352ef0055a66336fa0f092d1ee1ae807393bde2ccdc2839f5b.

QA/20261113/llm_access_diagnostic_r1 report/preparedcomparison/proposeddiagnostic
sealed manifestce7405fc432bd04ec9e27eb29462d03f647dead17f3fbd49ac852682f503663f.
2767/2771protectedoldfiles unchanged: ONLY3code files above+LLMpackageREADME
changed; allolddata/release/CURRENT/gold/run/review/receipts untouched.
OldL5v3live/review andv4review cachedreplay pass. LatestA7cachedreplay passes
but currentpinsmatchFALSE now (LLMfileschanged; do NOT rewriteA7result).
Currentreadiness oldv3review keep_disabled pluspins_changed; storedinQA,
historicalassessment NOT overwritten. CURRENTv4/lexical/LLMoff. No commit/push/
deploy, RAGbaseline/guard/LLMprompt/tokenlimits/consent/F2facts unchanged.

Concrete PROPOSED diagnostic, NOTapproved: max1call L5V4-Q001 F1/3607promptchars,
preparedr2 pinnedmodelgemini-3.5-flash-lite/GoogleHTTPS/max1024outputtokens/
5sminspacing/no retry/switch, inputtokens/costunknown; backendkeyneverprint/edit,
keepdefaultoff. Need actualAIStudio status/accessfix first, then separate
explicit1callapproval. After successfulaccess verification, fullcohort needs
separatebudget/pins/freshrun/exactused+fallbackreview; no reuseold24calls.
No additionallivepermission question asked prematurely while access unresolved.

Docs/RAG_LLM_ACCESS_DIAGNOSTIC_2026_11_13.md added; roadmap/operations/README/
packageREADME/preflight/historylink updated. Q002/Q011 baselinefixes remain
pending, Q003academic equivalence unresolved; A8newpackage/machinepending.
Ignoredone-shotprepare/seal scripts+snapshot are provenance; don'trerunwriters
or overwrite sealed r2/QA. No proactiveagents/toolkit used.

## A7 three-case source/contract review complete, no runtime fix — 2026-11-13

User selected roadmap item1 review Q002/Q003/Q011 before choosing fixes.
Completed cached-source/code/contract review,23pure existing guard/router
probes,10archiveSHA/exactlocator checks,1selected DOCX paragraph comparison.
No new end-to-end answer/search/model/API inference; socket/answerer/search
guards0attempts. CURRENTv4/lexical/LLMoff. Stillhus-llm-rag/basef61b0fd+priorWIP.
2722old data/runtime/schema/service/static/tools/tests files SHA unchanged;
new/old A7 measurement+overlay replay/pins match. No prod/test/evaluator/data/
gold/run/review/score changes, no env/key access, commit/push/deploy/Google.

Q002: cachedtarget291b6949cf13e7e60e54762b0d09ae77 rank1 high_quality/unknown.
Guard specificclc/thiet/tich; targetonlymissingclc. Effective program_variant
and retrieval filterNULL, standardhits present. RemovingCLCdiagnostic accepts
target, NOT permissible productionfix via global neutral token: normalize
CLC/fullform to verifiedscope constraint; preserve bodyfact evidence, unknown,
version/conflict guard. Fullform currently selects2019other source, not target.

Q003: output DOCX2023standard e5a82ded76438ecd8803b9c5e5d2e9c1rank1 vs web
gold e29e0cbb74eb7a68f3992ec91f5dd4e9rank2 edition/variantunknown. Both conditional
postgradlists, different fields, NO equivalence established. Exact selected
DOCX paragraph matches binary SHA4838b51f795e858c0672883ff0994a82b8be70e379260189c034e166a0f63517
in data/hus/citation_assets/files (historical recovery path not on disk).
Each source individually passes guard; swappedcachedorder choosesweb. F1 auto
clears decisionselector by existingcontract; not a sourceedition pin. Keep
entailmentpass/completenessfail, NO rankingpatch to force gold. Futurecohort
must pin source/edition or define prospective alternative-source policy;
do not merge lists or infer fields equivalent/unknown=standard. Independent
specialist needed IF claiming equivalence; not blocker to othertechnicalfixes.

Q011 classifierassessment but requestedfieldscontent+assessment -> multi-field
clarification beforesearch. Proposedreading: content OF assessment is1field;
boundedmodifier recognition, preserve genuine contentANDassessment/creditsAND
exam/negation/official/optin/scope guards. V4has1463content290objectives,
noassessment; MAT3557official_assessmentnull/profile noassessment/generated/
needs_review/academicfalse. Correct1field still no_information when absent.
Original observedneeds_clarification/goldno_information mismatch remains.

All original scores preserved: Recall24/24,completeness34/36,controls11/12,
AI/nonblind/human0. Reviewonly: no new regression tests claimed, matrix proposed.
If follow-up implements using this cohort, retainasdev and freeze different
48/12major afterfix; no QIDpatch/relabel/regrade oldrun. L5newbudget spent24
HTTP403 remains exhausted/L6keep_disabled; no furtherGoogleauthorized.

QA/20261113/a7_three_case_review_r1 diagnostics+review+report+manifest:
SHA72b47c68959695ebc602d6ba69e2c94181fe797d292c736127f3557a0e8893f4.
Ignored backups/hus_a7_review_20261113 contains snapshot/one-shotdiagnose+seal;
don't rerun writers/overwrite sealedreceipt. New docs/RAG_A7_THREE_CASE_REVIEW_2026_11_13.md,
roadmap and originalA7doc linked. Next recommended implementation: general
scopeCLC and assessmentmodifier repairs with positive/negative matrix; source
edition/alternative-source evaluation contract explicit before newcohort.

## L5 v3 authorized live finished: all24 HTTP403, budget exhausted — 2026-11-13

User explicitly approved max24 NEW Google calls for prepared
llm_v3_v4_prepared_20261113_r1 (call_01ab4caa543d4e99b839e05a96fa2932:0).
Collected once to NEW runs/llm_l5_v3_google_20261113_r1: all24 HTTP403,
0used/24fallback,8calls each F1/F2/F3;12controls0calls. Budget now EXHAUSTED;
no further inference/smoke/model-list/tokenizer authorization. Requested model
gemini-3.5-flash-lite unchanged, actual_models empty, all usage/cost UNKNOWN
not0. No retry/model switch; max1024 output tokens, >=5s pacing, direct HTTPS.
Root .env loaded internally ONLY by approved runner via --env-file .env;
explicit live exception, no key print/edit or template read. Never dump env.

After repeated403 attempted exact-runner process lookup to stop early, but
Get-CimInstance denied by sandbox; batch finished all24 before stop possible.
Do NOT claim early stop or remaining budget. Existing quota circuit stops429,
not403. No error body stored, so specific403 cause UNKNOWN; official Google
troubleshooting supports possible key/project access checks, not a diagnosis.
No provider/config/key changes or extra calls made to investigate.

Pins still match; all36 B replies and canonical hus_answer EXACT A. All36 A,
requests, gold/evidence match prior live11/11. NEW review
reviews/llm_l5_v3_ai_20261113_r1.json carries forward PRIOR A-only semantics
after exact equality/prior pair/target hash checks. NOT newly read36 displays,
NOT old B/readability labels. All24 positives supported/complete relative to
same evidence, same readability;12 controlsN/A. AI/nonblind/human0. Allfallback
is NOT LLM success. Overlay runs/llm_l5_v3_ai_review_20261113_r1 sealed/replayed.

NEW runs/llm_l6_v3_readiness_20261113_r1 = keep_disabled; reasons
latency_unavailable,no_generated_output,no_supported_readability_gain,
no_used_output_f1/f2/f3,observed_model_changed (because observed models EMPTY,
not proof of actual switching). Activationfalse/blockedcases0/no human/operator
acceptance. FailedHTTP provider p50/p95721/797ms,fallback722/799ms excluding
pacing; NOT generated latency/SLO. Four F3stress/Q022 remain untested by model.

2615 protected old data/runtime/schema/service/static files unchangedSHA;
live/review/oldL5 replay and current readiness reproduce OFFLINE/socketguard0.
No code/prompt/guard/retrieval/source/gold changes during live/reporting. Kept
CURRENTv4/lexical/LLMoff; no commit/push/deploy.67preflight tests already passed,
no unnecessary full-suite rerun. A7/A8 pending issues unaffected.

QA/20261113/llm_l5_v3_live_r1 includes authorization/report/reviewprovenance:
manifest f36ccf9330f83bff3339aedbb4614e3b40013ae0336c2ff6240df61aa2b4300b.
Live manifest8eb1876427a11be3e4a671eca164d158961d950dd698fdfcb1e44c1eb0742ce7;
review08c01abf625238991c9cf386f8ff6a1e78bc6320135a1c67f7761dc42664d0a1;
readiness6e97765b6b0a9c2e0a54e0a4e5013e4f161b4f6d1f028a57ca335f5a92bf48a8.
Ignored backups/llm_l5_v3_20261113 has one-shot finalizers,protected snapshot,
auth and binding proofs; don't rerun writers/overwrite sealed artifacts.
Docs/RAG_LLM_L5_V3_2026_11_13.md, roadmap/ops/README/preflight updated. Next:
operator checks Google key/project status WITHOUT sharing key; fix actual
access issue, separately authorize new limited diagnostic/cohort budget,
recheckpins/create fresh run. Consider stopping repeated403 for future batch
outside this frozen measurement. Only actual used output/gain/content/latency
and operator acceptance can qualify L6. Historical sections below are prior
state, superseded by this exhausted-budget outcome.

## L5 v3 reprepare current pins complete, new budget pending — 2026-11-13

User selected L5reprepare/preflight thenliveonlyafternewbudget/L6conditional.
Completedofflineconcretecohort/pins/export/privacybinding/tests/QA;noGoogle,
noenv/template/keyread/edit,DB/account/advisor,commit/push/deploy. Stillhus-llm-rag,
basef61b0fd+priorWIP,CURRENTv4/lexical/LLMoff. Old24callsbudgetexhausted; NOnew
budgetauthorizationyet. PreparingisnotpermissionforliveorL6activation.

New immutable data/hus/evaluation/llm_v3_v4_dev_20261113_r1 and runs/
llm_v3_v4_prepared_20261113_r1. FixedsameEXPOSED36L5V4-Q001..036,notnewholdout:
24positive8F1/8F2/8F3+12controls,positive6/major;totalsCS8/DS12/Math8/MI8.
36sourceaudits/24validprompts/12noprovidercontrols,0preflightbudgetfallback.
98268totalpromptchars,2711..7328each,12kprompt/8192raw/1024outputcapsunchanged,
F1F3documentv3/F2evidencev1. FourF3stress19..23leaves39..41units;threeMAT3148
sameconceptdifferentmajor. Q022fourbullets,Q0251993/name+programmeupdate remain.
No liveoutput/token-fit/entailment/readabilitygainclaim frompreflight/copyJSON.

Preparedmanifest0e111799ed0e172653c1bfe6bb6bedb0f3ff9e79aa8ffa020d12e15399afe2a6;
pinssha c8b580a7630e5e37891ff734e667f9e7a55772a1daaf2a667359d14f13b1edc3.
Sourcepackmanifest8e8b0c0a8fb73c840685c756a3216e578072640b71260c452a2ef828464d69ca
samebytesasoldpackbutnewpath;currentpinsrequireTHISnewpath.Currentnewpinsmatch,
oldprepared12/11pinsDONOTmatch(twochangedrouting/guardruntimefilehashes).

Exactbaseline/effectiverequest/retrievaltrace/prompthashALL36equalpriorprepared
12/11;payloads.jsonall24BYTEIDENTICALpriorroot-reviewed24publicpayloads,
manifest860dca2adecd6b352ef0055a66336fa0f092d1ee1ae807393bde2ccdc2839f5b.
Recheckedall24allowlist/bundle/question/release/scope/hash;REUSEDpriorfullmanual
payloadprivacyreviewbybyteequality,NOTclaimed24changedpayloadsnewlyread.
Nohistory/account/grades/keys/tools/authheaders inexport. No actualkeycomparison.
Ignored backups/hus_l5_v3_prepare_20261113 contains freshprepare/audit/comparison/
receiptwriters,protectedhashes,payloads_r1/reviewpacket/log/JUnit. Originalsealed
writers/artifactsunchanged,don'trerunnewone-shotwritersoroverwriteanything.

67client/evaluator/budget/readinesstests pass76.08s/oneexistingStarlettewarning;
nofullsuite.2603preexistingdata/runtime/staticfilesSHAunchanged,networksocket
guards0attempts,Googlecalls0. CurrentnewA7reviewandoldL5v4cachedreplayreproduce;
oldL6assessstillkeep_disabled/pins_changed/readability_regressed. QA/20261113/
llm_v3_preflight_r1 report+manifest sealed;manifestSHA
7516def964539cdedce0470740e662e73dc84c90f0793be365e722660880d714.
New docs/RAG_LLM_V3_PREFLIGHT_2026_11_13.md,priorpreflightlink/operations/roadmap/
rootREADMEupdated. No product/evaluator/testcodechangedthisreprepareturn.

Concrete proposedbudget (NOTyetauthorized): max24Google gemini-3.5-flash-lite,
8eachF1F2F3,12controls0calls,>=5sbetweenattempts,1concurrent/process,no retries/
redirect/stream/model-switch,stopcallingafter429. Requestmax_tokens1024/call,
24576totaloutputcap,inputtokens/costunknown,98268promptchars. DirectGoogleHTTPS
endpoint generativelanguage.googleapis.com/v1beta/openai,publicquestion/evidence
only,existingbackendkeynotprint/edit. HTTPX20sPERPHASE,nottotaldeadline.
Afterexplicitapproval: recheckpins,collectfreshlivetoNEWfolderagainstexactfrozen
A(noadditionalretrieval),reviewALLexactoutputsandfallbacks,actualmodel/token/
latency/errors,used/fallbackseparate. Googleapprovalforold24spentdoesn'tapply.
L6onlyafteractualgain/coverageandoperatorcontent/fallback/latencyacceptance;
remainoffaftermeasurement. A7new24/24Recall34/36complete11/12controls stillnot
fullyaccepted;thisL5preparationdoesn'tfixthoseissues. A8r2stilloldbaseline.

## Different A7 after follow-up measured/reviewed — Recall100%, not fully accepted

User selected newA7 minimum48/12major afterlanguagefix. Completed sourceauthor/
freeze/actualcollection/rootAIexact48review/sealedoverlay. Stillhus-llm-rag,
basef61b0fd+priorWIP,no commit/push/deploy/newGoogle/env/template/key/DB/accounts/
advisor. CURRENTv4/lexical/LLMoff. Runtime/UI/data/deps unchanged thisturn; only
preexisting evaluator tools/evaluate_hus_a7.py changed, plusNEWbuilder/tests.
Do NOT fix currentmeasurementmisses or relabelgold while reporting this result.

NEWtools/hus_a7_after_followup_cases.py, tests/hus/test_a7_after_followup.py13tests.
Fixed3F1/3F2/3F3+3controls permajor,48rawrequests withoutfield/dataset/codehints.
SourcegoldfromV4oracle/canonicalrows only, answerer/retriever/providerdisabled
whilefreeze.0normalizedwordingoverlapagainst25pinnedinputfiles,0/36targetID
reuseagainstALLpriorA7(72priorIDs),semantic/source/families/runtimeexposed.
No unusedF1introIDremains:4obj/6careers/2furtherstudy,DS3careers; no newconflict
F2case,prereqstates1present/1unknown/2unresolved. CoveragegapsdeclaredBEFORE
inference;don'tclaimallF1fields/independentholdout. PlannedreviewerrootAI/
nonblind/nonindependent/human0 pinnedinpack. Ifusedtuninglaterretiretodev.

Evaluator supports --cohort after-followup-20261112; pinsnewbuilder/tests,
stampsfrozen_at_utc(newcohort) andcollectionstart/end. Existingreplaycompatible.
101evaluator/metrics/source tests pass55.53s including13new,oneexistingStarlette
warning;Ruffpass. No fullruntime/browserrerun sinceappunchanged. Testgoldbuilder
cannotcallRAG/model. Oldtestsets/source/gold/packs remain byteunchanged.

Pack data/hus/evaluation/a7_after_followup_20261112_r1, A7F-Q001..048.
PackSHA ffd439c74a0959b53e652b9af95fa0215b92c3b1ae9be706fdb4c385efe7a5be;
manifest f6dc71af1a0110a304a90d9c905b43c91875b437a68bce293c88d34075eef7bf.
Freeze2026-11-12T17:08:38.480633+00:00,collection17:08:47.268483..17:09:05.372025UTC;
exactsource-draft/goldunchanged,freezeBEFOREinferenceproof inQA. Filedate/cohort
ID20261112isstable;UTCtimestampactual. ExposedAI,notindependentacceptance.

Run runs/a7_after_followup_lexical_20261112_r1;manifest
c73e3c7ffad8516b5418729f089234b3ce852e205fcf07bc9f51d2ad662e98d2.
Rootreadall4majorfull-displaypackets (48exactresponses/facts/citations/target),
manualjudgments notes forall48, notautoquoteequality grading. Review
reviews/a7_after_followup_ai_20261112_r1.json; overlayruns/
a7_after_followup_ai_review_20261112_r1 manifest
6372465cba3b8802bbdbac975fca5074dda82c8a044bcaa3b6e29bc190a9a04a.
RoutedRecall24/24=100%,no-call0/all24search/conditional24/24notusedassubstitute.
Classifier36/36,F2facts/types/source12/12,answeredsourceintegrity35/35,
sourceaudits48/48,AIentailment35/35,AIcompleteness34/36=94.44%,controls11/12.
HTTP/filter/scopeerrors0. Alltechnicalgatesfalse/noindependentacceptance.
EachmajorRecall6/6;CScomplete7/9controls2/3,DS/Math/MIcomplete9/9controls3/3.
Proxy22/24notsemantic.12binaryURLchecks/7distinctfiles(PDF/DOCX),not12files.
LocalTestClientp50/p95=27.6521/68.1517ms afterservice/configload;firstchatretained,
noexplicitchatwarmup;excludesaudits/review,notnetwork/UI/targetmachineSLO.

Issues KEEPASMEASURED:
A7F-Q002CLCcareers targetrank1/high_quality butno_information. Cachedanalysis
specifictokensclc/thiet/tich,onlyclcabsentgoldbody;guardacronym/scopeissue,no
runtimefixinmeasurement. A7F-Q003citesvalidDOCX2023conditionalpostgraduatelist
withdifferentfieldsfromwebgold(CosotoanhocchoTinhocnotexplicit). Questiondoesn't
pinedition;entailedrelativeactualcitesbutCONSERVATIVEcompletenessfailvsfrozen
target. Don'tinferlistequivalence/modifygold;scope/adjudicationneeded.
A7F-Q011goldno_information;observedneeds_clarification due lexicalcontent+
suggested_assessment in"goi y danh gia...co noi dung gi". Wordingmaymeanjust
assessmentcontent,not necessarily2intents;author/gold/guardambiguityneedsreview.
Keep controlmismatch1/12,don'trelabel/dropdenominator toboostscore. Reviewnotes
saydefensibleclarification/ambiguity,notproofgoldwrong or blanketappbug.

CLIwrapperreportedexit1withStarlettewarningNativeCommandError; all48responses
sealed,HTTPerrors0 andmanifest/replayverified. Preservecollectionlog, no rerun
inferencetocleanwarning.0Google/externaltransportattempts. Currentnewpinsmatch.
2589preexistingfilesprotected,2588unchanged;ONLYtools/evaluate_hus_a7.pychanged.
Oldruntime/data/static/deps/pack/gold/run/review/receipt/ZIP unchanged. Oldpostfix
A7,oldestr2A7,L5v4cachedreplayreproduce. NewQA/20261112/a7_after_followup_r1,
manifest bf74f07bcd2986dddf2463b70b81726cb922e7e12abf2b0dd0181006255c3401.
Ignoredbackups/hus_a7_after_followup_20261112 hasprotectedinventory/sourcechoices/
draft/freezeproof/tests/collectionlog/4reviewpackets/manualreview/sealer.
Neverrerunsealedwritersoroverwriteanynewartifact.

Newdocs/RAG_A7_AFTER_FOLLOWUP_2026_11_12.md;roadmap/rootREADMEupdated. Nextreview
Q002/Q003/Q011beforechoosingfix/adjudication; iftuningthiscohortretiredevandfreeze
another. Old23/24-33/36 and19/24-27/36staydev/resultsunchanged;differentcohortnot
causalA/Bgainproof. L5stillneedsfreshprep/separateGooglebudget(old24exhausted),
A8r2stillpre-followupbaseline/othermachineunverified;noautomaticLLMon/deploy.

## A7 follow-up language fixes complete as dev — 2026-11-12

User selected general repair of A7P-Q013/Q020/Q027 and said continue duringwork.
Completed code/regressions/devcheck, NOT freshA7measurement/repackage/liveLLM.
Stillhus-llm-rag/basef61b0fd+priorWIP, no commit/push/deploy/provider/DB/account/
advisor/env/template/keyread. CURRENTv4/lexical/LLMoff, assets/data/gold/run/review
unchanged. Previous24Googlecalls exhausted, no freshbudget authorized.

Onlyruntime app/hus/question_routing.py and answer_support.py changed from prior
baseline. Pilotcontexts dao tao/chuong trinh/trien khai/de an/du an/mo thi diem
removed only for assessment detection, not nakedbai thi diem; realexamclause
stillactive. SharedASSESSMENT_COMPOUNDS/VALUE_COMPOUNDS/FURTHER_STUDY_TERMS keep
same priorroutingsemantics outside boundedpilot. Clauseinitial tim hieu added
COMMAND_SYNTAX; factualskillstillrequireswords. Furtherstudy dua tren normalized
onlywhenfurtherstudyrequested/notnegated; sourcegroupmustbeF1further_study and
explicitpositivebasis(la tien de/nen tang/co so,etc) without khong/chua in same
sentence. BasisquoteIDsareforcedintodisplay,samesource/edition/variant/review.

Newnegative revealed scattered dinh luong+thu tu could satisfy luong tu after
imperativeremoval. Existingknownsciencecompounds nowmustoccurcontiguouslyin
ONEbodyofsamegroupandthatbodyrendered;notmetadatatitle/crosspassagestitching.
No QID/evaluation/gold imports in runtime, noBM25/ranking/index/prompt/LLMchange.

New tests/hus/test_followup_language.py39tests. Initial35:18RED17GREEN; later
4compoundnegativesRED;final39GREEN15.59s. Final broad593routing/RAG/API including
39new pass478.74s;all489LLM pass124.76s;oneexistingStarlettewarningeach. Ruffpass.
Notfullrepo/browserrerun. 593includes39,don'taddrepeatcounts asindependentwork.

Ignored backups/hus_a7_language_followup_20261112 has beforeprotect/diagnostics,
RED/GREEN/JUnit/logs,dev_check,sealer;don'trerunone-shotwriters. New immutable
data/hus/qa/20261112/a7_followup_language_dev_r1 report,before,after48,audits,
delta3AIreview,pins,verification,manifest;manifestSHA
f4e3e27006ab7057519d56f1698075ddfd7c7575759edc27115b7e11fd3b8fe6.
2583preexistingfilespinned,2581unchanged;ONLYtwoaboveruntimefileschanged.
Allpreexistingdata/gold/packs/runs/reviews/receipts/ZIPsunchanged.0newGooglecalls.

FreshDEV48requestcollection:36/36positiveANSWERED(notnewcompletenessscore),
sourceaudits48/48;onlyQ013/Q020/Q027responseschanged,F2andcontrols12eachexactsame.
Retrievalcalls47exactsame,Q013newlyreachessearch. RootAIread3fullnewreplies+
citations/targets,entailed/completerelativetoquotes;human0,notacademic/independent
acceptance/readabilitymeasurement. Q013has720/date/pilot+samewebcontextunknown,
Q020fullvisualchannelunit+extraAIcontext needs_review/citationAI/noofficialclaim,
Q027logic/modelingANDbasisrelationshipwithfullquote,warningsunknownpreserved.

OldA7postfixresults23/24Recall33/36completeunchanged/replayreproduces;cohortnow
USEDTUNING/retiredtodev,doNOTreuseasfreshA7. OldA7r1/r2alreadydev. Nextfreshcohort
>=48/12eachmajor/sourceauthoredfrozenBEFOREinferencewithfinalcode/exposure/review.
OldL5v4reviewcachedreplayreproduces. L5v3preparedr1NOWPINSSTALE because runtime
changed;don'trunoldpreparedorclaim67tests/preflightpermitsnewcalls. Needfreshprep/
preflight/pinsANDseparateGooglebudget;noauthorizationimpliedbycontinue.
SubmissionZIP/checkerr2alsoPRE-FIXsnapshotimmutable;localmachineacceptanceisfor
oldr2,notnewruntime. IfselectnewbaselineforotherWin64/Py311target,NEWpackage/
checker/hash/receipt+targetcheckneeded. Don'toverwriteoldZIP/receipts or silently
shipoldkit asnewcode. No newfreeze/repackage done in this baselinefix task.

New docs/RAG_A7_LANGUAGE_FOLLOWUP_2026_11_12.md; roadmapmovesnexttofreshA7,
L5reprepare,A8newpackage/othermachine. HistoricalA7report/preflight/operations/
submission/targetguide/rootREADMEannotatedwithoutmodifyingsealedartifacts.

## Submission machine clarification — 2026-11-12

User explicitly confirmed current host is NOT submission/demo machine; target is
another Windows64-bit with Python3.11. Do NOT relabel localclean-install receipt
as target-machine acceptance. Actual target install/browser/source/rollback and
operator acceptance still pending; no direct target access/results supplied.
Keep A8 open for that target, lexical/v4/LLMoff; no Google budget granted.

Supplement backups/hus_submission_20261112_r2/CHECK_TARGET.py standardlibrary
only, adjacent originalimmutable2ZIPs. Validates SHA/WindowsAMD64/CPython3.11/
64bit, freshroot/nooverwrite, freshvenv/offline25wheelinstall,pipcheck,20API/menu2124,
safeenvironment/log/report/custommanifest in target-receipt (even on failure).
ChildPython explicit-Xutf8 and-I, appcheck-B, noenvfiles/key/provider/download.
--run-demo optionally launches loopback afterchecks;manualreviewstillpending.
Python chosen because currentPSscriptExecutionPolicy disabled.ps1; no policy
change/bypass/escalation. OldfailedPSprobe neverraninstaller. Pythonprobe r1
failedCLIstdoutUnicodeEncodeError underisolatedWindowsCP1252 (install/pipcheck
passed), preservedreceipt in backups/hus_target_transfer_script_20261112_r1.
FixedexplicitUTF8, r2fullinstall/APIpassed. Finalimportsort/Ruffpassed; r3same
fullchecktest for exactdeliveredscript, freshpath and priorreceiptsuntouched.
R3 passed; deliveredscriptSHA2bd78346e5ce6b5a11b97cc4da022f167eb623301d77720f6367096cee0ae7a4.
Existingroot negativeprobe exited2 and preservedreporthash. Supplementreceipt
manifestSHA060be4cef6d1fcf3fa07c7eb0fe10e339861f436065fb259e3fbd848f34c89fb.
Kit includes README-MAY-KHAC.md/TRANSFER_MANIFEST.json and receipt-target-status;
original2ZIP hashes unchanged. Actualothermachine execution remains pending.

Roadmap/rootREADME/A8report/L6A8notes nowstate knownothermachineWin64/Py311.
New QA/20261112/submission_other_machine_r1 binds userclarification/priorlocal
receipt/kit/script/localinstallerprobe, NOT actualtargetresult. Do notoverwrite
sealedoldlocalreceiptwithnewconfirmation. Local rawscriptprobe dirs distinct
from target receipts user will create onothermachine. Neverclaim localrehearsal
is externalmachineverified. No commit/push/deploy or runtime/data/source/gold/
review change; oldA7threefailuresremain and L5Googlebudget remains pending.

## A8 fresh venv/real HTTP/browser verified locally, target identity pending — 2026-11-12

User selected A8 target-machine installation/check. Async question whether current
Windows host is submission machine still unanswered at sealing. Do NOT claim
different/actualtargetmachine acceptance. No newGooglebudget granted; old24spent.
Stillhus-llm-rag/basef61b0fd+priorWIP,CURRENTv4/lexical/LLMoff,no env/template/key
read/edit,DB/accounts/advisor,commit/push/deploy. All test servers stopped.

tools/package_hus_demo.py now includes newA7postfixreport+L5v3preflightdoc in
publicallowlist; generatedREADME and run_hus_submission.py limitstrings shownew
A7Recall23/24,complete33/36/3refusals plushistorical19/24,27/36 unchanged.
No app/runtime/UI/retrieval/data/gold/run/review change. DocsHUS_RAG_SUBMISSION
adds offlineinstall/receiptdirections; roadmap/newreport/rootREADME updated.

Fresh immutable ZIP backups/hus_submission_20261112_r2/hus-rag-demo.zip,
205payloads/67070408bytes/SHA b228bbad1353e2f11a655b50a1cd456ccdf9e8d116edf139f8da5fcdb75e0df8.
Adjacentwheelhouse-win-py311.zip25wheels/25814762bytes/SHA
b176282aeeba6bcc48fa5fc62af8e14be18bc3bfc6e00411d25d102c04234b9b.
Wheels recovered BYTEUNCHANGED from existinglocalpipcache.body/wheels, exact25
dependencyclosure of existingpinnedruntime, NOT rebuiltfrominstalledpackages.
Offline--isolated/noindex/nocacheinstall succeeds into newlycreatedvenv,
include-system-site-packagesfalse/usersitefalse/all27distswithinvenv(25runtime+
pip/setuptools);basePython3.11.9/Windows10.0.26300AMD64 reused. Pipcheckpass.
No packageindex/network/download/no PythonOSinstallation or othermachineclaim.

Ignored backups/hus_targetcheck_20261112_r1 holds scripts/wheels/clean_venv/
extracted/logs/images/proofs; never rerun one-shotsealedwriters.20APIinprocess/
menu2124pass,sourceimportfromextracted/-I/-B. Realfreshvenvserverloopback3phases
v4->v3->v4,each12PDF+2DOCXGETbytes/SHAandHEADpass,F2MAT3533=3,LLMfalse even
inheritedon/vector/invalidroot. Copiedselectorrestoredbyteexact,all205payloads
matchmanifest/currentpublicallowlist. Sharedrootselector+oldZIP untouched.
48oldnew-A7rawrequests viaactualHTTP produce exactsame48responses;compatibility
checkNOTnewscore/review. ThreeA7P-Q013needs_clarification,Q020/Q027no_information
preserved. No independentacceptance/humanreview gain.

BrowserChromiumheadlessusingoldrunnerdependency againstcleanvenvserver:
1380/390pxmenuF2/credits,EnterF3,AIlabel/consent/LLMdisabled,majorchangeclearsold
users/citationswithnewwelcome,F1newscope,nooverflowpass;rootviewed2screenshots.
NotfullA6/manualacceptance. Probeattempt1wrongviewportargTypeError,attempt2
wrongexpectedassistantcount(0vs1newwelcome)logsretained;onlyprobe correctedto
existingcontract,attempt3pass. Noappfix/loweredproductcriterion. proof.jsonkeeps
initialbrowserfailure;sealedreceiptbindsfinalbrowser-r3 plusfailurehistory.

16packageunittests0.71s+Ruffpass;notfullsuite.2570preexistingdata/runtime/UI/
service/evaluation+oldZIP filesSHAunchanged. FreshL5v3preparedpinsstillmatch;
tools/package/launcheranddocsnotinLLMmeasurementartifactpins. 0provider/external
attempts (socket/providerconstructor denied;browsernonloopbackblocked),no key.
QA/20261112/submission_clean_install_r1(report/environment/api/browser/exact48/
wheelinventory/verification/manifest) sealed,manifestSHA
34fa61e01682aaeb7b8d4bc22c53346ca7e73bc73fe03df25a5adb2d0024caea.
Status local_clean_install_verified_target_identity_pending. Userconfirmation
null,different_machine_verifiedfalse,public/load/security/operatorNOTaccepted.
New docs/RAG_A8_TARGET_CHECK_2026_11_12.md has kitSHA/receipt/reproduction/pending.
Do not overwrite anyoldreceipt ifuserconfirmsmachine later; addnewreceiptbinding
thisone. Ifdifferentmachine needactualaccess/output,notinferfromcurrentlocal.

## L5 compact v3 offline preflight sealed, live budget pending — 2026-11-12

User selected L5v3 then L6, explicitly Google needs separate new budget/old24spent.
Completed concrete offline prep/privacy review, NOT live measurement/activation.
Still hus-llm-rag/basef61b0fd+existingWIP, CURRENTv4/lexical/LLMoff. No env/template/
key read/edit, Google/network attempt, runtime/source/retrieval/gold/run changes,
DB/accounts/advisor, commit/push/deploy. Do not use exhausted old24-call approval.

New sealed source pack data/hus/evaluation/llm_v3_v4_dev_20261112_r1 and prepared
runs/llm_v3_v4_prepared_20261112_r1. SAME deterministic exposed36 cases/QIDs as
oldv4 (not freshquestions/holdout); newpack/currentbaseline/pins/protocolv3.
24positive8F1/8F2/8F3;12controls;6positiveeachmajor but totalCS8/DS12/Math8/MI8.
Sourceaudit36/36,24eligibleprompts/0budgetfallback,controls12no prompt.
98,268totalpromptchars,2711..7328each. F1/F3documentv3,F2evidencev1;1024outputtoken
cap unchanged. FourstressQ005/013/021/029 have19/19/23/19leaves,39/39/41/39units;
copyJSON2710..2842chars NOT live/tokenproof. ThreeMAT3148sameconceptdifferentmajor.
Q0225leaves/fourbullets,Q025includes1993/nameANDprogramupdate. No acceptancegainclaim.

Payload export ignored backups/hus_l5_v3_prepare_20261112/payloads_r1 sealed.
RootAI read24exactquestion/evidencepayloads; allowlistedpublicsnapshots only,
system/user2messages,nohistory/accounts/grades/key/tools. No actualsecretcomparison.
Ignoredprepare/audit socketguard0attempts,67existingevaluator/budget/readinesstests
pass74.75s/oneexistingStarlettewarning;notfullrepo.2557preexistingdata/runtime/
staticfilesSHAunchanged;cachedoldL5v4review/newA7reviewreplaysreproduce.

QA/20261112/llm_v3_preflight_r1 report+manifest sealed;manifestSHA
819fe0769b9ef2521db9fc3008ad9b630a2ab30c92bbe5c152f26449137758cd.
Sourcepackmanifest8e8b0c0a8fb73c840685c756a3216e578072640b71260c452a2ef828464d69ca;
preparedmanifest154fa5b126abfd05cedcdeeea3bb7d90c6597c329dd80fd21c12c1f57ccbbbc8;
pinssha d441a8d4a478ffe512f4957915b1b1b002a9bc348549452f5a7db48549d1f050.
Never rerun one-shot sealed writers; usefreshdirs if newprepnecessary.

New docs/RAG_LLM_V3_PREFLIGHT_2026_11_12.md, roadmap/operations updated.
Proposed (NOT authorized yet): max24Googlecalls gemini-3.5-flash-lite,8eachfamily,
controls0,>=5s spacing,1concurrent,no retries/model switch,stopafter429,
GoogleHTTPSdirect/publicquestion+evidence only,backendexistingkeynotprint/edit.
Output<=1024/call24576total,inputtokens/costunknown. HTTPX20sperphase nottotal.
Get explicit freshbudget approval after presenting concretecohort; then checkpins,
runfreshlivefolder usingexactfrozenA notnewretrieval; reviewALLexactoutputs/fallbacks,
actualmodel/token/latency/errors; separateused/fallback andstresscases. Oldreadiness
stillkeep_disabled/pins_changed/readability_regressed. No L6on until truegain,
coverage/content/fallback/demolatency/operatoracceptance;preflight/mock notsuccess.

## Missing-evidence source review complete, no promotion — 2026-11-12

User selected review Q001 variant and further F3/validity review. Completed
bounded read-only review, not baseline fix or source publication. Still hus-llm-rag,
basef61b0fd+priorWIP; CURRENTv4/lexical/LLMoff, no Google/provider/DB/account/advisor,
no env/template/key read/edit, no commit/push/deploy. Existing runtime/data/
metadata/gold/run/review unchanged. Never read root .env or .env.example (both
user-managed credential-bearing files). Old24Google-call budget remains exhausted.

New immutable data/hus/review/source_scope_20261112_r1 (report,captures,q001_review,
f3_review,validity_matrix,image_review,verification,manifest); QA/20261112/
source_scope_r1 receipt binds reviewmanifest. Custom manifest schema
hus-source-scope-review-1.0, not LLM read_sealed schema. Ignored scripts/raw/images/
network/test/protected snapshots in backups/hus_source_scope_20261112. Do not
rerun sealed writers or overwrite artifacts. Only docs/memory/newreviewdata this
turn, no product/tool/test code changed.

Q001 here means OLD A7V4-Q001 (standard variant), not new A7P-Q001 (CLC2018).
Old chunk f526a537e9132345485d15b065a5697b stillunknownvariant. Fresh HTTP200
MIM/vi/khmt-tt has same selected admission2012 quote; prose doesn't name standard.
Current page links standard-named2023 files, not explicit historical scopebinding.
Fresh VNU2012 admissionsFAQ post12528 explicitlyfirstcohort2012 but no variant.
Fresh HUS2024 admissionsplan1616 physicalp4 lists7480113/2160QĐ28-06-2022/start
TRAINING2012/latest2023; not variant-specific admission. Existing ec312...2015PDF
p1/p4 explicitlystandard+52480105 but says enterednationaldisciplinelist2012,
notadmission; p4decisionnumber/date blank. Partialcorroboration only, variant
binding remains open. No CLCinference; CLCpage2018 captured as separatecontrol.

New2012standardPDF lead hus.vnu.edu.vn/sites/default/files/huongdan/09_0.pdf:
web index returned text declaring4115QĐ30-11-2012/standard/52480105; directHTTP
ANDHTTPS fetch both404, no binary/hash/image recovered. Do NOT claim fresh PDF
validation or fullgapclosed; indexleadonly. Web tool autoHTTPS timeout/cachemiss
forMIM isn't HTTP404. Initialsandbox7ConnectErrors separate from actual approved
publicdownload results. Bounded8URLdirectGETs,6captures success(3HTML/3PDF),2schemes
same2012lead404. PublicprimaryURLs only, no auth/providerkey. No autoreviewrejection.

Two fresh syllabusPDFs match pinned bytes: S06CS2024 56d751cc897fe12626f05ebaa28842440e3b6402dede058bd280d6f3c1def2d0;
S07MI2021 6e049389bc467f41ea6d48cffd66182c50bf52e77efdbb57868dbe6f14f33b7b.
Actual11PDFimages viewed using pdfplumber/PDFium108dpi: admissions2024p4;
standardCS2015p1/4;CS2024p1/2/86/87/162;MI2021p1/256/257. Images/source hashes
bound, no full-document/first-ever inspection claim. CScover2385QĐ31-07-2024
references3568QĐ18-10-2023 standard; TOCp2 separately2380forcommon/fieldblock,
do not assume contradiction/equivalence without scopes/decisions. Existing
TOC MAT1202OOPp86/MAT1208embeddedp162 vs embeddedheaderMAT1202 persists; no mapping
fix. MI2021MAT3561prereqs3508/3509 differ2023F2MAT3533; do not transferweight/prereqs.
No complete adoption/amendment/current-student applicability chain obtained by
bounded officialsearch; absence notproved, HTTP200/hash notacademicvalidity.

4F3records/8fields read in full: CSMAT1202, MIMAT3561, MathMAT2308, DSMAT3383,
16units/16objectives. AI exposed/nonindependent, human0. OOPAI missing several
2024topics(generics/functional/JavaCollections/patterns/threadsGUI) and UML/debug/
test/teamworkgoals; NLPonlyconceptoverlap withdifferent2021edition, someindex/
stringalgorithm/content/goalsnotexplicit. Math/DS have no officialsyllabus in
two selectedcandidates. Reference grounding checked Pythonclasses,SLP3index,
OpenStaxCh3intro,Matplotlibquickstart viaweb; index/API/mutableversions not
sentence-by-sentence/HUS evidence. ExtraOMGref notopened. No datarewrite.
All290F3stillgenerated/needs_review/disclosure/academicfalse/officialnull;
106candidate44CS62MI stillcandidate_not_in_default_retrieval.84canonical identity
links existing do NOTgrantfield/validityapproval. No official/academicpromotion.

70existing source/F3/guard tests pass51.14s,18deselected, no fullsuite claim/new
tests for readonlyreview. 2524preexisting data/runtime/static files SHAunchanged;
oldA7r2,newA7review,L5v4review cachedreplay reproduce; newA7pinsmatch. Counts/results
unchanged(A7new23/24Recall33/36complete stillnotfullyaccepted). New docs
RAG_SOURCE_SCOPE_REVIEW_2026_11_12.md and roadmap record findings/open evidence.
Next sourcework: recover2012original+explicitvariant/admissionidentitybinding,
reviewfield/edition/adoption/errata in NEWcandidate if selected, never relabel
unknown or reuseCLC/changeoldgold to boostscore. Baseline3misses remain separate.

## New A7 after baseline measured/reviewed — 2026-11-12

User selected fresh A7 evaluation, not another baseline repair. Completed new
source-authored 48questions/12major (3F1/3F2/3F3+3controls each). Still hus-llm-rag,
basef61b0fd+existingWIP; no commit/push/PR/deploy. CURRENTv4/lexical/LLMoff, no
Google/DB/account/advisor or env/template/key read/edit. Old24-call budget remains
exhausted. Product runtime/data/static unchanged this turn; do NOT repair the new
three misses as part of this sealed evaluation or replace its gold/results.

New tools/hus_a7_postfix_cases.py with fixed declarations, source-only builder,
prior-input wording+oldA7target exposure. evaluate_hus_a7.py supports freeze cohort
postfix-20261112 and pins newbuilder/newtests; freeze rejects knownwording/reused
A7targets. hus_a7_cases.check_source_evidence validates optional full source_scope
against bound source. Historical cohorts/replay backward compatible. New
tests/hus/test_a7_postfix.py 13tests; 108total evaluator/metrics/oracle tests pass
34.78s, Ruff/scoped diff/linkchecks pass; one preexistingStarlettewarning. No full
repo/UI rerun or claim. Technical review by root only, no independent reviewer.

Pack data/hus/evaluation/a7_postfix_20261112_r1 sealed before prediction; recorded
2026-11-12T12:34:03.433731Z (19:34:03+07). Pack SHA
9d47c07b0c9999690adfd51b0758cec30ab7cd4057badf4f270bb40c88973f7c, manifestSHA
5fccce4eb65aad644f8775fdba11ab1147f33dd85abdd4ffb43b77258c1097bc. 0exact wording
overlap against22pinned evaluation inputfiles,0/36oldA7targetidentityoverlap. New
F2/F3codes/topics differ oldA7; source/runtime/families alreadyseen byAI, human0,
nonblind/sourceauthored/not independent holdout. Selfcohort excluded from novelty
scan for repeatability, not permission to relabel samequestions as freshholdout.
Gold authored from snapshots only. Prereqs cover present/unknown/conflict/unresolved.

One actual HTTP/TestClient collect to runs/a7_postfix_lexical_20261112_r1, all48
responses persisted before audits/metrics. Root read ALL48 exactdisplay+targets+
facts/citations in four packets under ignored backups/hus_a7_postfix_20261112.
Review evaluation/reviews/a7_postfix_ai_20261112_r1.json, score overlay runs/
a7_postfix_ai_review_20261112_r1. 33answered positives entailment/completenesspass,
3noanswers entailmentNA/completenessFAIL,12controlsNA+auditpass. Q002alternative
CLC2019PDF has Englishlevel4/6+communication/professional exchange, sourceversion
andvariant visible; passes content despite webgoldproxyuncredited. Q0262015PDF
teaching source also complete. Do not autoequate source/schema/testcount to review.

New routedRecall23/24=95.83% threshold MET; conditional23/23=100% notsubstitute,
1no-call retained. F2facts/types/source12/12,controls12/12,sourceintegrity33/33,
all48sourceauditpass,scope/filter/HTTPerrors0. AIentailment33/33answered; AIcomplete
33/36=91.67%, falseabstention3/36 => A7 NOTfullyaccepted. BymajorRecall/complete:
CS6/6+9/9,DS5/6+7/9,Math6/6+8/9,MI6/6+9/9. No human/independent/academicacceptance.
Goldquoteproxy20/24 notsemanticmetric. 13localPDF URL bytehashchecks (URLs, not13
distinctfiles); no remotewebhealth/academicvisualreview. LocalHTTPp50/p9527.9801/
64.4413ms after service/config, no explicit chatwarmup/firstchatretained, notnetwork
orproductionSLO. Some answers verylong; no readability/token/LLMquality measurement.

Failed positives A7P-Q013 introKHDL QD720/thi-diem routes f3/suggested_assessment,
no search then needs coursecode; Q020 contentMAT3383 data/visualchannels searched
correctfield+targettop5 but refuses; Q027 Mathfurtherstudylogic/modeling targettop5
but refuses. No new runtime fix. Future diagnostic/fix requires generalregression,
notQIDpatch; if tuned on these, retire newset todev and freeze another evaluation.

QA/20261112/a7_postfix_r1/report.json+manifest sealed:108testXMLhash, exactpack/run/
review bindings/exposure/config/promptSHA and 2507protected preexisting data/runtime/
static files unchangedSHA. Newmeasurement+review replay, botholdA7reviews replay;
newpinsmatch current, oldevaluatorpins correctlyhistorical. No oldsource/run/gold/
review/QA overwritten. Do not rerun fresh-path writers or edit sealed artifacts.
Docs RAG_A7_POSTFIX_2026_11_12.md + roadmap reflect threshold met/fullgate failed.
Prior A8 ZIP/QA remains its historical package; not repackaged/published this turn.
Next roadmap: diagnose3misses separately if selected; freshA7afterfuturetuning;
L5v3 requires newpins/cohort/Googlebudget thenL6operator review, LLMkeptoff.

## Baseline after A7, v4 readiness and local submission package — 2026-11-12

Current hus-llm-rag, verified base HEAD f61b0fd (older uncommitted/publication
notes below are historical). This turn changes are local, no commit/push/PR or
deploy. CURRENT hus-data-20261111-v4 unchanged, lexical/LLM off. No Google calls,
no private env/template/key read/edit; .env.example also contains a user-managed
credential and must never be read/printed/staged. Old 24-call budget exhausted.

User selected L6 checker/A8 then explicitly selected general baseline repair
after A7. Completed all authorized local work; no new A7 freeze or provider
measurement. Only product changes app/hus/question_routing.py and answer_support.py:
bounded domain compounds avoid folded do-thi/exam and uoc-luong/salary collisions;
historical admission phrases reach retrieval while current/metrics/later requests
remain blocked; explicit program aims precede career words; ambiguous name terms
require course context; bounded presentation syntax; explicit program-purpose
source patterns; no outcomes-only substitution; former-name evidence must exist
and be rendered in the same exact source scope. No BM25 ranking/data/F2/citation/
LLM prompt/protocol/token budget changes. No QID/evaluation imports in runtime.

50 new tests in tests/hus/test_baseline_language.py. Initial 27RED/19GREEN then
scope diagnostic corrected test expectation, not gold: Q001 source2012 variant
unknown, CLC2018, cannot answer standard-specific question. It now searches but
correctly refuses without matching variant. Eight other old misses answered;
new QA/20261112/baseline_a7_dev_r1 has exact48 responses/traces/source audits48pass,
35/36positive answered (NOT completeness/acceptance), 12F2+12controls exact same.
Only9diagnostic responses changed inclQ001reason. Read all changed quotes; AI
exposed/nonblind, human0. A7r1/r2 now explicitly retired to dev after tuning;
keep historical19/24recall27/36complete and all old run/gold/review bytes unchanged.
New A7 needs fresh>=48/12major, source/gold before inference and declared exposure.

Verification:782 related backend/API/routing/F2/evaluator/readiness/package tests
passed476.13s before two narrow final guards (former-name context render, inline
purpose/outcome heading). Both regressions RED->GREEN. Final430routing/support/
guard tests pass62.40s incl50new; final489wholeLLM pass131.26s incl9newreadiness;
16package tests+8JS pass, Ruff/scoped diff checks pass. Counts overlap; not full
repo green. One existingStarlette/httpx warning. 2585 preexisting data/hus files
unchanged SHA; twoL5+twoA7 cached replays reproduce. Evidence/logs/scripts ignored
backups/hus_baseline_a7_20261112; sealed QA/20261112/baseline_a7_validation_r1.

L6 tools/check_hus_llm_readiness.py now auto-selects v4 pack/pins, validates
provenance/manifest/release/cohort/effective request and source oracle, never
rebuilds oldv2 prompts with v3 or executes RAG/provider. Returned model must match;
report adds fallback latency/reasons. 9newtests tests/hus/llm/test_readiness_v4.py.
NEW evaluation/runs/llm_l6_v4_readiness_20261112_r1 before baseline and r2 after:
both keep_disabled, pins_changed/readability_regressed (old v4 L5 16used/8fallback,
2better/13same/1worse). No new livev3/latency/operator acceptance. Never enable flag
from this assessment. Legacy checker tests still pass. Docs HUS_LLM_OPERATIONS.md
updated; historical L6/L5 artifacts untouched.

A8 tools/package_hus_demo.py explicit public allowlist + deterministic fresh ZIP,
hash verification/refuse overwrite/private paths/symlinks; tools/run_hus_submission.py
forces local lexical/LLMoff/no env-file with --check API/source probe or loopback
uvicorn port8011 one worker/access_logfalse. New requirements-rag-demo.txt with
existing requirements-lock constraints (lock unchanged). tests/hus/test_submission_package.py
16pass. ZIP backups/hus_submission_20261112_r1/hus-rag-demo.zip, 203payloads,
67062026bytes SHA fdb3df4c915c2fff27585350cc8ef79df8ead61e2cb551ffc68fefbc9e2d449d.
No .env* (includingtemplate), keys/accounts/DB/git/backups/cache/venv bundled.
Extracted-source isolated -I child imports app from copy,20APIpass/menu2124,
v4->v3->v4 rollback/caches and all12PDF+2DOCX hashdownload eachpass. Copy selector
restored bytes, shared CURRENT/ZIP unchanged. Existing Python3.11.9/site-packages
onWindows; pipcheckpass, NOTfreshinstall/different-target-machine/browser/load/
publicsecurity acceptance. No publish/deploy. QA/20261112/submission_r1 sealed
report/proof; candidate and final package checks in ignored backups, do not rerun
fresh-path writers or overwrite artifacts.

Docs updated README, roadmap, runbook and new RAG_BASELINE_A7_DIAGNOSTIC_2026_11_12.md,
HUS_RAG_SUBMISSION.md, RAG_L6_A8_2026_11_12.md. Next: freshA7, source review for Q001
variant (do not infer/change old metadata), newcohort/pins/budget if L5v3 requested,
then operator L6; verify package on actual submission machine if different.
