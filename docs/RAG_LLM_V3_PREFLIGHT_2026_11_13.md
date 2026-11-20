# L5 v3 — prepare lại đạt trước lượt Google13/11

**Sau sửa diagnostic/circuit:** prepared r1 dưới đây đã khác pins hiện tại.
[Prepared r2 và chẩn đoán offline](RAG_LLM_ACCESS_DIAGNOSTIC_2026_11_13.md) giữ
nguyên baseline/retrieval/payload, chưa gọi Google mới; mọi budget cũ đã hết.

**Cập nhật sau collection:** ngân sách mới đã được duyệt và dùng hết24 calls;
24 HTTP403,0 used/24 fallback,12 controls không gọi. LLM vẫn tắt.
[Kết quả live, review và xử lý tiếp](RAG_LLM_L5_V3_2026_11_13.md).
Phần dưới ghi trạng thái và đề nghị tại thời điểm preflight, trước collection.

Ngày **13/11/2026**, nhánh `hus-llm-rag`, HEAD nền `f61b0fd` + WIP được ghim
bằng hash. **Prepared mới khớp baseline hiện tại**; v4/lexical/LLM off giữ nguyên.
Chưa gọi Google hoặc bật L6. Ngân sách24 calls lịch sử đã hết.

## Artifact mới và kết quả preflight

- [Source pack](../data/hus/evaluation/llm_v3_v4_dev_20261113_r1/pack.json),
  [exact A/retrieval/pins/prompts](../data/hus/evaluation/runs/llm_v3_v4_prepared_20261113_r1/prepared.json),
  [receipt](../data/hus/qa/20261113/llm_v3_preflight_r1/report.json).
- Cohort dev đã lộ gồm36 ca `L5V4-Q001`–`Q036`: **8 F1/8 F2/8 F3+12 controls**.
  Mỗi ngành6 positive; tổngCS8/DS12/Math8/MI8. Đây là prepare mới cho cùng câu
  diagnostic, không phải câu hỏi/holdout mới hoặc bộ A7 mới.
- **36/36 source audits,24/24 prompt hợp lệ**, 12 controls không có prompt;
  không preflight fallback. Tổng **98.268 prompt chars**, mỗi ca2.711–7.328,
  dưới12.000. F1/F3 `hus-llm-document-v3`, F2 `hus-llm-evidence-v1`.
- **67 test evaluator/budget/readiness đạt**, một cảnh báo Starlette/httpx có sẵn.
  Không sửa product/tool code hoặc viết lại source/gold để đạt; không chạy full repo.
- **2.603 file** dữ liệu/runtime/static có trước giữ SHA; A7 mới và L5 lịch sử
  cached replay tái hiện. Socket bị chặn trong prepare/audit: **0 lần thử mạng**.
  Không đọc `.env`/template/key, account/bảng điểm/DB/advisor.

| Binding | SHA-256 |
| --- | --- |
| Prepared manifest | `0e111799ed0e172653c1bfe6bb6bedb0f3ff9e79aa8ffa020d12e15399afe2a6` |
| Pins JSON canonical | `c8b580a7630e5e37891ff734e667f9e7a55772a1daaf2a667359d14f13b1edc3` |
| Source pack manifest | `8e8b0c0a8fb73c840685c756a3216e578072640b71260c452a2ef828464d69ca` |
| Payload export manifest | `860dca2adecd6b352ef0055a66336fa0f092d1ee1ae807393bde2ccdc2839f5b` |
| QA manifest | `7516def964539cdedce0470740e662e73dc84c90f0793be365e722660880d714` |

## So với prepared cũ và quyền gửi dữ liệu

Hai file guard/routing đã đổi so với prepared12/11; pins cũ không hợp lệ cho
collection hiện tại. Tuy nhiên, trên **cohort L5 này**, exact A, effective request,
retrieval trace và prompt của36 ca đều không đổi. Toàn bộ export24 payload
**khớp byte** với payload đã được root đọc trong [preflight trước](RAG_LLM_V3_PREFLIGHT_2026_11_12.md).

Đã kiểm lại24 allowlist/binding/question/release/scope/hash. Reuse review nội
dung payload cũ nhờ byte equality; không ghi là đã đọc thủ công24 payload thay
đổi mới. Chỉ system/user và câu hỏi/bằng chứng công khai từ một snapshot; không
history, account, bảng điểm, key hoặc tool/action. Export không chứa auth header,
lưu local tại `backups/hus_l5_v3_prepare_20261113/payloads_r1/`.

B sẽ chỉ rewrite **chính A đã lưu**, không retrieval lại hay đổi snapshot.
Runner kiểm pins trước/sau collection. Nếu runtime/data/prompt/config liên quan
đổi tiếp thì prepare lại; giữ nguyên mọi pack/run/review/receipt đã seal.

Bốn ca F3 dài Q005/Q013/Q021/Q029 vẫn19–23 leaves/39–41 units; ba ca MAT3148
dùng cùng nội dung ở scope khác nhau. Q022 giữ bốn bullet mục tiêu, Q025 giữ cả
năm1993/tên cũ và ý cập nhật chương trình. Preflight/copy JSON không chứng minh
model sinh đủ dưới1.024 token, có gain hoặc entailment thật.

## Ngân sách đề nghị tại preflight — sau đó đã duyệt và dùng hết

Đề nghị **tối đa24 Google calls `gemini-3.5-flash-lite`** cho đúng prepared mới:
8 F1/8 F2/8 F3,12 controls không gọi. Endpoint trực tiếp
`https://generativelanguage.googleapis.com/v1beta/openai`; key chỉ ở backend,
không in/chỉnh key. Tổng98.268 prompt chars; request cap **1.024 output token/call,
24.576 cả lượt**. Input token và chi phí thực tế chưa biết; chưa gọi tokenizer/provider.

Cách nhau ít nhất5 giây, một call đồng thời/process, không retry/redirect/stream
hoặc đổi model; ngừng gọi tiếp sau HTTP429. HTTPX20s **mỗi pha**, không phải
deadline tổng20s. Giữ LLM mặc định off sau phép đo.

Sau duyệt ngân sách: kiểm pins → collect run mới → root đọc exact A/B và mọi
fallback → ghi model thực/prompt hash/token/latency/lỗi, tách **used/fallback**
và ca stress. Không tính fallback/mock là thành công model, không đổi guard,
retrieval, gold hoặc budget giữa phép so sánh.

**L6 vẫn keep_disabled.** Checker v4 đã nối; assessment live lịch sử còn
`pins_changed/readability_regressed`. Chỉ xét bật sau gain/bảo toàn ý thật và
operator nghiệm thu content/fallback/latency trên máy demo. A7 hiện vẫn chưa
đạt toàn bộ (Q002/Q003/Q011); prepare L5 không giải quyết các điểm đó. Chưa có
live output v3, human/operator acceptance, commit/push hoặc deploy mới.
