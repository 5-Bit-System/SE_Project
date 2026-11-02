# Rà soát môn tiên quyết — Vinh

Ngày kiểm tra: 20/10/2026.

**Trạng thái sau sửa:** 5 mã tham chiếu đã bổ sung, 20 ô tiên quyết đã chuẩn hóa,
69 quan hệ mới đã nạp. Còn MAT3423 `unknown` (MAT3402 chưa rõ) và MAT3325
`conflict` (giữ hai điều kiện theo nhóm nguồn). Toàn bộ suite đạt
**275 passed, 10 skipped**. Xem [kết quả và bằng chứng PDF](VINH_PDF_SOURCE_REVIEW.md).
Các con số 279 quan hệ / 21 trường hợp dưới đây là mốc trước khi sửa.

**Cập nhật sau khi nhận ZIP PDF:** đã đối chiếu trực tiếp các bảng tiên quyết.
Năm mã vắng có định nghĩa trong PDF Toán tài năng; MAT3402 chưa tìm được dòng định
nghĩa. Biểu thức MAT3359, hai điều kiện khác nhau của MAT3325 và hai lỗi locator
đã được xác nhận tại [báo cáo đối chiếu PDF](VINH_PDF_SOURCE_REVIEW.md).
Các phần dưới ghi kết quả kiểm tra nội bộ trước khi nhận PDF; các việc “cần đối
chiếu” phải được đọc cùng cập nhật này.

## Kết quả

- 279 quan hệ trong SQL nguồn, export và PostgreSQL khớp nhau; không phát hiện
  mất quan hệ khi import. Đây là đối chiếu nội bộ, chưa đối chiếu PDF chính thức.
- 173 dòng `normalized`: nhóm AND/OR khớp ô nguồn theo quy ước của bản SQL
  phiên âm: `/` là OR, xuống dòng tách nhóm AND, dòng xuống sau `/` được nối lại.
  Test xử lý cả mã có hậu tố như `MAT3552E`.
- 19 dòng `unlisted_prerequisite` có mã tiên quyết không tồn tại trong danh mục
  `courses`; các ô này chưa được chuẩn hóa đầy đủ.
- 2 dòng `complex_expression`: MAT3359 ở Toán học và Toán tin, cần đối chiếu
  cách hiểu biểu thức có dấu ngoặc.
- 21 môn tính theo từng ngành ở trạng thái `unknown`; đã kiểm tra chúng vẫn bị
  chặn ngay cả khi mọi môn còn lại trong ngành được đánh dấu đã đạt.
- Sáu mã vắng trong danh mục: `MAT2313`, `MAT2320`, `MAT2321`, `MAT2322`,
  `MAT3340`, `MAT3402`.

## Danh sách cần Trung/lead xác minh

Trang và dòng lấy từ bản phiên âm hiện có. Tên PDF và nguyên văn ô tiên quyết
được giữ trong `database/data/hus_source.json`, bảng `official_curriculum_entries`.
Danh sách dưới đây chưa khẳng định mã nào bị nhập sai hoặc phải bổ sung.

| Ngành | Môn bị ảnh hưởng | Mã chưa có / vấn đề | Trang / dòng |
| --- | --- | --- | --- |
| Toán học | MAT2308 | MAT2320 | 10 / 26 |
| Toán học | MAT2310 | MAT2321 | 10 / 28 |
| Toán học | MAT2314 | MAT2321 | 9 / 23 |
| Toán học | MAT2407 | MAT2321 | 10 / 27 |
| Toán học | MAT3300 | MAT2321 | 10 / 35 |
| Toán học | MAT3306 | MAT2320 | 11 / 41 |
| Toán học | MAT3307 | MAT2322 | 11 / 42 |
| Toán học | MAT3313 | MAT2321, MAT2322 | 11 / 48 |
| Toán học | MAT3317 | MAT3340 | 11 / 49 |
| Toán học | MAT3325 | MAT2322; khác điều kiện giữa các lần xuất hiện | 13 / 72 |
| Toán học | MAT3327 | MAT2313 | 12 / 58 |
| Toán học | MAT3339 | MAT2321 | 11 / 45 |
| Toán học | MAT3344 | MAT2321, MAT2322 | 11 / 38 |
| Toán học | MAT3359 | Biểu thức phức tạp | 11 / 44 |
| Toán học | MAT3423 | MAT3402 | 13 / 76 |
| Toán tin | MAT2314 | MAT2321 | 9 / 23 |
| Toán tin | MAT2407 | MAT2321 | 10 / 28 |
| Toán tin | MAT3327 | MAT2313 | 12 / 51 |
| Toán tin | MAT3359 | Biểu thức phức tạp | 10 / 39 |
| Khoa học máy tính và thông tin | MAT2407 | MAT2321 | 10 / 24 |
| Khoa học dữ liệu | MAT2407 | MAT2321 | 10 / 24 |

## Việc cần chốt trước khi báo đủ dữ liệu tiên quyết

1. Đối chiếu sáu mã vắng với PDF gốc: xác nhận môn ngoài chương trình, mã tương
   đương, khác phiên bản hay lỗi phiên âm. Chỉ bổ sung/thay mã khi có bằng chứng.
2. Xác nhận dấu ngoặc của MAT3359 và điều kiện khác nhau giữa các lần xuất hiện
   của MAT3325 trong Toán học. MAT3325 có một dòng đã chuẩn hóa và một dòng chứa
   MAT2322 chưa có trong danh mục; không chọn tùy ý một dòng làm quy tắc đầy đủ.
3. Rà soát 103 dòng `none` với PDF gốc để phát hiện điều kiện có thể đã bị bỏ
   ngay từ khâu nhập nguồn. Hiện chỉ xác nhận hệ thống bảo toàn bản nguồn đã nhập.
4. Sau khi Trung sửa nguồn, chạy lại test rồi publish catalog qua công cụ chuẩn.
   Chưa sửa dữ liệu nguồn hoặc tự thêm quan hệ tiên quyết trong lần rà soát này.

## Kiểm thử

- Thêm 12 ca ở `tests/database/source/test_prerequisite_coverage.py`: đối chiếu
  AND/OR với ô nguồn, bảo toàn điều kiện chưa rõ và chặn mở khóa sai theo 4 ngành.
- Thêm 2 ca ở `tests/database/test_hus_postgres.py`: đối chiếu đủ 279 quan hệ và
  297 ô nguồn/trạng thái trên PostgreSQL với export, dùng mã ngành thay vì ID cố định.
- Chạy toàn bộ suite với cả `HUS_TEST_DATABASE_URL` và `TEST_DATABASE_URL`:
  **238 passed, 10 skipped**, 38,79 giây. 10 ca bỏ qua cần nguồn đã rà soát riêng.
- Ruff: đạt. Có một cảnh báo deprecation FastAPI/Starlette về httpx.

SQL và export cùng nguồn nên cùng khớp không chứng minh dữ liệu học thuật đầy đủ.
Xem lịch sử Git để biết commit bàn giao phần kiểm thử và sửa tiên quyết.
