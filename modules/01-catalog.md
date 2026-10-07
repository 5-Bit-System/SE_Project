# Module 01 — Catalog và kiểm tra dữ liệu

**Use case:** UC01, UC08

## Vai trò

Đọc và kiểm tra dữ liệu cho cả bốn chương trình. Catalog Toán học, Toán tin, KHMTTT và KHDL được lưu riêng bằng `program_id`. Module là thành phần hệ thống, không đại diện cho một thành viên.

## Đầu vào và đầu ra

- Đầu vào runtime: `program_id`, `curriculum.json` và `courses.json` của ngành được chọn.
- Đầu ra: `Catalog` gồm thông tin chương trình và danh sách môn; báo lỗi nếu ngành hoặc dữ liệu không hợp lệ.
- Interface hiện có: `load_catalog(program_id) -> Catalog`, `list_catalogs() -> list[Catalog]`.
- Công cụ dữ liệu đọc `source_rows.json` và `curriculum.json` để sinh/kiểm tra `courses.json`; không chạy lại công cụ này trong mỗi lần gợi ý.

## Thành phần triển khai

- `app/catalog.py`, test loader/validator; bộ test dữ liệu hiện có trong `tests/test_curriculum_data.py`.
- `tools/build_catalogs.py` đã có; các `source_rows.json`, `curriculum.json` và `courses.json` trong `data/curricula/`.
- Kiểu dữ liệu dùng chung nằm trong `app/models.py`; API và bộ luật sử dụng cùng cấu trúc catalog.

## Chức năng cần đáp ứng

1. Hoàn thiện loader: chọn đúng ngành, báo rõ JSON lỗi, mã môn trùng, nhóm không tồn tại, mã tiên quyết cần xác minh và trang nguồn thiếu.
2. Hoàn thiện công cụ sinh catalog từ `source_rows.json` và `curriculum.json`; hiện đã kiểm tra độ phủ STT, số bản ghi, nhóm, cơ cấu TC và nhánh tốt nghiệp. Bổ sung kiểm tra theo lỗi phát hiện khi review.
3. Nếu một mã môn xuất hiện nhiều dòng trong cùng ngành, hợp nhất quan hệ nhóm và giữ dấu vết dòng nguồn. Nếu tên, tín chỉ hoặc tiên quyết khác nhau thì báo cần review; không tự chọn một bản ghi để ghi đè bản khác.
4. Đối chiếu các nhóm và tổng chỉ tiêu với bảng cơ cấu tín chỉ. Phối hợp Module 03 biểu diễn hướng chuyên sâu/nhánh tốt nghiệp; tổng tín chỉ hoàn thành không cộng lặp môn thuộc nhiều nhóm.
5. Có test loader/công cụ sinh dữ liệu và hướng dẫn chạy. Catalog chỉ chuyển sang `verified` sau khi đủ bảng và review nguồn.

## Đầu ra và nghiệm thu

- Có lệnh sinh/kiểm tra catalog và báo lỗi dễ tìm về đúng file/STT.
- Mỗi ngành có catalog độc lập; mã trùng giữa hai ngành không bị gộp.
- Test chứng minh phát hiện thiếu dòng, mã trùng chưa xử lý, xung đột dữ liệu và tham chiếu nhóm sai.
- Các lỗi nguồn, gồm KHDL 28/63 so với 28/57 TC và số quyết định KHMTTT, có ghi chú để xử lý.

## Quan hệ với các module khác

Module 02 sử dụng catalog để kiểm tra hồ sơ và điều phối luồng; Module 03 sử dụng dữ liệu môn/quy định để kiểm tra điều kiện. Catalog không gọi LLM hoặc quyết định thứ tự đề xuất. Hiện có 90/68/67/65 mã môn theo ngành; dữ liệu đang chờ review nguồn.
