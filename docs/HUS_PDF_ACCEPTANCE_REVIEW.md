# Đối chiếu nguồn PDF cho bốn catalog HUS, khóa 2022

Ngày thực hiện: 22/10/2026. Người rà soát cuối: người dùng dự án (đã nhận trách nhiệm, **chưa ký xác nhận kết quả**). Phạm vi áp dụng từ khóa tuyển sinh 2022 đã được người dùng xác nhận. Chưa biết có văn bản điều chỉnh nào ban hành sau năm quyết định dưới đây.

## Nguồn đã nhận

Năm PDF trong `docs/` đọc được và SHA-256 đều khớp `metadata_source_archive.documents` trong `database/data/hus_source.json`:

| Quyết định | PDF | SHA-256 | Vai trò |
| --- | --- | --- | --- |
| 3565/QĐ-ĐHKHTN | `101. Toán học-chuẩn final QD 3565 Scan.pdf` | `e6e33a8a489f7ab77f3db0c727cc4c837ba86f8f17a7eae17c9da08d3c066bd0` | Toán học |
| 3566/QĐ-ĐHKHTN | `102. Toán học-tài năng final QD 3566 Scan.pdf` | `96d47580e257606b0bb25544286c1fd0a8a0b4144c912cb663b91e1c02112744` | Chỉ tham chiếu ngoài bốn catalog |
| 3567/QĐ-ĐHKHTN | `103. Toán tin-chuẩn final QD 3567 Scan.pdf` | `6c19e390ba61c1766e2826b055fe39b3987db25ef707263f60ce337347d87df8` | Toán tin |
| 3568/QĐ-ĐHKHTN | `104.-KHMTTT-chuẩn final QD 3568 Scan final (1).pdf` | `bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab` | Khoa học máy tính và thông tin |
| 3569/QĐ-ĐHKHTN | `105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf` | `b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2` | Khoa học dữ liệu |

Trang đầu bốn quyết định catalog ghi ngày 18/10/2023 và mô tả quyết định ban hành chương trình đào tạo điều chỉnh. Tên file QĐ 3568 có thêm `(1)` nhưng nội dung trùng hash đã lưu.

## Đối chiếu đã hoàn thành

Đã render 22 trang bảng của bốn chương trình và trích **danh sách mã học phần theo trang trực tiếp từ ảnh PDF** vào [HUS_PDF_CODE_PAGE_AUDIT.csv](HUS_PDF_CODE_PAGE_AUDIT.csv). Danh sách này được tạo từ OCR cột mã, không sinh từ `hus_source.json` hoặc catalog builder. Có 295 mã OCR đọc chính xác; hai mã `THL1057` (QĐ 3565, trang PDF 8) và `FLF1107` (QĐ 3567, trang PDF 8) được đọc trực tiếp trên ảnh vì OCR nhận sai. Đã so sánh cả số lần xuất hiện của mã trùng, không chỉ tập mã duy nhất.

| Chương trình | Lượt mã/trang trong PDF | So với `official_curriculum_entries` |
| --- | ---: | --- |
| Toán học | 96 | Khớp 96 |
| Toán tin | 69 | Khớp 69 |
| Khoa học máy tính và thông tin | 67 | Khớp 67 |
| Khoa học dữ liệu | 65 | Khớp 65 |
| **Tổng** | **297** | **Khớp 297** |

`tests/database/source/test_pdf_code_page_audit.py` kiểm tra lại phép đối chiếu đa tập mã/trang với source export. Kiểm tra này **chỉ chứng minh sự hiện diện của mã trên đúng trang và số lần lặp**. Nó không xác nhận tên, số tín chỉ, giờ học, tiên quyết, nhóm lựa chọn hoặc hiệu lực học vụ của từng dòng.

## Điểm cần người rà soát quyết định

| Vấn đề | Bằng chứng từ PDF và trạng thái hiện tại | Cần xác nhận |
| --- | --- | --- |
| `MAT3402` | QĐ 3565, trang PDF 13, STT 76 ghi `MAT3402` là tiên quyết của `MAT3423`; chưa tìm thấy dòng định nghĩa môn trong năm PDF. Source giữ `unlisted_prerequisite` và chặn môn phụ thuộc. | Mã này có định nghĩa ở văn bản khác, là mã nhầm, hay có môn tương đương nào được công nhận? |
| `MAT3325` | QĐ 3565, trang PDF 12, STT 56 ghi `MAT2314` và `MAT2304`; trang PDF 13, STT 72 ghi `MAT2304/MAT2322` và `MAT2314`. Source giữ hai variant và trạng thái xung đột. | Hai điều kiện áp dụng theo từng định hướng hay có điều chỉnh/thống nhất khác? |
| `PHI1002` | QĐ 3565, trang PDF 8, STT 3 ghi tiên quyết `PHI1006`; source hiện khớp PDF. Khác biệt với trang web từng được báo cáo. | Có văn bản hiệu lực mới hơn thay ô tiên quyết này không? Nếu không, giữ theo PDF. |
| Văn bản sau quyết định | Người dùng cho biết hiện **chưa biết** có văn bản điều chỉnh khác hay không. | Kiểm tra danh mục văn bản điều chỉnh trước khi kết luận bản 2023 là bản cuối cùng có hiệu lực. |

## Kết quả cập nhật: 10 ca tự động đã chạy được

Đã bổ sung [bộ kỳ vọng HUS 2022](acceptance/hus_2022/README.md) và đường kiểm tra HUS cho đúng 10 ca hiện có; vẫn giữ đường kiểm tra JSON cũ. Các giá trị trong từng ca đã đối chiếu trực tiếp ảnh PDF: tổng tín chỉ ở trang cuối, MAT2505 ở hai ngành, MAT3323 lặp, hai ô MAT3325, MAT3423/MAT3402, PHI1002, MAT3508, giờ MAT4082, MAT4070 không đánh số và nhóm tự chọn Khoa học dữ liệu. Mã/trang của toàn bộ 297 occurrence được so với CSV độc lập; không tạo bốn catalog kỳ vọng từ builder rồi so chúng với chính builder.

Lượt chạy đầu đạt 9/10 và phát hiện HUS export chưa giữ phần tóm tắt Khoa học dữ liệu `28/63` ở trang PDF 8. Đã bổ sung nhóm cha `V.2` trong `official_curriculum_groups`, với locator trong `group_note`; production builder tự giữ thông tin này trong `source_group_rules`. Bốn nhóm con vẫn có offered credits 6+9+15+27=57, kể cả tiêu đề V.2.3 bị lặp trong PDF. Đây là bổ sung bằng chứng nguồn, chưa publish runtime.

Sau sửa: nhóm offline có **302 passed, 35 deselected**, bao gồm 10 ca `full_catalog_acceptance`; không còn skip trong lượt chạy có truyền bộ HUS. Nhóm PostgreSQL có **35 passed, 302 deselected** (43,05 giây), gồm cả legacy và HUS integration trên database/schema thử nghiệm. Tổng hai nhóm là **337 passed riêng biệt**. Ruff cho mã mới/sửa đạt; còn cảnh báo Starlette/httpx đã có từ trước. JUnit PostgreSQL ở `backups/catalog_acceptance_20261022/postgres.xml` (Git bỏ qua). Các kết quả này là nghiệm thu tự động đúng phạm vi assertions, chưa phải người dùng đã ký xác nhận học vụ đầy đủ.

## Giới hạn của kết quả tự động

Chưa hoàn thành nghiệm thu học vụ toàn bộ. Trước đây 10 ca chỉ hỗ trợ thư mục bốn catalog JSON và bị skip. Hiện chúng nhận thêm manifest HUS cùng CSV mã/trang độc lập qua `--full-catalog-root docs/acceptance/hus_2022`. Mười ca có thể chạy trước khi người dùng xác nhận học vụ; trạng thái review không được tự nâng lên verified theo kết quả test. Kết quả không thay thế đối chiếu toàn diện từng trường của tất cả dòng hoặc xác minh văn bản điều chỉnh sau năm 2023.

Để xác nhận học vụ đầy đủ, cần tiếp tục rà từng ô PDF về tên, tín chỉ, giờ, tiên quyết, nhóm và quota, ghi locator cùng sai lệch; xác minh văn bản điều chỉnh; giải quyết hoặc chấp nhận trạng thái an toàn của các mục trên; rồi người dùng xác nhận phạm vi và kết luận review. Các công việc này không ngăn chạy 10 ca tự động. Trước khi có xác nhận học vụ, bốn catalog giữ `draft_unverified`.

Sau chạy PostgreSQL, không còn database `ai07_runtime_test_*` hoặc schema `se_test_*`; `accounts`, `students`, `course_attempts` đều có 0 dòng. JUnit 10 ca nguồn lưu tại `backups/catalog_acceptance_20261022/acceptance.xml`. Không commit/push hoặc publish runtime trong lượt này.

Sau rà dọn bằng project-toolkit: đã xóa ảnh PNG render tạm (có thể tạo lại từ PDF), giữ TXT/TSV OCR, CSV đối chiếu và JUnit. Đã xóa module không dùng `database/hus_db/schema.py`; migration HUS vẫn là nguồn định nghĩa schema và publisher dùng reflection từ database. Suite sau dọn đạt **337 passed, không skip**, Ruff đạt; JUnit ở `backups/catalog_acceptance_20261022/cleanup-regression.xml`.
