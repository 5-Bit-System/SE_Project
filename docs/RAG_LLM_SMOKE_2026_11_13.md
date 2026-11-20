# Test RAG → Gemini: HTTP503, giữ bản RAG

Người dùng cấp **tối đa1 call mới** cho `gemini-3.5-flash-lite`; đã dùng đúng1,
không retry hoặc đổi model. Google trả **HTTP503 / `UNAVAILABLE`** sau khoảng
**1,99 giây**. Không có actual model/token usage hoặc bản sinh được dùng; chi phí
chưa biết. Kết quả này không xác định lỗi key/quota và không chứng minh chất lượng
diễn đạt. Không đổi key/billing hoặc mặc định LLM tắt.

Payload là câu F1 `L5V4-Q001`: “Ra trường KHMTTT có những hướng công việc nào trong
bản chương trình đã lưu?”, cùng bằng chứng RAG công khai, **3.607 ký tự prompt**,
cap **1.024 output token**. Gọi trực tiếp Google qua endpoint OpenAI-compatible.
Key backend chỉ đọc trong bộ nhớ; không giữ raw error body hoặc text bị từ chối.

Trước call, [prepared r6](../data/hus/evaluation/runs/llm_v3_v4_prepared_20261113_r6/prepared.json)
đạt **36/36 audit**, pins hiện tại khớp. Các record giữ nguyên so với r5 ngoài
latency baseline; prompt/hash của câu test giữ nguyên. R5 vẫn là artifact lịch sử,
không sửa để hợp thức hóa pins mới.

[Receipt live](../data/hus/qa/20261113/llm_smoke_r1/report.json) ghi
`http_error`, `provider_http`, `UNAVAILABLE`, `validated_rewrite_used=false` và
fallback nguyên canonical. Đây là smoke trực tiếp adapter với baseline đã chuẩn
bị, không phải lượt browser/API đầy đủ hoặc cohort L5 A/B.

[Verification offline](../data/hus/qa/20261113/llm_smoke_verification_r1/report.json)
kiểm **3.020 file cũ nguyên SHA**, pins r6 khớp và replay lỗi503 qua `generate_reply`
bằng settings/key giả: reply và `hus_answer` giữ nguyên, metadata
`used=false/fallback_reason=http_error/http_status=503`. Replay này không gọi
Google hoặc đọc lại key, không phải call live thứ hai. Không sửa runtime/chạy lại
suite khi không có thay đổi code.

**Budget đã hết:1/1, còn0.** Call tiếp theo cần budget mới theo điều kiện đã đặt;
chưa có cohort L5 mới hoặc nghiệm thu L6. Không dùng503/fallback làm thành công
LLM, không nới validator từ một lỗi provider. Giữ v4/lexical/LLM mặc định tắt.

Manifest r6: `d0bfe7a95addc56cbd735fb225ff0f2dcfefafa1cdd732f874f41ef8f97175ca`.
Live: `93ecbaa3754a516fd7b903f6fd5f3a3d34e3de6025bf1d94497523708a976224`.
Verification: `9f3e7664be4c57eae337080ecb213fb8abb8c7240754219ce1a20c7915c82bfd`.
