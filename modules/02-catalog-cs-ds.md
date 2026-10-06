# Module 02 — Catalog KHMTTT và Khoa học dữ liệu

**Nhánh:** `feat/catalog-cs-ds`

**Use case:** UC01, UC02, UC08

**Trạng thái:** hai `curriculum.json` mới là khung nháp; hai `courses.json` đang rỗng.

## Mục tiêu

Nhập **toàn bộ bảng Khung chương trình đào tạo** của ngành Khoa học máy tính và thông tin (KHMTTT) và Khoa học dữ liệu từ PDF riêng của mỗi ngành. Catalog phải giữ đúng `program_id`; môn có cùng mã ở hai ngành không tự động được coi có cùng nhóm hay điều kiện.

## File phụ trách

- `data/curricula/khmtt_7480113qtd_2022/{curriculum,courses}.json`
- `data/curricula/khdl_7460108_2022/{curriculum,courses}.json`
- Test riêng, ví dụ `tests/test_catalog_cs_ds.py`. Việc đổi `app/models.py` hoặc `app/catalog.py` cần thống nhất với trưởng nhóm và Module 01/03.

## Việc cần làm

1. Nhập từng dòng học phần từ PDF 9–13 của mỗi ngành, đủ mã, tên, TC, khối/nhóm, tiên quyết, trang nguồn. Xử lý AND/OR theo đúng ký hiệu trong scan; trường hợp không rõ phải đánh dấu cần kiểm tra, không tự đoán.
2. Kiểm tra các nhóm tự chọn KHMTTT: kỹ năng phần mềm 4 TC và AI/phát triển phần mềm 12 TC. Với Khoa học dữ liệu: bốn nhóm 4, 6, 9, 9 TC. Lưu thành viên nhóm bằng `choice_group_ids`.
3. Tạo issue riêng cho hai điểm cần xác minh: số quyết định trên PDF KHMTTT không nhất quán; PDF Khoa học dữ liệu ghi 28/63 TC tự chọn nhưng các nhóm liệt kê cộng thành 28/57. **Không** thêm môn giả hoặc tự sửa tổng nguồn để làm đẹp dữ liệu.
4. Ghi một môn thuộc nhiều nhóm thành một bản ghi trong ngành; review chéo tối thiểu 10 dòng/ngành với Module 01 và toàn bộ dòng tiên quyết phức tạp.
5. Chỉ gắn `verified` khi toàn bộ bảng đã được nhập, đối chiếu và các sai khác nguồn có quyết định xử lý được ghi lại.

## Đầu ra và nghiệm thu

- Hai endpoint `/courses?program_id=...` chỉ trả môn của ngành được chọn. Số dòng bảng tham khảo là 61 (KHMTTT) và 59 (KHDL), không đồng nghĩa số môn duy nhất.
- Test JSON tải được, mã trong ngành duy nhất, nhóm tồn tại, trang nguồn có giá trị và ví dụ tiên quyết AND/OR được giữ đúng.
- PR nêu số dòng đã xử lý, chỗ scan khó đọc, issue nguồn đang mở và kết quả review chéo; `python -m pytest -q` đạt.
- Không commit PDF bản quyền, thông tin sinh viên hoặc dữ liệu suy đoán không gắn nhãn.

## Ranh giới

Module này phụ trách dữ liệu, không cài thuật toán rule/ranking. Với lỗi nguồn chưa giải quyết, vẫn để `draft_unverified` và giữ cảnh báo trong `notes`.
