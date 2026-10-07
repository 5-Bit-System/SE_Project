# Module 02 — Hồ sơ, API và luồng gợi ý

**Nhánh:** `feat/profile-api`

**Use case:** UC01, UC02, UC03, UC05, UC06

## Vai trò

Tiếp nhận thông tin người học, gọi các module theo thứ tự và tạo kết quả thống nhất cho giao diện: chọn catalog → kiểm tra hồ sơ → lọc luật → xếp hạng → kiểm tra đầu ra → trả kết quả.

## File phụ trách

- `app/models.py`, `app/main.py`, `app/service.py`.
- Test API/hồ sơ/tích hợp trong `tests/test_api.py`, `tests/test_service.py` (cần tạo); điều phối thay đổi test tích hợp hiện có.
- Thay đổi schema phải thông báo bằng một PR nhỏ để các module cập nhật trước khi ghép tính năng lớn.

## Việc lập trình

1. Kiểm tra hồ sơ: bắt buộc một `program_id`, mã môn đã qua thuộc ngành đã chọn, mục tiêu và giới hạn tín chỉ hợp lệ; xử lý mã lặp nhất quán.
2. Bổ sung đầu vào hướng chuyên sâu/nhánh tốt nghiệp khi Module 03 cần, đồng thời phối hợp Module 01 cập nhật cấu trúc chương trình.
3. Tích hợp kết quả luật và ranker. Chặn mã lạ, mã trùng, môn đã qua và môn ngoài tập ứng viên; kiểm tra kế hoạch cuối theo luật cả nhóm môn và tổng TC, không chỉ từng môn.
4. Trả lý do gợi ý, lý do loại và cảnh báo từ các module bằng một response thống nhất. LLM lỗi hoặc chưa cấu hình vẫn trả được kết quả baseline.
5. Hoàn thiện thông báo HTTP 404/422 và test luồng xuyên module bằng dữ liệu tổng hợp. Test API chạy độc lập với khóa LLM thật.

## Việc dữ liệu của người nhận module

Review phần được giao trong bảng phân công và kiểm tra ghi chú của người kế tiếp. Khi sửa bản chép nguồn/metadata, phối hợp Module 01 và sinh lại catalog bằng công cụ đã có.

## Đầu ra và nghiệm thu

- API vẫn dùng được với bốn ngành, hồ sơ sai trả lỗi rõ; đổi ngành không được dùng mã hồ sơ ngành cũ.
- Test với ranker lỗi/mã lạ, thiếu tiên quyết, giới hạn tín chỉ và catalog nháp; đầu ra luôn giữ đúng ngành và luật đã chốt.
- Tài liệu API có ví dụ request/response; Module 05 có thể kết nối theo hợp đồng mà không phải đọc logic backend.

## Phối hợp

Module 01 cung cấp catalog, Module 03 quyết định luật, Module 04 xếp hạng, Module 05 dùng API. Người phụ trách module này làm phần ghép bằng code; trưởng nhóm review/merge Git vẫn là trách nhiệm riêng của một trong năm thành viên.
