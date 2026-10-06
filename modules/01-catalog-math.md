# Module 01 — Catalog Toán học và Toán tin

**Nhánh:** `feat/catalog-math`

**Use case:** UC01, UC02, UC08

**Trạng thái:** hai `curriculum.json` mới là khung nháp; hai `courses.json` đang rỗng.

## Mục tiêu

Nhập **toàn bộ bảng Khung chương trình đào tạo** của ngành Toán học và Toán tin từ hai PDF tương ứng, để hệ thống có danh sách môn và ràng buộc riêng của từng ngành. Không lấy mục tiêu đào tạo hay các phần thuyết minh ngoài bảng khung chương trình. Không gộp hai ngành dù có mã môn trùng nhau.

## File phụ trách

- `data/curricula/toan_hoc_7460101_2022/{curriculum,courses}.json`
- `data/curricula/toan_tin_7460117_2022/{curriculum,courses}.json`
- Test riêng, ví dụ `tests/test_catalog_math.py`. Nếu cần đổi schema trong `app/models.py` hoặc loader trong `app/catalog.py`, mở issue/PR nhỏ để cả nhóm thống nhất trước.

## Việc cần làm

1. Lấy bảng học phần ở trang PDF 8–14 (Toán học) và 8–12 (Toán tin). Nhập từng môn: `code`, `name`, `credits`, `block`, `prerequisites`, `choice_group_ids`, `source_page`.
2. Đối chiếu cơ cấu tín chỉ, các nhóm tự chọn, **chọn đúng một** định hướng chuyên sâu và nhánh tốt nghiệp với `KHUNG_CHUONG_TRINH_4_NGANH.md`; ghi những quy tắc chưa biểu diễn được vào issue thay vì nhét vào trường sai nghĩa.
3. Với tiên quyết, mỗi phần tử ngoài của `prerequisites` là điều kiện **và**; các mã trong cùng phần tử là **hoặc**. Trường hợp PDF khó đọc hoặc mã tham chiếu ngoài bảng phải ghi chú để xác minh.
4. Kiểm tra môn xuất hiện ở nhiều nhóm: lưu một bản ghi theo mã/ngành, gắn nhiều `choice_group_ids`; không nhân đôi tín chỉ.
5. Review chéo với người làm Module 02 một mẫu tối thiểu 10 dòng/ngành và toàn bộ dòng có tiên quyết phức tạp. Chỉ đổi `catalog_status` sang `verified` sau khi kiểm tra hết bảng, không chỉ sau khi JSON hợp lệ.

## Đầu ra và nghiệm thu

- `GET /courses?program_id=toan_hoc_7460101_2022` và `...toan_tin_7460117_2022` trả môn của **đúng một** ngành; không trả môn của ngành khác.
- Không có mã trùng trong cùng ngành; mỗi môn có trang PDF nguồn; tổng số dòng nhập/ngoại lệ được ghi trong PR. Số dòng bảng tham khảo là 89 và 63, **không** dùng làm số môn duy nhất vì có lựa chọn và dòng lặp.
- Test tự động kiểm tra JSON tải được, mã duy nhất, tham chiếu nhóm có thật và ít nhất một chuỗi tiên quyết; `python -m pytest -q` đạt.
- PR đính kèm bảng lỗi nguồn/chỗ chưa chắc chắn và tên người đã review chéo. Không đưa dữ liệu sinh viên thật hoặc bản PDF lên Git.

## Ranh giới

Module này tạo dữ liệu, **không** tự sửa thuật toán lọc, LLM hay UI. Các quy tắc hướng chuyên sâu/nhánh tốt nghiệp chưa được schema hiện tại hỗ trợ đầy đủ; phối hợp Module 03 để bổ sung sau khi chốt cách biểu diễn.
