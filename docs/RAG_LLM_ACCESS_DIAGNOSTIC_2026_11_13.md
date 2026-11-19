# L5 v3 — chẩn đoán quyền và dừng batch, đã kiểm offline

**Lượt live mới hơn:** [một call đã được cấp và thực hiện trên r4](RAG_GOOGLE_DIAGNOSTIC_2026_11_13.md)
trả HTTP403/unspecified, chưa sửa quyền; các trạng thái chưa được cấp trong phần
lịch sử dưới đây không thay thế authorization/kết quả mới này.

**Cập nhật sau sửa baseline:** prepared r2 dưới đây nay stale; đã có
[preflight r3 khớp pins](RAG_LLM_V3_PREFLIGHT_R3_2026_11_13.md), chưa gọi Google
mới hoặc được duyệt1call. Phần dưới giữ trạng thái lịch sử lúc kiểm r2.

Ngày **13/11/2026**, nhánh `hus-llm-rag`, nền `f61b0fd` + WIP.
Đã triển khai phần chuẩn bị offline: diagnostic HTTP có giới hạn, circuit dừng
lỗi quyền, regression và prepared `r2` khớp pins mới. **Chưa xác định hoặc sửa
quyền key/project thực tế, chưa gọi thêm Google, chưa có phép đo L5 mới.**
Hai ngân sách24 calls trước đều đã hết; LLM mặc định vẫn tắt.

**Bổ sung từ người dùng:** đã nhận banner gần bandwidth limit và đề nghị
configure billing. Chưa có error body403/trạng thái riêng key hoặc project;
không kết luận nguyên nhân là quota/billing hoặc quyền đã được sửa.
[Đối chiếu tài liệu Google và assessment L6 mới](RAG_L6_KEEP_DISABLED_2026_11_13.md).
Receipt offline dưới đây ghi trạng thái trước khi nhận banner, giữ nguyên.

## Hành vi mới

| Trường hợp | Hành vi runner L5 |
| --- | --- |
| Hai HTTP403 liên tiếp | Dừng gửi các câu tiếp theo, ghi `permission_denied`. |
| HTTP401 | Dừng ngay, ghi `authentication`. |
| HTTP429 | Dừng ngay, ghi `quota`, giữ hành vi đã có. |
| HTTP khác hoặc transport error xen giữa403 | Ngắt chuỗi403; không retry câu đã lỗi. |
| Hết `--max-calls` | Dừng gửi, ghi `call_budget` cho các ca còn lại cần gọi. |
| Các ca còn lại và controls | Giữ bản trích nguồn; controls không gọi. Ca chưa gọi không được giả lập HTTP lỗi hoặc model thực. |

Circuit nhận status **trước khi đọc body**, nên timeout/malformed body không
làm batch tiếp tục sau ngưỡng lỗi quyền. Không đổi model, token cap, pacing hay
retrieval. Đây là circuit **trong một batch L5**, không phải trạng thái toàn cục
qua nhiều request chatbot. HTTP403 đơn lẻ chưa đóng circuit; giới hạn một call
vẫn được dùng cho chẩn đoán riêng nếu người dùng duyệt.

Client giữ `HUSLLMError(code="http_error", status_code=...)`, thêm diagnostic
`stage=provider_http` chỉ gồm `provider_status` và `access_issue` theo Literal.
Chỉ parse JSON lỗi tối đa16.384 bytes; message dùng để phân loại tối đa8.192 ký
tự và không được ghi ra. Không lưu error message/body, headers, unknown code,
project ID, URL hoặc key. Unknown/non-JSON/quá giới hạn trả `other/unspecified`.
Giới hạn này áp dụng phần **phân tích**, không phải trần tải HTTP body tổng thể.

Các nhóm nhận biết được gồm provider báo key bị lộ, cần xác minh free tier hoặc
project bị từ chối; HTTP403 chung không đủ để chọn một nhóm cụ thể. Google có
hướng dẫn kiểm key và trạng thái project, gồm xác minh/hạn chế truy cập/key bị
chặn. Không suy ra trường hợp nào đã xảy ra cho key hiện tại từ run cũ.
[Hướng dẫn chính thức](https://aistudio.google.com/docs/troubleshooting#project-unavailable).

Trace mới lưu `provider_error` đã lọc; report ghi `failure_policy` và
`evaluation_stop_reason`. Replay kiểm circuit theo chính sách mới đối với run
có marker đó; run lịch sử không bị áp quy tắc mới để viết lại kết quả.

## Kiểm chứng offline và prepared mới

- **519 test LLM pass**, gồm30 mới; sau chỉnh cách dùng fixture đã chạy lại30
  test mới pass. Các nhóm giao nhau, không cộng thành549 hoặc full-repo claim.
  Ruff đạt; còn một warning Starlette/httpx đã có.
- Kiểm403 lặp/không liên tiếp,401/429, body timeout, không retry/đổi model,
  max1call, giữ canonical/fallback/controls, không rò error text/key và replay
  từ chối circuit bị sửa. Không dùng mock làm bằng chứng kết nối Google thật.
- Prepared mới: `data/hus/evaluation/runs/llm_v3_v4_prepared_20261113_r2`.
  Dùng cùng source pack `llm_v3_v4_dev_20261113_r1`;36 source audits,24 prompts,
  12 controls, tổng **98.268 prompt chars**, cap1.024 output token/call.
- **36/36** baseline/request/effective request/gold/evidence/retrieval trace/
  prompt khớp `r1`.24 exported payload khớp byte bản đã đọc trước; tái dùng
  privacy review theo equality, không tuyên bố đọc mới24 payload hoặc so với key.
- Pins mới `33ab82eefad8ee70028abe084a729ce9331dd2111a1596cb0e38240877972e4f`;
  manifest prepared `f8c5fbd0808343c91220d20798410f93483336bb08a22a557fdf8f5948d6fd52`.
  Prepared `r1` và các run trước thay đổi này **không còn khớp pins hiện tại**;
  không sửa chúng. Replay tái hiện điểm cũ không đồng nghĩa nghiệm thu code mới.

Trong bước prepare/export, socket và khởi tạo provider bị chặn: **0 lần thử**.
Không đọc `.env`, template, key hoặc trạng thái riêng tài khoản Google.
`CURRENT` v4/lexical/LLMoff, dữ liệu/retrieval/gold/prompt không đổi.

## Việc còn lại trước lời gọi thật

1. **Trạng thái riêng project/key:** banner gần bandwidth limit đã nhận chưa
   xác định403. Kiểm trạng thái của đúng project/key; chỉ cung cấp mã/nội dung
   không chứa key. Chưa thể khẳng định đã khắc phục403.
2. **Xử lý đúng nguyên nhân:** làm theo thông báo thực tế trong tài khoản backend;
   không tự thay key/model, bật billing hoặc sửa cấu hình riêng trong bước này.
3. **Ngân sách mới:** đề xuất chẩn đoán giới hạn **tối đa1 call**, dùng ca public
   đầu tiên của prepared `r2`, model hiện tại,1.024 output token, không retry.
   Chưa được duyệt và chưa chạy; không tự gộp vào quyền24 calls đã dùng hết.
   Smoke/model-list/tokenizer cũng cần quyền riêng theo điều kiện người dùng.
4. **Sau khi quyền hoạt động và có budget cohort:** kiểm pins lại, tạo run mới,
   giữ exact A/retrieval/snapshot giữa A/B. Review output/fallback/token/latency;
   chỉ xét L6 khi có bản sinh thật giữ đủ ý và gain cùng operator chấp nhận.

Không lấy lỗi403 cũ để khẳng định key bị lộ/thiếu billing; không coi bản chuẩn
bị offline hoặc một smoke OK là nghiệm thu chất lượng RAG→LLM.

[Receipt và test binding](../data/hus/qa/20261113/llm_access_diagnostic_r1/report.json),
[đối chiếu prepared](../data/hus/qa/20261113/llm_access_diagnostic_r1/prepared_comparison.json),
[đề nghị một call chưa được duyệt](../data/hus/qa/20261113/llm_access_diagnostic_r1/proposed_diagnostic.json),
[run403 lịch sử](RAG_LLM_L5_V3_2026_11_13.md),
[runbook](HUS_LLM_OPERATIONS.md).
