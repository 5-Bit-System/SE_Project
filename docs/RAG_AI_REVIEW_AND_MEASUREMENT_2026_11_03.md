# Review AI và phép đo RAG — 03/11/2026

Đã hoàn tất review AI 56/56 câu theo quyết định bỏ điều kiện chữ ký người thật
của bạn. Đã sửa ba gold/rubric trong bản dẫn xuất trước inference và đo trên
snapshot runtime/data đã ghim. **Recall@5 chỉ đạt 80%, chưa đạt mục tiêu 90%.**
Đây là tập đánh giá đã lộ, không chứng nhận holdout độc lập.
[Biên bản tổng hợp và kiểm hash](acceptance/hus_ai_review_measurement_report.json).

## Review nguồn, đáp án và trùng ý

[Kết quả từng câu](../data/hus/evaluation/holdout_v2_ai_review_v1/README.md),
[CSV](../data/hus/evaluation/holdout_v2_ai_review_v1/review_results.csv),
[quyết định đầy đủ](../data/hus/evaluation/holdout_v2_ai_review_v1/review_decisions.jsonl)
và [policy](../data/hus/evaluation/holdout_v2_ai_review_v1/policy.json).

- 53 gold dùng nguyên bản được cho đánh giá đã lộ; ba gold/rubric cần sửa.
- Q043 bổ sung nội dung mục tiêu cụ thể, Q044 bổ sung ba nhóm việc làm bị thiếu;
  bốn chunk bổ sung cùng nguồn là phần cần thiết của đáp án, không phải bốn nguồn
  thay thế tương đương độc lập.
- Q048 phải giữ nghĩa ô tiên quyết trống/chưa biết, không suy thành không có điều
  kiện học hoặc đủ điều kiện đăng ký.
- Bốn gợi ý thay thế khác không chứng minh cùng ý: Q002 khác hệ tài năng/chuẩn;
  Q031 khác hệ CLC/chương trình thường và mốc tuyển sinh; hai chunk Q045 nêu ý khác.
- Q024 có đề cương ứng viên 2021 chưa duyệt, chưa ràng buộc cho bản 2023. Từ chối
  assessment official bản 2023 không khẳng định không tồn tại tài liệu khác.

52 câu có nguy cơ trùng ý cao, bốn câu ở mức vừa. 12/16 F2 đã có câu hỏi cùng
mã/ngành/field trong evaluation cũ; tám F3 dương đã có cùng course/field/anchor.
Khác cách viết và 0 cờ trùng chữ không xác nhận độc lập ngữ nghĩa. Reviewer là AI,
số review người thật thực tế vẫn 0; điều này không chặn phép đo theo policy mới.

## Bộ đánh giá và snapshot

[ai_reviewed_exposed_v1](../data/hus/evaluation/ai_reviewed_exposed_v1/README.md)
giữ nguyên 56 câu, 14 mỗi ngành, đủ sáu nhóm, dùng 48 evidence IDs.
[Changes](../data/hus/evaluation/ai_reviewed_exposed_v1/changes.jsonl) ghi ba sửa đổi
gold thực chất. Mọi gold được đánh dấu AI review; trạng thái review nguồn không đổi.
Bộ candidate, worksheet người review, baseline P11/P12/P2 và runtime/source giữ nguyên.

- Pack manifest SHA: `c2733c06f007c0a4299982c058ec40dcaaa3337767042bfc3ce0bc829352ff4e`.
- Question SHA vẫn là `f87686da543e95d2dfd025d476bf15fe567ef671dcc0c2ba8a4163ffa24f5aa1`.
- Release `hus-data-20261031-v3`, SHA `27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`.
- Ghim 111 artifact, runtime/evaluator và môi trường Python 3.11.9; 144 file được
  bảo vệ giữ nguyên. HEAD `1287e2a` chỉ là base; WIP chưa commit, `tested_commit=null`.

[Run gốc](../data/hus/evaluation/runs/h2_ai_reviewed_exposed_v1/report.json),
[metric tách lớp](../data/hus/evaluation/runs/h2_ai_reviewed_exposed_v1/layered_metrics.json),
[predictions](../data/hus/evaluation/runs/h2_ai_reviewed_exposed_v1/predictions.jsonl)
và [input snapshot](../data/hus/evaluation/runs/h2_ai_reviewed_exposed_v1/input_snapshot.json).
Collector chỉ nhận request, lưu đủ 56 observations trước khi scorer tải gold.
Cache đã tái tính khớp và snapshot hiện tại trùng toàn bộ inputs, không thêm inference.

## Kết quả tự động trên snapshot ghim

| Lớp | Kết quả | Ý nghĩa |
| --- | --- | --- |
| Routing dataset + field, trước gate | 28/36 = 77,78% | Tám câu dương sai/thiếu intent |
| Có gọi retrieval, F1/F3 dương | 16/20 = 80% | Bốn câu nội dung F3 bị route sang F2 |
| Routed Recall@5 | 16/20 = 80% | Không gọi search tính miss; Q043/Q044 tính đủ các anchor bổ sung |
| Recall@5 sau khi đã gọi search | 16/16 = 100% | Không dùng mẫu số này để tuyên bố đạt 90% toàn luồng |
| F2 lookup + facts/anchor/oracle | 11/16 = 68,75% | Bốn câu tên không được nhận diện; một mismatch biểu diễn ô trống |
| Citation integrity | 16/16 câu có citation | Nguồn/trang/hash/review hợp lệ không chứng minh đúng câu hỏi |
| Positive có anchor đúng theo scorer | 11/36 = 30,56% | Đây là kiểm anchor tự động; không thay chấm đủ ý |
| Từ chối đúng thiếu nguồn/ngoài phạm vi | 16/16 | Không lẫn vào accuracy routing câu dương |
| Chặn khi chưa AI opt-in | 4/4 | Không có citation/facts rò rỉ |
| Từ chối sai trên câu dương | 20/36 = 55,56% | 16 sau retrieval, bốn tại intent tên môn |
| HTTP / sai ngành / sai edition / sai mã | 0 / 0 / 0 / 0 | Sai dataset/field được báo riêng ở routing |

Bốn citation mà scorer gọi “unjudged alternative” thuộc câu F3 bị trả thành F2.
Không thể mặc nhiên công nhận chúng là nguồn thay thế đúng câu hỏi. Các semantic
fields của scorer cũ giữ `null`; review AI câu trả lời được lưu riêng và không đổi
số đo tự động hoặc giả chữ ký người thật.

## Chấm ngữ nghĩa AI riêng

[AI review đủ 56 câu trả lời đã lưu](acceptance/hus_h2_ai_response_support.json)
tách ba câu hỏi: nguồn có hỗ trợ dữ kiện đã trả không, dữ kiện có đúng điều người
dùng hỏi không, và toàn bộ đáp án có đủ ý không.

- 16/16 citation hỗ trợ dữ kiện thật được trả; 12/16 liên quan đúng yêu cầu.
- 11/36 câu dương trả lời đủ, một câu Q048 partial, 24 câu dương sai/từ chối.
  Tính cả 20 control đúng, tổng đủ yêu cầu là 31/56; không đánh đồng với status
  accuracy 36/56 hoặc citation integrity 16/16.
- Q048 nói đúng “Dòng nguồn không ghi điều kiện tiên quyết”, không suy đủ điều
  kiện học. Tuy nhiên thiếu cảnh báo hiển thị rõ chưa biết/ô trống không có nghĩa
  không cần tiên quyết; vì vậy strict completeness chưa đạt. Tách nhận xét này
  khỏi mismatch kiểu dữ liệu `[]`/`[null]` của metric tự động.
- Không có đáp án F3 được trả đúng dataset trong run này; không dùng run này
  chứng minh chất lượng đáp án AI/nhãn F3. Test opt-in không rò rỉ vẫn đạt.

[Ba ca dev tồn đọng](acceptance/hus_dev_three_cases_ai_review.json) cũng đã được
AI đối chiếu nguồn ghim và binary:Q006 hỗ trợ ý học tiếp chung nhưng thiếu phần
thạc sĩ/tiến sĩ có điều kiện theo gold;Q049/Q050 được nguồn DOCX2023 hỗ trợ đủ.
Không cộng hai nguồn thay thế này vào metric dev cũ hoặc suy điểm semantic toàn
bộ64 câu từ việc chỉ review ba câu.

## Nguyên nhân đã tái hiện từ trace

[Phân tích 25 ca lỗi](acceptance/hus_h2_failure_diagnosis.json) không gọi search/API
lại, chỉ chạy classifier/gate trên các hit đã lưu và đối chiếu nguồn ghim.

1. **16 ca gate:** buộc mọi token còn lại xuất hiện trong từng body. Q001 bị đòi
   cả `edition`, `2008`, `hieu` dù edition đã nằm trong metadata. Các mệnh đề yêu
   cầu chép nguồn/giữ giới hạn/không suy quy định cũng thành điều kiện khớp literal.
2. **Bốn ca tên:** cách hỏi “nguyên tên của mã” chưa có trong luật intent tên môn.
3. **Bốn ca nội dung:** “hình dung trước môn … các chủ đề … AI” khớp `truoc mon`
   của tiên quyết trước khi xét intent nội dung, rồi trả dữ kiện F2 thật nhưng sai ý.
4. **Q048:** scorer so `raw_variants=[]` với giá trị theo source rows `[null]`.
   Giữ nguyên lỗi metric này; lời trả lời và tính đầy đủ của cảnh báo ô trống cần
   được xét riêng.

Ngoài ra handler chỉ lấy tối đa hai chunk sau gate; sửa gate xong vẫn phải kiểm
đáp án đủ bốn nhóm như Q044. “Có một anchor” không đủ làm tiêu chí đủ ý.

## Regression sau phép đo

[Receipt mới](acceptance/hus_h2_ai_regression_report.json) ghi lần chạy sau H2:
**1.479 test offline đạt, 90 deselected, 5 test Node, 50 ca Chromium**. Đã kiểm
API/citation/scope và UI đổi ngành, response cũ, AI opt-in; viewer Chromium thực
mở đúng trang vật lý13/12, plugin loaded và scroll khớp, binary21.509.533 byte
đúng hash. Hai screenshot được AI xem; không thay review học vụ bảng nguồn.

108 pin regression,111 artifact H2,136 file test Python, một file test Node và
môi trường đều giữ nguyên; tái tính cache H2 khớp. Không chạy các marker PostgreSQL,
HUS PostgreSQL và full-catalog acceptance; có cảnh báo Starlette/httpx từ trước.
Không chạy database sản phẩm/VNU/provider hoặc activation production. Test kỹ
thuật đạt không thay kết luận chất lượng RAG chưa đạt từ phép đo mới.

## Lệnh đã dùng

Các lệnh dùng Python3.11.9 trong môi trường CI local đã ghim. Runner mới dùng lại
collector/scorer/oracle sẵn có, không nới validator người review hoặc runtime.

```powershell
python -X utf8 backups/h2_ai_review_finalize/run_ai_exposed_benchmark.py --validate-only
python -X utf8 backups/h2_ai_review_finalize/run_ai_exposed_benchmark.py --out data/hus/evaluation/runs/h2_ai_reviewed_exposed_v1
python -X utf8 backups/h2_ai_review_finalize/run_ai_exposed_benchmark.py --verify-run data/hus/evaluation/runs/h2_ai_reviewed_exposed_v1
```

`--out` chỉ chạy một lần và từ chối ghi đè; các lần kiểm sau dùng cache. Runner
được sao vào run; preflight cần các input snapshot local đã ghi trong receipt.
Lệnh test đầy đủ và hash log/JUnit/browser/PDF nằm trong receipt regression.

## Bước kỹ thuật tiếp theo

Đưa các ca đã xem sang một phiên bản dev mới trước khi sửa runtime. Giữ bản đo
này làm bằng chứng lỗi. Ưu tiên intent tên/mã và “trước môn”, tách ngữ pháp yêu cầu
và scope metadata khỏi các khẳng định thực sự cần bằng chứng; giữ chặn dữ kiện
không có nguồn, điều kiện hệ/ngành/edition, review và AI opt-in. Chốt nghĩa ô trống
và phép chấm; kiểm đủ ý khi cần nhiều chunk. Đo phiên bản sau bằng một run riêng,
không gọi bộ này là holdout độc lập sau tuning.

Sáu blocker nguồn, bốn identity đề xuất, edition/cohort/hiệu lực và phạm vi release
vẫn cần giải quyết riêng. Official F3 chưa bật mặc định. Chưa đạt nghiệm thu chất
lượng; chưa xuất bản hoặc triển khai production.
