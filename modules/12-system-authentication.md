# Module 12 — Tài khoản hệ thống, xác thực email và phân quyền

**Cập nhật mới nhất:** sinh viên dùng VNU để cấp phiên app, admin dùng tài khoản
local riêng. Đã đóng đăng ký/xác thực email công khai. `vnu_subject` giữ danh tính
khi xóa bảng điểm; `auth_method` kiểm tra phương thức đăng nhập theo role.
Xem [luồng và migration hiện tại](../docs/VNU_SIGNIN_2026_10_25.md).
Các đoạn mô tả email/student bên dưới là lịch sử, không còn là luồng hoạt động.

Cập nhật 25/10/2026. **Đã triển khai và kiểm tra local**. Người dùng yêu cầu tài khoản
riêng của Sổ học tập; đăng nhập VNU chỉ phục vụ kết nối/lấy bảng điểm.

[Kế hoạch chi tiết](../docs/KE_HOACH_TAI_KHOAN_HE_THONG_2026_10_25.md) là nguồn
chính cho schema, API, luồng email, hai account mẫu và tiêu chí nghiệm thu.

## Phạm vi

Đăng ký bằng email/password, xác thực email, login/logout hệ thống, role admin
và student, phiên DB và kiểm tra quyền tại backend. Mở rộng bảng accounts hiện
có; không ép người đăng ký phải có MSSV/CTĐT hoặc tạo students giả.

Đã tạo hai account local bằng CLI có chủ đích: một admin, một
student. Hash mật khẩu, bootstrap verified có ghi nhận, phải đổi mật khẩu tạm;
không hardcode credentials hoặc tự seed production. Đăng ký gửi thư qua SMTP
Mailpit loopback; chưa xác nhận gửi tới hộp thư production ngoài hệ thống.

## Ranh giới với VNU

Account hệ thống sở hữu liên kết tới portal owner đã xác minh. Một account và
một danh tính VNU tối đa một liên kết ở bản đầu. Dữ liệu cũ chỉ claim sau login
VNU thành công, không tự ghép theo email/tên. Cookie VNU RAM vẫn theo từng app
session; VNU hết phiên không làm mất quyền xem snapshot của account còn hợp lệ.

Xóa bảng điểm khác với xóa/đăng xuất account hệ thống. Admin quản lý tài khoản,
không mặc định đọc bảng điểm hoặc credentials người khác. Giữ cổng completeness,
nhắc 7 ngày và việc hoãn tự động crawl hằng tuần.

## Bàn giao

Schema/head compatibility, auth/email service, dependencies quyền/ownership,
API/UI auth/admin, cutover VNU resolver và lệnh seed. Test offline/DB/Chrome/email
local trước, email thật và public deployment có điều kiện nghiệm thu riêng.

Liên quan: [07 API](07-recommendation-api.md), [08 UI](08-web-ui.md),
[09 Portal](09-portal-transcript-import.md).

[Hướng dẫn vận hành bản local](../docs/HUONG_DAN_TAI_KHOAN_HE_THONG.md): cấu hình,
seed/idempotency, API cutover, quyền sở hữu VNU và các gate production.

Đã kiểm tra 434 offline, 44 PostgreSQL HUS và Chrome/SMTP Mailpit với dữ liệu giả;
backup restore/checksum xác nhận 17 bảng cũ được giữ nguyên. Chưa nghiệm thu
SMTP bên ngoài hoặc đăng nhập VNU thật qua liên kết tài khoản hệ thống mới.
