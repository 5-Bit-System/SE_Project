# Final rubric review — VT-098

Dương Văn Tài — 23001925 — SE2026-T25 — AI-07. Review date: 2026-10-30
(Asia/Bangkok). Review target before documentation fixes: `bf47b3c`.

## Kết luận trong đúng phạm vi

Bài có đủ nội dung của năm nhóm yêu cầu, đúng biến thể VT-098 và có executable
fallback harness. Đã chạy lại evidence thay vì chỉ đọc kết quả cũ. Những lần
pass dưới đây chứng minh SQLite empty-draft slice; không chứng nhận production
API, authentication, CSRF, eligibility, PostgreSQL hoặc browser E2E.
Không có merge. Đây là agent review, không giả nhận sinh viên/team đã review.

## Đối chiếu rubric

| Nhóm yêu cầu | Kết quả đối chiếu | Evidence |
|---|---|---|
| 1. Specification/plan | 1 problem, 5 AC, 3 NFC, invariant I1; plan trước code; R1–R3 sửa/bác bỏ bằng source baseline | Report mục 1–2; PLAN_REVIEW.md; source links tại `7b387a3` |
| 2. Strategy/design | Unit/API/E2E strategy và loại test không cần; 20 TC đủ cột; negative/failure paths; 8 pairwise scenarios phủ 24/24 pairs | Report mục 3–4; T pair-coverage/pairwise tests |
| 3. Test-first/patch | Baseline/feature branch; red đúng do duplicate/missing receipt; hai test AI được sửa trước patch; patch logic 27+/8−; pass giữ nguyên test bytes ở giai đoạn red/green | `9b18b7d` → `a20c996` → `91b2030`; reproduced stages dưới đây |
| 4. Test quality/performance | Mutant `>`→`>=` bị bắt; line/branch và risk coverage có giới hạn; time/order/network/concurrency review; 150 offered tasks/burst so p95 4.0 s | QUALITY_REPORT.md; original evidence và `evidence/final-review/` |
| 5. Engineering evidence | Traceability có cả case chưa chạy, AI log đủ trường; D1/D2 có before/after executable code; reflection 286 whitespace words | ENGINEERING_EVIDENCE.md; AI_USAGE.md; REFLECTION.md |
| Đầu ra/hình thức | Đúng tên PDF, baseline/branch/cam kết ở trang đầu; 8 trang chính, phụ lục AI/log tách riêng; README ngắn; không nộp ảnh thay source | Local PDF/TeX, README và documentation/layout checks |

## Kiểm tra lại bằng thực thi độc lập

Các commit được export từ Git vào thư mục audit riêng, không thay source nhánh
nộp hoặc log lịch sử. `unittest` chạy bằng interpreter đã dùng cho thực nghiệm:

| Stage | Commit | Kết quả mới |
|---|---|---|
| Draft đỏ | `9b18b7d` | 3 methods, exit 1; hai status-only tests xanh, result-equality đỏ |
| Reviewed đỏ | `a20c996` | 18 methods, exit 1; lỗi nghiệp vụ/assertion, không phải import failure |
| Patch xanh | `91b2030` | 18 methods, exit 0 |
| Bản hiện tại | `bf47b3c` | 19 methods, exit 0 |
| Mutant focused | `0a05796` | 1 method, exit 1 tại length=64 |

Thử thêm một **venv sạch không dùng system-site-packages**, chỉ cài
`requirements.txt`: 19 methods OK. Log/pip freeze ở
`evidence/final-review/readme-clean-env.json` chứng minh recipe README chạy được.

Chạy lại quality với output directory riêng:

- Coverage khớp: harness 85/85 lines, 18/18 branches; loader 13/14 và 1/2.
  Guard thiếu/trùng schema vẫn không được nhận là đã test.
- Sáu functional process mới: **114 executions pass**, dependency attempts rỗng.
- Chín load burst mới: **150 task/burst, 1.350 mẫu, zero errors**, mọi SQL/ID oracle
  pass; peak lần rà này đều 150. Max p95 mới **2,5604576 s <= 4.0 s**.
- Tính lại từng percentile và count trong log gốc: đúng 1.350 mẫu, max burst p95
  **3,0686327 s**. Không thay kết quả gốc trong báo cáo bằng con số mới thuận lợi
  hơn. Khác biệt cho thấy timing phụ thuộc môi trường, không phải chứng nhận SLA.
- Source hashes của harness/schema/test/runner khớp artifact lịch sử; runtime
  vẫn dùng `> 64`, mutant không thuộc ancestry nhánh nộp. Ruff pass.

Raw rerun logs ở `evidence/final-review/`, tách khỏi original `green.json`,
`reviewed-red.json`, `coverage.json`, `mutation.json`, `flaky.json`, `load.json`.
Review không auto-retry test fail để lấy xanh và không xóa mẫu chậm/lỗi.

## Những chỗ đã sửa trong lần review

1. Rút README thành quickstart ngắn; giữ hướng dẫn dài trong REPRODUCTION.md.
2. Sửa mapping TC05: case concurrent/new-key thuộc pairwise T:100, không gán
   riêng cho test retry tuần tự T:64. TC05 vẫn đã chạy qua pairwise.
3. Sửa câu “mọi JSON có command”: load log lưu cấu hình/mẫu; lệnh tái chạy có
   trong README/REPRODUCTION. Không thêm trường giả vào log lịch sử.
4. Tách Ruff thành style check tùy chọn; harness quickstart chỉ cần Pydantic và
   stdlib, đúng với lần chạy trong venv sạch.

Không có lỗi runtime mới được phát hiện trong phạm vi các lần chạy này; không
thay SUT/test, không diễn giải điều đó thành chứng minh không còn lỗi.

## Điều kiện cá nhân còn phải thực hiện trước nộp

- Sinh viên cần tự đọc/hiểu patch và tests, xác nhận assumptions/reflection và
  chịu trách nhiệm theo cam kết; agent không thể chứng nhận việc đó thay sinh viên.
- TC12–13 và TC19–20/API/PostgreSQL/E2E chưa chạy, đã ghi rõ. Fallback được đề cho
  phép, nhưng không được trình bày như triển khai production hoàn chỉnh.
- Nộp **một PDF** cùng **một branch/PR link** vào Assignment Google Classroom;
  không gửi email. Deadline theo Assignment, không suy đoán từ phiên này.
- Nhóm chưa review thì không merge; nhánh mutant không phải nhánh nộp.

Không dự đoán điểm số hoặc nhận đã có chấp thuận của giảng viên. Hồ sơ này cung
cấp evidence có thể chạy lại và nêu rõ những gì chưa được chứng minh.
