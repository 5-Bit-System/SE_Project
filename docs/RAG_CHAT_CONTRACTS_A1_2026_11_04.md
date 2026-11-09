# A1 — Hợp đồng hỏi đáp F2 và mỗi lượt hỏi

Ngày 04/11/2026, local `crawldata`, release `hus-data-20261031-v3` giữ nguyên.
Phạm vi là chatbot hỏi đáp HUS; không nối chatbot đề xuất môn học.

`facts.prerequisite_status` mô tả cách đọc nguồn, tách biệt với
`facts.review_status` và `answer.status`:

| Giá trị | Ý nghĩa |
| --- | --- |
| `unknown` | Thiếu dòng hoặc có ô điều kiện trống; chưa đủ căn cứ kết luận không có tiên quyết. |
| `present` | Nguồn ghi điều kiện, đọc được, không phát hiện mâu thuẫn/mã chưa giải quyết. |
| `conflict` | Flag mâu thuẫn hoặc các dòng ghi điều kiện khác nhau; giữ mọi dòng, chưa chọn điều kiện đúng. |
| `unresolved` | Có mã ngoài phạm vi hoặc cách phân tích điều kiện chưa giải quyết; giữ nguyên chuỗi nguồn. |

Ưu tiên khi đồng thời có nhiều dấu hiệu: conflict → thiếu raw/unknown → unresolved
→ present. Không trạng thái nào kết luận người dùng đủ điều kiện đăng ký. Review
`verified` vẫn chỉ là sign-off cấp dự án, không biến ô trống thành “không có”.

Q048/MAT2400 giữ `facts.value=[null]`, nhóm tiên quyết và citation như nguồn;
thêm trạng thái/cảnh báo rõ. Scorer, gold và điểm lịch sử `[]`/`[null]` giữ nguyên.

MVP hỗ trợ một môn, một loại thông tin mỗi lượt. Câu phát hiện nhiều field yêu
cầu chọn lại một trường (`needs_clarification`, không facts/citation), kể cả khi
API gửi field hint. Alias dùng chung với router; phủ định yêu cầu chỉ loại object
đã xác định, không nuốt yêu cầu khẳng định phía sau. Cụm “học những…” không dấu
không bị tách thành mệnh đề “nhưng”; yêu cầu học trước thật vẫn ưu tiên F2.
Đây là xử lý lexical có giới hạn, không bảo đảm hiểu mọi diễn đạt tiếng Việt.

Câu sau không tự lấy môn từ câu trước. Người dùng cần ghi mã hoặc tên đầy đủ
khớp duy nhất trong ngành/phiên bản đang chọn. Help và UI ghi rõ giới hạn này;
dòng trạng thái phân biệt hội thoại, trả lời, thiếu thông tin, cần làm rõ và
tiên quyết chưa rõ. Review, lọc ngành/phiên bản, bằng chứng và AI opt-in giữ nguyên.

Dev v4 đóng băng 16 ca trước sửa, gồm nguồn ở bốn ngành, Q048 đã lộ và probe
nhiều field/follow-up. Test bổ sung cũng là dev. Có 25 câu H2 đã dùng tuning
qua dev v2/v3/v4; không dùng làm holdout độc lập. Reviewer là AI, human review 0.
Technical peer review đã sửa các lỗi alias, phủ định và “học những…”; lượt review
lại không còn Critical/Important trong delta A1.

Xem [receipt ghim code/data và regression](acceptance/hus_chat_contracts_a1_report.json),
[dev v4](../data/hus/evaluation/diagnostic_dev_v4_contracts/README.md),
[kế hoạch tiếp theo](RAG_PROGRESS_AND_NEXT_PLAN.md). Receipt ghi riêng phép đo cũ
và kiểm hợp đồng mới; không sửa baseline, không chạy lại toàn bộ H2, không chứng
minh mục tiêu Recall@5 độc lập ≥90% từ dev. PostgreSQL/full-catalog và nghiệm thu
PDF viewer thực không thuộc lượt regression này. Chưa commit/push/deploy,
embedding/Chroma, tích hợp LLM hoặc bật official F3.
