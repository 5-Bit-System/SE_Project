# Module 01 — Catalog và kiểm tra dữ liệu

**Nhánh:** `feat/catalog`

**Use case:** UC01, UC08

## Vai trò

Hoàn thiện cách đọc và kiểm tra dữ liệu cho cả bốn chương trình. Catalog Toán học, Toán tin, KHMTTT và KHDL được lưu riêng bằng `program_id`. Bảng đã được số hóa đầy đủ; cả năm người review dữ liệu theo [bản phân công](../docs/PHAN_CHIA_CONG_VIEC.md).

## File phụ trách

- `app/catalog.py`, test loader/validator; bộ test dữ liệu hiện có trong `tests/test_curriculum_data.py`.
- `tools/build_catalogs.py` đã có; các `source_rows.json`, `curriculum.json` và `courses.json` trong `data/curricula/`.
- `app/models.py` do Module 02 phụ trách; hai người thống nhất schema trước khi thêm trường dữ liệu.

## Việc lập trình

1. Hoàn thiện loader: chọn đúng ngành, báo rõ JSON lỗi, mã môn trùng, nhóm không tồn tại, mã tiên quyết cần xác minh và trang nguồn thiếu.
2. Hoàn thiện công cụ sinh catalog từ `source_rows.json` và `curriculum.json`; hiện đã kiểm tra độ phủ STT, số bản ghi, nhóm, cơ cấu TC và nhánh tốt nghiệp. Bổ sung kiểm tra theo lỗi phát hiện khi review.
3. Nếu một mã môn xuất hiện nhiều dòng trong cùng ngành, hợp nhất quan hệ nhóm và giữ dấu vết dòng nguồn. Nếu tên, tín chỉ hoặc tiên quyết khác nhau thì báo cần review; không tự chọn một bản ghi để ghi đè bản khác.
4. Đối chiếu các nhóm và tổng chỉ tiêu với bảng cơ cấu tín chỉ. Phối hợp Module 03 biểu diễn hướng chuyên sâu/nhánh tốt nghiệp; tổng tín chỉ hoàn thành không cộng lặp môn thuộc nhiều nhóm.
5. Thêm test loader và công cụ ghép; hướng dẫn cả nhóm cách chạy. Catalog chỉ chuyển sang `verified` sau khi đủ bảng và review nguồn.

## Việc dữ liệu của người nhận module

Review phần được giao và kiểm tra ghi chú của người kế tiếp. Việc hoàn thiện công cụ và kiểm tra dữ liệu cũng được tính vào khối lượng module; nếu việc tích hợp tăng nhiều, phân lại một phần review cho người đã xong mốc code.

## Đầu ra và nghiệm thu

- Có lệnh sinh/kiểm tra catalog và báo lỗi dễ tìm về đúng file/STT.
- Mỗi ngành có catalog độc lập; mã trùng giữa hai ngành không bị gộp.
- Test chứng minh phát hiện thiếu dòng, mã trùng chưa xử lý, xung đột dữ liệu và tham chiếu nhóm sai.
- Các lỗi nguồn, gồm KHDL 28/63 so với 28/57 TC và số quyết định KHMTTT, có ghi chú để xử lý.

## Phối hợp

Module 02 chốt schema/API, Module 03 chốt cách xử lý luật đã biểu diễn trong metadata. Catalog đã có 90/68/67/65 mã môn theo ngành; công cụ sinh dữ liệu hiện có, phần tiếp theo là review nguồn và hoàn thiện loader/validator.
