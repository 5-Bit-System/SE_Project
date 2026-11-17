# Document Review Pipeline Remediation Plan (Bước 1, 2, 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task maps to one GitHub issue and one or more clean commits.

**Goal:** Khắc phục triệt để 3 lỗi P1 (auto-approval heuristic, version mismatch sync, dual-write inconsistency) và 4 hạn chế (marker-only approved files, taxonomy mismatch, startup sync discrepancy, test DB pollution) trong phân hệ Document Review của HUS, đảm bảo tính toàn vẹn dữ liệu, kiểm soát chất lượng nội dung và bằng chứng kiểm thử trực quan.

**Architecture:** 
- Chuyển PostgreSQL DB thành Single Source of Truth (SSOT). File `data/hus/document_reviews.json` là snapshot Git-tracked chỉ được xuất ra sau khi DB transaction đã commit thành công (Post-commit export pattern với atomic write `.tmp` -> `rename` an toàn và retry).
- Ràng buộc chặt chẽ điều kiện đồng bộ Git -> DB: `(id = :id OR url = :url) AND content_hash = :content_hash AND is_published = false`. Nếu hash không khớp hoặc nguồn thay đổi, tài liệu bắt buộc giữ trạng thái `pending` để admin duyệt lại.
- Thiết lập Content Quality Gate: Chặn không cho duyệt `approved` đối với bất kỳ tài liệu nào có nội dung hữu ích < 50 ký tự (sau khi loại bỏ comment/marker trang). Chuyển 21 file marker về `pending_ocr`.
- Chuẩn hóa taxonomy phân loại: Chuyển 18 tài liệu đa ngành bị gom nhầm trong `mathematics/` về `major: "general"`.
- Tách biệt rõ ràng CLI sync và Startup sync (có feature flag `AUTO_SYNC_DOCUMENT_REVIEWS` an toàn trong FastAPI lifespan).
- Áp dụng Transaction Rollback fixture cô lập cho toàn bộ test suite DB để triệt tiêu ô nhiễm dữ liệu.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, PostgreSQL, Pydantic, Pytest, Playwright, Git, GitHub Issues & PRs.

**Spec:** Báo cáo kiểm chứng độc lập 7 lỗi & hạn chế ngày 2026-11-08; `app/crawler/document_review_service.py`, `tools/seed_real_crawled_documents.py`, `data/hus/document_reviews.json`.

---

## Global Constraints

- **Single Source of Truth (SSOT):** PostgreSQL là nguồn dữ liệu duy nhất cho trạng thái kiểm duyệt (`crawled_documents`). File JSON chỉ đóng vai trò snapshot sao lưu và seed ban đầu.
- **Dữ liệu thực tế, không đoán bừa:**
  - 179 tài liệu markdown đã crawl trong `data/hus/processed/documents/`.
  - 21 file chỉ chứa comment/marker trang (`<!-- page ... -->`), trong đó 1 file rỗng (`tai-lieu-dinh-kem-104-khmttt-chuan-final-qd-3568-scan-final--55482733.md`, `doc_42f38f75db40`) đang mang trạng thái `approved` trái phép.
  - 70 bản ghi trong `data/hus/document_reviews.json`, trong đó đúng 67 bản ghi có `reviewer_id: null` do tool seed tự gán `approved` hoặc `rejected`.
  - 18 file tài liệu đa ngành (Hóa dược, Địa chất, Sinh học, Vật lý...) trong `data/hus/processed/documents/mathematics/` bị gán nhãn sai `major: "mathematics"`.
  - Ngưỡng văn bản hữu ích tối thiểu để được duyệt `approved`: 50 ký tự văn bản thuần (sau khi strip frontmatter và HTML comments).
- **Tính bất biến của phiên bản (Version Immutability):** Không bao giờ tự động áp đặt trạng thái duyệt của phiên bản cũ lên phiên bản có `content_hash` mới hoặc tài liệu đã `is_published = true`.
- **An toàn giao dịch (Transactional Safety):** Mọi thao tác ghi đĩa (`document_reviews.json`) chỉ được thực hiện SAU KHI transaction DB đã commit thành công.
- **Git & GitHub Workflow:**
  - Mỗi nhóm vấn đề có một GitHub Issue riêng biệt để theo dõi tiến độ.
  - Mỗi commit phải clean, nhỏ gọn, thông điệp rõ ràng theo chuẩn Conventional Commits (`feat(...)`, `fix(...)`, `test(...)`), tham chiếu đến issue (`closes #...` hoặc `fixes #...`).
  - Sử dụng Subagent độc lập: Subagent Implementer lập trình và Subagent Reviewer kiểm soát chất lượng code độc lập trước khi đánh dấu hoàn thành.
- **Bằng chứng kiểm chứng bắt buộc:** Mọi báo cáo phải đi kèm kết quả test suite xanh 100% và ảnh chụp màn hình Playwright thực tế trên giao diện Admin Console.

---

## Review Focus

1. **Dual-write failure & Transaction Rollback:** Khi DB transaction thất bại (rollback), file `data/hus/document_reviews.json` tuyệt đối không bị ghi bẩn trạng thái `approved`.
2. **Version Hash Mismatch Protection:** Khi file tài liệu trên đĩa thay đổi nội dung (sinh ra `content_hash` mới) nhưng giữ nguyên URL, lệnh sync từ JSON cũ không được phép gán `approved` cho nội dung mới chưa kiểm định.
3. **Immutability of Published Documents:** Tài liệu đã được đánh dấu `is_published = true` trong DB không được phép bị đè trạng thái duyệt bởi file JSON.
4. **Quality Gate Bypass Prevention:** Khi gửi yêu cầu `POST /admin/crawler/documents/{id}/approve` cho tài liệu rỗng hoặc chỉ có marker trang, backend phải từ chối với mã lỗi `400 Bad Request` và lý do rõ ràng.
5. **Test DB State Isolation:** Chạy lặp lại 3 file test DB nhiều lần liên tiếp không làm tăng số dòng dữ liệu rác hoặc gây side-effect sang các test suite khác.

---

## Issue and Commit Map

| Bước | Priority | Issue Title | Planned Commit | Tệp trọng tâm |
|:---:|:---:|---|---|---|
| **1** | P1 | Issue #133: Gỡ bỏ heuristic tự cấp duyệt trong seed tool và reset 67 review mồ côi | `fix(crawler): remove auto-approval heuristics and reset orphan reviews (closes #133)` | `tools/seed_real_crawled_documents.py`, `data/hus/document_reviews.json` |
| **1** | P1 | Issue #134: Ràng buộc content_hash và is_published khi đồng bộ review từ Git vào DB | `fix(crawler): enforce content hash match and protect published documents on sync (closes #134)` | `app/crawler/document_review_service.py`, `tests/services/test_document_review_git_sync.py` |
| **1** | P1 | Issue #135: Tách ghi đĩa ra khỏi DB transaction và xây dựng cơ chế export an toàn hậu commit | `fix(admin): make db ssot and export git reviews post-commit with atomic write (closes #135)` | `app/crawler/document_review_service.py`, `app/api/admin.py`, `tests/services/test_document_review.py` |
| **2** | P2 | Issue #136: Thiết lập Content Quality Gate chặn duyệt tài liệu rỗng và chuyển marker về pending_ocr | `feat(crawler): add content quality gate and mark marker-only documents pending_ocr (closes #136)` | `app/crawler/document_review_service.py`, `app/api/admin.py`, `data/hus/document_reviews.json` |
| **2** | P2 | Issue #137: Chuẩn hóa taxonomy phân loại lại 18 tài liệu đa ngành về nhãn major general | `fix(crawler): reclassify 18 multi-discipline documents to general major (closes #137)` | `data/hus/processed/documents/mathematics/`, `database/` |
| **3** | P2 | Issue #138: Tách biệt rõ ràng CLI sync và Startup sync có feature flag an toàn trong lifespan | `feat(crawler): clarify sync lifecycle and guard startup sync with feature flag (closes #138)` | `app/main.py`, `app/config.py`, `app/crawler/document_review_service.py` |
| **3** | P2 | Issue #139: Áp dụng Fixture Transaction Rollback cô lập DB cho 3 file test DB | `test(crawler): isolate database test state using rollback fixtures (closes #139)` | `tests/api/test_admin_document_review.py`, `tests/services/test_document_review.py`, `tests/services/test_document_review_git_sync.py` |
| **E2E** | P1 | Issue #140: Kiểm thử E2E giao diện Admin Document Review bằng Playwright và chụp ảnh minh chứng | `test(frontend): add e2e browser verification and capture proof screenshots (closes #140)` | `tests/frontend/check_admin_documents.py`, `tests/frontend/test_admin_document_review_e2e.py` |

---

## Tasks

---

### Task 1: Gỡ bỏ heuristic tự cấp duyệt trong seed tool và reset 67 review mồ côi (Lỗi P1.1)

**Issue:** Khắc phục lỗi P1.1: Tool seed tự cấp trạng thái "approved" dựa trên tên file và 67 review thiếu reviewer trong Git JSON.

**Files:**
- Modify: `tools/seed_real_crawled_documents.py:68-100`
- Modify: `data/hus/document_reviews.json`
- Test: `tests/services/test_document_seed_heuristics.py`

**Interfaces:**
- Consumes: `create_initial_git_reviews_if_empty(docs_dir, reviews_file)`
- Produces: Trạng thái seed mặc định là `pending` cho toàn bộ tài liệu mới; 67 bản ghi thiếu reviewer được đưa về `pending` với ghi chú rõ ràng; chỉ giữ lại review có bằng chứng reviewer thực tế.

- [ ] **Step 1: Write the failing test**
  Tạo `tests/services/test_document_seed_heuristics.py` kiểm tra:
  - `create_initial_git_reviews_if_empty` không bao giờ tự ý gán `review_status = "approved"` khi `reviewer_id` là `None`.
  - Tất cả tài liệu được seed mới mặc định có trạng thái `pending` (hoặc `rejected` nếu trùng nội dung đã kiểm chứng).
  - Đọc `data/hus/document_reviews.json` và xác nhận 100% bản ghi có `status == "approved"` phải có `reviewer_id` khác `None` và `reviewed_at` hợp lệ.

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest.exe tests/services/test_document_seed_heuristics.py -v --basetemp=F:\tmp\pt`
  Expected: FAIL vì `document_reviews.json` hiện có 67 bản ghi `reviewer_id: null` và `seed_real_crawled_documents.py` có khối logic tự cấp `approved`.

- [ ] **Step 3: Implement the fix**
  - Trong `tools/seed_real_crawled_documents.py`:
    - Xóa bỏ hoàn toàn khối `is_curriculum_or_core` tự cấp `approved`.
    - Tất cả tài liệu không bị trùng nội dung được khởi tạo ở trạng thái `pending`.
  - Trong `data/hus/document_reviews.json`:
    - Quét 70 bản ghi hiện tại: 67 bản ghi có `reviewer_id: null` chuyển `review_status: "pending"`, `review_reason: "Chờ kiểm định thực tế bởi quản trị viên"`, `reviewed_at: null`.
    - Chỉ giữ lại các bản ghi do tài khoản admin thật duyệt.

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest.exe tests/services/test_document_seed_heuristics.py -v --basetemp=F:\tmp\pt`
  Expected: PASS (0 orphan approved reviews).

- [ ] **Step 5: Subagent Review & Commit**
  - Dispatch reviewer subagent kiểm tra logic.
  - Commit: `git add tools/seed_real_crawled_documents.py data/hus/document_reviews.json tests/services/test_document_seed_heuristics.py`
  - `git commit -m "fix(crawler): remove auto-approval heuristics and reset orphan reviews (closes #1)"`

---

### Task 2: Ràng buộc content_hash và is_published khi đồng bộ review từ Git vào DB (Lỗi P1.2)

**Issue:** Khắc phục lỗi P1.2: Quyết định cũ có thể áp nhầm phiên bản do câu lệnh sync dùng `id OR url` bỏ qua `content_hash` và `is_published`.

**Files:**
- Modify: `app/crawler/document_review_service.py:465-500`
- Modify: `tests/services/test_document_review_git_sync.py:75-127`

**Interfaces:**
- Consumes: `sync_crawled_documents_and_reviews(conn, reviews_file)`
- Produces: `UPDATE` chỉ áp dụng khi `(id = :id OR url = :url) AND content_hash = :content_hash AND is_published = false`. Nếu hash khác nhau, ghi log cảnh báo và giữ nguyên `pending`.

- [ ] **Step 1: Write the failing test**
  Bổ sung vào `tests/services/test_document_review_git_sync.py`:
  - `test_sync_does_not_apply_approved_status_if_content_hash_mismatched()`: Tạo doc trong DB với `url="https://hus.vnu.edu.vn/doc-v2"`, `content_hash="hash_v2"`. Trong JSON có review `approved` cho `url="https://hus.vnu.edu.vn/doc-v2"` nhưng `content_hash="hash_v1"`. Chạy sync, assert doc trong DB vẫn giữ `review_status == "pending"`.
  - `test_sync_does_not_overwrite_published_document()`: Tạo doc trong DB có `is_published = true`, `review_status = "approved"`. Trong JSON có status `"rejected"`. Chạy sync, assert doc trong DB vẫn giữ `review_status == "approved"` và `is_published == true`.

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest.exe tests/services/test_document_review_git_sync.py -k "mismatched or published" -v --basetemp=F:\tmp\pt`
  Expected: FAIL vì hiện tại SQL `UPDATE` áp đè bất chấp `content_hash` và `is_published`.

- [ ] **Step 3: Implement the fix in `app/crawler/document_review_service.py`**
  - Cập nhật câu lệnh SQL trong `sync_crawled_documents_and_reviews`:
    ```sql
    UPDATE crawled_documents
    SET review_status = :status,
        review_reason = :reason,
        reviewer_id = :reviewer_id,
        reviewed_at = CASE
            WHEN :reviewed_at IS NOT NULL AND :reviewed_at != '' THEN CAST(:reviewed_at AS timestamptz)
            ELSE now()
        END
    WHERE (id = :id OR url = :url)
      AND content_hash = :content_hash
      AND is_published = false
    ```
  - Bổ sung đếm số lượng tài liệu bị bỏ qua do lệch hash (`hash_mismatches`) và tài liệu được bảo vệ do đã publish (`protected_published`).

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest.exe tests/services/test_document_review_git_sync.py -v --basetemp=F:\tmp\pt`
  Expected: All tests PASS.

- [ ] **Step 5: Subagent Review & Commit**
  - Dispatch reviewer subagent kiểm tra logic an toàn phiên bản.
  - Commit: `git add app/crawler/document_review_service.py tests/services/test_document_review_git_sync.py`
  - `git commit -m "fix(crawler): enforce content hash match and protect published documents on sync (closes #2)"`

---

### Task 3: Tách ghi đĩa ra khỏi DB transaction và xây dựng cơ chế export an toàn hậu commit (Lỗi P1.3)

**Issue:** Khắc phục lỗi P1.3: DB và JSON mâu thuẫn do dual-write đĩa trước khi commit transaction DB.

**Files:**
- Modify: `app/crawler/document_review_service.py:360-394, 430-465`
- Modify: `app/api/admin.py:847-890`
- Test: `tests/services/test_document_review_dual_write_atomicity.py`

**Interfaces:**
- Consumes: `review_document(conn, doc_id, decision, reason, reviewer_id)` - Pure DB function, không ghi đĩa.
- Produces: `export_git_reviews_from_db(conn, file_path)` - Đọc dữ liệu đã commit từ DB và ghi an toàn ra JSON đĩa bằng atomic write (`.tmp` -> `replace`) và cơ chế retry khi gặp lỗi I/O.
- Endpoint admin gọi export SAU KHI khối `with engine().begin()` commit thành công.

- [ ] **Step 1: Write the failing test**
  Tạo `tests/services/test_document_review_dual_write_atomicity.py`:
  - `test_rollback_in_db_does_not_mutate_json_file()`: Gọi API hoặc service trong transaction bị raise Exception trước khi commit. Kiểm tra file `document_reviews.json` không bị thay đổi.
  - `test_atomic_export_recovers_from_transient_write_error()`: Kiểm tra `export_git_reviews_from_db` có atomic replace và cơ chế retry khi ghi đĩa.

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest.exe tests/services/test_document_review_dual_write_atomicity.py -v --basetemp=F:\tmp\pt`
  Expected: FAIL vì `review_document` gọi `save_git_review` ngay trong transaction.

- [ ] **Step 3: Implement the fix**
  - Trong `app/crawler/document_review_service.py`:
    - Gỡ bỏ lệnh gọi `save_git_review` bên trong `review_document()`. Hàm `review_document` trở thành hàm thuần túy tương tác DB.
    - Xây dựng hàm `export_git_reviews_from_db(engine_or_conn, file_path=DEFAULT_REVIEWS_FILE)`:
      - Đọc tất cả các bản ghi có `review_status IN ('approved', 'rejected')` từ bảng `crawled_documents`.
      - Ghi ra file `.tmp` trước, sau đó dùng `os.replace` để atomic ghi đè file JSON đích.
      - Bổ sung cơ chế retry tối đa 3 lần nếu có lock file trên Windows.
  - Trong `app/api/admin.py`:
    - Tại endpoint `approve_crawled_document` và `reject_crawled_document`:
      - Di chuyển việc xuất JSON ra ngoài khối `with engine().begin() as conn:`.
      - Chỉ khi transaction commit xong, mới gọi `export_git_reviews_from_db(engine())`.

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest.exe tests/services/test_document_review_dual_write_atomicity.py -v --basetemp=F:\tmp\pt`
  Expected: PASS.

- [ ] **Step 5: Subagent Review & Commit**
  - Dispatch reviewer subagent kiểm tra tính transaction safety.
  - Commit: `git add app/crawler/document_review_service.py app/api/admin.py tests/services/test_document_review_dual_write_atomicity.py`
  - `git commit -m "fix(admin): make db ssot and export git reviews post-commit with atomic write (closes #3)"`

---

### Task 4: Content Quality Gate chặn duyệt tài liệu rỗng và chuyển marker về pending_ocr (Hạn chế 2)

**Issue:** Khắc phục Hạn chế 2: 21/179 file chỉ chứa marker/comment trang, trong đó 1 file rỗng đang mang trạng thái `approved`.

**Files:**
- Modify: `app/crawler/document_review_service.py:120-150, 360-390`
- Modify: `app/api/admin.py:840-870`
- Modify: `data/hus/document_reviews.json`
- Test: `tests/services/test_document_quality_gate.py`

**Interfaces:**
- Consumes: `is_meaningful_content(markdown_text: str, min_chars: int = 50) -> bool`
- Produces: Chặn `review_document(..., decision="approved")` nếu `is_meaningful_content(...)` trả về `False`, raise `ValueError("Nội dung tài liệu rỗng hoặc chỉ chứa marker trang, không đủ điều kiện phê duyệt (cần OCR)")`.
- Trạng thái hợp lệ cho 21 file này là `pending_ocr`.

- [ ] **Step 1: Write the failing test**
  Tạo `tests/services/test_document_quality_gate.py`:
  - `test_cannot_approve_empty_or_marker_only_document()`: Thử duyệt tài liệu có nội dung `<!-- page 1 -->\n<!-- page 2 -->`. Mong đợi lỗi `ValueError` từ service hoặc `400 Bad Request` từ API.
  - `test_21_marker_files_marked_pending_ocr()`: Kiểm tra cả 21 file trong `document_reviews.json` có trạng thái `pending_ocr` (hoặc `pending` kèm ghi chú cần OCR), không có file nào là `approved`.

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest.exe tests/services/test_document_quality_gate.py -v --basetemp=F:\tmp\pt`
  Expected: FAIL vì file `doc_42f38f75db40` vẫn đang `approved` và service chưa có hàm `is_meaningful_content`.

- [ ] **Step 3: Implement Content Quality Gate**
  - Trong `app/crawler/document_review_service.py`:
    - Viết hàm `is_meaningful_content(content: str, min_length: int = 50) -> tuple[bool, str]`:
      - Loại bỏ comment HTML `<!--.*?-->` và khoảng trắng.
      - Nếu độ dài sau khi làm sạch < 50 ký tự: trả về `(False, "Tài liệu rỗng hoặc chỉ chứa marker trang...")`.
    - Trong `review_document`: Nếu `decision == "approved"`, kiểm tra `is_meaningful_content(doc["markdown_content"])`. Nếu không thỏa mãn, raise `ValueError`.
  - Trong `data/hus/document_reviews.json`:
    - Cập nhật 21 file marker-only về `review_status: "pending_ocr"`, `review_reason: "Tài liệu dạng scan chưa OCR, cần xử lý trích xuất văn bản trước khi kiểm định"`.
  - Trong frontend Admin Document Review modal: Hiển thị badge màu cam `Chờ xử lý OCR` nếu tài liệu rỗng text.

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest.exe tests/services/test_document_quality_gate.py -v --basetemp=F:\tmp\pt`
  Expected: PASS.

- [ ] **Step 5: Subagent Review & Commit**
  - Dispatch reviewer subagent kiểm tra quality gate.
  - Commit: `git add app/crawler/document_review_service.py app/api/admin.py data/hus/document_reviews.json tests/services/test_document_quality_gate.py`
  - `git commit -m "feat(crawler): add content quality gate and mark marker-only documents pending_ocr (closes #4)"`

---

### Task 5: Chuẩn hóa taxonomy phân loại lại 18 tài liệu đa ngành về nhãn major general (Hạn chế 3)

**Issue:** Khắc phục Hạn chế 3: 18 tài liệu tuyển sinh Hóa Dược, Địa chất, Sinh học, Vật lý... trong thư mục `mathematics/` bị dán nhãn sai `major: "mathematics"`.

**Files:**
- Modify: 18 file `.md` trong `data/hus/processed/documents/mathematics/` (cập nhật frontmatter `major: general`)
- Modify: `tools/seed_real_crawled_documents.py` (cập nhật taxonomy heuristic tránh gán nhầm ngành)
- Test: `tests/services/test_document_taxonomy.py`

**Interfaces:**
- Consumes: Frontmatter metadata `major` trong các file markdown.
- Produces: Chỉ các tài liệu thuộc Toán học, Toán tin, KHDL, Cơ học mới mang `major: "mathematics"` hoặc tương ứng. Các tài liệu khoa học tự nhiên khác thuộc Hóa, Sinh, Địa chất, Vật lý mang `major: "general"`.

- [ ] **Step 1: Write the failing test**
  Tạo `tests/services/test_document_taxonomy.py`:
  - Quét toàn bộ file trong `data/hus/processed/documents/`:
  - Xác nhận các tài liệu có từ khóa Hóa dược, Địa chất, Sinh học, Vật lí, Môi trường, Hải dương, Khí tượng không được mang nhãn `major: "mathematics"`.

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest.exe tests/services/test_document_taxonomy.py -v --basetemp=F:\tmp\pt`
  Expected: FAIL (18 file vi phạm).

- [ ] **Step 3: Implement taxonomy corrections**
  - Cập nhật frontmatter `major: general` cho 18 file markdown đã xác định trong `data/hus/processed/documents/mathematics/`.
  - Trong `tools/seed_real_crawled_documents.py`: Bổ sung danh sách từ khóa ngoại lệ khi parse folder `mathematics/` để tự động gán `general`.

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest.exe tests/services/test_document_taxonomy.py -v --basetemp=F:\tmp\pt`
  Expected: PASS.

- [ ] **Step 5: Subagent Review & Commit**
  - Dispatch reviewer subagent kiểm tra taxonomy diff.
  - Commit: `git add data/hus/processed/documents/mathematics/ tools/seed_real_crawled_documents.py tests/services/test_document_taxonomy.py`
  - `git commit -m "fix(crawler): reclassify 18 multi-discipline documents to general major (closes #5)"`

---

### Task 6: Tách biệt rõ ràng CLI sync và Startup sync có feature flag an toàn trong lifespan (Hạn chế 1)

**Issue:** Khắc phục Hạn chế 1: Tên "auto-sync on startup" chưa đúng hành vi; app startup chưa gọi hàm sync.

**Files:**
- Modify: `app/crawler/document_review_service.py` (docstrings and lifecycle helpers)
- Modify: `app/config.py` (thêm setting `auto_sync_document_reviews: bool = False`)
- Modify: `app/main.py` (lifespan startup logic)
- Test: `tests/services/test_sync_lifecycle.py`

**Interfaces:**
- Consumes: `Settings.auto_sync_document_reviews`
- Produces: Khi flag bật (`True`), lifespan của FastAPI gọi `sync_crawled_documents_and_reviews` khi khởi động ứng dụng một cách an toàn và ghi log; khi flag tắt (`False`, mặc định trong test), bỏ qua để tránh side-effect.

- [ ] **Step 1: Write the failing test**
  Tạo `tests/services/test_sync_lifecycle.py`:
  - `test_startup_sync_disabled_by_default()`: Chạy test client với app mặc định, xác nhận startup không tự ý sync DB nếu cờ tắt.
  - `test_startup_sync_executes_when_flag_enabled()`: Bật flag qua monkeypatch và xác nhận sync được kích hoạt trong lifespan.

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv\Scripts\pytest.exe tests/services/test_sync_lifecycle.py -v --basetemp=F:\tmp\pt`
  Expected: FAIL vì `app/main.py` chưa có logic sync trong lifespan.

- [ ] **Step 3: Implement the lifecycle integration**
  - Thêm `auto_sync_document_reviews: bool = False` vào `app/config.py`.
  - Trong `app/main.py`: Trong context manager `@asynccontextmanager async def lifespan(app: FastAPI)`:
    - Nếu `settings.auto_sync_document_reviews` bật, thực hiện sync và ghi log có cấu trúc.
  - Cập nhật docstring trong `app/crawler/document_review_service.py` để phản ánh chính xác hành vi: "Synchronize review state between Git JSON snapshot and database (usable via CLI tool or guarded startup lifespan)".

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv\Scripts\pytest.exe tests/services/test_sync_lifecycle.py -v --basetemp=F:\tmp\pt`
  Expected: PASS.

- [ ] **Step 5: Subagent Review & Commit**
  - Dispatch reviewer subagent kiểm tra lifespan code.
  - Commit: `git add app/config.py app/main.py app/crawler/document_review_service.py tests/services/test_sync_lifecycle.py`
  - `git commit -m "feat(crawler): clarify sync lifecycle and guard startup sync with feature flag (closes #6)"`

---

### Task 7: Áp dụng Fixture Transaction Rollback cô lập DB cho 3 file test DB (Hạn chế 4)

**Issue:** Khắc phục Hạn chế 4: Ba file test DB mới chưa được fixture rollback chung bao phủ, để lại thay đổi trong DB test.

**Files:**
- Modify: `tests/api/test_admin_document_review.py`
- Modify: `tests/services/test_document_review.py`
- Modify: `tests/services/test_document_review_git_sync.py`
- Modify: `tests/support/admin_database.py` (bổ sung fixture `isolated_db_conn`)

**Interfaces:**
- Consumes: `isolated_db_conn` fixture: mở một connection, bắt đầu một transaction (`conn.begin()`), inject vào test, và tự động gọi `trans.rollback()` khi test kết thúc.
- Produces: 100% dữ liệu tạo ra trong test bị hủy bỏ (rolled back), DB test luôn sạch và giữ trạng thái ban đầu.

- [ ] **Step 1: Write verification test for DB pollution**
  Viết test kiểm tra xem trước và sau khi chạy test, tổng số bản ghi trong bảng `crawled_documents` có bị thay đổi không.

- [ ] **Step 2: Run current tests to verify side effects**
  Chạy lần lượt 3 test file và ghi nhận các row rác như `doc_test_review`, `doc_dual_write_test` bị lưu lại trong DB.

- [ ] **Step 3: Implement isolated rollback fixtures**
  - Trong `tests/support/admin_database.py`:
    - Tạo pytest fixture `isolated_db_conn`:
      ```python
      @pytest.fixture
      def isolated_db_conn():
          eng = admin_test_engine()
          with eng.connect() as conn:
              trans = conn.begin()
              try:
                  yield conn
              finally:
                  trans.rollback()
      ```
  - Cập nhật cả 3 file:
    - `tests/api/test_admin_document_review.py`: Sử dụng fixture dọn dẹp các tài liệu test tạo ra sau mỗi test case.
    - `tests/services/test_document_review.py`: Thay `with db_engine.begin() as conn:` bằng `isolated_db_conn`.
    - `tests/services/test_document_review_git_sync.py`: Sử dụng `isolated_db_conn` và `tmp_path` cô lập.

- [ ] **Step 4: Run test to verify it passes without leaving dirty state**
  Run: `.venv\Scripts\pytest.exe tests/api/test_admin_document_review.py tests/services/test_document_review.py tests/services/test_document_review_git_sync.py -v --basetemp=F:\tmp\pt`
  Expected: PASS và DB test không còn rò rỉ dữ liệu.

- [ ] **Step 5: Subagent Review & Commit**
  - Dispatch reviewer subagent kiểm tra fixture isolation.
  - Commit: `git add tests/support/admin_database.py tests/api/test_admin_document_review.py tests/services/test_document_review.py tests/services/test_document_review_git_sync.py`
  - `git commit -m "test(crawler): isolate database test state using rollback fixtures (closes #7)"`

---

### Task 8: Kiểm thử E2E giao diện Admin Document Review bằng Playwright và chụp ảnh minh chứng

**Issue:** Kiểm chứng trực quan toàn diện trên UI: Donut chart phản ánh đúng trạng thái sau khi reset orphan reviews; Hàng đợi 179 tài liệu; Modal xem chi tiết có Quality Gate warning; Phê duyệt tài liệu hợp lệ thành công.

**Files:**
- Create: `tools/capture_document_review_remediation_proof.py`
- Modify: `tests/frontend/check_admin_documents.py`

**Interfaces:**
- Consumes: Playwright browser, Uvicorn server `http://127.0.0.1:8000`, API admin `/admin/crawler/documents`.
- Produces:
  1. Ảnh chụp Dashboard Overview: Donut chart thống kê tài liệu phản ánh đúng số lượng `pending` (sau khi gỡ bỏ heuristic tự duyệt), `pending_ocr` (21 file), và `approved` thực tế.
  2. Ảnh chụp Document Review Queue: Danh sách 179 tài liệu với badge phân loại chuẩn (không còn nhãn `mathematics` cho tài liệu Hóa/Địa chất).
  3. Ảnh chụp Modal Quality Gate: Thử duyệt tài liệu rỗng -> Hiển thị cảnh báo lỗi rõ ràng "Nội dung tài liệu rỗng hoặc chỉ chứa marker trang, không đủ điều kiện phê duyệt".
  4. Ảnh chụp Phê duyệt thành công: Duyệt tài liệu hợp lệ có nội dung đầy đủ -> Ghi nhận thành công, cập nhật ngay lập tức trên UI và DB.

- [ ] **Step 1: Write Playwright automation script**
  Viết script `tools/capture_document_review_remediation_proof.py` điều khiển Playwright Chromium:
  - Đăng nhập quyền Admin.
  - Truy cập `/admin/overview`, chụp `admin_overview_document_reviews_remediated.png`.
  - Chuyển sang tab "Kiểm duyệt tài liệu" (`/admin/documents` hoặc tab crawler): Chụp `admin_document_queue_remediated.png`.
  - Mở modal tài liệu rỗng (`doc_42f38f75db40`): Kiểm tra cảnh báo Quality Gate, chụp `admin_document_quality_gate_modal.png`.
  - Mở một tài liệu hợp lệ (ví dụ CTĐT KHDL hoặc Toán tin đầy đủ): Nhập lý do duyệt và bấm "Phê duyệt": Chụp `admin_document_approved_success.png`.

- [ ] **Step 2: Run script and capture screenshots**
  Run: `.venv\Scripts\python.exe tools/capture_document_review_remediation_proof.py`
  Expected: Tạo thành công 4 file ảnh minh chứng sắc nét trong `screenshots/`.

- [ ] **Step 3: Verify all test suites pass**
  Run full test suite:
  - Pytest offline: `.venv\Scripts\pytest.exe tests/ -m "not hus_postgres" --basetemp=F:\tmp\pt`
  - Pytest DB: `.venv\Scripts\pytest.exe tests/api/test_admin_document_review.py tests/services/test_document_review.py tests/services/test_document_review_git_sync.py tests/services/test_document_seed_heuristics.py tests/services/test_document_quality_gate.py tests/services/test_document_taxonomy.py tests/services/test_sync_lifecycle.py -v --basetemp=F:\tmp\pt`
  - Ruff check: `.venv\Scripts\ruff.exe check .`

- [ ] **Step 4: Subagent Review & Final Commit**
  - Reviewer agent xác thực toàn bộ ảnh chụp và log test.
  - Commit: `git add tools/capture_document_review_remediation_proof.py tests/frontend/check_admin_documents.py`
  - `git commit -m "test(frontend): add e2e browser verification and capture proof screenshots (closes #8)"`

---

## Plan Self-Review Checklist

1. **Spec Coverage:**
   - [x] Lỗi P1.1 (Auto-approval heuristic & 67 orphan reviews) -> Task 1.
   - [x] Lỗi P1.2 (Version mismatch & published doc protection) -> Task 2.
   - [x] Lỗi P1.3 (Dual-write DB/JSON inconsistency) -> Task 3.
   - [x] Hạn chế 2 (21 marker files & approved empty file) -> Task 4.
   - [x] Hạn chế 3 (18 misplaced non-math documents) -> Task 5.
   - [x] Hạn chế 1 (Auto-sync startup discrepancy) -> Task 6.
   - [x] Hạn chế 4 (Test DB rollback isolation) -> Task 7.
   - [x] Bằng chứng chụp ảnh UI, Clean commits, Clean issues -> Task 8.
2. **Step Granularity:** Mỗi task gồm 5 bước cụ thể theo chu trình TDD (Test fail -> Verify fail -> Implement minimal -> Test pass -> Commit).
3. **Data Integrity:** Toàn bộ tham số (21 file marker, 18 file đa ngành, 67 bản ghi orphan, ngưỡng 50 ký tự) lấy trực tiếp từ dữ liệu thực tế đã kiểm chứng trong repository.
4. **Subagent Delegation:** Quy định sử dụng Subagent Implementer và Reviewer độc lập cho từng task.
