# Google — smoke mới503; lần200 trước vẫn là kết quả lịch sử

**Kết quả tiếp theo14/11:** đã sửa tách prefix tiêu đề lồng và có một câu F1
HTTP200/`used=true`; dùng2/3 call mới, dừng khi thành công. Các lượt bên dưới giữ
lịch sử. [Báo cáo hiện tại](RAG_F1_LLM_WORKING_2026_11_14.md).

**Smoke mới theo budget riêng1 call:** Google trả **HTTP503/UNAVAILABLE**, provider≈1,99s,
không actual model/usage/bản sinh được dùng. Preparedr6 mới36/36 audit, pins khớp;
không retry/đổi model, key/billing/mặc định giữ nguyên. Budget1/1 đã hết. Verification
offline kiểm3.020 file nguyên SHA và replay L2 với lỗi503 giữ exact fallback;
không gọi Google thêm hoặc suy503 thành lỗi key/quota. [Báo cáo mới](RAG_LLM_SMOKE_2026_11_13.md).

## Lần200 trước và diagnostic offline

**Cập nhật offline sau bản sửa baseline:** đã bổ sung sáu nhãn `text_issue` cố định cho `output_text`, không đổi validator/fallback hoặc suy lại nguyên nhân call cũ.43 regression mới,607 kiểm LLM/UI đạt;42 ca giả giữ nguyên quyết định trước–sau. R5 nay stale trên năm runtime artifact; pins khớp nói trong phần call bên dưới chỉ là lịch sử. Không gọi Google thêm, mọi budget đã hết và L6 off. [Báo cáo offline](RAG_OUTPUT_TEXT_DIAGNOSTIC_2026_11_13.md).

**Lần gọi Google sau báo thay key trước smoke503:** người dùng báo “tôi vừa thay khóa”; đã dùng đúng **1 call**
được cấp có điều kiện. Google trả **HTTP200**, actual model
`gemini-3.5-flash-lite`, provider≈**2.738ms**. Usage thực:934 prompt token,
245 completion token, tổng1.179; output dưới cap1.024 token, chi phí chưa tính.
Điều này xác nhận truy cập trong lần gọi đó, không xác minh độc lập việc vô hiệu
key cũ hoặc chất lượng câu trả lời. [Receipt live](../data/hus/qa/20261113/google_access_after_rotation_r1/report.json).

Client nhận text866 ký tự, finish=`stop`, không tool call. Validator dừng ở
**`invalid_output`, `stage=output_text`, `leaf_id=b001`**, nên **0 bản sinh được dùng**;
fallback giữ nguyên canonical answer/facts/citation. Stage này gom kiểm text
trống, xuống dòng, marker cấu trúc, link/HTML hoặc độ dài sau phục hồi prefix.
Không lưu raw output, chưa xác định nhánh vi phạm cụ thể; không suy model sai
facts/thiếu ý hoặc nới validator từ metadata này. Chưa review entailment của
raw output, chưa có gain/L5 chất lượng hoặc nghiệm thu L6.

Trước call đã tạo [preparedr5](../data/hus/evaluation/runs/llm_v3_v4_prepared_20261113_r5/prepared.json):
36/36 source audits; toàn bộ A/request/effective/retrieval/gold/prompt/audits
giống r4, chỉ pins/timing mới. Prompt F1 `L5V4-Q001` vẫn3.607 ký tự/hash đã duyệt;
**pins r5 khớp trước/sau call**. Model/endpoint/cap giữ nguyên, không retry/đổi model.
Key backend `.env` dùng trong bộ nhớ; không in/lưu/chỉnh key hoặc billing.
Không ghi raw error/body/header/ID riêng. Không đổi cờ mặc định; L6 giữ off.

**Budget1 call mới đã dùng hết**; mọi Google call tiếp theo cần budget riêng,
kể cả retry/smoke/model-list/tokenizer. [Verification](../data/hus/qa/20261113/google_access_after_rotation_verification_r1/report.json)
xác nhận2.949 file bảo vệ nguyên SHA, fallback đúng canonical, không thêm call.
Tại lượt call/verification đó không sửa runtime hoặc chạy lại suite;564 test LLM/UI là kết quả trước, code
bindings không đổi. Bước tiếp theo là diagnostic offline `output_text/b001`;
nếu đổi code/prompt phải prepare/pin mới trước phép đo sau. Cohort L5 A/B cần
ngân sách riêng và exact output review; một HTTP200/fallback không là thành công LLM.

Manifest r5: `b63724a77396f582d29a75fcf17ada48a16592ecdd3bb5b7870215aed76b35b6`;
live: `48432218a7e8d6abbfb382b7ed5179fba9b9492e65597768eae25ea1d6ad7017`;
verification: `a5525e600db9e5d903f5094d172f03eceeccec4941491338ba92355736d3b72f`.

## Lịch sử trước khi người dùng báo thay key

**Cached readiness mới:** đã kiểm lại36 source audit của r4, chỉ hash diagnostic
lệch so với pins cũ. Prompt F1 `L5V4-Q001` vẫn đúng3.607 ký tự/hash đã review.
Đã chuẩn bị [proposal tối đa1 call](../data/hus/qa/20261113/llm_access_readiness_r1/proposal.json)
và [receipt offline](../data/hus/qa/20261113/llm_access_readiness_r1/report.json),
người dùng đã trả lời **“Chưa thay key”** và **“Cho phép tối đa1 call sau khi thay key”**.
Tại bước này budget có điều kiện đã cấp, chưa dùng; sau đó đã dùng ở phép kiểm
HTTP200 phía trên. Receipt readiness là snapshot trước khi duyệt budget.
**Chưa đọc key, tạo preparedr5/preflight mới hoặc gọi Google**; đây không phải
cohort L5 mới hoặc xác minh quyền.2.945 file bảo vệ nguyên SHA,0 request/search/
provider. Tại thời điểm receipt này, cần operator xác nhận thay key mới tạo thư mục prepared và kiểm pins trước
call; L6 off. Manifest `a9b8a0e7fb6aa1d88cfed4c144ed6d89472b17163e9b18b96447c39c14036382`.

**Bản vá offline sau hai call:** parser production đã nhận top-level array chứa
đúng một dictionary, rồi dùng bộ phân loại nhãn cố định hiện có. Không mở mảng
nhiều phần tử, phần tử không phải object hoặc mảng lồng nhau; không tìm đệ quy
qua body. Giữ giới hạn16KiB body/8.192 ký tự message, gate HTTP403 và không mở
mảng response thành completion thành công. Không giữ message/header/ID riêng.

TDD:7fail/46pass trước sửa,53/53 sau sửa; nhóm LLM/UI **564pass**,1 warning
Starlette/httpx cũ. Ruff ba file thay đổi đạt; review code AI tách context không
có finding. Mock kiểm nhãn lỗi/quyền, privacy, ngân sách một call và fallback;
không phải bằng chứng truy cập Google hoặc chất lượng model.0 live/provider/key
access; không thay key/billing.2.932/2.934 file bảo vệ nguyên SHA; chỉ diagnostic
runtime và test lỗi quyền cũ đổi, thêm test biên mới; data/gold/run/review giữ
nguyên. [Receipt bản vá](../data/hus/qa/20261113/singleton_diagnostic_r1/report.json),
manifest `2b3c13b1b470234aa006f0e7c1e9ccb900459c054351440804cb649a2e3356c0`.

Replay A7R/L5 cũ tái hiện; **pins A7R và prepared L5r4 nay stale** vì hash
`app/hus/llm/diagnostics.py` đổi. Không sửa pins/điểm cũ, không tự prepare cohort
mới hoặc gọi key bị chặn. Cần prepare/preflight mới trước lượt live sau khi có
key thay thế và budget mới; L6 giữ off. Phần dưới là lịch sử hai call trước bản vá.

**Call bổ sung đã được cấp và thực hiện:** HTTP403,
JSON dạng mảng chứa một error object, status `PERMISSION_DENIED`, nhóm
`key_reported_leaked`. Google báo key backend hiện tại bị lộ; chưa xác định nơi/
thời điểm lộ và chưa sửa quyền truy cập. Parser cũ chỉ nhận object nên bỏ qua
dạng mảng này. Call đầu không lưu raw body, không xác định lại được hình dạng;
không suy nó giống call bổ sung. Bản vá offline không khôi phục quyền của key.
[Receipt call bổ sung](../data/hus/qa/20261113/google_diagnostic_r2/report.json),
manifest `4c3f36f6cdc5356e0a194a2deb2d5ea677063b1a4435ce9df23eb2d6fe2a9ec4`.
Không raw body/message/key/project ID được lưu. Hai hạn mức một call đều đã dùng
hết; không call/cohort tiếp theo được cấp. Phần dưới ghi lịch sử call đầu.

Ngày **13/11/2026**, nhánh `hus-llm-rag`, nền `f61b0fd` + WIP local.
Người dùng đã cho phép gọi để test/fix theo mục tối đa một call; không xin lại
quyền bật LLM. **Đã gọi một lần, HTTP 403; chưa xác định hoặc sửa được quyền.**

## Preflight và kết quả

- Prepared [r4](../data/hus/evaluation/runs/llm_v3_v4_prepared_20261113_r4/prepared.json)
  khớp code lúc prepare/call, nay stale sau bản vá:36 source audits,24 prompt,12 control. Toàn bộ36 A,
  request, retrieval, gold và prompt bằng r3; chỉ pins/latency lượt prepare mới.
- Chỉ gọi `L5V4-Q001` (F1), prompt **3.607 ký tự**, hash
  `d0acd06dae285c783aed132cef10aab754124088bc5bbc8826a979699e0fb329`,
  bằng bản đã review. Model `gemini-3.5-flash-lite`, endpoint Google đã ghim,
  cap 1.024 output token; không retry/redirect/đổi model.
- **HTTP 403**, `http_error`; diagnostic an toàn là
  `provider_status=other`, `access_issue=unspecified`. Latency provider khoảng
  **589 ms**. Actual model/usage/input token/chi phí **unknown**, không ghi là 0.
- Không có bản sinh được dùng; giữ bản trích nguồn F1/citation. Đây là diagnostic
  truy cập, **không phải run chất lượng L5**, nghiệm thu L6 hoặc cohort mới.
- Dùng key backend hiện có trong bộ nhớ; không in/lưu/sửa key, không đọc file
  mẫu, không đổi billing. Không lưu body/message lỗi/header/project ID. Vì vậy
  không thể khôi phục dạng envelope/mã chưa nhận diện từ artifact hiện có.

[Receipt](../data/hus/qa/20261113/google_diagnostic_r1/report.json) ·
[metadata và fallback](../data/hus/qa/20261113/google_diagnostic_r1/result.json).
Prepared manifest: `d473a280adbf4564304ddef99333fefcfd4444bfa28f912d2a18b5b49a6b4f68`.
QA manifest: `b5171aadcf823f331d16d9ccadc60f9ae494fab2bf7f59afca089e67d6e8727a`.

## Điều đã kiểm và điều chưa biết

30 test xử lý lỗi quyền/circuit đạt, một warning Starlette/httpx cũ; bảy kiểm
metadata hình dạng/phòng lộ dữ liệu chạy offline đạt. **2.885 file cũ giữ SHA**;
runtime/data/gold/run/review cũ không đổi, pins r4 vẫn khớp sau call. Không lặp
toàn suite vì không sửa runtime; kết quả toàn suite trước vẫn có một lỗi dev cũ.

Endpoint và Bearer key phù hợp ví dụ [OpenAI compatibility của Google](https://aistudio.google.com/docs/openai).
[Tài liệu lỗi Google](https://aistudio.google.com/docs/api-errors?generate-content=true)
nêu nhiều khả năng cho 403, gồm quyền key và hạn chế/xác minh project. Chưa có
căn cứ chọn một nguyên nhân cho lần này; banner gần bandwidth limit trước đó
không đủ để kết luận quota hoặc cần billing. Không suy lỗi nằm ở RAG hay đã có
bản vá xác thực. Không có phiên trình duyệt/tài liệu AI Studio kết nối để kiểm
project trực tiếp; không truy cập cookies hoặc tài khoản.

## Bước tiếp theo đã ghi sau call403 bổ sung — lịch sử

Tạo key thay thế trong [Google AI Studio](https://aistudio.google.com/apikey),
cập nhật `HUS_LLM_API_KEY` ở backend, vô hiệu hóa key cũ theo
[hướng dẫn xử lý lộ key của Google](https://aistudio.google.com/docs/api-key#leak-response).
Không gửi key qua chat hoặc đặt key mới trong file mẫu/source; tôi chưa tự đổi
key hoặc billing. Bước kiểm sau báo thay key nay đã thực hiện ở kết quả HTTP200 phía trên;
không dùng hướng dẫn lịch sử này làm quyền gọi thêm.

Parser singleton error array và regression offline **đã sửa** ở bản vá phía trên;
sửa nhãn diagnostic không làm key bị chặn hoạt động trở lại. Sau khi truy cập hoạt động,
L5 cần cohort/ngân sách riêng, A/B cùng snapshot/retrieval và review exact output.
LLM được bật theo tác vụ khi cần; mặc định hiện giữ tắt, chưa nghiệm thu bật mặc
định. Không stage/commit/push/PR/Actions/deploy.
