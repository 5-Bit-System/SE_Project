# V4 — Vector query và rào chắn

Trạng thái: người dùng đã duyệt và yêu cầu triển khai; hoàn tất local 10/11/2026.
Nhánh: `hus-embedding-chromadb`. Chỉ làm local; không push khi chưa có lệnh.

## Mục tiêu và phạm vi

Nối query F1/F3 vào index V3 đã có, lọc trước top-k, lấy câu trích dẫn
từ snapshot canonical và fallback BM25 có lý do khi thành phần vector lỗi.
F2 tiếp tục lookup cấu trúc; routing, support gate và citation policy giữ nguyên.
Không thực hiện hybrid V5, LLM, nâng trạng thái nguồn hoặc đổi lexical mặc định.

## Phương án

Đề xuất adapter vector giữ cùng giao diện `search()` và trả canonical
`RetrievalHit`, được chọn tường minh qua `HUS_RETRIEVAL_MODE=vector`.
Service vẫn nạp canonical trước khi khởi tạo vector. Lexical không import ML.
Phương án này đã được người dùng duyệt để triển khai V4.

Một CLI query chỉ chạy offline có thể kiểm index nhưng chưa đáp ứng nối query
vào chatbot. Sửa trực tiếp BM25 để luôn nạp vector làm mất tính độc lập của
lexical. Vì vậy hai hướng này không được đề xuất cho V4.

## Cấu hình và identity

Vector mode cần đường dẫn index, model cache và expected index ID được ghim
tách khỏi DB. Contract và passage set phải khớp snapshot canonical và index V3.
Không download, tạo collection, build index hoặc sửa artifact cũ trong request.
Hybrid vẫn unavailable. Thay cấu hình/release cần restart hoặc clear cache
có kiểm soát như hiện tại.

## Query và prefilter

1. Kiểm input và lấy tập canonical đủ quyền theo đúng bộ tham số của BM25:
   family, major, version, variant, course code, field và generated opt-in.
   Giữ cả ràng buộc course code xuất hiện trong câu hỏi.
2. Tạo `where` Chroma trước query: release ID/hash, family/major và các scope
   được yêu cầu; F1 chỉ selection review include/include_markdown, F3 chỉ
   generated/needs_review có opt-in. Ràng buộc tập parent canonical đủ quyền
   ngay trong prefilter để không lấy global top-k rồi lọc muộn.
3. Tokenize chuỗi đầy đủ `query: ` + câu hỏi với graph tokenizer V3 đã ghim,
   bao gồm special tokens. Quá 512 token thì fallback; không truncate.
4. CPU float32, masked mean và L2 theo cùng identity encoder V3. Truy vấn bằng
   query embedding tường minh, không sử dụng embedding function mặc định.
5. Passage ID phải thuộc inventory đã verify; metadata/hash phải khớp.
   Resolve parent canonical và kiểm scope/hash lần nữa. Không lấy quote hoặc
   locator từ index. Gộp passage cùng parent theo khoảng cách tốt nhất;
   thứ tự tie xác định. Không hứa luôn đủ k parent khi top-k passage trùng parent.

## Phân loại lỗi và fallback

- Canonical thiếu/sai hash/không hợp lệ: fail closed, không gọi fallback.
- Input sai hoặc chưa có quyền F3: giữ hợp đồng hiện tại, không coi là lỗi index.
- Query quá token budget; index/model/dependency thiếu hoặc sai identity;
  Chroma lỗi; kết quả sai schema/nonfinite/ID/hash/scope: bỏ toàn bộ vector result
  và chạy BM25 trên cùng canonical và đúng bộ tham số ban đầu.
- Không có hit hợp lệ trong một query thành công: trả rỗng, không tự mở rộng scope.
- Trace mỗi query ghi requested/used mode, index identity, mã lý do fallback,
  passage/parent IDs và filter. Không dùng trạng thái mutable dùng chung giữa
  các request; không log toàn văn câu hỏi hay đường dẫn nhạy cảm.

## Thành phần dự kiến

- Module retriever/query encoder V4 riêng, tái sử dụng verifier và pooling V3.
- Cấu hình vector tường minh và điểm chọn retriever trong HUS service/answerer.
- Kênh trace nội bộ theo từng kết quả query, giữ schema trả lời hiện có.
- Tests V4 và cập nhật test mode reserved tương ứng với phiên bản mới.
- Báo cáo và receipt mới; không ghi đè evidence V1–V3.

## Kiểm chứng

Tests offline với fake encoder/collection sẽ kiểm `where` đã truyền trước top-k;
không trộn ngành/edition/variant/môn/review/release; F3 không opt-in; parent
dedup; query prefix/special/token boundary; lỗi index và lý do fallback;
canonical hỏng fail closed; citation chỉ từ canonical; lexical không import ML.

Smoke riêng dùng venv/model/index V3 hiện có: query thật và reopen process,
so scope/parent/citation, kiểm fallback trên bản sao/synthetic artifact.
Không chạy helper ghi đè index gốc hoặc gọi provider ngoài.

Regression phù hợp gồm HUS/API, Chromium, Node và Ruff trong môi trường sẵn có.
Báo riêng điều kiện không chạy được; không dùng số test pass hoặc smoke làm
chứng nhận Recall độc lập. Không commit/push/deploy trong bước triển khai này.
