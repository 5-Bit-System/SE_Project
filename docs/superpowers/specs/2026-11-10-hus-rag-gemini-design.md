# HUS RAG → Gemini trực tiếp: thiết kế tích hợp

Trạng thái: L2/L3/L4 đã triển khai local theo từng hàng người dùng chọn;
adapter L3 đã nối vào Q&A sau guard, L4 có slot không chờ và UI opt-in/disclosure.
L5 đã đo36cặp/24live,19used/5fallback; một thiếu ý lọt validator, chưa đủ điều kiện
L6 bật mặc định. L6 kỹ thuật/readiness/rollback đã có, checker giữ off; xem
[hồ sơ L6](../../RAG_LLM_L6_2026_11_10.md). Nhánh `hus-llm-rag`; WIP chưa commit, mặc định LLM off. Xem [hồ sơ L5](../../RAG_LLM_L5_2026_11_10.md).

## Mục tiêu và quyết định của người dùng

Người dùng muốn LLM trả lời dựa trên RAG và gọi trực tiếp Google Gemini.
Người dùng đã chọn **cả F1/F2/F3 qua Gemini; dữ kiện F2 phải giữ nguyên từ nguồn**.
Điều này thay thế phần kế hoạch cũ bỏ qua LLM ở F2.

Luồng đề xuất: câu hỏi → RAG hiện có → đáp án/bằng chứng canonical → Gemini
→ kiểm đầu ra → câu trả lời hiển thị với citation. BM25, vector và hybrid đều dùng
được; không đổi retrieval mặc định `lexical` trong công việc này.

## Cách tiếp cận

Áp dụng lớp diễn đạt **sau** `HUSAnswerer`, theo hướng mục 7 đã đề xuất.
LLM không chọn ngành/phiên bản, không chạy truy vấn riêng, không chọn nguồn mới,
không quyết định một câu bị gate từ chối có được trả lời hay không.
Cho LLM điều phối retrieval sẽ thay đổi các rào chắn đã kiểm và vượt phạm vi này.

F1/F3 cho phép Gemini viết lại từ bằng chứng; F2 dùng đầu ra cấu trúc để backend
chèn nguyên khối dữ kiện canonical. Đây là lựa chọn đề xuất của người triển khai
để thực hiện yêu cầu giữ nguyên tín chỉ/tiên quyết, thay vì chỉ tin lời nhắc model.

## Quyền gọi và hành vi lỗi

- Thêm `allow_llm_rewrite`: strict boolean, mặc định `false`.
- Chỉ gọi khi server bật `HUS_LLM_ENABLED`, người dùng bật quyền diễn đạt,
  đáp án RAG có `status=answered` và có citation từ snapshot đang chọn.
- F3 vẫn cần `allow_generated_reference`; quyền F3 và quyền diễn đạt độc lập.
- F2 được gọi model sau lookup canonical; không dùng vector để suy diễn F2.
- Basic chat, thiếu nguồn, ngoài phạm vi và cần làm rõ không gọi model.
- Thiếu key/cấu hình sai/HTTP lỗi/timeout/đầu ra sai/quá tải/quá ngân sách → giữ
  nguyên bản trích nguồn, trả metadata lý do ổn định, không lộ lỗi provider.
- Không thử provider/model khác, không retry tự động, không gọi ở startup.
- Một lời gọi đồng thời/process; lời gọi đến khi bận dùng bản trích nguồn ngay.

## Ràng buộc dữ liệu và response

`hus_answer` giữ nguyên toàn bộ: reply gốc, facts, citations, quote, URL/hash,
release, phiên bản, review, warnings. Gemini chỉ thay `reply` cấp chat khi đầu ra
được chấp nhận. Client vẫn có thể đọc đáp án gốc và bằng chứng đầy đủ.

Metadata `generation`: used, requested_model, model từ envelope provider nếu được
dùng, fallback_reason; L3 bổ sung prompt hash chuẩn tắc và usage khi có, L4 thêm
http_status số nguyên khi lỗi HTTP. Theo yêu cầu giữ response
cũ khi tắt, nếu server hoặc người dùng tắt quyền thì giữ nguyên các key/giá trị,
không thêm null field. L3 hiện đã đăng ký adapter mặc định sau guard; chỉ khi
factory không cung cấp adapter mới dùng `pipeline_unavailable`.
Không nhận model ID hoặc URL/key provider từ payload người dùng.

Đọc cấu hình HUS riêng khi cần; không import recommendation, auth hoặc dữ liệu
tài khoản. Không tự tạo `.env`, sao chép key từ chatbot đề xuất môn hoặc bật billing.
Key hiện được lưu trong root `.env` bị Git bỏ qua; live smoke client L1 đã đạt
trước lượt L2. L2 chỉ kiểm offline, không đọc/in key hoặc gọi provider thật.

## Bundle và prompt

Chỉ gửi câu hỏi một lượt, scope ngành/phiên bản, release ID/hash, dữ kiện canonical
cần trả và các citation đã chọn: ID backend, quote và trạng thái nguồn.
Không gửi toàn bộ corpus, lịch sử chat, tài khoản, bảng điểm hoặc secret.
Không gửi đường dẫn filesystem. Tách system instruction và JSON evidence bundle;
mọi nội dung nguồn là dữ liệu, kể cả khi có câu yêu cầu bỏ chỉ dẫn hoặc gọi tool.
Không cấp tool/action, không truy cập web qua model.

Bundle không bị truncate âm thầm. Nội dung system+user vượt 12.000 ký tự Unicode
→ `prompt_budget` và dùng bản trích nguồn; output thô tối đa 8.192 ký tự kể cả
whitespace. Giới hạn này là lựa chọn ban đầu để kiểm thử, không phải benchmark.
Output tối đa 1.024 token, không stream; timeout HTTPX hiện có 20s mỗi pha.
Không công bố đây là deadline tổng 20s; deadline toàn request sẽ cần thiết kế riêng
nếu đưa ra yêu cầu vận hành đó.

## Đầu ra F1/F3

JSON strict: `kind=rewrite`, danh sách `points`; mỗi ý có `text`, một `citation_id`
và `anchor_quote` nguyên văn của citation đó (>=20 ký tự hoặc toàn nguồn ngắn).
Không nhận HTML, URL mới hoặc extra key.
Backend kiểm schema, ID, anchor thuộc quote, số/mã môn/phiên bản không phát sinh
ngoài bằng chứng, và mọi citation đã chọn được đại diện trong đầu ra.
Backend gắn lại nguyên cảnh báo/phạm vi/review và nguồn từ canonical.

Sửa coverage sau L5: prompt v2 giữ schema output, bổ sung kiểm bảo thủ theo các
đơn vị câu/xuống dòng/chấm phẩy có span gốc. Mỗi đơn vị cần toàn bộ token NFKC/
casefold theo thứ tự trong text của một point cùng citation, với anchor chứa cả
đơn vị. Không bỏ stopword/phủ định/điều kiện hoặc suy đồng nghĩa; thiếu thì fallback.
Không dùng ID/anchor hay khai báo coverage của model thay cho từ ngữ thực được trả.
Đổi case/spacing/câu nối trung tính được; paraphrase xa có thể bị loại. F2 vẫn chỉ style.

Các kiểm tra này **không chứng minh entailment hoặc đủ ý về mặt ngữ nghĩa**.
Ví dụ model có thể đổi quan hệ hoặc phủ định dù dùng đúng số và ID. Cần review
nội dung khi đo L5; giữ mặc định tắt và không coi schema đúng là nghiệm thu chất lượng.
Không thêm LLM judge để tự công nhận đầu ra đúng.

## Đầu ra F2: giữ dữ kiện bằng cấu trúc

Gemini nhận facts canonical cùng bằng chứng và trả JSON strict:
`kind=facts`, `style=direct|explain_source`, `fact_keys`, `citation_ids`.
Các key facts và citation phải khớp đủ bộ dữ liệu canonical, không được trả giá trị
mới hay một đoạn văn chứa số/tiên quyết do model tự viết.

Backend dùng style để chọn lời dẫn trung tính, sau đó chèn **nguyên đáp án F2
canonical**, gồm mọi giá trị, dòng nguồn, null/unknown/conflict/unresolved và warnings.
Ở pha này LLM tham gia chọn cách trình bày F2; không viết giải thích học vụ tự do.
Đây là giới hạn chức năng có chủ ý, cần hiển thị rõ trong hướng dẫn và khi nghiệm thu.
Không biến ô nguồn trống thành “không có tiên quyết”, không kết luận đủ điều kiện
đăng ký hoặc tốt nghiệp, không cộng/sửa số liệu chương trình/nhóm.

## UI

Thêm checkbox độc lập “AI diễn đạt từ nguồn”, mặc định tắt. Khi chọn, ghi rõ câu hỏi
và bằng chứng được gửi tới Google. Không gửi lại lịch sử trò chuyện.
Khi thực sự dùng: nhãn AI diễn đạt; khi fallback: báo đang hiển thị bản trích nguồn.
F3 luôn giữ nhãn “kiến thức AI”. Render text bằng `textContent` và citation bằng
resolver hiện có. Đổi ngành tắt cả hai quyền, xóa hội thoại và bỏ response muộn.
L4 đã triển khai khả năng cấu hình `/hus/config` không gọi provider; chỉ mở checkbox
cho endpoint HTTPS Google để disclosure đúng. Slot chỉ giới hạn adapter Q&A trong
một process, không giới hạn mọi worker hoặc client độc lập. Không xếp hàng/retry.

## File dự kiến và kiểm chứng

- `app/hus/llm/`: bundle/prompt, output contracts/validation, orchestration/concurrency.
- `app/schemas/hus.py`: quyền strict; `app/hus/chat.py`: adapter sau RAG và metadata.
- `app/hus/llm/client.py`: giữ API text cũ, bổ sung kết quả có returned model/usage
  nếu cần để không báo model yêu cầu thành model đã trả thực tế.
- `app/static/hus-rag-demo.{html,js,css}`: checkbox, disclosure và nhãn kết quả.
- Test trước: server/user tắt, cả F1/F2/F3, F3 hai quyền, F2 null/conflict/unresolved,
  không nguồn, basic chat, prompt injection, ID/anchor/số/mã lạ, thiếu ý/citation,
  HTTP/timeout, bận, ngân sách, giữ nguyên canonical, UI đổi ngành/response muộn.
- Chạy focused, regression offline đầy đủ, Ruff và browser checks phù hợp UI.
  Không sửa baseline/gold/source/index/model cache hoặc receipts lịch sử.

Không nằm trong pha này: A/B chất lượng L5, live quota, bật mặc định L6, deploy,
commit/push/PR. Live smoke cần key server được cung cấp; không xin key qua chat.
