# A7B sau sửa baseline — đạt Recall, chưa đạt tổng thể

Ngày **13/11/2026**, nhánh `hus-llm-rag`, nền `f61b0fd` + WIP local. Đã freeze, đo và root AI review **48 câu, 12 mỗi ngành**, v4/lexical/LLM tắt. **Routed Recall@5 =22/24=91,67%**, F2 đúng nguồn **12/12**, nhưng **đủ ý27/36**; controls còn lỗi. **Chưa đạt nghiệm thu A7 tổng thể**, chưa có review độc lập/người thật.

## Pack và trình tự đo

- Mỗi ngành3 F1/3 F2/3 F3 và3 controls:24 retrieval positives,12 F2 lookups,12 controls. [Pack nguồn/gold](../data/hus/evaluation/candidates/a7_bounded_request_20261113_r1/pack.json) freeze trước inference; API chỉ nhận request, không nhận gold/chunk ID/hint dataset-field.
- Freeze **16:36:58.820858 UTC (23:36:58 giờ Việt Nam)**, collection **16:37:08.274302–16:37:29.413501 UTC**. Ghim code/data/config/evaluator/environment, policy, index null, model/prompt dormant; pins khớp trước/sau đo và seal QA đầu. Sau đó sửa riêng fixture của test mới làm **pins lệch đúng test đó**, ghi riêng bên dưới; không sửa pins hoặc chấm lại run. Actual model null, không gọi hoặc đo chất lượng LLM.
- **0 nguyên câu trùng** trong131 file input đã kiểm, gồm95 file test scan literal AST. **10/36 target identity tái dùng, đều F1**;0 record F2/F3 tái dùng trong các target A7 đã scan. Không chứng minh không trùng cách diễn đạt được lắp động, khái niệm hoặc kiến thức; tác giả/reviewer biết nguồn/runtime, nonblind/human0, **không là holdout độc lập**.
- Chọn nguồn F1 và câu hỏi trước output; F2/F3 theo thứ tự hash identity cố định của record chưa dùng, không chọn bằng rank/pass. Các required ideas của câu chỉ hỏi một phần nguồn đã khai báo trước inference.
- Lưu [48 exact observations](../data/hus/evaluation/runs/a7_bounded_request_lexical_20261113_r1/observations.json) trước audit/scoring; [measurement](../data/hus/evaluation/runs/a7_bounded_request_lexical_20261113_r1/report.json), [review từng ca](../data/hus/evaluation/reviews/a7_bounded_request_ai_20261113_r1.json), [overlay riêng](../data/hus/evaluation/runs/a7_bounded_request_ai_review_20261113_r1/report.json). Không sửa code, câu hỏi, gold hoặc dữ liệu trong/sau lượt đo này.

## Kết quả

| Chỉ số | Kết quả | Phạm vi |
| --- | ---: | --- |
| Routed Recall@5 | **22/24=91,67%** | Gồm no-call bằng0, đạt mục tiêu90%. |
| Conditional Recall@5 |22/23=95,65%|Chỉ diagnostic, không thay routed Recall.|
| Dataset/field classifier đúng |34/36|Trước guard, không là thành công end-to-end.|
| F2 đúng hợp đồng nguồn |**12/12**|Credits/name/prerequisites mỗi loại4/4; giữ types/raw values/review.|
| Đủ ý theo AI review |**27/36=75%**|9 câu dương bị từ chối; không tính refusal là đủ ý.|
| Integrity / entailment theo nguồn đã cite |27/27 /27/27|Chỉ câu đã trả; không xác nhận sự thật học thuật hoặc độ đủ của cả cohort.|
| Controls theo checker hiện có |**11/12**|Q012 chào hỏi bị từ chối thay vì basic_chat.|
| Controls phù hợp về nghĩa — AI review riêng |**10/12**|Thêm Q036: đúng status làm rõ nhưng lý do hỏi mã học phần sai ngữ cảnh so sánh CTĐT.|
| Lỗi filter / HTTP / provider |0 /0 /0|Không rò nguồn/ngành/opt-in; không chứng minh LLM hoạt động.|

| Ngành | Routed Recall | Đủ ý | F2 đúng nguồn | Controls checker / review nghĩa |
| --- | ---: | ---: | ---: | ---: |
| KHMTTT |6/6|7/9|3/3|2/3 /2/3|
| KHDL |5/6|6/9|3/3|3/3 /3/3|
| Toán học |5/6|6/9|3/3|3/3 /2/3|
| Toán tin |6/6|8/9|3/3|3/3 /3/3|

**Hai cách kiểm control được ghi riêng**, không sửa scorer sau inference. Checker hiện xét status/guardrail/source integrity, chưa chứng minh câu làm rõ đúng lý do. [Review control gắn exact hash](../data/hus/qa/20261113/a7_bounded_request_r1/semantic_controls.json) giữ Q036 là thiếu sót nội dung ngay cả khi status đã đạt. Không nâng kết quả11/12 thành controls hoàn chỉnh.

Latency API local TestClient: p50≈**35,7ms**, p95≈**74,2ms**, max≈83,5ms. Answerer khởi tạo trước collection; không bỏ request đầu hoặc chạy warmup riêng. Thời gian audit/review nằm ngoài HTTP; không là latency browser/mạng/máy khác. Auditor kiểm15 route nguồn bằng bytes/hash/MIME của9 file vật lý (8PDF/1DOCX); không tải nguồn ngoài hoặc review trực quan/học thuật toàn bộ file trong lượt này.

## Ca chưa đạt cần review trước khi chọn sửa

| Nhóm | QID A7B | Quan sát exact output |
| --- | --- | --- |
| Có target nhưng refusal |Q001|CLC/editionunknown/mốc2018 ở rank1, vẫn từ chối; không được mượn mốc2012/hệunknown.|
| Sai field F1 |Q014|Vai trò tại trường,viện route introduction thay careers, target bị loại bởi field.|
| F1 further_study refusal |Q015/Q027|Có target đúng nhưng không trả khả năng/điều kiện học nâng cao và các kỹ năng/hoạt động đã hỏi.|
| F3 objectives refusal |Q009/Q021/Q033/Q045|Đúng route/target nhưng không trả mục tiêu, cả bốn giữ completeness fail.|
| F3 content không search |Q032|Chủ đề “Dự báo và kiểm tra mô hình” bị coi kèm suggested_assessment; làm rõ dù hỏi một chủ đề nội dung.|
| Basic chat |Q012|Chào/chúc ngày học tập bị đưa vào hus_rag/no_information. Không rò dữ kiện nhưng sai luồng.|
| So sánh CTĐT |Q036|Làm rõ bằng yêu cầu mã học phần; status đúng nhưng lý do sai. Không tính đây là xử lý scope đúng toàn bộ.|

Đây là **quan sát lỗi**, chưa là kết luận root cause của mọi token/cú pháp. Chưa sửa runtime từ kết quả A7B; không bỏ ca, đổi gold hoặc nới guard để tăng điểm. Nếu dùng bộ này tuning tiếp, chuyển thành dev và freeze bộ khác sau sửa.

## Ba hợp đồng cũ được giữ riêng

- **A7R-Q025:** câu cũ chưa chọn duy nhất nhánh nguồn. A7B-Q025 chọn rõ PDF2015/hệ chuẩn và trả đúng nguồn; không biến thành sửa hay pass của Q025 cũ, không ép ranking hoặc đổi gold cũ.
- **A7R-Q037:** nguồn chưa chứng minh cả “lịch sử và định hướng”. A7B-Q037 chỉ hỏi tên trước/mốc bắt đầu, đủ chứng cứ nguồn; không bỏ yêu cầu của run cũ hoặc công nhận định hướng mới.
- **DEV-Q002:** nguồn có liệt kê hai hệ nhưng câu “như thế nào” còn liệt kê-vs-so sánh; guard/test cũ vẫn xung đột. Không thay assertion/xfail/skip hay nới guard. Q036 so sánh hai CTĐT không thay được nghiệm thu liệt kê dương đang mở.

Lượt này chốt **cách xử lý trong phép đo: giữ nguyên hành vi và khai báo giới hạn**, chưa phân xử thay reviewer/người dùng về hành vi mới. A7R giữ20/24–18/36–12/12, A7S giữ23/24–32/36–12/12 và mọi artifact cũ.

## Kiểm chứng và giới hạn review

- Builder/freeze/sourcebinding/overlap/pins: TDD **8 fail→8 pass**; nhóm evaluator/candidate/metrics **113 pass**, một warning Starlette/TestClient cũ. Scoped Ruff và diff check đạt. Không chạy lại toàn HUS/repository; lỗi dev DEV-Q002 cũ vẫn được giữ.
- **2.987/2.988 file bảo vệ nguyên SHA**; chỉ evaluator A7 được phép đổi để đăng ký/pin cohort. Thêm builder/test riêng; không đổi runtime, data, old tests/gold/run/review. Replay cached bộ mới/cũ tái hiện; pins A7B khớp khi seal QA đầu, nay stale đúng hash test mới sau sửa fixture. Runtime/source/scorer không đổi. L5r5 vẫn stale năm runtime artifact, chưa prepare/cohort LLM mới.
- Reviewer code context riêng **bị giới hạn phiên, không hoàn thành review**. Sau người dùng yêu cầu tiếp tục, tác giả tự review trước freeze, không thấy finding; **đây là self-review yếu hơn review riêng**, không tuyên bố review độc lập đã đạt. Review nội dung cũng do rootAI nonblind/human0, chưa nghiệm thu của người thật.
- Giữ WIP/receipt local và các hợp đồng còn mở; không diễn giải ba câu mới dễ xác định nguồn hơn thành giải quyết hợp đồng cũ. Không có finding minor tự review ghi nhận; không có quyền stage/commit/push/PR/Actions/deploy hoặc Google call mới.

**Sửa fixture sau freeze, không sửa phép đo:** khi pack thật vừa được lưu, test mới kiểm cấu trúc dùng input thật đã tự thấy câu của chính nó và fail assertion “không trùng”. Đây là lỗi cách ly test, không phải lỗi overlap production. Đã quan sát **1 fail** rồi mock tập known-wording riêng cho test cấu trúc; các test same-cohort/đọc exposure/thử freeze trùng vẫn giữ. Không sửa builder/runtime/gold/scorer, không rerun measurement; hash test mới khác làm pins run cũ stale. Receipt đầu vẫn ghi pins khớp đúng thời điểm seal, không chỉnh lại artifact để che khác biệt.

Sau sửa fixture, nhóm evaluator/candidate/metrics **113 pass**, một warning cũ,74,81 giây; Ruff đạt. [Receipt riêng](../data/hus/qa/20261113/a7_bounded_test_isolation_r1/report.json) xác nhận replay giữ điểm và pins lệch đúng `tests/hus/test_a7_bounded_candidate.py`, manifest `32c886ca74494c0d746ed02807e8cf32c71ed4d0e4fef40db23fd31395981ef9`. Phép đo sau này cần pack/pins mới; không cập nhật pins trong run đã đo.

[QA receipt](../data/hus/qa/20261113/a7_bounded_request_r1/report.json) · [code bindings](../data/hus/qa/20261113/a7_bounded_request_r1/code_bindings.json) · [kế hoạch](superpowers/plans/2026-11-13-hus-a7-bounded-successor.md).

Manifest: pack `d3bf687366e7e07e60f8b9499535679ffae2510275647737a3ca3413ed556d81`; measurement `f86649c3fddbd51443d3f5b2247f3a8c992bf8ca065e314d647327d03c364e18`; overlay `52850c206bda6c786d19f941417dccefe887c9e6e53f01fd9fe8ee71e14e9025`; QA `99343a1befa247563215e7aba3b8a1a58e98264cfc40cefeeea90b63dd7a6607`.

Bước tiếp theo là review chung9 refusal và2 control sai nghĩa trước chọn bản sửa có regression tương tự/negative. Giữ đủ ý/điều kiện/nguồn và điểm vừa seal; không sửa baseline trong lượt đo. L5/L6 vẫn riêng: mọi budget Google hết, LLM mặc định tắt, chỉ xét bật khi có gain/bảo toàn ý/latency thật và operator chấp nhận.
