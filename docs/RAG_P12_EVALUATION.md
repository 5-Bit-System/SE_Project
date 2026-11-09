# P1-2 — Đo retrieval và chất lượng trả lời trên baseline

Ngày đo: **02/11/2026**. Kết luận: **đã đo sơ bộ, chưa đạt mục tiêu top-5 ≥90%,
chưa nghiệm thu độc lập**. Không sửa retrieval, router, answerer hoặc gold để nâng điểm.

## Phạm vi và bằng chứng

- Bộ câu hỏi: [P1-1 v1](../data/hus/evaluation/p11_holdout_v1/README.md), **48 câu**,
  gold nháp có AI hỗ trợ, **0 câu được reviewer con người ký duyệt**.
- Runtime giữ baseline `1287e2a`; code hiện tại còn uncommitted. Portable
  `hus-data-20261031-v3` giữ release hash
  `27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`.
- Thực thi `/hus/chat` của `app.hus.demo:app` qua TestClient, giữ nguyên request
  ngành/version/opt-in; không đưa gold dataset/field/evidence IDs vào runtime.
- Thu thập và lưu đủ 48 prediction trước bước chấm điểm, gồm trace search, hit IDs,
  score, metadata và câu trả lời. Không bỏ ca không gọi retrieval hoặc ca bị từ chối.
- Chỉ chạy bộ này **một lần** để lấy prediction. Các lần kiểm toán sau đọc lại
  observation đã lưu, không hỏi lại RAG hoặc chọn riêng những câu đã thành công.

| Artifact | Nội dung |
| --- | --- |
| [report.json](../data/hus/evaluation/runs/p12_baseline_v1/report.json) | Chỉ số tổng, theo ngành/nhóm, định nghĩa và hash code/data |
| [predictions.jsonl](../data/hus/evaluation/runs/p12_baseline_v1/predictions.jsonl) | 48 request/response thực tế và trace retriever |
| [citation_audits.jsonl](../data/hus/evaluation/runs/p12_baseline_v1/citation_audits.jsonl) | Kiểm chứng nguồn/trang/review/AI bằng EvidenceOracle độc lập |
| [scored_cases.jsonl](../data/hus/evaluation/runs/p12_baseline_v1/scored_cases.jsonl) | Điểm và loại lỗi từng question ID |
| [manifest.json](../data/hus/evaluation/runs/p12_baseline_v1/manifest.json) | Hash các artifact của lần đo, không ghi đè lần cũ |
| [Biên bản kỹ thuật](acceptance/hus_p12_evaluation_report.json) | Tái lập điểm, kiểm thử công cụ đo và giới hạn nghiệm thu |

## Định nghĩa và kết quả

| Chỉ số | Kết quả | Mẫu số / giới hạn |
| --- | ---: | --- |
| **Routed Recall@5 theo anchor nháp** | **8/20 = 40%** | 12 F1 + 8 F3; dùng top-5 của lần gọi retriever thực, không gọi search cũng tính miss; bao gồm lỗi phân loại câu hỏi |
| F1 Recall@5 | 3/12 = 25% | Một anchor được đề xuất cho mỗi câu; chưa có reviewer xác nhận đủ mọi evidence thay thế |
| F3 Recall@5 | 5/8 = 62,5% | Chỉ 8 câu đã bật AI opt-in |
| Lookup F2 đúng dữ kiện và có nguồn | 7/12 = 58,33% | Lookup có cấu trúc, không gộp vào mẫu số Recall@5 |
| Đúng trạng thái kỳ vọng | 22/48 = 45,83% | `answered` / `no_information` / `needs_clarification` theo gold nháp |
| Trả lời thành công có anchor nguồn | 7/32 = 21,875% | Toàn bộ 32 câu có đáp án, gồm cả các ca hệ thống đã từ chối |
| Từ chối không cần thiết trên câu có đáp án | 25/32 = 78,125% | 12 F1, 8 F3 và 5 F2 bị từ chối; HTTP error không bị tính nhầm là abstention |
| Citation precision theo anchor, chấm bảo thủ | 7/7 = 100% | Chỉ 7 citation đã phát ra, đều thuộc F2; không chứng minh citation F1/F3 hoặc toàn bộ claim đúng ngữ nghĩa |
| Citation integrity trên đáp án có citation | 7/7 = 100% | Oracle kiểm quote/row/page/hash/review; nguồn file đã GET và kiểm binary thật |
| Guard đúng trạng thái và không lộ facts/citation | 15/16 = 93,75% | 8 thiếu nguồn + 4 ngoài phạm vi + 4 cần opt-in |
| Từ chối đúng trạng thái, thiếu nguồn/ngoài phạm vi | 11/12 = 91,67% | Q035 trả cần làm rõ thay vì từ chối ngoài phạm vi |
| Yêu cầu opt-in đúng | 4/4 = 100% | Không trả generated content trước đồng ý |
| Ca sai ngành / mã môn / phiên bản được phát hiện | 0 / 0 / 0 | Theo response/citation/trace; phần lớn câu bị từ chối, không suy ra đã bao phủ mọi lỗi scope |
| Lỗi HTTP | 0/48 | Cả 48 response là HTTP 200 |
| Semantic citation precision / source support | **Chưa có** | Để null cho tới khi reviewer độc lập kiểm ý nghĩa claim, nguồn và gold |

Precision theo anchor là phép đo tự động bảo thủ trên nguồn đã đề xuất, không phải
semantic precision đã nghiệm thu. Chỉ **7/32 câu có đáp án được trả thành công**, nên
7/7 citation không được dùng để tuyên bố chất lượng trả lời đạt 100%. Trong lần này
F1 và F3 không tạo đáp án `answered` nào; không có mẫu citation thực phát ra của hai
nhóm đó để kết luận precision.

Mọi chỉ số còn phụ thuộc gold nháp. Câu/nguồn khác anchor có thể vẫn đúng; reviewer
cần kiểm tra các trường hợp đó. Recall có bao gồm router/guard trước search, không
được đổi tên thành Recall thuần BM25. Mục tiêu 90% **chưa đạt ngay ở phép đo sơ bộ**.

## Lỗi quan sát được từ prediction đã lưu

| Nhóm | Số ca | Ví dụ và bằng chứng |
| --- | ---: | --- |
| Không gọi retrieval trên câu F1/F3 có nguồn | 10 | Q001/Q013/Q025/Q037 diễn đạt tự nhiên không được nhận diện; Q019/Q044 có phủ định “chính thức” nhưng bị guard chính thức chặn |
| Có retrieval nhưng sau đó vẫn từ chối | 10 | Q003/Q007/Q020/Q026/Q027/Q031/Q032/Q043 đã có anchor trong top-5 nhưng không thành đáp án; cần kiểm guard yêu cầu mọi từ riêng của câu hỏi đều khớp |
| Lookup F2 không được thực hiện/trả lời | 5 | Q006/Q017/Q030/Q042 không khớp cách nói “học trước”/tên môn hoặc có phủ định; Q016 có “khối lượng tín chỉ” nhưng bị chặn bởi từ “lương” trong danh sách unsupported |
| Guard sai trạng thái kỳ vọng | 1 | Q035 yêu cầu xếp hạng 20 tín chỉ, hệ thống hỏi lại mã môn thay vì nêu ngoài phạm vi |

Đối chiếu trực tiếp 16 guard response: **cả 16 không có facts/citation**. Q035 là sai
phân loại/trạng thái, không phải trường hợp đã trả khuyến nghị hoặc bịa dữ kiện.
Hai nhóm đầu tổng cộng 20 câu; có 8 câu đã truy xuất được anchor nhưng bị từ chối sau
search. Xem `retrieval_calls.parameters`, hit IDs và reply trong artifact để tái kiểm.

Những quan sát này là đầu vào đề xuất việc tiếp theo, chưa có sửa lỗi runtime trong
P1-2. Nếu dùng chính các câu đã thấy lỗi để điều chỉnh router/retrieval, phải coi bộ
này là development/diagnostic và chuẩn bị holdout mới cho lần nghiệm thu cuối.

## Cách tái lập và đọc báo cáo

Kiểm lại chỉ số từ prediction đã đóng băng, **không inference mới**:

```powershell
python -X utf8 -m tools.evaluate_hus_rag --verify-run data/hus/evaluation/runs/p12_baseline_v1
python -m pytest tests/hus/test_rag_evaluation.py tests/hus/test_reviewer_holdout.py -q
```

Lệnh verify kiểm artifact hash, candidate hash, ID joins, điểm từng ca và mọi nhóm
theo ngành/category. Nó báo riêng code công cụ hiện tại có còn khớp hash công cụ tại
lần đo không. Sau lần đo đã sửa một lỗi **chỉ ở công cụ thu thập**: response HTTP500
không phải JSON giờ vẫn giữ status/raw body/trace. Có regression tổng hợp; 48 response
đã lưu đều HTTP200 nên kết quả không đổi. Artifact gốc giữ nguyên, không sửa hash để
giả như dùng phiên bản công cụ mới. Cách tính metric được tái kiểm từ cache.

Khi có lý do chạy một baseline khác, tạo thư mục **mới**:

```powershell
python -X utf8 -m tools.evaluate_hus_rag --out backups/hus_eval/p12_new_run
```

Lệnh inference mới từ chối ghi đè và yêu cầu runtime còn khớp baseline của candidate.
Không chạy lặp để chọn kết quả tốt nhất; ghi rõ snapshot/split/mục đích của lần mới.
P1-1 manifest/receipt có `rag_inference_run=false` là ảnh chụp **lúc chuẩn bị gói**;
run P1-2 mới ghi `holdout_inference_run=true`. Không sửa gói P1-1 để đổi lịch sử.

Không có browser viewer test, website-health check, provider/LLM call, VNU login,
database sản phẩm hoặc deployment trong phép đo này. P0-2/P0-3 giữ bằng chứng viewer
lịch sử riêng; TestClient/PDF binary GET không thay kiểm giao diện trình duyệt.

## Các bước tiếp theo

1. Reviewer độc lập kiểm gold/nguồn/semantic overlap và đánh giá ý nghĩa câu trả lời;
   hiện chưa ký nghiệm thu P1-1/P1-2 hoặc semantic metrics.
2. Nếu chọn sửa coverage, dùng phiên bản diagnostic/dev riêng, giữ baseline 40% này;
   ưu tiên intent/paraphrase, phủ định, “khối lượng” và guard sau search.
3. Chuẩn bị holdout mới độc lập trước khi công bố kết quả sau tuning; báo rõ mẫu số,
   Recall có/không router, tỷ lệ từ chối và precision theo nguồn/claim.

Các thay đổi P1-1/P1-2 hiện ở local trên crawldata, chưa commit/push; không có CI
remote mới hoặc nghiệm thu production được suy ra từ những kết quả này.
