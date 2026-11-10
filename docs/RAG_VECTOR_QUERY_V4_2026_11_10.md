# V4 — query vector có rào chắn và fallback BM25

Triển khai local ngày 09–10/11/2026 trên `hus-embedding-chromadb`.
HEAD hiện tại `1ad85e3` + WIP V4, chưa commit/push/deploy.
Thiết kế: [V4](superpowers/specs/2026-11-09-hus-vector-query-v4-design.md).
Các kết quả cuối được ghim trong [receipt](acceptance/hus_vector_query_v4_report.json).

## Lưu trữ và lựa chọn retrieval

Chroma V3 lưu bền vững 939 vector/935 parent và metadata scalar; không lưu
documents/quote/QA/gold/bảng điểm. Corpus, nội dung nguồn và citation vẫn do
snapshot canonical cung cấp. BM25 tính xếp hạng lexical trên snapshot trong
bộ nhớ, không phải nơi lưu vector.

`HUS_RETRIEVAL_MODE=lexical` vẫn mặc định. Chọn `vector` tường minh mới dùng
adapter V4; `hybrid` vẫn unavailable đến V5. F2 tiếp tục lookup cấu trúc và
không khởi tạo model/Chroma, kể cả khi service được cấu hình vector.
Manifest V3 vẫn `index_built_not_activated`, `activation_allowed=false`:
V4 không sửa artifact lịch sử hoặc tự bật chế độ vector/production.

## Luồng query

- Lấy tập canonical đủ quyền và kiểm snapshot không đổi. `where` truyền vào
  Chroma **trước top-k** gồm release ID/hash, family/major, review/opt-in,
  tập parent đủ quyền và version/variant/course/field khi được chỉ định.
  Mã môn trong câu hỏi cũng thu hẹp tập parent trước query.
- F1 giữ edition nguồn; không đổi version F2/F3 thành edition F1.
  F3 chỉ dùng generated/needs_review đã có opt-in. Không gọi vector khi
  scope rỗng hoặc F3 chưa được phép.
- Tokenize `query: ` + câu hỏi, gồm special tokens, bằng graph tokenizer
  V3 đã kiểm hash. Tối đa 512 token, không truncate. Inference local CPU
  float32, masked mean/L2 theo encoder V3; không download hoặc gọi provider.
- Verify toàn index lúc khởi tạo bằng ID ghim ngoài DB. Mỗi query kiểm lại
  manifest, logical inventory, collection identity/config và toàn inventory
  DB trước lấy top-k; phát hiện cả sửa vector/document sau startup.
- Kết quả phải có ID thuộc passage inventory, metadata/hash/kiểu JSON khớp,
  distance hữu hạn hợp lệ và không có document. Một hit sai làm bỏ toàn bộ
  vector result. Resolve và kiểm parent canonical; quote/locator/citation
  không lấy từ index. Gộp parent theo passage có distance tốt nhất, tie theo ID.
  `top_k` là giới hạn passage; có thể trả ít parent hơn do dedup.

## Lỗi và trace

Query vượt budget, thiếu config/index/model, sai identity hoặc lỗi runtime
đều fallback BM25 với **cùng canonical và cùng toàn bộ tham số scope**.
Canonical load lỗi hoặc snapshot bị thay đổi vẫn fail closed; không dùng
fallback để che lỗi dữ liệu. Query vector thành công nhưng không có hit trả
rỗng, không tự mở rộng scope hoặc chuyển sang nguồn khác.

`search_with_trace()` trả hits và trace bất biến theo từng lần gọi, gồm
requested/used mode, index ID, filter, passage/parent IDs và reason code.
`search()` gửi cùng trace vào logger `app.hus.vector_query` ở mức INFO;
ứng dụng cần bật logger này nếu muốn thu log. Không log toàn văn câu hỏi,
exception detail, key hoặc đường dẫn cache. Schema câu trả lời HTTP giữ nguyên.
Model/query và kiểm Chroma được serialize trong process; không lưu trace
mutable dùng chung giữa các request.

## Chạy thử tường minh

Ví dụ trong PowerShell, chỉ áp dụng cho process đang chạy:

```powershell
$env:HUS_RETRIEVAL_MODE = 'vector'
$env:HUS_VECTOR_INDEX_PATH = "$PWD/data/hus/vector_indexes/e5_small_v3_20261109"
$env:HUS_VECTOR_MODEL_CACHE = "$PWD/backups/vector_index_v3_20261109/model"
$env:HUS_VECTOR_EXPECTED_INDEX_ID = '8dad2f0f719a5228403d87f2b0c36a95f64fada9b82bf26bf432d4fed2469f74'
& './backups/vector_index_v3_20261109/venv/Scripts/python.exe' -m uvicorn app.hus.demo:app --host 127.0.0.1 --port 8001
```

Môi trường ML riêng phải có đúng các package trong hash lock V1 và model
cache V3 đã verify. Không tự tìm hoặc tạo index khi path thiếu. Đổi mode/data/
index cần restart hoặc clear cache service có kiểm soát. Trở lại lexical
bằng cách đặt `HUS_RETRIEVAL_MODE=lexical` rồi restart; không cần model/index.
Ví dụ trên không được chạy để bật mặc định trong lượt triển khai này.

## Kiểm chứng và giới hạn

- Bộ test V4 kiểm prefilter/scope/opt-in, canonical fail closed, hit sai,
  parent dedup, concurrency, tokenizer 512/513 và live index tamper.
- Hai process riêng chạy 8 query thật F1/F3 × 4 ngành trên **bản sao index V3**;
  thứ hạng parent trùng nhau. Query quá budget fallback đúng; sửa manifest
  bản sao sau startup bị chặn. SHA toàn bộ index gốc trước/sau không đổi.
- HTTP thật qua service vector: 12 câu F1/F2/F3 × 4 ngành đều answered có
  citation; 8 lượt F1/F3 có vector trace, F2 không gọi vector. F3 chưa opt-in
  bị chặn. Đây là smoke kỹ thuật, không phải đánh giá ngữ nghĩa độc lập.
- Rà soát kỹ thuật AI độc lập không có Critical/Important/Minor được xác nhận.
  Regression, Chromium, Node và Ruff ghi riêng trong receipt.
- Chi phí kiểm toàn inventory được chấp nhận cho demo này: 8 query local ghi
  nhận cold đầu tiên khoảng 13–41 giây (kèm nạp/verify model và index), warm
  khoảng 0,8–1,0 giây ở lượt đầu. Không coi đây là benchmark/SLO production.
- Không có phép đo Recall mới; không chứng minh Recall độc lập ≥90%.
  Support gate lexical vẫn giữ nguyên, nên vector tìm được passage không
  mặc nhiên bảo đảm chatbot trả lời mọi paraphrase. V5/RRF, LLM và A7 còn riêng.

Trong lúc làm, checkout được reset bên ngoài từ `586e460` về `1ad85e3`
lúc 00:08 ngày 10/11. Phần tích hợp V4 được áp lại trên HEAD mới; không thay
lịch sử branch. Receipt phân biệt regression cũ trên `586e460` với lượt cuối.
Python mặc định thiếu argon2, nên kiểm thử đầy đủ dùng venv CI đã có;
không cài đặt/nâng package trong Python chính hoặc sửa optional ML lock.
