# Review P1-04 — Toán học STT 1–55 và MAT4070

Ngày thực hiện: **09/10/2026**. Người thực hiện: **Codex**, đối chiếu trực quan các trang scan với JSON. Theo bảng phân công, Người 5 kiểm tra chéo phần này; bước kiểm tra chéo của thành viên nhóm chưa được ghi nhận.

## Nguồn và phạm vi

PDF: `101. Toán học-chuẩn final QD 3565 Scan.pdf`, tìm thấy tại thư mục Downloads trên máy làm việc. SHA-256 đọc từ file thực tế khớp `curriculum.json`:

```text
e6e33a8a489f7ab77f3db0c727cc4c837ba86f8f17a7eae17c9da08d3c066bd0
```

Đã render và xem trực tiếp các trang PDF 8, 9, 10, 11, 12, 14. PDF scan không có lớp text; đối chiếu dùng hình ảnh trang, không dựa vào kết quả OCR. Số trang trong `source_page` tính từ đầu file PDF, khác số in ở chân trang.

| Trang PDF | Trang in | Phần giao Người 1 | Bản ghi đã đối chiếu | Kết quả bản chép |
|---:|---:|---|---:|---|
| 8 | 6 | STT 1–8, đủ bảy phương án B1 | 14 | Khớp các trường đã kiểm tra |
| 9 | 7 | STT 9–23 | 15 | Khớp các trường đã kiểm tra |
| 10 | 8 | STT 24–37 | 14 | Khớp các trường đã kiểm tra |
| 11 | 9 | STT 38–51 | 14 | Khớp các trường đã kiểm tra |
| 12 | 10 | STT 52–55 | 4 | Khớp các trường đã kiểm tra |
| 14 | 12 | Khóa luận MAT4070, không đánh STT | 1 | Khớp các trường đã kiểm tra |

Tổng: **55 STT và một dòng không STT**, tương ứng **62 bản ghi** vì STT 8 có bảy lựa chọn. Phạm vi này không xác nhận các STT 56–89 hay các ngành khác đã được review PDF.

Các trường đã đối chiếu: STT, trang, nhãn mục/nhóm trong bảng, mã môn, tên Việt/Anh, tín chỉ, ba cột giờ và tiên quyết nguyên văn. Ngắt dòng trong tên được ghép thành khoảng trắng; ngắt dòng trong tiên quyết được giữ bằng `\n`. Không sửa mã, số liệu hoặc thay mã ngoài bảng bằng mã gần giống.

## Mốc dữ liệu để kiểm thử

[math_p1_review.json](../tests/fixtures/math_p1_review.json) lưu 62 bản ghi đã đối chiếu, nguồn/hash, ngày và phạm vi. Mốc này được tạo sau khi xem PDF và xác nhận bản chép, không phải bằng chứng review chéo của một thành viên khác. Test đọc mốc cố định để phát hiện thay đổi nội dung sau review; test không cần file PDF hoặc đường dẫn Downloads trên máy khác.

- `tests/test_catalog.py`: lỗi file/JSON/schema, whitelist ngành, nguyên nhân lỗi và vị trí phần tử sai, metadata nguồn/xung đột được giữ, không ghi file khi nạp, cùng mã khác ngành được nạp riêng.
- `tests/test_curriculum_data.py`: đối chiếu từng bản ghi với mốc review; đủ phạm vi Người 1; đủ bảy B1; giờ trống và khóa luận không STT; mã ngoài bảng; ngoặc tiên quyết của STT 44; trạng thái và ghi chú tham chiếu ngoài bảng cả bốn ngành.

Khi bản chép hoặc PDF được cập nhật, đối chiếu lại phần thay đổi trước khi cập nhật mốc. Không tái sinh mốc để làm test đạt mà bỏ qua review.

## Kết quả và việc cần xác minh

Không phát hiện sai lệch bản chép trong 62 bản ghi đã kiểm tra. Các điểm sau đã được xác nhận hoặc cần theo dõi:

| Điểm | Bằng chứng PDF | Xử lý/kết luận |
|---|---|---|
| B1 không phải một môn duy nhất | Trang 8, STT 8, `5/35`; bảy mã FLF1107–FLF1707 | Giữ đủ bảy bản ghi, mỗi môn 5 TC và giờ 25/50/175 |
| Ô giờ học trống | Trang 9, CME1000 và PES1000 | Giữ `hours = null`, không điền số 0 hoặc tự suy ra giờ |
| Lựa chọn lập trình | Trang 10, IV.2 `3/12`, STT 31–34 | Bốn môn 3 TC, nhóm yêu cầu chọn 3 TC; không cộng cả bốn vào tổng yêu cầu |
| Mã Giải tích phức và tham chiếu khác mã | Trang 11, STT 38 là MAT3344; STT 49 có tiên quyết MAT3340 | Giữ nguyên cả hai; MAT3340 nằm ngoài bảng, cần xác minh tương đương |
| Ngoặc tiên quyết thực tập | Trang 11, STT 44: `(MAT1202\nMAT3507)/\nMAT3304` | Ngoặc được giữ; test kiểm tra hai mã trong ngoặc cùng có hoặc MAT3304 |
| Khóa luận không đánh STT | Trang 14, V.3.1, MAT4070: 7 TC, giờ 75/60/215, ô tiên quyết trống | Giữ `source_row = null`, `source_rows = []`, nhánh `thesis`, không tự gán STT 86 |
| Tiên quyết trộn “/” và xuống dòng | Ví dụ trang 10, STT 25 MAT2307 | Cần Người 3 xác minh cách nhóm AND/OR trước khi khẳng định điều kiện tư vấn |

Các mã tiên quyết ngoài bảng xuất hiện trong phần Người 1: `MAT1202`, `MAT2320`, `MAT2321`, `MAT2322`, `MAT2400`, `MAT2502`, `MAT3340`, `MAT3500`, `MAT3507`. Mã được giữ nguyên và đã có trong nhóm issue `external_reference` của curriculum.

### Điểm cần Người 3 kiểm tra: ưu tiên AND/OR

Chú thích cuối trang PDF 14 giải thích dấu `/` mang nghĩa “hoặc”, nhưng không nêu rõ quy tắc ưu tiên cho ô trộn `/` và các dòng không có `/`. Ví dụ STT 25, trang 10:

```text
MAT2314
MAT2316/
MAT2505/
MAT2318/
MAT2319
```

Parser hiện tại cho AND ưu tiên hơn OR. Catalog sinh ra cho MAT2307 là:

```json
[["MAT2314", "MAT2505", "MAT2318", "MAT2319"],
 ["MAT2316", "MAT2505", "MAT2318", "MAT2319"]]
```

Vì vậy, chỉ có `MAT2505` cũng làm biểu thức hiện tại trả true, không cần `MAT2314`. Đây là hành vi đã tái hiện từ code, **chưa phải kết luận điều kiện học chính thức**. Nếu ý nghĩa cần dùng là `MAT2314 AND (MAT2316 OR MAT2505 OR MAT2318 OR MAT2319)`, parser hiện tại cần được sửa và kiểm thử sau khi xác minh. Các ô trộn tương tự trong phạm vi review còn có STT 23, 26, 27, 38, 41, 48, 49 và 54.

Bàn giao cho Người 3 xác minh cách nhóm điều kiện và đánh giá ảnh hưởng với Người 2/5; Người 5 kiểm tra chéo hình PDF. Review P1-04 giữ nguyên `prerequisites_raw`, không chọn một cách diễn giải bằng phỏng đoán và không nâng `catalog_status` hoặc `digitization.review_status`.

## Lệnh kiểm tra

```powershell
python -m pytest -q tests/test_catalog.py tests/test_curriculum_data.py
python -X utf8 tools/build_catalogs.py --check
python -m pytest -q
```

Kết quả ngày 09/10/2026: hai file test Catalog/dữ liệu đạt **129 passed, 1 skipped**; toàn bộ bộ test đạt **205 passed, 1 skipped**. `--check` đạt cả bốn ngành và `git diff --check` đạt. Test bị bỏ qua cần quyền tạo symlink trên Windows; kiểm tra từ chối thư mục resolve ra ngoài root vẫn được chạy bằng mock trong `tests/test_catalog.py`.

PDF và các ảnh render chỉ dùng tại máy làm việc; không đưa vào repository. Catalog của cả bốn ngành vẫn là `draft_unverified`, `pending_peer_review`.
