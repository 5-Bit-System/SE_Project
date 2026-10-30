# Đặc tả VT-101 (chốt trước production patch)

Nguyễn Công Việt · 23001953 · SE2026-T25 · Nhóm trưởng · BT cá nhân 3.
AI-07 – Explainable Course Recommender. Cơ sở: Lecture 06 và 07 theo yêu cầu
người dùng; chưa nhận slide/rubric gốc, không khẳng định đã đối chiếu chúng.

## Bài toán và contract có thật

`app/api/routes.py::courses` hiện phục vụ GET `/courses?program_id=...`, bắt buộc
program_id kiểu string; không có tìm kiếm/phân trang/sắp xếp. Response 200 là
`list[Course]` nguyên thứ tự catalog, có cả field mở rộng. Thiếu query: 422;
program không tồn tại: 404 JSON detail string; ValueError domain: 422 detail string;
storage mất kết nối: 503 detail string; dữ liệu server lỗi: 500 detail đã che nội dung.
`app/main.py::storage_unavailable_handler/storage_data_error_handler` làm ánh xạ lỗi.
`app/static/app.js::onProgramChange` (request ở dòng 229 tại baseline) gán JSON
trực tiếp vào `state.courses`, rồi dùng `.find/.filter`, code/name/credits/block,
name_en và metadata. File này **legacy**, không còn được index.html nạp;
client hoạt động hiện tại dùng workspace/course-status và `/me/...`. Vì thế
test legacy chứng minh consumer contract có thật, không tuyên bố UI legacy đang active.
`tests/catalogs/test_hus_metadata_enrichment.py::test_api_preserves_both_names_and_hours`
cũng phụ thuộc mảng và bảo toàn metadata. Endpoint catalog công khai, không đòi
VNU/session; BT3 không thêm auth hoặc mở rộng quyền đọc hồ sơ cá nhân.

Luồng thật: routes → `app/catalog.py::load_catalog` → JSON repository hoặc
`HusRepository.load_catalog` → Catalog/Course Pydantic → response serialization.
HUS đọc/validate một revision JSON nguyên vẹn trong REPEATABLE READ, không trả
query rowset học phần. Catalog kiểm tra mã duy nhất; legacy JSON cũng chống mã trùng.
Không cần migration. CI `.github/workflows/checks.yml` chạy Ruff, builders, offline
và hai nhóm PostgreSQL riêng; fixture `tests/conftest.py` chặn HTTP ra ngoài.

## Contract bổ sung

GET `/courses/search`, public, chỉ đọc một catalog:

| Query | Kiểu/default/validation | Ý nghĩa |
|---|---|---|
| program_id | string bắt buộc, như endpoint cũ | Alias được repository giải quyết; không tồn tại 404 |
| q | string, `""`, tối đa 120 ký tự | strip rồi Unicode casefold; substring literal trong code/name/name_en; dấu giữ nguyên |
| block | string hoặc absent | Khớp chính xác block có nguồn; chuỗi lạ/rỗng không khớp |
| requirement_type | required/elective/required_excluded/graduation hoặc absent | Khớp chính xác; enum sai 422 |
| sort | code/name/credits, default code | Chỉ tăng dần; name dùng casefold; code là tie-breaker tăng dần |
| page | integer ≥1, default 1 | Trang bắt đầu từ 1 |
| page_size | integer 1..100, default 20 | Giới hạn payload |

200 object chính xác các field `program_id: str` (canonical), `items: Course[]`,
`total: int` (sau filter, trước pagination), `page: int`, `page_size: int`.
Không có kết quả hoặc trang vượt cuối: 200, items=[], total vẫn đúng.
Không suy ra unknown metadata hay đổi cờ draft_unverified. Filter kết hợp AND;
q khớp OR trên ba trường. Pipeline: load một snapshot → filter → sort toàn tập
đã lọc → total → slice → serialize. Không tác động thứ tự/mutable state catalog gốc.
Lỗi giữ semantics endpoint cũ; unexpected exception là 500, không empty-success.

## Acceptance criteria

- **AC-01**: q literal không phân biệt hoa/thường và trim, kết hợp block và
  requirement_type theo AND; chỉ trả môn của program yêu cầu, không tự xác minh nguồn.
- **AC-02**: page/page_size defaults và bounds như bảng; total sau filter;
  ghép các trang trên dữ liệu cố định có đúng toàn bộ kết quả, không trùng/mất;
  empty/out-of-range 200 phân biệt với validation 422.
- **AC-03**: sort code/name/credits xác định, tie-breaker code; cùng query và
  dữ liệu không đổi cho cùng kết quả dù repository đổi thứ tự đầu vào.
- **AC-04**: request cũ GET /courses giữ mảng đầy đủ, thứ tự cũ, field/kiểu,
  metadata mở rộng, nullable name_en, status/error semantics; không bắt client đổi.
- **AC-05**: lỗi storage 503, dữ liệu lỗi 500, program lạ 404; không bị nuốt thành
  200 empty/default. Failure contract test phải giết mutant nuốt exception.

## Non-functional constraints và giới hạn

- **NFC-01**: 100 worker HTTP đồng thời, p95 ≤3.000 ms cho workload tổng hợp
  được công bố; warm-up riêng, mọi response kiểm correctness. Chỉ công bố đạt
  nếu không có lỗi/correctness violation. Benchmark không đại diện production DB.
- **NFC-02**: tương thích ngược, không dependency runtime mới/migration/DB write,
  không mạng/provider bên ngoài hoặc credentials thật. Evidence tái lập được.
- **NFC-03**: test deterministic, fixture cố định, không dựa thời gian/random/network.

Offset pagination chỉ bảo đảm khi dataset không đổi. Các request khác nhau có
thể đọc revision khác nhau; không có snapshot token/cursor, không hứa ổn định khi
catalog đang được publish. Sort Unicode codepoint/casefold không phải collation
tiếng Việt. Public catalog search không phải eligibility/recommendation và không
chứng nhận lịch mở lớp. UI mới, RAG, embedding, persistent index, DB tuning,
SSO và thay chính sách học vụ ngoài phạm vi. API slice được phép theo yêu cầu;
chưa có xác nhận cá nhân của sinh viên về lựa chọn thiết kế hoặc số liệu.
