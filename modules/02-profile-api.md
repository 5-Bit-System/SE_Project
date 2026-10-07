# Module 02 — Hồ sơ sinh viên (Profile)

**Use case:** UC01, UC02, UC03

## Vai trò

Biểu diễn và kiểm tra thông tin người học: ngành, môn đã qua, mục tiêu, giới hạn tín chỉ và các lựa chọn hướng học khi được bổ sung. Module này không điều phối toàn bộ quá trình gợi ý; phần đó thuộc module Đề xuất môn học.

## Đầu vào và đầu ra

- Đầu vào: phần hồ sơ của `RecommendationRequest`, gồm `program_id`, `passed_course_codes`, `goal`, `max_credits`, cùng catalog để xác minh mã môn.
- Đầu ra mục tiêu: hồ sơ hợp lệ, đã chuẩn hóa; hoặc lỗi trường dữ liệu/mã môn không hợp lệ.
- Hiện kiểm tra kiểu/giới hạn nằm trong `app/models.py`, kiểm tra mã môn nằm trong `app/service.py`; chưa có service hồ sơ tách riêng.
- Chưa có API lưu hồ sơ, đăng nhập hoặc quản lý tài khoản. Hồ sơ chỉ sử dụng trong lần yêu cầu gợi ý.

## Thành phần triển khai

- Mục tiêu: `app/modules/profile/service.py` và `schemas.py`; chưa refactor code.
- Hiện tại: phần hồ sơ trong `app/models.py`, phần xác minh mã môn ở `app/service.py`.
- Kiểm thử hồ sơ/API hiện có trong `tests/test_recommendations.py`; bộ test hồ sơ riêng cần bổ sung.

## Chức năng cần đáp ứng

1. Kiểm tra hồ sơ: bắt buộc một `program_id`, mã môn đã qua thuộc ngành đã chọn, mục tiêu và giới hạn tín chỉ hợp lệ; xử lý mã lặp nhất quán.
2. Bổ sung đầu vào hướng chuyên sâu/nhánh tốt nghiệp khi Module 03 cần, đồng thời phối hợp Module 01 cập nhật cấu trúc chương trình.
3. Chuẩn hóa danh sách môn đã qua, không tính lặp một mã môn.
4. Trả lỗi có cấu trúc để router của module Đề xuất môn học chuyển thành HTTP 404/422 và giao diện hiển thị được.
5. Kiểm thử hồ sơ độc lập với LLM và giao diện, bao gồm sai ngành, mã môn lạ, TC ngoài giới hạn và mục tiêu quá dài.

## Đầu ra và nghiệm thu

- Kiểm tra được hồ sơ của cả bốn ngành; đổi ngành không được dùng mã môn đã qua thuộc ngành cũ.
- Hồ sơ sai không được đưa tiếp sang bộ luật/xếp hạng; lỗi chỉ rõ trường cần sửa.
- Có test cho mã môn lặp, mã lạ, giới hạn tín chỉ và độ dài mục tiêu. Không cần khóa LLM để chạy test.

## Quan hệ với các module khác

Catalog cung cấp danh sách mã môn để xác minh. Module Đề xuất môn học gọi kiểm tra hồ sơ trước khi gọi module Điều kiện học. Giao diện cung cấp đầu vào và hiển thị lỗi. Profile không xếp hạng, không sửa catalog và không quyết định tiên quyết.
