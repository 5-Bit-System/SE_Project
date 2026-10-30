# Implementation plan và self-review trước code

Baseline chính thức đã kiểm tra qua `git ls-remote --heads origin main`:
`7b387a394e334e217733a571ee76a573157a24f2` (PR #16 Dashboard).
Nhánh `bt3/23001953-VT-101-search-contract`; worktree riêng
`D:/SE_Project/backups/bt3_23001953`. Root vẫn main với 14 file modified,
4 entry untracked, không staged; không stash/reset/copy các thay đổi đó sang bài.
Memory gần nhất 29/10 đã cũ; Git hiện tại và `docs/DASHBOARD_INTEGRATION_2026_10_30.md`
là bằng chứng mới hơn. Không cần dependency từ nhánh chưa merge.

## Các điều chỉnh thật sau khảo sát

1. Phương án ban đầu: mở rộng `/courses` để trả `{items,total,page}` → evidence:
   `app/api/routes.py::courses` khai báo `list[Course]`, `app/static/app.js`
   gán mảng vào state.courses; test metadata duyệt response như list → thay shape
   vi phạm risk VT-101 → **bác bỏ**, thêm `/courses/search` có schema riêng;
   không đổi code endpoint cũ. Không ghi đây là lỗi production đã xảy ra.
2. Phương án khảo sát: SQL `ORDER BY/OFFSET` và index để hỗ trợ pagination →
   evidence `HusRepository._load_catalog/_validated` lấy payload revision đã hash,
   `app/catalog.py` còn hỗ trợ JSON adapter; Course thuộc snapshot validation →
   truy vấn bảng học phần trực tiếp có thể bỏ qua revision/evidence và ép migration
   không cần → **bác bỏ**, pure service nhận catalog, filter/sort/slice một lần.
3. Ban đầu cân nhắc sửa ô tìm kiếm legacy như một E2E UI → evidence index.html
   chỉ nạp workspace/course-status, không nạp app.js; UI active lấy nguồn VNU →
   **thu hẹp** API vertical slice, browser fetch smoke qua HTTP thực vào API;
   không giả vờ chứng minh UI VNU cũ hoặc thêm màn hình không được yêu cầu.

Đây là review của Codex trên code, chưa phải review/approval của sinh viên.

## Revised plan đã chốt

1. Runner lưu baseline, Git context, command, exit/log. Chạy regression liên quan.
2. Viết API/consumer contract test trước production, không import module chưa có.
   RED phải do endpoint/tính năng thiếu, không collection/import error. Commit test-red.
3. `app/schemas/catalog.py`: model page tái dùng Course; `app/services/course_search_service.py`:
   pure function trên Catalog; `app/api/routes.py`: một route, validation Query/Literal,
   load snapshot đúng một lần, lỗi theo boundary đang có. Không thêm catch-all default.
4. Bổ sung unit tests hàm thuần (ordering/nonmutation); GREEN API + regressions,
   review diff. Commit implementation đúng.
5. Worktree mutant riêng từ commit đúng: bắt Exception sau domain handlers và trả
   page rỗng. Lưu patch, chạy failure tests, expected exit 1; không commit mutant.
6. Line/branch coverage (coverage.py dev-only, pin riêng nếu môi trường chưa có);
   hai flaky checks: input order/shared-state và repeated/hash seed; không sleeps.
7. HTTP harness real Uvicorn app trên loopback port ngẫu nhiên, JSON fixtures
   trên temp dir; external services/startup portal tắt bằng test adapter. Warm-up
   rồi 100 async workers ×20 request ×3 run; mix filter/page/sort, kiểm response
   với oracle closed-form của fixture, ghi từng latency và summary. Browser fetch
   smoke nếu Chrome sẵn, phân biệt backend thật và synthetic repository.
8. Tài liệu, traceability, AI log, reflection AI draft 250–350 từ, PDF handoff;
   final diff/secret/quality/root integrity; commits BT3, push branch, draft PR nếu
   có GitHub capability. Không merge; nếu quyền thiếu ghi blocked chính xác.

Trạng thái lúc chốt: spec/revised plan **executed**, baseline tests **planned**,
production patch/mutation/load **planned**. Chi tiết thực thi tiếp theo ở REPORT.md
và evidence; tài liệu này cố ý lưu quyết định trước code.
