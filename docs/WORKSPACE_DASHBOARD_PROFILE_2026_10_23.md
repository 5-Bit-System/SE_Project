# Dashboard và trang hồ sơ — 23/10/2026

Đã thiết kế lại frontend theo `.github/skills/frontend-design/SKILL.md`.
Người dùng yêu cầu hồ sơ thành một mục riêng, Dashboard thay trang mở đầu
bảng điểm và để phần module đăng nhập/401 sang lượt sau.

## Cập nhật biểu đồ và bỏ demo

Cập nhật này thay mô tả Dashboard nhập tay ở lần bàn giao ban đầu bên dưới.
Dashboard ưu tiên bảng điểm VNU đã lưu, với ba biểu đồ:

- Đường trung bình cộng điểm hệ 10 hợp lệ theo học kỳ. Mọi lần học được giữ
  riêng; đây không phải GPA chính thức hoặc trung bình có trọng số tín chỉ.
- Vòng phân bố ký hiệu điểm chữ nguồn, gồm trạng thái trống/chưa có điểm.
- Cột tín chỉ ghi trên từng lượt học theo học kỳ, gồm học lại; đây không phải
  tổng tín chỉ tích lũy hoặc phép tính đủ điều kiện tốt nghiệp.

Có lọc năm học, chú giải, bảng số liệu/cách tính, trạng thái trống, thời điểm
lấy và cảnh báo completeness. Số chưa rõ không được gán 0; điểm 0 hợp lệ vẫn
được tính. Đường không nối qua kỳ chưa có điểm. Tổng kết chính thức chỉ hiển
thị nguyên văn từ nguồn. Không apply nguồn vào nhập tay/GPA dự án/gợi ý môn.

Đã bỏ bộ chọn “Dữ liệu minh họa”, luồng tải profile demo và các nút tạo điểm
mẫu theo năm. Giữ fixture tổng hợp phục vụ test và API backend tương thích.
Dashboard giờ tự đọc `/me/profile` khi mở trang để lấy snapshot đã lưu; không
tự đăng nhập/crawl VNU. Trạng thái chưa có phiên vẫn theo quyền truy cập cũ.
Phần kế hoạch nhập tay được thu gọn riêng. Nguồn được giữ trong RAM và xóa
khỏi biểu đồ khi đăng xuất/xóa dữ liệu/hết hạn phiên.

Kiểm tra bổ sung đã đạt:

```powershell
node tests/frontend/check_analytics.mjs
.venv/Scripts/python.exe tests/frontend/check_charts.py
.venv/Scripts/python.exe tests/frontend/check_workspace.py
.venv/Scripts/python.exe tests/frontend/check_portal.py
```

Đã xem ảnh fixture sáng/tối/mobile dưới ignored
`backups/dashboard_charts_20261023/`. Ruff frontend, JS syntax, diff checks đạt.
Không gọi portal thật, không sửa API/database hoặc restart backend trong lượt
này. Ghi chú “không gọi API profile khi mở Dashboard” bên dưới là trạng thái
của lần thiết kế trước, đã được thay bởi yêu cầu dùng bảng điểm VNU để thống kê.

## Bố cục đã bàn giao

- Dashboard là trang mặc định `/#dashboard`: chỉ số kế hoạch, thanh tích lũy
  tín chỉ nhập tay, học kỳ đã ghi nhận, tối đa bốn môn đủ điều kiện theo API
  và các thao tác chuyển sang nhập điểm/lập kế hoạch/hồ sơ.
- Hồ sơ là trang `/#profile`, không còn dialog. Có khối danh tính, thời điểm
  lấy nguồn, thông tin chưa có được đánh dấu rõ, tổng kết nguồn, bảng điểm
  đầy đủ theo học kỳ, tìm mã/tên môn, lọc học kỳ và đếm lượt học hiển thị.
- Nhập điểm có mục riêng `/#transcript`, giữ toàn bộ thao tác thủ công và
  xem tệp nguồn; Điều kiện học/Gợi ý kỳ tới vẫn có mục riêng.
- Header gọn lại với tài khoản, ngôn ngữ và theme. Chương trình/demo nằm
  trong sidebar. Mobile dùng điều hướng ngang cuộn trong vùng riêng.
- Sidebar hỗ trợ phím mũi tên/Home/End; tab có aria-selected/aria-controls.
  Các trang có hash riêng và hỗ trợ Back/Forward. Focus rõ, bảng cuộn ngang
  trong vùng riêng, không tràn trang ở 390px và tôn trọng reduced motion.

Giữ font Be Vietnam Pro và token palette hiện hành: nền #eef2ff, bề mặt #fff,
chữ #253654, nhấn #3658ad, tối #101a32/#e6edfc. Bỏ hero lớn để phần học tập
được nhìn thấy sớm hơn. Bảng điểm nguồn dùng bố cục toàn trang; nguồn dữ liệu
được phân biệt ngay cạnh các chỉ số.

## Ngữ nghĩa dữ liệu

Dashboard dùng dữ liệu nhập tay và chương trình đang chọn. Thanh tín chỉ là
đối chiếu tổng tín chỉ catalog, không kết luận đủ điều kiện tốt nghiệp. Các
môn “Có thể học tiếp” là kết quả eligibility, không phải gợi ý đã xếp hạng
hoặc khẳng định sẽ mở lớp. Lỗi eligibility không tiếp tục trình bày danh sách
cũ như kết quả hiện hành.

Bảng điểm VNU giữ nguyên mã/tên/điểm và mọi lần học. Tìm kiếm/lọc chỉ thay
cách xem, không sửa snapshot hoặc nhập điểm sang kế hoạch. Đổi chương trình
xóa kế hoạch nhập tay như trước; hồ sơ tài khoản vẫn độc lập. Không tính lại
GPA VNU, không tạo tên/ngành/khóa từ MSSV, không lưu profile vào localStorage.

Lượt này chỉ sửa frontend; không chỉnh API/auth/worker/database hoặc gọi VNU.
Không restart backend để tránh thu hồi phiên người dùng đang có. Dashboard
không gọi profile API khi vừa mở; vào hồ sơ mới đọc dữ liệu. HTTP 401 khi đọc
hồ sơ không có phiên vẫn giữ đúng quyền truy cập; module đăng nhập để sau.

## Kiểm chứng

Hai kiểm tra Chrome độc lập đã đạt:

```powershell
.venv/Scripts/python.exe tests/frontend/check_workspace.py
.venv/Scripts/python.exe tests/frontend/check_portal.py
```

Bao gồm năm panel trực tiếp/ID không trùng, dashboard mặc định, không dò dữ
liệu cá nhân trên dashboard, nhập và sửa điểm, chỉ số kế hoạch phản ánh API,
nguồn VNU không đổi nhập tay, tìm kiếm/lọc, escape text, thứ tự học kỳ, VI/EN,
hai theme qua nút thật, desktop/390px, không tràn trang/JS exception, đổi ngành
xóa kế hoạch nhưng giữ hồ sơ độc lập, logout xóa DOM/state.

Đã xem ảnh desktop sáng/tối và mobile, sửa các lỗi bố cục phát hiện khi review.
Ảnh chỉ dùng fixture tổng hợp, ở thư mục ignored
`backups/workspace_redesign_20261023/` và `backups/portal_integration_20261023/`.
Ruff cho kiểm tra frontend, JS syntax và `git diff --check` đạt. Không chạy
lại Python/PostgreSQL suite vì không sửa backend. Các kết quả trước đó là
bằng chứng lịch sử; không coi lượt UI này là nghiệm thu login mới.

Chưa commit/push. Các thay đổi tích hợp portal có từ lượt trước vẫn được giữ.
