# Bản nháp reflection do AI hỗ trợ

Sinh viên cần tự đọc, sửa theo trải nghiệm của mình và xác nhận trước khi nộp.
Đoạn dưới là đề xuất diễn đạt, không phải bằng chứng sinh viên đã trực tiếp làm
hoặc review mọi thao tác của agent.

---

Điều làm tăng độ tin cậy của bài này là có bằng chứng nối từ yêu cầu đến kết quả
thực thi. Contract cũ trả mảng học phần được xác định từ API và cách client dùng
dữ liệu. Vì vậy, thêm endpoint tìm kiếm riêng giúp kiểm thử tính năng mới mà vẫn
giữ cách gọi cũ. Test được viết trước patch, chạy đỏ vì endpoint còn thiếu, rồi
chạy xanh sau khi bổ sung. Các mã môn kỳ vọng được xác định từ fixture tổng hợp,
không tính lại bằng chính hàm đang kiểm thử.

Thử nghiệm mutation cho thấy một lỗi có thể tạo cảm giác hệ thống vẫn hoạt động:
bắt exception rồi trả danh sách rỗng. Test phân biệt kết quả rỗng hợp lệ với lỗi
dependency bằng status và response contract. Điều này thuyết phục hơn việc chỉ
thấy nhiều test xanh. Việc phát hiện lỗi encoding, tên biến che module và giả
định PID trong harness cũng nhắc rằng code AI sinh cần được chạy và kiểm tra.

Tuy nhiên, coverage cao của service chưa chứng minh mọi điều kiện sản phẩm.
Benchmark dùng HTTP thật nhưng catalog tổng hợp và JSON repository; kết quả
không chứng nhận PostgreSQL production chịu cùng tải. Phân trang offset cũng
chưa bảo đảm nhất quán khi revision catalog đổi giữa các request. Ở cả hai cấu
hình thử, một lượt vượt ngưỡng p95; tôi chưa có cơ sở kết luận mục tiêu hiệu năng
đã đạt ổn định. Chưa có
bằng chứng rằng mọi nguồn học vụ đã được trường xác minh.

Test tiếp theo có giá trị cao nhất là chạy cùng contract và workload trên một
PostgreSQL dùng riêng cho test, đồng thời kiểm tra việc chuyển revision giữa
các trang. Tôi cần tự đọc diff, chạy lại các lệnh và giải thích các giới hạn
trước khi hoàn thiện bài nộp.
