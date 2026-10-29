# Bàn học số — 29/10/2026

## Phạm vi và thiết kế trước triển khai

Mở rộng `motion.css`/`motion.js` hiện có; giữ bốn trang, API, nội dung và logic
học vụ. Không thêm thư viện, nền mới song song hoặc sự kiện thành công giả.

- Một sách CSS 3D/SVG, màu giấy trung tính/lavender/indigo. Trang lật quanh gáy
  1,6 giây, nghỉ trong chu kỳ 8 giây; front/back riêng, backface hidden, đường
  chữ mô phỏng. Trang quay về ở mặt dưới, hai đầu chu kỳ cùng hình dạng.
- Sách nằm ở khoảng trống bên phải vùng tiêu đề. Định vị theo vùng trống thực,
  kiểm tra giao với nút, chữ, bảng và card; thu nhỏ hoặc ẩn nếu không đủ chỗ.
  Vị trí absolute trong tài liệu nên cuộn tự nhiên, không cần scroll loop.
  Hai chi tiết nhỏ tối đa (tờ giấy và dấu cộng), cùng phong cách. Mobile ẩn sách.
- Ripple 380ms trên button/nav/card có hành động, từ vị trí bấm hoặc tâm khi
  dùng bàn phím; tối đa bốn ripple, tối đa một/control. Lớp clip riêng giữ focus
  ring bên ngoài; không preventDefault hoặc chặn pointer. Label nav giữ vị trí.
- Chip kế hoạch công khai: fade/FLIP/exit ngắn sau response thật; tổng tín chỉ
  cập nhật ngay và chỉ chuyển opacity. Không animate lại toàn bộ bảng khi lọc.
- Loader sách 20px ở thông báo đang kết nối thật; checkmark SVG ở thông báo
  cập nhật đã kết thúc và snapshot được chấp nhận. Dùng status region sẵn có,
  không dựng thông báo lưu kế hoạch vào server khi sản phẩm chưa có hành động đó.
- IntersectionObserver dừng sách/loader ngoài viewport; visibility và reduced
  motion dùng controller hiện có. Khi giảm chuyển động, sách tĩnh, không ripple
  lan rộng/scale; nội dung và feedback trạng thái vẫn hiện đầy đủ.

Tự rà soát: ưu tiên một điểm nhấn sách, không đặt đồ vật sau bảng đọc dài hoặc
thêm chuyển động mạnh lên card tĩnh. Giữ gradient hiện có; không thêm particle,
cursor hay confetti. Đo và xem thực tế ít nhất hai lần lật trước nghiệm thu.

## Kiểm chứng

Đã triển khai trực tiếp trong `app/static/index.html`, `motion.css`, `motion.js`.
Các hook trình bày nhỏ nằm ở `curriculum-reference.js`, `course-status.js` và
`portal.js`; không sửa backend, endpoint/payload hoặc công thức/quy tắc học vụ.
Revision HTML: `20261029-study-desk`; cơ chế asset hash hiện có nạp CSS/JS mới.

### Hiệu ứng và vị trí thực tế

| Hiệu ứng | Vị trí và điều kiện |
| --- | --- |
| Sách tự lật | Khoảng trống bên phải vùng tiêu đề desktop. Lật 1,6s, chu kỳ 8s; trở về ở mặt dưới khi ẩn để không ló trang qua bìa hoặc bật ngược. Sách chờ entrance kết thúc rồi đo vị trí; có lớp clip trang trí để không gây tràn ngang trong lúc resize. |
| Hai chi tiết phụ | Tờ giấy và dấu cộng nhỏ nằm trong cùng vùng của sách, nhịp 13/15s; sách nổi 2px/11s. Không rải thêm đồ vật vào bảng. |
| Ripple và nhấn | Button và navigation thật, 380ms, theo vị trí pointer hoặc tâm khi Enter/Space. Giới hạn bốn phần tử transient, tối đa một ripple/control, tự xóa sau hoàn tất/hủy. Clip con giữ nguyên focus ring. |
| Navigation/card | Giữ indicator hiện có; icon hover 1px, nhãn đứng yên. Card chương trình có hover/focus nâng 2px và press nhỏ; card dữ liệu tĩnh chỉ đổi viền. |
| Môn trong kế hoạch | Chip công khai enter 220ms, exit 160ms, FLIP 220ms cho chip còn lại. Chỉ chạy sau response kế hoạch thật; số tín chỉ cập nhật ngay, opacity 180ms, không count-up. Kế hoạch cá nhân dùng cùng phản hồi tổng. |
| Loader sách | 20px cạnh trạng thái “Đang kết nối VNU…” của tác vụ thật. Icon aria-hidden; role/status và nhãn thông báo sẵn có vẫn phục vụ screen reader. |
| Checkmark | SVG stroke 360ms và notice fade/slide 180ms trong status region hiện có. Chỉ khi job `done`, latest collection `saved`/`unchanged` và `complete`. Không hiện cho tải hồ sơ thụ động, lỗi hoặc `retained`. |
| Empty state | Một icon sách tĩnh nhỏ trong vùng biểu đồ trend rỗng; nội dung giải thích vẫn là chính. |

Không thêm toast toàn trang, confetti hoặc sự kiện lưu giả. Các phản hồi sau
cập nhật dùng thông báo sẵn có. Lưu kế hoạch vào backend chưa phải chức năng của
trang này; lựa chọn công khai vẫn là kế hoạch tham khảo như trước.

### Kết quả chạy

- `tests/frontend/check_study_desk.py` đạt. Ghi **18,69 giây quan sát thực** của
  sách, đủ hai lần lật; kiểm tra origin, backface, ma trận hai đầu chu kỳ giống
  nhau và mặt trang ẩn ở pha trở về. Xem ảnh pha 0/2000/2500/6000/7999ms ở DPR 3.
- Kiểm tra độc lập mọi text node/control/bảng/card với vùng sách: **24 tổ hợp**
  trang × theme × viewport 1440/1024/390; thêm đối chiếu VI/EN. Không giao nhau,
  không tràn ngang. Mobile ẩn sách; desktop tự thu nhỏ/ẩn nếu không có chỗ trống.
- Bấm nhanh 60 lần không tích tụ ripple; sau 500ms không còn ripple/layer.
  Kiểm tra vị trí pointer, tâm keyboard, disabled không phản hồi giả, focus card
  và 24 lượt đổi mục không nhân đôi background/sách/indicator/listener.
- Thử giữ response kế hoạch: chip chưa thêm trước khi server trả kết quả; sau
  response thực của public planner stateless mới animate. Thêm/bỏ CME1000/PES1000
  giữ đúng tổng; chip còn lại đổi vị trí; lọc bảng không replay animation hàng.
- Hai job cập nhật VNU giả lập: đang chạy chỉ có loader; `done/saved/complete`
  mới có check; lỗi `incomplete_snapshot/retained` giữ thông báo lỗi và không có
  check. Loader dừng ngoài viewport và khi mô phỏng visibility hidden.
- Reduced motion: sách tĩnh, không ripple lan/scale/FLIP, giá trị và feedback vẫn
  đầy đủ. Sách/loader dùng IntersectionObserver; nền giữ controller visibility
  hiện có. Không có vòng lặp JavaScript theo scroll hoặc mousemove.
- Chín regression còn lại cũng đạt: presentation, motion, workspace, charts,
  course_status, curriculum_reference, portal, portal_sync_feedback, vnu_only.
  Tổng cộng **10 script Chrome**; thêm Node analytics aggregation, syntax của
  bốn JS thay đổi, whole-repo Ruff và `git diff --check` đều đạt.
- Stack không có build/typecheck frontend riêng. Giữ Uvicorn no-reload đang chạy;
  không restart, sửa DB/catalog hoặc truy cập VNU thật.

### Xem preview và chạy lại

Mở `http://127.0.0.1:8000/?ui=study-desk#dashboard` ở desktop. Đợi khoảng hai giây
để bắt đầu thấy trang lật. Các artifact nằm trong Git-ignored folder:

```text
backups/study_desk_motion_20261029/
  book-turn-preview.webm        # clip sách 18 giây
  study-desk-preview.webm       # bản ghi đầy đủ tương tác/kiểm tra
  book-phase-*.png              # ảnh pha, DPR 3
  dashboard-light-1440.png ... # ảnh từng trang/theme/viewport
  loader.png / success.png / reduced-motion.png
  verification.json
```

```text
.venv/Scripts/python.exe -m playwright install ffmpeg
.venv/Scripts/python.exe tests/frontend/check_study_desk.py
.venv/Scripts/python.exe tests/frontend/check_presentation.py
.venv/Scripts/python.exe tests/frontend/check_curriculum_reference.py
node --check app/static/motion.js
.venv/Scripts/python.exe -m ruff check .
```

Các lệnh browser check cần server local cổng 8000 và Chrome. FFmpeg chỉ cần cho
thu bản ghi trong test; không tham gia giao diện sản phẩm.

Toàn bộ tài khoản/mật khẩu/điểm trong fixture và video là giả lập. Public planner
chỉ xử lý kế hoạch tham khảo, không lưu tài khoản hoặc bảng điểm. Request ngoài
localhost bị chặn; không ghi dữ liệu người dùng thật vào artifact/Git.

### Giới hạn

Đã chạy Chrome và xem ảnh/video; chưa chạy Safari/Firefox hoặc benchmark FPS trên
điện thoại yếu. Mobile chủ động ẩn sách nền để giữ chỗ đọc; vẫn có phản hồi nút,
loader và thông báo. Backend lưu kế hoạch hoặc mốc đủ điều kiện tốt nghiệp chưa
được triển khai trong phạm vi này. Phạm vi phát hành gồm mã nguồn, font/giấy phép,
test và tài liệu; ảnh/video kiểm chứng chỉ giữ cục bộ.

### Kiểm tra trước phát hành

Lượt kiểm tra publication ngày 29/10 đạt **500 offline tests, 50 deselected**;
Ruff, Node aggregation/syntax và hai catalog builder checks đều đạt. Một kỳ vọng
integration test cũ (`eligible == []` khi chương trình đang rà soát) đã được tái
hiện trên commit gốc `883b9d3` và cập nhật trong commit test riêng: các môn đủ cơ
sở mặc định vẫn hiện, nhưng `can_plan` vẫn false, không gợi ý môn và tổng gợi ý
bằng 0. Không thay code nghiệp vụ Python. Các kiểm tra PostgreSQL không chạy lại
trong lượt frontend/publication này; báo cáo XML chỉ lưu trong `backups/`.
