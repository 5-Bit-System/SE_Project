# Kế hoạch hoàn thiện dữ liệu HUS — 31/10/2026

Mục tiêu: bàn giao dữ liệu F1/F2/F3 có thể nạp ở bước truy xuất tiếp theo, với build
tái lập, nguồn gốc rõ, dữ kiện chưa biết được xử lý tường minh và kiểm chứng độc lập.
Người dùng cho phép thực hiện toàn bộ xử lý dữ liệu và bổ sung nội dung AI sinh.

1. Ghim đầu vào, làm việc trên feature branch riêng kế thừa crawldata; bảo toàn main,
   runtime, tài khoản, dữ liệu cá nhân và lịch sử tác giả.
2. Rà soát bản crawl, thử thu hồi nguồn ưu tiên theo robots/allowlist; đối chiếu PDF
   có sẵn và lập sổ theo dõi mọi nguồn thiếu, lỗi trích xuất và mâu thuẫn.
3. Đồng bộ F2 với main 94b7d05, giữ sign-off KHMTTT. Chuẩn hóa bản ghi truy vấn F2,
   tách trạng thái nguồn/từng dữ kiện khỏi quyền sử dụng và độ chắc chắn tiên quyết.
4. Rà soát văn bản F1/F3, chuẩn hóa bản hiển thị, giữ nguyên quote; bổ sung nội dung
   tham khảo hoặc metadata truy xuất khi thiếu. Không biến nội dung sinh thành quy định,
   đề cương, tín chỉ hoặc tiên quyết đã xác minh.
5. Tạo release độc lập, portable, có một schema chunks, F2 cấu trúc, nguồn/citation,
   phạm vi ngành/khóa/phiên bản, dữ liệu câu hỏi để nghiệm thu, báo cáo chất lượng và
   manifest. Dữ liệu lịch sử không được index lặp cùng release hiện tại.
6. Thực hiện review thứ hai bằng kiểm tra độc lập: coverage, key/join, quote/source-map,
   phạm vi, duplicate, stale, labels, Unicode, hash, tính tái lập và ca hỏng chủ động.
   Chạy suite phù hợp, viết báo cáo hoàn tất và hướng dẫn bước tiếp theo.

Nghiệm thu: không còn lỗi kỹ thuật mở trong release; đủ trường cần thiết cho bốn ngành;
mọi thông tin chính thức chưa xác minh phải có quyết định giữ unknown/khóa hoặc loại
khỏi tập trả lời chính thức. Một khoảng trống bằng chứng được giải quyết về mặt dữ liệu
bằng trạng thái có thể xử lý, không bằng cách giả xác nhận nguồn. Chỉ đánh dấu sẵn sàng
cho bước truy xuất mô tả/tham khảo, không tuyên bố HUS đã chứng nhận học vụ.

Phạm vi Git: feature branch local `feat/hus-data-ready-20261031`, chưa có yêu cầu
commit/push/PR/merge. Không triển khai chatbot, embedding trả phí hoặc đổi database.

Kết quả: cả sáu bước đã thực hiện. Release schema 2.0 có 1.271 chunks, 15 nguồn
khôi phục, 24 đoạn F1 đối chiếu, F2/sign-off hiện hành và 174 hồ sơ alias bổ sung.
Review độc lập gồm 581 test offline, 1.466 ca lookup, 24 ca âm, 5 ca quan trọng,
hash/PDF/quote checks, mutation tests và tái tạo byte-identical. Chi tiết và giới hạn
bằng chứng tại `HUS_DATA_HANDOFF_2026_10_31.md`.
