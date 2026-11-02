# Mở demo hỏi đáp RAG trên máy hiện tại

Sau lần hợp nhất main để xử lý PR #6, lệnh mở và phạm vi demo vẫn như dưới đây.
Môi trường mới nên cài `requirements-dev.txt` với constraint `requirements-lock.txt`
và chạy `python -m playwright install chromium` trước khi mở demo.

Demo độc lập dùng `app.hus.demo:app`, giao diện hỏi đáp riêng và dữ liệu HUS thật.
Phạm vi gồm **F1/F2/F3 và trò chuyện cơ bản**. Ứng dụng chạy trên loopback, không cần
đăng nhập, tài khoản/ngữ cảnh giả lập, catalog, bảng điểm, database hoặc model provider.

Từ thư mục repository, mở PowerShell và chạy:

```powershell
Set-Location C:\Users\dtai168\SE_Project
& .\backups\hus_integration\p05-ci-venv\Scripts\python.exe -X utf8 -m tools.run_hus_rag_demo
```

Đường dẫn interpreter trên dùng môi trường local đã có Playwright/Chromium. Nếu dùng
môi trường khác đã đủ dependency, có thể chạy `python -m tools.run_hus_rag_demo`.
Lệnh cũ qua `backups/hus_integration/open_hus_rag_demo.py` vẫn hoạt động vì file đó
hiện chuyển tiếp tới cùng launcher mới.

Chromium tự mở trang **Hỏi đáp HUS**. Chọn trực tiếp một trong bốn ngành ở **Ngành
đang tra cứu**; **Phiên bản dữ liệu** hiển thị phiên bản có trong gói. Mặc định là
Khoa học dữ liệu. Nhập vào **Câu hỏi của bạn**, bấm **Gửi** hoặc nhấn Enter;
Shift+Enter xuống dòng.

| Thử | Câu hỏi / kỳ vọng |
| --- | --- |
| Trò chuyện cơ bản | “Xin chào”, “Cảm ơn”, “Bạn giúp được gì?”, “Tạm biệt” — có lời đáp riêng, không tạo dẫn chứng |
| F1 | “Giới thiệu ngành” — thông tin ngành hiện chọn kèm dẫn chứng |
| F2, ngành Khoa học dữ liệu | “MAT3533 có bao nhiêu tín chỉ?” — 3 tín chỉ, giữ trạng thái nguồn và link PDF |
| F3, ngành Khoa học dữ liệu | Tích **Cho phép kiến thức AI tham khảo**, hỏi “Nội dung MAT3533?” — hiện **kiến thức AI**, không gắn link PDF cho nội dung AI |
| Thiếu bằng chứng | “MAT3533 thi cuối kỳ bao nhiêu phần trăm?” — `no_information`, không đoán dữ kiện |
| Ngoài phạm vi F1/F2/F3 | Thông báo chưa có thông tin phù hợp, không tạo dữ kiện hay nguồn dẫn |

Chỉ tra cứu các phiên bản có trong dữ liệu; ngày crawl hoặc tệp PDF không tự chứng
nhận hiệu lực hiện hành. F3 là tham khảo AI sinh, không phải đề cương hay quy định
đánh giá chính thức. Đổi ngành sẽ xóa hội thoại, tắt lại lựa chọn AI và bỏ câu trả lời
đến muộn của ngành cũ. Hội thoại chỉ nằm trong bộ nhớ tab.

Giữ terminal đang chạy. Đóng tab hoặc nhấn **Ctrl+C** để dừng; nếu đang mở demo cũ,
dừng rồi chạy lại lệnh trên. Mỗi lần chạy dùng URL/cổng riêng, không dùng lại URL cũ
và không cần tự mở file HTML.

Thêm `--smoke` vào lệnh launcher để kiểm thử headless rồi thoát. Lần kiểm tra mới đã
đạt **50 câu hỏi trình duyệt trên bốn ngành**, kiểm thêm đổi ngành khi chờ phản hồi,
reset hội thoại/AI và giữ hai dẫn chứng cùng PDF ở trang **13/12**. Xem
[receipt đúng phạm vi](acceptance/hus_rag_scope_report.json) để biết snapshot và kết
quả kiểm thử cuối. [Receipt 48 ca cũ](acceptance/hus_manual_demo_report.json) chỉ ghi
nhận launcher dùng harness P0-5 trước thay đổi này.

Các snapshot, bundle và receipt **P0-4/P0-5 giữ nguyên**. Demo độc lập này không phải
nghiệm thu tích hợp production; bước đó cần endpoint RAG đúng phạm vi, giữ đầy đủ
auth/CSRF/Origin, binding ngành, kiểm revision trước/sau xử lý và receipt mới.
