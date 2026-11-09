# Diagnostic/dev v1 — HUS RAG

Ngày 03/11/2026. **Development được phép xem và dùng để sửa routing/field/gate.
Không phải holdout độc lập; không có human acceptance hoặc phép đo chất lượng mới.**

96 request, 24 mỗi ngành. Mỗi ngành: 6 F1, 6 F2, 4 F3 opt-in,
4 thiếu bằng chứng, 2 ngoài phạm vi, 2 cần opt-in. Đây là 48 nhóm ý được
diễn đạt hai cách, không phải 96 câu độc lập về ngữ nghĩa. Có 8 prompt được
lặp có chủ đích với AI opt-in true/false, tạo 96 request nhưng 88 chuỗi câu hỏi.

## Cách sử dụng

- `questions.jsonl`: chỉ question_id và request (question/major/version/allow_generated_reference).
  Chỉ phần này được gửi vào API sau khi có yêu cầu đo; không đưa gold/cases vào router.
- `gold.jsonl`: kỳ vọng nháp kế thừa từ P1-1, chỉ đổi question_id. Giữ nguyên
  evidence IDs, facts, source review, warning và giới hạn học vụ/AI.
- `cases.jsonl`: truy vết parent, nhóm paraphrase/contrast và tags; dùng phân tích lỗi.
- `casebook.md`: bảng để người sửa code/reviewer đọc, không phải nguồn runtime.
- `manifest.json`: hash payload, toàn bộ P1-1/P1-2/P2 gốc, phiên bản runtime tại
  thời điểm chuẩn bị và phân bố. Runtime snapshot là thông tin lịch sử, không
  chặn sửa code sau này. Baseline gốc vẫn được kiểm hash khi validate.

Evidence IDs `P11-E...` trỏ tới `../p11_holdout_v1/evidence.jsonl`. Validator kiểm
nguồn gốc qua validator P1-1: record identity/JSON pointer/value/major/version,
review và generated label. Không tạo bản sao corpus hoặc đưa review candidate vào index.
`expected_field` kế thừa là khái niệm đánh giá (ví dụ `course_name`,
`prerequisites.raw_variants`); không ép router dùng đúng tên nội bộ này.

```powershell
python -X utf8 -m tools.validate_hus_diagnostic
python -m pytest tests/hus/test_diagnostic_pack.py tests/hus/test_reviewer_holdout.py -q
```

Validator chỉ đọc file, không import app/answerer/retriever, không chạy RAG,
không tự ký review và không chứng minh paraphrase tương đương ngữ nghĩa.
Gold là đề xuất đích sửa, không suy ra runtime hiện tại đã trả đúng. Trường hợp
chỉ có tên môn được thiết kế để kiểm resolution trong đúng ngành/version; nếu
tên thực sự đa nghĩa thì cần làm rõ, không chọn mã bằng suy đoán.

## Tiêu chí trước khi sửa runtime

Ghim bộ này trước tuning. Đánh giá từng lớp: intent/routing, field/candidate scope,
gate sau retrieval, F2 facts, nguồn/citation và abstention. Ca dương phải có
evidence; ca thiếu nguồn/ngoài phạm vi không có facts/citation; F3 chưa opt-in
không phát nội dung AI. Không nới scope/review hoặc dựng dữ kiện để làm pass dev.
Recall@5 mục tiêu >=90% chỉ được nghiệm thu trên holdout mới được review độc lập;
điểm dev không đại diện chất lượng tổng quát. Không có metric nào được tạo ở bước này.

## Nhật ký exposure — có hiệu lực từ 03/11/2026

P1-1 v1 và lỗi trong prediction P1-2 đã được đọc và dùng để soạn các paraphrase này.
**P1-1 v1 được coi là exposed cho development từ đây; không dùng lại để chứng nhận
holdout độc lập sau tuning.** P1-1/P1-2/P2 gốc giữ nguyên byte và ý nghĩa lịch sử.
Cờ `used_for_retrieval_tuning=false` trong manifest cũ là snapshot lúc soạn;
không phải chứng nhận độc lập hiện tại. Chưa sửa runtime và chưa tuning code
trong bước chuẩn bị này; việc tái sử dụng nguồn/gold đã làm mất tính độc lập
của split cho lần nghiệm thu tương lai. Cần holdout mới >=40 câu có reviewer thật,
kiểm semantic overlap với cả dev này và các bộ cũ trước nghiệm thu cuối.

Phạm vi bộ này là các lớp lỗi đã thấy. Chưa bổ sung full coverage cho version sai,
xung đột mã, basic chat hoặc multi-hop; giữ các regression có sẵn riêng biệt.
