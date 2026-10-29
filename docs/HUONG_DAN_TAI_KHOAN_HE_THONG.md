# Vận hành tài khoản Sổ học tập

Cập nhật 28/10/2026. Hướng dẫn cài mới và chạy dự án được duy trì tại
[LOCAL_SETUP.md](LOCAL_SETUP.md). Các lệnh bên dưới chạy từ thư mục gốc trong
môi trường Python đã kích hoạt.

## Luồng hiện tại

- Sinh viên chọn **Sinh viên VNU** và đăng nhập trực tiếp bằng tài khoản VNU.
  Backend xác thực nguồn, tạo/tìm danh tính ứng dụng và cấp session riêng.
- Admin chọn **Quản trị viên**, dùng username/email và mật khẩu local được cấp.
- Không có đăng ký/xác thực email cá nhân cho sinh viên trong luồng hiện tại.
  Các API register/resend/verify cũ trả 410; không cần Mailpit để đăng nhập VNU.
- Connector không phải OAuth/SSO chính thức. CAPTCHA/OTP hoặc nguồn không xác
  minh được có thể chặn kết nối; không tự nâng cờ dữ liệu để vượt kiểm tra.

Xem chi tiết [VNU_SIGNIN_2026_10_25.md](VNU_SIGNIN_2026_10_25.md).

## Cấu hình và khởi động

`.env` chứa database runtime và migration. `.env.auth` chứa `APP_ENV`,
`AUTH_TOKEN_PEPPER`, base URL, origin và SMTP. Cả hai đều ignored.
Auth settings đọc `.env.auth` và shell; shell có ưu tiên cao hơn file.
Khóa cần được sinh ngẫu nhiên, ít nhất 32 ký tự. Không đổi khóa hợp lệ hoặc ghi
đè SMTP đang dùng khi cập nhật code. Xem cách tạo file còn thiếu trong setup.

```bash
conda activate SE_Project
python -m database.tools.migrate upgrade
python -m database.tools.migrate current
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Sao lưu database trước upgrade; head hiện tại `hus_20261028_08`. Migration
không seed tài khoản và không publish catalog. Không chạy seed để sửa lỗi
mật khẩu, migration hoặc bảng điểm. Mailpit chỉ dành cho thử nghiệm email
local riêng; không thay SMTP đã cấu hình bằng Mailpit theo thói quen.

## Admin trên database mới

Sinh viên không cần seed; danh tính được tạo qua đăng nhập VNU đã xác thực.
Với **DB local mới** thật sự cần tài khoản thử, công cụ dev có sẵn:

```bash
python -m database.tools.seed_system_accounts
```

Chỉ chạy sau migration và cấu hình auth. CLI từ chối Neon/production, chỉ cho
local `ai07` hoặc DB test được phép. Nó tạo admin và một tài khoản student
local lịch sử; student seed không thay thế đăng nhập VNU. Không mở lại API
email cũ để dùng student seed. Mật khẩu tạm được ghi riêng trong
`backups/system_auth_20261025/accounts.private.txt`, không in ra console.
Đăng nhập admin bằng email được tạo, đổi mật khẩu khi được yêu cầu.

Seed không reset mật khẩu đã đổi, không phải công cụ khôi phục tài khoản và
không được dùng trên DB đang có chỉ vì quên thông tin đăng nhập. File bàn giao
là mật khẩu tạm, không phản ánh thay đổi mật khẩu về sau. Admin trên Neon cần
quy trình cấp tài khoản riêng được nhóm cho phép; không bỏ kiểm tra bảo vệ seed.

## Session và dữ liệu nguồn

- Cookie ứng dụng `study_app_session`: HttpOnly/SameSite=Lax, Secure khi chạy
  HTTPS. Database lưu digest token; idle 2 giờ, tối đa 12 giờ.
- Cookie VNU được giữ riêng trong RAM backend, không lưu DB/localStorage/log;
  có thể hết hạn sớm hoặc mất khi restart. Có cookie hợp lệ thì thử resume;
  hết hiệu lực thì yêu cầu xác thực VNU lại.
- Cập nhật và các thay đổi cá nhân yêu cầu session, origin và CSRF phù hợp.
  Đăng xuất thu hồi session ứng dụng và kết nối VNU tương ứng.
- Xóa/ngắt dữ liệu nguồn theo UI không biến tài khoản VNU khác thành cùng
  sinh viên; quyền sở hữu được kiểm tra ở server.
- Admin quản lý quyền/trạng thái tài khoản, không mặc định được xem bảng điểm
  người khác. Chỉnh quyền hoặc khóa tài khoản có thể thu hồi phiên của người đó.

## API chính

| API | Chức năng |
|---|---|
| `POST /auth/vnu` | Đăng nhập sinh viên VNU |
| `POST /auth/login` | Đăng nhập admin local |
| `GET /auth/session`, `GET /auth/me` | Đọc trạng thái phiên/tài khoản |
| `POST /auth/logout` | Đăng xuất |
| `POST /me/password` | Đổi mật khẩu khi loại tài khoản cho phép |
| Các `/me/portal-*`, `GET /me/profile` | Kết nối, cập nhật và xem nguồn VNU |
| `GET /admin/users`, `PATCH /admin/users/{account_id}` | Quản trị có phân quyền |

Dùng `/docs` để đối chiếu method/schema hiện tại. `/auth/portal` và `/profiles/...`
legacy đã đóng với 410. Chưa hỗ trợ triển khai nhiều worker chia sẻ cookie VNU.
Production cần HTTPS, cấu hình origin/SMTP phù hợp và không có seed dev đang
active; không coi hướng dẫn local là nghiệm thu production.
