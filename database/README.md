# Module database HUS / PostgreSQL (AI-07)

## Current HUS runtime - 2026-10-17

This database now supplies application catalogs. Follow [HUS_RUNTIME.md](HUS_RUNTIME.md) for setup, migrations, publication and rollback. Compose starts PostgreSQL without legacy SQL initialization; SQL10 is historical, never a runtime updater. app/db retains legacy schema. SQL/Neon instructions below are historical and do not apply to the migrated runtime.


Thư mục này là **module cơ sở dữ liệu thứ hai** của dự án: bản mô phỏng cổng đào tạo HUS
dùng để phát triển và demo AI-07, chạy trên **PostgreSQL 16 trong Docker** hoặc Neon
(database `ai07`, schema `public`).

> **Tách biệt với `app/db/`:**
> `app/db/` mô tả schema runtime của ứng dụng (`program_revisions`, `courses`, …).
> Thư mục `database/` này mô tả **thiết kế dữ liệu HUS** (`faculties`, `majors`,
> `curricula`, `students`, `course_attempts`, …). Hai thiết kế nói về hai thứ khác nhau,
> **không trộn** vào nhau.

## Chạy trên Docker local (PowerShell)

Database hiện tại được dựng ở container `se_hus_db`, volume `se_hus_pgdata`, cổng
`127.0.0.1:5433`. Container/volume này độc lập với `se_recommender_db` của ứng dụng.
Mật khẩu được tạo ngẫu nhiên và nằm trong `database/.env.docker` (Git bỏ qua).

Chạy từ thư mục gốc repository, với Docker Desktop đang hoạt động:

```powershell
docker compose --env-file database/.env.docker -f database/docker-compose.yml up -d --wait
.venv\Scripts\python.exe -m database.tools.verify_data
.venv\Scripts\python.exe -m database.tools.inspect_schema
```

Trên máy mới, trước tiên copy `database/.env.example` thành `database/.env.docker` và
thay hai chỗ mật khẩu bằng cùng một mật khẩu ngẫu nhiên. Không ghi đè file cấu hình
của volume đã có dữ liệu. CLI tự đọc file local này; biến `HUS_DATABASE_URL` trong
process được ưu tiên nếu đã đặt. Docker dùng `sslmode=disable` trên loopback; Neon
vẫn dùng TLS (`sslmode=require`).

Hai SQL trong `sql/` được Docker tự nạp theo thứ tự `00`, `10` khi khởi tạo volume
trống. Khởi động lại container giữ nguyên dữ liệu và không tự chạy lại SQL.
Sau khi chỉnh SQL, cần xem xét thay đổi và chạy `apply_sql` rõ ràng; script `10`
có xóa dữ liệu demo theo điều kiện đã mô tả bên dưới.

Tạm dừng mà vẫn giữ dữ liệu:

```powershell
docker compose --env-file database/.env.docker -f database/docker-compose.yml stop
```

Thông tin kết nối trong công cụ SQL: host `127.0.0.1`, port `5433`, database `ai07`,
user `ai07`; mật khẩu xem tại file local `database/.env.docker`.

Kết quả kiểm thử local và giới hạn: [DOCKER_VERIFICATION.md](DOCKER_VERIFICATION.md).
Ảnh chụp schema local: [DOCKER_SCHEMA.md](DOCKER_SCHEMA.md).

Các bảng sinh viên/điểm hiện vẫn trống. Dựng database này chưa tích hợp schema HUS
vào FastAPI và chưa tạo luồng lấy bảng điểm từ cổng đào tạo.

## Nội dung thư mục

| Đường dẫn | Vai trò |
|---|---|
| `DESIGN.md` | Tài liệu thiết kế CSDL AI-07 (15 mục + checklist kiểm thử) |
| `SCHEMA.md` | Ảnh chụp schema thật từ Neon (sinh tự động, đừng sửa tay) |
| `sql/00_ai07_schema.sql` | DDL 11 bảng nền + 2 view |
| `sql/10_official_curricula_2023.sql` | Nạp 4 CTĐT chính thức 2023 (tạo thêm 2 bảng `official_*`) |
| `hus_db/` | Thư viện Python: cấu hình, kết nối, introspection, kiểm chứng |
| `tools/` | CLI: xem schema, kiểm chứng dữ liệu, chạy file SQL |

## Bảo mật: chuỗi kết nối là bí mật

Chuỗi kết nối Neon chứa mật khẩu. **Không bao giờ** commit nó vào Git. Thay vào đó, đặt
biến môi trường `HUS_DATABASE_URL`:

```bash
export HUS_DATABASE_URL="postgresql://<user>:<password>@<host>/ai07?sslmode=require"
```

`SCHEMA.md` và mọi công cụ ở đây chỉ **đọc**; chỉ `apply_sql` mới ghi, và nó **từ chối**
các file chứa `DROP DATABASE` / `DROP SCHEMA` / `ALTER DATABASE` trừ khi bạn truyền
`--allow-dangerous`. Dự án không xoá database dùng chung.

## Thứ tự dựng database trên Neon (tùy chọn)

Chạy trên database `ai07` trống (đã `CREATE DATABASE ai07`):

```bash
export HUS_DATABASE_URL="postgresql://<user>:<password>@<host>/ai07?sslmode=require"

python -m database.tools.apply_sql database/sql/00_ai07_schema.sql --dry-run
python -m database.tools.apply_sql database/sql/00_ai07_schema.sql
python -m database.tools.apply_sql database/sql/10_official_curricula_2023.sql

python -m database.tools.verify_data          # kỳ vọng: 26/26 checks passed
python -m database.tools.inspect_schema       # xem nhanh schema + số dòng
```

`01_ai07_tables_and_data_fixed.sql` gốc không nằm trong repo; `00_ai07_schema.sql` đã
được dựng lại từ schema thật trên Neon (xem DESIGN.md mục 13).

## Trạng thái dữ liệu đã xác minh (`ai07`, bao gồm Docker local)

Sau khi chạy `00` rồi `10`, số dòng thực tế:

| Bảng | Số dòng |
|---|---|
| `faculties` | 1 |
| `majors` | 4 |
| `curricula` | 4 (bốn CTĐT chính thức 2023) |
| `courses` | 174 |
| `curriculum_courses` | 290 |
| `course_prerequisites` | 279 |
| `official_curriculum_groups` | 41 |
| `official_curriculum_entries` | 297 |
| `accounts`, `students`, `course_attempts`, `student_preferences` | 0 |

> **Lưu ý:** script `10` **xoá** sinh viên demo `99000001`–`99000008` và các CTĐT
> `DEMO-2023`. Vì vậy các mục checklist trong DESIGN.md nhắc tới `99000005` / `99000006`
> chỉ đúng với dữ liệu demo ban đầu, không còn đúng sau khi nạp CTĐT chính thức.
> Đây là **CSDL mẫu**, không phải dữ liệu học vụ chính thức của HUS.

## Kiểm chứng

`verify_data` kiểm tra các bất biến mà schema **không tự ràng buộc được** (DESIGN.md mục 11.3):

- đủ 13 bảng và 2 view;
- số dòng tối thiểu (catalog đã nạp);
- **không có vòng lặp tiên quyết** (A → B → A);
- mọi CTĐT đều có môn;
- mọi dòng `official_curriculum_entries` đều có môn tương ứng trong `curriculum_courses`.

Test tích hợp `tests/test_hus_postgres.py` yêu cầu biến `HUS_TEST_DATABASE_URL`
được đặt rõ ràng tới database `ai07` trên loopback. Test chỉ thêm hồ sơ/điểm tổng
hợp trong transaction và luôn rollback. Ví dụ dùng cấu hình local đang có:

```powershell
@'
import os
import pytest
from database.hus_db.config import load_config
os.environ['HUS_TEST_DATABASE_URL'] = load_config().url
raise SystemExit(pytest.main(['-q', 'tests/test_hus_database.py', 'tests/test_hus_postgres.py']))
'@ | .venv\Scripts\python.exe -
```
