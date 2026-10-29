# Nền và chuyển động Sổ học tập — 28/10/2026

## Yêu cầu hiện hành và nguyên nhân bản trước

Yêu cầu bổ sung của người dùng thay thế giới hạn trước về gradient/motion.
Giữ nguyên bố cục, nội dung và nghiệp vụ; ưu tiên nền chuyển động nhìn thấy được.
Lượt tinh chỉnh đầu **chưa triển khai** ambient background hoặc chart animation:
`themes.css` đặt nền đặc; không có lớp ánh sáng hoặc motion controller. CSS được
import và máy chủ phục vụ SHA-256 khớp workspace, asset URL gắn hash, HTML
`no-store`/CSS `no-cache`. Không có bằng chứng lỗi cache hay background bị che.

Kế hoạch đổi typography/Archivo ở lượt phản hồi trước chưa triển khai; yêu cầu
motion hiện tại thay thế kế hoạch đó. Giữ Be Vietnam Pro và hệ chữ đã có.

## Thiết kế trước khi triển khai

- Nền lavender gần trắng, ba radial gradient tím/cyan/hồng, chu kỳ 24/28/30s.
  Chỉ animate transform/opacity, khác pha và loop liền mạch. Một dot texture
  rất nhẹ, cố định. Lớp trang trí fixed, aria-hidden/inert, pointer-events none,
  ở sau nội dung, không ảnh hưởng layout hoặc chiều rộng trang.
- Sidebar/header dùng glass có chọn lọc: blur 10–12px, nền sáng/tối tương ứng;
  fallback nền đặc. Bảng/biểu đồ dùng surface gần opaque, không phủ kính đại trà.
- Entrance tối đa vài nhóm: 420ms, translateY 10px, stagger 60ms. Chuyển tab
  220ms; active cập nhật ngay. Navigation indicator chuyển theo nút hiện có.
- Nút hover/active 180–220ms; chỉ card chương trình thực sự là button mới nâng
  2px. Input đổi viền/focus không đổi kích thước. Dialog và accordion hiện có
  được mở/đóng nhẹ, bảo toàn Escape/focus.
- SVG line vẽ 700ms, credit bar scaleX 650ms, donut fade/scale 650ms. Không đổi
  giá trị/scale/công thức, không count-up điểm hoặc animate từng hàng bảng.
- Reduced motion dừng orb và mọi transform/stagger; nội dung luôn có trạng thái
  cuối mặc định. Mobile còn hai vùng sáng; dừng nền khi tab trình duyệt ẩn.

Tự kiểm tra: gradient chỉ ở lớp nền; glass không làm mờ chữ; animation có thể
quan sát được nhưng không làm control chậm phản hồi. Không dùng WebGL/video nền,
thư viện motion mới, mousemove loop hoặc will-change trên toàn bộ component.

## Kiểm chứng

Kiểm tra hoàn tất ngày **29/10/2026**, tiếp nối triển khai bắt đầu ngày 28/10.
Các hiệu ứng trên đã triển khai trong `app/static/motion.css` và `motion.js`,
được nạp trong layout đang dùng. `index.html` có revision
`20261028-ambient-motion`; URL CSS/JS do cơ chế hash hiện có tạo mới tự động.
`analytics.js` phát thông báo sau render cho controller motion, không đổi phép
tính. Dialog chi tiết hiện có dùng close animation 160ms, sau đó native close
khôi phục focus; reduced motion đóng ngay. Khi logout, xóa cache revision biểu
đồ trong RAM và hủy animation biểu đồ đang chạy. Entrance chung không bị hủy
bởi lần kiểm tra phiên 401 đầu tiên; trường hợp chưa đăng nhập này cũng đã được
kiểm tra riêng bằng Chrome.

### Kết quả thực chạy

- `tests/frontend/check_motion.py` đạt: quan sát **30,59 giây thực**, lấy mẫu
  transform/currentTime từng 5 giây; cả ba lớp hoàn thành ít nhất một chu kỳ.
  Kiểm tra background fixed tiếp tục che viewport khi cuộn, không tràn ngang.
- Có bản ghi Chrome **WebM**, gồm chu kỳ nền và thao tác điều hướng, nút,
  accordion, dialog, theme/mobile, reduced motion. Đã xem các ảnh ở những thời
  điểm khác nhau để xác nhận vùng sáng đổi vị trí; screenshot tĩnh không được
  dùng thay cho bằng chứng thời gian/animation. Bản ghi dài **40,84 giây**, đã
  mở giải mã trong Chrome và xem frame tại giây 8/23 để xác nhận video hợp lệ.
- Instrumentation trong test ghi nhận entrance 420ms/stagger 60ms, line 700ms,
  bar/donut 650ms; hover tooltip không replay, đổi lọc không replay page header.
  Nút active scale, hover shadow và indicator đến đúng mục được chọn đều đạt.
- Đo pixel background thực đã compositing ở **48 vùng/pha** (sáng/tối, 0/10/20/30s)
  cho chữ phụ/sidebar/header: tỷ lệ thấp nhất **4,7:1**. Đã làm đậm chữ phụ trên
  gradient và để màu chữ navigation cập nhật ngay khi đổi theme, giữ transition
  cho nền. Đây là kiểm tra mẫu, không phải chứng nhận WCAG toàn ứng dụng.
- Mobile 390px có hai vùng sáng, blur 8px; desktop có ba vùng, blur 10–12px.
  Reduced motion: không còn animation orb hoặc WAAPI entrance; dữ liệu hiện ngay.
  Chặn tải `motion.js` vẫn giữ nội dung hiển thị và điều hướng cũ hoạt động.
- Tám regression hiện có cũng đạt: presentation, workspace, charts, course_status,
  curriculum_reference, portal, portal_sync_feedback, vnu_only. Gồm 1440/1024/390,
  hai theme, VI/EN, nguồn dữ liệu, ngân sách/quota, focus/Escape và logout race.
- Node analytics aggregation, JS syntax, whole-repo Ruff và `git diff --check`
  đạt. Stack HTML/CSS/JS này không có build/typecheck frontend riêng.
- `/health`, `/ready`, `/static/motion.css`, `/static/motion.js` trả HTTP 200.
  Không restart server hoặc đổi chế độ Uvicorn; giữ no-reload trên Windows.

### Xem và chạy lại

Mở `http://127.0.0.1:8000/?ui=ambient-motion#dashboard`. Đợi 5–10 giây để thấy
vùng sáng dịch chuyển; một chu kỳ dài nhất là 30 giây. Thử chuyển bốn mục,
hover/nhấn nút, mở chi tiết môn hoặc dữ liệu biểu đồ. Cài đặt giảm chuyển động
của hệ điều hành/trình duyệt được tôn trọng, cho nền gradient tĩnh.

```text
.venv/Scripts/python.exe -m playwright install ffmpeg
.venv/Scripts/python.exe tests/frontend/check_motion.py
.venv/Scripts/python.exe tests/frontend/check_presentation.py
node tests/frontend/check_analytics.mjs
.venv/Scripts/python.exe -m ruff check .
```

Artifact chỉ lưu cục bộ, bị Git ignore:

```text
backups/frontend_motion_20261029/
  ambient-cycle-and-interactions.webm
  cycle-00s.png ... cycle-30s.png
  motion-light-1440.png / motion-dark-1440.png
  motion-light-1024.png / motion-dark-1024.png
  motion-light-390.png / motion-dark-390.png
  reduced-motion-390.png / scrolled-background.png
  verification.json / rendered-background-contrast.json
```

Fixture chỉ là bản ghi giả lập, mọi request VNU thật bị chặn. FFmpeg được dùng
bởi công cụ test để ghi video cục bộ, không phải dependency hoặc video nền của
sản phẩm. Không lưu mật khẩu/điểm thật vào ảnh, video, test hoặc repository.

### Giới hạn

Đã chạy Chrome; chưa benchmark FPS trên điện thoại yếu hoặc chạy Safari/Firefox.
Backdrop blur và accordion height dùng progressive enhancement với fallback
surface đặc/native details. Select/dropdown hệ điều hành vẫn là native control;
không thay bằng popover tự dựng. Không thực hiện đăng nhập VNU thật trong lượt
motion; backend/collector/API và quy tắc học vụ giữ nguyên. Ảnh/video kiểm chứng
chỉ giữ cục bộ; mã nguồn được quản lý trên nhánh `feat/vnu-curriculum-planning`.
