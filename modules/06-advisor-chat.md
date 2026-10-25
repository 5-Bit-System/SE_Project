# Module 06 — Chatbot tư vấn học tập

## Mục tiêu

Cung cấp chatbot nổi để tư vấn trong context ngành, transcript, eligible set và preference của phiên hiện tại.

## Phạm vi cốt lõi

- Nhận message và session context.
- Nhánh recommendation advice: gọi pipeline recommendation qua Module 07.
- Scope guardrail cho câu hỏi ngoài phạm vi.
- Heuristic fallback khi LLM không khả dụng.
- Giữ chat history trong session và xóa khi đổi ngành.
- Không lưu message hoặc profile cá nhân lâu dài.

## Các câu hỏi được phép

- Nên học môn nào trong tập eligible.
- Định hướng chủ đề, track và career goal.
- Giải thích vì sao môn được phép hoặc bị chặn.
- Hỏi lại để làm rõ preference mơ hồ.

## Các câu hỏi phải từ chối

- Xếp thời khóa biểu.
- Kiểm tra trùng lịch.
- Xác nhận môn chắc chắn mở lớp.
- Đánh giá giảng viên hoặc khả năng chấm điểm.
- Quyết định học vụ chính thức.
- Câu hỏi HUS ngoài phạm vi dữ liệu được cung cấp.

## Thông tin HUS

HUS crawler, allowlist, chunking, retrieval index và citation model là phase sau. Ở core phase chỉ giữ interface để sau này thêm nhánh HUS, không trộn tài liệu HUS vào catalog course.

## Dữ liệu vào và dữ liệu ra

Dữ liệu vào gồm tin nhắn, program_id, bảng điểm, context môn hợp lệ/bị chặn và lịch sử trong phiên.

Dữ liệu ra gồm câu trả lời, loại ý định, kết quả gợi ý hoặc thông báo từ chối, nguồn trích dẫn nếu có, cảnh báo và metadata của phiên.

## Tiêu chí hoàn thành

- Chat recommendation không thể đề xuất blocked course.
- Đổi ngành xóa history/context.
- Có fallback không cần API key.
- Có test guardrail cho câu hỏi lịch học, giảng viên và offering.
