# L5 protocol v3 — đã prepare, chờ ngân sách Google mới

Đã có [prepared/preflight thay thế ngày13/11](RAG_LLM_V3_PREFLIGHT_2026_11_13.md)
khớp baseline hiện tại. Báo cáo này và artifact12/11 giữ nguyên làm lịch sử.

**Sau lần sửa ba ca A7 ngày12/11:** prepared trong báo cáo này không còn khớp
pins runtime. Giữ nguyên pack/receipt lịch sử; cần prepare/preflight mới trước
collection và duyệt budget. [Diagnostic baseline mới](RAG_A7_LANGUAGE_FOLLOWUP_2026_11_12.md).

Ngày 12/11/2026 · Nhánh `hus-llm-rag` · HEAD nền `f61b0fd` + WIP có hash trong pins.

**Preflight 36/36 đạt, chưa gọi Google.** Giữ `CURRENT` v4, lexical/BM25 và
`HUS_LLM_ENABLED=false`. Ngân sách 24 calls lịch sử đã hết; receipt này không
cho phép lượt live mới hoặc bật L6.

## Cohort và bằng chứng đã đóng băng

- [Source pack](../data/hus/evaluation/llm_v3_v4_dev_20261112_r1/pack.json),
  [prepared A/pins/prompt hash](../data/hus/evaluation/runs/llm_v3_v4_prepared_20261112_r1/prepared.json),
  [receipt preflight](../data/hus/qa/20261112/llm_v3_preflight_r1/report.json).
- 36 ca `L5V4-Q001`–`Q036`: **8 F1 + 8 F2 + 8 F3 + 12 controls**.
  Mỗi ngành có sáu positive; tổng số ca lần lượt CS8, DS12, Math8, MI8.
  Controls gồm opt-in, thiếu nguồn/ngoài phạm vi, clarification và basic chat.
- **Dùng lại đúng các câu diagnostic đã lộ của pack v4 cũ**, không tạo câu hỏi
  holdout mới. Pack/prepared/pins mới cho protocol v3 trên baseline hiện tại;
  AI-authored/nonblind, human review=0. Không dùng chênh lệch với run v2 cũ
  để quy kết nhân quả riêng cho prompt/model vì code baseline cũng đã đổi.
- Release `hus-data-20261111-v4`, SHA
  `ed4c1ccb93da50829c6b6b960f22d1a077c433ed0a55c3a1e1bed832c1baf463`.
  Retrieval lexical, index null. F2 lookup canonical; F3 vẫn `generated/needs_review`.

| Binding | SHA-256 |
| --- | --- |
| Source pack manifest | `8e8b0c0a8fb73c840685c756a3216e578072640b71260c452a2ef828464d69ca` |
| Prepared manifest | `154fa5b126abfd05cedcdeeea3bb7d90c6597c329dd80fd21c12c1f57ccbbbc8` |
| Pins JSON canonical | `d441a8d4a478ffe512f4957915b1b1b002a9bc348549452f5a7db48549d1f050` |
| Payload export manifest | `860dca2adecd6b352ef0055a66336fa0f092d1ee1ae807393bde2ccdc2839f5b` |

Đã lưu A và trace retrieval một lần. B sẽ diễn đạt **chính A đã lưu**, không
retrieval lại hoặc đổi snapshot. Runner kiểm pins trước/sau collection; thay
runtime/data/prompt/evaluator/config liên quan sẽ cần prepare mới và ngân sách
đúng cohort, không sửa artifact đã seal.

## Kết quả offline

Source audit **36/36**; đủ điều kiện tạo prompt **24/24**, 12 controls không có
prompt. F1/F3 dùng `hus-llm-document-v3`, F2 giữ `hus-llm-evidence-v1`.
Tổng **98.268 prompt chars**, mỗi ca **2.711–7.328**, dưới trần12.000.

| Ca F3 dài | Leaves / units | Prompt chars | Exact-copy JSON chars |
| --- | --- | --- | --- |
| Q005 — CS MAT3148 | 19 / 39 | 6.789 | 2.710 |
| Q013 — DS MAT3148 | 19 / 39 | 6.769 | 2.710 |
| Q021 — Math MAT3311 | 23 / 41 | 7.328 | 2.842 |
| Q029 — MI MAT3148 | 19 / 39 | 6.824 | 2.710 |

Ba ca MAT3148 dùng cùng nội dung ở scope ngành khác, không phải ba chủ đề độc lập.
Q022 giữ năm leaf gồm tiêu đề/bốn bullet mục tiêu; Q025 giữ cả năm1993/tên cũ và
ý chương trình liên tục cập nhật. Những con số exact-copy chỉ mô tả biểu diễn
nguồn, **không chứng minh model thật sinh đủ dưới 1.024 token hoặc có gain**.

Root AI đã đọc đủ24 payload câu hỏi/bằng chứng; đối chiếu đúng builder allowlist,
release/scope/hash. Chỉ hai message system/user, không history, tài khoản, bảng
điểm, key hoặc tools. File kiểm payload nằm local tại
`backups/hus_l5_v3_prepare_20261112/payloads_r1/`; không chứa header xác thực.
Không đọc/so sánh key hoặc hai file cấu hình người dùng quản lý.
Review này kiểm dữ liệu chuẩn bị gửi, chưa phải review ngữ nghĩa output sinh.

**67 test evaluator/budget/readiness đạt**, một cảnh báo Starlette có sẵn;
không chạy full repo. 2.557 file dữ liệu/runtime/static cũ giữ SHA; replay L5 v4
review và A7 mới tái hiện. Chuẩn bị/audit chặn socket: **0 lần thử mạng**.
Không sửa runtime/retrieval, nguồn, gold, run/review cũ hay selector.

## Ngân sách đề nghị và phần còn lại

Chờ người dùng cho phép riêng **tối đa24 lời gọi `gemini-3.5-flash-lite`**:
8 F1/8 F2/8 F3; 12 controls không gọi. Endpoint Google HTTPS trực tiếp
`https://generativelanguage.googleapis.com/v1beta/openai`; dùng key backend hiện
có, không in/chỉnh key. Cách nhau ít nhất5 giây, một call đồng thời/process,
không retry hoặc đổi model, ngừng gọi tiếp sau HTTP429. Giữ timeout HTTPX20s
mỗi pha, không phải deadline tổng20s. Tối đa1.024 output token/call, **24.576**
cho cả lượt; input token và chi phí thực tế chưa biết.

Sau duyệt ngân sách mới: kiểm lại pins → collect vào run mới → đọc **exact A/B
và mọi fallback** → ghi model thực/prompt hash/token/latency/lỗi, tách used/fallback
và bốn ca stress. Không chấm fallback/mock thành thành công sinh LLM; giữ tiêu
chí facts/citation/đủ ý/bullet, không hạ guard hay sửa gold để đổi điểm.

Checker v4 đã nối. Assessment lịch sử vẫn `keep_disabled` vì `pins_changed` và
`readability_regressed`; preflight mới không thay thế live/review. Chỉ xét L6
sau gain/bảo toàn ý thật và operator nghiệm thu nội dung/fallback/latency trên
máy demo. Chưa bật mặc định, commit/push hoặc deploy.
