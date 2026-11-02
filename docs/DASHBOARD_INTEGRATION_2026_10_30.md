# Tích hợp Dashboard mới — 30/10/2026

## Kết quả rà soát

Nhánh nguồn `feat/dashboard-semester-drilldown-20261028` được lấy từ GitHub tại
`81610619d2b4b391d587b27de80b40f49dac0cc6`. Bản local và `origin/main` ở
`1fb3a175df6f54ae5c4ba894f89e39181c097e97` khi bắt đầu. Local là tổ tiên trực
tiếp của nguồn, còn thiếu 27 commit; merge thử không có xung đột.

Nhánh tích hợp là `integration/dashboard-latest-20261030`. Merge commit
`7c2fe11` giữ cả lịch sử local và 27 commit gốc của Thang. Các sửa lỗi, test và
tài liệu tích hợp được chia thành commit theo công việc thực tế, giữ nguyên
author/hash của đồng đội. Publication của nhánh tích hợp không tự cập nhật
GitHub `main`; cập nhật `main` vẫn phải qua PR và Create a merge commit.

## Hành vi sau tích hợp

- Chọn điểm trên biểu đồ hệ 10/4 để xem bảng điểm học kỳ ngay trong Dashboard.
- Chọn điểm chữ trên biểu đồ hoặc chú giải để xem các lượt học tương ứng;
  bộ lọc năm học vẫn có hiệu lực. Học lại và lượt chưa có điểm được giữ riêng.
- Bảng giữ mã/tên/tín chỉ và các cột điểm nguồn, hỗ trợ bàn phím, VI/EN,
  sáng/tối và cuộn ngang trên mobile.
- Điều kiện học hiển thị tiến độ theo khối/nhóm; tìm kiếm có thông báo kết quả
  và các lựa chọn kế hoạch có tên truy cập rõ ràng.
- Catalog, thông tin cơ bản hoặc tiên quyết chưa xác minh chặn các kết quả
  học vụ tương ứng. Catalog runtime vẫn là `draft_unverified`; Dashboard mô tả
  bảng điểm vẫn hoạt động, việc merge không biến catalog thành đã duyệt.

Review phát hiện bảng chi tiết chỉ bị ẩn khi xóa nguồn, để lại các hàng điểm
trong DOM. Commit `b21c13b` xóa bảng, tiêu đề và metadata khi đóng/mất nguồn.
Regression đã thất bại trước sửa và qua sau sửa; kiểm tra biểu đồ cũng xác nhận
DOM sạch sau logout. Các fixture cũ về điều hướng, account/session, kế hoạch
và reauth được cập nhật cho hợp đồng hiện tại; test phục vụ asset ngay từ disk.

## Kiểm chứng

Kiểm tra trên bản tích hợp riêng với toàn bộ 18 file thay đổi local có sẵn
được sao lưu và chép sang để kiểm tra tương thích:

| Nhóm | Kết quả |
|---|---|
| Offline, gồm acceptance PDF với đường dẫn chỉ định | 587 passed, 80 deselected |
| PostgreSQL legacy/HUS trên container riêng | 80 passed, 587 deselected |
| Chrome tổng hợp | 11 script passed |
| Ruff | Passed |
| JavaScript syntax | 12 file passed |
| Analytics Node | Passed |
| Catalog builders | 4 fixture và mẫu 65 môn passed |

Các script Chrome và cách chạy nằm trong
[`tests/frontend/README.md`](../tests/frontend/README.md).
Ảnh desktop/mobile của Dashboard đã được xem trực tiếp. Các ca này kiểm tra
nguồn tổng hợp, không đăng nhập tài khoản VNU thật hoặc đọc điểm cá nhân.

Lần offline đầu có cảnh báo Starlette/httpx và hai cảnh báo giải mã stdout
Windows từ subprocess của test metadata builder. Chạy lại cả 8 test builder
với `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8` và coi cảnh báo thread là lỗi:
8 passed, không cảnh báo. Test PostgreSQL chỉ còn cảnh báo Starlette/httpx.

Database kiểm thử dùng container `se_dashboard_test_20261030`, cổng loopback
55440. Migration và catalog publication phục vụ test chỉ chạy ở đó. Task
không yêu cầu migration hay publication lại catalog runtime.

## Bảo toàn và bằng chứng local

Baseline ghi hash 493 file và sao lưu 18 file local chưa commit. Không đưa
các thay đổi cũ đó vào commit tích hợp. Cấu hình, source/PDF, tài khoản và dữ
liệu runtime được giữ theo phạm vi hiện có.

Artifact được Git bỏ qua tại `backups/dashboard_merge_20261030/`: baseline,
originals, offline.xml, postgres.xml, log trình duyệt, bản thử và ảnh tổng hợp.
Đây là bằng chứng local; một fresh clone không có các artifact này.
