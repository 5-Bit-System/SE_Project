# Bản thử nền login — 31/10/2026

Nền minh họa được dùng chung cho trang đăng nhập và các mục trong workspace.
Tham số `?preview=study-login` tiếp tục bật riêng bố cục đăng nhập phóng lớn.

## Thiết kế

Nền cố định phủ toàn viewport, phía sau tiêu đề và form. Các nhánh môn học chạy
xuyên nền; ba trang ghi chú trôi ở các vùng mép, sách và bút ở góc dưới. Không
còn hình minh họa chen trong cột giới thiệu hoặc nằm dưới form. Không có điểm,
thông tin sinh viên hoặc học phần thật.

Giữ Be Vietnam Pro và nền hiện có. Bảng màu sáng gồm trắng giấy `#FFFDF8`, nét
lavender `#A08ABF`, bìa sách `#B5A1D3`, bìa nhạt `#D0C1E3` và tím `#9371CD`.
Chế độ tối dùng cùng hình dạng với bảng màu dịu hơn. Bố cục preview dùng chiều
cao viewport thực, header gọn hơn và form được căn trong phần còn lại. Footer
thông tin dự án được ẩn ở login preview; nội dung riêng tư về mật khẩu vẫn hiển thị.

Hai cột được gom trong container tối đa 1740px và căn giữa màn hình. Khung form
rộng tối đa 690px, tăng 1,5 lần; chữ giới thiệu, mô tả và các điều khiển form
cũng lớn hơn trên desktop. Tiêu đề đạt tối đa 75px trên màn hình rộng, tự thu
theo chiều rộng để cân dòng. Khoảng cách giữa hai cột vẫn là 32–64px. Cửa sổ
thấp dùng kích thước điều khiển gọn hơn để nút đăng nhập luôn trong màn hình;
mobile giữ bố cục một cột.

Các trang trôi 24px và nghiêng nhẹ trong 12–15 giây; hai vệt sáng chạy dọc nhánh
trong 8/11 giây, sách và bookmark chuyển động nhẹ. Cảnh dừng khi ẩn hoặc tab bị
ẩn; chế độ giảm chuyển động dùng hình tĩnh. Hình trang trí không nhận focus
hoặc chuột, không có nội dung dành cho trình đọc màn hình.

Mobile giữ tiêu đề ngắn và form ngay trong màn hình, thu gọn header thành một
hàng, dùng nút biểu tượng cho sáng/tối với tên truy cập. Màn hình thấp bỏ lời
giới thiệu trùng; điện thoại nằm ngang đặt hai ô nhập trên cùng hàng. Không dùng
overflow hidden để cắt nội dung form; thông báo phát sinh vẫn có thể mở rộng trang.

SVG, CSS và script nằm trong repository, không cần thư viện hoặc ảnh ngoài.
Script đưa nền ra ngoài luồng nội dung trên mọi trang và chỉ bật bố cục đăng nhập
phóng lớn khi URL có tham số preview; không đọc account, lưu trạng thái hay gửi
request. Nền nằm dưới nội dung và không nhận focus hoặc chuột. Hành vi gửi form
VNU/admin và khôi phục phiên được giữ nguyên.

## Kiểm chứng local trước khi dùng nền chung

- Chrome tổng hợp: 13 viewport, mỗi viewport kiểm tra VI/EN. Chiều rộng 320–1920px,
  gồm laptop 1366×768, 1280×720 và điện thoại nằm ngang 844×390.
- Kiểm tra cả scrollHeight và scrollWidth: màn hình VNU ban đầu không cần cuộn;
  nút đăng nhập nằm trong viewport. Nền fixed có kích thước đúng viewport.
- Sáng/tối, chuyển tab sinh viên/admin; ảnh desktop/mobile được xem trực tiếp.
- Đo cả transform trang giấy và strokeDashoffset vệt sáng sau 1,2 giây để xác
  nhận chuyển động thực; giảm chuyển động dùng hình tĩnh.
- Ở bản preview ban đầu, cảnh bị ẩn ở URL thường và trong workspace.
- `check_session_restore` passed; JavaScript syntax và whitespace passed.
- Ảnh desktop/mobile sáng/tối được xem để chỉnh bố cục.

Script QA, ảnh và `verification.json` được Git bỏ qua tại
`backups/login_background_v2_20261031/`. Bằng chứng bản cũ nằm riêng ở
`backups/login_scene_preview_20261031/`. Đây là kiểm tra với phiên giả lập,
không đăng nhập VNU thật hay đọc dữ liệu cá nhân. Theo yêu cầu tiếp theo, nền
đã được bật trên toàn ứng dụng; thay đổi phạm vi này chưa được chụp ảnh QA lại.

Lần cân bố cục hai cột có ảnh và QA riêng tại `backups/login_centered_20261031/`:
13 viewport/VI-EN tiếp tục qua kiểm tra; desktop đo thêm khoảng cách ngang
32–64px và tâm cụm nội dung trùng tâm viewport.
Tinh chỉnh cỡ chữ/form và nâng khối chữ có ảnh/QA riêng tại
`backups/login_scale_20261031/`; cùng 13 viewport/VI-EN tiếp tục qua kiểm tra.
