# BÀI TẬP CÁ NHÂN 3 — BIẾN THỂ VT-099
# SPECIFICATION, AI-ASSISTED PLAN VÀ RISK-BASED TEST STRATEGY

**Sinh viên:** Thái Văn Thắng — **MSSV:** 23001939 — **Nhóm:** SE2026-T25  
**Mã đề tài:** AI-07 — Explainable Course Recommender  
**Mã biến thể:** **VT-099**  
**Repository:** https://github.com/5-Bit-System/SE_Project  
**Baseline commit:** `1205fa94eadfaa6a52721e85cdab8a7dea9cfa11` ("Merge PR #148 … fix(rag)")  
**Nhánh Git:** `bt3/23001939-vt099`  

> **Cam kết:** *"Tôi chịu trách nhiệm về toàn bộ code, test và nội dung bài làm; tôi đã khai báo việc sử dụng AI."*

---

## 1. Specification và AI-Assisted Plan (15 điểm)

### 1.1. Problem Statement
Hệ thống hiện tại chỉ hỗ trợ hai vai trò người dùng trong cơ chế xác thực: `admin` (toàn quyền quản trị) và `student` (tra cứu thông tin qua VNU OAuth). Để giải quyết khối lượng lớn tài liệu crawl từ website HUS, ban quản trị cần phân quyền cho một vai trò mới là **`reviewer` (người kiểm duyệt)**. Reviewer có quyền đọc danh sách, xem chi tiết và đưa ra quyết định phê duyệt (`approved`) hoặc từ chối (`rejected`) tài liệu, nhưng **nghiêm cấm tuyệt đối việc chỉnh sửa dữ liệu gốc (`PUT /admin/crawler/documents/{id}/metadata` $\to$ HTTP 403 Forbidden)**.

Đồng thời, hàm kiểm duyệt hiện tại trong service (`review_document()`) dù đã có khóa `SELECT ... FOR UPDATE` và `publication_lock` nhưng **chưa hỗ trợ cơ chế so khớp trạng thái kỳ vọng (Compare-and-Set)**. Khi hai reviewer cùng mở một tài liệu đang ở trạng thái `pending` và gửi hai quyết định trái ngược nhau đồng thời (A duyệt `approve`, B duyệt `reject`), hệ thống sẽ âm thầm ghi đè quyết định của người đến sau (lỗi **Last-Writer-Wins / Conflicting Concurrent Modification**) mà không hề thông báo xung đột cho người duyệt.

### 1.2. Acceptance Criteria (Kiểm thử được & Strong Oracle)
* **AC1 (Quyền đọc và duyệt của Reviewer):** Tài khoản có `role = 'reviewer'` và session hợp lệ được phép truy cập `GET /admin/crawler/documents` (danh sách), `GET /admin/crawler/documents/{doc_id}` (chi tiết), `POST /admin/crawler/documents/{doc_id}/approve` (phê duyệt) và `POST /admin/crawler/documents/{doc_id}/reject` (từ chối), nhận mã phản hồi HTTP 200 OK.
* **AC2 (Bảo vệ dữ liệu gốc - Cấm sửa Metadata):** Tài khoản có `role = 'reviewer'` bị cấm tuyệt đối (**HTTP 403 Forbidden**) khi gửi yêu cầu `PUT /admin/crawler/documents/{doc_id}/metadata`. Chỉ tài khoản `admin` mới có quyền này. (Được kiểm chứng không pass rỗng: test xác nhận reviewer gọi `GET` thành công 200 trước khi gọi `PUT` bị 403).
* **AC3 (Xử lý xung đột đồng thời qua Compare-and-Set):** Endpoint `approve` và `reject` hỗ trợ trường tùy chọn `expected_status` trong payload. Khi hai yêu cầu kiểm duyệt gửi đồng thời vào cùng một tài liệu `pending` và cả hai cùng gửi `expected_status="pending"`: đúng một yêu cầu được chấp nhận (HTTP 200 OK), yêu cầu đến sau phát hiện trạng thái đã bị thay đổi và bị từ chối với mã **HTTP 409 Conflict** (thông báo xung đột trạng thái). Quyết định của người thắng cuộc được bảo toàn nguyên vẹn trong DB. Nếu không gửi `expected_status`, hệ thống giữ nguyên hành vi cập nhật không điều kiện (duyệt lại).
* **AC4 (Tính giải trình và toàn vẹn Audit Log):** Quyết định kiểm duyệt của `reviewer` phải lưu đúng `reviewer_id` trong bảng `crawled_documents` và ghi nhận một bản ghi kiểm toán trong bảng `admin_audit_logs`.

### 1.3. Non-functional Constraints
* **NFC1 (Hiệu năng tải đồng thời):** Hệ thống phải đáp ứng tốt ở mức tải **80 tác vụ đồng thời**, với mục tiêu độ trễ **p95 không quá 2.5 giây**. Phân tích rõ tác động của cơ chế tuần tự hóa do `pg_advisory_xact_lock` và hàng đợi connection pool của SQLAlchemy (`QueuePool`).
* **NFC2 (Bảo toàn 100% tính tương thích ngược):** Không thay đổi schema cơ sở dữ liệu của bảng `crawled_documents`; giữ nguyên vẹn 100% kết quả kiểm thử của các test suite hiện có (đặc biệt là bài test duyệt lại tài liệu `test_admin_document_review.py`).

### 1.4. Invariant / Contract Cốt lõi Cần Bảo vệ & Non-goals
> **Core Invariant:** *"Khi client chỉ định trạng thái kỳ vọng `expected_status`, tài liệu chỉ được chuyển trạng thái kiểm duyệt nếu trạng thái hiện tại khớp chính xác với kỳ vọng. Mọi yêu cầu đồng thời đến sau có cùng kỳ vọng phải bị từ chối với HTTP 409 Conflict (loại trừ Last-Writer-Wins). Vai trò reviewer chỉ có quyền đọc và duyệt, tuyệt đối không được phép chỉnh sửa dữ liệu gốc metadata."*

* **Non-goals / Residual Risks được ghi nhận:**
  1. *Cấp tài khoản Reviewer qua API:* Trong `app/api/auth.py` dòng 179, endpoint quản trị tài khoản chỉ cho phép đổi role sang `{'student', 'admin'}`. Việc mở rộng API quản lý người dùng để tạo/đổi role reviewer từ giao diện web là Non-goal của vertical slice này (tài khoản reviewer trong bài tập được cấp qua database seed / test fixture).
  2. *Phạm vi bảo vệ Concurrency:* Cơ chế chống race condition hoạt động khi client gửi trường `expected_status`. Nếu client cũ không gửi trường này, hệ thống sẽ thực hiện cập nhật vô điều kiện để tương thích ngược.
  3. *Quy chuẩn Schema DB:* Ràng buộc `accounts_role_check` ban đầu chỉ chấp nhận `('student', 'teacher', 'admin')`. Để đảm bảo tính toàn vẹn hệ thống mà không dùng DDL can thiệp trong fixture test (tránh rủi ro *false fixtures* theo Lecture 07), hệ thống bổ sung migration Alembic `database/hus_alembic/versions/20261111_14_reviewer_role.py` (`hus_20261111_14`) chính thức mở rộng ràng buộc cho `reviewer`.

### 1.5. Prompt ban đầu, Assumptions và Các File Dự định Thay đổi

* **Prompt ban đầu đã đưa cho AI Coding Agent:**
  > *"Em hãy đọc kỹ change request của biến thể VT-099: 'Thêm vai trò reviewer có quyền đọc và phê duyệt nhưng không được sửa dữ liệu gốc', risk trọng tâm là race condition khi hai yêu cầu đồng thời cùng thay đổi một tài nguyên. Hãy lập specification, implementation plan và test strategy theo đúng Lecture 06 và Lecture 07."*

* **Assumptions ban đầu (Giả định kỹ thuật):**
  1. Hệ thống đã có cơ chế xác thực local và session cookie, cần mở rộng để chấp nhận `role = 'reviewer'`.
  2. Tài khoản reviewer có thể đăng nhập bằng username/password qua `app/auth/repository.login()`.
  3. Cơ sở dữ liệu PostgreSQL đã có transaction isolation ở mức Read Committed, và hàm `review_document()` đã dùng `SELECT ... FOR UPDATE` và advisory lock.
  4. Việc kiểm soát race condition có thể thực hiện thông qua cơ chế Compare-and-Set trên trường trạng thái hiện tại mà không cần sửa đổi schema bảng `crawled_documents`.

* **Các File Dự định Thay đổi:**
  - `app/auth/repository.py`: Mở rộng câu truy vấn `login()` và `PRINCIPAL` cho role `reviewer`.
  - `app/api/admin.py`: Mở quyền cho `reviewer` tại `list_crawled_documents`, `get_crawled_document_detail`, `approve_crawled_document`, `reject_crawled_document`; thêm trường `expected_status` vào schema request; bắt `DocumentConflictError` trả về HTTP 409 Conflict.
  - `app/crawler/document_review_service.py`: Định nghĩa `DocumentConflictError`; bổ sung tham số `expected_status` vào `review_document()` và kiểm tra xung đột trạng thái.

### 1.6. Đề xuất Hai Phương án AI và Bác bỏ bằng Evidence
Theo yêu cầu bắt buộc của biến thể VT-099, AI đề xuất hai phương án kiến trúc và tiến hành lựa chọn dựa trên bằng chứng thực tế từ repository:

* **Phương án A (Được chọn): Compare-and-Set Tùy chọn qua Request Payload (`expected_status`) + Row Lock `FOR UPDATE`**
  - Mở rộng hàm `login()` và câu SQL `PRINCIPAL` trong `app/auth/repository.py` để hỗ trợ vai trò `role = 'reviewer'`.
  - Phân quyền tại 4 API endpoint đọc/duyệt trong `app/api/admin.py`, giữ cấm tuyệt đối endpoint `metadata`.
  - Thêm trường tùy chọn `expected_status: str | None = None` vào `DocumentReviewActionRequest`.
  - Trong `review_document()`, sau khi khóa dòng `SELECT id FROM crawled_documents WHERE id=:id FOR UPDATE`:
    ```python
    if expected_status is not None and doc.get("review_status") != expected_status:
        raise DocumentConflictError(
            f"Trạng thái tài liệu '{doc_id}' hiện tại là '{doc.get('review_status')}', "
            f"không khớp với trạng thái kỳ vọng '{expected_status}'."
        )
    ```
  - Trong `app/api/admin.py`, bắt lỗi `DocumentConflictError` trước `ValueError` để chuyển thành `HTTPException(409, detail=str(exc))`.
  - *Evidence chọn:* Không thay đổi schema DB; bảo toàn 100% các test suite hiện có (như `tests/api/test_admin_document_review.py` dòng 98–116 khi không gửi `expected_status`); loại trừ triệt để Last-Writer-Wins khi client gửi `expected_status="pending"`; diff nhỏ gọn và kiểm soát được (Lecture 06 tr.13).

* **Phương án B (Bị loại): Khóa Cứng Unconditional "Pending-Only"**
  - Sửa `review_document()` bắt buộc chỉ cho phép duyệt tài liệu đang ở trạng thái `pending`.
  - *Evidence loại:* Trực tiếp phá vỡ test hiện có trong repository (`tests/api/test_admin_document_review.py` dòng 107–116 cố tình duyệt lại tài liệu sau khi rejected), tước đoạt tính năng duyệt lại tài liệu và vi phạm ràng buộc NFC2.

* **Phương án C (Bác bỏ bổ sung): Optimistic Locking với Cột `version` trong Schema DB**
  - Thêm cột `version INT DEFAULT 1` vào bảng `crawled_documents`.
  - *Evidence loại:* Đòi hỏi thay đổi database schema, viết migration script, sửa API schema và giao diện web client. Phạm vi thay đổi quá lớn, vi phạm nguyên tắc "vertical slice nhỏ nhất chạy được" (Lecture 06 tr.13).

* **Phương án D (Bác bỏ bổ sung): In-Memory Mutex Lock (`threading.Lock`)**
  - Dùng `threading.Lock()` trong bộ nhớ Python để serialize request.
  - *Evidence loại:* Theo Lecture 07 tr.10, integration test phải kiểm tra boundary App $\leftrightarrow$ Database (schema, transactions, constraints). Khóa trong bộ nhớ Python hoàn toàn vô hiệu khi ứng dụng chạy nhiều tiến trình worker.

### 1.7. Phản biện và Sửa đổi dựa trên Code Repository Thực tế
Các đề xuất ban đầu của **Antigravity Coding Agent (DeepMind / Gemini)** và các phản biện đa tầng từ **Claude (Anthropic)** cùng **reviewer kỹ thuật của nhóm** đã được đối chiếu nghiêm ngặt và hiệu chỉnh dựa trên bằng chứng mã nguồn:
1. **Sửa đổi tên Endpoint:** AI ban đầu phỏng đoán generic `POST /admin/documents/{id}/review` và `DELETE /admin/documents/{id}`. Reviewer đã đọc [`app/api/admin.py`](file:///f:/SE_Project/app/api/admin.py) và chỉ ra các endpoint thực tế là `POST /admin/crawler/documents/{doc_id}/approve` & `/reject`, và sửa dữ liệu gốc là `PUT /admin/crawler/documents/{doc_id}/metadata`.
2. **Bác bỏ giả định "chưa có lock":** AI ban đầu nhận định mã nguồn chưa có lock và đề xuất thêm `FOR UPDATE`. Reviewer đã đọc [`app/crawler/document_review_service.py`](file:///f:/SE_Project/app/crawler/document_review_service.py) dòng 479–480 và chỉ ra hệ thống đã có `publication_lock` và `FOR UPDATE`, vấn đề thực chất là thiếu kiểm tra trạng thái kỳ vọng (Compare-and-Set) dẫn tới Last-Writer-Wins.
3. **Mở rộng Đầy đủ Tầng Auth:** AI ban đầu chỉ định sửa câu `PRINCIPAL`. Reviewer đã kiểm tra [`app/auth/repository.py`](file:///f:/SE_Project/app/auth/repository.py) dòng 91 và 102, chỉ ra hàm `login()` cũng giới hạn `role='admin'`. Kế hoạch đã bổ sung việc mở rộng `login()` cho role `reviewer`.
4. **Tránh Nuốt Mã Lỗi 409 thành 400:** Reviewer chỉ ra `admin.py` bắt `ValueError` ném 400. Do đó `except DocumentConflictError` phải đặt trước `except ValueError` và chốt đúng mã **HTTP 409 Conflict** (Strong Oracle, Lecture 07 tr.22).
5. **Khắc phục Mâu thuẫn Nghiệp vụ với Test Cũ:** Reviewer phát hiện `test_admin_document_review.py` dòng 98–116 có case duyệt lại tài liệu rejected. Kế hoạch đã chuyển sang cơ chế Compare-and-Set tùy chọn qua `expected_status` để bảo toàn 100% test cũ.
6. **Bảo vệ Working Tree khỏi Tác dụng phụ:** Test API sẽ monkeypatch `export_git_reviews_from_db` để tránh ghi file thật vào `data/hus/document_reviews.json` làm bẩn Git diff của PR.

---

## 2. Risk-Based Test Strategy và Bảng Test Cases (20 điểm)

### 2.1. Phân bổ Cấp độ Kiểm thử (Test Portfolio)
* **Unit Tests:** Kiểm tra logic thuần, validation đầu vào (`_safe_uuid`, `is_meaningful_content`).
* **Integration / API Tests (Trọng tâm):**
  - Kiểm tra ranh giới App $\leftrightarrow$ Database trên kết nối thật: xác thực `login()` và `session_from_token()` cho role `reviewer`.
  - Kiểm tra RBAC trên các endpoint: 200 OK cho đọc/duyệt, 403 Forbidden cho sửa metadata (có assertion chống pass rỗng).
  - Kiểm tra Concurrency Race Condition ở tầng service với **hai kết nối DB thật độc lập** và đồng bộ qua `threading.Barrier(2)`.
* **E2E Tests (Loại trừ có giải thích):** Theo Lecture 07 tr.8 & tr.12, kiểm thử E2E qua browser chậm và không thể tạo độ trễ vi giây chính xác để kiểm chứng race condition. Concurrency race condition được kiểm chứng đáng tin cậy nhất ở tầng Integration/Service với database thật.

### 2.2. Giải thích Cách Chọn Dữ liệu Kiểm thử (Test Data Selection) cho Concurrency Testing
Theo yêu cầu bắt buộc của đề bài VT-099 và nguyên lý Combinatorial Testing (Lecture 07 tr.16 & tr.26):
- **Tài khoản kiểm thử:** 2 tài khoản riêng biệt (`reviewer_1` và `reviewer_2`) có thật trong bảng `accounts`, mang `role='reviewer'`. Việc dùng 2 tài khoản thật đảm bảo không bị lỗi khóa ngoại `reviewer_id` trong `review_document()`.
- **Tài liệu kiểm thử:** 1 tài liệu `doc_concurrency_race` ở trạng thái `pending`, có nội dung markdown hợp lệ ($\ge 50$ ký tự, không phải marker trang) và `is_published = False`.
- **Hành động & Dữ liệu gửi:** Luồng 1 gửi quyết định `approve`, Luồng 2 gửi quyết định `reject`. Cả hai luồng cùng gửi tham số `expected_status = "pending"`.
- **Lý do lựa chọn:** Đây là tổ hợp nguy hiểm nhất (most critical combination) đại diện cho xung đột nghiệp vụ: hai người dùng cùng nhìn thấy trạng thái `pending`, đưa ra hai quyết định trái ngược nhau vào cùng một thời điểm. Nếu không có Compare-and-Set, hệ thống sẽ bị lỗi Last-Writer-Wins.

### 2.3. Bảng Ma trận Test Cases (Lecture 07 tr.16)

| Test ID | Risk / Requirement | Test Level | Precondition & Input | Expected Result (Strong Oracle) | Priority |
| :---: | :--- | :---: | :--- | :--- | :---: |
| **TC-01** | AC1: Reviewer đăng nhập và có session hợp lệ | DB / Integration | Tạo account `role='reviewer'`. Gọi `login()` và `session_from_token()`. | Đăng nhập thành công, session hợp lệ, `role = 'reviewer'`. | P0 |
| **TC-02** | AC1: Role lạ không có session | DB / Integration | Account có `role='guest'` (không hỗ trợ). Gọi `login()`. | `AuthFailure` (401 invalid_login). | P1 |
| **TC-03** | AC1: Reviewer đọc danh sách tài liệu | API | Account `reviewer`, session hợp lệ. Gọi `GET /admin/crawler/documents`. | HTTP 200 OK, danh sách tài liệu. | P1 |
| **TC-04** | AC1: Reviewer đọc chi tiết tài liệu | API | Account `reviewer`, session hợp lệ. Gọi `GET /admin/crawler/documents/{doc_id}`. | HTTP 200 OK, chi tiết tài liệu. | P1 |
| **TC-05** | AC1: Reviewer phê duyệt tài liệu pending | API | Tài liệu `pending`. Reviewer gửi `POST .../approve` kèm reason $\ge 3$ ký tự. | HTTP 200 OK, `review_status='approved'`, lưu đúng `reviewer_id`. | P0 |
| **TC-06** | AC1: Reviewer từ chối tài liệu pending | API | Tài liệu `pending`. Reviewer gửi `POST .../reject` kèm reason $\ge 3$ ký tự. | HTTP 200 OK, `review_status='rejected'`, lưu đúng `reviewer_id`. | P0 |
| **TC-07** | **AC2 (Negative 1):** Reviewer sửa metadata bị cấm (chống pass rỗng) | API | Account `reviewer`. Bước 1: `GET` tài liệu ra 200 OK. Bước 2: Gọi `PUT .../metadata`. | Bước 1: 200 OK. **Bước 2: HTTP 403 Forbidden**, metadata gốc giữ nguyên. | P0 |
| **TC-08** | **AC2 (Negative 2 - Regression):** Student gọi API kiểm duyệt | API | Account `student`. Gọi `POST .../{doc_id}/approve`. | **HTTP 403 Forbidden**. | P1 |
| **TC-09** | **AC2 (Negative 3 - Regression):** Anonymous gọi API kiểm duyệt | API | Chưa đăng nhập (không session). Gọi `POST .../{doc_id}/approve`. | **HTTP 401 Unauthorized**. | P1 |
| **TC-10** | **AC3 (Race Condition):** Hai kết nối duyệt đồng thời trên cùng tài liệu | Service / Concurrency | Hai kết nối DB thật (`conn1`, `conn2`), tài liệu `pending`. Luồng 1 `approve`, Luồng 2 `reject`, cùng gửi `expected_status="pending"`, đồng bộ qua `Barrier(2)`. | **Đúng 1 luồng commit thành công, 1 luồng ném `DocumentConflictError`**. DB lưu trạng thái người thắng. | P0 |
| **TC-11** | AC3: API ánh xạ DocumentConflictError thành HTTP 409 | API | Tài liệu đã `approved`/`rejected`. Reviewer gửi `POST .../reject` hoặc `POST .../approve` kèm `expected_status="pending"`. | **HTTP 409 Conflict**, detail giải thích rõ trạng thái xung đột (kiểm chứng cả 2 nhánh approve/reject). | P0 |
| **TC-12** | AC4: Audit trail lưu vết hành động của reviewer | API / DB | Reviewer duyệt thành công tài liệu. Kiểm tra bảng `admin_audit_logs`. | Có bản ghi audit với `actor_id = reviewer.id`, `action = 'document.approve'`. | P1 |
| **TC-13** | AC2: Reviewer bị cấm truy cập các endpoint quản trị khác | API | Reviewer có session gọi `GET /admin/overview` và `GET /admin/audit-logs`. | **HTTP 403 Forbidden** (Least Privilege RBAC bảo vệ toàn diện). | P1 |
| **TC-14** | AC1: Reviewer tuân thủ cờ must_change_password | DB / Auth | Tạo account reviewer với `must_change_password=True`. Gọi `login()`. | `session["must_change_password"] is True`. | P1 |
| **TC-15** | AC3: API validate expected_status theo enum Literal | API | Reviewer gửi `expected_status="not_a_valid_status"`. | **HTTP 422 Unprocessable Entity** (Strong Oracle, loại bỏ giá trị lạ). | P1 |

---

## 3. Lộ trình Thực thi & Quy tắc Commit (Git Flow)

1. **Khởi tạo nhánh Git từ Baseline:**
   ```powershell
   git checkout -b bt3/23001939-vt099 1205fa94eadfaa6a52721e85cdab8a7dea9cfa11
   git rev-parse HEAD  # Lưu vết baseline: 1205fa94eadfaa6a52721e85cdab8a7dea9cfa11
   ```
2. **TDD RED Phase:**
   - Viết test suite `tests/api/test_vt099_reviewer_concurrency.py`.
   - Chạy test, ghi nhận kết quả thất bại thực tế (không ghi khống kết quả), lưu log vào `deliverables/evidence/test-first-red.txt`.
   - Commit RED riêng biệt: `test: add failing tests for reviewer role rbac and concurrency conflict (RED)`.
3. **AI Patch & TDD GREEN Phase:**
   - Triển khai patch nhỏ: mở `login()` và `PRINCIPAL` trong `app/auth/repository.py`; mở quyền 4 endpoint đọc/duyệt và bắt `DocumentConflictError` ra 409 trong `app/api/admin.py`; thêm `DocumentConflictError` và `expected_status` trong `app/crawler/document_review_service.py`.
   - Review diff 4 lớp (Lecture 06 tr.17).
   - Chạy test, ghi nhận kết quả pass thực tế, lưu log vào `deliverables/evidence/test-first-green.txt`.
   - Commit GREEN: `feat(auth,admin): implement reviewer role rbac and compare-and-set concurrency protection (GREEN)`.
4. **Mutation Testing:**
   - Thử nghiệm Mutation 1: Bỏ validation cấm reviewer sửa metadata $\to$ Test TC-07 bắt được (**Killed**).
   - Thử nghiệm Mutation 2: Bỏ kiểm tra `expected_status` trong `review_document()` $\to$ Test TC-10 và TC-11 bắt được (**Killed**).
   - Lưu log vào `deliverables/evidence/mutation-killed.txt`. Revert commit tạm trước khi nộp.
5. **Concurrency Load Experiment:**
   - Chạy script `tools/verify_vt099_concurrency_load.py` kích hoạt **80 tác vụ đồng thời** (80 concurrent workers).
   - Đo lường và đối chiếu p95 so với mục tiêu $\le 2.5$ giây, phân tích hàng đợi connection pool và advisory lock.
   - Lưu log vào `deliverables/evidence/load-test-80-users.txt`.
6. **Deliverables & Hướng dẫn Nộp bài:**
   - Tạo thư mục `docs/assignment/` với `README.md` (hướng dẫn chạy test, link PR, cam kết không merge vào `main` khi nhóm chưa review).
   - Biên tập nội dung `deliverables/BT3_23001939_VT-099.html` và xuất sang `deliverables/BT3_23001939_VT-099.pdf` (tối đa 8 trang chính).
