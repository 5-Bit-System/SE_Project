# Đáp án thực tế ý định/F2 — 14/11/2026

Google11/12 call:6 đáp án dùng model,1 lỗi output,1 cần làm rõ và4 control. Không retry. Review người thật pending; các phần dưới là đúng phản hồi đã lưu, không phải bản sửa để làm đẹp kết quả.

## IF2-001

**Câu hỏi:** Ngành Toán học có bao nhiêu môn học?

**Scope:** mathematics / QD3565-2023

**Thực tế:** answered; interpretation calls=0; generation calls=1; generation.used=True.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Thông tin theo nguồn đã chọn:

Toán học (QD3565-2023): danh mục có 90 học phần. [1]

Đếm mỗi mã học phần một lần trong danh mục ngành/phiên bản đã chọn; không có nghĩa mỗi sinh viên phải học toàn bộ số môn này.

Trạng thái review: draft_unverified; chưa xác minh hiệu lực hiện tại hoặc áp dụng cho từng sinh viên.

Nguồn [1]: Toán học; https://github.com/5-Bit-System/SE_Project/blob/94b7d05988d4118df283ad09a12ff75cef3161fc/database/data/hus_source.json; Vị trí JSON theo bản chép nguồn đã ghim; chưa xác minh hiệu lực hoặc truy cập lại URL.
```

</details>

- Nguồn: Toán học; review=draft_unverified; https://github.com/5-Bit-System/SE_Project/blob/94b7d05988d4118df283ad09a12ff75cef3161fc/database/data/hus_source.json

## IF2-002

**Câu hỏi:** Cho mình xem toàn bộ danh sách học phần

**Scope:** mathematics / QD3565-2023

**Thực tế:** api_error; interpretation calls=1; generation calls=1; generation.used=False.

API báo lỗi an toàn: `{"code": "output_rejected"}`; không hiển thị đáp án bị chặn và không thay bằng offline.

Diagnostic generation: `output_coverage/fact_keys`. Bước hiểu đã qua kiểm tra để tới generation; metadata interpretation không được trả trong response lỗi. Không lưu raw JSON bị chặn nên chưa biết cụ thể key thiếu/thừa/trùng.

## IF2-003

**Câu hỏi:** Liệt kê các môn trong chương trình

**Scope:** mathematics_informatics / QD3567-2023

**Thực tế:** answered; interpretation calls=0; generation calls=1; generation.used=True.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Thông tin theo nguồn đã chọn:

Toán tin (QD3567-2023): danh mục có 68 học phần. [1]
- CME1000 — Giáo dục quốc phòng - an ninh
- FLF1107 — Tiếng Anh B1
- FLF1207 — Tiếng Nga B1
- FLF1307 — Tiếng Pháp B1
- FLF1407 — Tiếng Trung Quốc B1
- FLF1507 — Tiếng Đức B1
- FLF1607 — Tiếng Nhật Bản B1
- FLF1707 — Tiếng Hàn Quốc B1
- HIS1001 — Lịch sử Đảng Cộng sản Việt Nam
- HIS1056 — Cơ sở văn hóa Việt Nam
- HUS1011 — Tin học cơ sở
- HUS1012 — Kỹ năng bổ trợ
- HUS1021 — Khoa học Trái Đất và sự sống
- HUS1022 — Nhập môn Internet kết nối vạn vật
- HUS1023 — Nhập môn phân tích dữ liệu
- HUS1024 — Nhập môn Robotic
- MAT1201 — Phương pháp nghiên cứu khoa học
- MAT1202 — Lập trình hướng đối tượng
- MAT2300 — Đại số tuyến tính 1
- MAT2301 — Đại số tuyến tính 2
- MAT2302 — Giải tích 1
- MAT2303 — Giải tích 2
- MAT2304 — Giải tích 3
- MAT2314 — Phương trình vi phân
- MAT2404 — Giải tích số
- MAT2405 — Xác suất
- MAT2406 — Thống kê ứng dụng
- MAT2407 — Tối ưu hóa
- MAT2505 — Lập trình cơ bản
- MAT3148 — Tính toán song song
- MAT3323 — Tối ưu rời rạc
- MAT3327 — Điều khiển tối ưu
- MAT3333 — Các mô hình toán ứng dụng 1
- MAT3334 — Các mô hình toán ứng dụng 2
- MAT3335 — Đại số máy tính
- MAT3359 — Thực tập chuyên ngành
- MAT3365 — Phương trình đạo hàm riêng
- MAT3366 — Hệ thống máy tính
- MAT3367 — Đại số ứng dụng
- MAT3368 — Thuật toán ngẫu nhiên
- MAT3369 — Giải tích số nâng cao
- MAT3370 — Thống kê Bayes
- MAT3371 — Xây dựng phần mềm
- MAT3409 — Giải tích hàm ứng dụng
- MAT3452 — Phân tích thống kê nhiều chiều
- MAT3456 — Logic ứng dụng
- MAT3500 — Toán rời rạc
- MAT3504 — Thiết kế và đánh giá thuật toán
- MAT3507 — Cơ sở dữ liệu
- MAT3508 — Nhập môn trí tuệ nhân tạo
- MAT3509 — Ngôn ngữ hình thức và ôtômat
- MAT3514 — Cấu trúc dữ liệu và thuật toán
- MAT3525 — Thực hành tính toán
- MAT3531 — Tính toán phân tán
- MAT3533 — Học máy
- MAT3539 — Mật mã và an toàn dữ liệu
- MAT3545 — Lý thuyết tính toán
- MAT3561 — Xử lí ngôn ngữ tự nhiên và ứng dụng
- MAT3562 — Thị giác máy tính
- MAT3565 — Nhập môn khai phá các tập dữ liệu lớn
- MAT4072 — Một số vấn đề chọn lọc trong tính toán khoa học
- MAT4082 — Khóa luận tốt nghiệp
- PEC1008 — Kinh tế chính trị Mác - Lênin
- PES1000 — Giáo dục thể chất
- PHI1002 — Chủ nghĩa xã hội khoa học
- PHI1006 — Triết học Mác - Lênin
- POL1001 — Tư tưởng Hồ Chí Minh
- THL1057 — Nhà nước và pháp luật đại cương

Đếm mỗi mã học phần một lần trong danh mục ngành/phiên bản đã chọn; không có nghĩa mỗi sinh viên phải học toàn bộ số môn này.

Trạng thái review: draft_unverified; chưa xác minh hiệu lực hiện tại hoặc áp dụng cho từng sinh viên.

Nguồn [1]: Toán tin; https://github.com/5-Bit-System/SE_Project/blob/94b7d05988d4118df283ad09a12ff75cef3161fc/database/data/hus_source.json; Vị trí JSON theo bản chép nguồn đã ghim; chưa xác minh hiệu lực hoặc truy cập lại URL.
```

</details>

- Nguồn: Toán tin; review=draft_unverified; https://github.com/5-Bit-System/SE_Project/blob/94b7d05988d4118df283ad09a12ff75cef3161fc/database/data/hus_source.json

## IF2-004

**Câu hỏi:** Đếm học phần giúp tôi

**Scope:** mathematics_informatics / QD3567-2023

**Thực tế:** needs_clarification; interpretation calls=1; generation calls=0; generation.used=False.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Chưa có thông tin đủ căn cứ để trả lời. Bạn muốn hỏi thông tin ngành, dữ kiện chương trình hay nội dung của môn nào? Hãy nêu một ý và mã/tên đầy đủ của môn nếu có.
```

</details>


Phản hồi yêu cầu làm rõ, không có call diễn đạt; không coi đây là đếm thành công.

## IF2-005

**Câu hỏi:** Ngành khoa học máy tính có bao nhiêu môn học?

**Scope:** computer_science / QD3568-2023

**Thực tế:** answered; interpretation calls=0; generation calls=1; generation.used=True.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Thông tin theo nguồn đã chọn:

Khoa học máy tính và thông tin (QD3568-2023): danh mục có 67 học phần. [1]

Đếm mỗi mã học phần một lần trong danh mục ngành/phiên bản đã chọn; không có nghĩa mỗi sinh viên phải học toàn bộ số môn này.

Trạng thái review: verified; chưa xác minh hiệu lực hiện tại hoặc áp dụng cho từng sinh viên.

Nguồn [1]: Khoa học máy tính và thông tin; https://github.com/5-Bit-System/SE_Project/blob/94b7d05988d4118df283ad09a12ff75cef3161fc/database/data/hus_source.json; Vị trí JSON theo bản chép nguồn đã ghim; chưa xác minh hiệu lực hoặc truy cập lại URL.
```

</details>

- Nguồn: Khoa học máy tính và thông tin; review=verified; https://github.com/5-Bit-System/SE_Project/blob/94b7d05988d4118df283ad09a12ff75cef3161fc/database/data/hus_source.json

## IF2-006

**Câu hỏi:** MAT1204 được tính mấy TC?

**Scope:** computer_science / QD3568-2023

**Thực tế:** answered; interpretation calls=1; generation calls=1; generation.used=True.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Thông tin theo nguồn đã chọn:

MAT1204 — Phương pháp nghiên cứu khoa học (QD3568-2023)
Số tín chỉ: 3

Trạng thái: verified theo sign-off cấp dự án đã ghi trong nguồn; không phải chứng nhận của trường.

Nguồn [1]: 104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf; trang PDF 10; /hus/sources/bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab?page=10#page=10; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.
```

</details>

- Nguồn: 104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf; review=verified; /hus/sources/bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab?page=10#page=10

## IF2-007

**Câu hỏi:** Liệt kê các môn trong chương trình

**Scope:** data_science / QD3569-2023

**Thực tế:** answered; interpretation calls=0; generation calls=1; generation.used=True.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Thông tin theo nguồn đã chọn:

Khoa học dữ liệu (QD3569-2023): danh mục có 65 học phần. [1]
- CME1000 — Giáo dục quốc phòng - an ninh
- FLF1107 — Tiếng Anh B1
- FLF1207 — Tiếng Nga B1
- FLF1307 — Tiếng Pháp B1
- FLF1407 — Tiếng Trung Quốc B1
- FLF1507 — Tiếng Đức B1
- FLF1607 — Tiếng Nhật Bản B1
- FLF1707 — Tiếng Hàn Quốc B1
- HIS1001 — Lịch sử Đảng Cộng sản Việt Nam
- HIS1056 — Cơ sở văn hóa Việt Nam
- HUS1011 — Tin học cơ sở
- HUS1012 — Kỹ năng bổ trợ
- HUS1021 — Khoa học Trái Đất và sự sống
- HUS1022 — Nhập môn Internet kết nối vạn vật
- HUS1023 — Nhập môn phân tích dữ liệu
- HUS1024 — Nhập môn Robotic
- MAT1202 — Lập trình hướng đối tượng
- MAT1204 — Phương pháp nghiên cứu khoa học
- MAT1209 — Tự động hóa
- MAT2034 — Giải tích số
- MAT2323 — Xác suất - Thống kê
- MAT2400 — Đại số tuyến tính
- MAT2403 — Phương trình vi phân
- MAT2407 — Tối ưu hóa
- MAT2501 — Giải tích 1
- MAT2502 — Giải tích 2
- MAT2503 — Giải tích 3
- MAT2505 — Lập trình cơ bản
- MAT3148 — Tính toán song song
- MAT3378 — Quản trị dữ liệu lớn
- MAT3379 — Phân tích hồi quy và ứng dụng
- MAT3381 — Thực tập thực tế về Khoa học dữ liệu
- MAT3382 — Lập trình cho Khoa học dữ liệu
- MAT3383 — Trực quan hóa thông tin
- MAT3385 — Cơ sở dữ liệu Web và hệ thống thông tin
- MAT3386 — Phương pháp tính toán trong thống kê và khoa học dữ liệu
- MAT3387 — Kĩ thuật lấy mẫu khảo sát
- MAT3388 — Phân tích chuỗi thời gian
- MAT3389 — Quy hoạch thực nghiệm
- MAT3390 — Nhập môn Tin sinh học
- MAT3391 — Hệ thống thông tin địa lí
- MAT3392 — Ứng dụng dữ liệu lớn trong quản lí rủi ro tai biến thiên nhiên
- MAT3393 — Khai thác dữ liệu trong Hóa học
- MAT3394 — Mô hình toán sinh thái
- MAT3395 — Lí thuyết trò chơi
- MAT3397 — Một số vấn đề ứng dụng của khoa học dữ liệu
- MAT3398 — Một số chủ đề trong mô hình hóa và phân tích dữ liệu
- MAT3399 — Xử lí ngôn ngữ tự nhiên và học sâu
- MAT3500 — Toán rời rạc
- MAT3504 — Thiết kế và đánh giá thuật toán
- MAT3507 — Cơ sở dữ liệu
- MAT3508 — Nhập môn trí tuệ nhân tạo
- MAT3514 — Cấu trúc dữ liệu và thuật toán
- MAT3533 — Học máy
- MAT3534 — Khai phá dữ liệu
- MAT3535 — Tìm kiếm thông tin
- MAT3557 — Môi trường lập trình Linux
- MAT3562 — Thị giác máy tính
- MAT4083 — Khóa luận tốt nghiệp
- PEC1008 — Kinh tế chính trị Mác - Lênin
- PES1000 — Giáo dục thể chất
- PHI1002 — Chủ nghĩa xã hội khoa học
- PHI1006 — Triết học Mác - Lênin
- POL1001 — Tư tưởng Hồ Chí Minh
- THL1057 — Nhà nước và pháp luật đại cương

Đếm mỗi mã học phần một lần trong danh mục ngành/phiên bản đã chọn; không có nghĩa mỗi sinh viên phải học toàn bộ số môn này.

Trạng thái review: draft_unverified; chưa xác minh hiệu lực hiện tại hoặc áp dụng cho từng sinh viên.

Nguồn [1]: Khoa học dữ liệu; https://github.com/5-Bit-System/SE_Project/blob/94b7d05988d4118df283ad09a12ff75cef3161fc/database/data/hus_source.json; Vị trí JSON theo bản chép nguồn đã ghim; chưa xác minh hiệu lực hoặc truy cập lại URL.
```

</details>

- Nguồn: Khoa học dữ liệu; review=draft_unverified; https://github.com/5-Bit-System/SE_Project/blob/94b7d05988d4118df283ad09a12ff75cef3161fc/database/data/hus_source.json

## IF2-008

**Câu hỏi:** MAT3533 được tính mấy TC?

**Scope:** data_science / QD3569-2023

**Thực tế:** answered; interpretation calls=1; generation calls=1; generation.used=True.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Thông tin theo nguồn đã chọn:

MAT3533 — Học máy (QD3569-2023)
Số tín chỉ: 3

Trạng thái xác minh: draft_unverified; dữ kiện chép từ nguồn, chưa xác minh học vụ.

Mã tiên quyết chưa giải quyết: MAT2406

Nguồn [1]: 105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf; trang PDF 11; /hus/sources/b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2?page=11#page=11; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.
```

</details>

- Nguồn: 105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf; review=draft_unverified; /hus/sources/b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2?page=11#page=11

## IF2-009

**Câu hỏi:** Ngành khoa học máy tính có bao nhiêu môn học?

**Scope:** data_science / QD3569-2023

**Thực tế:** no_information; interpretation calls=0; generation calls=0; generation.used=False.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Chưa có thông tin đủ căn cứ để trả lời. Bạn đang chọn Khoa học dữ liệu nhưng câu hỏi nhắc đến Khoa học máy tính và thông tin. Hãy chọn Khoa học máy tính và thông tin ở ô ngành rồi hỏi lại.
```

</details>


## IF2-010

**Câu hỏi:** Ngành Toán học phải học bao nhiêu môn?

**Scope:** mathematics / QD3565-2023

**Thực tế:** needs_clarification; interpretation calls=0; generation calls=0; generation.used=False.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Chưa có thông tin đủ căn cứ để trả lời. Bạn muốn đếm/liệt kê toàn bộ danh mục hay số môn phải học/bắt buộc/tự chọn theo điều kiện? Hiện chỉ hỗ trợ toàn bộ danh mục; chưa tính số môn mỗi sinh viên phải học hoặc lọc theo điều kiện.
```

</details>


## IF2-011

**Câu hỏi:** Nội dung MAT3533?

**Scope:** data_science / QD3569-2023

**Thực tế:** needs_clarification; interpretation calls=0; generation calls=0; generation.used=False.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Chưa có thông tin đủ căn cứ để trả lời. Cần bật cho phép kiến thức AI tham khảo để dùng dữ liệu F3 AI sinh.
```

</details>


## IF2-012

**Câu hỏi:** MAT9999 có bao nhiêu tín chỉ?

**Scope:** data_science / QD3569-2023

**Thực tế:** no_information; interpretation calls=0; generation calls=0; generation.used=False.

<details>
<summary>Phản hồi nguyên văn</summary>

```text
Chưa có thông tin đủ căn cứ để trả lời. Không có môn này trong ngành và phiên bản đã chọn.
```

</details>

