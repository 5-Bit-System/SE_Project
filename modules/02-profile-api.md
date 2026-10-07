# Module 02 — Hồ sơ, API và luồng gợi ý

**Use case:** UC01, UC02, UC03, UC05, UC06

## Vai trò

Tiếp nhận thông tin người học, gọi các module theo thứ tự và tạo kết quả thống nhất cho giao diện: chọn catalog → kiểm tra hồ sơ → lọc luật → xếp hạng → kiểm tra đầu ra → trả kết quả.

## Đầu vào và đầu ra

- Đầu vào: `RecommendationRequest` gồm `program_id`, `passed_course_codes`, `goal`, `max_credits`, `limit`.
- Đầu ra: `RecommendationResponse` gồm danh sách môn, lý do, số ứng viên hợp lệ và cảnh báo; hồ sơ sai trả lỗi HTTP phù hợp.
- Interface hiện có: `POST /recommendations` gọi `recommend(catalog, request, ranker=None)`.
- Các API đọc dữ liệu: `GET /programs`, `GET /courses?program_id=...`.

## Thành phần triển khai

- `app/models.py`, `app/main.py`, `app/service.py`.
- Test API/hồ sơ/tích hợp trong `tests/test_api.py`, `tests/test_service.py` (cần tạo); điều phối thay đổi test tích hợp hiện có.
- Schema là hợp đồng dùng chung giữa giao diện, catalog, bộ luật và bộ xếp hạng.

## Chức năng cần đáp ứng

1. Kiểm tra hồ sơ: bắt buộc một `program_id`, mã môn đã qua thuộc ngành đã chọn, mục tiêu và giới hạn tín chỉ hợp lệ; xử lý mã lặp nhất quán.
2. Bổ sung đầu vào hướng chuyên sâu/nhánh tốt nghiệp khi Module 03 cần, đồng thời phối hợp Module 01 cập nhật cấu trúc chương trình.
3. Tích hợp kết quả luật và ranker. Chặn mã lạ, mã trùng, môn đã qua và môn ngoài tập ứng viên; kiểm tra kế hoạch cuối theo luật cả nhóm môn và tổng TC, không chỉ từng môn.
4. Trả lý do gợi ý, lý do loại và cảnh báo từ các module bằng một response thống nhất. LLM lỗi hoặc chưa cấu hình vẫn trả được kết quả baseline.
5. Hoàn thiện thông báo HTTP 404/422 và test luồng xuyên module bằng dữ liệu tổng hợp. Test API chạy độc lập với khóa LLM thật.

## Đầu ra và nghiệm thu

- API vẫn dùng được với bốn ngành, hồ sơ sai trả lỗi rõ; đổi ngành không được dùng mã hồ sơ ngành cũ.
- Test với ranker lỗi/mã lạ, thiếu tiên quyết, giới hạn tín chỉ và catalog nháp; đầu ra luôn giữ đúng ngành và luật đã chốt.
- Tài liệu API có ví dụ request/response; Module 05 có thể kết nối theo hợp đồng mà không phải đọc logic backend.

## Quan hệ với các module khác

Module 01 cung cấp catalog, Module 03 kiểm tra luật, Module 04 xếp hạng, Module 05 gọi API và hiển thị kết quả. Module này điều phối các lời gọi và kiểm tra kết quả cuối; không lưu cứng quy định riêng của từng ngành hoặc tự xếp hạng thay Module 04.
