# A7 sau lần sửa tiếp theo — Recall100%, chưa đạt toàn bộ nghiệm thu

Nhánh `hus-llm-rag`, HEAD nền `f61b0fd` + WIP có hash trong pins. Đã freeze,
thu response và root AI đọc **48 câu,12 mỗi ngành** trên baseline sau sửa.
**Routed Recall@5 đạt24/24=100%**, nhưng **đủ ý34/36** theo review bảo thủ và
**controls11/12** theo gold đã đóng băng. Vì vậy **chưa nghiệm thu toàn bộ**.
LLM tắt; không gọi Google, đổi runtime/retrieval/data hoặc sửa gold trong phép đo.

**Review bổ sung13/11 đã xong, chưa sửa baseline:** [ba ca và ma trận regression](RAG_A7_THREE_CASE_REVIEW_2026_11_13.md).
Giữ nguyên toàn bộ điểm/run/gold/review bên dưới. Review mới phân biệt lỗi
scope alias CLC, nguồn thay thế không ghim edition và cấu trúc bổ nghĩa assessment;
không chứng nhận hai danh sách học thuật tương đương hoặc nghiệm thu độc lập.

## Bộ mới và thứ tự đóng băng

- [Pack](../data/hus/evaluation/a7_after_followup_20261112_r1/pack.json),
  [run](../data/hus/evaluation/runs/a7_after_followup_lexical_20261112_r1/report.json),
  [review exact output](../data/hus/evaluation/reviews/a7_after_followup_ai_20261112_r1.json),
  [score overlay](../data/hus/evaluation/runs/a7_after_followup_ai_review_20261112_r1/report.json),
  [receipt](../data/hus/qa/20261112/a7_after_followup_r1/report.json).
- Mỗi ngành3 F1/3 F2/3 F3+3 controls; tổng24 retrieval F1/F3,12 lookup F2,
  12 controls. Raw request không có dataset/field/course-code hint riêng; gold
  trích trực tiếp từ snapshot/canonical records, không lấy từ prediction.
- **0/48 trùng wording chuẩn hóa** trong **25 input files** đã ghim;
  **0/36 target ID trùng A7 trước**. Khác identity không chứng minh khác ngữ
  nghĩa: nguồn, runtime, intent families và nhiều nội dung đã được AI thấy.
- Trước prediction đã công bố coverage: hết target F1 introduction chưa dùng;
  F1 gồm4 objectives/6 careers/2 further-study, riêng KHDL3 career roles.
  F2 prerequisites:1 present/1 unknown/2 unresolved, không có conflict mới.
  Không suy bộ48 câu này bao trùm mọi field/hệ hoặc mọi cách hỏi.
- Reviewer được ghim từ pack: **root AI, nonblind/nonindependent, human0**.
  Đã đọc đủ48 exact display cùng facts/citations/target, không chấm từ status
  hoặc quote-equality tự động. Không gọi đây là holdout độc lập/nghiệm thu học vụ.

Freeze lúc **`2026-11-12T17:08:38.480633+00:00`**, trước collection bắt đầu
**`17:08:47.268483+00:00`**, kết thúc **`17:09:05.372025+00:00`**.
Trong freeze, answerer/retriever/provider bị chặn; source draft/gold và pack
khớp nguyên vẹn. Pins được kiểm trước/sau collection, response lưu trước scoring.

| Binding | SHA-256 |
| --- | --- |
| Pack | `ffd439c74a0959b53e652b9af95fa0215b92c3b1ae9be706fdb4c385efe7a5be` |
| Pack manifest | `f6dc71af1a0110a304a90d9c905b43c91875b437a68bce293c88d34075eef7bf` |
| Run manifest | `c73e3c7ffad8516b5418729f089234b3ce852e205fcf07bc9f51d2ad662e98d2` |
| Review overlay manifest | `6372465cba3b8802bbdbac975fca5074dda82c8a044bcaa3b6e29bc190a9a04a` |

## Cấu hình và kết quả

`CURRENT` v4/SHA `ed4c1ccb93da50829c6b6b960f22d1a077c433ed0a55c3a1e1bed832c1baf463`,
lexical, index null, `app.hus.demo:app`, LLM false. Code/data/UI/dependencies/
evaluator/environment/config được ghim. Model cấu hình `gemini-3.5-flash-lite`
và dormant prompt v3/F2 có hash; **actual model null, không có model inference**.
Đây là phép đo local cùng profile, chưa phải chạy trên máy nộp khác.

| Chỉ số | Kết quả |
| --- | --- |
| **Routed Recall@5** | **24/24=100%**, gồm mọi F1/F3 positive; no-call0, không dùng conditional thay ngưỡng |
| Classifier đúng dataset/field positives | 36/36; sau retrieval vẫn có1 false abstention |
| F2 facts/types/source | **12/12**, raw null/slash/newline và unknown/unresolved giữ nguyên |
| Source integrity câu đã trả lời | **35/35**; source audits48/48 không đồng nghĩa status/gold hoặc semantic đều đạt |
| AI entailment câu đã trả lời | **35/35**, tương đối với trích nguồn; không xác minh học vụ |
| AI đủ ý trên mọi positive | **34/36=94,44%**, Q002/Q003 chưa đạt theo target bảo thủ |
| Controls theo frozen gold | **11/12**, Q011 khác status; không bỏ khỏi mẫu hoặc sửa nhãn |
| HTTP/scope/filter errors | 0 |
| Quote coverage proxy | 22/24, không thay review ngữ nghĩa |
| Local HTTP p50/p95 | **27,6521/68,1517ms**, không phải latency mạng/UI/production |

| Ngành | Routed Recall@5 | Đủ ý positives (AI) | Controls theo gold |
| --- | --- | --- | --- |
| KHMTTT | 6/6 | 7/9 | 2/3 |
| KHDL | 6/6 | 9/9 | 3/3 |
| Toán học | 6/6 | 9/9 | 3/3 |
| Toán Tin | 6/6 | 9/9 | 3/3 |

Latency đo TestClient sau nạp service/config, first chat giữ lại, không warmup
chat riêng; không gồm audit/review. Một số câu F3 trả cả ngữ cảnh/chương dài;
đủ ý không chứng minh ngắn gọn hoặc cải thiện diễn đạt.

## Ba điểm chưa chốt — giữ nguyên gold và kết quả

1. **A7F-Q002 — false abstention:** câu nghề nghiệp CLC có target rank1/top5,
   scope high_quality đúng nhưng vẫn bị từ chối. Phân tích cache thấy guard còn
   đòi token `clc` trong body; scope/nhãn có CLC nhưng trích nguồn không lặp từ đó.
   Chưa sửa runtime trong lượt đánh giá, không bỏ qualifier hoặc đổi target để đạt.
2. **A7F-Q003 — nguồn thay thế và scope gold:** output trích DOCX2023 hợp lệ,
   giữ điều kiện học tiếp, nhưng danh sách lĩnh vực khác target web (có “Cơ sở
   toán học cho Tin học”). Câu hỏi không ghim edition. Review entailment pass
   theo source output, **completeness fail bảo thủ** vì chưa chứng minh bao phủ
   target. Không suy hai danh sách tương đương hoặc sửa gold sau inference;
   cần review scope/tiêu chí nguồn thay thế trước cohort tiếp theo.
3. **A7F-Q011 — control status/wording:** gold là no_information cho assessment
   không có nguồn; câu còn dùng “có nội dung gì”, classifier quan sát cả content
   và suggested_assessment nên trả needs_clarification. Người đọc có thể hiểu
   đây là một ý về nội dung đánh giá; cần review wording/hợp đồng, chưa quy hoàn
   toàn cho gold hay runtime. **Giữ control mismatch1/12**, không relabel để nâng điểm.

Các bộ cũ23/24–33/36 và19/24–27/36 giữ nguyên. Bộ mới khác câu/target, nên không
dùng chênh lệch điểm làm A/B nhân quả cho bản sửa. Nếu dùng Q002/Q003/Q011 để
tuning tiếp, giữ bộ này làm dev và freeze bộ khác sau sửa.

## Kiểm chứng và việc tiếp theo

**101 test evaluator/source đạt, gồm13 mới**, Ruff đạt; một cảnh báo Starlette/
httpx đã có. CLI collection wrapper báo exit1 với warning NativeCommandError
trên PowerShell; run vẫn seal đủ48 response, HTTP errors0, manifest/pins và cached
replay kiểm được. Không rerun inference để thay log hoặc làm đẹp exit status.
Không chạy lại full runtime/browser suite vì runtime/UI không đổi trong phép đo.

**2.588/2.589 file đã ghim nguyên SHA**; chỉ evaluator A7 đổi để thêm cohort/pins/
timestamp. Runtime, UI, dependencies, dữ liệu, pack/gold/run/review/receipt/ZIP cũ
không đổi. Có12 lượt kiểm URL binary trên7 tệp khác nhau (PDF/DOCX), đúng hash;
không kiểm remote web health. New/old A7 và L5 cache replay tái hiện, pins mới khớp.

Tiếp theo: review ba điểm trên trước khi chọn sửa hoặc cần người thật phân xử
gold/scope; không sửa ngay trong measurement. L5 v3 vẫn cần prepare mới và ngân
sách Google riêng; gói/checker r2 vẫn là baseline trước lần sửa gần nhất, máy
nộp khác chưa kiểm. LLM/L6 giữ off, không commit/push hoặc deploy từ điểm Recall.
