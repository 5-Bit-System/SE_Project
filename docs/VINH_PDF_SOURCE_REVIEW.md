# Đối chiếu PDF gốc — Vinh

Ngày rà soát: 20/10/2026. Nguồn: ZIP người dùng cung cấp trong Downloads,
`1. KCT ban hành năm 2023 (áp dụng từ K67)-20261019T180055Z-1-001.zip`.

## Trạng thái sau khi sửa theo yêu cầu của Vinh

Đã bổ sung 5 môn tham chiếu, chuẩn hóa 20 ô nguồn có đủ bằng chứng, thêm 69 quan
hệ tiên quyết và sửa hai locator. Danh mục hiện có 179 môn; bốn catalog vẫn có
65/67/68/90 môn và 290 membership, không thêm ngành Toán tài năng vào runtime.

MAT3359 đã dùng biểu thức có cấu trúc. MAT3325 lưu hai variant và từng quy tắc
theo `group_key` trong `source_prerequisite_rules`, mang trạng thái `conflict` và
tiếp tục bị chặn. MAT3423 vẫn `unknown` vì MAT3402 chưa có định nghĩa.

Đã publish bốn revision mới vào PostgreSQL cục bộ. Kết quả sau cập nhật:
**275 passed, 10 skipped**, 26/26 kiểm tra SQL đạt, Ruff đạt. Các kiểm tra HTTP
thực chạy xác nhận đủ tiên quyết mở MAT2407 ở cả bốn ngành, điều kiện MAT3359
hoạt động, hai trường hợp cần xác nhận vẫn bị chặn. Catalog vẫn `draft_unverified`.

Nguồn lưu các hash và phạm vi đối chiếu trong `prerequisite_pdf_review` của
`database/data/hus_source.json`; snapshot runtime cũng giữ thông tin này.

Các mục phía dưới là bằng chứng rà soát trước khi áp dụng sửa đổi; phần mô tả
“chưa sửa” ở cuối ghi trạng thái của lượt rà soát ban đầu.

## Kết luận

Các mã tiên quyết đang bị báo thiếu có thật trong PDF. Năm mã được định nghĩa
trong chương trình **Toán học tài năng** (file 102), ngoài bốn catalog đang nạp.
Vì vậy không thể kết luận tất cả là lỗi OCR hoặc mã nhập sai. Export giữ được
ô nguồn nhưng việc chuẩn hóa điều kiện đang thiếu danh mục tham chiếu bên ngoài.

Chưa có bằng chứng để tự đặt tên, tín chỉ hoặc mã tương đương cho `MAT3402`.
Môn này được nhắc ở cột tiên quyết của MAT3423 nhưng chưa tìm thấy dòng định nghĩa
trong các bảng chương trình đã xem.

## Phạm vi đã xem trực tiếp

PDF đều là bản scan, `pdftotext` không trích được nội dung bảng. Đã render và đọc
ảnh cột mã môn/tiên quyết của toàn bộ bảng bốn ngành chuẩn:

| File | Chương trình | Trang PDF đã rà | Trang in trên giấy |
| --- | --- | --- | --- |
| 101 | Toán học | 8–14 | 6–12 |
| 103 | Toán tin | 8–12 | 6–10 |
| 104 | Khoa học máy tính và thông tin | 9–13 | 7–11 |
| 105 | Khoa học dữ liệu | 9–13 | 7–11 |

Đối chiếu các ô tiên quyết với 297 dòng `official_curriculum_entries`:
chưa phát hiện ô tiên quyết bị chép mất hoặc sai mã trong phạm vi đã rà. Cả 103
dòng đang để `none` có cột tiên quyết trống ở bảng PDF. Đây là kiểm tra thủ công
cột tiên quyết, không phải nghiệm thu mọi thông tin của chương trình hay quy chế.

File 102 (Toán học tài năng) được đọc bổ sung các trang PDF 9–14 để tìm danh mục
tham chiếu; không tạo thêm catalog ngành thứ năm.

## Năm mã đã tìm được định nghĩa

Nguồn: `102. Toán học-tài năng final QD 3566 Scan.pdf`.

| Mã | Tên học phần in trong PDF | Tín chỉ | Trang PDF / trang in | STT |
| --- | --- | ---: | --- | ---: |
| MAT2320 | Đại số tuyến tính 1 | 5 | 10 / 8 | 20 |
| MAT2321 | Đại số tuyến tính 2 | 5 | 10 / 8 | 21 |
| MAT2322 | Giải tích 3 | 5 | 10 / 8 | 24 |
| MAT2313 | Phương trình đạo hàm riêng 1 | 4 | 10 / 8 | 26 |
| MAT3340 | Giải tích hàm | 4 | 11 / 9 | 38 |

Các mã này không có trong `courses` hiện tại. Có thể bổ sung như danh mục môn
tham chiếu ngoài chương trình khi cập nhật dữ liệu; không mặc nhiên thêm chúng
vào danh sách môn của bốn ngành chuẩn hoặc gán chúng bằng mã cùng tên khác.

`MAT3402` xuất hiện ở điều kiện của MAT3423 trong file 101, trang PDF 13 / trang
in 11, STT 76; cũng xuất hiện trong file 102, trang PDF 14 / trang in 12, STT 75.
Chưa đủ cơ sở xác định tên hay môn thay thế.

## Biểu thức và xung đột xác nhận từ PDF

Các PDF có chú thích cuối bảng: dấu `/` trong danh sách tiên quyết mang nghĩa
“hoặc”. Các mã xuống dòng không có `/` được đọc là các điều kiện đồng thời.

**MAT3359 — Thực tập chuyên ngành**:

- File 101: PDF 11 / trang in 9, STT 44.
- File 103: PDF 10 / trang in 8, STT 39.
- Điều kiện được in là `(MAT1202 và MAT3507) hoặc MAT3304`; file 103 đảo thứ tự
  hai mã trong ngoặc nhưng giữ cùng ý nghĩa.
- Có thể biểu diễn tương đương bằng hai nhóm AND/OR hiện có:
  `[[MAT1202, MAT3304], [MAT3507, MAT3304]]`.
  Đây là đề xuất chuẩn hóa sau đối chiếu, chưa thay đổi dữ liệu runtime.
  Vẫn cần xử lý các mã tham chiếu ngoài ngành trước khi cho nhập transcript.

**MAT3325 — Lịch sử toán học**, file 101 có hai ô khác nhau:

- PDF 12 / trang in 10, STT 56: `MAT2314 và MAT2304`.
- PDF 13 / trang in 11, STT 72: `(MAT2304 hoặc MAT2322) và MAT2314`.

Sự khác biệt có ngay trong PDF; cần giữ theo ngữ cảnh định hướng học hoặc xin
nhóm xác nhận quy tắc gộp. Không chọn tùy ý một ô làm điều kiện chung.

## Hai lỗi vị trí trang trong export

| File / ngành | Môn / STT | `pdf_page` đang lưu | Trang PDF thực tế | Trang in |
| --- | --- | ---: | ---: | ---: |
| 103 / Toán tin | MAT3327 / 51 | 12 | 11 | 9 |
| 105 / Khoa học dữ liệu | MAT2034 / 26 | 11 | 10 | 8 |

Nội dung ô tiên quyết của hai dòng vẫn khớp PDF, nhưng locator đang lệch một
trang. Báo cáo rà soát trước đó ghi trang theo export, nên MAT3327 Toán tin ở
đó mang số 12; khi mở PDF phải đến trang 11.

## Bằng chứng và giới hạn

Bản giải nén, ảnh trang và manifest SHA-256 nằm tại `backups/pdf_review/` (Git
bỏ qua). Quy ước `101-11.png` là ảnh trang thứ 11 trong file PDF 101, tính từ 1,
không phải số trang in dưới chân giấy.

| File | SHA-256 |
| --- | --- |
| 101.pdf | e6e33a8a489f7ab77f3db0c727cc4c837ba86f8f17a7eae17c9da08d3c066bd0 |
| 102.pdf | 96d47580e257606b0bb25544286c1fd0a8a0b4144c912cb663b91e1c02112744 |
| 103.pdf | 6c19e390ba61c1766e2826b055fe39b3987db25ef707263f60ce337347d87df8 |
| 104.pdf | bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab |
| 105.pdf | b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2 |

Ở lượt rà soát ban đầu chỉ đối chiếu và ghi báo cáo; chưa sửa SQL/export, chưa publish revision
mới, chưa đổi trạng thái catalog sang đã xác minh. Kết quả test trước đó
`238 passed, 10 skipped` không tự động chứng nhận những vấn đề nguồn trên đã được
sửa. 10 acceptance test yêu cầu định dạng bộ dữ liệu riêng; ZIP PDF không thể
được truyền trực tiếp vào `--full-catalog-root`.

## Sao lưu và khôi phục bản chạy trước khi sửa

- `backups/pdf_review/ai07_before_prerequisite_review.dump`: bản `pg_dump -Fc`
  trước khi publish.
- `backups/pdf_review/active_revisions_before_review.json`: bốn revision cũ để
  kích hoạt lại bằng `database.tools.publish_catalogs --activate PROGRAM_ID REVISION_ID`.
- `backups/pdf_review/hus_source_before_review.json`: bản export trước khi sửa.

Publisher giữ các snapshot cũ và không xóa quan hệ nguồn trước đó. SQL import
lịch sử trong `database/sql/10_official_curricula_2023.sql` vẫn là bản trước rà
soát; runtime mới phải nạp từ export hiện tại bằng publisher, theo hướng dẫn HUS.
Xem lịch sử Git để biết commit bàn giao các thay đổi.
