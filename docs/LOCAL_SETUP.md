# Cài đặt và chạy local

Cập nhật 28/10/2026. Chạy các lệnh từ thư mục gốc chứa `app/`, `database/`
và `requirements.txt`. Hướng dẫn dành cho local; không phải quy trình triển khai
production. Dùng PostgreSQL HUS database `ai07`, qua Neon hoặc Docker.
Nếu chưa có mã nguồn, clone rồi chuyển vào thư mục dự án:

```bash
git clone https://github.com/5-Bit-System/SE_Project.git
cd SE_Project
```

Nếu đã có checkout, dùng checkout hiện tại; không clone đè hoặc xóa cấu hình.

## 1. Môi trường Python

Dùng Python 3.11 để khớp CI. Máy đã có Conda `SE_Project` chỉ cần kích hoạt,
không tạo lại hoặc xóa môi trường đang dùng:

```bash
conda activate SE_Project
python --version
```

Nếu chưa có môi trường:

```bash
conda create -n SE_Project python=3.11
conda activate SE_Project
```

Cài dependency ứng dụng, test và connector trong cùng môi trường:

```bash
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
python -m pip install -r requirements-portal.txt -c requirements-lock.txt
```

Không dùng Conda thì tạo `.venv` bằng `python -m venv .venv`; kích hoạt bằng
`source .venv/bin/activate` trên Linux/macOS hoặc `.venv\Scripts\Activate.ps1`
trên PowerShell. Các lệnh `python -m ...` bên dưới giữ nguyên.
`.venv` là thư mục môi trường; `.env` là file cấu hình, không thay thế nhau.

## 2. Trình duyệt cho kết nối VNU

Worker của web dùng Google Chrome đã cài trên máy:
`playwright.chromium.launch(channel="chrome", headless=True)`.
Máy cần chạy được Chrome headless và kết nối HTTPS tới cổng VNU. Nếu chưa cài
Chrome, có thể cài từ nhà cung cấp hoặc dùng Playwright:

```bash
python -m playwright install chrome
```

Lệnh cài có thể cần quyền quản trị tùy hệ điều hành. Đừng chỉ cài Chromium rồi
cho rằng worker đã có Chrome: `channel="chrome"` yêu cầu đúng Google Chrome.
CLI chẩn đoán `tools.try_daotao` dùng Chromium riêng; chỉ khi dùng CLI này mới cần:

```bash
python -m playwright install chromium
```

## 3. File cấu hình

Không ghi đè `.env`, `.env.auth` hoặc `database/.env.docker` đã có. Không đưa
mật khẩu, token hay cookie thật vào Git, ảnh chụp hoặc đầu ra dùng chung.

### Tạo file còn thiếu

Đoạn Python sau chỉ tạo file chưa tồn tại; ví dụ lệnh dùng Bash.
Khóa auth được sinh trong bộ nhớ và ghi trực tiếp vào file, không in ra terminal:

```bash
python - <<'PY'
from pathlib import Path
import os
import secrets

for target, template in [('.env', '.env.example'), ('.env.auth', '.env.auth.example')]:
    path = Path(target)
    if path.exists():
        print(f'Giữ nguyên {target}')
        continue
    content = Path(template).read_text(encoding='utf-8')
    if target == '.env.auth':
        content = content.replace('replace-with-a-generated-secret', secrets.token_urlsafe(48))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as output:
        output.write(content)
    print(f'Đã tạo {target}; hãy kiểm tra cấu hình')
PY
```

Khối `python - <<'PY'` trên là cú pháp Bash (Linux/macOS). Với PowerShell, lưu
phần Python giữa hai dòng `PY` vào một file tạm rồi chạy `python <file-tam.py>`.
Không đưa file cấu hình thật vào commit. Nếu `.env.auth` đã tồn tại nhưng còn
placeholder hoặc thiếu khóa: tạo khóa bằng `python -c "import secrets; print(secrets.token_urlsafe(48))"`
và đặt vào `AUTH_TOKEN_PEPPER` trên máy của bạn. Không đổi khóa đang dùng hợp lệ
chỉ vì cập nhật code: đổi khóa làm token/phiên hiện có mất hiệu lực.

### `.env`: database và ứng dụng

```dotenv
STORAGE_BACKEND=postgres
DATABASE_MODEL=hus
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/ai07?sslmode=require
HUS_DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/ai07?sslmode=require
RECOMMENDATION_LLM_ENABLED=false
```

Các URL trên là mẫu, phải thay bằng thông tin database được cấp. Hai biến phải
trỏ cùng database/host/port; không chỉ giống tên `ai07`. Nếu mật khẩu có ký tự
đặc biệt, dùng URL đã được provider mã hóa hoặc mã hóa phần mật khẩu đúng chuẩn.
Tắt LLM không tắt kết nối PostgreSQL hoặc VNU, chỉ tránh gọi mô hình khi xếp hạng.

| Thành phần | Cách nạp cấu hình |
|---|---|
| FastAPI | `DATABASE_URL` từ shell hoặc `.env` gốc |
| Migration CLI | Tự nạp `.env` gốc; đọc `HUS_DATABASE_URL` |
| Các công cụ DB khác | Đọc `HUS_DATABASE_URL` từ shell hoặc `database/.env.docker`; không tự nạp `.env` |
| Auth | `.env.auth` và biến môi trường của tiến trình |

Biến shell có ưu tiên cao hơn giá trị file. Migration dùng shell → `.env` gốc
→ `database/.env.docker`; không tự lấy `DATABASE_URL` thay `HUS_DATABASE_URL`.
Auth đọc riêng `.env.auth`; `.env` không được auth settings nạp trực tiếp.

### `.env.auth`: phiên đăng nhập

Giữ cấu hình trong mẫu, kiểm tra ít nhất:

```dotenv
APP_ENV=local
PUBLIC_BASE_URL=http://127.0.0.1:8000
AUTH_ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
AUTH_TOKEN_PEPPER=<khóa ngẫu nhiên đã sinh, ít nhất 32 ký tự>
```

Không dùng dòng placeholder này làm khóa thật. SMTP trong mẫu là cấu hình mail
local; đăng nhập sinh viên VNU hiện tại không yêu cầu đăng ký/xác thực email cá
nhân hoặc Mailpit. Giữ SMTP đã cấu hình nếu có; không đổi Gmail/SMTP hay seed lại
admin để giải quyết lỗi khởi động. Production có yêu cầu HTTPS/SMTP riêng.

## 4. Chọn database

### Database Neon đã có

Dùng chuỗi kết nối Neon trong cả hai biến URL của `.env`, giữ tham số TLS của
provider (`sslmode=require`, có thể kèm `channel_binding=require`).
Không cần khởi động Docker. Với database đã có catalog, không publish lại hoặc
seed tài khoản chỉ để chạy app.

### PostgreSQL Docker mới

Chỉ khi chọn Docker: tạo `database/.env.docker` từ `database/.env.example` nếu
chưa có; thay mật khẩu và kiểm tra URL của file đó khớp `.env` gốc. Mẫu Docker
mặc định dùng user `ai07`, host `127.0.0.1`, port `5433`, DB `ai07`,
`sslmode=disable` thay cho `require` vì PostgreSQL local không bật TLS.

```bash
docker compose --env-file database/.env.docker -f database/docker-compose.yml up -d --wait
```

Giữ nguyên volume đang dùng. Không chạy `docker compose down -v` để sửa lỗi app.

## 5. Migration và catalog

Trước khi upgrade database có dữ liệu, tạo backup và kiểm tra khả năng khôi phục
qua công cụ provider hoặc `pg_dump -Fc` theo quy trình vận hành của nhóm.

```bash
python -m database.tools.migrate upgrade
python -m database.tools.migrate current
```

Head hiện tại: `hus_20261028_08 (head)`; cách in thứ tự nhãn có thể
khác. Migration trước đó nối lịch sử cũ với auth; head hiện tại bổ sung kế hoạch học kỳ.
Không chạy root Alembic, sửa `hus_alembic_version` hoặc dùng `stamp` để vượt lỗi.

**Chỉ database mới/chưa có catalog:** sau migration, kiểm tra rồi publish nguồn
HUS. Publisher không tự nạp `.env` nên dùng wrapper nạp file trong cùng tiến trình:

```bash
python -m database.tools.publish_catalogs --dry-run
python -c "from dotenv import load_dotenv; load_dotenv('.env'); from database.tools.publish_catalogs import main; main()"
```

Dry-run không kết nối/ghi DB. Lệnh thứ hai ghi catalog và active revisions vào
DB được cấu hình. Dùng `database/data/hus_source.json`; không seed bốn catalog
bằng mẫu `data/curricula/` hoặc dữ liệu trong `tests/`. Catalog vẫn draft_unverified.

Sinh viên đăng nhập VNU để hệ thống tạo/liên kết danh tính, không chạy seed.
Nếu cần bootstrap admin trên **DB local mới**, đọc
[hướng dẫn tài khoản](HUONG_DAN_TAI_KHOAN_HE_THONG.md). Seed dev từ chối Neon;
không bỏ chặn đó hoặc reset mật khẩu admin đang có.

## 6. Khởi động và sử dụng

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở <http://127.0.0.1:8000/>. Giữ terminal chạy; `Ctrl+C` để dừng.
Dùng một worker vì job/cookie VNU hiện nằm trong RAM của tiến trình. Không thêm
`--workers` để triển khai nhiều tiến trình khi chưa có cơ chế chia sẻ trạng thái.
Restart hoặc auto-reload làm mất phiên VNU trong RAM và có thể cần xác thực lại.

| URL | Kết quả mong đợi |
|---|---|
| `/health` | HTTP 200, tiến trình hoạt động |
| `/ready` | HTTP 200, đúng schema và catalog |
| `/docs` | OpenAPI; không tự bỏ qua cookie/CSRF khi gọi API cá nhân |

Sinh viên chọn đăng nhập VNU; admin chọn tab quản trị và dùng tài khoản đã được
cấp. Thông tin ngành/khóa, completeness và policy cần đối chiếu trước khi dùng
kết quả học vụ. Hệ thống không xác nhận lịch mở lớp chính thức.

## 7. Những lần chạy sau

```bash
conda activate SE_Project
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Nếu dùng Docker và DB đang dừng, khởi động lại service DB trước. Sau pull code,
đọc thay đổi dependency, cài lại nếu cần và chạy migration nếu có revision mới;
không tạo lại cấu hình, sinh khóa mới hoặc publish/seed lại mỗi lần.

## 8. Lỗi thường gặp

| Lỗi | Cách kiểm tra |
|---|---|
| `No module named ...` | Đã activate đúng `SE_Project` và cài dependency của cả core/portal chưa? |
| `HUS_DATABASE_URL is not set` | Điền đúng tên biến trong `.env`, lưu file; shell rỗng cũng có thể ghi đè file. |
| `HUS database migrations are not current` | Kiểm tra hai URL cùng DB rồi chạy migration và `current`. |
| `Can't locate revision ...hus_20261023_04` | Cập nhật đủ code có migration khôi phục; xem [database README](../database/README.md). Không stamp/reset. |
| `Auth configuration requires a server secret` | `.env.auth` phải có `AUTH_TOKEN_PEPPER` ngẫu nhiên ≥32 ký tự; shell có thể ghi đè. |
| `Executable doesn't exist` / `browser_unavailable` | Worker cần Chrome; Chromium chỉ phục vụ CLI. |
| `origin_rejected` / `csrf_rejected` | Mở đúng URL/port cấu hình, đăng nhập lại từ UI; không tắt kiểm tra bảo vệ. |
| Cổng 8000 đã được dùng | Dừng server cũ trước; đổi port phải đổi cả base URL/origin auth. |
| DB mới báo thiếu catalog | Migration chỉ tạo schema; thực hiện bước publish cho DB mới. |

Nếu gặp lỗi khác, cung cấp traceback đã che thông tin riêng, không gửi `.env`.
Không reset seed, volume hoặc toàn database để sửa lỗi giao diện.

## 9. Kiểm tra dành cho lập trình viên

```bash
python -m ruff check .
python -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"
```

Các test mặc định dùng dữ liệu tổng hợp. PostgreSQL tests cần DB thử riêng theo
[tests/README.md](../tests/README.md); không đặt URL Neon thật vào biến test.
Các kiểm tra browser trong `tests/frontend/` dùng dữ liệu giả lập, có thể cần
Chrome và server fixture riêng theo từng script. Kiểm tra code pass không thay
cho nghiệm thu bằng tài khoản thật của chủ tài khoản.
