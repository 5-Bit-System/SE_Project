# Module 03 — Kiểm tra điều kiện và tiến độ

**Nhánh:** `feat/rules`

**Use case:** UC02, UC04, UC06

**Trạng thái:** `app/rules.py` hiện lọc môn đã qua, tiên quyết AND/OR, giới hạn TC từng môn và quota nhóm đơn giản. Chưa xử lý đủ hướng chuyên sâu, nhánh tốt nghiệp và giải thích môn bị loại.

## Mục tiêu

Tạo một lớp luật **xác định được và có thể test** để chỉ đưa môn hợp lệ vào bộ xếp hạng. Quy tắc phải lấy từ `curriculum.json` của ngành đã chọn, không gán cứng chỉ tiêu của một ngành vào toàn hệ thống.

## File phụ trách

- `app/rules.py` và test mới, ví dụ `tests/test_rules.py`.
- Nếu cần thêm `tracks`/`graduation_paths`, chốt cấu trúc với Module 01 và Module 02; Module 02 phụ trách `app/models.py`/`app/service.py`, Module 01 phụ trách loader/catalog.

## Việc cần làm

1. Giữ nguyên kiểm tra tiên quyết: `[[A, B], [C]]` nghĩa là `(A hoặc B) và C`; không gợi ý môn đã qua hoặc môn thiếu điều kiện.
2. Hoàn thiện quota tự chọn: môn ở nhiều nhóm không được tính hai lần trong tổng tiến độ; không cho một lựa chọn vượt quy tắc nếu nhóm đã đủ TC. Phân biệt **ứng viên đủ tiên quyết** với **kế hoạch học kỳ đã chọn**.
3. Biểu diễn và kiểm tra định hướng chuyên sâu chọn một trong nhiều nhánh, các phương án tốt nghiệp 7 TC và chỉ tiêu theo từng ngành. Nếu thông tin nguồn thiếu/chưa chắc, trả cảnh báo thay vì khẳng định môn hợp lệ.
4. Trả lý do cấu trúc cho môn bị loại (`already_passed`, `missing_prerequisite`, `group_full`, `credit_limit`, ...), để Module 05 hiển thị; lý do hiện trên UI phải bắt nguồn từ luật, không do LLM tự nghĩ ra.
5. Giữ hàm lọc độc lập với HTTP và API LLM để có thể kiểm thử bằng catalog giả trong `tests/` khi dữ liệu bốn ngành còn nhập dở.

## Đầu ra và nghiệm thu

- Test đủ tình huống: AND, OR, thiếu tiên quyết, môn đã qua, giới hạn TC, nhóm đã đủ, môn ở hai nhóm, chọn sai hướng, hai nhánh tốt nghiệp thay thế nhau, đổi `program_id`.
- Không có môn không hợp lệ trong danh sách đưa cho ranker; tín chỉ không bị cộng lặp.
- `python -m pytest -q` đạt với các test cũ và mới. PR giải thích thay đổi schema/API nếu có, kèm ví dụ trước–sau.

## Ranh giới

Người nhận module còn nhập và review lô dữ liệu theo [bản phân công](../docs/PHAN_CHIA_CONG_VIEC.md). Có thể làm code trước trên fixture tổng hợp. Khi trả kết quả luật hoặc đổi interface, phối hợp Module 02 để ghép vào API; giữ phần kiểm tra luật trong `app/rules.py`.

Không dùng LLM để quyết định tiên quyết hoặc tính tín chỉ. Không suy ra lịch mở môn, điểm số hay quy định công nhận tương đương vì nguồn MVP chưa có các dữ liệu đó.
