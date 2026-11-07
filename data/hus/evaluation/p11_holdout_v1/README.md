# P1-1 — Bộ câu hỏi cho reviewer và holdout dự kiến v1

Ngày soạn: **02/11/2026**. Trạng thái: **đã chuẩn bị, chờ review độc lập**.
Có **48 câu, 40 evidence IDs**; mỗi ngành có 12 câu.

Đây là bản nháp có hỗ trợ AI, soạn từ record/quote của release đã ghim và quy tắc
phạm vi. Chưa có reviewer con người xác nhận; không gọi đây là holdout đã nghiệm thu
hoặc dữ liệu học vụ đã được xác minh. Không lấy dự đoán của RAG làm đáp án chuẩn,
không chạy RAG hay điều chỉnh retrieval theo các câu của bộ này trong P1-1.

## Thành phần

| File | Vai trò |
| --- | --- |
| `questions.jsonl` | Chỉ question ID và request: câu hỏi, ngành, phiên bản, AI opt-in. Không đưa nhãn/gold field/dataset/code suy ra vào request |
| `gold.jsonl` | Đáp án kỳ vọng dạng nháp, trạng thái, dữ kiện có cấu trúc, evidence IDs, yêu cầu từ chối/nhãn AI |
| `evidence.jsonl` | Evidence ID → file nguồn ghim hash, record/chunk ID, JSON pointer, giá trị/quote, scope, citation và review gốc |
| `review_decisions.jsonl` | Mẫu 48 dòng chờ duyệt, ghim hash từng question/gold; reviewer và reviewed_at đều null |
| `reviewer_packet.md` | Bản đọc thuận tiện gồm câu hỏi, đáp án nháp và evidence IDs; không thay việc mở nguồn |
| `manifest.json` | Hash 6 payload, nguồn release, 7 bộ câu hỏi development cũ, code baseline, phân bố và giới hạn độc lập |

| Nhóm | Mỗi ngành | Tổng |
| --- | ---: | ---: |
| F1 có nguồn | 3 | 12 |
| F2 tra dữ kiện | 3 | 12 |
| F3 tham khảo, đã bật AI | 2 | 8 |
| Thiếu bằng chứng chính thức/lớp đang mở | 2 | 8 |
| Ngoài phạm vi | 1 | 4 |
| F3 chưa đồng ý opt-in | 1 | 4 |
| **Tổng** | **12** | **48** |

Bốn ngành: Toán học, Toán tin, KHMTTT và Khoa học dữ liệu. Câu hỏi có diễn đạt tự
nhiên, chữ viết tắt và mã có hậu tố E. Bộ này chưa phủ hết mọi alias, conflict,
multi-hop, phiên bản sai hoặc basic chat; các regression hiện có vẫn giữ riêng.

## Cách reviewer làm việc

1. Chạy validator ở repository root để kiểm hash/source/join. Không sửa runtime
   hoặc chạy retrieval để chọn đáp án có lợi cho hệ thống.
2. Đọc `reviewer_packet.md`; với mỗi `P11-Q...`, tra gold và các `P11-E...`.
   Mở file trong `source_ref.path`, tìm đúng identity và JSON pointer. F1 có quote;
   F2 có giá trị nguồn và PDF locators; F3 chỉ là nội dung AI tham khảo.
3. Kiểm câu hỏi có tự nhiên, đủ identity, đúng ngành/edition/biến thể; đáp án có
   đúng ý và đủ nguồn không. Các IDs là anchor đã đề xuất, không có nghĩa mọi nguồn
   thay thế đều sai. Ghi thêm nguồn tương đương hỗ trợ đầy đủ claim khi có.
4. Với `absence_check`, giá trị null trong snapshot là lý do **không đủ bằng chứng**,
   không chứng minh ngoài đời không tồn tại dữ kiện đó. Không hiển thị absence ID như
   citation cho một khẳng định học vụ. `expected_citations=[]` ở ca từ chối.
5. F3 đã opt-in phải có nhãn **“kiến thức AI”**, không dẫn PDF F2 làm nguồn nội dung,
   không biến đề xuất thành đánh giá/tỷ lệ thi chính thức. Khi opt-in tắt, yêu cầu
   đồng ý trước và không tiết lộ generated content.
6. Kiểm semantic overlap với bộ development cũ, cả những câu cùng ý nhưng khác
   cách diễn đạt. Validator chỉ kiểm trùng sau chuẩn hóa, chưa đo tính độc lập ngữ
   nghĩa. Việc trùng mã môn/nguồn không tự chứng minh rò rỉ câu hỏi hoặc độc lập.
7. Copy mẫu `review_decisions.jsonl` sang một file review riêng, ví dụ
   `data/hus/evaluation/reviews/p11_v1_<reviewer>_20261102.jsonl`; giữ question/gold
   hashes, điền reviewer thật, thời gian có múi giờ, `reviewer_kind=human`, quyết định
   accept/reject/revise và lý do. Đánh dấu hai mục kiểm overlap/alternative evidence
   chỉ khi đã thực hiện. Không điền tên giả hoặc tự ký thay reviewer.
8. Chỉ chốt bộ holdout sau khi đủ câu được duyệt độc lập (ít nhất 40), giải quyết
   câu revise/reject và lưu biên bản quyết định. Không sửa frozen v1 để hợp thức hóa
   kết quả; nếu sửa nội dung thì tạo phiên bản mới, ghim lại và review lại phần đổi.

Mẫu trong v1 giữ pending để tái lập gói soạn ban đầu. Validator v1 kiểm mẫu và tính
toàn vẹn của candidate; **không cấp human acceptance** và không đọc file review ngoài
gói để tự nâng trạng thái. Người duyệt có thể xem đáp án/nguồn; phần phát triển và
điều chỉnh retrieval phải tránh dùng những câu đó cho đến lần đánh giá đã chốt.

## Tách khỏi development và đo lường

Gói đặt ở `data/hus/evaluation/`, ngoài `data/hus/rag/`; loader/retriever, launcher
và smoke hiện tại không nạp thư mục này. Bảy bộ lookup/acceptance cũ được ghim riêng
trong manifest. Khi soạn v1, đối chiếu 914 chuỗi development sau chuẩn hóa cho kết
quả **0 trùng chính xác**; chưa phải chứng nhận độc lập về người soạn hay ngữ nghĩa.

Giữ `questions.jsonl` tách khỏi gold/evidence khi đưa vào runner P1-2. Không lấy
category, expected_dataset/field hoặc expected_facts từ gold để giúp retriever.
P1-1 chưa chạy trả lời RAG trên 48 câu và chưa có Recall@5/citation precision/source
support/abstention score. Việc pass validator không phải pass RAG.

Khi thiết kế phép đo P1-2, tách **20 câu F1/F3 có thể truy xuất** khỏi **12 câu F2
lookup có cấu trúc**; không gán Recall@5 cho 48 câu gồm cả ca từ chối/opt-in. Đánh
giá source support/citation trên 32 câu có đáp án, và báo riêng 16 ca thiếu nguồn,
ngoài phạm vi hoặc chưa opt-in. Mẫu còn nhỏ; báo rõ mẫu số và phạm vi từng chỉ số.

Nếu sau này xem lỗi trên bộ này rồi điều chỉnh retrieval, bộ đó đã bị dùng cho
development. Ghi nhận việc sử dụng, không tiếp tục báo kết quả trên nó như holdout
độc lập; chuẩn bị phiên bản câu hỏi mới để đánh giá cuối. Repository và manifest
không thể tự bảo đảm người sửa code chưa xem câu hỏi: cần kỷ luật review và nhật ký.

## Lệnh kiểm tra

```powershell
python -X utf8 -m tools.validate_hus_holdout
python -m pytest tests/hus/test_reviewer_holdout.py -q
```

Có thể lưu report mới, không ghi đè lần cũ:

```powershell
python -X utf8 -m tools.validate_hus_holdout --out backups/hus_holdout/p11_validation_01.json
```

Validator không import app/answerer/retriever và không gửi HTTP. Nó kiểm hash, scope,
giá trị nguồn, quan hệ ID, trùng development, opt-in và nhãn AI; không tự đánh giá ý
nghĩa một câu hỏi/đáp án, tính đúng học vụ hoặc độ mở được của website ngoài.
