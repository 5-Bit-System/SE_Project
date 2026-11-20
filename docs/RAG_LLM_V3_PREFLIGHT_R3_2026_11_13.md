# L5 v3 — preflight r3 đạt, quyền Google chưa xác định

**Cập nhật mới hơn:** người dùng đã cấp một call chẩn đoán và đã thực hiện trên
[prepared r4: HTTP403, chưa xác định nguyên nhân](RAG_GOOGLE_DIAGNOSTIC_2026_11_13.md).
Các đề nghị “chưa duyệt” bên dưới là trạng thái lịch sử của lượt r3; receipt cũ
giữ nguyên. Chưa được cấp cohort mới hoặc call thứ hai của lượt chẩn đoán.

Ngày **13/11/2026**, nhánh `hus-llm-rag`, nền `f61b0fd` + WIP. Đã prepare lại
trên code sau sửa CLC/assessment và kiểm offline. **Chưa gọi Google mới**, chưa
xử lý quyền thực tế, chưa đo B sinh thật; giữ LLM tắt/L6 `keep_disabled`.

**Lưu ý sau sửa runtime cùng ngày:** [cú pháp/role scope](RAG_REQUEST_ROLE_REPAIR_2026_11_13.md)
đã thay code; prepared r3 nay **stale**, không dùng để gọi mới. Các khẳng định
pins khớp dưới đây áp dụng tại lượt preflight đã seal. Cần prepare/preflight mới
và ngân sách riêng trước mọi Google call; không sửa artifact cũ để làm khớp.

## Prepared và phép so sánh A/B

- [Prepared r3](../data/hus/evaluation/runs/llm_v3_v4_prepared_20261113_r3/prepared.json)
  dùng source pack cũ `llm_v3_v4_dev_20261113_r1`:36 ca,24 prompts (8 F1/8 F2/
  8 F3),12 controls; **98.268 prompt chars**, cap **1.024 output token/call**.
- Source audits36/36 đạt; pins trước/sau và validate hiện tại khớp. R2 nay stale,
  giữ nguyên để đối chiếu. Không rebuild/đổi câu hỏi/gold để chạy qua preflight.
- 36 request/effective request/A/gold/evidence/audit/retrieval/prompt khớp r2
  và prepared của live v3 cũ;36 A cũng khớp exact observations A đã lưu. Chỉ
  baseline latency được đo lại; không dùng equality của A để suy chất lượng B.
- 24 payload khớp byte bản đã review public/privacy. Tái dùng review theo equality,
  không nhận là đã đọc mới payload hoặc so với backend key. Không gửi tài khoản,
  bảng điểm/history hoặc key trong prompt. Model yêu cầu giữ
  `gemini-3.5-flash-lite`, endpoint Google HTTPS trực tiếp đã ghim.
- 61 test `test_v4_measurement.py`/`test_access_failures.py` đạt; một warning
  Starlette/httpx có sẵn. Không có runtime change nên không lặp full suite.
  Source oracle/pins/guard offline không chứng minh kết nối provider thành công.

## Bằng chứng lỗi quyền hiện có

Run13/11 có24 lần thử: **24 HTTP403,24 `http_error`**, không actual model.
Không có retained error body hoặc provider_error category; không thể khôi phục
nguyên nhân từ cache. Banner gần bandwidth limit đã biết chưa là bằng chứng lỗi
key/billing/quota cụ thể. Hai ngân sách24 calls đều đã hết; không gọi thêm
smoke/model-list/tokenizer theo quyền cũ.

Người dùng yêu cầu agent tự kiểm tra. Đã kiểm công cụ kết nối: **không có Codex
document session**, không có phiên AI Studio/browser đã đăng nhập để đọc trạng
thái riêng. Không truy cập cookie/password hoặc suy trạng thái tài khoản từ trang
public. Phần kiểm được đã hoàn tất bằng artifact local và tài liệu chính thức.

Google mô tả nhiều trường hợp project/verification/payment/key có thể dẫn tới
403, phải dựa vào thông báo thật; trang hướng dẫn cũng nêu model-list trả200
không chứng minh inference được phép. Đây là thông tin tham khảo chung, **không
xác định trường hợp nào đã xảy ra ở project hiện tại**.
[Hướng dẫn Google](https://aistudio.google.com/docs/troubleshooting#project-unavailable).
Không tự đổi key/model, bật billing hoặc retry để đoán nguyên nhân.

## Chẩn đoán đề xuất — chưa được duyệt

[Đề nghị cụ thể](../data/hus/qa/20261113/llm_preflight_r3/proposed_diagnostic.json):
**tối đa1 call** với `L5V4-Q001` (F1),3.607 prompt chars, model/endpoint đã ghim,
max1.024 output token. Dùng key backend hiện có sau khi được phép; không in/sửa
key. Không retry/đổi model, dừng sau một lần thử; nếu công cụ dùng pacing thì giữ
tối thiểu5 giây. Input token/chi phí chưa biết, không giả định miễn phí.

Mục tiêu là lấy HTTP status và diagnostic allowlist thật (`provider_status`,
`access_issue`); không lưu error message/body/header/key/project ID. Kết quả có
thể vẫn unspecified, khi đó không gán nguyên nhân. Một call thành công cũng
không thành nghiệm thu nội dung L5 hoặc quyền bật mặc định L6.

Chưa cấp ngân sách cho24-call cohort tiếp theo. Sau khi xác minh/khắc phục quyền,
cần ngân sách riêng, kiểm lại pins và tạo run mới. A/B dùng đúng frozen A/
retrieval/snapshot, ghi actual model/usage/token/latency/used/fallback và review
exact output. Batch dừng ngay401/429, sau hai403 liên tiếp; không retry/switch.

## Receipt và giới hạn

[Receipt](../data/hus/qa/20261113/llm_preflight_r3/report.json) ghim comparison,
đề nghị1call chưa duyệt,403 cache và61 test. **2.841 file cũ giữ SHA**; source/
run/gold/review trước giữ nguyên. Cached replay ba L5 run/review cũ tái hiện,
không provider/network; prepare/export cũng0 lần thử socket/provider.

| Binding | SHA-256 |
| --- | --- |
| Prepared r3 manifest |`a18e1ca9924e71ad4bfc112f3b976dfe39c03c953dd60b04040a2cf443760587`|
| Pins |`a13f21c4883707ac4be51c1260e70cc5c8efbae33bf864128dad4214c3bc3982`|
| QA manifest |`8069afba50b966fa6d04e28765e7e3e667736935cff7743041e6c7a86788aede`|

Không đọc private `.env`/template/key, đổi cấu hình server hoặc tạo live run.
L6 cần bản sinh thật có gain, đủ ý/facts/citation, latency phù hợp và operator
chấp nhận; fallback/mock/preflight không thay bằng chứng này. Giữ local-only,
không stage/commit/push/PR/Actions/deploy.
