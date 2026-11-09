# A2 — Baseline BM25 + trích nguồn sau A1/A1b

Ngày **04/11/2026**, nhánh local `crawldata`, base `1287e2a`; code WIP được ghim
bằng hash, không coi base commit là code đã test. Runtime **không sửa trong A2**.
Release `hus-data-20261031-v3`, SHA-256
`27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`.
Pipeline F1/F3 BM25 top 5 + trích nguồn; F2 lookup cấu trúc. Chưa vector/LLM.

**Kết luận:** H2 exposed đạt Recall@5 **20/20** sau các sửa trước, không còn
false refusal trong các ca đo. Dev vẫn có **DEV-Q027 thiếu vai trò nghề nghiệp cụ thể**.
H2 có 25 câu đã dùng tuning, toàn tập đã lộ; **chưa chứng minh Recall độc lập ≥90%**.
Review ngữ nghĩa là AI, human review 0; không xác nhận nguồn còn hiệu lực học vụ.

## Phạm vi và phép đo

Ba tập giữ riêng: dev96, H2 AI-reviewed exposed56 và hợp đồng28 (26 F2,2clarification)
được sao chép từ dev A1/A1b trước inference. Không gộp chúng thành mẫu độc lập.
`tools/evaluate_hus_chatbot.py`, `tools/hus_rag_metrics_v2.py` và
`tools/hus_chatbot_source_audit.py` mới; collector/layer/scorer/oracle cũ giữ nguyên.
Lưu phản hồi/trace trước audit và chấm. Không đưa gold vào request/retrieval.

| Tập | Route đúng (positive) | Recall@5 | F2 raw cũ | F2 hợp đồng nguồn | Citation integrity (đáp án) | AI entailment (đáp án) | AI đủ ý (positive) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dev96 | 64/64 | 39/40 | 24/24 | 24/24 | 64/64 | 64/64 | 63/64 |
| h2_exposed | 36/36 | 20/20 | 15/16 | 16/16 | 36/36 | 36/36 | 36/36 |
| contracts28 | 26/26 | — | không áp dụng | 26/26 | 26/26 | 26/26 | 26/26 |

Recall là macro trên **tất cả** positive F1/F3: top 5 của lần search thực đầu tiên,
đúng anchor/scope; không gọi retriever vẫn tính miss. Conditional Recall báo riêng
trong JSON; lượt này cùng 39/40 và20/20 do mọi ca eligible đều search. F2 không vào Recall.
Filter major/version/mã/hệ/review/AI: **0 lỗi quan sát**, kiểm cả tham số search khi
không có hit; có40/20/0search ở ba tập. Không suy số0 thành bảo đảm mọi cách hỏi.

Từ chối thiếu nguồn/OOS đúng **24/24 dev,16/16 H2**; chặn AI chưa opt-in **8/8,4/4**;
hai clarification hợp đồng **2/2**. False abstention **0/64,0/36,0/26**; HTTP errors0.
DEV-Q027 là câu **trả thiếu ý**, không phải từ chối sai.

## Nguồn, đủ ý và raw score

- H2-Q048 giữ `[null]`/`unknown`, cảnh báo chưa đủ căn cứ kết luận không có tiên quyết.
  F2 raw vẫn **15/16** vì gold lịch sử `[]`; v2 nguồn **16/16**. Không đổi gold/scorer.
- Dev raw anchor **60/64** giữ nguyên. Q004 dùng talent2015 có ghi rõ hệ/phạm vi,
  chấp nhận cho câu không chỉ định hệ; không khái quát sang mọi cử nhân Toán.
  Q049/050 dùng objectives DOCX standard2023, phù hợp câu không chỉ định edition;
  đây là nguồn thay thế, không phải cùng anchor gốc hoặc xác nhận hiện hành.
- **DEV-Q027 thiếu ý:** nguồn standard2015 chỉ nêu nơi làm việc/giảng dạy; câu hỏi
  cần vai trò trong doanh nghiệp. Thiếu các ví dụ lập trình, phân tích dữ liệu,
  thống kê, phát triển thuật toán có ở nguồn gold. Giữ lỗi trong baseline; chỉ sửa
  ở lượt dev sau, không tuning runtime/gold để nâng điểm A2. Gold đã có trong
  top5 thực của câu này; cần ưu tiên chọn nguồn đủ chi tiết trong pool đã có.
- H2-Q043 có đủ hai phần mục tiêu; Q044 có bốn nhóm nghề, giữ “tùy theo năng lực”.
  Nội dung F3 vẫn nhãn AI/chưa official và phải opt-in; nguồn draft giữ draft.

AI đã đọc180 câu/phản hồi và đối chiếu source audits/gold, xem đầy đủ các ngoại lệ,
điều kiện và nguồn thay thế; 126 positive có judgment,54control ghi not_applicable
cho thang semantic. Review gắn request/response/gold/audit hashes, measurement ID,
snapshot code/data, release và run; overlay mới không sửa run inference. **Không gọi
quote coverage hay anchor-match là entailment.** AI entailment ở cấp đáp án,
không phải semantic precision từng citation; metric precision cũ vẫn null.

Proxy phủ quote gold của ranked cases: dev36/40,H2 20/20, không dùng riêng để kết luận đủ ý.
Các trường `failure`, `scope_errors` trong **case** kế thừa raw legacy để đối chiếu:
12 case chương trình ở tập contract có legacy scope-error do schema cũ không hiểu
metadata mới; `raw_legacy=null` ở tập này. Kết luận v2 dùng `filter_errors` và
`f2_contract_correct` (đều đúng trong tập này). Q048 cũng giữ legacy `fact_mismatch`.

## Độ trễ và breakdown

Một lượt tuần tự, local warmed FastAPI TestClient, millisecond; nearest-rank p50/p95.
Chỉ time HTTP POST; init/warmup, JSON/trace capture, source audit và AI review loại
khỏi mẫu. Init/warmup được lưu riêng; chưa phải đo tải, network hay production.

| Tập | N | p50 ms | p95 ms | max ms |
| --- | --- | --- | --- | --- |
| dev96 | 96 | 26.85 | 67.77 | 110.27 |
| h2_exposed | 56 | 32.01 | 88.64 | 108.89 |
| contracts28 | 28 | 26.60 | 68.88 | 75.24 |

| Tập/ngành | Routing | Recall@5 | F2 nguồn | AI đủ ý |
| --- | --- | --- | --- | --- |
| dev96/computer_science | 16/16 | 9/10 | 6/6 | 16/16 |
| dev96/data_science | 16/16 | 10/10 | 6/6 | 16/16 |
| dev96/mathematics | 16/16 | 10/10 | 6/6 | 16/16 |
| dev96/mathematics_informatics | 16/16 | 10/10 | 6/6 | 15/16 |
| h2_exposed/computer_science | 9/9 | 5/5 | 4/4 | 9/9 |
| h2_exposed/data_science | 9/9 | 5/5 | 4/4 | 9/9 |
| h2_exposed/mathematics | 9/9 | 5/5 | 4/4 | 9/9 |
| h2_exposed/mathematics_informatics | 9/9 | 5/5 | 4/4 | 9/9 |
| contracts28/computer_science | 6/6 | — | 6/6 | 6/6 |
| contracts28/data_science | 7/7 | — | 7/7 | 7/7 |
| contracts28/mathematics | 7/7 | — | 7/7 | 7/7 |
| contracts28/mathematics_informatics | 6/6 | — | 6/6 | 6/6 |

JSON mỗi run có `by_major`, `by_category`: routing, filter, retrieval, F2 theo field,
source/semantic, refusal và latency; không chỉ báo số tổng hợp.

## Ghim phiên bản và kiểm chứng

**850 file cũ không đổi**, gồm runtime, scorer/test cũ, data/gold/review và receipt cũ.
Code/data/test/dependency/environment ổn định qua từng lệnh. **31 test evaluator mới**;
regression **1.794 đạt/90 deselected**, **50 ca Chromium,5 Node,Ruff đạt**.
PDF regression kiểm endpoint/binary/hash/trang nguồn; chưa nghiệm thu lại viewer thực.
Không chạy PostgreSQL/full-catalog, promote official F3, commit/push/deploy.

Sáu run gốc/overlay replay đúng, không inference mới, cờ artifact/evaluator hiện tại
đều khớp bản đã ghi. Technical AI review đã tái hiện và sửa các lỗ hổng evaluator:
source envelope/release/marker, binding riêng từng run, filter tham số không hit,
ranh giới timing và preflight release. Final không còn Critical/Important trong scope.

- dev96: [run gốc](../data/hus/evaluation/runs/a2_dev_v1_20261104/report.json), [AI review overlay](../data/hus/evaluation/runs/a2_dev_v1_20261104_ai_review/report.json).
- h2_exposed: [run gốc](../data/hus/evaluation/runs/a2_h2_exposed_20261104/report.json), [AI review overlay](../data/hus/evaluation/runs/a2_h2_exposed_20261104_ai_review/report.json).
- contracts28: [run gốc](../data/hus/evaluation/runs/a2_contracts_20261104/report.json), [AI review overlay](../data/hus/evaluation/runs/a2_contracts_20261104_ai_review/report.json).
- [Receipt tổng và toàn bộ pins](acceptance/hus_chatbot_baseline_a2_report.json).
- [Review AI](../data/hus/review/a2_response_review_v1/policy.json).
- [Snapshot code/test/dependency327file](../data/hus/evaluation/a2_baseline_snapshot_v1/code_snapshot.zip),
  [manifest/hash](../data/hus/evaluation/a2_baseline_snapshot_v1/manifest.json). Archive giữ bytes WIP;
  data release/asset và các tập frozen giữ ở đường dẫn đã ghim, không nhân bản vào ZIP.

Lệnh đo mới (đổi tên `--out`, không ghi đè run):

```powershell
python -m tools.evaluate_hus_chatbot --pack data/hus/evaluation/ai_reviewed_exposed_v1 --out data/hus/evaluation/runs/<fresh-name>
python -m tools.evaluate_hus_chatbot --score-run data/hus/evaluation/runs/<measurement> --review <bound-ai-review.json> --out data/hus/evaluation/runs/<fresh-overlay>
python -m tools.evaluate_hus_chatbot --verify-run data/hus/evaluation/runs/a2_h2_exposed_20261104_ai_review
```

Đây là đối chứng cố định cho A3–A5. DEV-Q027 cần xử lý chọn nguồn/đủ ý ở dev riêng;
thử vector/hybrid/LLM vẫn phải so cùng snapshot và không dùng chúng để nới bằng chứng.
Nghiệm thu độc lập cần bộ mới chưa dùng tuning theo A7; nguồn/triển khai vẫn là luồng riêng.
