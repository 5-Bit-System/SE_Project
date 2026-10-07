# Module 04 — Xếp hạng và LLM

**Nhánh:** `feat/ranking`

**Use case:** UC03, UC05, UC06

**Trạng thái:** `app/ranking.py` có `KeywordRanker`; `app/service.py` lọc mã lạ/trùng, kiểm tra tổng TC và dùng thứ tự dự phòng khi ranker lỗi. Chưa gọi LLM thật.

## Mục tiêu

Cho LLM **chỉ xếp thứ tự** các môn đã qua Module 03 kiểm tra, dựa trên mục tiêu người học. API key là tùy chọn; app vẫn chạy và demo được bằng baseline nếu thiếu key hoặc nhà cung cấp lỗi.

## File phụ trách

- `app/ranking.py`, adapter mới trong `app/` (nếu cần), test riêng như `tests/test_ranking.py`.
- Module 02 phụ trách `app/models.py`/`app/service.py` và bộ kiểm tra đầu ra cuối. Module 04 phụ trách adapter, kiểm tra định dạng trả về từ provider và test ranker.

## Việc cần làm

1. Giữ một interface `rank(candidates, goal) -> list[course_code]`. `app/service.py` đã chốt `program_id` và chỉ truyền ứng viên hợp lệ của đúng ngành cho ranker; nếu provider cần nhận thêm `program_id`, chốt thay đổi interface với trưởng nhóm trước. Không gửi cả bốn catalog hoặc dữ liệu sinh viên thật.
2. Yêu cầu đầu ra có cấu trúc và kiểm tra định dạng ở adapter. Cung cấp test/mock cho Module 02 kiểm tra mã, trùng lặp, số lượng, ngành và tập ứng viên ở service.
3. Đặt timeout, xử lý lỗi mạng/JSON và fallback về baseline. Không để request chờ vô hạn hoặc trả lỗi 500 chỉ vì LLM không hoạt động.
4. Tạo lý do ngắn bám thông tin mục tiêu/môn được chọn; phân biệt phần giải thích dựa trên luật (chắc chắn) và nhận xét xếp hạng (gợi ý). Không đưa ra khẳng định về lịch mở môn hay khả năng đậu.
5. So sánh baseline và LLM trên hồ sơ tổng hợp nhỏ, lưu cách đánh giá/giới hạn của phép thử trong PR. Không cần huấn luyện hay fine-tune model.

## Đầu ra và nghiệm thu

- Test khi LLM trả mã lạ, mã ngành khác, trùng mã, danh sách rỗng, JSON sai, timeout và thiếu API key; kết quả cuối vẫn chỉ chứa ứng viên hợp lệ.
- Không có khóa trong Git, log hoặc test fixture; hướng dẫn cấu hình bằng biến môi trường và `.env.example` nếu cần.
- `python -m pytest -q` đạt; PR nêu provider/model được dùng, cách chạy **không cần key** và giới hạn chi phí sử dụng.

## Ranh giới

Người nhận module review phần dữ liệu theo [bản phân công](../docs/PHAN_CHIA_CONG_VIEC.md). Chốt interface ranker/lý do với Module 02; dùng mock để test LLM lỗi và phát triển độc lập trên catalog đã số hóa.

Module này không sửa catalog, không quyết định điều kiện học vụ và không tự merge PR. LLM là bước ưu tiên mềm sau bộ lọc luật; nếu chưa có key, baseline vẫn là hành vi mặc định.
