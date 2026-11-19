# Vận hành LLM HUS: bật có điều kiện và rollback

Phạm vi: chatbot hỏi đáp độc lập `app.hus.demo:app`; không dùng server/chatbot
recommendation hoặc tài khoản/bảng điểm. Google Gemini HTTPS trực tiếp, không cần
9Router. API key chỉ nằm trong môi trường/file cấu hình riêng ở backend.

## Trạng thái hiện tại

**Giữ `HUS_LLM_ENABLED=false`.** [L5 v3 live13/11](RAG_LLM_L5_V3_2026_11_13.md)
đã dùng hết24 calls được duyệt mới:24 HTTP403,0 used/24 fallback;12 controls
không gọi. Reply/canonical36 cặp giữ nguyên, không có bản sinh để nghiệm thu
diễn đạt/latency; token/chi phí chưa biết. Checker mới `keep_disabled`.
Đã [kiểm lại L6 trên code hiện tại](RAG_L6_KEEP_DISABLED_2026_11_13.md):
assessment13/11 r2 vẫn giữ tắt, thêm pins_changed;60 test readiness/rollback
đạt, gồm6 ca401/403 mới. Operator/content/latency sinh thật còn pending.
Các lệnh khởi động với cờ true bên dưới dành cho đợt nghiệm thu tương lai đã đạt
và được người vận hành chấp nhận; không phải chỉ dẫn bật ở trạng thái hiện tại.

Run lịch sử không lưu error body nên chưa xác định nguyên nhân403 cụ thể. Kiểm
trạng thái key/project trong AI Studio theo thông báo thực tế; không đưa key
vào chat/log/repo. Không gọi thêm smoke/model-list/tokenizer trong ngân sách đã
hết. Sau xử lý quyền, cần ngân sách riêng và kiểm pins trước run mới.
[Diagnostic/circuit mới đã kiểm offline](RAG_LLM_ACCESS_DIAGNOSTIC_2026_11_13.md):
hai403 liên tiếp dừng batch,401/429 dừng ngay, trước khi đọc body; HTTP khác hoặc
transport error ngắt chuỗi403. Client chỉ lưu mã/nhóm cố định; không lưu error
message/header/key/project ID. Không retry/đổi model; circuit chỉ áp dụng batch
L5, không dùng chung qua các request chatbot. Chưa xác minh quyền tài khoản thật.

L5 v4 lịch sử có16 used/8 fallback, readability2 tốt hơn/13 same/1 kém hơn;
không thay kết quả v3 bằng số cũ. Profile [nộp demo](HUS_RAG_SUBMISSION.md) ép LLM
tắt. Review mới tái dùng A cũ sau exact answer/request/gold/evidence binding;
human0, không là nghiệm thu độc lập hoặc chứng minh gain từ fallback.

[Prepared13/11 r1](RAG_LLM_V3_PREFLIGHT_2026_11_13.md) khớp pins trong collection:
36 audits/24 prompt/12 controls,98.268 prompt chars;67 test preflight đạt.
Prepared12/11 và13/11 r1 nay là lịch sử, pins khác sau sửa code. Prepared mới
`llm_v3_v4_prepared_20261113_r2` khớp code diagnostic/circuit:36 audits/24 prompt/
12 controls,24 payload nguyên byte;519 test LLM đạt. Đề nghị chẩn đoán tối đa1
call public L5V4-Q001/3.607 prompt chars/1.024 output token, **chưa được duyệt**.
Không sửa run/review/gold đã seal; nếu code/data/config đổi tiếp thì prepare lại.

**Sau sửa CLC/assessment:** r2 cũng đã stale. [Prepared/preflight r3](RAG_LLM_V3_PREFLIGHT_R3_2026_11_13.md)
khớp pins mới,36 A/retrieval/prompt và24 payload không đổi;61 test preflight đạt.
Chưa xác minh quyền thực, không có phiên AI Studio kết nối để agent đọc trạng
thái riêng. Đề nghị1call chẩn đoán nay ghim r3, vẫn chưa được duyệt; chưa cho
phép cohort24calls mới. RAG lexical/LLMoff vẫn là luồng test không cần key.

Người dùng báo banner gần bandwidth limit. Đây chưa phải error body403 hoặc
trạng thái riêng key/project; chưa đủ kết luận bật billing sẽ sửa lỗi. Không
thay key/billing hoặc gọi API mới từ banner; xem đối chiếu Google trong hồ sơ L6.

## Kiểm bằng chứng trước khi quyết định

```powershell
python -m tools.check_hus_llm_readiness --review-run data/hus/evaluation/runs/llm_l5_v3_ai_review_20261113_r1 --out data/hus/evaluation/runs/llm_l6_v3_readiness_20261113_r3
```

Dùng một tên output mới nếu đã tồn tại. Công cụ chỉ replay/đọc cache và hash nguồn/
code; không gọi model/retrieval, đọc key, sửa `.env` hay đổi cờ. Bằng chứng có lỗi
binding/hash sẽ bị từ chối; code/source/model khác run đo không đủ điều kiện reuse.
Report tách bản sinh dùng/fallback, lý do, ca thiếu ý và latency model thực đã đo.
Checker tự chọn pins theo pack v4 đã ghim, kiểm hash manifest/release/câu hỏi/
baseline bằng source oracle; không dựng lại prompt v2 cũ bằng builder v3 mới.
Run v4 lịch sử bị chặn bởi `pins_changed` và `readability_regressed`. Model trả
về phải khớp model yêu cầu; schema/hash đúng không thay nghiệm thu ngữ nghĩa.
100% fallback không được tính thành công LLM. `operator_review_required` chỉ có
nghĩa evidence đủ để người vận hành xét tiếp; không phải tự bật hoặc production sign-off.

Trước khi bật mặc định cần nghiệm thu facts/citation/đủ ý và cải thiện có review,
fallback/rollback, chấp nhận latency trên máy demo, scope ngành/phiên bản và hai
quyền người dùng. Review AI/dev hiện có không phải holdout hoặc xác minh học vụ.
Không sửa receipt/gold/prompt của run đã đo để đổi quyết định; dùng phiên bản/run mới.

## Khởi động ở trạng thái tắt

Chạy từ root bằng môi trường Python của dự án, trong terminal dành riêng cho demo:

```powershell
$env:HUS_LLM_ENABLED='false'
python -m uvicorn app.hus.demo:app --env-file .env --host 127.0.0.1 --port 8011
```

`--env-file .env` nạp key ở server nếu có, không in key ra console. Biến đã đặt trong
process environment ưu tiên hơn giá trị file; `HUSLLMSettings` không tự nạp `.env`.
Cờ false không yêu cầu key/model/URL hợp lệ để trả bản trích nguồn. Import/startup
không gọi provider. Demo loopback này không phải cấu hình public deployment.

Từ terminal khác, kiểm khả năng cấu hình, không phải kiểm mạng/quota Google:

```powershell
Invoke-RestMethod http://127.0.0.1:8011/hus/config | Select-Object llm_rewrite_available
```

Khi tắt, giá trị là false; UI checkbox diễn đạt bị disable sau khi tải lại trang.
Gửi câu RAG vẫn trả nguồn. F3 vẫn cần quyền kiến thức AI riêng.

## Khởi động có LLM sau khi được nghiệm thu

Khi evidence/run mới đạt và người vận hành đã chấp nhận, dừng riêng process demo
đó bằng Ctrl+C, rồi khởi động trong chính terminal với:

```powershell
$env:HUS_LLM_ENABLED='true'
python -m uvicorn app.hus.demo:app --env-file .env --host 127.0.0.1 --port 8011
```

Backend cần key riêng `HUS_LLM_API_KEY` và endpoint
`https://generativelanguage.googleapis.com/v1beta/openai`, model đã ghim cùng phép đo.
Không đưa key vào HTML/JS/payload, không in `.env`, không tái sử dụng key của advisor.
`llm_rewrite_available=true` chỉ xác nhận cấu hình HTTPS Google hợp lệ, không xác
nhận key/quota/mạng đang hoạt động. Phép kiểm kết nối live mới cần cohort/budget rõ.

Tải lại UI. Người dùng vẫn phải tự bật **AI diễn đạt từ nguồn**; F3 cần thêm
**Cho phép kiến thức AI tham khảo**. Server true không thay quyền người dùng.
Chỉ `generation.used=true` là bản sinh được hiển thị; fallback giữ bản trích nguồn.
Basic chat/clarification/no-information không gọi model.

## Rollback về bản trích nguồn

1. Dừng riêng process demo; giữ nguyên source/release/index/key/file cấu hình.
2. Trong terminal sẽ khởi động lại, đặt `$env:HUS_LLM_ENABLED='false'` rồi chạy lại
   lệnh uvicorn ở phần trạng thái tắt. Đặt biến ở terminal khác hoặc sửa file khi
   process cũ còn chạy không cập nhật môi trường đã nạp của process đó.
3. Tải lại UI để nhận config false, tắt hai checkbox và xóa hội thoại của tab.
4. Kiểm `/hus/config` có `llm_rewrite_available=false`. Gửi cùng câu RAG: API trả
   ba key cũ `mode/reply/hus_answer`, không `generation`; facts/citation/quote/review
   và câu canonical giống trạng thái chưa bật, không gửi request Google.

Rollback có hiệu lực cho request vào sau khi process nhận cấu hình tắt. Request
đã chạy với cờ bật có thể hoàn tất theo cấu hình cũ; không hứa hủy provider hoặc
xóa câu đã hiển thị. Shutdown cần để process cũ kết thúc trước khi dùng process mới.
Timeout là20s **mỗi pha HTTPX**, không phải deadline tổng20s. Không retry tự động.
Lỗi canonical vẫn503 ở cả bật/tắt; rollback model không sửa nguồn hỏng.

## Bằng chứng và phép đo

L5 v4 lịch sử đã đo provider thật trên máy này: 16 bản dùng p50/p95=4,087/6,456s;
8 fallback p50/p95=3,389/6,410s, không gồm pacing5s. Tổng35.265 token, trong đó
16.393 token cho fallback. Đây là protocol v2, không phải latency/chất lượng v3
hoặc full HTTP SLO. Chưa có phép đo provider mới trên code baseline sau sửa.

L6 kiểm API off→on→off và fallback→off bằng RAG/adapter/client thật với transport
provider giả, không dùng key Google. Các test chứng minh contract rollback và quyền;
thời gian mock không được gọi là latency model live. Không có lời gọi Google mới
trong L6. Xem [L5](RAG_LLM_L5_2026_11_10.md) và [L6](RAG_LLM_L6_2026_11_10.md).
