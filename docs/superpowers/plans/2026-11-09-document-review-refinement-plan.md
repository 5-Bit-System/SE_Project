# Kế hoạch Hoàn thiện Cơ chế Kiểm duyệt Tài liệu (Tasks A, B, C, D)
# Document Review Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Mục tiêu:** Khắc phục dứt điểm 4 kẽ hở kỹ thuật trọng tâm đã được chỉ ra tại Mục 9 và Mục 10 trong tài liệu `BAO_CAO_DOI_CHIEU_DOCUMENT_REVIEW_GUI_THANG_2026_11_09.md`:
1. **Task A (Mục 9.1 & 9.3 — Gác cổng Phê duyệt & Reviewer Audit Gate):** Chặn đứng triệt để việc phê duyệt mồ côi (thiếu reviewer) trong `review_document()` và chặn đường sync đi vòng qua điều kiện nội dung rỗng/marker và reviewer hợp lệ.
2. **Task B (Mục 9.2 & 9.4 — Xuất JSON thuần từ DB SSOT & Chống Race Condition):** Đưa DB thành nguồn chân lý duy nhất (SSOT), loại bỏ việc merge đè trên file cũ để tự động xóa các review bị thu hồi/pending; tuần tự hóa export bằng lock.
3. **Task C (Mục 10 — Bộ kiểm thử TDD mở rộng bao quát toàn diện):** Viết bộ kiểm thử bao quát toàn bộ các edge cases (sync từ chối marker, sync từ chối reviewer không tồn tại, export tự xóa review thu hồi, export đa luồng, file đĩa đổi hash).
4. **Task D (E2E Verification, Playwright Screenshots & Clean Commits):** Chạy kiểm thử Playwright trên giao diện Admin, chụp 4 ảnh minh chứng sắc nét, liên kết GitHub Issues, kiểm định qua Subagent Reviewer độc lập.

---

## Danh mục Files thay đổi & tạo mới

| File | Hành động | Trách nhiệm |
| :--- | :---: | :--- |
| `app/crawler/document_review_service.py` | Modify | Bắt buộc reviewer trong `review_document()`; bổ sung gate kiểm tra `is_meaningful_content()` và `valid_reviewer_id` trong `sync_crawled_documents_and_reviews()`; tái cấu trúc `_do_export_git_reviews()` xuất snapshot thuần từ DB; thêm `_export_lock`. |
| `tests/services/test_document_sync_gate.py` | Create | Test suites chuyên biệt kiểm tra việc sync từ chối approve file marker, từ chối reviewer không có trong DB, và nhận diện file đổi hash. |
| `tests/services/test_document_export_ssot.py` | Create | Test suites chuyên biệt kiểm tra export loại bỏ review thu hồi về pending, và kiểm tra concurrency lock khi export đồng thời. |
| `tests/services/test_document_quality_gate.py` | Modify | Bổ sung test kiểm tra `review_document()` bắt buộc phải có tài khoản reviewer thật trong DB, chặn gán null reviewer khi approve. |
| `tools/capture_document_review_remediation_proof.py` | Modify | Cập nhật kịch bản Playwright để chụp ảnh minh chứng: chặn approve file marker, approve hợp lệ với reviewer, và hiển thị trạng thái đồng bộ chính xác. |
| `docs/screenshots/remediation/` | Artifacts | 4 ảnh chụp minh chứng mới cho báo cáo nghiệm thu. |

---

## Chi tiết từng Task thực thi

---

### Task A: Gác cổng Phê duyệt & Reviewer Audit Gate (Mục 9.1 & 9.3)
**GitHub Issue:** Tạo Issue mới `fix(crawler): enforce valid reviewer in review service and close sync bypass for empty docs and unverified reviewers`

#### 1. Bối cảnh & Dữ liệu thực tế:
- Bảng `crawled_documents` có ràng buộc khóa ngoại `reviewer_id UUID REFERENCES accounts(id) ON DELETE SET NULL`.
- Lỗ hổng 1 (Mục 9.3): Trong `review_document()`, nếu `reviewer_id` không tồn tại trong bảng `accounts`, code hiện tại gán `valid_reviewer_id = None` rồi vẫn cho phép `review_status = 'approved'`. Điều này tạo ra trạng thái `approved` mồ côi (không ai chịu trách nhiệm).
- Lỗ hổng 2 (Mục 9.1): Trong `sync_crawled_documents_and_reviews()`, câu lệnh SQL UPDATE áp trực tiếp trạng thái `approved` từ file JSON mà không kiểm tra xem file trên đĩa có rỗng/chỉ chứa marker hay không (bỏ qua `is_meaningful_content`), và vẫn gán `approved` ngay cả khi `reviewer_id` bị thiếu/không có trong `accounts`.

#### 2. Các bước triển khai chi tiết:

- [ ] **Bước A1: Viết Failing Tests (TDD Red) cho Service & Sync Gate**
  - Tạo file `tests/services/test_document_sync_gate.py` với các ca kiểm thử:
    + `test_review_document_raises_if_reviewer_not_in_accounts`: Gọi `review_document(conn, doc_id, decision="approved", reason="Hợp lệ", reviewer_id="00000000-0000-0000-0000-000000000000")` → Phải raise `ValueError` với thông báo yêu cầu tài khoản reviewer hợp lệ.
    + `test_review_document_raises_if_reviewer_missing_on_approved`: Gọi `review_document(conn, doc_id, decision="approved", reason="Hợp lệ", reviewer_id=None)` → Phải raise `ValueError`.
    + `test_sync_rejects_approved_on_marker_only_document`: Seed tài liệu chỉ có marker `<!-- page 1 -->`, file JSON chỉ định `review_status: 'approved'`. Chạy sync → DB phải giữ nguyên `pending`, kết quả sync trả về `skipped_marker_only == 1`.
    + `test_sync_rejects_approved_when_reviewer_not_in_accounts`: Seed tài liệu có nội dung tốt, nhưng file JSON có `reviewer_id: "00000000-0000-0000-0000-000000000000"` (không có trong `accounts`). Chạy sync → DB phải giữ nguyên `pending`, kết quả sync trả về `skipped_unverified_approvals == 1`.
  - Chạy test để xác nhận FAIL:
    ```powershell
    $env:HUS_TEST_DATABASE_URL="postgresql+psycopg2://ai07:<TEST_DB_PASSWORD>@127.0.0.1:5433/ai07?sslmode=disable"
    .venv\Scripts\python.exe -m pytest tests/services/test_document_sync_gate.py -v
    ```

- [ ] **Bước A2: Triển khai kiểm tra Reviewer nghiêm ngặt trong `review_document()`**
  - Trong `app/crawler/document_review_service.py` tại hàm `review_document()`:
    ```python
    valid_reviewer_id = None
    safe_uid = _safe_uuid(reviewer_id)
    if safe_uid:
        try:
            exists = conn.execute(
                text("SELECT 1 FROM accounts WHERE id = :aid"),
                {"aid": safe_uid},
            ).scalar()
            if exists:
                valid_reviewer_id = safe_uid
        except Exception:
            valid_reviewer_id = safe_uid

    if decision == "approved":
        if not valid_reviewer_id:
            raise ValueError(
                "Phê duyệt tài liệu bắt buộc phải có tài khoản người duyệt (reviewer) hợp lệ trong hệ thống."
            )
    ```

- [ ] **Bước A3: Triển khai gác cổng kiểm tra trong `sync_crawled_documents_and_reviews()`**
  - Trong `app/crawler/document_review_service.py` tại hàm `sync_crawled_documents_and_reviews()`:
    1. Bổ sung 2 biến đếm: `skipped_marker_only = 0`, `skipped_unverified_approvals = 0`.
    2. Khi `status == "approved"`:
       - Kiểm tra reviewer:
         ```python
         if not valid_reviewer_id:
             logger.warning("Bỏ qua đồng bộ 'approved' cho doc %s: reviewer không hợp lệ hoặc không tồn tại trong accounts", doc_id)
             skipped_unverified_approvals += 1
             continue
         ```
       - Kiểm tra nội dung:
         ```python
         # Lấy nội dung hiện tại của tài liệu trong DB
         target_doc = conn.execute(
             text("SELECT markdown_content FROM crawled_documents WHERE (id = :id OR url = :url) AND content_hash = :content_hash"),
             {"id": doc_id, "url": url, "content_hash": content_hash},
         ).mappings().first()
         if target_doc:
             is_meaningful, _ = is_meaningful_content(target_doc["markdown_content"] or "")
             if not is_meaningful:
                 logger.warning("Bỏ qua đồng bộ 'approved' cho doc %s: nội dung rỗng hoặc chỉ có marker trang (cần OCR)", doc_id)
                 skipped_marker_only += 1
                 continue
         ```
    3. Thêm `skipped_marker_only` và `skipped_unverified_approvals` vào dict kết quả trả về.

- [ ] **Bước A4: Chạy lại Test & Xác nhận PASS (TDD Green)**
  - Chạy `pytest tests/services/test_document_sync_gate.py -v`.
  - Kiểm tra Ruff: `.venv\Scripts\ruff.exe check app/crawler/document_review_service.py tests/services/test_document_sync_gate.py`.
  - Tạo Git commit clean gắn với Issue.

---

### Task B: Chuẩn hóa Export SSOT & Serialization Lock (Mục 9.2 & 9.4)
**GitHub Issue:** Tạo Issue mới `fix(crawler): make db pure ssot for review export and serialize concurrent exporters`

#### 1. Bối cảnh & Dữ liệu thực tế:
- Lỗ hổng 1 (Mục 9.2): `_do_export_git_reviews()` gọi `load_git_reviews(path)` trước khi ghi đè các row DB. Nếu một tài liệu bị chuyển từ `approved` về `pending` hoặc bị xóa trong DB, nó không nằm trong câu SELECT `WHERE review_status IN ('approved', 'rejected')`, nên entry cũ vẫn bị giữ lại trong file JSON.
- Lỗ hổng 2 (Mục 9.4): Hai exporter chạy song song có thể gây race condition (lượt export sau đọc DB cũ hơn có thể ghi đè làm thụt lùi snapshot).

#### 2. Các bước triển khai chi tiết:

- [ ] **Bước B1: Viết Failing Tests (TDD Red) cho Pure SSOT Export & Concurrency Lock**
  - Tạo file `tests/services/test_document_export_ssot.py` với các ca kiểm thử:
    + `test_export_purges_revoked_or_pending_documents`:
      * Tạo file JSON mock có 2 entry `doc_1` (approved) và `doc_2` (approved).
      * Trong DB: `doc_1` vẫn approved, nhưng `doc_2` bị chuyển về `pending`.
      * Gọi `export_git_reviews_from_db()`.
      * Xác minh file JSON kết quả: chỉ còn `doc_1`, `doc_2` đã bị loại bỏ hoàn toàn khỏi file JSON.
    + `test_export_never_includes_unverified_approved_rows`:
      * Giả sử DB có 1 row mang `approved` nhưng `reviewer_id = NULL`.
      * Gọi export → file JSON không chứa row này.
    + `test_export_concurrent_serialization_lock`:
      * Dùng `concurrent.futures.ThreadPoolExecutor` gọi đồng thời 5 lượt export với các cập nhật giả lập.
      * Xác minh file JSON không bị lỗi định dạng JSON, không để lại file `.tmp` rác, và snapshot cuối cùng phản ánh đúng DB.
  - Chạy test xác nhận FAIL.

- [ ] **Bước B2: Tái cấu trúc `_do_export_git_reviews` để xuất snapshot thuần từ DB**
  - Trong `app/crawler/document_review_service.py`:
    Thay vì `reviews = load_git_reviews(path)`, chuyển thành:
    ```python
    reviews: dict[str, dict[str, Any]] = {}
    ```
    Query DB lấy toàn bộ tài liệu có trạng thái kiểm duyệt chính thức:
    ```sql
    SELECT id, url, content_hash, title, review_status, review_reason, reviewer_id, reviewed_at
    FROM crawled_documents
    WHERE (review_status = 'rejected' OR (review_status = 'approved' AND reviewer_id IS NOT NULL))
      AND url NOT LIKE 'javascript:%'
      AND id != 'doc_xss_test'
    ORDER BY id
    ```
    Xây dựng dict `reviews` từ chính các dòng này. Mọi tài liệu `pending`, file rỗng không đủ điều kiện, hoặc tài liệu đã bị xóa sẽ tự động không có trong file JSON.

- [ ] **Bước B3: Thêm Concurrency Serialization Lock**
  - Khai báo lock ở module-level:
    ```python
    import threading

    _EXPORT_LOCK = threading.Lock()
    ```
  - Bao bọc toàn bộ khối thực thi trong `export_git_reviews_from_db()` bằng `with _EXPORT_LOCK:`:
    ```python
    def export_git_reviews_from_db(
        engine_or_conn: Any,
        file_path: Path | None = None,
    ) -> int:
        with _EXPORT_LOCK:
            path = Path(file_path) if file_path is not None else DEFAULT_REVIEWS_FILE
            path.parent.mkdir(parents=True, exist_ok=True)
            if hasattr(engine_or_conn, "connect") and not hasattr(engine_or_conn, "execute"):
                with engine_or_conn.connect() as conn:
                    return _do_export_git_reviews(conn, path)
            else:
                return _do_export_git_reviews(engine_or_conn, path)
    ```

- [ ] **Bước B4: Chạy lại Test & Xác nhận PASS (TDD Green)**
  - Chạy `pytest tests/services/test_document_export_ssot.py -v`.
  - Kiểm tra Ruff và tạo Git commit clean gắn với Issue.

---

### Task C: Kiểm thử tích hợp toàn chuỗi Seed → Sync & Edge Cases (Mục 10)
**GitHub Issue:** Tạo Issue mới `test(crawler): add integrated seed-sync pipeline tests covering content hash divergence and database commit rollback`

#### 1. Bối cảnh & Dữ liệu thực tế:
- Mục 10 của Báo cáo yêu cầu: Kiểm tra toàn chuỗi seed → sync với tình huống file trên đĩa cùng URL nhưng nội dung đã đổi (hash divergence), đảm bảo bản published không bị chạm tới, và kiểm chứng rollback DB thật giữa 2 kết nối tách biệt.

#### 2. Các bước triển khai chi tiết:

- [ ] **Bước C1: Viết Test kiểm tra chuỗi Seed → Sync khi file đổi nội dung**
  - Trong `tests/services/test_document_sync_gate.py`:
    + Thêm test case `test_seed_sync_pipeline_when_file_content_hash_diverges`:
      1. Khởi tạo tài liệu trên đĩa với phiên bản A, seed vào DB, review thành `approved` với hash A.
      2. Sửa nội dung file trên đĩa thành phiên bản B (tạo ra hash B khác hash A).
      3. Chạy lại `sync_crawled_documents_and_reviews()`.
      4. Kiểm tra: Tài liệu trong DB không bị áp đè review của hash A; `hash_mismatches` tăng lên 1; tài liệu phiên bản B giữ trạng thái an toàn chờ duyệt lại.
    + Thêm test case `test_seed_sync_pipeline_protects_published_even_if_json_says_pending`:
      1. Tạo tài liệu đã xuất bản (`is_published = True`).
      2. File JSON chứa review cũ ghi `pending` hoặc `rejected`.
      3. Chạy sync → Trạng thái trong DB vẫn là published, không bị hạ cấp.

- [ ] **Bước C2: Viết Test kiểm chứng Rollback DB thật & Tính hiển thị độc lập**
  - Trong `tests/services/test_document_review_dual_write_atomicity.py`:
    + Thêm test case `test_real_db_rollback_leaves_no_residue_and_json_untouched`:
      1. Mở kết nối DB 1, thực hiện update trạng thái review trong transaction.
      2. Mở kết nối DB 2 song song, đọc DB → Kiểm tra isolation: kết nối 2 không nhìn thấy thay đổi uncommitted.
      3. Kết nối 1 gặp lỗi và rollback.
      4. Kiểm tra file JSON: Hoàn toàn không bị export hay thay đổi.
      5. Kết nối 2 đọc lại: Trạng thái DB trở về nguyên bản.

- [ ] **Bước C3: Chạy toàn bộ Test Suites của Document Review**
  - Chạy toàn bộ 12 test files liên quan đến Admin, Crawler và Corpus:
    ```powershell
    $env:HUS_TEST_DATABASE_URL="postgresql+psycopg2://ai07:<TEST_DB_PASSWORD>@127.0.0.1:5433/ai07?sslmode=disable"
    .venv\Scripts\python.exe -m pytest tests/services/test_document_seed_heuristics.py tests/services/test_document_quality_gate.py tests/services/test_document_taxonomy.py tests/services/test_document_review_dual_write_atomicity.py tests/services/test_sync_lifecycle.py tests/services/test_auto_sync_on_startup.py tests/services/test_document_review.py tests/services/test_document_review_git_sync.py tests/services/test_document_sync_gate.py tests/services/test_document_export_ssot.py tests/api/test_admin_document_review.py tests/hus/test_corpus.py -v --basetemp=F:\tmp\pt
    ```
  - Xác nhận 100% test cases đều PASSED (không có lỗi hay rò rỉ).
  - Commit clean gắn với Issue.

---

### Task D: Kiểm chứng Giao diện E2E, Chụp ảnh Minh chứng & Đẩy PR (Mục 10)
**GitHub Issue:** Tạo Issue mới `test(frontend): update e2e playwright verification, capture fresh remediation proofs and update PR`

#### 1. Bối cảnh & Dữ liệu thực tế:
- Mục 10 của Báo cáo yêu cầu: Phải có bằng chứng chụp ảnh màn hình giao diện thực tế với dữ liệu thật phản ánh đúng backend (tài liệu chờ OCR, chặn approve, duyệt thành công có người duyệt, thống kê đồng bộ).

#### 2. Các bước triển khai chi tiết:

- [ ] **Bước D1: Cập nhật kịch bản Playwright & Chụp ảnh minh chứng mới**
  - Cập nhật script `tools/capture_document_review_remediation_proof.py`:
    1. Ảnh 1: `admin_overview_document_reviews_remediated_v2.png` — Dashboard tổng quan hiển thị thống kê 179 tài liệu phân loại chuẩn, biểu đồ Donut chính xác.
    2. Ảnh 2: `admin_document_queue_remediated_v2.png` — Danh sách hàng đợi tài liệu, nhãn ngành rõ ràng (General cho các ngành đa môn).
    3. Ảnh 3: `admin_document_quality_gate_modal_v2.png` — Modal chi tiết tài liệu marker hiển thị cảnh báo `📷 Chờ xử lý OCR`, nút Duyệt bị vô hiệu hóa / chặn thông báo 400.
    4. Ảnh 4: `admin_document_approved_success_v2.png` — Phê duyệt thành công một tài liệu đạt chuẩn với tên/ID người duyệt được hiển thị rõ ràng trên UI.
  - Chạy script Playwright sinh ảnh vào thư mục `docs/screenshots/remediation/` và artifacts dir:
    ```powershell
    .venv\Scripts\python.exe tools/capture_document_review_remediation_proof.py
    ```

- [ ] **Bước D2: Kiểm tra Linting & Định dạng Mã nguồn**
  - Chạy Ruff trên toàn bộ codebase:
    ```powershell
    .venv\Scripts\ruff.exe check .
    ```

- [ ] **Bước D3: Tạo Subagent Senior Reviewer Độc lập kiểm tra toàn nhánh**
  - Sử dụng `invoke_subagent` để dispatch một reviewer agent độc lập kiểm tra toàn bộ diff giữa `origin/main` và nhánh làm việc, đảm bảo tuân thủ nguyên tắc:
    + Không làm bẩn cơ sở dữ liệu test.
    + Không vi phạm baseline corpus `hus-0404f37-20261026`.
    + Không để lọt orphan approval.
    + Không ghi đè file ngoài ý muốn.

- [ ] **Bước D4: Push Commits lên Remote & Cập nhật PR #141**
  - Đẩy các commit clean lên branch `feat/document-review-remediation-20261108`:
    ```powershell
    git push origin feat/document-review-remediation-20261108
    ```
  - Cập nhật nội dung PR #141 bằng `gh pr edit 141 --body-file ...`, liệt kê chi tiết các bổ sung theo Báo cáo đối chiếu ngày 09/11/2026.
  - Theo dõi CI trên GitHub Actions đến khi toàn bộ jobs xanh 10/10.
  - Lập báo cáo kết quả chi tiết kèm 4 ảnh minh chứng gửi bạn nghiệm thu.

---

## Tiêu chí Nghiệm thu Hoàn thành (Definition of Done)
1. **Không có bất kỳ Approved mồ côi nào:** Bắt buộc 100% tài liệu được duyệt phải có tài khoản reviewer tồn tại thực tế trong bảng `accounts`.
2. **Không thể đi vòng qua chất lượng nội dung:** Đường Sync không bao giờ tự động nâng một tài liệu rỗng hoặc chỉ có marker lên thành `approved`.
3. **DB là nguồn chân lý duy nhất (SSOT):** File JSON phản ánh chính xác các tài liệu được duyệt hợp lệ từ DB; việc thu hồi duyệt hoặc xóa doc trong DB sẽ tự động cập nhật ngay trên file JSON.
4. **Không có Race Condition:** Các lệnh export file JSON chạy tuần tự an toàn thông qua lock.
5. **100% CI Green:** Toàn bộ test suite địa phương và trên GitHub Actions CI đều đạt trạng thái XANH.
6. **Bằng chứng xác thực:** 4 ảnh chụp màn hình Playwright rõ ràng, minh chứng cho các trường hợp kiểm thử thành công.
