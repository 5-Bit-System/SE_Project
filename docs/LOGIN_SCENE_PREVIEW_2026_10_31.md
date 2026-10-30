# Bản thử nền login — 31/10/2026

Xem tại `http://127.0.0.1:8000/?preview=study-login` khi chưa đăng nhập.
Đây là bản local để người dùng duyệt; chưa bật mặc định và chưa publish.
URL không có tham số này tiếp tục dùng màn hình đăng nhập hiện có.

## Thiết kế

Kết hợp ba lựa chọn đã được yêu cầu: trang ghi chú nổi, bản đồ môn học và góc
bàn học. Sách, sổ mở, bút và thước tạo thành chân cảnh; hai trang ghi chú nối
với các nhánh nhỏ phía trên. Không có điểm, thông tin sinh viên hoặc học phần thật.

Giữ Be Vietnam Pro và nền hiện có. Bảng màu sáng gồm trắng giấy `#FFFDF8`, nét
lavender `#9C8AB2`, bìa sách `#B5A1D3`, bìa nhạt `#D0C1E3` và tím `#8060B9`.
Chế độ tối dùng cùng hình dạng với bảng màu dịu hơn. Cảnh nằm dưới lời giới
thiệu trên desktop, chuyển xuống dưới form ở màn hình rộng tối đa 850px.

Các trang dao động tối đa 7px trong 18–22 giây; một nét sáng đi dọc nhánh trong
20 giây, bookmark xoay nhẹ. Cảnh dừng khi ra ngoài vùng nhìn hoặc tab bị ẩn;
chế độ giảm chuyển động dùng hình tĩnh. Hình trang trí không nhận focus hoặc
chuột, không có nội dung dành cho trình đọc màn hình.

SVG, CSS và script nằm trong repository, không cần thư viện hoặc ảnh ngoài.
Script chỉ bật bản thử từ URL và bố trí/dừng cảnh; không đọc account, lưu trạng
thái hay gửi request. Form VNU/admin và hành vi khôi phục phiên được giữ nguyên.

## Kiểm chứng local

- Chrome tổng hợp qua sáu chiều rộng: 1920, 1440, 1024, 850, 390 và 320px.
- Sáng/tối, VI/EN, chuyển tab sinh viên/admin, không tràn ngang/đè form.
- Đo thay đổi transform để xác nhận chuyển động; giảm chuyển động dùng hình tĩnh.
- Cảnh ẩn ở URL thường và khi vào workspace. Không có page error/request ngoài.
- `check_session_restore` passed; JavaScript syntax và whitespace passed.
- Ảnh desktop/mobile sáng/tối được xem để chỉnh bố cục.

Script QA, ảnh và `verification.json` được Git bỏ qua tại
`backups/login_scene_preview_20261031/`. Đây là kiểm tra với phiên giả lập,
không đăng nhập VNU thật hay đọc dữ liệu cá nhân. Chờ người dùng duyệt trước
khi bật mặc định hoặc mở rộng sang các màn hình khác.
