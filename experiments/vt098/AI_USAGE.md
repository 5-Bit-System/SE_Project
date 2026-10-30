# AI usage — VT-098 requirement 3

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
The current request is only requirement 3, not the mutation/load experiment.

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
confidence only in the isolated SQLite slice. Production auth/CSRF/eligibility,
PostgreSQL, browser E2E, process death, coverage, mutation and 150-task performance
remain unproven. No main-branch merge is authorized or performed.
