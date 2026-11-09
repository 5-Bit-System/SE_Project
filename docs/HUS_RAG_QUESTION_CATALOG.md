# Danh mục câu hỏi trong demo RAG

Danh mục lấy từ release đang được demo nạp, chia theo ngành/phiên bản và có thể
bấm để gửi ngay qua luồng chat hiện có. Có tìm kiếm theo câu hỏi, tên hoặc mã môn,
không phân biệt hoa/thường và dấu tiếng Việt. Có thể tiếp tục tự nhập câu hỏi.

## Các nhóm và câu hỏi mẫu

| Nhóm | Câu hỏi hiển thị |
| --- | --- |
| F1 — Thông tin ngành | Giới thiệu ngành; Mục tiêu đào tạo của ngành là gì?; Cơ hội nghề nghiệp của ngành là gì?; Ngành có thể học tiếp như thế nào? |
| F2 — Chương trình và môn học | Thông tin học phần `{mã}`?; `{mã}` là môn gì?; `{mã}` có bao nhiêu tín chỉ?; Tiên quyết `{mã}`?; Số giờ học `{mã}`? |
| F3 — Tìm hiểu môn học, AI tham khảo | Nội dung `{mã}`?; Mục tiêu `{mã}`?; Gợi ý đánh giá `{mã}`? |
| Hướng dẫn | Bạn có thể làm gì?; Cách đọc nguồn?; Cách bật nội dung AI? |

Đây là các câu mẫu bao phủ trường dữ liệu được hỗ trợ, không phải mọi cách diễn
đạt tự nhiên. F1 chỉ liệt kê field có chunk trong selection đã duyệt, chia tiếp
theo phiên bản nguồn/hệ; `unknown` hiển thị là chưa rõ. Không gán phiên bản quyết
định F2/F3 cho nguồn F1 hoặc mặc nhiên xác nhận hiệu lực hiện tại.

F2/F3 chia tiếp theo từng môn trong đúng CTĐT. Chỉ gợi ý tín chỉ/thông tin tổng hợp
khi dòng nguồn có tín chỉ thống nhất; số giờ chỉ hiện khi có trường dữ liệu đó.
Tiên quyết trống được trả lời là nguồn không ghi, không suy ra được phép đăng ký.
Giữ trạng thái review dự án, mâu thuẫn và mã chưa giải quyết trong câu trả lời.

F3 chỉ dùng chunk generated thuộc membership đã chọn. Nút câu hỏi bị khóa khi
chưa tích **Cho phép kiến thức AI tham khảo**; bấm câu hỏi không tự cấp quyền.
Câu trả lời luôn giữ nhãn **kiến thức AI**, không phải đề cương/đánh giá chính thức.
Các candidate đề cương official chưa được đưa vào danh mục hoặc retrieval mặc định.

## Phạm vi hiện có

Release `hus-data-20261031-v3`, SHA-256
`27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`.

| Ngành | Phiên bản F2/F3 | Môn | Câu F1 | Câu F2 | Câu F3 | Hướng dẫn | Tổng |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Toán học | QD3565-2023 | 90 | 12 | 448 | 270 | 3 | 733 |
| Toán tin | QD3567-2023 | 68 | 7 | 338 | 204 | 3 | 552 |
| Khoa học máy tính và thông tin | QD3568-2023 | 67 | 17 | 333 | 201 | 3 | 554 |
| Khoa học dữ liệu | QD3569-2023 | 65 | 4 | 323 | 195 | 3 | 525 |
| Tổng membership/câu mẫu theo scope | | 290 | 40 | 1.442 | 870 | 12 | 2.364 |

Cùng mã môn trong hai CTĐT vẫn là hai membership riêng. Câu F1 lặp nội dung nhưng
khác phiên bản/hệ là lựa chọn nguồn khác nhau, không phải câu đánh giá độc lập.

## Sử dụng và kiểm chứng

Chạy `python -m tools.run_hus_rag_demo`, chọn ngành, mở mục rồi chọn câu hỏi.
Danh sách đầy đủ dạng JSON có tại
`GET /hus/questions?major=data_science&version=QD3569-2023` trên máy chủ demo.
Endpoint chỉ chấp nhận scope có thật; mỗi mục chứa request và cờ cần AI, không chứa
đáp án viết sẵn hoặc quyền opt-in. Bấm chọn gửi request tới `/hus/chat`; backend
vẫn kiểm bằng chứng, ngành/phiên bản/hệ/mã, review và consent. Khi đổi ngành, danh
mục/hội thoại được làm mới, AI tắt lại và phản hồi cũ bị bỏ qua.

Kiểm tra kỹ thuật mới: duyệt toàn bộ 2.364 mục qua API chat thật, kiểm nguồn và
consent; Chromium kiểm bấm câu hỏi, tìm kiếm không dấu, mobile/bàn phím, tải lại
khi lỗi và phản hồi muộn sau đổi ngành. Xem
[receipt danh mục](acceptance/hus_question_catalog_report.json) để biết phiên bản
và kết quả regression. Đây là kiểm tra chức năng của menu với request có field
đã chọn, không phải điểm Recall/holdout hoặc nghiệm thu mọi cách diễn đạt. Gate
sau retrieval đã được [sửa trên 20 ca dev đã xem](RAG_SUPPORT_GATE_FIX_2026_11_03.md);
kết quả này vẫn tách biệt với nghiệm thu chất lượng trên tập độc lập.

Thay đổi còn local trên `crawldata`; chưa xuất bản hoặc triển khai production.
