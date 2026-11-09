# Trạng thái các gói đánh giá HUS

Cập nhật **03/11/2026**, local trên `crawldata`, chưa commit/push.

| Gói/lần chạy | Trạng thái |
| --- | --- |
| [Đo dev trên snapshot ghim](runs/dev_pinned_remeasurement_v1/report.json) |96 request mới,routing64/64 câu dương,scoped Recall39/40,F224/24; [metric tách lớp](runs/dev_pinned_remeasurement_v1/layered_metrics.json);không nghiệm thu holdout |
| [Holdout mới v2 candidate](holdout_v2_candidate/README.md) |56 câu/44 evidence IDs,0 human acceptance,0 inference; bạn nhận review; chưa xác nhận độc lập ngữ nghĩa |
| [Worksheet review v2](holdout_v2_review/README.md) |56 dòng CSV/JSONL pending; đối chiếu99.344 cặp,0 exact/strong lexical flags nhưng semantic overlap vẫn chờ;8 gợi ý nguồn thay thế chưa duyệt |
| [P1-1 candidate v1](p11_holdout_v1/README.md) | 48 câu, 40 evidence IDs; bản nháp AI hỗ trợ, 0 human acceptance; đã exposed để soạn dev từ 03/11/2026, không còn dùng làm holdout độc lập sau tuning |
| [Diagnostic/dev v1](diagnostic_dev_v1/README.md) | 96 request/88 chuỗi câu hỏi, 24 request mỗi ngành; gói soạn giữ nguyên; đã dùng sửa routing và đo dev trước–sau, không phải nghiệm thu độc lập |
| [Dev trước routing](runs/dev_before_routing_v1/report.json) | Recall@5 6/40, F2 0/24, guard20/32; runtime cũ, không ghi đè baseline P1-2 |
| [Dev sau routing](runs/dev_after_routing_v1/report.json) | Recall@5 39/40, F2 24/24, guard32/32; nguồn theo anchor61/64; semantic review còn chờ |
| [P1-2 baseline v1](runs/p12_baseline_v1/report.json) | Đã chạy RAG một lần trên đủ 48 câu; routed Recall@5 8/20=40%, F2 lookup 7/12, nguồn hỗ trợ 7/32; chưa đạt 90% |
| [Biên bản P1-2](../../../docs/RAG_P12_EVALUATION.md) | Định nghĩa, mẫu số, phân tích lỗi, citation/semantic limits và cách tái tính từ cache |

P1-1 manifest/receipt và các cờ `rag_inference_run=false` là snapshot **khi chuẩn bị
candidate**. Run P1-2 ghi `holdout_inference_run=true`; nguồn sự thật về việc đã đo
là run/report mới, không sửa artifact P1-1 để đổi lịch sử. Human review và semantic
metrics vẫn đang chờ; kỹ thuật pass không thay nghiệm thu độc lập.

Các lần verify đọc prediction đã lưu, không hỏi lại RAG. Đã sửa runtime routing,
field và gate; source/gold/baseline giữ nguyên. Từ 03/11/2026, P1-1 và phân tích lỗi
P1-2 đã được dùng để soạn tập diagnostic/dev. Giữ nguyên byte các artifact cũ và
các cờ lịch sử; trạng thái hiện hành là exposed cho development. Cần holdout mới
được review độc lập cho nghiệm thu sau tuning; điểm dev không thay nghiệm thu đó.

Cờ `rag_inference_run=false` ở manifest gói dev là snapshot lúc chuẩn bị;
hai run mới ghi `development_inference_run=true`, `holdout_eligible=false` và
`tested_commit=null` với runtime/evaluator hashes. Không dùng cờ snapshot cũ để
phủ nhận các phép đo/tuning hiện tại. Xem [báo cáo sửa routing](../../../docs/RAG_ROUTING_FIXES_2026_11_03.md).

Thư mục `evaluation/` không được runtime loader/index nạp; dữ liệu trả lời vẫn nằm
trong release đã ghim ở `data/hus/rag/`.

Holdout v2 mới **chưa chạy app/retrieval**. Candidate là nháp AI có exposure
runtime/dev, không gọi là độc lập người soạn. Bạn cần duyệt nguồn/đáp án/trùng ý/
nguồn thay thế,loại hoặc sửa các câu chưa phù hợp, rồi chốt>=40 câu trước nghiệm thu.
Hướng dẫn phép đo và điều kiện xuất bản/production:
[review→release gates](../../../docs/RAG_REVIEW_RELEASE_GATES_2026_11_03.md).
