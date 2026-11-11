# V5 — Hybrid RRF và đối chứng retrieval

10/11/2026, local `hus-embedding-chromadb`, HEAD `1ad85e3` + WIP V4/V5.
Lexical vẫn là mặc định; không commit/push/deploy hoặc gọi LLM/provider.
Thiết kế: [V5](superpowers/specs/2026-11-10-hus-hybrid-retrieval-v5-design.md).
Ba mode đã chạy xong và replay đạt; [comparison đã seal](../data/hus/evaluation/runs/hybrid_v5_comparison_20261110_r1/comparison.json).
Receipt cuối: [V5](acceptance/hus_hybrid_v5_report.json).

## Kết quả đối chứng

160câu/mode =96dev+28contracts+36V5dev;56positive F1/F3 vào Recall/MRR,
54F2 vào source-contract,50control. Không có HTTP/scope/source-audit error;
vector/hybrid đều56lượt vector thật,0fallback trong run thường.

| Mode V5 | Final Recall@5 | MRR@5 | False refusal /110positive | F2 source contract |
| --- | --- | --- | --- | --- |
| Lexical20→5 | 55/56 =98,21% | 0,87649 | 5 | 54/54 |
| Vector20passage→5parent | 55/56 =98,21% | 0,88690 | 6 | 54/54 |
| Hybrid RRF60 | 56/56 =100% | 0,88155 | 5 | 54/54 |

Candidate recall cả3mode là56/56; số đó **không** thay final Recall@5.
Hybrid lấy lại anchor của `DEV-Q050`; đây là ca lịch sử đã có nguồn thay thế
được ghi nhận, nên việc tăng strict anchor Recall không tự chứng minh đáp án
ngữ nghĩa tốt hơn. Status câu trả lời hybrid không đổi so với lexical.
Vector-only làm `DEV-Q052` từ answered thành no_information.

Năm false refusal vốn có từ probe/newpack giữ nguyên: paraphrase nghề nghiệp
của cả4ngành và ca loại trừ giảng dạy của Toán. Không sửa gate/gold để nâng
điểm; đã retrieve đủ anchor không có nghĩa evidence gate sẽ chấp nhận cách hỏi.
Các nhóm paraphrase/tên-mã/phủ định/không dấu mới đều4/4anchor với hybrid;
control thiếu nguồn/OOS/opt-out/sai edition vẫn đúng hợp đồng.

**Quyết định hiện tại: giữ lexical mặc định.** Hybrid đã cải thiện retrieval
trên bộ dev này, nhưng review entailment/completeness theo từng response còn
pending; comparison ghi lý do `semantic_review_pending`. Không tái dùng
judgment cũ cho response khác. Đây không phải chứng nhận Recall độc lập≥90%.

| Mode | Warm p50/p95 toàn160câu (ms) | Warm p50/p95 của56query retrieval (ms) | Cold warmup (ms) | Peak RSS process (MiB) |
| --- | --- | --- | --- | --- |
| Lexical comparator | 35,72 /1554,04 | 1468,60 /1600,73 | 1314,32 | 322,71 |
| Vector comparator | 32,09 /3851,79 | 1666,34 /3949,92 | 20132,18 | 1431,77 |
| Hybrid | 31,63 /3886,07 | 1722,30 /4060,25 | 28410,35 | 1431,02 |

Đây là timing local một lượt của **comparator có canonical checks**, không
phải tốc độ native service BM25 cũ hoặc benchmark production. Cold gồm
lazy initialization/verify/model load. RSS là peak toàn process gồm source
audits; OS cache và run order có thể ảnh hưởng. Không build lại index V3 để
lấy duration; chỉ giữ reference lịch sử, không suy thời gian từ mtime.

## Thuật toán và đường chạy

`app/hus/hybrid_retrieval.py` bổ sung `HUSHybridRetriever`. Mỗi leg nhận cùng
query/scope; BM25 lọc trước scoring và Chroma dùng prefilter canonical V4
trước top-k. Policy cố định: BM25 top20 parent, vector top20 passage,
dedup parent, rank liên tiếp từ1, equal weights, RRF60, final top5.

`RRF(parent) = Σ 1/(60 + rank_parent_trong_leg)`; tie theo canonical parent ID.
Không cộng raw BM25 với cosine. Vector có thể còn ít hơn20 parent sau dedup;
không overfetch. Pool union và toàn fused ranking được giữ riêng với final5.
Quote/citation chỉ lấy từ canonical; routing/support gate không thay đổi.

Vector lỗi hoặc fallback được nhận diện từ trace V4. Hybrid trả BM25 cùng
scope, ghi actual_mode=lexical và lý do; không dùng bộ BM25 fallback làm leg
vector để bỏ phiếu hai lần. Canonical lỗi vẫn fail closed. F2 không gọi ML.
Trace bất biến theo query, không lưu trạng thái request dùng chung.

Chọn `HUS_RETRIEVAL_MODE=hybrid` tường minh và cung cấp ba biến cấu hình
`HUS_VECTOR_INDEX_PATH`, `HUS_VECTOR_MODEL_CACHE`, `HUS_VECTOR_EXPECTED_INDEX_ID`
như V4. V4 vector thông thường vẫn giữ budget mặc định5passage; comparator
vector của V5 dùng20passage→dedup→5parent để so với cùng policy của hybrid.
Không thay đổi cấu hình process đang chạy từ kết quả đánh giá.

## Evaluator và các lớp bằng chứng

Runner mới `tools/evaluate_hus_hybrid.py`, metrics mới
`tools/hus_rag_metrics_v3.py`, so sánh `tools/compare_hus_hybrid.py`.
Các evaluator/gold/run A2 cũ giữ nguyên byte.

- So160câu: dev96 + contracts28 +36V5dev mới. Gold mới lấy từ canonical,
  đóng băng trước inference; tags gồm paraphrase/tên-mã/phủ định/không dấu,
  thiếu nguồn/OOS/opt-out/sai edition và4F2control. Namespace ID nội bộ khi
  ghép pack chỉ tránh va chạm, không thay nội dung hoặc tiêu chí gold cũ.
- Bộ V5 là AI-prepared diagnostic/dev đã exposed, không là holdout hoặc A7.
  Có một probe lexical36câu trước lượt đối chứng chính; không sửa gold/gate
  sau probe. Probe thuộc phiên bản evaluator trước lượt sửa review và không
  được dùng thay kết quả ba run cuối.
- Mỗi mode chạy process riêng trong cùng venv ML hiện có, cùng ordered suite,
  code/gate/data/index/model/policy/environment pins. Lexical không import ML.
  Đo cold/warmup riêng, loại khỏi metric; ghi warm p50/p95 và peak process RSS.
- Recall@5 là macro tỷ lệ canonical gold parent hợp scope xuất hiện trong
  **final5**; MRR@5 dùng gold parent hợp scope đầu tiên. Positive không có
  search vẫn là miss. Candidate recall được báo riêng, không nâng Recall@5.
- Prediction được lưu trước khi scorer/auditor nhận target. Report giữ F2
  source contract, source/citation integrity, scope/opt-in/control failures và
  false refusal riêng với retrieval. Review ngữ nghĩa chưa đủ thì ghi pending;
  quote/anchor coverage không thay entailment hoặc đủ ý.
- Kiểm cả nested vector trace và actual mode, không gọi fallback là vector
  thực. Mọi file run được seal chỉ khi pins trước/sau ổn định. Replay chỉ
  đọc inputs/predictions/audits, không inference hoặc gọi provider.

## Giới hạn phép đo và quyết định

Đây là phép đo local một lượt, thứ tự lexical→vector→hybrid, không tuyên bố
ý nghĩa thống kê, hiệu lực học vụ hoặc SLO production. Comparator lexical V5
có budget20→5 và canonical checks của adapter; latency không phải benchmark
nguyên bản service BM25 mặc định. Các query F2/control rẻ hơn query retrieval,
nên phải phân biệt latency toàn bộ160câu với latency F1/F3 có search.

Index V3 được copy để thử nghiệm, không build lại. Thời gian build chỉ tham
chiếu receipt V3 với nhãn historical/not_remeasured; không phải số đo V5 mới.
Gold anchors là parent nghiêm ngặt, không chứng minh mọi nguồn thay thế sai.
Các lỗi ngôn ngữ của support gate vẫn có thể từ chối câu đã retrieve được.

Chỉ đề xuất hybrid khi final Recall tăng, hoặc Recall bằng và MRR tăng,
không giảm các guard/source contract/citation/chất lượng trả lời; cần review
AI đủ coverage và không suy giảm entailment/completeness/supported-complete.
Nếu chưa đủ bằng chứng thì giữ lexical. Khuyến nghị không tự đổi mode runtime.

## Review kỹ thuật

Review AI độc lập phát hiện2Important: suite order/multiplicity chưa bind
vào pins; recommendation chưa chặn reviewed semantic regressions. Cả hai
được tái hiện RED rồi sửa GREEN trước phép đo chính thức. Tự kiểm tra thêm
phát hiện validator có thể chấp nhận nested vector fallback như RRF leg;
đã có RED→GREEN. Chưa có review người thật; không tuyên bố re-review độc lập
sau lượt sửa. Chi tiết test và regression được ghi trong receipt V5 mới.

## Tái chạy và replay

Ví dụ chỉ đọc lại một run, không nạp model hoặc inference:

```powershell
python -m tools.evaluate_hus_hybrid --replay data/hus/evaluation/runs/hybrid_v5_hybrid_20261110_r1
```

Để đo mới, dùng Python venv ML V3 và `--pack` cho từng pack, `--mode`,
`--index`, `--model-cache`, `--expected-index-id` cùng `--out` **thư mục mới**.
Không chạy lại vào các output đã seal. `tools.compare_hus_hybrid` yêu cầu đủ
3mode, ordered suite và pins giống nhau, process riêng; chỉ ghi recommendation,
không đổi mode. Logs/helper và baseline WIP ở `backups/hybrid_v5_20261110`.

## Kiểm chứng cuối

2103test offline đạt,2skip symlinkWindows,90deselected;50Chromium,5Node,Ruff đạt. Smoke service hybrid12ca, F2noML/F3opt-out, copied-index fallback không double-vote và canonicalHTTP503 đạt. 480prediction replay khớp; nguồn/model/index/lock/evidence lịch sử giữ nguyên. V5 hoàn tất local theo phạm vi triển khai và phép đo; semantic review/A7 còn riêng.
