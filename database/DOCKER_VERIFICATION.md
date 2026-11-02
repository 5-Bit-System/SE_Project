# Kiểm chứng Docker HUS — 2026-10-17

Phạm vi: dựng schema HUS và dữ liệu CTĐT từ nhánh
`feat/database-setup-and-tests` trên PostgreSQL local, không dùng Neon.

## Môi trường

- Image `postgres:16-alpine`; project `se_hus`; container `se_hus_db`.
- Volume `se_hus_pgdata`; database `ai07`; schema `public`.
- Endpoint `127.0.0.1:5433`; user `ai07`.
- Mật khẩu ngẫu nhiên trong file bị Git bỏ qua `database/.env.docker`.
- `se_recommender_db`, volume `se_recommender_pgdata` và các container khác
  được giữ nguyên, không khởi động hoặc thay đổi.

## Bằng chứng thực thi

- Khởi tạo volume mới và chạy SQL `00`, `10` thành công.
- CLI `verify_data`: **26/26 passed** trên PostgreSQL thật.
- **13 bảng, 2 view**; 4 CTĐT, 174 môn, 290 liên kết, 279 prerequisite,
  41 nhóm nguồn và 297 dòng nguồn CTĐT.
- Nạp lại hai SQL: số bản ghi của mọi bảng/view giữ nguyên.
- Test module: **33 passed** (23 offline, 10 PostgreSQL thật).
- Full suite: **157 passed, 10 skipped**, một deprecation warning Starlette/httpx.
  Các test nguồn bên ngoài skip như thiết kế; không nâng dependency.
- Test thực tế CHECK/FK/UNIQUE cho điểm 10/4, số lần học, trạng thái,
  điểm bắt buộc khi đạt/trượt, môn/sinh viên không tồn tại và trùng lần học.
- Hai view trả đúng hồ sơ và cả lần trượt/lần đạt khi học lại.
- Test dùng dữ liệu tổng hợp trong transaction, luôn rollback. Sau test,
  `accounts`, `students`, `course_attempts`, `academic_terms`, `student_preferences`
  đều **0 bản ghi**; không còn schema tạm `se_test_*`.
- Restart container, chờ healthy rồi truy vấn lại: dữ liệu giữ nguyên.
- Ruff và `git diff --check` đạt.

Scanner SQL được sửa để bỏ qua comment và nội dung có quote; script `10`
không còn nhận nhầm comment `DOES NOT DROP database` thành lệnh xóa database.
Guard vẫn chặn keyword nguy hiểm qua xuống dòng/comment. Đây là kiểm tra
chống thao tác nhầm, không phải sandbox cho SQL không đáng tin.

## Chạy lại

Lệnh dựng/verify/test module nằm trong [README.md](README.md). Full suite:

```powershell
@'
import os
os.environ['PYTHONUTF8'] = '1'
import pytest
from database.hus_db.config import load_config
url = load_config().url
os.environ['HUS_TEST_DATABASE_URL'] = url
os.environ['TEST_DATABASE_URL'] = url
raise SystemExit(pytest.main(['-q']))
'@ | .venv\Scripts\python.exe -X utf8 -
```

Test runtime chỉ tạo/drop các schema ngẫu nhiên `se_test_*`; test HUS thêm dữ liệu
tổng hợp trong `public` rồi rollback. Không nhập thông tin sinh viên thật.

## Giới hạn

Kết quả chứng minh database local đã dựng, nạp và truy vấn thành công.
Chưa tích hợp schema HUS vào FastAPI, đăng nhập cổng đào tạo, đồng bộ bảng điểm
hoặc giao diện sử dụng database HUS. Chưa xác minh lại các PDF gốc hoặc quy chế
điểm/đạt/trượt. Các bảng hồ sơ sinh viên vẫn trống.
