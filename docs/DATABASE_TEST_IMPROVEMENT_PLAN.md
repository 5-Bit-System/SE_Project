# Kế hoạch cải thiện bộ test database

Ngày lập: 21/10/2026. Nhánh tích hợp: `codebase`.
Nguồn: `feat/vinh-database-tests`, commit `9ca403d83d9f29f9cce40ed5253bfee143fbcdee`.

## Mốc đã xác minh

Chạy độc lập trên Windows, Python 3.11.9, dependency theo `requirements-lock.txt`,
PostgreSQL 16 Alpine trong container riêng, database mới được migrate và publish:

| Kiểm tra | Kết quả |
| --- | --- |
| Offline, loại ba marker integration/acceptance | 246 passed, 39 deselected |
| `postgres or hus_postgres` | 29 passed, 256 deselected |
| Tổng ca riêng biệt đã chạy | 275 passed |
| `database.tools.verify_data` | 26/26 đạt |
| Ruff; builder fixture bốn ngành; builder metadata mẫu | Đạt |

Trong 246 ca offline có 91 ca thuộc `tests/database/source` và `integrity`.
10 ca `full_catalog_acceptance` chưa chạy do thiếu bộ nguồn đã được rà soát độc lập.
Hai lượt chạy đều có cảnh báo deprecation của Starlette về httpx TestClient.
Đây là kết quả của commit nguồn trước tích hợp; merge fast-forward giữ nguyên mã
và dữ liệu đã kiểm thử. Kế hoạch này chưa triển khai các cải tiến dưới đây.

## Tiến độ cập nhật sau khi tích hợp

Đã triển khai trên nhánh `codebase` sau mốc ban đầu:

- **Hoàn thành P1 publisher rollback:** test PostgreSQL tiêm lỗi sau hai upsert
  thật, so sánh toàn bộ hàng ở các bảng nguồn và revision trước/sau, xác nhận
  repository vẫn ready và publisher chạy lại được.
- **Hoàn thành kiểm tra tiên quyết ổn định:** mỗi prerequisite thiếu được kiểm tra
  bằng ca tham số riêng, không còn chọn phần tử không xác định từ `set`.
- **Hoàn thành báo cáo CI và assertion verifier:** từng job xuất JUnit XML thành
  artifact ngay cả khi test thất bại; verifier yêu cầu tên các kiểm tra bắt buộc
  thay vì khóa cứng tổng số 26.
- **Chưa làm nghiệm thu PDF:** cần artifact nguồn được người phụ trách duyệt;
  repository hiện tại không có bộ này.
- **Chưa làm test đồng thời/hiệu năng.**

Kết quả chạy lại sau thay đổi: **250 passed, 39 deselected** ở nhóm offline;
**29 passed, 260 deselected** ở nhóm PostgreSQL. Ruff đạt. Có một cảnh báo
deprecation Starlette/httpx như trước. Bộ acceptance nguồn vẫn chưa chạy.
Không có thay đổi nào tới dữ liệu production; test rollback dùng PostgreSQL
container/database tạm trên máy.

## Thứ tự thực hiện

### 1. P1 — Kiểm tra rollback thật của publisher HUS — Hoàn thành

File chính: `tests/database/test_hus_migration_runtime.py`;
đường ghi: `database/tools/publish_catalogs.py`.

Ca hiện có làm trùng khóa nguồn và bị chặn ở preflight. Ca rollback của legacy
seed không xác minh transaction của publisher HUS.

- Dùng database tạm từ fixture `runtime_engine`, publish bản nguồn hợp lệ ban đầu.
- Chụp nội dung các bảng được publisher ghi, danh sách revision và revision active.
- Tạo bản nguồn thay đổi hợp lệ; giả lập lỗi sau một số upsert và tại bước đổi
  revision active. Dùng hook SQLAlchemy hoặc monkeypatch trong test, không thêm
  cơ chế gây lỗi vào luồng sản phẩm.
- Sau lỗi, mở connection mới và so sánh trạng thái với snapshot trước đó.
- Publish lại bản hợp lệ để xác nhận transaction/lock đã được giải phóng.

Nghiệm thu: không có dữ liệu hay revision ghi dở, cả bốn revision active giữ nguyên,
repository vẫn ready và lần publish kế tiếp thành công. Các ca chạy trong job
`hus_postgres` của CI.

### 2. P1 — Nghiệm thu dữ liệu nguồn độc lập — Chờ nguồn được duyệt

File chính: `tests/catalogs/test_curriculum_data.py`, `tests/conftest.py`,
`.github/workflows/checks.yml`.

- Chuẩn bị bộ dữ liệu đúng định dạng `--full-catalog-root`, được người phụ trách
  học vụ/dữ liệu rà soát; không tạo expected bằng chính builder đang kiểm tra.
- Lưu manifest phiên bản, SHA-256 PDF, trang/dòng tham chiếu và người duyệt.
  ZIP PDF không thể truyền trực tiếp làm catalog root.
- Đối chiếu bốn ngành, tên/mã môn, tín chỉ, nhóm tự chọn, môn không tính tổng và
  các quan hệ tiên quyết, bao gồm AND/OR và tham chiếu ngoài ngành.
- Giữ trạng thái chưa xác minh của các trường hợp chưa đủ bằng chứng, đặc biệt
  MAT3325 và MAT3423/MAT3402; ghi rõ phạm vi được nghiệm thu.
- Thêm job acceptance dùng artifact đã định phiên bản, chạy với
  `--full-catalog-root`; thiếu artifact phải báo thiếu điều kiện nghiệm thu,
  không được hiển thị như đã kiểm tra nguồn thành công.

Nghiệm thu: 10 ca acceptance thực sự được chạy; báo cáo ghi rõ pass/fail và các
ngoại lệ cần xử lý. Chỉ nâng trạng thái catalog sau quyết định nghiệm thu dữ liệu,
không tự nâng từ kết quả unit test.

Phụ thuộc: cần bộ nguồn được duyệt riêng; có thể làm các mục khác trong lúc chờ.

### 3. P2 — Làm các ca tiên quyết ổn định và đủ nhánh — Đã làm phần thiếu nhánh

File chính: `tests/database/source/test_reviewed_prerequisites.py`.

- Thay `{next(iter(passed))}` bằng tham số tường minh: tập rỗng, mỗi singleton,
  tập đủ điều kiện, cho từng ngành liên quan.
- Giữ bảng chân trị tám trường hợp cho `(A AND B) OR C`; bổ sung các biểu thức
  hỗn hợp/ngoặc lồng mà parser hỗ trợ với kỳ vọng độc lập.
- Kiểm tra dữ liệu chưa rõ hoặc xung đột vẫn bị chặn qua eligibility.

Nghiệm thu: mỗi nhánh thiếu điều kiện có test ID riêng; chạy tập ca liên quan với
ít nhất hai `PYTHONHASHSEED` khác nhau cho cùng kết quả và cùng phạm vi trường hợp.

### 4. P2 — Tăng độ rõ của báo cáo và CI — Đã làm JUnit và verifier

- Thay assertion chỉ khóa số lượng `len(results) == 26` bằng tập tên kiểm tra
  bắt buộc và kết quả tương ứng. Giữ assertion số môn khi đó là hợp đồng dữ liệu.
- Xuất JUnit XML cho từng job và lưu artifact kể cả khi test lỗi. Phân biệt
  passed, failed, skipped và deselected trong hướng dẫn/báo cáo.
- Ghi rõ các ca thiếu điều kiện nghiệm thu nguồn, không cộng chúng vào số ca đạt.
- Đánh giá nâng dependency tương thích để xử lý cảnh báo TestClient; chạy lại
  API tests trước khi cập nhật lockfile, không chỉ tắt cảnh báo.

Nghiệm thu: CI cung cấp báo cáo tải được; thêm một kiểm tra SQL mới không làm
test thất bại chỉ vì thay đổi tổng số; các kiểm tra bắt buộc bị thiếu vẫn làm fail.

### 5. P3 — Đồng thời và vận hành — Chưa bắt đầu

- Chạy hai publisher đồng thời trên database tạm bằng hai connection riêng;
  dùng synchronization và timeout giới hạn, tránh phụ thuộc thời gian sleep.
- Xác nhận mỗi ngành có đúng một revision active, không có trạng thái trộn trong
  một snapshot đọc nhất quán, và advisory lock được giải phóng khi transaction lỗi.
- Đo thời gian publish/read trên fixture lớn có quy mô được mô tả; ghi baseline
  trước khi quyết định ngưỡng hiệu năng. Tách khỏi unit tests thường ngày.

Nghiệm thu: ca đồng thời chạy ổn định, lỗi có timeout rõ ràng, không để lại database
hay dữ liệu thử. Chỉ đặt ngưỡng hiệu năng khi đã có môi trường và baseline ổn định.

## Cách bàn giao từng bước

Mỗi mục thành một PR riêng với vấn đề cần bắt, ca lỗi tái hiện được, kết quả trước
và sau. Ưu tiên mục 1, tiếp theo mục 3 và 4; chuẩn bị nguồn cho mục 2 song song
về lịch thực hiện; mục 5 sau khi các kiểm tra nền ổn định.

Chạy test liên quan trước, sau đó job offline/PostgreSQL tương ứng với thay đổi.
Trước khi chốt nghiệm thu, chạy cả ba nhóm và công bố riêng kết quả acceptance.
Không dùng test để publish vào database vận hành hoặc thay dữ liệu sinh viên thật.
