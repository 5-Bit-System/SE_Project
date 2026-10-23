# Module 06 — Tư vấn môn học và phân luồng hội thoại

Cập nhật: 23/10/2026. **Hiện trạng:** có course advisor/guardrail/LLM/fallback; chưa nối HUS RAG.

## Trách nhiệm và hợp đồng

app/services/advisor_service.py và app/schemas/advisor.py nhận message/history có giới hạn cùng context học tập. Đầu ra hiện có là reply, mode, guardrail status và suggested codes. Contract mục tiêu bổ sung intent, citations khi dùng RAG, warnings và context/release tham chiếu.

## Phân luồng mục tiêu

- Tư vấn/chọn môn: dùng facts từ 03/04/05 cùng context; history cũ không ghi đè facts hiện tại.
- Tra cứu thông tin HUS: gọi 11, chỉ dùng release active.
- Câu hỏi hỗn hợp: tách phần tính toán và phần trích dẫn; tài liệu không mở khóa môn.
- Thiếu ngành/khóa/năm làm đổi đáp án: hỏi làm rõ.
- Yêu cầu xếp lịch, kiểm tra trùng lớp, đánh giá giảng viên hoặc chắc chắn mở lớp: nêu giới hạn chức năng.

## Kế hoạch chỉnh sửa

Advisor hiện dùng max_credits=40, recommendation tối đa 30; cần thống nhất constraints hoặc phân biệt rõ tư vấn từng môn với chọn gói môn. Dùng chung facts/scoring và context, không nhân bản policy nghiệp vụ.

Giữ kiểm tra mã/guardrail/fallback; đánh giá riêng các khẳng định prose vì code validation không đủ chứng minh mọi lời văn đúng. Thêm router tới RAG sau khi module 11 sẵn sàng.

## Phiên và nghiệm thu

History chỉ trong phiên, xóa/vô hiệu hóa khi đổi ngành hoặc áp transcript/context mới. Không đưa credentials, HTML portal hoặc thông tin định danh không cần thiết vào LLM.

Kiểm thử recommendation blocked, history đổi ngành, fallback, thiếu nguồn, phân luồng và constraints nhất quán. Không dùng course advisor hiện có làm bằng chứng đã hoàn thành tra cứu văn bản HUS.
