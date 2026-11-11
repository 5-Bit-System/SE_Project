# V5 — Hybrid RRF và phép đo đối chứng

Trạng thái: người dùng đã duyệt; triển khai và phép đo V5 hoàn tất local 10/11/2026.
Nhánh `hus-embedding-chromadb`, hiện HEAD `1ad85e3` + V4 WIP đã kiểm chứng.
Chỉ làm local; không commit, push hoặc deploy trong phạm vi này.

## Mục tiêu và ràng buộc

Thử nghiệm BM25, vector và hybrid trên cùng snapshot/code gate để đánh giá
giá trị của Chroma. Giữ canonical làm nguồn quote/citation, F2 lookup riêng,
scope/review/opt-in và fallback V4. Không sửa nguồn, gold/scorer/evidence cũ,
V1–V3 artifact, dependency lock, model/index hoặc support gate để nâng điểm.
LLM và đánh giá cuối A7 không thuộc V5. Lexical vẫn là mặc định trong lúc thử.

## Phương án

Người dùng đã chỉ định top20 mỗi leg, parent dedup, RRF60 và final5.
Đề xuất `HUSHybridRetriever` riêng, cùng giao diện search của V4/BM25,
cộng evaluator v3 mới. Phương án đã được người dùng duyệt.

Sửa trực tiếp BM25 sẽ làm khó giữ đối chứng; chỉ ghép trong một script đo
sẽ chưa cung cấp hybrid mode cho service. Adapter riêng tái sử dụng V4 và
cho phép đo qua cùng đường HTTP mà vẫn giữ evaluator A2 nguyên trạng.

## Thuật toán và policy được ghim

Policy v5 đầu tiên: lexical_k=20, vector_passage_k=20, rrf_constant=60,
final_k=5, weight mỗi leg=1, rank bắt đầu từ1, tie theo canonical parent ID.
Policy và hash phải có trong trace/manifest; không tự tuning trong cùng run.

1. Cả hai leg nhận cùng query và toàn bộ scope. BM25 lọc trước scoring;
   vector dùng canonical allowlist/where V4 trước Chroma top-k. Không lấy
   global top-k rồi mới lọc. Canonical lỗi vẫn fail closed.
2. BM25 lấy tối đa20 parent. Chroma lấy tối đa20 passage, resolve parent như
   V4 và dedup; có thể còn ít hơn20 parent, không overfetch ngầm.
3. Mỗi parent chỉ xuất hiện một lần trong mỗi leg. Xếp parent theo kết quả
   leg và đánh rank liên tiếp sau dedup. Vector giữ thứ tự theo best distance,
   tie theo parent ID như V4.
4. Hợp candidate pool hai leg theo parent ID, tối đa40 parent. RRF(parent)
   = tổng `1/(60 + parent_rank)` trên các leg có parent đó. Parent chỉ có
   ở một leg vẫn hợp lệ. Không cộng raw BM25 score với cosine similarity.
5. Xếp RRF giảm dần/tie ID, lấy tối đa5 canonical parent. Routing, evidence
   gate và CitationResolver xử lý kết quả như trước; không dùng similarity
   để bỏ gate hoặc tự xác nhận đủ ý.

## Fallback và trace

Gọi vector qua `search_with_trace()`, không suy vector thành công từ việc
có hits. Nếu `mode_used=lexical`/có fallback_reason, coi vector leg unavailable,
không đưa bộ BM25 fallback vào RRF như một leg độc lập. Trả top5 BM25 cùng
scope, ghi actual_mode=lexical và lý do; không ghi là hybrid thành công.
Vector thành công nhưng rỗng là một leg rỗng hợp lệ. Không mở rộng scope.

Trace bất biến theo query, không dùng mutable state chia sẻ giữa request:

- requested/actual mode, policy/hash, release/index/model identity, filters;
- lexical top20 parent IDs/rank/raw scores;
- vector top20 passage IDs và parent IDs/rank/raw similarity, success/fallback;
- candidate union, từng hạng đóng góp RRF, fused ordering và final_top5;
- khi đo HTTP, lưu citation/parent sau gate riêng với final retrieval top5.

F2/basic chat/guard từ chối trước retrieval được ghi no_call, không giả trace.
Không log question text/secret vào runtime logger; câu hỏi trong bộ đo nằm
trong artifact đánh giá đã được chủ động tạo, không thu thập hội thoại thật.

## Evaluator v3 và bộ đo

Thêm runner/metrics v3, không thay đổi `evaluate_hus_chatbot.py`,
`hus_rag_metrics_v2.py`, layer scorer hoặc run cũ. Dùng chung source auditor
và validator hiện có ở những phần giữ đúng hợp đồng.

- So ba mode trên cùng code/release/gate/index/model/policy/dependency pins.
  Mỗi mode chạy process riêng trong venv ML đã có, tránh cộng dồn model/RAM.
  Lexical không import ML dù các package có trong venv.
- Đối chứng **vector của V5** cũng lấy20 passage, dedup parent rồi chọn5;
  lexical lấy20 parent rồi chọn5. Hybrid dùng đúng hai candidate pool theo
  cùng policy này. Không âm thầm dùng default5passage của V4 cho đối chứng
  vector. Adapter đo được inject qua answerer/service trong process đánh giá;
  routing/gate/HTTP giữ nguyên. V4 vector thông thường giữ default hiện có;
  report ghi rõ comparator V5 có policy20→5, không gọi là phép đo V4 nguyên bản.
- Dùng dev96/contracts đã exposed làm đối chứng và đề xuất thêm36 ca V5 dev:
  8ca/ngành (paraphrase, tên/mã, phủ định/loại trừ, không dấu; thiếu nguồn,
  OOS, chưa opt-in, sai edition/scope) +1F2 control/ngành. Chốt source/gold,
  tags và manifest trước khi chạy cả ba mode. Điều chỉnh câu hỏi/gold chỉ
  được làm trước freeze, không dựa trên kết quả để hợp thức hóa điểm.
- Bộ mới là diagnostic/dev do AI chuẩn bị và đối chiếu nguồn; ghi exposure,
  reviewer_kind=ai và human0, không gọi là holdout độc lập hoặc thay A7.
- Recall@5 và MRR@5 chỉ tính trên final retrieval parent top5; positive
  F1/F3 không có search được tính miss. Báo candidate/union coverage riêng,
  không dùng top20/union để nâng Recall@5. MRR dùng parent liên quan đầu tiên.
  Gold chỉ vào scorer/auditor sau prediction, không vào retrieval/index.
- Recall mỗi case = số canonical parent gold hợp scope có trong final5 /
  số canonical parent gold duy nhất của case; báo macro trên mọi positive
  F1/F3. MRR@5 = 1/rank của parent gold hợp scope đầu tiên, không hit là0;
  cũng macro trên cùng denominator. Kiểm scope gồm dataset/major/edition/
  field/course/variant theo gold/request. Gold positive thiếu anchor hợp lệ
  phải fail preflight, không được tự loại khỏi denominator. Các định nghĩa
  này thuộc metrics v3; không ghi đè hoặc diễn giải lại báo cáo lịch sử A2.
- Báo theo ngành/family và các nhóm paraphrase/tên-mã/phủ định/không dấu/
  nguồn thiếu; F2/controls có chỉ số riêng, không trộn vào denominator Recall.
- Đo answer status, false refusal, scope/opt-in violations, F2 source facts,
  citation integrity/coverage và chất lượng đủ ý với review AI theo response
  hash mới. Không kế thừa judgment cũ khi response khác, không coi quote
  coverage là entailment. Báo pending nếu chưa có review đủ căn cứ.
- Ghi fallback count/rate và tách query vector thực với fallback; không gọi
  mode vector/hybrid cải thiện khi chỉ chạy bằng BM25 fallback.
- Tách initialization, cold đầu tiên, warm p50/p95, sample count và RAM peak
  process theo API hệ điều hành. Cùng warmup protocol, không đưa warmup vào
  metric. Giữ thời gian build V3 lịch sử với nhãn historical/not_remeasured;
  không build lại write-once index chỉ để đo V5.
- Writer chỉ tạo output mới và seal manifest sau khi kiểm pins trước/sau;
  replay chỉ đọc predictions/trace đã lưu, không gọi inference hoặc provider.

## Quy tắc kết luận đề xuất

Chỉ đề xuất hybrid khi Recall@5 tăng, hoặc Recall@5 bằng và MRR@5 tăng,
trên phép đo đối chứng đã ghim; không có scope/opt-in/citation regression,
không tăng false refusal hoặc giảm source-contract/control correctness.
Nếu chưa đủ review để xác nhận chất lượng câu trả lời, chỉ kết luận về
retrieval và giữ lexical. Báo tradeoff latency/RAM, không tự đặt production
SLO hoặc tuyên bố thống kê từ bộ dev nhỏ.

Nếu không cải thiện theo tiêu chí trên, kết luận giữ lexical. Dù kết quả
thế nào, không tự đổi cấu hình process đang chạy; report recommended_mode
và lý do riêng. Index Chroma và canonical vẫn được giữ nguyên.

## Kiểm chứng và bàn giao

Tests: công thức/rank/tie/dedup/candidate union; parent lặp ở hai leg;
không cộng cosine+BM25; filter trước top-k với distractor ngoài scope;
F3 opt-out; vector fallback không double-count; canonical fail closed;
no-call controls/F2; thread trace isolation; evaluator chặn pool/top5 nhầm
và drift pins; fresh-output/replay integrity. Chạy TDD và regression liên quan.

Real smoke/đo dùng model/index/cache hiện có và bản sao Chroma nếu cần
fault injection; không sửa binary gốc, download hoặc gọi LLM/provider.
Receipt mới ghi hash WIP V4 đầu vào để giữ bằng chứng V4 cũ nguyên trạng.
Bàn giao code, report so ba mode, manifest/trace/replay và recommendation;
chưa commit/push/deploy. Không tuyên bố sản phẩm hoặc A7 hoàn tất từ V5.

## Rà soát thiết kế

Builder check độc lập nêu một điểm cần chốt: candidate budget của đối chứng
vector. Đã chọn20passage→dedup→5parent để so với cùng pool của hybrid, và ghi
rõ khác default5passage của V4. Đây là quyết định đề xuất của người triển khai,
đã được người dùng duyệt cùng toàn bộ thiết kế.
