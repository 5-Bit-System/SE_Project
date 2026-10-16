# Module database HUS / Neon (AI-07)

Thư mục này là **module cơ sở dữ liệu thứ hai** của dự án: bản mô phỏng cổng đào tạo HUS
dùng để phát triển và demo AI-07, chạy trên **PostgreSQL của Neon** (database `ai07`,
schema `public`).

> **Tách biệt với `app/db/`:**
> `app/db/` mô tả schema runtime của ứng dụng (`program_revisions`, `courses`, …).
> Thư mục `database/` này mô tả **thiết kế dữ liệu HUS** (`faculties`, `majors`,
> `curricula`, `students`, `course_attempts`, …). Hai thiết kế nói về hai thứ khác nhau,
> **không trộn** vào nhau.

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

## Thứ tự dựng database

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

## Trạng thái dữ liệu đã xác minh (Neon `ai07`)

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
