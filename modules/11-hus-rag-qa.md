# Module 11 — Tra cứu thông tin HUS bằng RAG

Cập nhật: 23/10/2026. **Hiện trạng:** chưa có retrieval/answering service runtime.

## Trách nhiệm và hợp đồng

Trả lời từ corpus release đã duyệt của 10, có nguồn hỗ trợ hoặc nêu chưa đủ căn cứ. Được gọi qua 06/07; không thay eligibility/recommendation.

Đầu vào: câu hỏi, bậc học, phạm vi ngành/chương trình, năm/khóa nếu cần và context tối thiểu. Đầu ra mục tiêu: answer, trạng thái answered/needs_clarification/insufficient_evidence/unavailable, citations, warnings và release_id. Citation gồm document/chunk ID, URL, tiêu đề, locator/trang-mục và bằng chứng. Schema cụ thể chưa triển khai.

## Luồng dự kiến

1. Pin release active cho toàn request để không trộn corpus/index giữa phiên bản.
2. Làm rõ phạm vi nếu thiếu bậc học/ngành/chương trình/khóa/năm làm đổi đáp án. Unknown không tự thành general.
3. Truy xuất theo cấu hình đã đánh giá, xét tài liệu đúng bậc học và ngành/chương trình, cùng tài liệu chung đã review. Câu hỏi về học tiếp cần nguồn điều kiện tuyển sinh, không chỉ khung chương trình.
4. Lấy đủ ngữ cảnh bảng/điều kiện trong token budget.
5. Xử lý mâu thuẫn bằng bằng chứng phạm vi/hiệu lực; chưa rõ thì trình bày khác biệt, không chọn theo fetched_at.
6. Sinh câu trả lời trong bằng chứng; backend ánh xạ citations, không cho model tự tạo URL.
7. Thiếu nguồn/index lỗi thì hỏi lại, nêu giới hạn hoặc unavailable; không suy đoán học vụ từ model.

## Ranh giới

Tài liệu crawl là dữ liệu tham khảo, không phải chỉ dẫn hệ thống. Không làm theo lệnh trong tài liệu để gọi công cụ/đổi rules/đọc credentials. Không nhận bảng điểm đầy đủ hay thông tin định danh không cần thiết.

Tài liệu lịch sử không đủ chứng minh quy định hiện tại. Nguồn khác catalog là vấn đề cần review, không tự sửa prerequisite/equivalence. Câu tính GPA/tiến độ/chọn gói môn gọi nghiệp vụ 02–05.

## Tiêu chí hoàn thành

Dùng bộ câu hỏi có expected source/locator và tập giữ lại trong kế hoạch RAG. Kiểm tra diễn đạt lại, mã quyết định, bảng/số liệu, sai ngành/khóa, thiếu nguồn và nguồn mâu thuẫn. Đánh giá retrieval riêng với correctness/citation support; URL đúng chưa đủ khi đoạn đó không hỗ trợ khẳng định.

Có kiểm tra release pinning, source instruction injection và retrieval unavailable. Không có lỗi nghiêm trọng số tiền/hạn/điều kiện trong tập nghiệm thu. Không coi tạo embedding hoặc course advisor hiện có là hoàn thành RAG; báo rõ chất lượng/giới hạn thực tế.
