# Báo cáo kiểm thử database — Vinh

Ngày cập nhật: **22/10/2026**. Các kết quả gốc ngày 20/10/2026 trên commit `26aeb39` được giữ ở phần lịch sử bên dưới.

## Kết quả sau cải thiện test database

Nền mã kiểm tra: `codebase` tại commit **`2bf1e5c`** (gồm các commit riêng `9327166` cho publish đồng thời và `2bf1e5c` cho metadata persistence/API). Môi trường: Windows, Python **3.11.9**, PostgreSQL **16.15** trong Docker local; dependency từ `.venv` của dự án. Các nhóm dưới đây chạy riêng, với marker và database thử nghiệm tường minh.

| Nhóm kiểm tra | Kết quả | Đối tượng |
| --- | ---: | --- |
| Offline, loại `postgres`, `hus_postgres`, `full_catalog_acceptance` | **291 passed, 45 deselected** | Fixture tổng hợp, source regression và URL guard |
| `postgres` | **16 passed, 320 deselected** | Schema riêng trong `se_project_test` |
| `hus_postgres` | **19 passed, 317 deselected** | `ai07` chỉ đọc/rollback test; migration/publisher trên database tạm |
| `full_catalog_acceptance` | **10 skipped, 326 deselected** | Chưa có bộ nguồn được review qua `--full-catalog-root` |

Ba nhóm kỹ thuật có **326 ca passed riêng biệt**, không có ca failed. Ruff, bốn fixture builder tổng hợp và `database.tools.verify_data` (**26/26**) đạt. Có một cảnh báo Starlette/httpx TestClient đã tồn tại. Đây là kết quả local của ba nhóm marker dùng trong CI; chưa chạy toàn bộ bước thiết lập/publish của GitHub Actions và chưa xác nhận CI cho hai commit mới.

Test P0 từ chối URL sai đích trước khi tạo engine. Test P1 chèn lỗi ngay sau khi tắt revision active, publish hai bundle tổng hợp khác nhau đồng thời, và kiểm tra metadata qua SQL, repository, `/courses`. Sau chạy, không còn database `ai07_runtime_test_*` hay schema `se_test_*`; `accounts`, `students`, `course_attempts` trong `ai07` đều có **0** dòng. Database thử nghiệm `se_project_test` được giữ để chạy lại test legacy. Không publish metadata mới vào runtime `ai07` trong lượt này.

Chạy lại từ thư mục gốc với `TEST_DATABASE_URL` trỏ PostgreSQL local `se_project_test` và `HUS_TEST_DATABASE_URL` trỏ PostgreSQL local `ai07` (nạp thông tin từ file cấu hình bị Git bỏ qua, không ghi mật khẩu vào lệnh hoặc báo cáo):

```powershell
.venv\Scripts\python.exe -m pytest -q -m "not postgres and not hus_postgres and not full_catalog_acceptance"
.venv\Scripts\python.exe -m pytest -q -m postgres
.venv\Scripts\python.exe -m pytest -q -m hus_postgres
.venv\Scripts\python.exe -m pytest -q -m full_catalog_acceptance
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m database.tools.verify_data
```

JUnit XML của lượt local nằm trong thư mục Git bỏ qua `backups/database-tests-20261022-2bf1e5c/`: `offline.xml`, `postgres.xml`, `hus-postgres.xml`, `acceptance-skipped.xml`. Workflow `.github/workflows/checks.yml` đã cấu hình upload ba artifact JUnit kỹ thuật cho các lần chạy CI. Test fixture và việc khớp source export/SQL không thay thế review độc lập PDF; bốn catalog vẫn `draft_unverified`.

## Kết quả lịch sử sau sửa tiên quyết

- Toàn bộ suite chạy với PostgreSQL: **275 passed, 10 skipped** trong 34,77 giây.
- Ruff đạt; `database.tools.verify_data` đạt **26/26** kiểm tra.
- Export/database có **179 môn, 348 quan hệ tiên quyết**, gồm 5 môn tham chiếu
  đã đối chiếu PDF Toán tài năng. Vẫn 4 ngành, 290 membership, 297 dòng nguồn.
- 20 ô nguồn được chuẩn hóa, MAT3359 có điều kiện có dấu ngoặc đúng cấu trúc.
- MAT3325 giữ hai điều kiện theo nhóm và bị chặn do `conflict`; MAT3423 vẫn
  `unknown` do MAT3402 chưa rõ. Không gán mã tương đương hoặc tạo môn giả.
- Hai locator của MAT3327 Toán tin và MAT2034 Khoa học dữ liệu đã sửa.
- Đã sao lưu và publish revision mới vào PostgreSQL cục bộ; kiểm tra HTTP qua web đạt.

Các kết quả bên dưới ghi các mốc trước khi sửa. Bằng chứng PDF, phạm vi kiểm tra
và sao lưu ở [báo cáo đối chiếu PDF](VINH_PDF_SOURCE_REVIEW.md).

## Phạm vi và dữ liệu

Kiểm thử export đang được runtime HUS sử dụng tại
`database/data/hus_source.json`. Bản clone không có nhánh tên `datasetup`;
nhánh liên quan hiện có là `origin/feat/database-setup-and-tests`. Báo cáo này
không khẳng định đã kiểm thử một nhánh `datasetup` riêng hoặc dữ liệu crawl mới.

Export có 174 môn dùng chung, 290 quan hệ chương trình–môn, 279 quan hệ tiên quyết,
41 nhóm chương trình và 297 dòng nguồn.

| Ngành | Số môn trong chương trình | Dòng nguồn | Tín chỉ yêu cầu |
| --- | ---: | ---: | ---: |
| Toán học | 90 | 96 | 135 |
| Toán tin | 68 | 69 | 132 |
| Khoa học máy tính và thông tin | 67 | 67 | 129 |
| Khoa học dữ liệu | 65 | 65 | 127 |

Một môn có thể xuất hiện trong nhiều dòng nguồn. Tổng tín chỉ yêu cầu không phải
tổng tín chỉ của tất cả môn được liệt kê vì có môn tự chọn và môn không tính tổng.

## Kết quả thực chạy

Môi trường: Windows, Python 3.12.10, `.venv`, dependency theo
`requirements-dev.txt` với constraints `requirements-lock.txt`.

- Bổ sung 42 ca: 16 kiểm tra 4 ngành, 18 kiểm tra từ chối export lỗi,
  8 kiểm tra logic truy vấn SQL bằng dữ liệu tổng hợp trên SQLite tạm.
- Toàn bộ bộ test offline: **197 passed, 37 deselected**.
- Kiểm thử PostgreSQL thật sau khi cài Docker: **27 passed, 207 deselected**
  trong 23,59 giây với marker `hus_postgres or postgres`.
- `python -m database.tools.verify_data`: **26/26 kiểm tra đạt** trên database
  `ai07`, PostgreSQL **16.15** trong container `se_hus_db`, cổng `127.0.0.1:5433`.
- `python -m ruff check .`: **đạt**.
- Kiểm tra builder trên `tests/support/fixtures/catalogs`: **đạt** cho 4 bộ
  fixture tổng hợp; không dùng kết quả này làm bằng chứng nghiệm thu học thuật.
- Có một cảnh báo deprecation từ FastAPI/Starlette về httpx; không có test lỗi.

Lệnh chạy lại nằm trong `tests/database/README.md`.

## Giới hạn và phần cần xác minh tiếp

Đã chạy cả 27 ca PostgreSQL trên Docker cục bộ: schema/import HUS, constraint
điểm và lượt học, khóa ngoại, view bảng điểm có học lại, seed lặp không tạo dữ liệu
trùng, lưu/đọc catalog, rollback khi seed lỗi, migration và khôi phục revision.
Ca migration HUS tạo database tạm riêng; các ca legacy tạo schema ngẫu nhiên
riêng. Các dữ liệu sinh viên tổng hợp trong test được rollback.

Sau kiểm thử, runtime readiness đạt, migration head là `hus_20261017_02`, có
4 revision hoạt động với số môn 65/67/68/90. Các bảng `accounts`, `students`,
`course_attempts` đều có 0 dòng. Không còn database `ai07_runtime_test_*` hay schema
`se_test_*` do test tạo. Container và volume dữ liệu project được giữ lại.

Kết quả 197 test offline và 27 test PostgreSQL đến từ hai lượt chạy riêng.
10 ca nghiệm thu nguồn đầy đủ chưa chạy vì thiếu bộ nguồn đã rà soát. Các test
SQLite bổ sung kiểm tra logic truy vấn, còn constraint/migration được xác minh
bằng các test PostgreSQL nêu trên.

Export hiện có trạng thái `draft_unverified`. Các test xác nhận tính nhất quán
và bảo toàn dữ liệu xuất, chưa chứng minh dữ liệu đúng với PDF/quy chế chính thức.
Các số lượng ở bảng trên là mốc hồi quy của bản export, không phải kết quả đối
chiếu nguồn độc lập.

Đã tạo `database/.env.docker` (Git bỏ qua) với mật khẩu ngẫu nhiên, migrate bằng
`database.tools.migrate upgrade`, và nạp dữ liệu bằng
`database.tools.publish_catalogs`. Có thể chạy lại các kiểm tra SQL:

```powershell
.venv\Scripts\python.exe -m database.tools.verify_data
.venv\Scripts\python.exe -c "import os,pytest; from dotenv import dotenv_values; url=dotenv_values('database/.env.docker')['HUS_DATABASE_URL']; os.environ['HUS_TEST_DATABASE_URL']=url; os.environ['TEST_DATABASE_URL']=url; raise SystemExit(pytest.main(['-q','-m','hus_postgres or postgres']))"
```

Chỉ đặt biến này cho database kiểm thử cục bộ. Các ca integration hiện có bao gồm
kiểm tra schema/import, constraint điểm và lượt học, view bảng điểm và lưu catalog.
Nghiệm thu đối chiếu PDF cần bộ dữ liệu đã được rà soát riêng qua
`--full-catalog-root`, theo hướng dẫn của repository.

Xem lịch sử Git để biết commit bàn giao phần kiểm thử và sửa tiên quyết.

## Cập nhật rà soát tiên quyết

Sau yêu cầu kiểm tra thêm của lead, bổ sung 14 test và chạy toàn bộ suite với
PostgreSQL: **238 passed, 10 skipped** trong 38,79 giây; Ruff đạt.
279 quan hệ đã chuẩn hóa khớp SQL/export/database, nhưng còn 19 dòng chứa mã
chưa có trong danh mục và 2 dòng biểu thức phức tạp. Cả 21 trường hợp đều bị chặn
trong runtime, chưa thể khẳng định dữ liệu tiên quyết đầy đủ theo PDF gốc.
Danh sách môn, trang nguồn và phần cần Trung/lead xác minh nằm trong
[báo cáo rà soát tiên quyết](VINH_PREREQUISITE_AUDIT.md).

Sau khi người dùng cung cấp ZIP, đã rà trực tiếp cột tiên quyết của bảng bốn
chương trình và tra bổ sung PDF Toán tài năng: tìm được định nghĩa cho 5/6 mã
vắng, xác nhận biểu thức MAT3359 và hai dòng MAT3325 khác nhau trong nguồn, phát
hiện hai tham chiếu trang bị lệch. Chưa sửa dữ liệu hoặc publish lại.
Xem [kết quả đối chiếu PDF gốc](VINH_PDF_SOURCE_REVIEW.md).
