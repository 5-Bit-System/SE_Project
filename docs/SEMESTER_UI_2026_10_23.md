# Giao diện Sổ học tập — 23/10/2026

## Điều chỉnh theo mẫu cổng đào tạo

Phần này thay thế thiết kế chọn học kỳ 1–12 bên dưới. Người dùng yêu cầu
bảng liên tục theo năm học/học kỳ thực tế, mới nhất trước. Bản xem trước
hiện có các cột STT, mã MH, môn học, số TC, điểm hệ 10, điểm chữ và điểm hệ 4;
dòng nhóm ghi học kỳ, năm học và mã kỳ từ nguồn. Không tạo sẵn 12 học kỳ.
Nhập tay cho phép tạo học kỳ theo năm bắt đầu và kỳ 1/2/hè, sắp mới nhất trước.

Nút “Mở bảng điểm mẫu” đọc JSON do người dùng chọn trực tiếp trong trình duyệt.
Tệp mẫu cá nhân được người dùng cho phép sử dụng nằm trong thư mục `backups/`
đã được Git bỏ qua; tên/MSSV không được chép vào mẫu. Không đưa điểm cá nhân
vào mã nguồn, fixtures, database hoặc tài liệu Git. Mở lại trang sẽ xóa bản
xem trước; có thể chọn lại tệp cục bộ.

Bản xem trước giữ từng lần học và điểm chữ/hệ 4 theo nguồn; không suy ra từ
quy tắc quy đổi điểm của demo, không đưa các mã chưa khớp vào eligibility.
Các thẻ KPI nhập tay được ẩn trong chế độ này để tránh hiển thị số liệu của
một bảng điểm khác. Luồng review/apply và kết nối portal vẫn chưa triển khai.

Kiểm tra Chrome qua DevTools: đọc tệp bằng input thật; nhóm/sắp học kỳ;
giữ điểm nguồn; giữ các lần học trùng mã; hiển thị nội dung như văn bản;
từ chối dữ liệu điểm lỗi và giữ bản xem trước đang có; nhập tay theo năm học;
đổi ngành xóa bảng điểm/nhóm kỳ/bản xem trước; mobile cuộn trong khung.
Không ghi nhận JavaScript exception. Ảnh đã xem và báo cáo mới nằm trong
`backups/semester_ui_20261023/portal-*`. Cửa sổ xem trực tiếp đã mở tại cổng 8000.
JavaScript syntax/diff checks đạt. Số 302 tests bên dưới thuộc lần kiểm tra
trước điều chỉnh này; không chạy lại nhóm Python cho thay đổi chỉ ở giao diện.

## Thiết kế và phạm vi

Áp dụng `.github/skills/frontend-design/SKILL.md` và các skill frontend-design,
webapp-testing được chọn qua `project-toolkit/SKILL.md`.
Giữ nền tảng FastAPI và HTML/CSS/JavaScript hiện có.

Bảng màu: nền #F3F5FA, giấy #FFFFFF, xanh chữ/điều hướng #243B67,
chữ phụ #56657B, thao tác #087B78, cảnh báo #8B5A15.
Chữ Be Vietnam Pro với Segoe UI dự phòng; nội dung căn trái.

```
Tên sản phẩm                 Ngành / ngôn ngữ / dữ liệu minh họa
Điều hướng | Giới thiệu và trạng thái nguồn
           | Tiến độ học tập
           | Học kỳ đang nhập
           | Bảng học kỳ 1
           | Bảng học kỳ 2
           | Thêm học phần (tìm kiếm và lọc, có thể thu gọn)
```

Điểm nhấn là sổ kết quả theo học kỳ; dùng bảng có tiêu đề cột thay cho các
hàng thẻ môn học. Thanh điều hướng xanh đậm giúp nhận biết vùng thao tác.
Logo hình sổ, tên trang và footer dùng “Sổ học tập”, bỏ nhãn AI-07 hiển thị.

## Hành vi

- Người dùng chọn học kỳ trước khi thêm môn, có thể chuyển kỳ hoặc xóa môn.
- Mỗi bảng có trạng thái đạt, mã/tên học phần, tín chỉ, điểm và học kỳ.
- Dữ liệu không có học kỳ thực tế nằm trong “Chưa xếp học kỳ”. Không suy ra
  học kỳ thực tế từ thứ tự môn, năm học hoặc học kỳ gợi ý của catalog.
- Học kỳ chỉ là thuộc tính trong state trình duyệt, không gửi vào hợp đồng
  transcript API và không lưu bền vững. Đổi ngành xóa bảng điểm và bộ lọc.
- Tìm kiếm/lọc chỉ áp dụng danh sách thêm môn, không che kết quả đã nhập.
- Các nút mẫu theo năm ẩn khi chương trình thiếu dữ liệu năm; phép lọc năm
  không còn coi null là năm 0.
- Trên điện thoại, bảng cuộn ngang trong khung; có focus và tiêu đề cột.

## Kiểm tra

Chrome headless qua DevTools Protocol (môi trường chưa có Playwright).
Kịch bản và ảnh ở `backups/semester_ui_20261023/` (được Git bỏ qua).
Đã kiểm tra hai nhóm học kỳ, nhập điểm 8.5 và 4, xóa điểm, chuyển kỳ,
xóa môn, tìm kiếm, đổi ngôn ngữ, cách ly dữ liệu khi đổi ngành, gợi ý môn
và mở/phóng to/đóng tư vấn. Bốn ngành nạp 65/67/90/68 môn.
Gợi ý trả về 5 môn; không có JavaScript exception.
Ảnh desktop 1440×1080 và mobile 390×844 đã được xem; không tràn ngang trang.
`node --check app/static/app.js` và `git diff --check` đạt.
Kiểm tra hồi quy với `tests -m "not postgres and not hus_postgres"
--full-catalog-root docs/acceptance/hus_2022`: **302 passed, 35 deselected**;
một cảnh báo Starlette/httpx đã tồn tại. Không chạy lại nhóm PostgreSQL.

Không kiểm tra hội thoại với nhà cung cấp LLM hoặc nhập dữ liệu portal.
