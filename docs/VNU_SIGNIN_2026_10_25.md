# Đăng nhập VNU cho sinh viên và tài khoản riêng cho admin

Ngày 25/10/2026. Thực hiện theo yêu cầu thay thế luồng sinh viên đăng nhập email
rồi kết nối VNU. Đây là đăng nhập qua connector cổng đào tạo hiện có, chưa phải
OAuth/SSO chính thức của VNU.

## Hành vi

- Trang đăng nhập mặc định chọn **Sinh viên VNU**. Nhập tài khoản/mật khẩu cổng
  đào tạo một lần, xác thực thành công rồi vào workspace; tài khoản nội bộ được
  tự tạo hoặc tìm lại theo danh tính VNU đã xác minh. Không cần email cá nhân.
- Tab **Quản trị viên** dùng tài khoản hoặc email và mật khẩu quản trị đã cấp.
  Giữ mật khẩu/role/đổi mật khẩu ban đầu; không mở đăng ký admin công khai.
- Backend chỉ cấp phiên student từ xác thực VNU và phiên admin từ mật khẩu
  local. Sinh viên không thể dùng mật khẩu email cũ để đi vòng qua VNU.
- Xác thực phải có fresh form POST được cổng đào tạo chấp nhận và menu sinh viên
  đã được connector kiểm tra. Chỉ có username, bảng điểm hoặc cookie client gửi
  lên không đủ để cấp danh tính. Nhãn MSSV mâu thuẫn vẫn bị từ chối.
- Sau khi xác thực thành công, lỗi kỹ thuật tải hồ sơ/bảng điểm hoặc bố cục bảng
  điểm chưa nhận diện không làm mất quyền vào ứng dụng. Hiện cảnh báo, giữ nguyên
  dữ liệu cũ, không tạo snapshot giả hoặc cập nhật mốc đồng bộ thành công.
  Sai danh tính, CAPTCHA/OTP và lỗi trước xác thực vẫn chặn đăng nhập.
- Phiên app vẫn dùng DB, idle 2 giờ/tối đa 12 giờ. Phiên VNU chỉ ở RAM theo từng
  phiên app; logout/khóa tài khoản/đổi quyền thu hồi theo cơ chế hiện có. VNU hết
  phiên chỉ yêu cầu xác thực lại khi cần cập nhật bảng điểm.
- Giữ nhắc cập nhật 7 ngày, completeness/binding/policy và các cổng học vụ.

## Dữ liệu và migration

Migration mới `hus_20261025_06` bổ sung:

- `accounts.vnu_subject`: danh tính đăng nhập duy nhất, độc lập với bảng điểm có
  thể xóa. Tài khoản VNU mới không có email hay mật khẩu app; cột hash bắt buộc
  chứa dấu hiệu không thể dùng để đăng nhập, không chứa mật khẩu VNU.
- `auth_sessions.auth_method`: phân biệt `local` và `vnu` để backend thực thi
  đúng phương thức theo role; không dùng cờ email_verified để giả xác thực VNU.
- Backfill chính xác các liên kết student/VNU đã có, giữ nguyên account ID,
  email, hash mật khẩu, role và snapshot. Không ghép theo tên/email, không tạo
  liên kết cho tài khoản chưa có bằng chứng nguồn, không chuyển nguồn của admin.
- Thu hồi phiên student cũ để lần tiếp theo đi qua đăng nhập VNU. Không reset
  mật khẩu hay role của tài khoản đã tồn tại.

Xóa bảng điểm xóa nguồn/link như trước nhưng giữ `vnu_subject`; lần đăng nhập sau
vẫn nhận đúng account ID. Account khác không được chiếm lại danh tính đã giữ.
Đăng nhập đồng thời cùng danh tính dùng transaction/khóa và ràng buộc duy nhất.

Admin tìm sinh viên bằng tài khoản VNU, email hoặc tên; không mặc định xem điểm
người khác. Nâng quyền một tài khoản chỉ có VNU bị chặn nếu chưa có thông tin
đăng nhập quản trị riêng. Tài khoản student email cũ chưa liên kết vẫn được giữ
trong DB, không tự gán cho sinh viên hay cấp quyền từ email đó.

## API

| API | Hành vi |
| --- | --- |
| `POST /auth/vnu` | `{username,password}`, xác thực VNU và cấp cookie app; có thể kèm cảnh báo nguồn |
| `POST /auth/login` | Admin local; nhận `username` hoặc `email` cùng `password` |
| `POST /auth/register`, `/auth/email/resend`, `/auth/email/verify` | 410 `use_vnu_login`, không gửi thư hoặc thay đổi account |
| `/auth/session`, `/auth/me`, `/auth/logout` | Vòng đời phiên app dùng chung |
| `POST /me/password` | Chỉ đổi mật khẩu quản trị local; mật khẩu VNU quản lý tại VNU |
| `/me/portal-*`, `/me/profile` | Giữ phiên nguồn, ownership, cập nhật/xóa và dữ liệu nguồn hiện có |

Origin/CSRF, cookie HttpOnly, no-store, rate limit trong DB và audit an toàn
được giữ. Không lưu mật khẩu/cookie VNU vào DB, localStorage hoặc log.

## Vận hành và kiểm tra

Giữ `.env`, `.env.auth` và cấu hình Gmail SMTP hiện có. Luồng đăng nhập mới không
cần gửi email; Mailpit/fake chỉ dùng trong môi trường kiểm thử riêng. Không chạy
lại seed để thay mật khẩu admin. Backup trước migration; không publish catalog,
reset Docker volume hoặc sửa migration cũ.

```powershell
.venv/Scripts/python.exe -m pytest tests -q -m "not postgres and not hus_postgres" --full-catalog-root docs/acceptance/hus_2022
.venv/Scripts/python.exe -m pytest tests -q -m hus_postgres
.venv/Scripts/python.exe -m tests.frontend.check_system_auth
.venv/Scripts/python.exe -m ruff check .
```

HUS tests cần `HUS_TEST_DATABASE_URL` được kiểm tra đích local; tự tạo/drop DB
dùng một lần. Browser proof dùng VNU giả lập và database riêng, không gửi email
hoặc đăng nhập VNU thật. Nghiệm thu tài khoản VNU thật do người dùng nhập trực
tiếp trên giao diện local, không cung cấp mật khẩu trong chat.

SSO chính thức, API bảng điểm được VNU cấp quyền, đa process cho kho cookie RAM
và triển khai public vẫn cần thiết kế/nghiệm thu riêng. Không tự thêm đồng bộ
hằng tuần hoặc mở khóa tính toán học vụ trong thay đổi đăng nhập này.

## Kết quả local

- 440 kiểm tra offline đạt, gồm nguồn PDF HUS; Ruff toàn repo, cú pháp JS và
  `git diff --check` đạt. Còn cảnh báo Starlette/httpx đã có từ trước.
- Bộ HUS PostgreSQL: 54 đạt; sau gia cố chống chiếm danh tính đã xóa nguồn,
  chạy lại nhóm auth/VNU: 31 đạt. Tất cả dùng DB tự tạo/drop riêng.
- Chrome dùng server/database riêng xác nhận một lần đăng nhập VNU, không gửi
  đăng ký email hay kết nối VNU lần hai, reload phiên, phân quyền, đổi mật khẩu
  admin, khóa sinh viên, cập nhật và xóa dữ liệu hiển thị khi logout.
- Các hồi quy profile/workspace/charts/loading/reminder/reauth/resume, nguồn
  profile, hết phiên và phản hồi muộn sau logout đạt; VI/EN/themes/mobile đạt.
  Hai assertion cũ chờ form admin sau hết phiên đã được đổi sang form sinh viên
  và chạy lại thành công. Screenshot kiểm thử dùng dữ liệu giả, đã xem bản mobile.
- Local `ai07` đã backup/check archive và áp dụng head 06. So sánh checksum trong
  transaction giữ nguyên dữ liệu mọi bảng ngoài các trường phiên được phép đổi
  và cột danh tính mới. Account ID, hash cũ, liên kết, snapshot và catalog giữ nguyên.
- App chạy ở `http://127.0.0.1:8000/`; `/health`, `/ready` OK, `/auth/session`
  không cookie trả `authenticated:false`. Log/backup/evidence nằm dưới ignored
  `backups/vnu_signin_20261025/` và `backups/system_auth_20261025/`.

Chưa có kiểm thử đăng nhập VNU thật bởi agent; cần người dùng tự nghiệm thu tài
khoản trên giao diện. Không đổi `.env.auth`/SMTP, không gửi mail, không reset seed,
không commit/push/PR hoặc thay dữ liệu học vụ nguồn.
