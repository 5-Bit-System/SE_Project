# Vận hành tài khoản Sổ học tập

**Cập nhật mới nhất 25/10/2026:** sinh viên đăng nhập trực tiếp bằng VNU, admin
giữ tài khoản/mật khẩu riêng. Luồng đăng ký/xác thực email sinh viên bên dưới là
lịch sử, API công khai tương ứng đã đóng. Xem [hướng dẫn hiện tại](VNU_SIGNIN_2026_10_25.md).
Gmail SMTP hiện có được giữ nguyên; không đổi cấu hình runtime về Mailpit.

Bản local triển khai ngày 25/10/2026. Tài khoản hệ thống dùng email/mật khẩu riêng.
Sau khi đăng nhập, sinh viên mới kết nối tài khoản VNU để lấy bảng điểm. VNU không
cấp phiên đăng nhập hệ thống. Chưa triển khai crawl tự động hằng tuần.

## Cấu hình và chạy local

Giữ cấu hình PostgreSQL HUS trong `.env`. Sao chép `.env.auth.example` thành
`.env.auth`, tạo `AUTH_TOKEN_PEPPER` ngẫu nhiên bằng lệnh được ghi trong mẫu.
File này được Git bỏ qua. Không ghi đè file đang dùng: đổi secret làm các phiên
và liên kết email hiện tại hết hiệu lực. Biến môi trường tiến trình có ưu tiên
cao hơn `.env.auth`; cấu hình auth không tự đọc các giá trị trong `.env`.

```powershell
docker compose -f database/docker-compose.mail.yml up -d
.venv/Scripts/python.exe -m database.tools.migrate upgrade
.venv/Scripts/python.exe -m database.tools.seed_system_accounts
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Trước migration trên database đã có dữ liệu, sao lưu bằng `pg_dump -Fc` và kiểm
tra bản sao. Bản local này đã có backup trong `backups/system_auth_20261025/`.
Migration bổ sung đi qua `hus_20261025_04` rồi `hus_20261025_05`; không publish
lại catalog, không tạo bản ghi sinh viên giả, không chuyển bảng điểm sang seed user.

Mở app tại <http://127.0.0.1:8000/>. Mailpit ở <http://127.0.0.1:8025/> là hộp
thư thử nhận email xác thực; SMTP chỉ mở loopback `1025`, không chuyển email ra
Gmail/Outlook. Đăng ký địa chỉ bất kỳ đúng cú pháp trong local, mở thư tương ứng,
bấm liên kết và xác nhận trên app. API không xác thực giả nếu SMTP lỗi.

## Hai tài khoản mẫu

CLI tạo `admin@sohoctap.test` (`admin`) và `student@sohoctap.test` (`student`),
đều được đánh dấu `seeded_for_dev`, active và bootstrap verified cho local.
Mật khẩu ngẫu nhiên được lưu riêng tại
`backups/system_auth_20261025/accounts.private.txt`, không đưa vào Git/log.
Phải đổi mật khẩu khi đăng nhập lần đầu, trước khi dùng các chức năng khác.

Database chỉ lưu Argon2id hash. Chạy lại seed không reset mật khẩu hoặc tạo
trùng; account trùng email nhưng không phải seed hoặc sai role sẽ làm lệnh dừng.
CLI chỉ cho phép local `ai07`, hoặc database dùng một lần với tên
`ai07_runtime_test_*` khi `APP_ENV=test`. Không tự seed khi khởi động app.
File bàn giao là mật khẩu **tạm**, không được cập nhật sau khi người dùng đổi mật khẩu.

## Luồng sử dụng

1. Đăng ký email, tên hiển thị và mật khẩu 6–128 ký tự. Tài khoản ở trạng thái
   pending cho đến khi xác thực; người dùng không tự chọn role/admin.
2. Liên kết email hết hạn sau 30 phút và chỉ dùng một lần; mở link không tự
   kích hoạt cho đến khi bấm xác nhận. Nếu mở trên thiết bị khác, app yêu cầu
   người sở hữu email đặt mật khẩu để tránh giữ mật khẩu do người khác đăng ký hộ.
   Gửi lại có giới hạn/cooldown, giữ các liên kết cũ còn hạn trong giới hạn cho phép.
3. Đăng nhập Sổ học tập, rồi vào Hồ sơ để kết nối VNU. Chỉ nhận bảng điểm cũ
   sau đăng nhập VNU mới thành công; không ghép theo tên/email và không tự chuyển
   danh tính VNU đã thuộc tài khoản hệ thống khác.
4. Cập nhật dùng cookie VNU trong RAM của phiên hiện tại. Hết phiên VNU hoặc
   restart server có thể yêu cầu xác thực VNU lại; vẫn xem được bảng điểm đã lưu
   khi phiên hệ thống còn hợp lệ. Giữ nhắc cập nhật sau 7 ngày và cổng completeness.
5. “Ngắt phiên VNU” hủy cookie VNU, giữ tài khoản và bảng điểm. “Xóa bảng điểm
   VNU” xóa dữ liệu/link nguồn và hủy các phiên VNU của owner, giữ tài khoản.
   “Đăng xuất” trên header hủy phiên hệ thống và cookie VNU của phiên đó.
6. Admin mở Quản trị để tìm/danh sách, đổi role hoặc khóa/mở tài khoản. Không
   tự khóa/hạ quyền chính mình hoặc xóa admin hoạt động cuối cùng. Thay đổi quyền
   thu hồi phiên của tài khoản bị sửa. Admin không mặc nhiên xem bảng điểm người khác.

Phiên hệ thống lưu DB dưới dạng digest token, cookie HttpOnly/SameSite=Lax;
idle 2 giờ, tối đa 12 giờ. Đổi mật khẩu thu hồi phiên cũ và cấp phiên mới.
Quan hệ family bảo đảm logout đồng thời vẫn hủy phiên vừa được xoay token.
Origin/CSRF được kiểm tra phía server; auth/personal/admin trả `no-store`.
Mật khẩu/cookie VNU không lưu DB, localStorage, log hoặc email.

## API và tương thích

`/auth/register`, `/auth/email/resend`, `/auth/email/verify`, `/auth/login`,
`/auth/logout`, `/auth/session`, `/auth/me`, `/me/password` phục vụ tài khoản hệ
thống. `/me/portal-connection` tạo/đọc/ngắt kết nối nguồn; các route sync/reauth
tiếp tục dưới `/me/` và tra owner từ link server.

`POST /me/portal-sync` trả 202 cùng job khi bắt đầu cập nhật. Khi cookie VNU
trong RAM đã hết hạn/chưa có, trả 200 với `{"state":"reauth_required"}` để UI
mở bước xác thực lại bình thường; chưa có job hoặc lần đồng bộ thành công mới.
Mất phiên hệ thống/quyền sở hữu và các lỗi kỹ thuật vẫn trả lỗi phù hợp.

`POST /auth/portal` cũ trả 410. Các `/profiles/...` chưa có mapping ownership
cũng trả 410; domain/fixture tính toán vẫn được giữ. GET catalog public; POST
tính toán legacy yêu cầu tài khoản verified và CSRF. UI hoạt động từ nguồn VNU,
không khôi phục nhập tay/CSV trong luồng người dùng.

## Kiểm tra

```powershell
.venv/Scripts/python.exe -m pytest -q tests -m "not postgres and not hus_postgres" --full-catalog-root docs/acceptance/hus_2022
.venv/Scripts/python.exe -m pytest -q tests -m hus_postgres
.venv/Scripts/python.exe -m tests.frontend.check_system_auth
.venv/Scripts/python.exe -m ruff check .
```

PostgreSQL tests cần `HUS_TEST_DATABASE_URL` trỏ đến đích local được bộ kiểm tra
cho phép. Test tự tạo/drop database riêng; không chạy destructive tests trên bảng
production. Browser/SMTP proof cần Chrome, Playwright và Mailpit; nó tạo DB dùng
một lần, chỉ dùng account/bảng điểm/email `.test` giả, không gọi VNU thật.

## Điều kiện trước khi triển khai công khai

Cần cấu hình SMTP thật, mail-from/domain được kiểm soát và kiểm thử gửi/nhận tại
địa chỉ được phép, HTTPS, origin/proxy chính xác, secret riêng và chính sách backup.
`APP_ENV=production` từ chối SMTP fake/không mã hóa, HTTP và seed còn active;
startup cùng `/ready` kiểm tra các điều kiện tương ứng. Rate limit đăng ký/login/
verify/resend dùng DB để chia sẻ giữa các worker. Cookie VNU hiện chỉ ở RAM một
process; triển khai nhiều process cần thiết kế kho phiên nguồn phù hợp trước.
Khôi phục mật khẩu qua email và tự động đồng bộ hằng tuần chưa thuộc bản này.
