# R? so?t metadata m?n h?c ? 17/10/2026

## Ph?m vi v? c?ch ki?m tra

?? ki?m tra t?ng b?n ghi c?a 4 catalog d?ng b?ng builder hi?n t?i t? database/data/hus_source.json (290 b?n ghi theo ng?nh, 174 m? ngu?n d?ng chung) v? b? m?u KHDL (65 b?n ghi). Kh?ng truy v?n snapshot PostgreSQL ?ang ch?y; k?t qu? ?p d?ng cho c?c file ngu?n t?i th?i ?i?m r?. Kh?ng c? ??i so?t PDF g?c trong ??t n?y.

Ki?m tra schema/evidence, m? tr?ng, credits v?i m?i source occurrence, quan h? nh?m/nh?nh/kh?i, ti?n quy?t AND/OR, external references, chu tr?nh, nh?n t? ?i?n b?ng validator d? ?n. ??m t?ng tr??ng thi?u; ??i chi?u b? m?u v?i source_rows v? ngu?n HUS. PASS c?u tr?c kh?ng ch?ng minh n?i dung ch?nh th?c ??ng.

## K?t lu?n

Metadata t? v?n ch?a ?? ?? x?p h?ng theo ch? ??: to?n b? 290 b?n ghi HUS v? 65 b?n ghi m?u ??u null ? topics, description, orientation, difficulty, workload, career_paths. Kh?ng c? nh?n hi?n h?u ?? th?m ??nh ng? ngh?a t?ng m?n. Null ??ng quy t?c khi thi?u ngu?n; c?n b? sung n?i dung c? b?ng ch?ng tr??c khi g?n nh?n.

| B? | Ng?nh | S? m?n | Topics c? d? li?u | Ti?n quy?t unknown | M?n c? m? ti?n quy?t ngo?i ng?nh |
|---|---|---:|---:|---:|---:|
| HUS | khdl_7460108_2022 | 65 | 0 | 1 | 2 |
| HUS | khmtt_7480113qtd_2022 | 67 | 0 | 1 | 3 |
| HUS | toan_hoc_7460101_2022 | 90 | 0 | 15 | 7 |
| HUS | toan_tin_7460117_2022 | 68 | 0 | 4 | 9 |
| SAMPLE | khdl_7460108_2022 | 65 | 0 | 0 | 3 |

## Ph?t hi?n c?n x? l?

1. Ngu?n courses: 174/174 m? c? topics=[] v? description=null. Builder kh?ng ??a topics/description ngu?n l?n tr??ng t? v?n, vocabulary HUS r?ng. Ch? ?i?n JSON ngu?n s? ch?a ?? ?? ranking nh?n metadata; c?n t?ch h?p ?nh x? v? b?ng ch?ng t??ng ?ng.
2. B? m?u c? 65 t?n ti?ng Anh v? 63 b? gi? h?c; catalog HUS d?ng ra kh?ng c? c?c tr??ng n?y. Ph?i xem x?t ngu?n tr??c khi chuy?n, kh?ng t? ??ng h?p nh?t c? b? m?u.
3. C? 21 b?n ghi theo ng?nh c? prerequisite_status=unknown. Danh s?ch ??y ?? ? b?ng d??i/CSV. C?c bi?u th?c r?ng trong nh?m n?y kh?ng ???c hi?u l? kh?ng c? ti?n quy?t.
4. MAT2407 KHDL: b? m?u c? bi?u th?c AND/OR v? unresolved_external; HUS gi? nguy?n ghi ch? ngu?n nh?ng bi?u th?c r?ng, status unknown. C?n ??i so?t ngu?n.
5. MAT3562 KHDL: m?u (MAT2301 OR MAT2400) AND (MAT2301 OR MAT3533); HUS (MAT2301 OR MAT2400) AND MAT3533. Kh?c nhau v? logic; MAT2301 l? m? ngo?i catalog KHDL. Kh?ng k?t lu?n b?n n?o ??ng khi ch?a ??i chi?u PDF.
6. MAT3533 KHDL: hai b? c? c?ng logic OR sau khi b? kh?c bi?t th? t?; tr?ng th?i external kh?c nhau. Kh?ng coi kh?c th? t? l? l?i d? li?u.
7. C? l?i s? d?ng nh?n trong scoring.py: c?u h?i computer_vision ???c thay underscore th?nh kho?ng tr?ng nh?ng topics trong searchable v?n computer_vision. Probe ch? b?t tr?ng s? topic cho nh?n tr?ng tr? 0.0 thay v? 1.0. fit_reason d?ng c?ng c?ch so kh?p. ??y l? l?i code ph?t hi?n k?m audit, ch?a s?a.
8. T? ?i?n m?u c? 24 topics v? 6 career_paths nh?ng alias ch? c? computer vision. Extractor c? b?ng alias ri?ng, ch?a ??ng b? vocabulary; vocabulary HUS kh?ng c? nh?n. C?n th?ng nh?t tr??c khi nh?p metadata t? v?n.

## V? d? Th? gi?c m?y t?nh

MAT3562 ? KHDL v? To?n tin, MAT3562E ? KHMTTT ??u 3 t?n ch? theo export; topics/description hi?n null. H?c m?y c? trong ti?n quy?t t??ng ?ng, nh?ng ti?n quy?t kh?ng t? ch?ng minh n?i dung m?n. Mu?n g?n machine_learning, computer_vision, image_processing c?n ?? c??ng ho?c rubric ?nh x? c? ngu?n theo ??c t?.

## ??i chi?u b? m?u v?i b?n ch?p source_rows

Sai kh?c t?n/t?n ti?ng Anh/t?n ch?/gi? so v?i ?t nh?t m?t d?ng c?ng m?: 0. Xem audit-details.json. ??y l? nh?t qu?n n?i b? gi?a b?n ch?p, kh?ng ph?i ki?m ??nh ngu?n ??c l?p.

## Th? t? ho?n thi?n

1. Thu th?p ?? c??ng/m? t? m?n; nh?p description v? topics k?m field_evidence, ?u ti?n m?n chuy?n ng?nh.
2. ??i so?t 21 ti?n quy?t unknown v? kh?c bi?t MAT2407/MAT3562; gi? c?c l?a ch?n ngo?i ng?nh ??ng ngu?n.
3. ??ng b? vocabulary, alias, builder v? b? so kh?p nh?n.
4. Ch? b? sung difficulty/workload khi c? rubric; kh?ng suy ra t? t?n ch?.

## T?ng b?n ghi

T?t c? h?ng d??i c? schema PASS, s?u tr??ng t? v?n ??u null, source_status=draft_unverified. CSV k?m to?n b? tr??ng, ngu?n v? b?ng ch?ng ?? l?c theo ng?nh/m?n.

| B?/ng?nh | M? | T?n | TC | Ti?n quy?t | Ngo?i ng?nh | Trang |
|---|---|---|---:|---|---|---|
| HUS | CME1000 | Giáo dục quốc phòng - an ninh | 8 | draft_unverified |  | 9 |
| HUS | FLF1107 | Tiếng Anh B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1207 | Tiếng Nga B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1307 | Tiếng Pháp B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1407 | Tiếng Trung Quốc B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1507 | Tiếng Đức B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1607 | Tiếng Nhật Bản B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1707 | Tiếng Hàn Quốc B1 | 5 | draft_unverified |  | 9 |
| HUS | HIS1001 | Lịch sử Đảng Cộng sản Việt Nam | 2 | draft_unverified |  | 9 |
| HUS | HIS1056 | Cơ sở văn hóa Việt Nam | 3 | draft_unverified |  | 10 |
| HUS | HUS1011 | Tin học cơ sở | 3 | draft_unverified |  | 9 |
| HUS | HUS1012 | Kỹ năng bổ trợ | 3 | draft_unverified |  | 9 |
| HUS | HUS1021 | Khoa học Trái Đất và sự sống | 3 | draft_unverified |  | 10 |
| HUS | HUS1022 | Nhập môn Internet kết nối vạn vật | 2 | draft_unverified |  | 10 |
| HUS | HUS1023 | Nhập môn phân tích dữ liệu | 2 | draft_unverified |  | 10 |
| HUS | HUS1024 | Nhập môn Robotic | 3 | draft_unverified |  | 10 |
| HUS | MAT1202 | Lập trình hướng đối tượng | 3 | draft_unverified |  | 11 |
| HUS | MAT1204 | Phương pháp nghiên cứu khoa học | 3 | draft_unverified |  | 10 |
| HUS | MAT1209 | Tự động hóa | 2 | draft_unverified |  | 11 |
| HUS | MAT2034 | Giải tích số | 3 | draft_unverified |  | 11 |
| HUS | MAT2323 | Xác suất - Thống kê | 4 | draft_unverified |  | 10 |
| HUS | MAT2400 | Đại số tuyến tính | 5 | draft_unverified |  | 10 |
| HUS | MAT2403 | Phương trình vi phân | 3 | draft_unverified |  | 10 |
| HUS | MAT2407 | Tối ưu hóa | 3 | unknown |  | 10 |
| HUS | MAT2501 | Giải tích 1 | 4 | draft_unverified |  | 10 |
| HUS | MAT2502 | Giải tích 2 | 4 | draft_unverified |  | 10 |
| HUS | MAT2503 | Giải tích 3 | 2 | draft_unverified |  | 10 |
| HUS | MAT2505 | Lập trình cơ bản | 3 | draft_unverified |  | 10 |
| HUS | MAT3148 | Tính toán song song | 3 | draft_unverified |  | 11 |
| HUS | MAT3378 | Quản trị dữ liệu lớn | 3 | draft_unverified |  | 11 |
| HUS | MAT3379 | Phân tích hồi quy và ứng dụng | 3 | draft_unverified |  | 11 |
| HUS | MAT3381 | Thực tập thực tế về Khoa học dữ liệu | 3 | draft_unverified |  | 11 |
| HUS | MAT3382 | Lập trình cho Khoa học dữ liệu | 2 | draft_unverified |  | 11 |
| HUS | MAT3383 | Trực quan hóa thông tin | 2 | draft_unverified |  | 11 |
| HUS | MAT3385 | Cơ sở dữ liệu Web và hệ thống thông tin | 3 | draft_unverified |  | 11 |
| HUS | MAT3386 | Phương pháp tính toán trong thống kê và khoa học dữ liệu | 3 | draft_unverified |  | 12 |
| HUS | MAT3387 | Kĩ thuật lấy mẫu khảo sát | 3 | draft_unverified |  | 12 |
| HUS | MAT3388 | Phân tích chuỗi thời gian | 3 | draft_unverified |  | 12 |
| HUS | MAT3389 | Quy hoạch thực nghiệm | 3 | draft_unverified |  | 12 |
| HUS | MAT3390 | Nhập môn Tin sinh học | 3 | draft_unverified |  | 12 |
| HUS | MAT3391 | Hệ thống thông tin địa lí | 3 | draft_unverified |  | 12 |
| HUS | MAT3392 | Ứng dụng dữ liệu lớn trong quản lí rủi ro tai biến thiên nhiên | 3 | draft_unverified |  | 12 |
| HUS | MAT3393 | Khai thác dữ liệu trong Hóa học | 3 | draft_unverified |  | 12 |
| HUS | MAT3394 | Mô hình toán sinh thái | 3 | draft_unverified |  | 12 |
| HUS | MAT3395 | Lí thuyết trò chơi | 3 | draft_unverified |  | 12 |
| HUS | MAT3397 | Một số vấn đề ứng dụng của khoa học dữ liệu | 4 | draft_unverified |  | 13 |
| HUS | MAT3398 | Một số chủ đề trong mô hình hóa và phân tích dữ liệu | 3 | draft_unverified |  | 13 |
| HUS | MAT3399 | Xử lí ngôn ngữ tự nhiên và học sâu | 3 | draft_unverified |  | 12 |
| HUS | MAT3500 | Toán rời rạc | 4 | draft_unverified |  | 11 |
| HUS | MAT3504 | Thiết kế và đánh giá thuật toán | 3 | draft_unverified |  | 11 |
| HUS | MAT3507 | Cơ sở dữ liệu | 4 | draft_unverified |  | 11 |
| HUS | MAT3508 | Nhập môn trí tuệ nhân tạo | 3 | draft_unverified |  | 11 |
| HUS | MAT3514 | Cấu trúc dữ liệu và thuật toán | 4 | draft_unverified |  | 11 |
| HUS | MAT3533 | Học máy | 3 | draft_unverified | MAT2406 | 11 |
| HUS | MAT3534 | Khai phá dữ liệu | 3 | draft_unverified |  | 12 |
| HUS | MAT3535 | Tìm kiếm thông tin | 3 | draft_unverified |  | 12 |
| HUS | MAT3557 | Môi trường lập trình Linux | 2 | draft_unverified |  | 11 |
| HUS | MAT3562 | Thị giác máy tính | 3 | draft_unverified | MAT2301 | 12 |
| HUS | MAT4083 | Khóa luận tốt nghiệp | 7 | draft_unverified |  | 13 |
| HUS | PEC1008 | Kinh tế chính trị Mác - Lênin | 2 | draft_unverified |  | 9 |
| HUS | PES1000 | Giáo dục thể chất | 4 | draft_unverified |  | 9 |
| HUS | PHI1002 | Chủ nghĩa xã hội khoa học | 2 | draft_unverified |  | 9 |
| HUS | PHI1006 | Triết học Mác - Lênin | 3 | draft_unverified |  | 9 |
| HUS | POL1001 | Tư tưởng Hồ Chí Minh | 2 | draft_unverified |  | 9 |
| HUS | THL1057 | Nhà nước và pháp luật đại cương | 2 | draft_unverified |  | 9 |
| HUS | CME1000 | Giáo dục quốc phòng - an ninh | 8 | draft_unverified |  | 9 |
| HUS | FLF1107 | Tiếng Anh B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1207 | Tiếng Nga B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1307 | Tiếng Pháp B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1407 | Tiếng Trung Quốc B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1507 | Tiếng Đức B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1607 | Tiếng Nhật Bản B1 | 5 | draft_unverified |  | 9 |
| HUS | FLF1707 | Tiếng Hàn Quốc B1 | 5 | draft_unverified |  | 9 |
| HUS | HIS1001 | Lịch sử Đảng Cộng sản Việt Nam | 2 | draft_unverified |  | 9 |
| HUS | HIS1056 | Cơ sở văn hóa Việt Nam | 3 | draft_unverified |  | 10 |
| HUS | HUS1011 | Tin học cơ sở | 3 | draft_unverified |  | 9 |
| HUS | HUS1012 | Kỹ năng bổ trợ | 3 | draft_unverified |  | 9 |
| HUS | HUS1021 | Khoa học Trái Đất và sự sống | 3 | draft_unverified |  | 10 |
| HUS | HUS1022 | Nhập môn Internet kết nối vạn vật | 2 | draft_unverified |  | 10 |
| HUS | HUS1023 | Nhập môn phân tích dữ liệu | 2 | draft_unverified |  | 10 |
| HUS | HUS1024 | Nhập môn Robotic | 3 | draft_unverified |  | 10 |
| HUS | MAT1202 | Lập trình hướng đối tượng | 3 | draft_unverified |  | 11 |
| HUS | MAT1203 | Phân tích và thiết kế hệ thống thông tin | 4 | draft_unverified |  | 13 |
| HUS | MAT1204 | Phương pháp nghiên cứu khoa học | 3 | draft_unverified |  | 10 |
| HUS | MAT1205E | Tiếng Anh chuyên ngành khoa học máy tính | 2 | draft_unverified |  | 10 |
| HUS | MAT1206E | Nhập môn Trí tuệ nhân tạo | 3 | draft_unverified |  | 11 |
| HUS | MAT1207 | Công nghệ phần mềm | 3 | draft_unverified |  | 11 |
| HUS | MAT1208 | Xây dựng hệ thống nhúng | 2 | draft_unverified |  | 12 |
| HUS | MAT2034 | Giải tích số | 3 | draft_unverified |  | 12 |
| HUS | MAT2323 | Xác suất - Thống kê | 4 | draft_unverified |  | 10 |
| HUS | MAT2400 | Đại số tuyến tính | 5 | draft_unverified |  | 10 |
| HUS | MAT2403 | Phương trình vi phân | 3 | draft_unverified |  | 10 |
| HUS | MAT2407 | Tối ưu hóa | 3 | unknown |  | 10 |
| HUS | MAT2501 | Giải tích 1 | 4 | draft_unverified |  | 10 |
| HUS | MAT2502 | Giải tích 2 | 4 | draft_unverified |  | 10 |
| HUS | MAT2503 | Giải tích 3 | 2 | draft_unverified |  | 10 |
| HUS | MAT2505 | Lập trình cơ bản | 3 | draft_unverified |  | 10 |
| HUS | MAT3148 | Tính toán song song | 3 | draft_unverified |  | 12 |
| HUS | MAT3373E | Nhập môn an toàn máy tính | 3 | draft_unverified |  | 11 |
| HUS | MAT3374 | Thực tập thực tế phát triển phần mềm | 3 | draft_unverified |  | 11 |
| HUS | MAT3377 | Một số vấn đề chọn lọc về Trí tuệ nhân tạo | 3 | draft_unverified |  | 13 |
| HUS | MAT3452 | Phân tích thống kê nhiều chiều | 3 | draft_unverified | MAT2311,MAT2406 | 12 |
| HUS | MAT3453 | Phương pháp chọn mẫu dữ liệu | 3 | draft_unverified |  | 12 |
| HUS | MAT3500 | Toán rời rạc | 4 | draft_unverified |  | 11 |
| HUS | MAT3505 | Kiến trúc máy tính | 3 | draft_unverified |  | 11 |
| HUS | MAT3506 | Mạng máy tính | 3 | draft_unverified |  | 11 |
| HUS | MAT3507 | Cơ sở dữ liệu | 4 | draft_unverified |  | 11 |
| HUS | MAT3514 | Cấu trúc dữ liệu và thuật toán | 4 | draft_unverified |  | 11 |
| HUS | MAT3519 | Ngôn ngữ lập trình thứ hai | 2 | draft_unverified |  | 11 |
| HUS | MAT3533 | Học máy | 3 | draft_unverified | MAT2406 | 11 |
| HUS | MAT3534 | Khai phá dữ liệu | 3 | draft_unverified |  | 12 |
| HUS | MAT3535 | Tìm kiếm thông tin | 3 | draft_unverified |  | 12 |
| HUS | MAT3538 | Các hệ thống tri thức | 3 | draft_unverified |  | 12 |
| HUS | MAT3539 | Mật mã và an toàn dữ liệu | 3 | draft_unverified | MAT2301,MAT2316,MAT2318,MAT2319 | 12 |
| HUS | MAT3541E | Nguyên lí các ngôn ngữ lập trình | 3 | draft_unverified |  | 11 |
| HUS | MAT3542 | Phát triển ứng dụng web | 3 | draft_unverified |  | 12 |
| HUS | MAT3550E | Nguyên lí hệ điều hành | 3 | draft_unverified |  | 11 |
| HUS | MAT3552E | Thiết kế và đánh giá thuật toán | 3 | draft_unverified |  | 11 |
| HUS | MAT3554E | Ngôn ngữ hình thức và ôtômat | 3 | draft_unverified |  | 12 |
| HUS | MAT3557 | Môi trường lập trình Linux | 2 | draft_unverified |  | 11 |
| HUS | MAT3558 | Lập trình mobile | 2 | draft_unverified |  | 11 |
| HUS | MAT3560 | Phát triển phần mềm trò chơi | 2 | draft_unverified |  | 12 |
| HUS | MAT3561E | Xử lí ngôn ngữ tự nhiên và ứng dụng | 3 | draft_unverified |  | 12 |
| HUS | MAT3562E | Thị giác máy tính | 3 | draft_unverified |  | 12 |
| HUS | MAT3563 | Một số vấn đề chọn lọc về thị giác máy tính | 3 | draft_unverified |  | 12 |
| HUS | MAT4080 | Khóa luận tốt nghiệp | 7 | draft_unverified |  | 13 |
| HUS | PEC1008 | Kinh tế chính trị Mác - Lênin | 2 | draft_unverified |  | 9 |
| HUS | PES1000 | Giáo dục thể chất | 4 | draft_unverified |  | 9 |
| HUS | PHI1002 | Chủ nghĩa xã hội khoa học | 2 | draft_unverified |  | 9 |
| HUS | PHI1006 | Triết học Mác - Lênin | 3 | draft_unverified |  | 9 |
| HUS | POL1001 | Tư tưởng Hồ Chí Minh | 2 | draft_unverified |  | 9 |
| HUS | THL1057 | Nhà nước và pháp luật đại cương | 2 | draft_unverified |  | 9 |
| HUS | CME1000 | Giáo dục quốc phòng - an ninh | 8 | draft_unverified |  | 9 |
| HUS | FLF1107 | Tiếng Anh B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1207 | Tiếng Nga B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1307 | Tiếng Pháp B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1407 | Tiếng Trung Quốc B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1507 | Tiếng Đức B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1607 | Tiếng Nhật Bản B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1707 | Tiếng Hàn Quốc B1 | 5 | draft_unverified |  | 8 |
| HUS | HIS1001 | Lịch sử Đảng Cộng sản Việt Nam | 2 | draft_unverified |  | 8 |
| HUS | HIS1056 | Cơ sở văn hóa Việt Nam | 3 | draft_unverified |  | 9 |
| HUS | HUS1011 | Tin học cơ sở | 3 | draft_unverified |  | 8 |
| HUS | HUS1012 | Kỹ năng bổ trợ | 3 | draft_unverified |  | 9 |
| HUS | HUS1021 | Khoa học Trái Đất và sự sống | 3 | draft_unverified |  | 9 |
| HUS | HUS1022 | Nhập môn Internet kết nối vạn vật | 2 | draft_unverified |  | 9 |
| HUS | HUS1023 | Nhập môn phân tích dữ liệu | 2 | draft_unverified |  | 9 |
| HUS | HUS1024 | Nhập môn Robotic | 3 | draft_unverified |  | 9 |
| HUS | MAT1076 | Cơ học lý thuyết | 3 | draft_unverified |  | 9 |
| HUS | MAT2300 | Đại số tuyến tính 1 | 4 | draft_unverified |  | 9 |
| HUS | MAT2301 | Đại số tuyến tính 2 | 4 | draft_unverified |  | 9 |
| HUS | MAT2302 | Giải tích 1 | 5 | draft_unverified |  | 9 |
| HUS | MAT2303 | Giải tích 2 | 5 | draft_unverified |  | 9 |
| HUS | MAT2304 | Giải tích 3 | 4 | draft_unverified |  | 9 |
| HUS | MAT2306 | Phương trình đạo hàm riêng 1 | 3 | draft_unverified |  | 10 |
| HUS | MAT2307 | Giải tích số 1 | 4 | draft_unverified |  | 10 |
| HUS | MAT2308 | Xác suất 1 | 3 | unknown |  | 10 |
| HUS | MAT2310 | Hình học giải tích | 2 | unknown |  | 10 |
| HUS | MAT2311 | Thống kê ứng dụng | 4 | draft_unverified |  | 10 |
| HUS | MAT2314 | Phương trình vi phân | 4 | unknown |  | 9 |
| HUS | MAT2315 | Phương pháp nghiên cứu khoa học | 3 | draft_unverified |  | 10 |
| HUS | MAT2316 | Lập trình C/C++ | 3 | draft_unverified |  | 10 |
| HUS | MAT2318 | Lập trình Python | 3 | draft_unverified |  | 10 |
| HUS | MAT2319 | Lập trình Julia | 3 | draft_unverified |  | 10 |
| HUS | MAT2407 | Tối ưu hóa | 3 | unknown |  | 10 |
| HUS | MAT2505 | Lập trình cơ bản | 3 | draft_unverified |  | 10 |
| HUS | MAT3300 | Đại số đại cương | 4 | unknown |  | 10 |
| HUS | MAT3301 | Giải tích hàm | 3 | draft_unverified |  | 10 |
| HUS | MAT3302 | Toán rời rạc | 4 | draft_unverified |  | 10 |
| HUS | MAT3304 | Thực hành tính toán | 2 | draft_unverified |  | 11 |
| HUS | MAT3305 | Tôpô đại cương | 3 | draft_unverified |  | 11 |
| HUS | MAT3306 | Cơ sở hình học vi phân | 3 | unknown |  | 11 |
| HUS | MAT3307 | Lý thuyết độ đo và tích phân | 3 | unknown |  | 11 |
| HUS | MAT3310 | Cơ sở tôpô đại số | 3 | draft_unverified |  | 11 |
| HUS | MAT3311 | Lý thuyết nhóm và biểu diễn nhóm | 3 | draft_unverified |  | 11 |
| HUS | MAT3313 | Lý thuyết số | 3 | unknown |  | 11 |
| HUS | MAT3317 | Phương trình đạo hàm riêng 2 | 3 | unknown |  | 11 |
| HUS | MAT3318 | Giải tích trên đa tạp | 3 | draft_unverified |  | 11 |
| HUS | MAT3321 | Quá trình ngẫu nhiên | 3 | draft_unverified |  | 12 |
| HUS | MAT3322 | Xác suất 2 | 3 | draft_unverified |  | 12 |
| HUS | MAT3323 | Tối ưu rời rạc | 3 | draft_unverified | MAT3500 | 12 |
| HUS | MAT3324 | Tổ hợp | 3 | draft_unverified |  | 12 |
| HUS | MAT3325 | Lịch sử toán học | 3 | unknown |  | 12 |
| HUS | MAT3326 | Xêmina Toán lý thuyết | 3 | draft_unverified |  | 12 |
| HUS | MAT3327 | Điều khiển tối ưu | 3 | unknown |  | 12 |
| HUS | MAT3329 | Giải tích số 2 | 3 | draft_unverified |  | 12 |
| HUS | MAT3333 | Các mô hình toán ứng dụng 1 | 3 | draft_unverified | MAT2405 | 12 |
| HUS | MAT3334 | Các mô hình toán ứng dụng 2 | 3 | draft_unverified | MAT2406 | 13 |
| HUS | MAT3335 | Đại số máy tính | 3 | draft_unverified |  | 13 |
| HUS | MAT3337 | Xêmina Toán ứng dụng | 3 | draft_unverified |  | 13 |
| HUS | MAT3339 | Đại số tuyến tính 3 | 3 | unknown |  | 11 |
| HUS | MAT3344 | Giải tích phức | 4 | unknown |  | 11 |
| HUS | MAT3345 | Lý thuyết ổn định của phương trình vi phân | 3 | draft_unverified |  | 11 |
| HUS | MAT3347 | Lý thuyết Galois | 4 | draft_unverified |  | 11 |
| HUS | MAT3359 | Thực tập chuyên ngành | 3 | unknown |  | 11 |
| HUS | MAT3360 | Tối ưu hóa nâng cao | 3 | draft_unverified |  | 12 |
| HUS | MAT3361 | Cơ học lý thuyết nâng cao | 3 | draft_unverified |  | 13 |
| HUS | MAT3362 | Một số vấn đề chọn lọc trong Cơ học | 3 | draft_unverified |  | 14 |
| HUS | MAT3370 | Thống kê Bayes | 3 | draft_unverified | MAT2405 | 12 |
| HUS | MAT3396 | Sức bền vật liệu | 3 | draft_unverified |  | 13 |
| HUS | MAT3401 | Phép tính biến phân | 3 | draft_unverified |  | 13 |
| HUS | MAT3406 | Lý thuyết dao động | 3 | draft_unverified |  | 13 |
| HUS | MAT3407 | Lý thuyết đàn hồi | 3 | draft_unverified |  | 13 |
| HUS | MAT3408 | Cơ học chất lỏng | 3 | draft_unverified |  | 13 |
| HUS | MAT3411 | Phương pháp phần tử hữu hạn | 3 | draft_unverified |  | 14 |
| HUS | MAT3412 | Lý thuyết dẻo | 3 | draft_unverified |  | 14 |
| HUS | MAT3413 | Cơ học giải tích | 3 | draft_unverified |  | 14 |
| HUS | MAT3415 | Cơ học vật liệu composite | 3 | draft_unverified |  | 14 |
| HUS | MAT3418 | Phương pháp số trong cơ học | 3 | draft_unverified |  | 14 |
| HUS | MAT3422 | Lý thuyết bản và vỏ mỏng | 4 | draft_unverified |  | 14 |
| HUS | MAT3423 | Cơ học môi trường liên tục | 3 | unknown |  | 13 |
| HUS | MAT3452 | Phân tích thống kê nhiều chiều | 3 | draft_unverified | MAT2323,MAT2406 | 12 |
| HUS | MAT3539 | Mật mã và an toàn dữ liệu | 3 | draft_unverified | MAT2400 | 13 |
| HUS | MAT4070 | Khóa luận tốt nghiệp | 7 | draft_unverified |  | 14 |
| HUS | MAT4071 | Một số vấn đề chọn lọc trong Toán học | 3 | draft_unverified |  | 14 |
| HUS | MAT4072 | Một số vấn đề chọn lọc trong tính toán khoa học | 4 | draft_unverified | MAT2404 | 14 |
| HUS | PEC1008 | Kinh tế chính trị Mác - Lênin | 2 | draft_unverified |  | 8 |
| HUS | PES1000 | Giáo dục thể chất | 4 | draft_unverified |  | 9 |
| HUS | PHI1002 | Chủ nghĩa xã hội khoa học | 2 | draft_unverified |  | 8 |
| HUS | PHI1006 | Triết học Mác - Lênin | 3 | draft_unverified |  | 8 |
| HUS | POL1001 | Tư tưởng Hồ Chí Minh | 2 | draft_unverified |  | 8 |
| HUS | THL1057 | Nhà nước và pháp luật đại cương | 2 | draft_unverified |  | 8 |
| HUS | CME1000 | Giáo dục quốc phòng - an ninh | 8 | draft_unverified |  | 9 |
| HUS | FLF1107 | Tiếng Anh B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1207 | Tiếng Nga B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1307 | Tiếng Pháp B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1407 | Tiếng Trung Quốc B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1507 | Tiếng Đức B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1607 | Tiếng Nhật Bản B1 | 5 | draft_unverified |  | 8 |
| HUS | FLF1707 | Tiếng Hàn Quốc B1 | 5 | draft_unverified |  | 8 |
| HUS | HIS1001 | Lịch sử Đảng Cộng sản Việt Nam | 2 | draft_unverified |  | 8 |
| HUS | HIS1056 | Cơ sở văn hóa Việt Nam | 3 | draft_unverified |  | 9 |
| HUS | HUS1011 | Tin học cơ sở | 3 | draft_unverified |  | 8 |
| HUS | HUS1012 | Kỹ năng bổ trợ | 3 | draft_unverified |  | 9 |
| HUS | HUS1021 | Khoa học Trái Đất và sự sống | 3 | draft_unverified |  | 9 |
| HUS | HUS1022 | Nhập môn Internet kết nối vạn vật | 2 | draft_unverified |  | 9 |
| HUS | HUS1023 | Nhập môn phân tích dữ liệu | 2 | draft_unverified |  | 9 |
| HUS | HUS1024 | Nhập môn Robotic | 3 | draft_unverified |  | 9 |
| HUS | MAT1201 | Phương pháp nghiên cứu khoa học | 3 | draft_unverified |  | 10 |
| HUS | MAT1202 | Lập trình hướng đối tượng | 3 | draft_unverified |  | 10 |
| HUS | MAT2300 | Đại số tuyến tính 1 | 4 | draft_unverified |  | 9 |
| HUS | MAT2301 | Đại số tuyến tính 2 | 4 | draft_unverified |  | 9 |
| HUS | MAT2302 | Giải tích 1 | 5 | draft_unverified |  | 9 |
| HUS | MAT2303 | Giải tích 2 | 5 | draft_unverified |  | 9 |
| HUS | MAT2304 | Giải tích 3 | 4 | draft_unverified |  | 9 |
| HUS | MAT2314 | Phương trình vi phân | 4 | unknown |  | 9 |
| HUS | MAT2404 | Giải tích số | 4 | draft_unverified |  | 10 |
| HUS | MAT2405 | Xác suất | 3 | draft_unverified |  | 10 |
| HUS | MAT2406 | Thống kê ứng dụng | 4 | draft_unverified |  | 10 |
| HUS | MAT2407 | Tối ưu hóa | 3 | unknown |  | 10 |
| HUS | MAT2505 | Lập trình cơ bản | 3 | draft_unverified |  | 9 |
| HUS | MAT3148 | Tính toán song song | 3 | draft_unverified |  | 12 |
| HUS | MAT3323 | Tối ưu rời rạc | 3 | draft_unverified | MAT3302 | 11 |
| HUS | MAT3327 | Điều khiển tối ưu | 3 | unknown |  | 12 |
| HUS | MAT3333 | Các mô hình toán ứng dụng 1 | 3 | draft_unverified | MAT2308 | 12 |
| HUS | MAT3334 | Các mô hình toán ứng dụng 2 | 3 | draft_unverified | MAT2311 | 12 |
| HUS | MAT3335 | Đại số máy tính | 3 | draft_unverified | MAT2316,MAT2318,MAT2319 | 11 |
| HUS | MAT3359 | Thực tập chuyên ngành | 3 | unknown |  | 10 |
| HUS | MAT3365 | Phương trình đạo hàm riêng | 3 | draft_unverified |  | 10 |
| HUS | MAT3366 | Hệ máy tính | 3 | draft_unverified |  | 10 |
| HUS | MAT3367 | Đại số ứng dụng | 3 | draft_unverified |  | 11 |
| HUS | MAT3368 | Thuật toán ngẫu nhiên | 3 | draft_unverified |  | 11 |
| HUS | MAT3369 | Giải tích số nâng cao | 3 | draft_unverified |  | 12 |
| HUS | MAT3370 | Thống kê Bayes | 3 | draft_unverified | MAT2308 | 12 |
| HUS | MAT3371 | Xây dựng phần mềm | 3 | draft_unverified |  | 12 |
| HUS | MAT3409 | Giải tích hàm ứng dụng | 3 | draft_unverified |  | 9 |
| HUS | MAT3452 | Phân tích thống kê nhiều chiều | 3 | draft_unverified | MAT2311,MAT2323 | 10 |
| HUS | MAT3456 | Logic ứng dụng | 3 | draft_unverified |  | 11 |
| HUS | MAT3500 | Toán rời rạc | 4 | draft_unverified |  | 10 |
| HUS | MAT3504 | Thiết kế và đánh giá thuật toán | 3 | draft_unverified |  | 10 |
| HUS | MAT3507 | Cơ sở dữ liệu | 4 | draft_unverified |  | 10 |
| HUS | MAT3508 | Nhập môn trí tuệ nhân tạo | 3 | draft_unverified |  | 11 |
| HUS | MAT3509 | Ngôn ngữ hình thức và ôtômat | 3 | draft_unverified |  | 11 |
| HUS | MAT3514 | Cấu trúc dữ liệu và thuật toán | 4 | draft_unverified |  | 10 |
| HUS | MAT3525 | Thực hành tính toán | 2 | draft_unverified |  | 10 |
| HUS | MAT3531 | Tính toán phân tán | 3 | draft_unverified |  | 11 |
| HUS | MAT3533 | Học máy | 3 | draft_unverified | MAT2323 | 10 |
| HUS | MAT3539 | Mật mã và an toàn dữ liệu | 3 | draft_unverified | MAT2316,MAT2318,MAT2319,MAT2400 | 11 |
| HUS | MAT3545 | Lý thuyết tính toán | 3 | draft_unverified |  | 11 |
| HUS | MAT3561 | Xử lí ngôn ngữ tự nhiên và ứng dụng | 3 | draft_unverified |  | 12 |
| HUS | MAT3562 | Thị giác máy tính | 3 | draft_unverified |  | 12 |
| HUS | MAT3565 | Nhập môn khai phá các tập dữ liệu lớn | 3 | draft_unverified |  | 12 |
| HUS | MAT4072 | Một số vấn đề chọn lọc trong tính toán khoa học | 4 | draft_unverified | MAT2307 | 12 |
| HUS | MAT4082 | Khóa luận tốt nghiệp | 7 | draft_unverified |  | 12 |
| HUS | PEC1008 | Kinh tế chính trị Mác - Lênin | 2 | draft_unverified |  | 8 |
| HUS | PES1000 | Giáo dục thể chất | 4 | draft_unverified |  | 9 |
| HUS | PHI1002 | Chủ nghĩa xã hội khoa học | 2 | draft_unverified |  | 8 |
| HUS | PHI1006 | Triết học Mác - Lênin | 3 | draft_unverified |  | 8 |
| HUS | POL1001 | Tư tưởng Hồ Chí Minh | 2 | draft_unverified |  | 8 |
| HUS | THL1057 | Nhà nước và pháp luật đại cương | 2 | draft_unverified |  | 8 |
| SAMPLE | PHI1006 | Triết học Mác - Lênin | 3 | draft_unverified |  | 9 |
| SAMPLE | PEC1008 | Kinh tế chính trị Mác - Lênin | 2 | draft_unverified |  | 9 |
| SAMPLE | PHI1002 | Chủ nghĩa xã hội khoa học | 2 | draft_unverified |  | 9 |
| SAMPLE | HIS1001 | Lịch sử Đảng Cộng sản Việt Nam | 2 | draft_unverified |  | 9 |
| SAMPLE | POL1001 | Tư tưởng Hồ Chí Minh | 2 | draft_unverified |  | 9 |
| SAMPLE | THL1057 | Nhà nước và pháp luật đại cương | 2 | draft_unverified |  | 9 |
| SAMPLE | HUS1011 | Tin học cơ sở | 3 | draft_unverified |  | 9 |
| SAMPLE | FLF1107 | Tiếng Anh B1 | 5 | draft_unverified |  | 9 |
| SAMPLE | FLF1207 | Tiếng Nga B1 | 5 | draft_unverified |  | 9 |
| SAMPLE | FLF1307 | Tiếng Pháp B1 | 5 | draft_unverified |  | 9 |
| SAMPLE | FLF1407 | Tiếng Trung Quốc B1 | 5 | draft_unverified |  | 9 |
| SAMPLE | FLF1507 | Tiếng Đức B1 | 5 | draft_unverified |  | 9 |
| SAMPLE | FLF1607 | Tiếng Nhật Bản B1 | 5 | draft_unverified |  | 9 |
| SAMPLE | FLF1707 | Tiếng Hàn Quốc B1 | 5 | draft_unverified |  | 9 |
| SAMPLE | CME1000 | Giáo dục quốc phòng-an ninh | 8 | draft_unverified |  | 9 |
| SAMPLE | PES1000 | Giáo dục thể chất | 4 | draft_unverified |  | 9 |
| SAMPLE | HUS1012 | Kỹ năng bổ trợ | 3 | draft_unverified |  | 9 |
| SAMPLE | HUS1021 | Khoa học Trái Đất và sự sống | 3 | draft_unverified |  | 10 |
| SAMPLE | HUS1022 | Nhập môn Internet kết nối vạn vật | 2 | draft_unverified |  | 10 |
| SAMPLE | HUS1023 | Nhập môn phân tích dữ liệu | 2 | draft_unverified |  | 10 |
| SAMPLE | HUS1024 | Nhập môn Robotic | 3 | draft_unverified |  | 10 |
| SAMPLE | HIS1056 | Cơ sở văn hóa Việt Nam | 3 | draft_unverified |  | 10 |
| SAMPLE | MAT2505 | Lập trình cơ bản | 3 | draft_unverified |  | 10 |
| SAMPLE | MAT2400 | Đại số tuyến tính | 5 | draft_unverified |  | 10 |
| SAMPLE | MAT2501 | Giải tích 1 | 4 | draft_unverified |  | 10 |
| SAMPLE | MAT2502 | Giải tích 2 | 4 | draft_unverified |  | 10 |
| SAMPLE | MAT2503 | Giải tích 3 | 2 | draft_unverified |  | 10 |
| SAMPLE | MAT2403 | Phương trình vi phân | 3 | draft_unverified |  | 10 |
| SAMPLE | MAT2323 | Xác suất - Thống kê | 4 | draft_unverified |  | 10 |
| SAMPLE | MAT2407 | Tối ưu hóa | 3 | unresolved_external | MAT2301,MAT2303,MAT2321 | 10 |
| SAMPLE | MAT1204 | Phương pháp nghiên cứu khoa học | 3 | draft_unverified |  | 10 |
| SAMPLE | MAT2034 | Giải tích số | 3 | draft_unverified |  | 10 |
| SAMPLE | MAT3500 | Toán rời rạc | 4 | draft_unverified |  | 11 |
| SAMPLE | MAT3557 | Môi trường lập trình Linux | 2 | draft_unverified |  | 11 |
| SAMPLE | MAT1202 | Lập trình hướng đối tượng | 3 | draft_unverified |  | 11 |
| SAMPLE | MAT3514 | Cấu trúc dữ liệu và thuật toán | 4 | draft_unverified |  | 11 |
| SAMPLE | MAT3507 | Cơ sở dữ liệu | 4 | draft_unverified |  | 11 |
| SAMPLE | MAT3378 | Quản trị dữ liệu lớn | 3 | draft_unverified |  | 11 |
| SAMPLE | MAT3148 | Tính toán song song | 3 | draft_unverified |  | 11 |
| SAMPLE | MAT3379 | Phân tích hồi quy và ứng dụng | 3 | draft_unverified |  | 11 |
| SAMPLE | MAT3533 | Học máy | 3 | unresolved_external | MAT2406 | 11 |
| SAMPLE | MAT3381 | Thực tập thực tế về Khoa học dữ liệu | 3 | draft_unverified |  | 11 |
| SAMPLE | MAT3382 | Lập trình cho Khoa học dữ liệu | 2 | draft_unverified |  | 11 |
| SAMPLE | MAT3383 | Trực quan hóa thông tin | 2 | draft_unverified |  | 11 |
| SAMPLE | MAT1209 | Tự động hóa | 2 | draft_unverified |  | 11 |
| SAMPLE | MAT3385 | Cơ sở dữ liệu Web và hệ thống thông tin | 3 | draft_unverified |  | 11 |
| SAMPLE | MAT3504 | Thiết kế và đánh giá thuật toán | 3 | draft_unverified |  | 11 |
| SAMPLE | MAT3508 | Nhập môn trí tuệ nhân tạo | 3 | draft_unverified |  | 11 |
| SAMPLE | MAT3534 | Khai phá dữ liệu | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3386 | Phương pháp tính toán trong thống kê và khoa học dữ liệu | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3387 | Kĩ thuật lấy mẫu khảo sát | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3388 | Phân tích chuỗi thời gian | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3389 | Quy hoạch thực nghiệm | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3390 | Nhập môn Tin sinh học | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3391 | Hệ thống thông tin địa lí | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3392 | Ứng dụng dữ liệu lớn trong quản lí rủi ro tai biến thiên nhiên | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3393 | Khai thác dữ liệu trong Hóa học | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3394 | Mô hình toán sinh thái | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3562 | Thị giác máy tính | 3 | unresolved_external | MAT2301 | 12 |
| SAMPLE | MAT3395 | Lí thuyết trò chơi | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3535 | Tìm kiếm thông tin | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT3399 | Xử lí ngôn ngữ tự nhiên và học sâu | 3 | draft_unverified |  | 12 |
| SAMPLE | MAT4083 | Khóa luận tốt nghiệp | 7 | draft_unverified |  | 13 |
| SAMPLE | MAT3397 | Một số vấn đề ứng dụng của khoa học dữ liệu | 4 | draft_unverified |  | 13 |
| SAMPLE | MAT3398 | Một số chủ đề trong mô hình hóa và phân tích dữ liệu | 3 | draft_unverified |  | 13 |

## Danh s?ch ti?n quy?t unknown theo ng?nh

- khdl_7460108_2022: MAT2407 (Tối ưu hóa).
- khmtt_7480113qtd_2022: MAT2407 (Tối ưu hóa).
- toan_hoc_7460101_2022: MAT2308 (Xác suất 1), MAT2310 (Hình học giải tích), MAT2314 (Phương trình vi phân), MAT2407 (Tối ưu hóa), MAT3300 (Đại số đại cương), MAT3306 (Cơ sở hình học vi phân), MAT3307 (Lý thuyết độ đo và tích phân), MAT3313 (Lý thuyết số), MAT3317 (Phương trình đạo hàm riêng 2), MAT3325 (Lịch sử toán học), MAT3327 (Điều khiển tối ưu), MAT3339 (Đại số tuyến tính 3), MAT3344 (Giải tích phức), MAT3359 (Thực tập chuyên ngành), MAT3423 (Cơ học môi trường liên tục).
- toan_tin_7460117_2022: MAT2314 (Phương trình vi phân), MAT2407 (Tối ưu hóa), MAT3327 (Điều khiển tối ưu), MAT3359 (Thực tập chuyên ngành).

## Gi?i h?n th?m ??nh

Kh?ng t?m ki?m ngu?n h?c v? tr?n web trong ??t r? n?i b? n?y. T?n ch? kh?p gi?a courses v? 297 source occurrences, nh?ng c? hai c? th? c?ng k? th?a sai s?t phi?n ?m. C?n PDF g?c ?? k?t lu?n ??ng v? h?c thu?t. Kh?c tr?ng th?i external gi?a b? m?u v? HUS ch?a ch?ng minh l?i m? kh?a; danh s?ch external v?n ???c gi?. Kh?ng t? s?a d? li?u ho?c code trong ??t audit.
