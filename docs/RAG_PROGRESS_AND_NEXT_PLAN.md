# Chatbot HUS — Tiến độ và các bước tiếp theo

Cập nhật **15/11/2026** · Nhánh **`hus-llm-rag`** · Phạm vi **đồ án sinh viên**.

**Yêu cầu GitHub mới:** người dùng đã cho phép chia thay đổi thành10 commit và
push nhánh `hus-llm-rag`; quyết định này thay yêu cầu giữ local trước đó cho lượt
đưa code này lên GitHub. Không merge `main`, tạo PR hoặc deploy trong yêu cầu này.

**Có thể chạy thử chatbot ngay khi đã cài dependency và cấu hình key backend hợp lệ.**
Luồng RAG → Gemini → kiểm đầu ra → hiển thị đã có kết quả thật ở các lượt trước;
những bước tiếp theo là kiểm phần mới và cải thiện các ca còn lỗi, không phải
điều kiện phải làm xong hết mới được chạy đồ án.

| Chế độ | Đã kiểm đến đâu? | Phần còn thiếu |
| --- | --- | --- |
| **Mặc định `legacy`** |Đã gọi Gemini thật cho F1/F2/F3 trong các lượt đã lưu; có đáp án được hệ thống dùng, không chỉ HTTP200. [Bộ30 câu](RAG_STUDENT_CONTENT_30_LIVE_2026_11_14.md), [xác nhận F2](RAG_F2_PROMPT_CONFIRMATION_2026_11_14.md), [ý định/F2 live](RAG_INTENT_F2_PRACTICAL_LIVE_2026_11_14.md). |Vẫn có lỗi/từ chối/cần làm rõ ở một số cách hỏi; chưa được nhóm nghiệm thu toàn bộ nội dung. Các kết quả live là bằng chứng lịch sử, không tự chứng minh mọi bản sửa mới đã kiểm Google. |
| **Lựa chọn mới `focused`** |Đã kiểm offline/đầu ra giả lập, UI và5 search hybrid/Chroma thật; [báo cáo](RAG_FOCUSED_ANSWER_2026_11_15.md). |**Chưa gọi Gemini với prompt/protocol focused mới**. Cần một lượt live riêng trước khi kết luận model tuân thủ tốt; test xanh hoặc retrieval thật không thay phép kiểm này. |

Lệnh chạy luồng mặc định bằng key đã lưu, không nhập lại key:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_llm
```

Nếu đã chuẩn bị hybrid/cache, dùng Python `.venv-hybrid` và thêm `--retrieval hybrid`.
Thêm `--answer-policy focused` khi muốn thử chế độ mới. Server đang chạy cần restart
để nhận code/cờ mới; [hướng dẫn đầy đủ](HUS_RAG_QUICKSTART.md).

## 1. Mục tiêu đã thống nhất

Xây dựng chatbot hỏi đáp thông tin bốn ngành của Khoa Toán: **Toán học, Toán tin,
Khoa học máy tính và thông tin, Khoa học dữ liệu**. Người dùng chọn ngành, nhập
câu hỏi; chatbot **lấy bằng chứng từ RAG rồi dùng LLM để trả lời bằng tiếng Việt**,
kèm nguồn để đối chiếu.

| Nhóm | Nội dung hỏi đáp | Yêu cầu chính |
| --- | --- | --- |
| **F1 — Thông tin ngành** | Giới thiệu, định hướng đào tạo, cơ hội nghề nghiệp, học tiếp và thông tin có trong tài liệu ngành. | Trả lời đúng ngành/hệ/phiên bản tài liệu; thiếu căn cứ thì nói rõ. |
| **F2 — Thông tin môn học trong chương trình** | Tên/mã môn, tín chỉ, tiên quyết và các dữ kiện đã lưu. | LLM hỗ trợ diễn đạt; backend giữ nguyên dữ kiện gốc, không tự bổ sung tín chỉ hoặc tiên quyết. |
| **F3 — Nội dung tham khảo AI** | Tổng quan, nội dung/chủ đề và mục tiêu học tập của môn học. | Dùng hồ sơ tham khảo đã lưu, có nhãn **“kiến thức AI”**; không trình bày thành đề cương chính thức. Không cần bài tập/tiêu chí đánh giá. |

Độ phức tạp hướng tới **cơ bản đến trung bình**: ưu tiên hỏi đáp dùng được, dễ chạy,
dễ giải thích trong báo cáo. Tài khoản, bảng điểm, tư vấn chọn môn, triển khai public,
hạ tầng nhiều người dùng và kiểm Linux/macOS nằm ngoài kế hoạch hiện tại.

## 2. Hiện tại đã có gì?

| Thành phần | Trạng thái thực tế |
| --- | --- |
| **Review ý định/F2 — đã đối chiếu12 ca, chờ nhóm** |Sáu đáp án live khớp nguồn/canonical/preflight; hai danh sách68/65 mã-tên đủ từng dòng; bốn control giữ biên.002 bị generation `fact_keys`, bundle cần4 khóa ngoài nhưng không có raw để biết model sai khóa nào;004 chỉ làm rõ, chưa đếm. Lưu nhận xét AI/CSV riêng,19 file cũ giữ hash, Google0; không sửa prompt/runtime.12 review người thật pending. [Review và hướng sửa](RAG_INTENT_F2_CONTENT_REVIEW_2026_11_15.md). |
| **Kiểm nội dung sau router — đã chạy offline, chờ nhóm review** |24 câu nháp AI/bốn ngành:11 answered/7 no-information/6 cần làm rõ.3/4 câu nghề nghiệp,4/4 khái niệm và4/4 tiên quyết có đáp án;31 citation khớp canonical, F2 giữ dòng nguồn/cảnh báo,001/017 được hỏi rõ. Phát hiện câu nghề nghiệp Toán tin chứa “em” bị guard chặn; diagnostic chỉ bỏ xưng hô thì answered, chưa sửa runtime.63 file cũ giữ hash, Google0;24 review người thật pending. [Báo cáo](RAG_ROUTER_CONTENT_REVIEW_2026_11_15.md), [CSV nhóm](../data/hus/review/router_content_dev_20261115_r1/review_group_return.csv). |
| **Dữ liệu và tìm kiếm** |Dữ liệu vẫn `hus-data-20261111-v4`. **Hybrid v4 đã chuẩn bị và chạy kiểm thật**:1.818 parent/1.822 passage/vector, E5 CPU + Chroma/BM25/RRF. Profile ghim ID ngoài DB; launcher chọn bằng `--retrieval hybrid`, lexical vẫn mặc định để đối chiếu. F2 tra dữ kiện trực tiếp; F3 giữ nhãn AI/quyền riêng, chưa được giảng viên nghiệm thu đầy đủ. [Báo cáo](RAG_HYBRID_V4_2026_11_14.md). |
| **Backend và giao diện** | Có API/chat UI, chọn ngành, menu, nguồn trích dẫn và lựa chọn dùng AI. Bản RAG cơ bản có thể chạy local trên Windows 64-bit/Python 3.11. |
| **Kết nối LLM** | Có client gọi trực tiếp Google qua API tương thích OpenAI, không cần 9Router. Model cấu hình đang dùng là `gemini-3.5-flash-lite`; key chỉ đặt ở backend. |
| **Tích hợp F1/F2/F3 — đã triển khai, kiểm offline** | F1/F3 chọn bằng chứng rồi gọi LLM trước khi dựng bản trích nguồn; F2 giữ nguyên dữ kiện backend. Đã sửa các cụm hỏi thường gặp, tên chủ đề chứa “kiểm tra”, ngữ cảnh chương trình và chào hỏi.66 test mới cùng các nhóm liên quan đạt; API giả lập kiểm cả bốn ngành, tín chỉ/tiên quyết, nhãn AI và fallback. [Báo cáo](RAG_F1_F2_F3_INTEGRATION_2026_11_14.md). |
| **Test F1 ban đầu — kết quả lịch sử** |Một câu F1 được Gemini trả lời và dùng thật (`used=true`), HTTP200≈1,89s; sửa lỗi tách tiêu đề lồng `## 4. …`,139 test liên quan đạt. Dùng2/3 call của lượt riêng và dừng khi thành công; sau đó đã chạy bộ30 câu bên dưới. [Báo cáo](RAG_F1_LLM_WORKING_2026_11_14.md). |
| **Bộ30 câu — đã chạy Gemini thật, chờ nhóm review** |24 câu nội dung: **F1 dùng8/8, F2 dùng7/8, F3 dùng8/8**;6 control không gọi Google. Đã dùng24/24 call mới được duyệt, tất cả HTTP200;1 câu tín chỉ MAT2300 (`SV30-003`) bị `invalid_output`, fallback giữ dữ kiện4 tín chỉ. Có CSV/đáp án/nguồn, **30 review người thật còn pending**. [Kết quả](RAG_STUDENT_CONTENT_30_LIVE_2026_11_14.md), [CSV nhóm điền](../data/hus/review/student_content_live_20261114_r1/review.csv). |
| **Rà soát sơ bộ30 câu — đã có bản riêng của AI** |Đã đọc từng đáp án/quote, ghi nhận xét Codex(AI) cho cả30 câu.4 câu F3 đúng chủ đề nhưng dư unit (005/011/017/023),2 ví dụ cần làm rõ giả định/wording; F2 giữ đúng dữ kiện nguồn. Có [CSV trả riêng](../data/hus/review/student_content_ai_draft_20261114_r1/review_group_return.csv), các cột xác nhận nhóm vẫn trống/pending. Không thay bảng gốc hoặc điểm cũ. [Nhận xét](RAG_STUDENT30_AI_REVIEW_2026_11_14.md). |
| **Diagnostic F2 — đã sửa offline** |Đã thêm nhãn phân biệt JSON/kind/style/schema/khóa/nguồn/result/credential echo.29 regression cuối và nhómLLM668 test đạt;61 đầu ra giả giữ nguyên quyết định trước–sau. Không nới validator, dữ kiện4 tín chỉ/citation/fallback giữ nguyên. **Nguyên nhân nhánh của call cũ vẫn unknown** vì không có raw output; không gọi Google hoặc đổi kết quả cũ. [Báo cáo](RAG_F2_OUTPUT_DIAGNOSTIC_2026_11_14.md). |
| **Kiểm F2 mới — đã xác định nhánh kind** |Dùng1/1 call riêng sau diagnostic: HTTP200≈2,18s nhưng `used=false`, `output_schema/facts_issue=kind`. Trường `kind` thiếu hoặc không hợp lệ với F2; không lưu giá trị bị từ chối, không suy lỗi này cho call cũ. Fallback giữ4 tín chỉ/citation; ở lượt kiểm đó chưa sửa prompt hoặc nới validator. [Báo cáo](RAG_F2_LIVE_CHECK_2026_11_14.md). |
| **Prompt F2 riêng — đã sửa và có xác nhận live** |Tách hướng dẫn F2, bắt buộc `kind=facts`;13 test mới/nhóm liên quan42 và nhóm LLM rộng680 đạt. Prompt F1/F3, payload/validator/dữ kiện giữ nguyên. Call MAT2300 riêng sau sửa: **HTTP200/used=true≈1,62s**,775 input/53 output token, giữ4 tín chỉ/citation; dùng hết1/1 call được duyệt. Không chấm lại run30 câu hoặc khẳng định mọi F2 đều ổn định. [Sửa offline](RAG_F2_DEDICATED_PROMPT_2026_11_14.md), [xác nhận](RAG_F2_PROMPT_CONFIRMATION_2026_11_14.md). |
| **UI và hướng dẫn Windows — đã chốt/kiểm local** |Làm rõ nhãn dùng AI/fallback và lỗi quyền/hạn mức/503; hướng dẫn RAG không key và Gemini qua biến backend riêng.29 test browser,14 citation,27 wrapper/package đạt. Venv tối thiểu mới + source chuyển thư mục chạy `--check`20 ca/2.124 menu/4 file nguồn và server HTTP5 chat đạt. Không gọi Google; chưa kiểm máy khác/clone remote. [Quickstart](HUS_RAG_QUICKSTART.md), [receipt/báo cáo](RAG_UI_QUICKSTART_2026_11_14.md). |
| **Báo cáo và demo — đã chuẩn bị** |Có [báo cáo phân hệ](HUS_RAG_PROJECT_REPORT.md): luồng RAG–LLM, ví dụ F1/F2/F3, số liệu và giới hạn; [kịch bản demo 5–7 phút](HUS_RAG_MANUAL_DEMO.md) dùng quickstart, không gắn đường dẫn cá nhân. Sáu câu demo kiểm offline đạt, không gọi Google. Phần Gemini live là tùy chọn cần key/backend và ngân sách phù hợp. Chưa có thông tin học phần/thành viên hoặc xác nhận review/cài thử từ nhóm. |
| **Chất lượng RAG** |Bộ30 câu đã có phản hồi thật và lỗi còn lại; chưa được nhóm xác nhận đúng/đủ ý hoặc có cải thiện diễn đạt. Vẫn có giới hạn câu hỏi và F3 dài. Nguồn F1 KHDL giữ hệ/edition unknown, F3 giữ nhãn AI. A7B cũ giữ Recall22/24, đủ ý27/36; không chấm lại để nâng điểm. [Review lịch sử](RAG_A7B_FAILURE_REVIEW_2026_11_13.md). |
| **Chẩn đoán bước bị chặn — đã triển khai/kiểm offline** |API gắn mã tại routing/scope/thao tác/retrieval/guard; phân biệt output bị chặn và lỗi dịch vụ trong HTTP502. UI có nhãn/hướng xử lý; sai ngành nêu ngành đang chọn và ngành cần chọn lại, không tự đổi ngành. Log `hus_chat_block code=...` không ghi key/câu hỏi/body lỗi.155 test liên quan đạt, có warning Starlette cũ; rà soát không ghi nhận lỗi quan trọng. Không đổi chính sách offline chỉ sau429; chưa gọi Google thật ở lượt này. |
| **20 câu tự nhiên/latency — đã đo, bản nháp AI cho nhóm** |20 câu/5 mỗi ngành được lưu kỳ vọng/nguồn trước inference, không sao chép nguyên menu. Cùng v4/code/index, lexical và hybrid đều9 answered/6 no-information/5 cần làm rõ.9 câu search có cùng tập top5; chưa thêm câu trả lời nhờ hybrid. Median RAG của9 câu search: lexical0,007s/hybrid6,058s; cold155,333s. Google0. Câu/review do Codex(AI) soạn,20 xác nhận người thật pending; không là điểm chính xác hoặc bộ nhóm đã nghiệm thu. [Báo cáo](RAG_HYBRID_NATURAL20_2026_11_14.md), [đáp án/nguồn](RAG_HYBRID_NATURAL20_RESPONSES_2026_11_14.md), [CSV nhóm điền](../data/hus/review/hybrid_natural20_20261114_r1/review_group_return.csv). |
| **Hiểu ý định + đếm/liệt kê F2 — đã triển khai** |Launcher Gemini gọi bộ hiểu JSON khi luật trả `routing_unknown`; backend kiểm thao tác/mã môn, giữ câu gốc/edition/hệ/quyền F3. Đếm/liệt kê mã môn duy nhất đúng ngành/phiên bản, có nguồn và metadata phép tính; không đếm menu hoặc để model tạo số. Câu hỏi lệch ngành yêu cầu chọn lại; số môn phải học/bắt buộc và lọc có điều kiện chưa hỗ trợ sẽ làm rõ. Một câu có thể cần2 call (ý định + diễn đạt), metadata riêng;429 khóa cả hai bước, lỗi khác báo lỗi.177 test/`--check` là kiểm offline của bước triển khai; đã có lượt Gemini thật riêng ghi ở dòng “Kiểm thực tế ý định/F2” bên dưới. [Hợp đồng/giới hạn](RAG_INTENT_F2_CATALOG_2026_11_14.md). |
| **Cú pháp/router — đã sửa offline** |Phân biệt “thì” có dấu với thi thật trước bỏ dấu; nhận làm việc ở đâu, phải hoàn thành môn nào trước và câu hỏi khái niệm. F2 tiên quyết không cần quyền F3; F3 giữ opt-in/nhãn AI.001/017 hỏi rõ mục tiêu/nghề nghiệp/danh mục môn. Diagnostic code mới:002/004/005/008 trả lời từ đúng nhóm dữ liệu;001/017 cần làm rõ.53 regression mới/reviewer53 ca đạt; lượt rộng cuối636 test, Ruff5 file và `--check` đạt, Google0.30 file pack/run/review cũ giữ nguyên hash; không chấm lại run. [Chi tiết](RAG_ROUTER_GRAMMAR_REPAIR_2026_11_14.md). |
| **Kiểm thực tế ý định/F2 — đã chạy Gemini** |Người dùng duyệt tối đa12 call mới; dùng11, tất cảHTTP200/actual model `gemini-3.5-flash-lite`:6/8 câu F2 có đáp án dùng model,IF2-002 lỗi `output_coverage/fact_keys`,IF2-004 cần làm rõ;4 control0call,0fallback offline.21.316 input/653 output token.74pins/prompt/canonical khớp; review người thật pending. Không retry hoặc dùng1 call còn lại cho việc khác. [Kết quả/CSV](RAG_INTENT_F2_PRACTICAL_LIVE_2026_11_14.md). |
| **Guard/nguồn/context tập trung — đã triển khai opt-in** |Có `--answer-policy focused`: chọn edition/hệ/source trước retrieval, UI chọn nguồn, lấy đủ đoạn mô tả theo ý hỏi; protocol `focused_rewrite_v1` giữ từ/số/toán tử/điều kiện, không sửa citation/quote/facts.1072 test liên quan và49 lượt tập trung sau sửa đạt (có giao nhau), Ruff/CLI/browser đạt;5 search hybrid thật đúng index/nguồn, không fallback retrieval, Google0. Mặc định legacy/v3; chưa paraphrase tự do hoặc nghiệm thu Gemini/người thật. [Triển khai và CSV](RAG_FOCUSED_ANSWER_2026_11_15.md). |
| **Latency hybrid — đã đo và tối ưu local** |Bỏ lần sao chép metadata đệ quy dư trong fingerprint; vẫn kiểm đầy đủ snapshot/index/inventory/scope. Lượt cặp20 câu,10 có search: median RAG hybrid **6,591→3,327s, giảm49,5%**;10 no-search tách riêng.20/20 response/trace cũ–mới giống nhau,37 file được bảo vệ giữ hash.173 test đạt/1 skip symlink Windows, Ruff và `--check` đạt; Google0. Chưa là đo Gemini/điểm chất lượng,20 review người thật pending. [Báo cáo](RAG_HYBRID_LATENCY_2026_11_15.md), [CSV mới](../data/hus/review/hybrid_latency_paired_20261114_r1/review_group_return.csv). |

**Dữ liệu vẫn v4; lexical mặc định, hybrid có lựa chọn explicit. Launcher RAG tắt LLM; launcher Gemini tự động dùng LLM.** Luồng bằng chứng → LLM
đã triển khai; bộ30 câu đã kiểm24 câu với Google theo budget riêng. Người tải source có thể kiểm RAG không
cần key; muốn dùng Gemini thật thì cần internet và key Google hợp lệ ở backend.
[Hướng dẫn chạy](HUS_RAG_QUICKSTART.md).

**Lựa chọn mới:** thêm `--answer-policy focused` để thử chọn nguồn/context và
protocol mới; không có cờ này vẫn legacy/v3. Chỉ kiểm offline/giả lập và hybrid
local, chưa đo Gemini với prompt mới. Không đổi key/release/index hoặc tự restart.

**Chạy Gemini bằng key đã lưu:** `python -m tools.run_hus_llm` (dùng Python của
`.venv`) tự đọc `HUS_LLM_API_KEY` từ `.env` gốc, không nhập lại key.32 test
launcher/đóng gói offline đạt; chưa gọi Google ở lượt sửa này. Lệnh RAG cũ vẫn
ép LLM tắt, cấu hình lưu trên đĩa không đổi.

**Quyết định mới — Gemini tự động, offline chỉ sau hạn mức:** launcher Gemini
đặt `HUS_LLM_AUTO=true`; UI không cần tick diễn đạt, API tự bật cho câu có bằng
chứng. Quyền F3 vẫn riêng. Khi Google trả429, process chuyển RAG offline và
ngừng gọi tiếp đến khi restart;429 có thể là giới hạn theo phút/ngày, không suy
ra mọi quota đã hết. Lỗi401/403/503/mạng/timeout hoặc output không hợp lệ báo
lỗi, không thay bằng offline. Chào hỏi/thiếu nguồn/mơ hồ vẫn xử lý trước model.
Đây là chính sách dùng LLM đã triển khai. Phần hiểu câu hỏi/đếm môn cũng đã được
bổ sung và có lượt live riêng; riêng lần sửa chính sách này kiểm provider giả lập,
không dùng key thật/call Google.
Nhóm API/UI/launcher/đóng gói đạt **77 test** (warning Starlette cũ), có regression
cho request đang chuẩn bị bằng chứng khi request khác nhận429. Đã rà soát code;
không coi mock là bằng chứng Gemini live hoặc cải thiện nội dung.

**Đã sửa cách hỏi giới thiệu môn:** “Tôi muốn tìm hiểu về môn Thị giác máy tính”
được route F3/content và khớp MAT3562 trong KHDL, thay vì từ chối trước retrieval.
Thêm 18 regression; tổng nhóm liên quan 129 test đạt (có warning Starlette cũ).
Giữ quyền F3, phạm vi ngành/môn, dữ kiện F2 và citation. Chưa gọi Google trong
lượt sửa này; số liệu live30 cũ không thay đổi. Server cần restart để nạp code mới.

**Hiển thị F3 gọn hơn:** theo yêu cầu nhóm, bỏ số dẫn chứng và các thẻ nguồn AI
lặp lại, giữ thông báo “kiến thức AI” cùng trạng thái dùng model/fallback.
F1/F2 vẫn hiện dẫn chứng tài liệu thật. Chỉ đổi giao diện; metadata/validator
và dữ liệu nguồn giữ nguyên.41 test UI/citation liên quan đạt, không gọi Google.

## 3. Vì sao hỏi ngoài menu còn khó?

**Không phải chỉ do BM25. LLM vẫn diễn đạt bằng chứng được backend chấp nhận;
nay đã có thêm bước hiểu JSON cho câu luật chưa hiểu trong launcher Gemini.**
Luồng thực tế: luật nhận diện câu hỏi → kiểm ngành/môn/phiên bản → nếu chưa hiểu,
nhận diện ý định JSON và kiểm lại → lấy dữ liệu/tra hoặc tính từ F2 →
kiểm bằng chứng → gọi Gemini nếu được phép → kiểm output → hiển thị/fallback.
Chế độ tự động không bỏ qua những bước chặn trước model; không còn cần tick
diễn đạt trong profile này. F3 vẫn cần quyền tham khảo riêng.

| Nguyên nhân trong code hiện tại | Tác động và hướng xử lý |
| --- | --- |
| **Menu cung cấp sẵn thông tin định tuyến** | Nút menu gửi kèm dataset/field/mã môn/edition; nhập tự do phải tự nhận diện các thông tin này bằng luật từ khóa. Menu không phải danh sách câu hỏi duy nhất được phép, nhưng các câu có sẵn dễ đi đúng luồng hơn. Cần cải thiện hiểu câu hỏi, thay vì bổ sung vô hạn mẫu câu. |
| **Phạm vi ngành khóa theo ô chọn** | Trong ảnh, đang chọn KHDL nhưng hỏi KHMT. Offline tái hiện đúng lỗi scope. Nên hỏi rõ “Bạn muốn chuyển sang KHMTTT?” và đồng bộ UI trước khi tra cứu; không âm thầm trộn hai ngành. |
| **Thiếu phép toán trong bản chụp ảnh — đã bổ sung** | Lúc chẩn đoán, chọn đúng KHMTTT vẫn chưa có thao tác đếm. Nay đã đếm/liệt kê từ F2 theo ngành/phiên bản; sai ngành cần chọn lại trước. Danh mục không đồng nghĩa mọi sinh viên phải học hết; đếm bắt buộc/tự chọn/điều kiện vẫn cần làm rõ. |
| **Hợp đồng chỉ nhận yêu cầu hẹp** | Backend hiện từ chối nhiều mã môn hoặc nhiều field trong một câu. Các câu so sánh hai môn/hỏi nhiều ý có thể bị chặn dù từng phần có dữ liệu. Cần tách thành các truy vấn nhỏ theo đúng scope, rồi tổng hợp; không đơn giản bỏ guard. |
| **BM25 thiên về từ khóa** | Cách hỏi dùng từ đồng nghĩa hoặc tên môn viết khác có thể không lấy được đoạn đúng. Nhóm đã chọn bổ sung ChromaDB và gộp hybrid để cải thiện bước này; vẫn phải sửa routing/scope/phép toán và kiểm hiệu quả, không coi vector là đã chữa mọi lỗi. |
| **Guard bằng chứng và prompt quá thiên về giữ nguyên văn** | Guard trước model có thể từ chối dù lấy được đoạn liên quan. Prompt F1/F3 yêu cầu giữ mọi đoạn/từ theo thứ tự, kể cả phần ngoài ý hỏi; validator lexical có thể chặn cách diễn đạt tương đương. F2 chỉ trả style/fact_keys/citation_ids. Thiết kế này bảo toàn bản trích nhưng hạn chế tổng hợp, giải thích và suy luận. Cần hợp đồng trả lời theo ý hỏi, giữ facts/điều kiện thiết yếu thay vì bắt giữ từng từ. |
| **Không có lịch sử hội thoại trong request** | “Môn đó”, “ngành này” ở lượt tiếp theo không được suy ra từ lượt trước. Cần hoặc hỏi lại rõ ràng, hoặc thêm context ngắn về ngành/môn đã xác nhận; không gửi toàn bộ history mặc định. |

Ca trong ảnh trước sửa đã được kiểm **offline, 0 Google call**: cả hai ngành
đều bị chặn trước model. Sau sửa, regression xác nhận sai ngành vẫn yêu cầu chọn
lại và chọn đúng KHMTTT sẽ tính từ F2. Không sửa kết quả chẩn đoán/run cũ; chưa
đo chất lượng Gemini thật cho luồng mới.

Căn cứ: [menu và hints](../app/hus/question_catalog.py),
[định tuyến](../app/hus/question_routing.py), [scope/tra cứu](../app/hus/answering.py),
[guard bằng chứng](../app/hus/answer_support.py),
[điều kiện gọi model](../app/hus/llm/generation.py),
[prompt](../app/hus/llm/prompts.py), [coverage](../app/hus/llm/coverage.py).

## 4. Hướng cải thiện phù hợp đồ án — đã triển khai một phần

**Câu hỏi tự nhiên → hiểu ý hỏi/ngành/môn/phép toán → lấy dữ liệu phù hợp →
Gemini tổng hợp/giải thích theo câu hỏi → kiểm dữ kiện → trả lời.**

- **Hiểu câu hỏi — đã làm offline:** luật rõ ràng đi trước; `routing_unknown`
  trong launcher Gemini dùng JSON chọn dataset/field/ngành/mã môn. Backend kiểm
  schema/định danh, giữ câu gốc và scope; không cho model chạy code/SQL hoặc tạo
  dữ kiện. Có thể thêm một call và độ trễ/quota.429 mới dùng đường offline;
  lỗi provider/JSON khác báo lỗi. Câu chưa rõ hỏi lại; chưa thay guard hoặc sửa
  mọi ca luật chọn nhầm field. [Chi tiết](RAG_INTENT_F2_CATALOG_2026_11_14.md).
- **F1/F2:** Gemini được tổng hợp từ dữ liệu đã lấy; tín chỉ, tiên quyết, số môn,
  edition và điều kiện vẫn do backend xác định. Đếm bằng mã môn duy nhất trong
  ngành/phiên bản đã chọn; nói rõ đếm toàn bộ danh mục hay môn bắt buộc/tự chọn.
  Tổng môn trong danh mục không đồng nghĩa mọi sinh viên phải học hết.
- **F3:** cho phép giải thích khái niệm, ví dụ hoặc so sánh dựa trên hồ sơ liên quan;
  phần bổ sung kiến thức chung của model cần được xác định rõ trong hợp đồng mới,
  có quyền F3 và nhãn AI. Không dùng kiến thức chung để tự bổ sung quy định HUS,
  tín chỉ/tiên quyết hoặc khẳng định đề cương chính thức. UI không cần dẫn chứng AI;
  ẩn thẻ nguồn không có nghĩa backend hiện đã cho phép sinh tự do.
- **Kiểm output:** đã có protocol focused chọn đủ phần liên quan trước model,
  giữ chuỗi từ/toán tử và literal số nghiêm; chưa cho paraphrase tự do. Hướng
  diễn đạt tương đương linh hoạt hơn vẫn cần thiết kế/đo riêng. Giữ facts, mã môn, phủ định, điều kiện, scope và nguồn
  thật của F1/F2. Dùng nhóm đọc nội dung để đánh giá đúng/đủ ý; không bỏ mọi kiểm
  tra hoặc coi schema JSON đúng là câu trả lời đúng.
- **Retrieval — đã chọn hybrid:** F1/F3 lấy ứng viên từ BM25 và ChromaDB với
  cùng bộ lọc ngành/phiên bản/môn/quyền F3, gộp bằng RRF rồi đưa bằng chứng cho
  Gemini. F2 tra/tính trực tiếp từ dữ liệu có cấu trúc, không dùng vector để đoán
  tín chỉ/tiên quyết/số môn. Embedding có thể tìm khái niệm gần nhau, không chứng
  minh hai môn/thuật ngữ tương đương. Chỉ gọi LLM khi qua scope/bằng chứng phù hợp.

### Hybrid v4 — đã chuẩn bị và kiểm local

Đã có [HUSHybridRetriever/RRF](../app/hus/hybrid_retrieval.py),
[service chọn retrieval](../app/services/hus_service.py) và
[runtime ChromaDB + E5 local](../app/hus/vector_runtime.py). Policy hiện có lấy
tối đa20 ứng viên mỗi nhánh, bỏ trùng/gộp RRF (hằng số60), trả top5; đây là cấu
hình khởi đầu, chưa chứng minh tốt hơn lexical trên câu hỏi của nhóm.

- Đã tạo contract/passages/index riêng `e5_small_v4_20261114`; giữ13 file bộ cũ/
  CURRENT nguyên hash. Sai pin hoặc contract v3 dùng với v4 bị từ chối.
- `.venv-hybrid` và cache model local đã kiểm112 package/9 file; tái sử dụng
  model cũ, không tải mới. Môi trường seed local, chưa phải cài PyPI sạch/máy khác.
- Cả hai launcher hỗ trợ `--retrieval hybrid`, `--model-cache`, `--check`.
  Profile ghim ba đường dẫn artifact/expected ID ngoài DB, không dùng nhầm v3.
  Check không đọc key, chỉ đạt khi **actual_mode=hybrid**, hai nhánh có ứng viên
  và đúng ID. [Lệnh chạy](HUS_RAG_QUICKSTART.md#chạy-hybrid-bm25--chromadb-với-v4).
- 16 cặp lexical/hybrid cùng snapshot đạt smoke;4F2/4F3 opt-out không gọi vector;
  5 ca HTTP thật trên môi trường mới đạt, rollback lexical20API/2.124menu/4hash đạt.
  Nhóm test104 và44 đạt có giao nhau. Google0, không coi đây là điểm nội dung.
- Số lịch sử: cold local65–156s, warm16ca khoảng3–9,3s. Sau tối ưu fingerprint,
  lượt cặp mới10ca có search đạt median RAG3,327s so với6,591s của hàm cũ,
  cùng runtime/snapshot. Cold mới56,484s được ghi riêng, không suy cải thiện cold
  từ hai thời điểm khác nhau; chưa gồm Gemini. [Số đo](RAG_HYBRID_LATENCY_2026_11_15.md).
- Vector lỗi mà dùng lexical là fallback **retrieval**, không có nghĩa chuyển
  LLM sang offline. Chroma binary/weights local bị ignore; máy nhận source phải
  chuẩn bị thêm theo quickstart. [Bằng chứng/giới hạn](RAG_HYBRID_V4_2026_11_14.md).

**Kết quả lịch sử của lượt20 câu tự nhiên:**002/005/008 bị “thì”→`thi`→assessment trước search;
004 chưa nhận diện cách hỏi khái niệm,001/017 cần làm rõ field/cấp ngành.
006 có target rank1 và019 rank3 nhưng guard vẫn từ chối.012 là đáp án khác duy
nhất: hybrid chọn PDF2015 ít chi tiết hơn DOCX2023 của lexical; cần quy tắc
edition/ý hỏi, không coi hai nguồn tương đương.009/014 có ý được hỏi nhưng dư
unit. Ba F2 trả đúng4/3/3 tín chỉ; hỏi tiên quyết008 chưa vào F2.010/015/020 giữ
đúng biên scope/quyền F3/môn không có. Chưa sửa runtime hoặc gold trong phép đo.
Lượt này **LLM tắt có chủ đích**, không phải Gemini hết lượt/fallback; chưa đo
Google hay cải thiện diễn đạt. Bỏ riêng “thì” trong diagnostic vẫn chưa ra đúng
intent, nên không chữa bằng xóa một token toàn cục. [Chi tiết](RAG_HYBRID_NATURAL20_2026_11_14.md).

**Sau sửa riêng router:** phân biệt trợ từ có dấu trước bỏ dấu, bổ sung cách hỏi
nghề nghiệp/tiên quyết/khái niệm và phép đếm đã có. Kiểm dev mới002/004/005/008
đi đúng nhóm và có nguồn;001/017 hỏi rõ ý cấp ngành. Không sửa kết quả đoạn trên,
không gọi đây là điểm mới hoặc đã sửa guard/edition/đủ ý. Giữ câu hỏi thi thật,
điều kiện/phủ định và kiểm source scope. [Báo cáo sửa](RAG_ROUTER_GRAMMAR_REPAIR_2026_11_14.md).

LLM có thể hiểu và suy luận, nhưng ứng dụng phải cấp đúng dữ liệu và cho phép
loại trả lời đó. Với dữ kiện học vụ của một phiên bản cụ thể, model vẫn không thể
tự biết chính xác chỉ từ kiến thức huấn luyện.

## 5. Các bước tiếp theo

**Nhóm có thể chạy/demo bản mặc định ngay.** Ưu tiên dưới đây giúp xác nhận
focused và xử lý các lỗi đã biết; phần review/báo cáo tiếp tục song song, không
phải một chuỗi chặn việc chạy thử.

| Ưu tiên | Công việc | Hoàn thành khi |
| --- | --- | --- |
| **1 — Xác nhận Gemini thật với focused khi có budget** |[Chế độ mới đã kiểm offline](RAG_FOCUSED_ANSWER_2026_11_15.md). Chọn vài câu đại diện F1/F2/F3 và chọn nguồn, chuẩn bị/pin bộ mới, thống nhất số call rồi chạy một lượt live riêng. Đọc đáp án/nguồn; ghi riêng model used, lỗi và offline sau429. |Có bằng chứng model trả được và output được hệ thống dùng theo prompt mới; không coi mock/5 search Chroma là đã test Gemini focused. Không dùng1 call cũ hoặc sửa run lịch sử; bản mặc định vẫn chạy thử được trong lúc chờ. |
| **2 — Nhóm review24 câu và chọn sửa xưng hô** |[Lượt nội dung mới](RAG_ROUTER_CONTENT_REVIEW_2026_11_15.md) đã có đáp án/quote/nhận xét AI riêng. Nhóm điền CSV, thêm câu tự viết; đọc các câu làm rõ001/017. Nếu chọn sửa: xử lý xưng hô “em” bị coi là nội dung cần nguồn và lời nhắc thiếu field đánh giá, thêm regression tương tự/negative rồi lưu run mới. |24 review người thật còn pending;11 answered không đồng nghĩa đúng/đủ ý. Không bỏ token toàn cục, nới guard hoặc chấm lại run20/run24. Giữ thi thật, điều kiện/phủ định, scope và quyền F3; Google thêm cần budget mới. |
| **3 — Nhóm review IF2 và chọn cải thiện prompt/câu đếm** |[Review12 ca đã có bản AI riêng](RAG_INTENT_F2_CONTENT_REVIEW_2026_11_15.md), nhóm điền CSV. Nếu chọn sửa: làm rõ danh sách khóa ngoài F2 cần copy; nhận câu đếm đơn giản từ scope đã chọn hoặc bổ sung ví dụ ý định, thêm regression tương tự/negative.004 chưa có số,002 chưa biết khóa model trả sai; prompt/runtime chưa đổi ở lượt review. |Không suy nguyên nhân raw đã mất, nới schema hoặc coi khả năng backend68 môn là đáp án004. Giữ11call/6used/0fallback và run cũ; live tiếp cần prepare mới theo code pins hiện tại và budget mới, không dùng lại1 call cũ. |
| **4 — Review câu tự nhiên sau tối ưu latency** |Profile và lượt cặp đã xong: median hybrid6,591→3,327s trên10ca search,20/20 cặp giữ đáp án/trace. Nhóm điền [CSV mới](../data/hus/review/hybrid_latency_paired_20261114_r1/review_group_return.csv), bổ sung câu tự viết và ghi lỗi/nội dung/độ trễ thực tế. Chỉ tối ưu thêm khi còn nhu cầu và có số đo. |Giữ run cũ, tách10no-search, không bỏ pin/scope/inventory. Chưa chứng minh chất lượng tốt hơn hoặc latency Gemini. Live tiếp cần budget mới và prepare lại vì code pins của packet ý định/F2 cũ đã khác; không sửa packet/run cũ. |
| **5 — Nhóm review và hoàn thiện báo cáo/demo** |Đọc [CSV6 tình huống focused](../data/hus/review/focused_answer_offline_20261115_r2/review_group_return.csv), [CSV20 câu](../data/hus/review/hybrid_natural20_20261114_r1/review_group_return.csv) và [CSV30 câu](../data/hus/review/student_content_ai_draft_20261114_r1/review_group_return.csv); cập nhật [báo cáo](HUS_RAG_PROJECT_REPORT.md), [demo](HUS_RAG_MANUAL_DEMO.md), để thành viên khác cài thử. |Review AI không thay người thật. Giữ run cũ23used/1fallback/6control; phân biệt rõ legacy đã có live và focused mới kiểm offline, không coi một call thành công là nghiệm thu toàn bộ. |

**Cách làm từ đây:** ưu tiên hoàn thiện luồng hỏi đáp trước. Các quy trình A7/L5/L6
chi tiết, A/B nhiều lượt, review chuyên môn toàn bộ dữ liệu và đóng gói nhiều
revision được giữ làm tài liệu tham khảo, **không là điều kiện bắt buộc cho bản đồ
án cơ bản**. Bộ khoảng30 câu ở trên là kiểm thử chức năng của nhóm, không thay thế
hoặc nâng điểm các lượt đánh giá cũ. Báo cáo/run/gold đã lưu giữ nguyên.

**Giới hạn thao tác:** bộ30 câu đã dùng đủ **24/24 Google call**, lượt kiểm F2 sau
diagnostic đã dùng đủ **1/1 call riêng**, xác nhận prompt F2 sau sửa cũng dùng đủ
**1/1 call mới**; không retry/đổi model.1 call chưa dùng của tác vụ trước đã dừng, không chuyển sang
tác vụ này. Đợt live tiếp theo cần thống nhất số call mới. Trước mắt giữ cap
1.024 output token/call; chỉ điều chỉnh sau khi thấy nhu cầu thực tế và được thống
nhất. Không đưa key vào source/file mẫu. Người dùng nay cho phép commit/push
feature branch theo ghi chú đầu trang; không tự tạo PR/deploy hoặc chạy workflow
thủ công. CI có trigger push sẵn có có thể chạy trên GitHub. Khi đưa thay đổi vào `main`, dùng feature branch + PR
và **Create a merge commit** theo quy định nhóm.

Riêng cohort ý định/F2 mới được duyệt tối đa12 call và đã kết thúc với **11 call**;
1 call chưa dùng không tự chuyển sang retry hoặc review guard. Giữ cap
1.024 token/call, không đổi model. Focused đã triển khai opt-in và kiểm offline,
không gọi Google; muốn đo protocol/context mới cần prepare/pin mới và thống nhất
budget riêng. Các packet/code pins lịch sử không được cập nhật đè để khớp code mới.
