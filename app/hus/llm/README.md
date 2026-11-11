# HUS LLM — L1/L2/L3/L4/L5/L6

Client HTTP gọi trực tiếp Google Gemini cho chatbot hỏi đáp HUS, dùng `httpx`
đã có trong dự án. Không cần cài hoặc chạy proxy local.
`config.py` đọc riêng `HUS_LLM_*`; `client.py` gửi Chat Completions và trả text.
Import package, đọc cấu hình và khởi tạo client đều không kết nối provider.
Client không import cấu hình hoặc dịch vụ recommendation.

Mẫu cấu hình trong `.env.example`:

```dotenv
HUS_LLM_ENABLED=false
HUS_LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
HUS_LLM_MODEL=gemini-3.5-flash-lite
HUS_LLM_API_KEY=
```

`HUSLLMSettings.from_env()` chỉ đọc môi trường hiện tại, không tự tải `.env`.
Đặt API key Google AI Studio vào `HUS_LLM_API_KEY` trong môi trường server khi bật;
không dùng key proxy hoặc tự lấy lại `GEMINI_API_KEY` của recommendation.
Model dùng ID trực tiếp của Google, không có tiền tố provider `gemini/`.
Model mặc định là `gemini-3.5-flash-lite`; có thể đổi `HUS_LLM_MODEL` theo quyền và
quota của key. Mặc định vẫn tắt. Smoke test trực tiếp ngày 10/11/2026 đã nhận
HTTP 200 và câu trả lời `OK` từ `gemini-3.5-flash-lite`: 1,285 giây, 9 token
(8 input + 1 output). Chỉ kiểm kết nối bằng câu hỏi tổng hợp ngắn, chưa kiểm
tích hợp hoặc chất lượng câu trả lời RAG. Receipt local tại
`backups/llm_live_smoke_20261110/result_20261110T044003795961Z.json` (ignored).
Cờ bật chấp nhận `true/1/yes/on`, cờ tắt `false/0/no/off` (không phân biệt hoa thường).
Giá trị khác, URL sai, model trống hoặc bật khi thiếu key gây `ValueError`.
Key không hiện trong `repr(settings)` hoặc thông báo lỗi.

```python
from app.hus.llm import HUSLLMClient, HUSLLMError, HUSLLMSettings

client = HUSLLMClient(HUSLLMSettings.from_env())
try:
    text = client.complete([
        {'role': 'system', 'content': 'Chỉ diễn đạt bằng chứng được cung cấp.'},
        {'role': 'user', 'content': 'Câu hỏi và bằng chứng đã chọn.'},
    ])
except HUSLLMError as error:
    reason = error.code
```

Chỉ `complete()` khi bật mới gửi `POST <base_url>/chat/completions`, dùng Bearer key,
model đã cấu hình, messages dạng text, `stream=false`, `max_tokens=1024`.
Timeout HTTPX là 20 giây cho từng pha connect/read/write/pool, không phải tổng thời
gian toàn request. Không tự retry hoặc theo redirect; bỏ proxy/netrc từ môi trường.
Tài nguyên HTTP được tạo và đóng trong mỗi lần gọi.

`complete()` giữ API text đã trim. `complete_result()` giữ nguyên content thô để
kiểm ngân sách, đồng thời trả model/usage từ envelope provider; không lấy model
từ JSON do model sinh hoặc suy model đã trả từ cấu hình yêu cầu. Usage chỉ có các
counter số nguyên không âm đã biết; thiếu usage thì giữ unknown, không tự tính.
Tool/function-call hoặc usage output báo vượt 1.024 token bị từ chối.

Lỗi có `code`: `disabled`, `http_error`, `timeout`, `transport_error`,
`invalid_response`; lỗi HTTP có thêm `status_code`. Không trả body lỗi provider,
prompt hoặc key trong thông báo lỗi. Phản hồi phải có text không rỗng và
`finish_reason=stop`; phản hồi cắt dở hoặc lọc nội dung bị từ chối.

## L2 — Quyền và hợp đồng

API `/hus/chat` nhận thêm `allow_llm_rewrite`, strict boolean, mặc định false.
Quyền này độc lập với `allow_generated_reference`. Nếu server hoặc người dùng tắt
LLM, response giữ nguyên ba trường cũ `mode`, `reply`, `hus_answer`; không thêm
`generation: null`. Khi cả hai bật, metadata `generation` ghi `used`,
`requested_model`, `model` do adapter báo khi được dùng và `fallback_reason`.

Chỉ F1/F2/F3 đã `answered` và có citation được gọi adapter. F3 cần cả hai quyền;
basic chat, cần làm rõ và không có thông tin không gọi adapter. Adapter nhận bản
sao sâu của request hiệu lực và đáp án canonical, không có key hoặc lịch sử chat.
`hus_answer` luôn giữ nguyên, gồm reply gốc, facts, quote, URL/hash, review và cảnh báo.

Hợp đồng nội bộ trong `contracts.py`:

- `HUSTextRewrite`: kết quả F1/F3 đã được adapter L3 kiểm; backend giữ cảnh báo nguồn.
- `HUSF2Presentation`: chỉ `style=direct|explain_source` và model; backend chèn nguyên
  khối đáp án F2, không nhận giá trị tín chỉ/tiên quyết hoặc văn bản thay thế tự do.
- Cả hai được kiểm schema lại ở ranh giới L2; schema đúng không chứng minh entailment.

`chat(..., rewriter=...)` chỉ nhận adapter do server cung cấp, không phải tham số HTTP.
**Pipeline L3 hiện đã đăng ký mặc định**, nhưng chỉ được tạo sau các guard L2.
Khi server/người dùng đều bật và có đáp án đủ nguồn, API có thể gọi Gemini bằng
bundle/prompt đã ràng buộc. `pipeline_unavailable` chỉ còn cho trường hợp factory
không cung cấp adapter. Lỗi cấu hình/provider/adapter giữ bản trích nguồn;
lỗi canonical/snapshot/scope vẫn fail closed (API 503).

Các lý do bỏ qua: `basic_chat`, `not_answered`, `no_sources`, `f3_opt_out`,
`ineligible_dataset`. Các lý do fallback: `configuration`, `pipeline_unavailable`,
`invalid_result`, `adapter_error`, `provider_error`, hoặc mã lỗi L1 đã nêu.
Khi lỗi, `model=null` để không báo nhầm model đã được dùng.

## L3 — Bundle, prompt và kiểm đầu ra

`evidence.py` kiểm binding release/scope từ một snapshot,
kể cả provenance lồng của F2 và môn F3 được suy ra từ câu hỏi. Chỉ gửi câu hỏi,
scope, facts được whitelist, ID/nội dung/review/origin và hash quote của các nguồn
đã chọn. Không serialize metadata/provenance tùy ý, locator/URL/path, account,
transcript, history hoặc cấu hình key. `prompts.py` tạo đúng hai messages system/user;
nguồn và câu hỏi nằm trong JSON dữ liệu không đáng tin về mặt chỉ dẫn, không có tool.

Mặc định F1/F3 dùng **document/protocol v3**. `document.py` chia quote tại LF/CRLF
thành các khối nguồn có ID cục bộ, giữ mọi nguồn/unit/offset và literal prefix ở
backend. Wire gửi mỗi đoạn chữ một lần, không lặp cả full quote và leaf text.
F2 vẫn dùng bundle/facts hiện có. Đầu ra F1/F3 phải là JSON strict:

```json
{"kind":"rewrite_v3","items":[{"id":"b001","text":"Ý được diễn đạt từ đúng khối nguồn"}]}
```

Phải trả đủ và đúng mỗi ID một lần, không gộp/bỏ khối. Backend phục hồi marker,
indentation, từng bullet, thứ tự và citation; text model không có newline hoặc
list/heading/HTML/URL/citation tự tạo. Anchor lấy nội bộ từ span nguồn; mở rộng
anchor ngắn không cấp thêm quyền mượn atom từ khối bên cạnh. Kiểm toàn document
trước khi hiển thị; sai/thiếu/quá budget thì trả nguyên canonical.

**Policy v2 — giữ từ ngữ theo từng đơn vị nguồn:** `coverage.py` tách quote tại
ranh giới câu, xuống dòng và dấu chấm phẩy, giữ span gốc. Mỗi đơn vị phải có toàn
bộ token từ ngữ theo thứ tự trong text của đúng khối và citation; anchor phải chứa
nguyên đơn vị. Chuẩn hóa NFKC/casefold, giữ dấu tiếng Việt,
phủ định, điều kiện và cả từ chức năng; không stopword/synonym/threshold theo chủ đề.
Anchor đầy đủ hoặc từ của citation khác không bù được ý vắng trong text. Không đủ
coverage → `evidence_coverage`, giữ canonical, không retry. V3 giữ guard từ ngữ v2,
đổi cách đóng gói/kiểm layout; không phải paraphrase tự do hoặc chứng minh entailment.
V3 còn giữ chuỗi ký hiệu/toán tử trong text có từ và vị trí tương đối với từ nguồn;
không cho đổi/bỏ/thêm hoặc dời `≠`, `≥`, dấu phép tính, ký hiệu tập hợp… để đảo nghĩa.
Chuẩn hóa Unicode/dấu trừ vẫn được; đây chưa phải chứng minh mọi quan hệ ngữ nghĩa.

Trần v3: 64 khối/128 unit/document, 3.000 ký tự/khối gồm prefix được phục hồi,
kiểm cả trước/sau model. Giữ 12.000 prompt chars, 8.192 raw chars, 1.024 output
token; ID gọn chưa chứng minh mọi F3 dài sẽ vừa token. `build_bundle()` và validator
v2 còn cho consumer legacy rõ phiên bản; default adapter không tự chấp nhận output
`rewrite/points/anchor_quote` trên một lời gọi v3.

Diagnostic nội bộ chỉ gồm enum/count: finish reason chuẩn hóa, loại/độ dài content,
tool-presence, validation stage và ID khối đã biết. Không lưu raw output bị loại,
provider error text/header hoặc ID lạ. Response API giữ reason công khai hiện có.

Đây là ràng buộc bảo thủ: diễn đạt đồng nghĩa hoặc đổi thứ tự từ hợp lý vẫn có
thể bị fallback; thêm câu nối trung tính/đổi case/spacing vẫn được nếu giữ các từ.
Không chứng minh entailment, quan hệ/phủ định hoặc ngăn mọi bổ sung sai. Giữ các
giới hạn cũ, không tăng budget để làm đẹp kết quả; phải đo lại L5 về chất lượng,
readability, token/latency và tỷ lệ fallback. Không dùng test thay review nội dung.

Đầu ra F2:

```json
{"kind":"facts","style":"direct","fact_keys":["các key facts đã cấp"],"citation_ids":["mọi ID đã cấp"]}
```

Style chỉ `direct|explain_source`, key/ID phải phủ đúng bộ đã cấp và không lặp.
Không nhận giá trị mới hoặc free text F2. Sau kiểm tra, adapter chỉ trả kiểu L2;
backend giữ nguyên đáp án F2, bao gồm null/unknown/conflict/unresolved.

Ngân sách không truncate: nội dung system+user tối đa 12.000 ký tự Unicode;
output content thô tối đa 8.192 ký tự, kể cả whitespace. Request cap 1.024 token;
đây không phải benchmark hoặc deadline tổng. JSON extra/duplicate key, NaN,
fence/commentary hoặc scalar sai đều bị từ chối. Key cấu hình xuất hiện trong
prompt hoặc output cũng bị chặn, không in body lỗi.

Các mã fallback L3: `prompt_budget`, `output_budget`, `invalid_output`,
`evidence_coverage`, `unsafe_prompt`. Khi chấp nhận kết quả, `generation` có thêm
`prompt_sha256` (hash chuẩn tắc messages) và usage nếu provider cung cấp.
`used=false` nghĩa là không dùng bản sinh; vẫn có thể đã phát sinh request/token
trước khi validator từ chối, không được coi mọi fallback là model trả lời đúng.

**Giới hạn:** ID/anchor/atom và retention từ ngữ không chứng minh entailment hoặc
đủ ý ngữ nghĩa. L5 v1 đã đo36cặp/24live:19used/5fallback, có1 thiếu ý lọt validator.
Policy v2 chặn diagnostic đó offline; chưa có A/B live mới. Pins của run cũ không
khớp runtime mới, cần prepare/run/review mới; không ghi lại số đo hoặc review cũ.
Giữ mặc định tắt. [Hồ sơ sửa coverage](../../../docs/RAG_LLM_QUALITATIVE_COVERAGE_2026_11_10.md). Xem
[kế hoạch RAG](../../../docs/RAG_PROGRESS_AND_NEXT_PLAN.md).

## L4 — Giới hạn và quyền trên giao diện

`capacity.py` giữ một slot không chờ trong mỗi process, bao quanh toàn bộ adapter
Q&A sau guard L2, kể cả adapter server truyền vào. Request đến khi bận nhận ngay
bản trích nguồn với `generation.fallback_reason=busy`; không xếp hàng/retry.
Slot được trả trong `finally` khi adapter hoàn tất hoặc lỗi. Đổi ngành/abort trên
trình duyệt không giải phóng sớm công việc đang chạy ở server. Đây không phải
giới hạn chung cho nhiều worker hoặc các lời gọi client độc lập ngoài Q&A.

Timeout vẫn **20 giây mỗi pha HTTPX**, không phải deadline tổng 20 giây.
Input/output/token budget giữ nguyên L3. Timeout, HTTP/quota, sai output hoặc
vượt budget đều giữ bản trích nguồn; canonical hỏng vẫn 503. Lỗi HTTP bổ sung
`generation.http_status` số nguyên an toàn để phân biệt 429; không gửi body lỗi.
`used=false` vẫn có thể đã tiêu token; không tự retry sau quota/timeout.

GET `/hus/config` có boolean `llm_rewrite_available`, không lộ key/model hoặc gọi
provider. Giao diện chỉ cho bật khi cấu hình hợp lệ, server bật và endpoint HTTPS
thuộc `generativelanguage.googleapis.com`, phù hợp lời đồng ý gửi tới Google.
Đây là khả năng cấu hình, không phải kiểm tra mạng/quota/provider đang hoạt động.

Checkbox **“AI diễn đạt từ nguồn”** mặc định tắt, độc lập quyền F3. Disclosure nêu
rõ gửi câu hỏi và bằng chứng đã chọn tới Google, không gửi lịch sử/tài khoản/bảng
điểm. Chỉ gửi `allow_llm_rewrite=true` khi người dùng bật; catalog không cấp quyền.
Kết quả `generation.used=true` mới có nhãn AI; khi đã yêu cầu nhưng fallback thì
hiện **“Bản trích nguồn”** kèm lý do dễ hiểu. Basic chat/clarification/no-information
không gắn nhãn diễn đạt. F3 luôn giữ citation **“kiến thức AI”**.
Đổi ngành tắt cả hai quyền, xóa hội thoại và bỏ text/metadata/status đến muộn,
kể cả khi transport bỏ qua abort. Hội thoại và quyền chỉ nằm trong bộ nhớ tab.

Kiểm thử backend bằng Events/HTTP giả lập; trình duyệt Chromium chạy qua RAG và
adapter thật với transport provider giả, gồm mobile/bàn phím và phản hồi muộn.
Không gọi Google thật trong L4. [Báo cáo L4](../../../docs/RAG_LLM_L4_2026_11_10.md).

Test offline: `python -m pytest tests/hus/llm -q`.

## L5 — Đo A/B nội dung với snapshot bất biến

`tools/evaluate_hus_llm.py` chuẩn bị A bằng lexical một lần, lưu request hiệu lực,
đáp án canonical, retrieval trace và source audit. B gọi chính adapter L2/L3 trên
đáp án A đã lưu; không chạy lại retrieval. Bộ 36 ca dev đã lộ gồm 24 ca dương tính
(bốn ngành × ba family × hai field) và 12 controls; không phải holdout độc lập.
Chọn ca từ gold/request trước khi sinh B, không chọn lại theo kết quả model.

Pin code/runtime/evaluator, nguồn/release/assets, pack gốc, môi trường, model yêu cầu
và hash prompt. Kiểm pin trước/sau collection; thư mục kết quả mới, không ghi đè.
Observer ghi model/token/status thực quan sát được kể cả khi L1/L3 loại kết quả;
không lưu provider body/key. Thiếu usage giữ unknown và ghi subtotal đã biết.
Tách used/fallback/guard/not-attempted, lỗi, quota và latency provider/diễn đạt.
Latency incremental bỏ thời gian pacing của phép đo, không phải SLO production.

CLI live yêu cầu `--live --env-file`, tối đa 24 lời gọi, cách nhau ít nhất 5 giây;
429 đóng circuit trước khi đọc body, không retry hoặc chuyển model/provider.
Chỉ bật cờ trong process đo rồi khôi phục, không sửa `.env` hoặc bật LLM mặc định.
Các lệnh tạo artifact yêu cầu đường dẫn mới dưới `data/hus/evaluation/runs`:

```powershell
python -m tools.evaluate_hus_llm --prepare --out data/hus/evaluation/runs/llm_l5_prepared_20261110_r1
python -m tools.evaluate_hus_llm --run data/hus/evaluation/runs/llm_l5_prepared_20261110_r1 --live --env-file .env --max-calls 24 --out data/hus/evaluation/runs/llm_l5_google_20261110_r1
python -m tools.evaluate_hus_llm --score data/hus/evaluation/runs/llm_l5_google_20261110_r1 --review backups/llm_l5_20261110/review.json --out data/hus/evaluation/runs/llm_l5_ai_review_20261110_r1
python -m tools.evaluate_hus_llm --replay data/hus/evaluation/runs/llm_l5_ai_review_20261110_r1
```

Review template buộc nhận xét entailment/đủ ý/readability gắn hash từng cặp A/B và
target/evidence. Reviewer AI, human count zero; controls không có positive semantic
score, thiếu đáp án dương tính là incomplete. Fallback giống A không được chấm
readability tốt hơn. Review và replay chỉ đọc cache, không gọi provider/retrieval.
Luôn giữ `recommended_enabled=false`; việc hoàn thành phép đo không bật L6.
[Hồ sơ L5](../../../docs/RAG_LLM_L5_2026_11_10.md).

## L6 — Điều kiện bật và rollback

L6 hiện có checker chỉ đọc và kiểm thử rollback; **chưa bật mặc định** vì L5 có
DEV-Q025 thiếu ý định tính dù được validator chấp nhận. Không chỉnh run cũ để đạt.

```powershell
python -m tools.check_hus_llm_readiness --review-run data/hus/evaluation/runs/llm_l5_ai_review_20261110_r1 --out data/hus/evaluation/runs/llm_l6_readiness_20261110_r1
```

Dùng output mới nếu tên đã có. Checker replay/kiểm pin, live use, source/controls,
entailment/đủ ý gồm fallback và gain chỉ từ bản sinh đúng/đủ; báo `keep_disabled`
với ID thiếu ý. `operator_review_required` ở một run đạt không tự thay cờ hoặc
thay nghiệm thu vận hành. Không đọc key, không provider/retrieval hoặc sửa `.env`.

Rollback: dừng process demo riêng, đặt process env `HUS_LLM_ENABLED=false`, restart
và tải lại UI. Request sau rollback giữ exact response cũ, không gọi provider dù
request opt-in true và key vắng. Process env không tự cập nhật khi sửa file/terminal
khác. Request đã vào với cờ bật có thể hoàn tất; không hứa total20s hoặc cancellation.
Endpoint trực tiếp Google HTTPS, key chỉ server; server bật vẫn cần user opt-in và
quyền F3 riêng. [Runbook](../../../docs/HUS_LLM_OPERATIONS.md),
[hồ sơ L6](../../../docs/RAG_LLM_L6_2026_11_10.md).

Tham chiếu: [Google OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai),
[Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite),
[HTTPX transports](https://www.python-httpx.org/advanced/transports/).
