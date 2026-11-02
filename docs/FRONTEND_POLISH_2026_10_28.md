# Tinh chỉnh giao diện Sổ học tập — 28/10/2026

## Yêu cầu bổ sung sau bản đầu

Báo cáo bên dưới ghi lại lượt tinh chỉnh typography/màu sắc ban đầu. Người dùng
sau đó yêu cầu nền gradient chuyển động, glass và animation, thay thế giới hạn
motion trước đó. Kế hoạch đổi typography ở lượt giữa đã dừng; giữ Be Vietnam Pro.
Triển khai và kiểm chứng mới nhất được ghi tại
[FRONTEND_MOTION_2026_10_28.md](FRONTEND_MOTION_2026_10_28.md).

## Phạm vi và cấu trúc được giữ

Frontend là HTML/CSS/JavaScript do FastAPI phục vụ. Điều hướng hash và state
trong phiên dùng các event `workspace:*`; biểu đồ dùng SVG, không có thư viện
UI hoặc bước build frontend riêng. Bốn mục hiện có là Dashboard, Hồ sơ của tôi,
Điều kiện học và Gợi ý kỳ tới. Điều kiện học có hai chế độ tra cứu và cá nhân.
Gợi ý kỳ tới hiện hiển thị trạng thái chờ tích hợp, chưa có form gợi ý hoạt động.

Giữ toàn bộ route, tên menu, vị trí chức năng, thứ tự section, trường nhập,
bộ lọc, cột bảng và hành động. Không thay API, dữ liệu học vụ, đăng nhập/đồng bộ
VNU hoặc cách tính thống kê. Không thêm dashboard, panel hay chức năng mới.

```text
Header: thương hiệu                         Ngôn ngữ / Giao diện
Thông tin nguồn VNU
Sidebar: hồ sơ / điều hướng    Thông báo nguồn / nội dung tab hiện tại
Footer
```

## Hướng thiết kế trước triển khai

- Canvas `#F7F7F9`, surface `#FFFFFF`, chữ chính `#202127`, chữ phụ `#626671`,
  viền `#E5E7EB`, tím nhấn `#6D4AFF`; thêm token trạng thái và dark theme.
- Giữ một font Be Vietnam Pro với đủ dấu tiếng Việt; tiêu đề trang 28–36px,
  tiêu đề section 18px, nội dung 14px, metadata 12–13px. Số dùng tabular numerals.
- Giữ căn trái và tỷ lệ khung hiện tại. Sidebar sáng với mục chọn tím nhạt;
  header/control gọn; dữ liệu có bề mặt rõ, khoảng cách theo nhịp 4/8px.
- Tính cách đến từ tiêu đề chắc, dữ liệu học vụ rõ và các nhóm môn có ý nghĩa.
  Các nhóm màu hoàn thành/có thể học/chưa thể học luôn có chữ đi kèm.

Đối chiếu brief: không đưa hero, lịch hoặc task inbox của Amie vào sản phẩm;
không dùng headline lớn và chuyển động trang trí của Shopify Design trong
bảng điểm. Không thêm chỉ số hay thẻ tổng hợp để lấp màn hình. Giảm gradient
và các viền lồng nhau trong cấu trúc có sẵn, giữ thông báo nguồn tại chỗ.

## Kiểm chứng

Trước chỉnh sửa, các regression Chrome cho biểu đồ, workspace/hồ sơ, bản đồ
học phần và tra cứu chương trình đều đạt. Ảnh trước/sau chỉ dùng dữ liệu tổng
hợp, lưu cục bộ trong `backups/frontend_polish_20261028/`.

## Thay đổi đã thực hiện

- `themes.css`: semantic tokens sáng/tối cho canvas, surface, chữ, viền, hành động,
  trạng thái và biểu đồ; các nền gradient lớn được đổi sang màu đặc. Placeholder
  dùng màu chữ phụ theo theme thay vì màu mặc định của trình duyệt. Viền ô nhập
  dùng token riêng, đủ tương phản 3:1 trên nền ô nhập trong hai theme.
- `fonts.css`, `fonts/`: phục vụ Be Vietnam Pro tại máy chủ ứng dụng, giữ family
  cũ và năm weight 400/500/600/700/800. Tổng 15 WOFF2 là 238.132 byte; chỉ tải
  subset cần dùng. Bản font không sửa đổi, kèm giấy phép SIL OFL từ
  [Google Fonts](https://github.com/google/fonts/tree/main/ofl/bevietnampro).
- `index.html`, `workspace.css`: giữ header/sidebar/footer và bốn tab; đồng bộ
  icon nét, thứ bậc chữ, khoảng cách, nút, focus và disabled. Ở 390px, các nút
  điều hướng hiện có wrap thành hai hàng để không giấu mục cuối; bộ chọn ngôn
  ngữ/theme vẫn ở header. Không thêm menu hoặc hệ thống điều hướng mới.
- Dashboard: biểu đồ dùng màu theo theme; dành đủ chiều rộng SVG cho nhãn và
  điểm khi có nhiều học kỳ, cuộn bên trong vùng biểu đồ khi cần. Giảm khoảng
  trắng dư dưới biểu đồ tín chỉ. Không sửa hàm thống kê hay số liệu.
- Hồ sơ: dành thêm chỗ cho tên môn, căn phải cột số, tabular numerals, giữ sáu
  cột và cuộn riêng. Form đăng nhập, thông tin nguồn, thông báo đồng bộ và các
  hành động quản lý dữ liệu được tinh chỉnh tại vị trí hiện có.
- Điều kiện học: giữ hai chế độ, bộ lọc, ngân sách mặc định 20 tín chỉ và ba nhóm
  trạng thái. Các môn hiển thị thành hàng rõ ràng trong từng nhóm, giảm khung
  lồng nhau; giữ điều kiện, lý do, checkbox và quy tắc chọn. Tra cứu công khai giữ
  bảng, PDF, CSV và dialog chi tiết; dialog được bổ sung tên truy cập.
- Gợi ý kỳ tới: áp dụng cùng typography và surface cho trạng thái chờ hiện có.
  Không dựng form hoặc kết quả giả.

JavaScript chỉ đổi màu/kích thước vẽ biểu đồ, tên truy cập của dialog và
`aria-orientation` của tablist theo breakpoint. Không thay endpoint, payload,
router, dữ liệu lưu trữ, logic đăng nhập, đồng bộ hoặc tính toán học vụ.

## Kết quả sau triển khai

Tám script Chrome đều đạt, dùng dữ liệu cá nhân giả lập và chặn các request
đăng nhập/đồng bộ thật:

| Script trong `tests/frontend/` | Phạm vi đã kiểm tra |
| --- | --- |
| `check_presentation.py` | Bốn trang ở 1440/1024/390px, sáng/tối, VI/EN; đúng thứ tự tab/panel; không tràn ngang toàn trang; font tiếng Việt đủ năm weight; tương phản chữ mẫu ≥4,5:1, viền ô nhập ≥3:1; focus bàn phím, cuộn bảng, focus/đóng dialog; lọc rỗng, loading, lỗi, disabled, reduced motion |
| `check_workspace.py` | Điều hướng, hồ sơ, lọc bảng điểm, cô lập dữ liệu và ngôn ngữ/theme/mobile |
| `check_charts.py` | Giữ mọi lượt học, học lại, khoảng thiếu điểm, thống kê/biểu đồ, bộ lọc và logout |
| `check_course_status.py` | Ba nhóm môn, lý do, quota, ngân sách, mặc định môn có thể học, checkbox bị khóa và logout race |
| `check_curriculum_reference.py` | Năm chương trình nguồn, khóa, tiên quyết, PDF, ngân sách, chọn môn, lọc, CSV và response trễ |
| `check_portal.py` | Đăng nhập giả lập, hiện/ẩn mật khẩu, giữ dữ liệu nguồn, lỗi CAPTCHA, hết phiên và logout race |
| `check_portal_sync_feedback.py` | Tiến độ/lỗi đồng bộ, giữ thông báo khi quay lại trang, reload, VI/EN và logout |
| `check_vnu_only.py` | Nguồn VNU, URL cũ, readiness, không gọi luồng nhập điểm thủ công và cô lập phiên |

Đã chạy thêm:

```text
node tests/frontend/check_analytics.mjs
node --check app/static/analytics.js
node --check app/static/curriculum-reference.js
node --check app/static/theme.js
node --check app/static/workspace.js
.venv/Scripts/python.exe -m ruff check .
git diff --check
```

Tất cả đạt. Không có bước build hoặc typecheck frontend riêng trong stack này.
`/health`, `/ready`, CSS font và WOFF2 trả HTTP 200. Giữ nguyên tiến trình Uvicorn
không dùng `--reload`, tránh ảnh hưởng phiên RAM và lỗi subprocess Windows.

Đã xem ảnh desktop/tablet/mobile, sáng/tối, bảng điểm, ba nhóm môn, tra cứu công
khai và form đăng nhập. Sau lần xem đầu, sửa vùng cuộn SVG/nhãn học kỳ, chiều cao
dư của biểu đồ tín chỉ và cách wrap bốn nút điều hướng trên mobile. Ảnh sau cùng
và báo cáo đo mẫu lưu ở `backups/frontend_polish_20261028/after/`; ảnh tra cứu
nguồn còn ở `backups/curriculum_lookup_20261024/ui/`. Đây là artifact cục bộ bị
Git ignore, không đưa dữ liệu cá nhân hoặc screenshot lên repository.

## Giới hạn và cấu trúc thông tin

- Kiểm tra trình duyệt bằng Chrome; chưa chạy Safari/Firefox hoặc chứng nhận
  accessibility toàn diện. Các phép đo tương phản là kiểm tra mẫu ở các vùng
  chính và control, không phải tuyên bố toàn bộ WCAG đã được chứng nhận.
- Không dùng tài khoản VNU thật trong lượt UI này. Regression đăng nhập/đồng bộ
  dựa vào response giả lập; không thay collector hoặc backend.
- Gợi ý kỳ tới vẫn chờ tích hợp nghiệp vụ như phiên bản đầu vào. Cảnh báo catalog
  đang rà soát và các giới hạn học vụ vẫn được giữ tại chỗ.
- Không có thay đổi kiến trúc thông tin được triển khai hoặc đề xuất bắt buộc
  để hoàn tất phạm vi này. Mã nguồn được quản lý trên nhánh
  `feat/vnu-curriculum-planning`; ảnh/video kiểm chứng chỉ giữ cục bộ.
