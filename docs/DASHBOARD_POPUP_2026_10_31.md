# Popup bảng điểm Dashboard — 31/10/2026

Chọn một điểm trên biểu đồ hệ 10 hoặc hệ 4 mở popup giữa màn hình, chỉ chứa
tiêu đề học kỳ, thông tin lựa chọn và bảng điểm của kỳ đó. Popup không chứa
biểu đồ; Dashboard giữ nguyên bố cục và vị trí cuộn phía sau nền tối.
Chọn điểm chữ hoặc chú giải vẫn mở các lượt học phù hợp với bộ lọc năm học.

## Thao tác

- Đóng bằng nút ×, phím Esc hoặc bấm vùng nền ngoài. Bấm trong popup không đóng.
- Tab/Shift+Tab giữ focus trong popup; đóng trả focus về điểm hoặc chú giải đã chọn.
- Khóa cuộn Dashboard khi popup mở; bảng dài cuộn bên trong, bảng rộng cuộn ngang.
- Hỗ trợ VI/EN và giao diện sáng/tối. Bảng giữ nguyên điểm nguồn và lượt chưa có điểm.
- Đóng popup, rời Dashboard hoặc mất/đổi nguồn sẽ xóa các hàng điểm và thông tin
  chi tiết khỏi DOM. Đăng xuất tiếp tục dùng luồng xóa nguồn hiện có.

Phần tổng hợp tín chỉ và trung bình hệ 10/4 đã được bỏ khỏi Dashboard theo yêu
cầu trước đó; thông tin tổng kết nguồn vẫn có trong Hồ sơ của tôi.

## Kiểm chứng

Hai script Chrome tổng hợp `check_analytics_drilldown` và `check_charts` passed;
Node analytics, JavaScript syntax, Ruff cho hai script và kiểm tra whitespace passed.
Kiểm tra gồm giữ vị trí cuộn khác 0, bố cục biểu đồ không đổi, bảng chỉ có đúng
kỳ được chọn, Esc/×/nền ngoài, focus, lọc điểm chữ/năm, bảng 40 lượt ở màn hình
390×400 và cuộn ngang. Ảnh sáng/tối và mobile đã được xem trực tiếp.

Lệnh chạy nằm trong [hướng dẫn frontend](../tests/frontend/README.md).
Ảnh tổng hợp được Git bỏ qua tại `backups/dashboard_popup_20261031/`.
Không dùng tài khoản VNU thật, không đọc điểm cá nhân, không đổi database/schema.
Đây là thay đổi local trên feature branch; chưa push hoặc mở/merge PR.
