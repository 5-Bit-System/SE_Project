# A7 sau sửa scope/assessment — Recall đạt, chưa nghiệm thu toàn bộ

**Review tiếp đã xong:** [bốn ca và nguyên nhân router/guard](RAG_A7S_FOUR_CASE_REVIEW_2026_11_13.md).
**Sau review đã sửa runtime:** [cú pháp/role scope và regression](RAG_REQUEST_ROLE_REPAIR_2026_11_13.md).
Phần đo/điểm bên dưới giữ nguyên; bộ này dùng tuning nên là dev, pins cũ không
còn khớp code. Không chấm lại hoặc gọi kết quả diagnostic là điểm A7 mới.

Ngày **13/11/2026**, nhánh `hus-llm-rag`, nền `f61b0fd` + WIP có hash trong pins.
Đã đo và root AI review đủ **48 câu,12 mỗi ngành** trên candidate đã freeze.
**Routed Recall@5 =23/24=95,83%** đạt mục tiêu≥90%, nhưng **đủ ý32/36**;
ba câu bị từ chối và một câu trả sai loại thông tin. Không kết luận nghiệm thu
toàn bộ. Giữ v4/lexical/LLM tắt, không Google hoặc GitHub/deploy.

## Bộ đã ghim và trình tự

- [Pack đã freeze](../data/hus/evaluation/candidates/a7_scope_assessment_20261113_r1/pack.json),
  [measurement](../data/hus/evaluation/runs/a7_scope_assessment_lexical_20261113_r1/report.json),
  [review exact output](../data/hus/evaluation/reviews/a7_scope_assessment_ai_20261113_r1.json),
  [score overlay](../data/hus/evaluation/runs/a7_scope_assessment_ai_review_20261113_r1/report.json),
  [receipt](../data/hus/qa/20261113/a7_scope_assessment_r1/report.json).
- Mỗi ngành3 F1/3 F2/3 F3 và3 controls:24 retrieval positives,12 F2 lookups,
  12 controls. Chỉ gửi raw request; không đưa gold/target ID cho runtime.
- Freeze **04:43:52.414931 UTC**, collection **08:17:29.448762–08:17:49.788360 UTC**.
  Pins trước/sau khớp candidate; response lưu trước source audit/scoring.
  Code/data/config/index/model/prompt/evaluator/environment đã ghim; model thực
  null, không inference LLM. Dormant model cấu hình không là model đã chạy.
- 0 wording overlap trong31 input files đã kiểm; **6/36 target identity tái dùng**,
  gồm Q013/Q014/Q015/Q026/Q038/Q039. Nguồn, runtime, concepts/intent đã lộ;
  ba ngành có MAT1202 cùng nội dung chủ đề nên khác mã identity không có nghĩa
  khác kiến thức. Không dùng bộ này làm holdout độc lập.
- Reviewer: **root AI, nonblind/nonindependent, đã thấy nguồn/runtime, human0**.
  Đã đọc từng exact reply, facts/citation/scope và target; source audits là kiểm
  riêng, không tự chuyển hash/quote đúng thành review semantic pass.

## Kết quả

| Chỉ số | Kết quả |
| --- | --- |
| **Routed Recall@5, gồm no-call** | **23/24=95,83%**, đạt≥90%;24/24 có search,0 no-call misses |
| Conditional Recall@5 | Cũng23/24 do mọi retrieval positive đều search; không dùng thay Routed Recall |
| Classifier đúng dataset/field |35/36; Q015 sai field |
| F2 facts/status/source | **12/12**,4 credits/4 prerequisites/4 name |
| Source integrity câu positive đã trả lời | **33/33**; audits48/48 đạt |
| Entailment AI tương đối với nguồn đã trích | **33/33**; không đồng nghĩa đúng yêu cầu — Q015 vẫn fail đủ ý |
| Đủ ý AI trên tất cả positive | **32/36=88,89%**, không bỏ ba câu từ chối khỏi denominator |
| Controls | **12/12**, gồm consent4, thiếu nguồn/out-of-scope5, nhiều ý2, basic1 |
| False abstention sau retrieval | **3/36**: Q013/Q027/Q037 |
| Scope/filter violations; HTTP errors |0; có1 target bị loại do filter field sai ở Q015 |
| Quote coverage proxy |20/24; không thay review entailment/đủ ý |
| Local HTTP p50/p95 | **30,2289/74,462ms**,48 mẫu, first chat giữ lại; không gồm source audit/review |
| All technical gates / independent acceptance | **false / false** |

| Ngành | Routed Recall@5 | Đủ ý positive (AI) | Controls |
| --- | --- | --- | --- |
| KHMTTT |6/6|9/9|3/3|
| KHDL |5/6|7/9|3/3|
| Toán học |6/6|8/9|3/3|
| Toán Tin |6/6|8/9|3/3|

F2 giữ `[null]`/unknown cho tiên quyết MAT2300 Toán học, không biến thành
“không có tiên quyết”. Sign-off cấp dự án của KHMTTT và draft_unverified ở các
ngành khác giữ nguyên. F3 giữ AI/opt-in; đủ ý ở đây tương đối với tham khảo AI
đã lưu, không xác nhận đề cương hoặc hiệu lực học vụ.

## Bốn ca chưa đạt — chỉ đọc trace đã lưu, chưa sửa baseline

| Ca | Quan sát | Cách giữ kết quả |
| --- | --- | --- |
| Q013 — KHDL careers | Target lập trình viên/quản trị dự án/trưởng phòng “tùy theo năng lực” ở rank1; response no_information. | Đủ ý fail, không entailment cho câu không trả lời; cần chẩn đoán guard riêng. |
| Q015 — KHDL roles | Classifier chọn introduction thay careers; chỉ search introduction. Reply nêu giới thiệu/ba lĩnh vực/kỹ năng, thiếu giảng viên/nghiên cứu viên/chuyên viên kỹ thuật ở trường/viện. | Recall miss và đủ ý fail. Trích nguồn thật chỉ cho entailment theo citation, không cho điểm relevance. |
| Q027 — Toán học further study | Target2015/standard ở rank1 nhưng no_information. | Giữ đủ ý fail; chưa xác định nguyên nhân guard bằng probe mới. |
| Q037 — Toán Tin objectives | Target2015/standard ở rank1 nhưng no_information. | Giữ đủ ý fail; không đổi edition/hệ/gold để đạt. |

Nguồn học tiếp Q003 hiện được câu hỏi ghim DOCX2023/standard và giữ điều kiện
đủ điều kiện/có nhu cầu. Kết quả này không sửa điểm Q003 cũ, không chứng minh
hai danh sách học thuật từ web/DOCX tương đương. Một số F3 trả thêm nhiều đoạn
nguồn ngoài chủ đề hỏi; bảo toàn target không chứng minh ngắn gọn/diễn đạt tốt.

## Kiểm chứng và phần tiếp theo

**61 test evaluator/candidate/metrics đạt**, một warning Starlette/httpx hiện có.
Không sửa code nên không chạy lại toàn bộ runtime/LLM. **2.819/2.819 file cũ**
đã ghim giữ SHA, gồm runtime/data/gold/run/review; cached replay measurement,
overlay mới và overlay A7F cũ tái hiện, không answerer/search/provider/network.
Old A7F vẫn Recall24/24, đủ ý34/36, controls11/12; không chấm lại.

| Binding | SHA-256 |
| --- | --- |
| Pack manifest |`623c8d3185e6651fffddd3fc11a52fe39f5f6b9a34d0ff4c5daa192edcc19f9a`|
| Run manifest |`0a800e1b456406d006aafa6b6bf2ad9f750c1ad013c0aa197a2a399a2113a25f`|
| Review overlay manifest |`52b11aab7a53080ffccd1ad2315b98805bc516d5205c4dc1fef6e41656f737cb`|
| QA manifest |`878fe4ae3d263be82df17d6b346b122c54f6d70d841ea4e485c55ce20ef99547`|

Bước tiếp theo là review nguyên nhân chung của ba guard refusal và một route
sai trước khi chọn sửa. Không vá QID/hạ tiêu chí/đổi run-gold-review. Nếu dùng
bộ này tuning, chuyển nó thành dev rồi freeze bộ khác trước phép đo sau.
Review AI không là nghiệm thu độc lập; đánh giá học vụ cần reviewer phù hợp.
L5 vẫn cần prepare/ngân sách Google riêng, L6 giữ off. Không stage/commit/push,
PR/Actions/deploy; Linux/macOS/remote clone chưa được kiểm từ phép đo này.
