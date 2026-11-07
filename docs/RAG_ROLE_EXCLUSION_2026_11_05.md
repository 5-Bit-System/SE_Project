# Diagnostic 1a — routing vai trò và loại trừ giảng dạy

05/11/2026, nhánh `crawldata`, base1287e2a, WIP code/data/test/environment đã ghim.
Chỉ chatbot hỏi đáp HUS; BM25 + trích nguồn. [Receipt đầy đủ](acceptance/hus_role_exclusion_report.json).

## Bản sửa và giới hạn

Hai file `question_routing.py`, `answer_support.py`: nhận cách hỏi “vai trò nào/gì”
trong bối cảnh công việc, giữ ưu tiên môn/chương trình/mục tiêu và tránh hiểu vai trò
của doanh nghiệp thành việc làm của cử nhân. Parse lời loại trừ giảng dạy có giới hạn,
giữ phạm vi địa điểm nếu có; “không có” là phủ định dữ kiện, không phải lời loại trừ.
Các yêu cầu dương, số liệu và official phía sau vẫn được kiểm.

Loại nguyên chunk F1-careers có nội dung bị loại trừ trong đúng phạm vi; không sửa
quote/hash/offset. Địa điểm được yêu cầu phải có trong body cùng nhóm nguồn. Đoạn
hỗn hợp có thể bị loại bảo thủ; thiếu bằng chứng sạch thì từ chối, không ghép khác
nguồn/ngành/edition/hệ/review hoặc suy ra không có nghề giảng dạy. Grammar vẫn lexical,
chưa phải hiểu mọi cách hỏi/phủ định tiếng Việt. F2/AI opt-in/release/review giữ nguyên.

## Run mới và kết quả

| Tập | Route positive | Recall@5 | F2 nguồn | Citation integrity | AI đủ ý/tuân thủ | Từ chối sai |
| --- | --- | --- | --- | --- | --- | --- |
| dev96 | 64/64 | 39/40 | 24/24 | 64/64 | 64/64 | 0/64 |
| h2_exposed | 36/36 | 20/20 | 16/16 | 36/36 | 36/36 | 0/36 |
| contracts28 | 26/26 | — | 26/26 | 26/26 | 26/26 | 0/26 |
| dev6_original | 8/8 | 8/8 | — | 8/8 | 8/8 | 0/8 |
| dev6_r2 | 8/8 | 8/8 | — | 8/8 | 8/8 | 0/8 |
| dev7 | 12/12 | 12/12 | — | 12/12 | 12/12 | 0/12 |

Giữ riêng dev6 gốc/r2 và dev7; không gộp biến thể cùng nguồn thành mẫu độc lập.
Dev7 đã freeze14câu trước tuning (12positive+2control edition). Dev6 gốc C003 nay
đi careers đúng; C007 chỉ còn đoạn doanh nghiệp, không trích thêm giảng dạy. Bộ r2
AI đủ ý7/8 →8/8 sau khi sửa C007, khác việc chỉ quote đủ từ khóa trước đây.
F2 H2 raw15/16 và source16/16 giữ riêng; Q048 raw[null]/unknown không bị chuẩn hóa.

Đối chiếu before theo **hash toàn bộ request** từ các run có sẵn trên code trước1a,
gồm run dev7-before mới, không giả tạo một run before đồng nhất hay sửa run cũ.
`response_changes.before_provenance` ghi run/ID/hash từng câu. Case đổi routing
có thể đổi field/top5; đó không phải bằng chứng BM25 mới tốt hơn. JSON báo riêng
routing/filter/retrieval/F2/citation/entailment/đủ ý/từ chối và latency theo ngành/nhóm.

## Review và kiểm chứng

AI đọc mới 17 phản hồi; 197 judgment
kế thừa chỉ khi request/response/gold/audit giống hash và nguồn không đổi.0human
review; không chứng nhận độc lập hoặc hiệu lực trường. H2 vẫn exposed25câu đã tuning;
**Recall độc lập≥90% chưa chứng minh** dù kết quả exposed cao.

49test mới; RED ban đầu23fail/17pass →GREEN313. Review kỹ thuật thấy2Important
(sai chủ thể vai trò, sai phạm vi loại trừ), đã thêm9test RED9fail/40pass →GREEN322
test liên quan. Bản cuối **1882offline đạt/90deselected,50Chromium,
5Node,Ruff đạt**. 968file cũ bảo vệ không đổi; chỉ hai file runtime thay
so với mốc Q027.12measurement/overlay replay cache đúng; code snapshot329file.
PDF kiểm theo regression hash/page/endpoint sẵn có; không phải nghiệm thu lại viewer
thật hoặc PostgreSQL/full-catalog. Các blocker nguồn/official F3 vẫn giữ nguyên.

HTTP local warm một lượt; không suy thành SLO hay cải thiện tốc độ production:

- dev96: p50 32.57 ms / p95 51.69 ms.
- h2_exposed: p50 34.69 ms / p95 100.56 ms.
- contracts28: p50 32.24 ms / p95 82.81 ms.
- dev6_original: p50 9.54 ms / p95 12.33 ms.
- dev6_r2: p50 8.43 ms / p95 12.32 ms.
- dev7: p50 8.38 ms / p95 10.84 ms.

## Hồ sơ

- [dev96: measurement](../data/hus/evaluation/runs/role_exclusion_dev96_20261105/report.json), [AI overlay](../data/hus/evaluation/runs/role_exclusion_dev96_20261105_ai_review/report.json).
- [h2_exposed: measurement](../data/hus/evaluation/runs/role_exclusion_h2_20261105/report.json), [AI overlay](../data/hus/evaluation/runs/role_exclusion_h2_20261105_ai_review/report.json).
- [contracts28: measurement](../data/hus/evaluation/runs/role_exclusion_contracts_20261105/report.json), [AI overlay](../data/hus/evaluation/runs/role_exclusion_contracts_20261105_ai_review/report.json).
- [dev6_original: measurement](../data/hus/evaluation/runs/role_exclusion_dev6_original_20261105/report.json), [AI overlay](../data/hus/evaluation/runs/role_exclusion_dev6_original_20261105_ai_review/report.json).
- [dev6_r2: measurement](../data/hus/evaluation/runs/role_exclusion_dev6_r2_20261105/report.json), [AI overlay](../data/hus/evaluation/runs/role_exclusion_dev6_r2_20261105_ai_review/report.json).
- [dev7: measurement](../data/hus/evaluation/runs/role_exclusion_dev7_20261105/report.json), [AI overlay](../data/hus/evaluation/runs/role_exclusion_dev7_20261105_ai_review/report.json).

[Review/provenance](../data/hus/review/role_exclusion_response_review_v1/policy.json),
[archive code/test/dependency](../data/hus/evaluation/role_exclusion_snapshot_v1/manifest.json).
Replay: `python -m tools.evaluate_hus_chatbot --verify-run data/hus/evaluation/runs/role_exclusion_dev6_original_20261105_ai_review`.
Giữ nguyên A2 và mốc sửa Q027; A3–A5 dùng cùng bản routing/gate mới giữa các nhánh
so sánh. Chưa tải model, gọi provider, commit/push hoặc triển khai.
