# Bản thử nền login — 31/10/2026

Xem tại `http://127.0.0.1:8000/?preview=study-login` khi chưa đăng nhập.
Đây là bản local để người dùng duyệt; chưa bật mặc định và chưa publish.
URL không có tham số này tiếp tục dùng màn hình đăng nhập hiện có.

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

Hai cột được gom trong container tối đa 1120px và căn giữa màn hình. Cột chữ
rộng tối đa 560px, form 440px, khoảng cách 32–64px theo chiều rộng. Tiêu đề
giảm còn tối đa 46px và cân dòng để cả cụm có trọng lượng thị giác đồng đều.

Các trang trôi 24px và nghiêng nhẹ trong 12–15 giây; hai vệt sáng chạy dọc nhánh
trong 8/11 giây, sách và bookmark chuyển động nhẹ. Cảnh dừng khi ẩn hoặc tab bị
ẩn; chế độ giảm chuyển động dùng hình tĩnh. Hình trang trí không nhận focus
hoặc chuột, không có nội dung dành cho trình đọc màn hình.

Mobile giữ tiêu đề ngắn và form ngay trong màn hình, thu gọn header thành một
hàng, dùng nút biểu tượng cho sáng/tối với tên truy cập. Màn hình thấp bỏ lời
giới thiệu trùng; điện thoại nằm ngang đặt hai ô nhập trên cùng hàng. Không dùng
overflow hidden để cắt nội dung form; thông báo phát sinh vẫn có thể mở rộng trang.

SVG, CSS và script nằm trong repository, không cần thư viện hoặc ảnh ngoài.
Script chỉ bật bản thử từ URL, đưa nền ra ngoài luồng nội dung và dừng cảnh khi
ẩn; không đọc account, lưu trạng thái hay gửi request. Hành vi gửi form VNU/admin
và khôi phục phiên được giữ nguyên.

## Kiểm chứng local

- Chrome tổng hợp: 13 viewport, mỗi viewport kiểm tra VI/EN. Chiều rộng 320–1920px,
  gồm laptop 1366×768, 1280×720 và điện thoại nằm ngang 844×390.
- Kiểm tra cả scrollHeight và scrollWidth: màn hình VNU ban đầu không cần cuộn;
  nút đăng nhập nằm trong viewport. Nền fixed có kích thước đúng viewport.
- Sáng/tối, chuyển tab sinh viên/admin; ảnh desktop/mobile được xem trực tiếp.
- Đo cả transform trang giấy và strokeDashoffset vệt sáng sau 1,2 giây để xác
  nhận chuyển động thực; giảm chuyển động dùng hình tĩnh.
- Cảnh ẩn ở URL thường và khi vào workspace. Không có page error/request ngoài.
- `check_session_restore` passed; JavaScript syntax và whitespace passed.
- Ảnh desktop/mobile sáng/tối được xem để chỉnh bố cục.

Script QA, ảnh và `verification.json` được Git bỏ qua tại
`backups/login_background_v2_20261031/`. Bằng chứng bản cũ nằm riêng ở
`backups/login_scene_preview_20261031/`. Đây là kiểm tra với phiên giả lập,
không đăng nhập VNU thật hay đọc dữ liệu cá nhân. Chờ người dùng duyệt trước
khi bật mặc định hoặc mở rộng sang các màn hình khác.

Lần cân bố cục hai cột có ảnh và QA riêng tại `backups/login_centered_20261031/`:
13 viewport/VI-EN tiếp tục qua kiểm tra; desktop đo thêm khoảng cách ngang
32–64px và tâm cụm nội dung trùng tâm viewport.
