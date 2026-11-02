# Database tests

Kiểm tra schema, migration, truy vấn và lưu trữ PostgreSQL; bao gồm runtime, persistence và các đường đi riêng của HUS.

Mốc local 22/10/2026 trên `codebase` commit `2bf1e5c`: **291 passed / 45 deselected** offline, **16 passed / 320 deselected** với `postgres`, **19 passed / 317 deselected** với `hus_postgres`. Mười ca `full_catalog_acceptance` vẫn skip do thiếu bộ nguồn đã review. Chi tiết môi trường, JUnit và giới hạn có trong [báo cáo kiểm thử](../../../docs/VINH_DATABASE_TEST_REPORT.md). Các số liệu cũ bên dưới là mốc lịch sử.

## Phần kiểm thử dữ liệu của Vinh

- `source/test_four_majors.py`: 16 ca cho 4 ngành; kiểm tra số môn, tín chỉ yêu cầu,
  bảo toàn từng dòng nguồn, quan hệ chương trình–môn học, mệnh đề tiên quyết,
  ngoại ngữ và các môn không tính vào tổng tín chỉ.
- `source/test_invalid_export.py`: 18 ca dữ liệu lỗi; kiểm tra khóa trùng,
  quan hệ thiếu, tín chỉ mâu thuẫn và tự tiên quyết bị từ chối trước khi ghi DB.
- `integrity/test_sql_checks.py`: 8 ca chạy truy vấn kiểm tra trên SQLite tạm;
  phát hiện chu trình tiên quyết, chương trình rỗng và môn nguồn thiếu quan hệ
  với đúng ngành. Các test này không xác minh DDL hoặc constraint PostgreSQL.

Chạy 42 ca mới từ thư mục gốc:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/database/source tests/database/integrity
```

Chạy toàn bộ test offline:

```powershell
.venv\Scripts\python.exe -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"
.venv\Scripts\python.exe -m ruff check .
```

CI tách ba report JUnit: `pytest-offline`, `pytest-postgres` và
`pytest-hus-postgres`. Artifact được tải lên kể cả khi pytest thất bại để phân biệt
ca passed, failed, skipped và deselected. Marker `postgres` và `hus_postgres` cần
PostgreSQL được cấu hình tường minh; mười ca `full_catalog_acceptance` vẫn skip cho
đến khi cung cấp `--full-catalog-root` trỏ tới bộ dữ liệu nguồn đã nghiệm thu.

Các fixture tích hợp xác thực URL **trước khi tạo engine**. `HUS_TEST_DATABASE_URL`
chỉ nhận PostgreSQL local `ai07`; `TEST_DATABASE_URL` chỉ nhận PostgreSQL local
`se_project_test`. Chỉ tham số query `sslmode` được phép để không chuyển hướng
host/database. Test HUS migration tạo và xóa database tạm; test legacy tạo và xóa
schema riêng trong `se_project_test`. Ca kiểm tra URL chạy offline trong
`test_database_targets.py` và `test_hus_migration_runtime.py`.
Test publisher HUS còn gây lỗi ngay sau khi tắt revision active để xác nhận
transaction rollback toàn bộ bảng và lần publish kế tiếp vẫn thành công.
Ca đồng thời với hai bundle tổng hợp khác nhau xác nhận bốn revision active,
source digest và metadata lưu trong PostgreSQL đều thuộc cùng một bundle.
Hai ca HUS PostgreSQL kiểm tra metadata từ source qua snapshot active, SQL,
repository và HTTP `/courses`, cùng tính bất biến của revision và quy tắc học vụ.

Xem kết quả, giới hạn và bước kiểm chứng PostgreSQL tại
[báo cáo kiểm thử](../../../docs/VINH_DATABASE_TEST_REPORT.md).

Rà soát bổ sung: `source/test_prerequisite_coverage.py` đối chiếu nhóm AND/OR với
ô nguồn và chặn môn có điều kiện chưa rõ theo 4 ngành (12 ca).
`test_hus_postgres.py` có thêm 2 ca đối chiếu dữ liệu tiên quyết trên PostgreSQL
với export. Xem [danh sách điều kiện cần xác minh](../../../docs/VINH_PREREQUISITE_AUDIT.md).

Sau sửa dữ liệu PDF, `source/test_reviewed_prerequisites.py` thêm 37 ca:
parser có dấu ngoặc và bảng chân trị, môn tham chiếu ngoài chương trình,
mở khóa bằng nhánh tiên quyết hợp lệ, giữ xung đột MAT3325, MAT3402 chưa rõ,
sửa trang nguồn và từ chối export bị mất quan hệ đã chuẩn hóa.
Kết quả lịch sử sau sửa dữ liệu PDF: **275 passed, 10 skipped** khi bật PostgreSQL; 10 ca bỏ qua
cần bộ dữ liệu nghiệm thu nguồn riêng.
