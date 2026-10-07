# Module 04 — Xếp hạng và LLM

**Use case:** UC03, UC05, UC06

**Trạng thái:** `app/ranking.py` có `KeywordRanker`; `app/service.py` lọc mã lạ/trùng, kiểm tra tổng TC và dùng thứ tự dự phòng khi ranker lỗi. Chưa gọi LLM thật.

## Mục tiêu

Cho LLM **chỉ xếp thứ tự** các môn đã qua Module 03 kiểm tra, dựa trên mục tiêu người học. API key là tùy chọn; app vẫn chạy và demo được bằng baseline nếu thiếu key hoặc nhà cung cấp lỗi.

## Đầu vào và đầu ra

- Đầu vào: danh sách môn hợp lệ của đúng ngành và mục tiêu học tập.
- Đầu ra hiện tại: danh sách mã môn theo thứ tự ưu tiên, qua `rank(candidates, goal) -> list[str]`.
- Adapter LLM cần bổ sung; nếu bổ sung lý do từ LLM thì phải mở rộng hợp đồng kết quả với Module 02, không coi interface hiện tại đã trả lý do.
- Baseline `KeywordRanker` hoạt động không cần API key.

## Thành phần triển khai

- `app/ranking.py`, adapter mới trong `app/` (nếu cần), test riêng như `tests/test_ranking.py`.
- Bộ kiểm tra đầu ra cuối nằm trong Module 02 (`app/service.py`); adapter và kiểm tra định dạng trả về từ provider thuộc module xếp hạng.

## Chức năng cần đáp ứng

1. Giữ một interface `rank(candidates, goal) -> list[course_code]`. `app/service.py` đã chốt `program_id` và chỉ truyền ứng viên hợp lệ của đúng ngành cho ranker; nếu provider cần nhận thêm `program_id`, cập nhật hợp đồng với Module 02. Không gửi cả bốn catalog hoặc dữ liệu sinh viên thật.
2. Yêu cầu đầu ra có cấu trúc và kiểm tra định dạng ở adapter. Cung cấp test/mock cho Module 02 kiểm tra mã, trùng lặp, số lượng, ngành và tập ứng viên ở service.
3. Đặt timeout, xử lý lỗi mạng/JSON và fallback về baseline. Không để request chờ vô hạn hoặc trả lỗi 500 chỉ vì LLM không hoạt động.
4. Tạo lý do ngắn bám thông tin mục tiêu/môn được chọn; phân biệt phần giải thích dựa trên luật (chắc chắn) và nhận xét xếp hạng (gợi ý). Không đưa ra khẳng định về lịch mở môn hay khả năng đậu.
5. So sánh baseline và LLM trên hồ sơ tổng hợp nhỏ, ghi lại cách đánh giá/giới hạn của phép thử. Không cần huấn luyện hay fine-tune model.

## Đầu ra và nghiệm thu

- Test khi LLM trả mã lạ, mã ngành khác, trùng mã, danh sách rỗng, JSON sai, timeout và thiếu API key; kết quả cuối vẫn chỉ chứa ứng viên hợp lệ.
- Không có khóa trong Git, log hoặc test fixture; hướng dẫn cấu hình bằng biến môi trường và `.env.example` nếu cần.
- `python -m pytest -q` đạt; tài liệu nêu provider/model được dùng, cách chạy **không cần key** và giới hạn chi phí sử dụng.

## Ranh giới

Module 02 truyền ứng viên từ Module 03 và kiểm tra kết quả cuối. Module xếp hạng không đọc toàn bộ catalog trực tiếp; dùng mock để test lỗi provider.

Module này không sửa catalog và không quyết định điều kiện học vụ. LLM là bước ưu tiên mềm sau bộ lọc luật; nếu chưa có key, baseline vẫn là hành vi mặc định.
