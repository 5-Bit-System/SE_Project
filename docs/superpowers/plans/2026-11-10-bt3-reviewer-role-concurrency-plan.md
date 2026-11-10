# Kế hoạch Triển khai Bài tập Cá nhân 3 (BT3) — Biến thể VT-099 (Phiên bản Hoàn thiện v3)
# Implementation Plan: Reviewer Role RBAC & Concurrency Compare-and-Set Protection

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Sinh viên:** Thái Văn Thắng — **MSSV:** 23001939 — **Nhóm:** SE2026-T25  
**Mã đề tài:** AI-07 — Explainable Course Recommender  
**Mã biến thể cá nhân hóa:** **VT-099**  
**Repository:** https://github.com/5-Bit-System/SE_Project  
**Baseline Commit:** `1205fa94eadfaa6a52721e85cdab8a7dea9cfa11` ("Merge PR #148 … fix(rag)")  
**Nhánh Git:** `bt3/23001939-vt099`  

---

## 1. Mục tiêu & Bối cảnh Kỹ thuật (Goal & Tech Context)

* **Goal:** Bổ sung vai trò `reviewer` vào hệ thống xác thực local (`app/auth/repository.py`), cho phép đọc (`list`, `detail`) và đưa ra quyết định duyệt (`approve`, `reject`) tài liệu crawl (`crawled_documents`), nhưng nghiêm cấm tuyệt đối việc chỉnh sửa dữ liệu gốc (`PUT /admin/crawler/documents/{id}/metadata` $\to$ HTTP 403 Forbidden). Đồng thời, khắc phục triệt để lỗi nghiệp vụ Race Condition (Last-Writer-Wins) khi hai reviewer gửi yêu cầu duyệt đồng thời cho cùng một tài liệu bằng cơ chế so khớp trạng thái kỳ vọng Compare-and-Set (`expected_status` trong payload, trả về HTTP 409 Conflict khi xung đột), bảo toàn 100% tính tương thích ngược với các test suite hiện có.
* **Architecture:** 
  1. Tầng định danh & xác thực (`app/auth/repository.py`):
     - Mở rộng hàm `login()`: cho phép tìm kiếm và xác thực tài khoản có `role IN ('admin', 'reviewer')`.
     - Mở rộng câu truy vấn `PRINCIPAL`: chấp nhận session hợp lệ của tài khoản có `role = 'reviewer'`. Cờ `must_change_password` áp dụng cho cả `admin` và `reviewer`.
     - Viết test trực tiếp trên DB thật để xác nhận việc đăng nhập và nạp session của role `reviewer`.
  2. Tầng API Quản trị (`app/api/admin.py`):
     - Áp dụng gác cổng RBAC tại 4 endpoint đọc/duyệt: `list_crawled_documents` (GET, dòng 763), `get_crawled_document_detail` (GET, dòng 790), `approve_crawled_document` (POST, dòng 843), `reject_crawled_document` (POST, dòng 882) cho phép `principal.get("role") in ("admin", "reviewer")`.
     - Giữ nguyên cấm tuyệt đối tại `update_crawled_document_metadata` (PUT, dòng 803): `if principal.get("role") != "admin": raise HTTPException(403, "forbidden")`.
     - Bổ sung trường tùy chọn `expected_status: str | None = None` vào `DocumentReviewActionRequest`.
     - Bắt lỗi `DocumentConflictError` trước `ValueError` để chuyển thành `HTTPException(409, detail=str(exc))`, tránh bị nuốt thành HTTP 400.
  3. Tầng Nghiệp vụ & Cơ sở dữ liệu (`app/crawler/document_review_service.py`):
     - Tận dụng `publication_lock(conn)` và `SELECT id FROM crawled_documents WHERE id=:id FOR UPDATE` sẵn có.
     - Khắc phục Last-Writer-Wins: bổ sung tham số `expected_status: str | None = None`. Nếu `expected_status` được truyền và khác với `doc.get("review_status")`, ném `DocumentConflictError`. Nếu không truyền (None), giữ nguyên hành vi cập nhật vô điều kiện để tương thích ngược.
* **Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL 16 (psycopg2), Pytest.
* **Căn cứ Lý thuyết:**
  - **Lecture 06:** Vòng lặp `Spec -> Plan -> Generate -> Verify -> Own`; Context trước prompt (tr.11); Hợp đồng làm việc từ `main` (tr.12); Vertical slice nhỏ con người hiểu được (tr.13); Review diff 4 lớp (tr.17); Tránh các AI failure modes (tr.16); Chuỗi truy vết Traceability (tr.22).
  - **Lecture 07:** A passing test is evidence, not the whole argument (tr.1); Integration test kiểm tra ranh giới App $\leftrightarrow$ Database (tr.10); API tests bảo vệ contract và negative path (tr.11); State transition testing (tr.15); Combinatorial testing Role x Status x Action (tr.16); Tránh weak oracle & false fixtures (tr.22); Mutation testing (tr.23); Concurrency pattern demo (tr.26).

---

## 2. Ràng buộc Toàn cục (Global Constraints)

1. **Baseline Commit Không Đổi:** Toàn bộ công việc xuất phát từ commit `1205fa94eadfaa6a52721e85cdab8a7dea9cfa11` trên branch mới `bt3/23001939-vt099`.
2. **Không Thay đổi Schema Database:** Không thêm cột `version` hay bảng phụ mới; tận dụng các trường `review_status`, `reviewer_id`, `review_reason`, `reviewed_at` sẵn có trong bảng `crawled_documents`.
3. **Mã HTTP Phản hồi Chuẩn xác (Strong Oracle):** Xung đột đồng thời khi sai `expected_status` phải trả về **HTTP 409 Conflict**. Reviewer sửa dữ liệu gốc phải trả về **HTTP 403 Forbidden**.
4. **Bảo vệ Working Tree khỏi Tác dụng phụ:** Mọi bài test gọi endpoint duyệt phải monkeypatch hàm `export_git_reviews_from_db` để không làm bẩn file `data/hus/document_reviews.json` trên Git tree.
5. **Mức tải kiểm chứng:** Đạt 80 tác vụ đồng thời; đo đạc p95 so với mục tiêu 2.5 giây; phân tích rõ tác động của advisory lock toàn cục và connection pool.

---

## 3. Trọng tâm Đánh giá & Rủi ro Nghiệp vụ (Review Focus & Non-goals)

1. **Cấp tài khoản Reviewer qua API (Non-goal):**
   - Trong `app/api/auth.py` dòng 179, API chỉ cho phép đổi role sang `{'student', 'admin'}`. Mở rộng API đổi role cho reviewer từ web là Non-goal của vertical slice này (tài khoản reviewer được cấp qua DB fixture/seed).
2. **Phạm vi bảo vệ Concurrency:**
   - Cơ chế bảo vệ race condition có hiệu lực khi client gửi trường `expected_status`. Khi không gửi, hệ thống giữ hành vi duyệt lại vô điều kiện để bảo toàn 100% test cũ.
3. **Phòng chống Pass Rỗng (Vacuous Truth) trong Negative Tests:**
   - Trong `TC-07` (Reviewer bị cấm sửa metadata), test phải xác nhận trước tiên reviewer gọi `GET` ra 200 OK (chứng minh session hợp lệ), rồi mới kiểm tra `PUT` metadata ra 403 Forbidden.
4. **Cô lập Concurrency Test với 2 Kết nối Thật:**
   - `TC-10` bắt buộc phải mở **hai kết nối thật (`engine().connect()`)**, dùng `threading.Barrier(2)` để đồng bộ thời điểm gọi, và tự dọn dẹp dữ liệu trong khối `finally`. Cả 2 luồng đều dùng tài khoản reviewer có thật trong bảng `accounts`.

---

## 4. Kế hoạch Chi tiết Từng Task (Task Decomposition)

### Task 1: Đặc tả Yêu cầu, Bác bỏ Phương án & Lập Kế hoạch AI (Phần 1 - 15đ)

- [ ] **Bước 1.1: Soạn thảo Specification, Acceptance Criteria & Invariant**
  - Problem Statement, AC1..AC4, NFC1..NFC2, Core Invariant (đã hoàn thiện tại `docs/BT3_SPEC_AND_PLAN.md`).
- [ ] **Bước 1.2: Ràng buộc AI — Đề xuất 2 Phương án & Evidence Bác bỏ**
  - **Phương án A (Được chọn):** Compare-and-Set Tùy chọn qua Request Payload (`expected_status`) + Row Lock `FOR UPDATE`.
  - **Phương án B (Bị loại):** Khóa cứng Unconditional "Pending-Only". Evidence loại: Phá vỡ test duyệt lại hiện có (`test_admin_document_review.py` dòng 107–116).
  - **Phương án C (Bác bỏ bổ sung):** Optimistic Locking với cột version. Evidence loại: Đổi schema DB, migration, phình to diff (Lecture 06 tr.13).
  - **Phương án D (Bác bỏ bổ sung):** In-Memory Lock. Evidence loại: Vi phạm nguyên tắc kiểm tra ranh giới DB (Lecture 07 tr.10).
- [ ] **Bước 1.3: Ghi nhận Phản biện & Hiệu chỉnh Kế hoạch dựa trên Code Repository**
  - Ghi nhận đầy đủ phản biện từ reviewer kỹ thuật về endpoint, advisory lock, mở rộng `login()`, bắt lỗi 409, concurrency 2 kết nối thật và monkeypatch export file.

---

### Task 2: Thiết kế Chiến lược Test & Bảng Test Cases (Phần 2 - 20đ)

- [ ] **Bước 2.1: Phân bổ Test Portfolio theo Risk**
  - Phân bổ: Unit tests (pure logic), Integration/API tests (kiểm tra boundary DB, session, mã lỗi HTTP 200/403/409, concurrency race condition), loại trừ E2E UI.
- [ ] **Bước 2.2: Bảng Ma trận 12 Test Cases Chi tiết**

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
| **TC-11** | AC3: API ánh xạ DocumentConflictError thành HTTP 409 | API | Tài liệu đã `approved`. Reviewer gửi `POST .../reject` kèm `expected_status="pending"`. | **HTTP 409 Conflict**, detail giải thích rõ trạng thái xung đột. | P0 |
| **TC-12** | AC4: Audit trail lưu vết hành động của reviewer | API / DB | Reviewer duyệt thành công tài liệu. Kiểm tra bảng `admin_audit_logs`. | Có bản ghi audit với `actor_id = reviewer.id`, `action = 'document.approve'`. | P1 |

---

### Task 3: Triển khai Test-First (TDD) & AI-Assisted Patch (Phần 3 - 25đ)

- [ ] **Bước 3.1: Khởi tạo Nhánh Git từ Baseline Commit**
  ```powershell
  git checkout -b bt3/23001939-vt099 1205fa94eadfaa6a52721e85cdab8a7dea9cfa11
  git rev-parse HEAD  # Lưu vết baseline: 1205fa94eadfaa6a52721e85cdab8a7dea9cfa11
  ```

- [ ] **Bước 3.2: Viết Test-First Suite (RED Phase)**
  - Tạo file `tests/api/test_vt099_reviewer_concurrency.py`:
    + Viết test cases theo bảng thiết kế (TC-01 $\to$ TC-12).
    + Monkeypatch `export_git_reviews_from_db` để bảo vệ Git tree.
  - Chạy test suite và ghi nhận kết quả thất bại (**RED**) thực tế:
    + Quan sát và ghi nhận mã lỗi thực tế: Reviewer gọi API bị 403 Forbidden do `admin.py` chưa mở role; TC-01 fail do `login()` chưa hỗ trợ reviewer; TC-10 fail do thiếu Compare-and-Set.
    + Lưu log RED thật vào `deliverables/evidence/test-first-red.txt`.
    + Commit RED riêng: `test: add failing tests for reviewer role rbac and concurrency conflict (RED)`.

- [ ] **Bước 3.3: Triển khai Patch Nhỏ bằng AI (GREEN Phase)**
  - **Patch 1 (`app/auth/repository.py`):**
    + Trong `login()`: mở rộng `role IN ('admin', 'reviewer')`.
    + Trong `PRINCIPAL`: mở rộng `a.role IN ('admin', 'reviewer')` và cờ `must_change_password`.
  - **Patch 2 (`app/crawler/document_review_service.py`):**
    + Định nghĩa:
      ```python
      class DocumentConflictError(ValueError):
          """Raised when a document review transition conflicts with its expected state."""
      ```
    + Trong `review_document()`: thêm tham số `expected_status: str | None = None`. Nếu được cung cấp và khác `doc.get("review_status")`, ném `DocumentConflictError`.
  - **Patch 3 (`app/api/admin.py`):**
    + Thêm `expected_status: str | None = None` vào `DocumentReviewActionRequest`.
    + Cập nhật quyền tại `list_crawled_documents`, `get_crawled_document_detail`, `approve_crawled_document`, `reject_crawled_document`:
      ```python
      if principal.get("role") not in ("admin", "reviewer"):
          raise HTTPException(403, "forbidden")
      ```
    + Trong `approve_crawled_document` và `reject_crawled_document`:
      ```python
      except DocumentConflictError as exc:
          raise HTTPException(409, detail=str(exc)) from exc
      except ValueError as exc:
          raise HTTPException(400, detail=str(exc)) from exc
      ```
  - Review diff theo 4 lớp (Lecture 06 tr.17): Scope $\to$ Design $\to$ Correctness $\to$ Evidence.

- [ ] **Bước 3.4: Chạy lại Test & Xác nhận Thành công (GREEN Phase)**
  - Chạy lại test suite: `pytest tests/api/test_vt099_reviewer_concurrency.py -v`.
  - Chạy lại test suite hồi quy: `pytest tests/api/test_admin_document_review.py -v` xác nhận 100% test cũ vẫn PASS.
  - Ghi nhận kết quả test thực tế và lưu log vào `deliverables/evidence/test-first-green.txt`.
  - Commit GREEN: `feat(auth,admin): implement reviewer role rbac and compare-and-set concurrency protection (GREEN)`.

---

### Task 4: Đánh giá Sức mạnh Test Suite — Mutation & Flaky Review (Phần 4 - 20đ)

- [ ] **Bước 4.1: Thử nghiệm Deliberate Bug / Mutation Testing**
  - **Mutation 1 (Bỏ validation cấm sửa metadata):**
    + Trong `app/api/admin.py` tại `update_crawled_document_metadata`: sửa `if principal.get("role") not in ("admin", "reviewer"):`.
    + Chạy `TC-07` $\to$ Test phát hiện hành vi sai trái và **FAIL** $\to$ **Mutation 1 Killed!**
  - **Mutation 2 (Bỏ validation kiểm tra expected_status):**
    + Trong `review_document()`: comment out đoạn kiểm tra `expected_status`.
    + Chạy `TC-10` và `TC-11` $\to$ Test phát hiện Last-Writer-Wins và **FAIL** $\to$ **Mutation 2 Killed!**
  - Tạo commit tạm ghi nhận hash mutation, lưu log thực tế vào `deliverables/evidence/mutation-killed.txt`.
  - Khôi phục code chuẩn (revert commit tạm), đảm bảo nhánh nộp bài sạch sẽ.

- [ ] **Bước 4.2: Đo Coverage & Đánh giá Flaky Risks**
  - Sử dụng công cụ coverage cục bộ (không thêm `pytest-cov` vào `requirements-dev.txt` để tránh dependency drift).
  - Lưu kết quả vào `deliverables/evidence/coverage-report.txt`.
  - Lập bảng so sánh Line/Branch Coverage với Risk Coverage theo ACs (Lecture 07 tr.18).
  - Đánh giá 2 nguy cơ Flaky Test (Shared State & Concurrency Timing - Lecture 07 tr.21).

---

### Task 5: Thực nghiệm Kiểm chứng Tải Concurrency (Phần 5 - 5đ)

- [ ] **Bước 5.1: Xây dựng Concurrency Load Harness**
  - Tạo script `tools/verify_vt099_concurrency_load.py`:
    + Mô phỏng 80 tác vụ đồng thời gửi yêu cầu duyệt tài liệu thông qua `ThreadPoolExecutor(max_workers=80)`.
    + Đo lường thời gian phản hồi từng request (latency).
- [ ] **Bước 5.2: Phân tích Số liệu & Giới hạn Kết luận Thực tế**
  - Đo lường và ghi nhận các phân vị: p50, p90, p95, p99.
  - So sánh p95 với mốc $\le 2.5$ giây.
  - Lưu log vào `deliverables/evidence/load-test-80-users.txt`.
  - Thảo luận trung thực về giới hạn kết luận: tác động của advisory lock toàn cục (`publication_lock`) tuần tự hóa giao dịch, và tác động của hàng đợi connection pool trong SQLAlchemy `engine()` (`QueuePool` size 5 overflow 10).

---

### Task 6: Engineering Evidence, Traceability, Reflection & Báo cáo PDF (Phần 6 - 15đ)

- [ ] **Bước 6.1: Ma trận Truy vết (Traceability Matrix)**
  - Lập bảng ánh xạ: `Acceptance Criterion / Risk -> Test ID -> Test File -> Commit Hash / PR -> Kết quả thực tế`.
- [ ] **Bước 6.2: AI Usage Log Chi tiết**
  - Khai báo đầy đủ công cụ sử dụng (Antigravity Agent, Codegraph MCP, Claude review feedback).
  - Ghi lại các Prompt chính ban đầu, Assumptions, Output được dùng, các điểm phản biện / bác bỏ dựa trên mã nguồn thực tế.
  - Phân tích 2 điểm AI không đáng tin cậy ban đầu (Plausible but wrong về endpoint và False confidence về advisory lock).
- [ ] **Bước 6.3: Viết Reflection (250–350 từ)**
  - Phản ánh trung thực: Điều gì làm tăng sự tự tin (TDD RED $\to$ GREEN, Concurrency Barrier, Mutation Testing); điều gì vẫn chưa được chứng minh (tác động khi nhiều process uvicorn tranh chấp pool, tài liệu rejected chưa thể mở lại); test tiếp theo có giá trị cao nhất.
- [ ] **Bước 6.4: README Hướng dẫn Chạy Test & Báo cáo PDF `BT3_23001939_VT-099.pdf`**
  - Tạo `docs/assignment/README.md` hướng dẫn chạy test, ghi link PR và cam kết không merge vào `main` khi nhóm chưa review.
  - Soạn thảo nội dung trong `deliverables/BT3_23001939_VT-099.html` tuân thủ đúng cấu trúc 8 trang chính.
  - Xuất ra file PDF: `deliverables/BT3_23001939_VT-099.pdf`.
