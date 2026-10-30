# Reflection — VT-098

Bản reflection do AI hỗ trợ soạn từ evidence của phiên cá nhân này. Nội dung
không xác nhận sinh viên đã tự chạy test hoặc review độc lập; sinh viên cần đọc
và xác nhận nội dung trước khi nộp. Số từ được tính trên phần giữa hai marker,
theo các token phân cách bằng khoảng trắng.

<!-- reflection:start -->
Confidence của bài tăng khi kết quả được kiểm tra bằng dữ liệu bền vững, thay vì chỉ nhìn mã 201. Hai test AI ban đầu vẫn xanh dù mỗi lần retry sinh ID khác. Việc sửa chúng để so sánh toàn bộ response và đếm plan, audit, receipt bằng connection độc lập giúp oracle sát invariant hơn. Test biên 64 ký tự còn phát hiện mutant > thành >=. Chuỗi red, patch, green giữ nguyên test bytes làm lập luận đáng tin hơn nhận xét rằng code có vẻ đúng.

Tuy nhiên, confidence chỉ áp dụng cho slice SQLite dùng bản nháp rỗng. Coverage cao không chứng minh auth, CSRF, eligibility hoặc khóa PostgreSQL đúng. Sáu lần đổi clock và thứ tự chạy chưa loại trừ mọi flaky test. Chín burst có p95 dưới 4,0 giây chỉ đo hàm cục bộ, không có mạng hay người dùng HTTP thật. Việc công bố peak thực tế 149–150, giữ mọi sample và ghi rõ guard schema chưa được test giúp tránh biến evidence giới hạn thành lời khẳng định quá mức.

Test tiếp theo có giá trị cao nhất là integration/API trên PostgreSQL tạm với hai worker và tài khoản tổng hợp. Cho request tạo commit nhưng làm mất phản hồi, rồi retry cùng key và body qua phiên hợp lệ. Oracle cần xác nhận cùng ID, version, response và đúng một plan, audit, receipt bằng connection độc lập; request vẫn phải qua kiểm tra quyền. Test này kiểm tra khoảng cách quan trọng nhất giữa harness và production: transaction, receipt, retry và middleware cùng hoạt động. Chỉ sau đó mới có cơ sở chạy lại tải 150 qua HTTP và đánh giá độ trễ đầu cuối.
<!-- reflection:end -->
