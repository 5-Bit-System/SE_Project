# AI Usage Log — VT-098 requirements 1–5

Tool: coding agent Codex in this conversation, Git/PowerShell, Python unittest,
SQLite and Pydantic. Do not infer an undisclosed model/version. Date: 2026-10-30
(Asia/Bangkok). This is an individual artifact for Dương Văn Tài, 23001925.

## Actual user prompt

> 3. Test-first AI-assisted implementation (25 điểm)
>
> - Chọn một vertical slice nhỏ nhưng chạy được của change request.
> - Tạo nhánh Git riêng; ghi commit ban đầu được dùng làm baseline.
> - Viết hoặc sinh test để test thất bại đúng lý do trước khi sửa code; lưu evidence của lần fail.
> - Dùng AI hỗ trợ tạo patch nhỏ; review diff trước khi chấp nhận. Không merge code không hiểu.
> - Sau patch, chạy lại test và ghi evidence pass; nêu file/commit/PR liên quan.
> - Nếu repository chưa đủ điều kiện triển khai change request, tạo executable test harness hoặc characterization test trên module gần nhất và giải thích giới hạn.

Context: AI-07, official 5-Bit-System/SE_Project repo; safe retries without duplicate
data/transactions; time/network/order-related flaky risk; required pairwise
technique; eventual `>` to `>=` mutation, 150 concurrency / p95 <= 4.0 seconds;
AI generates tests and at least two weak/duplicated tests must be edited/deleted.
At that stage the request was requirement 3 only; requirement 4 followed later.

## Used outputs, changes and evidence

- AI generated the initial executable SQLite scaffold and loaded the actual
  `SemesterPlanInput` declaration rather than inventing a different body contract.
- Two generated draft tests only asserted 201 and passed despite duplicate IDs.
  The same initial run contained a meaningful result-equality failure. See
  `draft-red.json` and commit `9b18b7d`.
- The agent edited D1 into full JSON/version + independent DB row-count checks.
  It replaced duplicated D2 with errors after each write, rollback checks and
  retry. See `a20c996` for before/after test code. These are executable changes,
  not merely a description of hypothetical tests.
- The reviewed red suite and the green suite use identical test bytes. The
  corrective patch affects only the harness transaction/receipt path. Review
  decisions and limits are recorded in `PATCH_REVIEW.md` and `PLAN_REVIEW.md`.
- No test plan, data, prompt, mutation or reflection was copied from a teammate.
  Existing repository source/tests were read only to identify contracts and
  mocked versus real integration boundaries.

## Responsibility and limits

All implementation and the recorded diff review were performed by the coding
agent. They are not proof of an independent student review. The student must
read and understand the exact diff and tests before accepting/submitting them;
no fabricated human approval is recorded. The observed evidence increases
confidence only in the isolated SQLite slice. At the end of requirement 3,
coverage/mutation/load were pending; requirement 4 below records them at harness
level. Production auth/CSRF/eligibility, PostgreSQL, browser E2E and process death
remain unproven. No main-branch merge is authorized or performed.

## Requirement 4 continuation (same individual conversation)

The user subsequently requested the boundary mutation `>` to `>=`, demonstration
that a test detects it, line/branch and risk coverage, at least two flaky risks,
and 150 simultaneous tasks compared with p95 4.0 seconds (or a disclosed harness).
These are the actual supplied requirements, not a teammate's prompt.

The agent used a separate temporary mutation worktree and preserved control versus
mutant test output. It installed coverage 7.17.0 into a workspace virtual
environment, added one 16 KiB body boundary test after inspecting missed branches,
and reran mutation against identical 19-method test files. No test was weakened
to kill the mutant or to improve percentages. The missing schema guard remains
disclosed. `harness.py` on the submission branch is byte-identical to `91b2030`.

Six guarded functional runs vary wall clock, order and hash seed, block sleep/DNS/
socket connections, and retain every result. Nine load bursts offer 150 tasks
each, retain all 1,350 samples and check SQL counts; actual peaks 149–150 and the
absence of real HTTP/PostgreSQL are disclosed. See QUALITY_REPORT.md and evidence
JSON for measured numbers and limitations. A raw report that includes AST schema
lines under academic.py is explicitly distinguished from production API coverage.

All code, data, interpretation and self-review are by the coding agent; no
independent student/team approval is claimed. No merge was performed. Requirement
5 was supplied subsequently and is documented below.

## Requirement 5 — actual user prompt

> 5. Engineering evidence và reflection (15 điểm)
>
> - Tạo traceability: Acceptance criterion/Risk → Test case → Test file → Commit/PR → Kết quả.
> - Lập AI Usage Log: công cụ, prompt chính, output được dùng, thay đổi/bác bỏ và evidence.
> - Chỉ ra 2 điểm AI-generated code/tests có vẻ hợp lý nhưng không đáng tin ngay.
> - Viết reflection 250–350 từ: điều gì khiến confidence tăng lên, điều gì vẫn chưa được chứng minh và test tiếp theo có giá trị cao nhất.

## Consolidated log — tools, prompts, outputs, review and evidence

The prompts below summarize the actual user instructions, not invented agent
conversations or teammate prompts. Their full wording for requirements 1–5 is
also recorded in the AI appendix of the local VT-098.tex report.

| Stage / tool | Main supplied prompt | Used output | Changes/rejections and evidence |
|---|---|---|---|
| 1 / Codex, GitHub connector, Git, PowerShell | Problem statement, 3–5 AC, 2+ constraints, invariant; plan before code; review 2+ points using repository | 5 AC, 3 NFC, invariant I1, plan and file list | Reject title/body-only dedup, process cache and replay before account verification; `PLAN_REVIEW.md`, immutable baseline source `docs/SEMESTER_PLANS.md:24`, service `:90–157`, auth/portal `:33–40` |
| 2 / Codex, Python combinatorial check | Unit/API/E2E strategy, 10+ cases, pairwise, 2 negatives and failure path | 20 planned TC, 8 binary-factor scenarios | Verify 24/24 pairs; separate boundary/crash tests; API/E2E remain planned. Executable factor rows and pair check in T:92/100 at `6824962` |
| 3a / Codex, unittest, SQLite/Pydantic | Executable slice and meaningful red before patch | Runnable duplicate-create scaffold, weak AI drafts D1/D2, result-equality red test | `9b18b7d`, `draft-red.json`: 2 weak tests pass despite different IDs; not an import failure |
| 3b / Codex, Git diff | Review AI test/code diff and preserve fail → patch → pass | D1 becomes JSON/version + independent counts; D2 becomes injected rollback path | `a20c996` has the edited executable tests before patch; `91b2030` adds atomic receipts. `reviewed-red.json`/`green.json` have identical test hashes; `PATCH_REVIEW.md` records agent self-review |
| 4 / Codex, Git worktrees, Coverage.py 7.17.0, Python runner | `>` → `>=` in temporary commit; coverage/risk; flaky review; 150 tasks/p95 4.0 s | `quality.py`, body byte boundary test, coverage/mutation/flaky/load JSON | Mutant killed, missing schema guard disclosed; actual peaks 149–150 disclosed. `6824962` code/data; `cf167fe` final mutation log and interpretation; runtime matches `91b2030` |
| 5 / Codex, Python read-only validation, Git | Traceability and log, 2 untrustworthy AI outputs, 250–350-word reflection | `ENGINEERING_EVIDENCE.md`, this consolidated log, `REFLECTION.md`, report section 7 | Explicitly retain unimplemented TC12–13/19–20; no fabricated PASS, independent review or personal execution claim. Reflection has 286 whitespace-separated words; method/line/commit links checked against source |

## Two untrustworthy AI outputs and actual edits

- **D1:** accepting two status-201 results ignored duplicate IDs. Edited
  `test_ai_draft_retry_status_only` into `test_retry_response_and_counts` before
  the patch. The independent SQL count + JSON/version oracle is necessary to
  test the invariant; response success alone is insufficient.
- **D2:** `test_ai_draft_duplicate_happy_path` repeated the same successful path.
  Replaced it with `test_failure_before_commit_rolls_back_then_retry`, injecting
  exceptions after plan, audit and receipt writes before retry. Git preserves
  both versions. Plan review R1/R2 is not counted as editing executable tests.

Both changes were made by the coding agent, not independently by the student.
This disclosure does not manufacture a student approval. The student must read
the actual diff/tests and take responsibility before submission/team review.

## Reflection and final scope

`REFLECTION.md` contains an AI-assisted evidence-based draft, with 286 words
between its explicit markers (whitespace-token count). It does not say the
student personally ran or independently reviewed work performed by the agent.
No material was copied from another member's plan/data/prompt/reflection.

Documentation work does not rerun/overwrite historical experimental logs or
claim additional production verification. All app/database production sources
are unchanged; no merge is authorized or performed. The branch link and runnable
README satisfy the GitHub evidence route; a PR number is not invented after the
connector's 403 response.
