# Adapter Gemini có kiểm tra bằng chứng cho HUS RAG

Adapter diễn đạt từ bằng chứng đã được chọn cho câu hỏi HUS. Client dùng
`httpx` gọi trực tiếp Google Gemini qua API tương thích OpenAI. Import,
khởi tạo client và kiểm cấu hình không gọi provider. Xem [hướng dẫn vận hành](../../../docs/HUS_LLM_OPERATIONS.md)
để chạy demo hoặc cấu hình Workspace.

## Cấu hình và quyền ở demo độc lập

```dotenv
HUS_LLM_ENABLED=false
HUS_LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
HUS_LLM_MODEL=gemini-3.5-flash-lite
HUS_LLM_API_KEY=
```

`HUSLLMSettings.from_env()` đọc các biến `HUS_LLM_*` của tiến trình.
Launcher Gemini nạp cấu hình lưu riêng ở backend và bật chế độ tự động
cho tiến trình demo. Launcher RAG offline giữ LLM tắt. Trong chế độ thủ
công, API dùng thêm `allow_llm_rewrite` kiểu boolean, mặc định tắt.
Quyền `allow_generated_reference` độc lập và được kiểm cho F3.
`GET /hus/config` trả khả năng diễn đạt ở demo mà không thử kết nối.

Adapter diễn đạt chỉ nhận đáp án F1/F2/F3 có trạng thái `answered` và
citation. Backend giữ `hus_answer` canonical, bao gồm facts, quote, URL,
hash, review và cảnh báo. `generation.used` cho biết có sử dụng đầu ra
provider. Metadata `interpretation` ghi riêng bước hiểu ý định.

## Ràng buộc bằng chứng và đầu ra

`evidence.py` kiểm release, phạm vi ngành, provenance và nguồn đã chọn.
Prompt chứa câu hỏi, scope, facts đã lọc, các đoạn và ID nguồn. Thông tin
tài khoản, bảng điểm, lịch sử chat, đường dẫn nội bộ và khóa API nằm ngoài
payload. Dữ liệu trong prompt không cấp thêm quyền cho model.

- F1/F3 ở chính sách `legacy` dùng `rewrite_v3`. Model phải trả đủ ID các
  đoạn được cấp. Backend kiểm từ ngữ và toán tử theo đoạn, rồi dựng lại
  thứ tự, bố cục và citation.
- F1/F3 ở chính sách `focused` chọn nguồn và đoạn phù hợp với ý hỏi. Nếu còn
  nhiều phạm vi nguồn hợp lệ, UI yêu cầu người dùng chọn. Protocol
  `focused_rewrite_v1` dùng ID của các đoạn đã chọn và kiểm từ ngữ, số,
  toán tử và điều kiện theo nguồn. [Thiết kế focused](../../../docs/RAG_FOCUSED_ANSWER_2026_11_15.md).
- F2 nhận kiểu trình bày và tập khóa facts/ID nguồn đã cấp. Backend giữ giá
  trị tín chỉ, tiên quyết, danh sách, kết quả đếm và trạng thái chưa rõ.
- Ở demo tự động, bước hiểu ý định chỉ xử lý câu `routing_unknown` thỏa
  guard. Backend kiểm schema và định danh môn, giữ nguyên phạm vi và quyền,
  rồi thực hiện tra cứu hoặc phép đếm. [Hợp đồng ý định và F2](../../../docs/RAG_INTENT_F2_CATALOG_2026_11_14.md).

Kiểm ID, từ ngữ và hash bảo vệ hợp đồng đầu ra. Đánh giá độ đúng và đủ ý
cần đối chiếu câu trả lời với nguồn.

## Giới hạn và lỗi

Adapter giữ trần 12.000 ký tự prompt, 8.192 ký tự nội dung trả về và
1.024 token đầu ra. Client dùng timeout 20 giây cho từng pha HTTPX và
không retry tự động. Metadata chẩn đoán gồm mã, số đếm hoặc ID đã biết.
Key, prompt, nội dung bị từ chối và body lỗi provider không đi vào phản
hồi lỗi.

Ở demo tự động, HTTP 429 bật RAG offline cho tiến trình đến khi restart.
Các lỗi provider hoặc lỗi kiểm đầu ra khác trả API 502. Lỗi dữ liệu
canonical trả API 503. Bản ghi `used=false` có thể đã phát sinh lời gọi
model trước khi đầu ra bị từ chối.

Chạy test offline của adapter bằng `python -m pytest tests/hus/llm -q`
trong môi trường dev. Xem báo cáo [30 câu dùng bản demo](../../../docs/RAG_STUDENT_CONTENT_30_LIVE_2026_11_14.md)
và [lượt focused dùng Gemini](../../../docs/RAG_FOCUSED_LIVE_2026_11_19.md)
để biết cấu hình, câu đối chứng và giới hạn của từng phép đo.
