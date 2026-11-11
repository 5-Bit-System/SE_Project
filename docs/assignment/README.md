# [SE2026][23001939] BT cá nhân 3 — AI-07 — VT-099

## Thông tin sinh viên và bài làm
- **Họ và tên:** Thái Văn Thắng
- **Mã số sinh viên (MSSV):** 23001939
- **Nhóm bài tập lớn:** SE2026-T25
- **Mã đề tài:** AI-07 (Explainable Course Recommender)
- **Mã biến thể:** **VT-099** (*Reviewer Role Moderation & Compare-and-Set Concurrency Conflict Protection*)
- **Baseline commit:** `1205fa94eadfaa6a52721e85cdab8a7dea9cfa11` ("Merge PR #148 … fix(rag)")
- **Nhánh Git:** [`bt3/23001939-vt099`](https://github.com/5-Bit-System/SE_Project/tree/bt3/23001939-vt099)
- **Tài liệu báo cáo:**
  - PDF: [`deliverables/BT3_23001939_VT-099.pdf`](../../deliverables/BT3_23001939_VT-099.pdf)
  - HTML gốc: [`deliverables/BT3_23001939_VT-099.html`](../../deliverables/BT3_23001939_VT-099.html)
  - Đặc tả & Kế hoạch TDD: [`docs/BT3_SPEC_AND_PLAN.md`](../BT3_SPEC_AND_PLAN.md)

> **Cam kết:** *"Tôi chịu trách nhiệm về toàn bộ code, test và nội dung bài làm; tôi đã khai báo việc sử dụng AI."*  
> **Lưu ý:** *"Không merge vào main khi nhóm chưa review."*

---

## Tóm tắt nội dung thay đổi của VT-099

Biến thể VT-099 triển khai một lát cắt dọc (vertical slice) hoàn chỉnh giải quyết yêu cầu phân quyền kiểm duyệt và bảo vệ xung đột đồng thời trong hệ thống RAG Tra cứu Đào tạo HUS:
1. **Phân quyền vai trò `reviewer` (Least Privilege RBAC):**
   - Reviewer có quyền đăng nhập xác thực local DB, tra cứu danh sách và xem chi tiết tài liệu crawl (`GET /admin/crawler/documents`, `GET /admin/crawler/documents/{id}`).
   - Reviewer có quyền phê duyệt (`POST .../approve`) hoặc từ chối (`POST .../reject`) tài liệu chờ duyệt (`pending`).
   - Reviewer **bị cấm tuyệt đối (HTTP 403 Forbidden)** khi cố tình chỉnh sửa siêu dữ liệu gốc (`PUT /admin/crawler/documents/{id}/metadata`). Quyền này chỉ thuộc về `admin`.
2. **Bảo vệ xung đột đồng thời (Compare-and-Set Concurrency Conflict Protection):**
   - Bổ sung trường tùy chọn `expected_status` trong payload kiểm duyệt (`Literal['pending', 'approved', 'rejected']`).
   - Khi hai reviewer cùng mở một tài liệu `pending` và gửi quyết định trái ngược nhau đồng thời kèm `expected_status="pending"`: hệ thống khóa hàng (`SELECT ... FOR UPDATE`), yêu cầu đầu tiên commit thành công (HTTP 200 OK), yêu cầu thứ hai phát hiện trạng thái đã đổi và bị từ chối ngay lập tức với **HTTP 409 Conflict** (loại trừ lỗi *Last-Writer-Wins* khi client chỉ định trạng thái kỳ vọng).
   - Bảo toàn 100% tính tương thích ngược cho các client cũ không gửi `expected_status` (vẫn hỗ trợ duyệt lại vô điều kiện).
3. **Quy chuẩn Schema Database bằng Alembic Migration:**
   - Hệ thống bổ sung migration `database/hus_alembic/versions/20261111_14_reviewer_role.py` (`hus_20261111_14`) mở rộng `accounts_role_check` cho vai trò `reviewer`.
   - Loại bỏ hoàn toàn việc chỉnh sửa DDL trong test fixtures (tránh lỗi *false fixtures*).

---

## Hướng dẫn Thiết lập Môi trường và Chạy Kiểm thử

### 1. Chuẩn bị Môi trường
Dự án sử dụng Python 3.11+ và cơ sở dữ liệu PostgreSQL. Kích hoạt môi trường ảo, đảm bảo database đã chạy migration mới nhất và thiết lập biến môi trường kết nối:

```powershell
# Di chuyển vào thư mục gốc repository
cd f:\SE_Project

# Thiết lập chuỗi kết nối database kiểm thử PostgreSQL
# Lưu ý an toàn thông tin: Thay thế <TEST_DB_PASSWORD> bằng mật khẩu cục bộ của bạn.
# Tuyệt đối không commit chuỗi chứa mật khẩu thực tế lên Git (CWE-798).
$env:HUS_TEST_DATABASE_URL = "postgresql+psycopg2://ai07:<TEST_DB_PASSWORD>@127.0.0.1:5433/ai07?sslmode=disable"

# BẮT BUỘC: Đảm bảo database đã chạy migration hus_20261111_14 mở rộng role reviewer
uv run alembic upgrade head
```

### 2. Chạy Test Suite VT-099 (15 Test Cases)
Test suite kiểm tra toàn diện 4 Acceptance Criteria (TC-01 đến TC-15) bao gồm xác thực, phân quyền RBAC, anti-vacuous authorization negative tests, service concurrency barrier race test, API 409 conflict (cả approve và reject) và literal validation:

```powershell
.venv\Scripts\python.exe -m pytest tests/api/test_vt099_reviewer_concurrency.py -v
```
*Kết quả kỳ vọng: 15 passed in ~5.0s.*

### 3. Chạy Regression Test Suite (Bảo toàn Test cũ)
Kiểm chứng 100% tính tương thích ngược với các test case duyệt tài liệu hiện có trong codebase:

```powershell
.venv\Scripts\python.exe -m pytest tests/api/test_admin_document_review.py -v
```
*Kết quả kỳ vọng: 2 passed in ~0.9s.*

### 4. Chạy Thử nghiệm Tải Đồng thời 80 Workers (NFC1 Load Experiment)
Harness kích hoạt đồng thời 80 tác vụ thông qua `ThreadPoolExecutor` và `threading.Barrier(80)` để đo lường phân bố độ trễ p95, xác nhận cơ chế tuần tự hóa advisory lock và connection pool:

```powershell
.venv\Scripts\python.exe tools/verify_vt099_concurrency_load.py
```
*Kết quả kỳ vọng: 80/80 requests hoàn tất, 0 lỗi 5xx, p95 latency đo được 1.4252s (dao động giữa các lần chạy trong khoảng ~0.76s - ~1.43s phụ thuộc tải CPU nền và trạng thái connection pool, hoàn toàn thỏa mãn mục tiêu SLA <= 2.50s).*

### 5. Kiểm thử Đột biến (Mutation Testing Verification)
Độ nhạy của test suite đối với các lỗi cố ý ("bỏ một validation quan trọng") được ghi nhận chi tiết tại [`deliverables/evidence/mutation-killed.txt`](../../deliverables/evidence/mutation-killed.txt):
- **Mutation 1 (Bỏ validation cấm reviewer sửa metadata trong `admin.py`):**
  - Chạy `pytest tests/api/test_vt099_reviewer_concurrency.py -k test_tc07`
  - Kết quả: **FAILED (KILLED)** do trả về 200 thay vì 403.
- **Mutation 2 (Bỏ validation Compare-and-Set `expected_status` trong `document_review_service.py`):**
  - Chạy `pytest tests/api/test_vt099_reviewer_concurrency.py -k "test_tc10 or test_tc11"`
  - Kết quả: **FAILED (KILLED)** do cả 2 luồng đều commit thành công mà không ném `DocumentConflictError`, API trả về 200 thay vì 409.
- **Tỉ lệ diệt đột biến:** 100% (2/2 mutations killed).

---

## Các Hạn chế Đã Biết & Lưu ý Vận hành (Known Limitations & Operational Notes)

1. **Giới hạn Khởi tạo Reviewer trên Giao diện Sản phẩm:**
   - Hiện tại, endpoint `PUT /api/auth/users/{account_id}` (`app/api/auth.py:179`) chỉ hỗ trợ đổi vai trò giữa `{'student', 'admin'}`. 
   - Vì vậy, việc cấp phát tài khoản `reviewer` trong môi trường thực tế hiện phải thực hiện thủ công bằng lệnh SQL trực tiếp vào bảng `accounts` hoặc qua migration/admin script chuyên biệt, chưa hỗ trợ trực tiếp từ UI quản trị chung.
2. **Lưu ý Ràng buộc khi Downgrade Database:**
   - Migration `hus_20261111_14` thêm role `reviewer` vào ràng buộc `accounts_role_check`. 
   - Nếu thực hiện rollback (`uv run alembic downgrade -1`) trong khi bảng `accounts` vẫn còn tồn tại các tài khoản mang `role = 'reviewer'`, PostgreSQL sẽ báo lỗi vi phạm check constraint. Quản trị viên cần xóa hoặc chuyển đổi các tài khoản reviewer sang role khác trước khi hạ cấp.
3. **Phạm vi Bảo vệ Compare-and-Set (CAS) & Giới hạn Giao diện UI:**
   - CAS là cơ chế tùy chọn kích hoạt khi client gửi trường `expected_status` trong payload kiểm duyệt.
   - Nếu client không gửi trường này, hệ thống sẽ thực hiện cập nhật vô điều kiện theo thiết kế nhằm bảo toàn 100% tính tương thích ngược cho quy trình duyệt lại của các client cũ.
   - Giao diện web frontend hiện tại chưa gửi trường `expected_status`, do đó sự bảo vệ chống race condition hiện có hiệu lực và được kiểm chứng ở tầng backend API/service; việc kích hoạt trên UI sẽ hoàn tất khi frontend bổ sung trường này.
4. **Giải thích Độ trễ Tải 80 Workers (Technical Hypothesis):**
   - Hiện tượng độ trễ của 80 worker phân bố trong khoảng hẹp (~1.38s - ~1.43s) trên máy thử nghiệm là một **giả thuyết kỹ thuật chưa kiểm chứng bằng profiler chuyên dụng**. Giả thuyết này dựa trên suy luận rằng Starlette `TestClient` in-process serialize HTTP request trước khi vào các khối database đồng bộ, kết hợp cùng cơ chế xếp hàng của `QueuePool`. Cần đo đạc bằng công cụ profiling phân tán để xác nhận nguyên nhân chính xác trong môi trường production.

---

## Danh mục Minh chứng Đã Lưu vết (Evidence Artifacts)

| Tên File Minh chứng | Vị trí | Mô tả nội dung |
| :--- | :--- | :--- |
| `test-first-red.txt` | `deliverables/evidence/test-first-red.txt` | Log test thất bại giai đoạn RED (commit `19e62ea`) |
| `test-first-green.txt` | `deliverables/evidence/test-first-green.txt` | Log test thành công giai đoạn GREEN (commit `a8567a0`) |
| `mutation-killed.txt` | `deliverables/evidence/mutation-killed.txt` | Nhật ký diệt 2 đột biến logic (100% Kill Score) |
| `coverage-report.txt` | `deliverables/evidence/coverage-report.txt` | Báo cáo coverage của coverage.py & ma trận AC coverage |
| `flaky-stability.txt` | `deliverables/evidence/flaky-stability.txt` | Phân tích rủi ro Flaky và vòng lặp 5 lần chạy (0% flakiness) |
| `load-test-80-users.txt` | `deliverables/evidence/load-test-80-users.txt` | Báo cáo tải 80 concurrent workers và phân tích chuyên sâu |
| `BT3_23001939_VT-099.html` | `deliverables/BT3_23001939_VT-099.html` | Báo cáo hoàn chỉnh 7 phần định dạng HTML in ấn |
| `BT3_23001939_VT-099.pdf` | `deliverables/BT3_23001939_VT-099.pdf` | File PDF báo cáo chính thức |
