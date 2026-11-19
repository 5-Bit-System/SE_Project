# A7 sau sửa baseline — Recall đạt, chưa đạt toàn bộ nghiệm thu

**Cập nhật sau phép đo:** ba ca lỗi dưới đây đã được dùng để
[sửa baseline và kiểm dev](RAG_A7_LANGUAGE_FOLLOWUP_2026_11_12.md). Bộ này nay
giữ làm dev; các điểm/run/gold/review bên dưới vẫn là kết quả trước sửa,
không đổi thành điểm A7 mới. Cần freeze bộ khác để đánh giá baseline tiếp theo.

Ngày **12/11/2026**, nhánh `hus-llm-rag`, HEAD nền `f61b0fd` và thay đổi local.
Đã freeze và đo **bộ mới 48 câu, 12 mỗi ngành**, review đủ 48 response. **Routed
Recall@5 = 23/24 = 95,83%**, đạt ngưỡng 90%; **đủ ý 33/36 = 91,67%**, còn ba câu
dương tính bị từ chối. Vì vậy **A7 chưa đạt toàn bộ điều kiện**, LLM vẫn tắt.

## Bộ mới và thứ tự đóng băng

[Pack](../data/hus/evaluation/a7_postfix_20261112_r1/pack.json) có mỗi ngành
3 F1/3 F2/3 F3 và 3 control. Có 24 ca retrieval F1/F3, 12 lookup F2 và 12 control:
4 opt-out F3, 4 thiếu trường đánh giá, khác ngành, hai mã cần làm rõ, basic chat
và yêu cầu nội dung chính thức/hiện hành khi nguồn chỉ là AI.

Target F1 và mã môn/chủ đề F2/F3 khác A7 r1/r2 đã dùng tuning. **0/48 trùng nguyên
văn sau chuẩn hóa** với **22 evaluation input files** đã ghim; **0/36 trùng
identity target A7 cũ**. Đây chỉ là phạm vi kiểm đã nêu, không chứng minh chưa từng
thấy chủ đề/ngữ nghĩa trong mọi cuộc hội thoại hoặc test. F1 có các hệ CLC/tài
năng; F2 gồm tín chỉ/tên và tiên quyết **present/unknown/conflict/unresolved**.

Tác giả AI đã thấy corpus/runtime/intent families; reviewer là **cùng root AI,
nonblind, human review 0**. Không gọi bộ này là holdout độc lập hoặc nghiệm thu
học vụ. Nếu dùng kết quả để tuning, giữ bộ này làm dev và freeze bộ khác sau sửa.

Gold trích trực tiếp từ snapshot/canonical records, không gọi RAG/model để chọn
đáp án. Đã rà wording/gold trước inference, sửa một câu hỏi vai trò để không hỏi
tên doanh nghiệp khi nguồn chỉ ghi loại vai trò. Sau khi seal không đổi câu hỏi,
gold, target hoặc runtime để tăng điểm.

Freeze được ghi lúc **19:34:03 +07:00**, trước lệnh thu response; pack SHA-256
`9d47c07b0c9999690adfd51b0758cec30ab7cd4057badf4f270bb40c88973f7c`, manifest
SHA-256 `5fccce4eb65aad644f8775fdba11ab1147f33dd85abdd4ffb43b77258c1097bc`.
Measurement lưu toàn bộ response trước audit/scoring. Executor chỉ nhận raw
request, không nhận gold/source target hoặc thêm hint field/dataset/code.

## Pins và cấu hình đo

- `CURRENT`: **hus-data-20261111-v4**, SHA
  `ed4c1ccb93da50829c6b6b960f22d1a077c433ed0a55c3a1e1bed832c1baf463`.
- Retrieval **lexical**, index **null**; không đổi BM25/routing/guard/data trong
  bước đo. Giữ đúng raw request và request hiệu lực sau mapping version F1.
- `HUS_LLM_ENABLED=false`, model cấu hình `gemini-3.5-flash-lite`, **actual model
  null / inference not run**. F3 dùng dữ liệu AI đã lưu, không gọi Gemini mới.
- Ghim app/schema/service/UI/dependencies/environment/evaluator/new builder/test,
  release/assets và hai dormant prompt hashes: F1/F3 v3
  `0584fcd688c674d1b2f7d4f52146678b6098014fc61f244db0a6a48a74dfabbe`,
  legacy/F2 `61c071ed0834d45f6555c9b12e7d5d4e10ae7f99a61457017a657a7537637a0a`.
- API thật `app.hus.demo:app` qua TestClient; chặn external transport/provider.
  Không nạp `.env`/template/key, product DB/tài khoản hoặc advisor.

## Kết quả đã review

| Chỉ số | Kết quả |
| --- | --- |
| **Routed Recall@5** | **23/24 = 95,83%**, một ca không search vẫn tính miss |
| Conditional Recall@5 | 23/23 = 100%; không dùng thay ngưỡng routed |
| Routing đúng dataset/field positives | 35/36 |
| Facts/type/source F2 | **12/12**; giữ raw null, conflict và unresolved |
| Source integrity câu đã trả lời | **33/33**; toàn bộ 48 ca qua audit theo contract |
| Controls status/content/source audit | **12/12** |
| Review AI entailment trên câu đã trả lời | **33/33** tương đối với nguồn |
| Review AI đủ ý trên mọi positive | **33/36 = 91,67%**, ba từ chối tính fail |
| HTTP/scope/filter errors | 0 |
| Quote coverage proxy | 20/24; không thay entailment hoặc đủ ý |
| Local HTTP p50/p95 | 27,980/64,441 ms, không phải latency mạng/production |

| Ngành | Recall@5 | Đủ ý positives (AI) |
| --- | --- | --- |
| KHMTTT | 6/6 | 9/9 |
| KHDL | 5/6 | 7/9 |
| Toán học | 6/6 | 8/9 |
| Toán Tin | 6/6 | 9/9 |

Root AI đã đọc câu hỏi, target, facts, citation metadata và **toàn bộ text hiển
thị của từng response**. Không dùng audit/schema hoặc số test thay review đủ ý.
`A7P-Q002` trả PDF CLC edition 2019 thay anchor web nhưng vẫn có đủ bậc tiếng
Anh 4/khung 6 bậc, giao tiếp/chuyên môn và đúng hệ; câu không ghim edition F1.
Chấm nội dung pass theo câu hỏi, không đổi gold/proxy để nâng điểm. Q026 dùng
PDF 2015 vẫn đủ nội dung giảng dạy và ghi đúng phiên bản/giới hạn nguồn.

Một số response, đặc biệt Q039, trích rất dài dù đủ ý; phép đo này không chứng
minh diễn đạt tốt hoặc hiệu quả token LLM. F3 chỉ được chấm giữ nội dung nguồn
tham khảo, không xác minh đề cương hoặc độ đúng học thuật của dữ liệu AI.

## Ba ca chưa đạt — giữ nguyên trong run

| Ca | Hiện tượng trong trace |
| --- | --- |
| **A7P-Q013** | Hỏi giới thiệu quyết định đào tạo thí điểm KHDL, nhưng classifier trả F3/suggested_assessment, không search rồi yêu cầu mã môn. |
| **A7P-Q020** | Hỏi nội dung MAT3383 về dữ liệu/kênh thị giác; đã search đúng F3/content và target ở top5 nhưng bị từ chối sau retrieval. |
| **A7P-Q027** | Hỏi học tiếp Toán học gắn tư duy logic/mô hình hóa; đã search F1/further_study, target ở top5 nhưng không có câu trả lời. |

Đây là chẩn đoán từ trace đã lưu, chưa sửa runtime trong lượt đo này. Bước sửa
tiếp theo cần regression tổng quát và negative, giữ nguyên run/gold/review này;
nếu tuning trên ba ca thì bộ mới cũng trở thành dev. Không bật LLM để che các
ca canonical chưa answered.

## Bằng chứng, kiểm và giới hạn

- [Measurement](../data/hus/evaluation/runs/a7_postfix_lexical_20261112_r1/report.json),
  [review 48 exact responses](../data/hus/evaluation/reviews/a7_postfix_ai_20261112_r1.json),
  [score AI](../data/hus/evaluation/runs/a7_postfix_ai_review_20261112_r1/report.json),
  [receipt](../data/hus/qa/20261112/a7_postfix_r1/report.json).
- **108 test liên quan đạt**, gồm 13 regression mới cho cohort/freeze/novelty và
  source binding; RED→GREEN cả biên overlap và source_scope. Ruff/diff/link checks
  đạt. Một cảnh báo Starlette/httpx đã có từ trước. Không chạy lại full repo/UI.
- **2.507 file dữ liệu/runtime/static đã ghim giữ SHA**. Pack/run/gold/review cũ
  không bị ghi đè; replay hai A7 cũ và measurement/review mới đều tái hiện. Pins
  mới khớp code hiện tại; pins evaluator cũ trở thành lịch sử đúng nghĩa.
- **13 URL PDF local** đã tải qua API và kiểm byte/hash, gồm hai trang của cùng
  tài liệu. Không kiểm remote web health hoặc review học vụ/PDF mới.
- Latency là TestClient local sau khởi tạo service/config, không thêm lượt warmup
  chat, giữ request chat đầu; không gồm source auditing/review hoặc mạng thật.
- Không so đây như A/B nhân quả với A7 19/24 cũ: câu hỏi/target sample đã khác.
  0 Google calls; không commit/push/deploy, đổi selector/index hay tự bật L6.

```powershell
# Chỉ replay cache đã seal, không chạy RAG/provider.
python -m tools.evaluate_hus_a7 --replay data/hus/evaluation/runs/a7_postfix_ai_review_20261112_r1
# Tái đo cùng pack, nếu cần, phải chọn --out mới và giữ pins/config.
# Freeze cohort này chỉ dùng cho lượt hiện tại, không tạo lại thành holdout mới.
```

[Tiến độ và các bước tiếp theo](RAG_PROGRESS_AND_NEXT_PLAN.md).
