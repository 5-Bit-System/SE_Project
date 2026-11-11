# Vận hành LLM HUS: bật có điều kiện và rollback

Phạm vi: chatbot hỏi đáp độc lập `app.hus.demo:app`; không dùng server/chatbot
recommendation hoặc tài khoản/bảng điểm. Google Gemini HTTPS trực tiếp, không cần
9Router. API key chỉ nằm trong môi trường/file cấu hình riêng ở backend.

## Trạng thái hiện tại

**Giữ `HUS_LLM_ENABLED=false`.** L5 có19/24 bản sinh dùng và5 fallback, nhưng một
bản dùng (`DEV-Q025`) bỏ ý nguồn. Chưa đạt điều kiện đủ ý để bật mặc định L6.
Các lệnh khởi động với cờ true bên dưới dành cho đợt nghiệm thu tương lai đã đạt
và được người vận hành chấp nhận; không phải chỉ dẫn bật ở trạng thái hiện tại.

Guard coverage v2 đã chặn diagnostic thiếu ý này offline. Chưa có phép đo live
mới, và code/prompt pins đã khác run L5 cũ; phải prepare/run/review mới trước khi
xét bật. Không đổi assessment/review cũ thành kết quả sau sửa.

## Kiểm bằng chứng trước khi quyết định

```powershell
python -m tools.check_hus_llm_readiness --review-run data/hus/evaluation/runs/llm_l5_ai_review_20261110_r1 --out data/hus/evaluation/runs/llm_l6_readiness_20261110_r1
```

Dùng một tên output mới nếu đã tồn tại. Công cụ chỉ replay/đọc cache và hash nguồn/
code; không gọi model/retrieval, đọc key, sửa `.env` hay đổi cờ. Bằng chứng có lỗi
binding/hash sẽ bị từ chối; code/source/model khác run đo không đủ điều kiện reuse.
Report tách bản sinh dùng/fallback, lý do, ca thiếu ý và latency model thực đã đo.
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

L5 đã đo provider thật trên máy này, dùng19 bản: incremental p50/p95=2,692/10,444s;
5 fallback p50/p95=5,070/6,248s, không gồm pacing5s. Tổng23.539 token có cả6.482
token cho output bị loại. Đây không phải full HTTP SLO hoặc tỷ lệ chất lượng mới.

L6 kiểm API off→on→off và fallback→off bằng RAG/adapter/client thật với transport
provider giả, không dùng key Google. Các test chứng minh contract rollback và quyền;
thời gian mock không được gọi là latency model live. Không có lời gọi Google mới
trong L6. Xem [L5](RAG_LLM_L5_2026_11_10.md) và [L6](RAG_LLM_L6_2026_11_10.md).
