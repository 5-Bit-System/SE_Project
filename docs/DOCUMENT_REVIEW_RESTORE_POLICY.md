# Khôi phục review và sửa phân loại tài liệu cũ

Chính sách sau review PR #141 ngày 09/11/2026, nền `72d291e`.

## Quyết định trong DB là nguồn chính

Export JSON vẫn diễn ra sau khi API đã commit quyết định review. Nếu export thất
bại, quyết định trong DB vẫn có hiệu lực. Sync không được dùng JSON cũ để đảo
quyết định đó.

Sync chỉ khôi phục một quyết định vào bản nháp **chưa có dấu vết review**:

- Trạng thái pending, chưa published, reviewer và thời điểm đều null, lý do rỗng.
- Khớp đúng document ID, URL và hash nội dung; không tìm phiên bản thay thế bằng URL.
- Có `review_fingerprint` khớp ID, URL, hash, title, major, doc_type và metadata JSON.
- Có reviewer tồn tại, lý do ít nhất ba ký tự và thời điểm ISO có múi giờ.
- Approval còn phải vượt qua kiểm tra nội dung hiện hữu.

Snapshot pending không phải quyết định và không thu hồi review trong DB. Sync
không tự tạo thời điểm duyệt. Các thao tác review/metadata/sync dùng chung khóa
publication của HUS; điều kiện UPDATE tiếp tục kiểm pending chưa có review.

Hash fingerprint nhận diện phiên bản trong snapshot được tin cậy. Nó không phải
chữ ký và không chứng minh một người thực sự đã duyệt. Người quản trị vẫn phải
kiểm tra nguồn gốc snapshot trước khi khôi phục.

Export luôn dựng lại snapshot từ DB và ghi file tạm rồi atomic replace. Khóa
threading bảo vệ exporter trong cùng process; cấu hình một worker của dự án vẫn
áp dụng. Không cam kết serialization giữa nhiều process.

## Tương thích snapshot cũ

`data/hus/document_reviews.json` cũ không có fingerprint. Các quyết định trong
file đó sẽ không tự cấp approval/rejection cho DB mới. Đây là thay đổi có chủ ý:
không thể suy ra metadata nào đã được duyệt chỉ từ URL và hash nội dung.

Không tự bổ sung fingerprint dựa trên file hiện tại rồi coi đó là bằng chứng
review lịch sử. Với DB có quyết định đáng tin cậy, export lại từ DB bằng công cụ
hiện hữu trong quy trình vận hành được cho phép; nếu thiếu bằng chứng, review lại.
Không chạy seed/sync hoặc export vào dữ liệu thật chỉ để cập nhật định dạng file.

Initializer giữ nguyên mọi JSON mapping không rỗng, kể cả file chỉ có 1, 3 hoặc
29 mục. Chỉ file chưa tồn tại hoặc object `{}` mới được khởi tạo. File sai cú
pháp/cấu trúc báo lỗi, không tự bị ghi đè. CLI seed không tạo fixture XSS và không
log URL chứa thông tin đăng nhập.

Sync thông thường không dọn fixture bằng các mẫu URL. Tài liệu có URL trông
giống tên dữ liệu thử vẫn phải được giữ nguyên. Nhánh cleanup lịch sử tường minh
cũng không được xóa bản approved/published hoặc có reviewer/thời điểm review.

Các chỉ số sync gồm `version_mismatches`, `skipped_existing_decisions`,
`invalid_review_evidence`, `skipped_marker_only`, `skipped_unverified_approvals`,
`hash_mismatches` và `protected_published`. Có bản ghi bị bỏ qua không đồng nghĩa
toàn bộ review đã được khôi phục thành công; phải xem các chỉ số này khi vận hành.

## Sửa phân loại tài liệu đã nhập trước đây

Seed không sửa metadata của URL đã tồn tại. Dùng công cụ riêng để xem trước và
áp dụng thay đổi đã kiểm tra:

```powershell
python -m tools.plan_document_taxonomy_remediation `
  --inventory-json inventory.json --output taxonomy-plan.json
```

Inventory là mảng các object có ID, URL, content_hash, title, major, doc_type,
metadata_json, review_status và is_published. Công cụ có thể đọc inventory từ DB
bằng biến môi trường được chỉ định tường minh; mặc định giao dịch read-only:

```powershell
python -m tools.plan_document_taxonomy_remediation `
  --database-url-env HUS_REMEDIATION_DATABASE_URL --output taxonomy-plan.json
```

Công cụ không đọc `.env` hoặc tự chọn DB ứng dụng. URL phải là PostgreSQL. File
kế hoạch chứa hash nguồn, fingerprint inventory, danh sách thay đổi/xung đột và
`plan_sha256`. Kiểm tra kế hoạch trước khi áp dụng; dùng đường dẫn output mới,
ngoài thư mục tài liệu nguồn.

Chế độ áp dụng phải chỉ rõ tất cả thông tin sau:

```powershell
python -m tools.plan_document_taxonomy_remediation `
  --database-url-env HUS_REMEDIATION_DATABASE_URL `
  --apply taxonomy-plan.json --expected-plan-sha256 SHA256_TRONG_KE_HOACH `
  --actor-id UUID_ADMIN_DA_XAC_THUC --reason "Reviewed taxonomy correction" `
  --output taxonomy-result.json
```

Đây là mẫu lệnh, không phải thao tác đã chạy. Biến DB và actor phải do người vận
hành chọn cho môi trường đích, sau khi sao lưu theo quy trình hiện hữu.

Apply kiểm admin active/verified, khóa publication và inventory, dựng lại kế hoạch
và từ chối nếu DB/nguồn đã đổi hoặc có xung đột. Cập nhật và audit nằm trong cùng
giao dịch. Bản approved/published được giữ nguyên, tạo draft thay thế pending qua
`update_document_metadata()`; bản nháp chưa duyệt được sửa metadata. Không sửa
bytes source/corpus đã ghim và không tự duyệt bản thay thế.

Kế hoạch sau nhận diện replacement phù hợp đã tồn tại để tránh tạo trùng. Cần
review lại kế hoạch khi inventory hoặc nguồn thay đổi. Nếu xuất receipt lỗi sau
commit, phải kiểm tra kết quả DB và lập kế hoạch mới; không suy ra rollback từ
việc CLI báo lỗi ghi file.

## Kiểm tra

Test offline mới dùng SQLite tổng hợp để kiểm các điều kiện SQL và file thật để
kiểm initializer/export; khóa advisory được stub rõ ràng. Test PostgreSQL riêng
kiểm metadata replacement và lỗi export sau API commit qua hai kết nối. Không
dùng kết quả offline thay cho nghiệm thu khóa, schema và giao dịch PostgreSQL.

```powershell
python -m pytest -q tests/services/test_document_review_restore_policy.py `
  tests/services/test_document_seed_heuristics.py `
  tests/services/test_document_taxonomy_remediation_plan.py
python -m pytest -q tests/services/test_document_review_restore_postgres.py -m hus_postgres
```

Lệnh PostgreSQL cần `HUS_TEST_DATABASE_URL` cho DB test riêng, đã migrate theo
hướng dẫn HUS. Không dùng DB ứng dụng hoặc hồ sơ thật. Các sửa này không xác minh
độ đúng OCR, nội dung học thuật, catalog hay điều kiện học vụ của sinh viên.
