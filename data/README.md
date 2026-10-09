# Dữ liệu khung chương trình đào tạo

Đã chuyển toàn bộ phần bảng Khung chương trình đào tạo trong bốn PDF scan được cung cấp. Mỗi ngành có catalog độc lập; mã môn có thể giống nhau giữa các ngành nhưng không tự gộp bản ghi, nhóm hoặc tiên quyết.

| Thư mục trong `curricula/` | STT nguồn | Dòng môn không có STT | Bản ghi theo mã sau khi gộp trong ngành | Tổng TC yêu cầu |
|---|---:|---:|---:|---:|
| `toan_hoc_7460101_2022` | 89 | 1 | 90 | 135 |
| `toan_tin_7460117_2022` | 63 | 0 | 68 | 132 |
| `khmtt_7480113qtd_2022` | 61 | 0 | 67 | 129 |
| `khdl_7460108_2022` | 59 | 0 | 65 | 127 |

Tổng cộng 290 bản ghi **theo ngành**. Đây không phải 290 môn khác nhau trên toàn bộ bốn ngành. Một dòng STT Ngoại ngữ B1 chứa bảy phương án; một môn có thể xuất hiện ở nhiều nhóm. Khóa luận `MAT4070` của Toán học có dòng riêng không đánh STT, đã được giữ đầy đủ.

## Ba file trong mỗi ngành

- `source_rows.json`: bản chép từng lần xuất hiện trong bảng, giữ STT, trang PDF, nhãn mục, mã/tên Việt–Anh, TC, ba cột giờ học và tiên quyết nguyên văn. Ô giờ học trống được lưu `null`.
- `courses.json`: bản ghi duy nhất theo mã trong ngành, dùng cho app. Môn lặp giữ nhiều `source_rows`, `choice_group_ids`; không có trường `sources`, nguồn chi tiết tra lại ở `source_rows.json`.
- `curriculum.json`: tổng/chỉ tiêu từng khối, nhóm lựa chọn và thành viên, hướng chuyên sâu, phương án tốt nghiệp, môn không tính vào tổng TC, SHA-256 nguồn và lỗi nguồn cần xác minh.

`validation_report.json` ở cấp `data/` ghi kết quả kiểm tra cấu trúc/độ phủ, không thay thế review chéo với PDF. `digitization.status = complete` xác nhận đã chép đủ bảng; `catalog_status = draft_unverified` và `review_status = pending_peer_review` giữ trạng thái cần người thứ hai kiểm tra.

[Biên bản review P1-04](../docs/REVIEW_P1_04_TOAN_HOC.md) ghi đối chiếu trực quan Toán học STT 1–55 và MAT4070 với PDF đúng SHA-256; kèm mốc dữ liệu để test và điểm cần xác minh về nhóm AND/OR. Review chéo của thành viên vẫn đang chờ.

## Cách hiểu dữ liệu

`prerequisites` là AND giữa các danh sách và OR giữa các mã trong cùng danh sách. Ví dụ `[["MAT2301", "MAT2321"], ["MAT2303"]]` nghĩa là `(MAT2301 hoặc MAT2321) và MAT2303`. Biểu thức có ngoặc được chuyển tương đương sang cấu trúc này; `prerequisites_raw` vẫn giữ cách viết trong bảng. Các mã tham chiếu không có trong ngành được giữ ở `external_prerequisite_codes`, chưa tự công nhận môn ngành khác.

Các nhóm dùng `selection_mode = exactly_one_course` (ngoại ngữ, lựa chọn lập trình Toán học) hoặc `minimum_credits` (chỉ tiêu nhóm). `listed_credits` là TC của danh sách phương án, khác `required_credits` là TC phải chọn. `track_selection` quy định chọn một hướng khi áp dụng. `graduation_selection.paths` là các phương án thay thế nhau; `allowed_track_ids = []` nghĩa là không giới hạn hướng theo bảng nguồn. Tổng TC hoàn thành chỉ cộng một lần mỗi môn và loại các mã trong `excluded_from_total`.

## Những điểm nguồn được giữ lại

- KHDL: tóm tắt tự chọn `28/63` khác tổng các nhóm `28/57`; dòng Ngoại ngữ B1 ghi `5/15` nhưng liệt kê bảy môn tổng 35 TC; hai nhóm cùng nhãn `V.2.3` được gắn ID khác nhau.
- Toán học: `MAT3325` có tiên quyết khác nhau ở STT 56 và 72. Lưu cả hai trong `prerequisite_variants`, đánh `source_conflict`; app tạm không gợi ý môn này. Mã `MAT3344` trong bảng và tham chiếu `MAT3340` ở môn khác được giữ nguyên.
- KHMTTT và Toán tin: tổng ba cột giờ của khóa luận khác TC × 50; số liệu scan được giữ nguyên, không tự tính lại để ghi đè.
- Mã Cơ sở văn hóa Việt Nam được chép đúng từng bảng: `HUS1056` ở KHMTTT, `HIS1056` ở ba ngành còn lại.
- Các môn tiên quyết ngoài bảng và số quyết định KHMTTT cần xác minh; chi tiết nằm trong `source_issues` của từng ngành.

App hiện mới có rule engine cơ bản; dữ liệu đã biểu diễn hướng và phương án tốt nghiệp nhưng các chức năng này vẫn cần Eligibility xử lý, Profile nhận lựa chọn của sinh viên và Recommendation tích hợp vào luồng gợi ý. Không dùng việc JSON đầy đủ để khẳng định rule engine đã xử lý đủ mọi quy tắc.

## Kiểm tra và cập nhật

```powershell
python -X utf8 tools/build_catalogs.py --check
python -X utf8 tools/build_catalogs.py --check --report
python -m pytest -q
```

Khi sửa dữ liệu sau review, sửa bản chép nguồn/metadata rồi chạy `python -X utf8 tools/build_catalogs.py --write` để sinh lại catalog. Chạy `--check` kiểm tra catalog đúng với nguồn, đủ STT, mã duy nhất, quota/nhóm/khối, nhánh tốt nghiệp và đồ thị tiên quyết. Khi cập nhật, đồng thời kiểm tra lại các ghi chú và báo cáo nguồn; báo cáo được tạo khi số hóa không tự thay đổi theo file JSON.

`--check` kiểm tra trực tiếp `courses.json` và báo lỗi nếu mã bị trùng, thiếu/thừa mã so với nguồn, tham chiếu nhóm sai hoặc mất STT/biến thể tiên quyết. Nhiều mã B1 cùng STT 8 vẫn hợp lệ; lặp cùng cặp STT–mã môn là lỗi. `--report` có `prerequisite_conflicts`, gồm các STT, trang và tiên quyết nguyên văn để review. Trạng thái `passed` chỉ xác nhận catalog giữ đúng dữ liệu đã chép, kể cả xung đột được đánh `source_conflict`; không xác nhận mâu thuẫn PDF đã được giải quyết hay chuyển catalog sang `verified`.
