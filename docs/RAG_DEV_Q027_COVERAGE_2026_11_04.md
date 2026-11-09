# DEV-Q027 — sửa coverage bối cảnh nghề nghiệp

Cập nhật 04/11/2026, nhánh `crawldata`, base `1287e2a`, WIP ghim bằng hash.
Chỉ chatbot hỏi đáp HUS; BM25 + trích nguồn, chưa vector/LLM. Snapshot v3 và
mọi kết quả A2 giữ nguyên. [Receipt/pins](acceptance/hus_dev_q027_coverage_report.json).

## Nguyên nhân và bản sửa

DEV-Q027 hỏi công việc trong doanh nghiệp. BM25 đã có đoạn web liệt kê lập trình
viên, phân tích dữ liệu, thống kê, phát triển thuật toán ở vị trí thứ hai; gate
loại từ bối cảnh khỏi yêu cầu rồi lấy nhóm PDF2015 đầu tiên, chỉ nêu nơi làm việc.

Chỉ sửa `app/hus/answer_support.py`: với F1 careers, cụm yêu cầu `doanh nghiệp`/
`công ty` phải có nguyên cụm trong body của cùng nhóm nguồn đã lọc. Metadata/title
và từ rời không đủ; không ghép khác nguồn/ngành/hệ/edition/review/hash. Nếu bối cảnh
và ý cụ thể nằm ở hai chunk cùng nhóm thì giữ citation cho cả hai. Tách từ chối
yêu cầu workplace có giới hạn khỏi điều kiện mới; giữ phủ định dữ kiện và yêu cầu
khẳng định phía sau. Không sửa BM25, routing, dữ liệu, F2, scorer hay review nguồn.

## Kết quả trong run mới

| Tập | Route positive | Recall@5 | F2 theo nguồn | Citation integrity | AI đủ ý | Từ chối sai |
| --- | --- | --- | --- | --- | --- | --- |
| dev96 | 64/64 | 39/40 | 24/24 | 64/64 | 64/64 | 0/64 |
| h2_exposed | 36/36 | 20/20 | 16/16 | 36/36 | 36/36 | 0/36 |
| contracts28 | 26/26 | — | 26/26 | 26/26 | 26/26 | 0/26 |
| dev6 | 8/8 | 8/8 | — | 8/8 | 7/8 | 0/8 |

Dev96 chỉ thay phản hồi DEV-Q027; H2 và contracts giữ nguyên toàn bộ phản hồi.
Trace query/filter/hit/score của các phép so sánh giống hệt trước sửa. Recall dev
vẫn39/40, H2 vẫn20/20; cải thiện là chọn bằng chứng/đủ ý, không phải retrieval.
Đáp án mới chứa đủ bốn vai trò trong nguồn; edition web vẫn `unknown`, không nâng
thành nguồn2015/official/hiện hành. AI đủ ý dev63/64 →64/64 theo chính sách bên dưới.
F2 H2 raw15/16 vẫn giữ, source-contract16/16; Q048 raw[null]/unknown không đổi.
Breakdown ngành/nhóm, routing/filter, quote proxy, entailment và từ chối ở các JSON.

## Diagnostic và review AI

Dev6 gốc và r2 đều freeze trước sửa:8 cách hỏi đã lộ +2 kiểm edition. Bản gốc C003
chỉ hỏi “vai trò” bị route introduction; giữ nguyên pack/run gốc. r2 thêm “công việc”
để tách đo coverage khỏi lỗi routing đó, không thay gold/nguồn hoặc sửa run cũ.
Không lấy các biến thể cùng câu làm mẫu độc lập; cách hỏi chỉ có “vai trò” còn cần
một bước routing riêng. Các run before nằm ở `dev6_career_context_before_20261104`
và `dev6_career_context_r2_before_20261104` trong cây evaluation/runs.

**DEV6-C007 còn chưa tuân thủ ý loại trừ:** đã trả đủ vai trò doanh nghiệp nhưng
vẫn trích thêm giảng dạy dù câu hỏi ghi “Không hỏi giảng dạy”. AI đánh giá entailment
đạt nhưng đủ ý/tuân thủ yêu cầu **không đạt**; vì vậy dev6 r2 AI đủ ý **7/8**, khác
quote coverage8/8 và hai control đúng2/2. Đây là giới hạn xử lý loại trừ đã có,
chưa sửa trong bước coverage workplace; không tuyên bố10/10ngữ nghĩa.

Review mới đọc phản hồi DEV-Q027 và10ca r2; các phản hồi A2 không đổi chỉ kế thừa
judgment AI sau đối chiếu chính xác hash request/response/gold/audit và nguồn không
đổi. Có 11 lượt đọc mới, 179
judgment kế thừa,0human review. Mọi bản ghi gắn measurement/snapshot mới; đây không
phải review độc lập mới cho toàn bộ tập. [Policy và provenance](../data/hus/review/dev_q027_response_review_v1/policy.json).
H2 vẫn exposed25câu từng tuning; Recall độc lập≥90% chưa được chứng minh.

## Kiểm chứng và độ trễ

39test mới; RED coverage và citation tiếp nối, rồi review phát hiện lỗi phủ định
đã RED9fail/30pass →GREEN273test liên quan. Bản cuối: **1.833offline đạt/90deselected,
50ca Chromium,5Node,Ruff đạt**. 895file cũ bảo vệ không đổi; code/data/test/
dependency/environment ổn định qua các lệnh.8run measurement/AIoverlay replay cache
đúng, không inference mới. Lượt full ban đầu bị ngắt để xử lý finding, không dùng
log đó làm kết quả cuối. PDF kiểm theo regression hash/page/endpoint hiện có;
chưa nghiệm thu viewer thật, PostgreSQL/full-catalog hoặc môi trường triển khai.

HTTP local warm một lượt, không phải benchmark production hay cam kết nhanh hơn:

- dev96: p50 25.45 ms, p95 40.88 ms.
- h2_exposed: p50 36.05 ms, p95 96.49 ms.
- contracts28: p50 28.82 ms, p95 80.57 ms.
- dev6: p50 7.71 ms, p95 10.23 ms.

## Hồ sơ tái lập

- [dev96: measurement](../data/hus/evaluation/runs/dev_q027_dev_v1_20261104/report.json), [AI overlay](../data/hus/evaluation/runs/dev_q027_dev_v1_20261104_ai_review/report.json).
- [h2_exposed: measurement](../data/hus/evaluation/runs/dev_q027_h2_exposed_20261104/report.json), [AI overlay](../data/hus/evaluation/runs/dev_q027_h2_exposed_20261104_ai_review/report.json).
- [contracts28: measurement](../data/hus/evaluation/runs/dev_q027_contracts_20261104/report.json), [AI overlay](../data/hus/evaluation/runs/dev_q027_contracts_20261104_ai_review/report.json).
- [dev6: measurement](../data/hus/evaluation/runs/dev_q027_career_context_r2_20261104/report.json), [AI overlay](../data/hus/evaluation/runs/dev_q027_career_context_r2_20261104_ai_review/report.json).

[Code delta và manifest](../data/hus/evaluation/dev_q027_snapshot_v1/manifest.json)
gắn ZIP code A2 với file runtime mới/test mới và before-image; dữ liệu/asset giữ
nguyên. Replay ví dụ: `python -m tools.evaluate_hus_chatbot --verify-run data/hus/evaluation/runs/dev_q027_dev_v1_20261104_ai_review`.
Thử tiếp A3–A5 phải dùng cùng bản gate này cho các nhánh so sánh và vẫn báo riêng
so với A2 lịch sử. Chưa commit/push/deploy, tải model hoặc gọi provider.
