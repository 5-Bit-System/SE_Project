# Kiểm tra giao diện bằng Chrome

Các lệnh dưới đây dùng Google Chrome đã cài và Playwright trong
`requirements-portal.txt`. Chạy từ thư mục gốc repository. Các fixture chặn
request và cung cấp tài khoản, bảng điểm, API và tài nguyên tĩnh ngay trong test;
không cần khởi động app hoặc đăng nhập VNU.

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
python -m tests.frontend.check_analytics_drilldown
python -m tests.frontend.check_charts
python -m tests.frontend.check_workspace
python -m tests.frontend.check_course_status
python -m tests.frontend.check_program_binding
python -m tests.frontend.check_semester_plans
python -m tests.frontend.check_session_restore
python -m tests.frontend.check_portal_session
python -m tests.frontend.check_presentation
python -m tests.frontend.check_study_desk
python -m tests.frontend.check_motion
node tests/frontend/check_analytics.mjs
```

`check_analytics_drilldown` kiểm tra bảng chi tiết hệ 10/4, lọc điểm chữ/năm học,
bàn phím, VI/EN, mobile và việc xóa các hàng điểm khỏi DOM khi mất nguồn.
`check_charts` còn kiểm tra điểm 0, dấu phẩy thập phân, học lại, khoảng trống
điểm, trung bình gia quyền, khôi phục focus và xóa dữ liệu sau logout.

`check_workspace` và `check_program_binding` cung cấp response riêng cho kế
hoạch học kỳ và bảng điều kiện học. Kiểm tra hai người dùng sử dụng account và
session ID khác nhau; nguồn tổng hợp không được coi là dữ liệu học vụ thật.

Các kiểm tra chuyển động cần khoảng một phút để quan sát đủ chu kỳ animation.
Ảnh và log sinh ra trong `backups/` là dữ liệu kiểm thử, được Git bỏ qua.
Các lệnh này bổ sung cho pytest và các test PostgreSQL; chúng không xác nhận
đăng nhập VNU thật, độ đầy đủ bảng điểm hoặc tính áp dụng của catalog.
