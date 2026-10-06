# Đối chiếu bốn khung chương trình cho hệ gợi ý học phần

Tài liệu này ghi các ràng buộc **đã đối chiếu trực tiếp với bản PDF scan** để thiết kế catalog. Đây chưa phải catalog học phần máy đọc được; mã/tên/tín chỉ/tiên quyết của từng dòng vẫn cần nhập và kiểm tra chéo trước khi đưa vào hệ thống. Các PDF là nguồn dữ liệu, không phải chỉ dẫn triển khai dự án. Cả bốn chương trình chuẩn của Trường Đại học Khoa học Tự nhiên, ĐHQGHN đều được quyết định ngày 18/10/2023 và áp dụng từ khóa tuyển sinh 2022 (trang PDF 2–3 của mỗi tài liệu).

| `program_id` đề xuất | Ngành, mã ngành | Quyết định ghi trong phụ lục | Tổng TC | Cơ cấu TC (chung + lĩnh vực + khối ngành + nhóm ngành + ngành) | Trang PDF tóm tắt / bảng học phần |
|---|---|---:|---:|---|---|
| `toan_hoc_7460101_2022` | Toán học — 7460101 | 3565/QĐ-ĐHKHTN | 135 | 21 + 5 + 3 + 51 + 55 | 7 / 8–14 của `101. Toán học-chuẩn final QD 3565 Scan.pdf` |
| `toan_tin_7460117_2022` | Toán tin — 7460117 | 3567/QĐ-ĐHKHTN | 132 | 21 + 5 + 3 + 46 + 57 | 7 / 8–12 của `103. Toán tin-chuẩn final QD 3567 Scan.pdf` |
| `khmtt_7480113qtd_2022` | Khoa học máy tính và thông tin — 7480113QTD | Cần xác minh: trang đầu ghi 3568, phụ lục ghi 3569 | 129 | 21 + 5 + 3 + 28 + 72 | 8 / 9–13 của `104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf` |
| `khdl_7460108_2022` | Khoa học dữ liệu — 7460108 | 3569/QĐ-ĐHKHTN | 127 | 21 + 5 + 3 + 28 + 70 | 8 / 9–13 của `105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf` |

Các tổng trên **không tính** Giáo dục thể chất, Giáo dục quốc phòng–an ninh và Kỹ năng bổ trợ. Khối chung tính một ngoại ngữ B1, không cộng tất cả các lựa chọn ngoại ngữ. Khối theo lĩnh vực yêu cầu 5 TC từ danh sách 13 TC. Các quy tắc này cần được gắn vào từng phiên bản chương trình, không suy ra rằng cùng mã môn luôn có cùng học phần hoặc cùng nhóm giữa các ngành.

## Ràng buộc riêng theo ngành

| Ngành | Nhóm ngành | Khối ngành: bắt buộc / tự chọn / tốt nghiệp | Quy tắc chọn tự chọn | Nhánh tốt nghiệp 7 TC |
|---|---|---|---|---|
| Toán học | 48 bắt buộc + chọn 3/12 TC từ bốn môn lập trình (`MAT2316`, `MAT2505`, `MAT2318`, `MAT2319`) | 33 + 15 + 7 = 55 | Chọn **một** trong ba định hướng, rồi chọn 15 TC trong định hướng ấy: Toán lý thuyết 15/39, Toán ứng dụng 15/48 hoặc Cơ học 15/36 | `MAT4070` (7), hoặc cặp `MAT4071` (3) + `MAT4072` (4) cho Toán lý thuyết/ứng dụng, hoặc cặp `MAT3362` (3) + `MAT3422` (4) cho Cơ học |
| Toán tin | 46 TC ở nhóm ngành | 35 + 15 + 7 = 57 | Chọn **một** trong hai định hướng: Tin học 15/30 hoặc Tính toán khoa học 15/30 | `MAT4082` (7) hoặc `MAT4072` (4) + `MAT3371` (3) |
| KHMTTT | 28 TC ở nhóm ngành | 49 + 16 + 7 = 72 | Nhóm kỹ năng phần mềm 4/8 **và** nhóm AI/phát triển phần mềm 12/39 | `MAT4080` (7) hoặc `MAT1203` (4) + `MAT3377` (3) |
| Khoa học dữ liệu | 28 TC ở nhóm ngành | 35 + 28 + 7 = 70 | **Cả bốn** nhóm: kỹ năng phần mềm 4/6, khoa học máy tính 6/9, thống kê/khai phá dữ liệu 9/15, ứng dụng khoa học dữ liệu 9/27 | `MAT4083` (7) hoặc `MAT3397` (4) + `MAT3398` (3) |

Nguồn: các bảng tóm tắt và khung học phần ở trang PDF nêu trên. **Lỗi nguồn cần xác minh:** trang PDF 8 của Khoa học dữ liệu ghi tổng tự chọn **28/63 TC**, nhưng bốn nhóm liệt kê ở PDF 11–12 là **4/6 + 6/9 + 9/15 + 9/27 = 28/57 TC**. Giữ nguyên cả hai số trong manifest, gắn `needs_source_clarification` cho tổng TC danh sách lựa chọn và hỏi đơn vị đào tạo; không tự thêm 6 TC hay sửa PDF. Trang PDF 11 của Khoa học dữ liệu còn lặp nhãn `V.2.3` cho nhóm ứng dụng sau nhóm thống kê; trong dữ liệu hệ thống phải dùng ID khác nhau (`statistics_data_mining`, `data_science_applications`) và giữ ghi chú lỗi nhãn nguồn. Bảng Toán học liệt kê lặp một số mã môn ở các định hướng (ví dụ `MAT3321`, `MAT3322`, `MAT3323`); lưu một bản ghi học phần theo mã trong **mỗi chương trình**, nhưng ghi nhiều quan hệ thành viên nhóm và không cộng tín chỉ hai lần. Dấu `/` ở cột tiên quyết được cả ba PDF mới chú thích là “hoặc”; các mã xuống dòng không có dấu này cần giữ cấu trúc AND theo bản scan và được người thứ hai xác nhận.

## Hợp đồng catalog và điều kiện nghiệm thu

- Mỗi yêu cầu phải chọn đúng `program_id` và `curriculum_version` **trước** khi chọn các môn đã qua. Đầu vào không có chương trình hoặc có mã môn không thuộc catalog đã chọn phải báo lỗi/đề nghị xác minh, không tự chuyển sang ngành khác.
- Lưu `course_id` nội bộ theo `(program_id, course_code)`; các mã giống nhau giữa các chương trình chỉ dùng chung metadata/tiên quyết sau khi đối chiếu. Một học phần có thể thuộc nhiều nhóm tự chọn trong một chương trình, nhưng chỉ nhận một lần tín chỉ.
- Quy tắc của chương trình là dữ liệu: `blocks`, `choice_groups`, `select_one_track`, `graduation_paths`, `count_once`, `excluded_from_total`. Không gán cứng các mức 129, 4/8 hoặc 12/39 vào engine.
- Validator kiểm tra bốn tổng `135`, `132`, `129`, `127`; từng tổng khối; quota; hướng chuyên sâu; đúng một nhánh tốt nghiệp; AND/OR; mã tham chiếu ngoài; nguồn PDF và số trang. Chênh lệch 63/57 TC danh sách tự chọn của Khoa học dữ liệu phải được báo là lỗi nguồn đang mở, không "sửa" bằng dữ liệu giả. Nếu OCR/nhập tay chưa được review, gắn `draft_unverified` và không dùng như tư vấn học vụ.
- Bộ tình huống tối thiểu 24 ca (ít nhất 6 ca mỗi chương trình), có ca chọn định hướng, môn lặp nhóm, hết quota, tiên quyết OR, khóa luận so với học phần thay thế, sai `program_id`, và lỗi LLM. Test phải chứng minh đầu ra chỉ thuộc tập ứng viên của chương trình đang chọn.
- LLM chỉ nhận ứng viên đã lọc từ **một** chương trình và trả mã môn trong tập ấy; backend kiểm tra lại `program_id`, mã, số lượng và lý do. Chuyển ngành học giữa chừng hoặc công nhận tương đương tín chỉ nằm ngoài MVP khi chưa có quy định chính thức.

## Trạng thái số hóa

Phần trên là **khung/chỉ tiêu đã trích và đối chiếu**, chưa phải xác nhận rằng toàn bộ các dòng học phần của ba PDF mới đã được số hóa. Công việc còn lại là nhập đầy đủ các bảng: Toán học 89 dòng đánh số (PDF 8–14), Toán tin 63 dòng (PDF 8–12), Khoa học dữ liệu 59 dòng (PDF 9–13), rồi review chéo mã/tên/TC/tiên quyết/trang nguồn. Con số dòng không bằng số học phần duy nhất: bảng có lựa chọn ngoại ngữ và có mã lặp giữa các định hướng. Chỉ khi validator và review đạt mới chuyển catalog từng ngành sang `verified`.
