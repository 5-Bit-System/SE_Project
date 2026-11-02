# Gợi ý kỳ tới: hội thoại và lộ trình

## Phạm vi và thiết kế trước triển khai

Yêu cầu ngày 01/11/2026: pull main mới nhất trước, triển khai toàn bộ concept
đã thống nhất. Đã fast-forward từ fba94de đến main 5239b73; giữ cấu hình IDE,
credentials và AD-102 local. Không tự commit, push hoặc deploy.

Giữ menu, Dashboard, Hồ sơ và bản đồ học phần hiện tại. Trong tab Gợi ý kỳ tới,
đặt hội thoại có lựa chọn ở giữa và lộ trình bên phải; trên điện thoại lộ trình
là bottom sheet. Công cụ xác minh nguồn và phương án đã lưu vẫn truy cập được.

Palette: paper #F8F9FD, ink #24253C, indigo #6554E8, lavender #ECE8FF,
mint #42B99C. Dark dùng token hiện có; chữ Be Vietnam Pro self-hosted.
Chữ và nội dung căn trái; khối câu hỏi lớn, câu trả lời là các thẻ lựa chọn.

```
menu | hội thoại + câu hỏi hiện tại | tóm tắt + đường học kỳ
     | các câu trả lời đã chọn     | môn của phương án đang xem
     | ô nhập mong muốn           | mốc tốt nghiệp mong muốn
     | ba phương án + so sánh     | xem / lưu phương án
```

Rà soát brief: điểm nhấn là các lựa chọn chuyển thành lộ trình có môn học thật,
không thêm một hệ thống nền hoặc sách 3D thứ hai. Dùng lại nền/motion toàn app.
Animation có mục đích: lựa chọn chuyển sang tóm tắt, chuyển bước, card nhập vị
trí, đường nối SVG, timeline, drawer, compare và xác nhận lưu thật. Tôn trọng
reduced-motion, visibility, bàn phím và không giữ hiệu ứng sau logout.

## Luồng và hợp đồng

- Hỏi định hướng, tải học/ngân sách mặc định 20 (1–30), mốc tốt nghiệp mong muốn,
  hướng/nhánh khi catalog yêu cầu. Không hỏi lại ngành/khóa đã có trong hồ sơ.
- Một coordinator chia sẻ board/track/path/budget với công cụ kế hoạch hiện có.
- Đọc context mới qua `/me/academic-context`; dùng revision đó và structured
  preference để gọi `/me/recommendations` cho ba bộ trọng số có tên rõ ràng.
- Không dùng `/recommendations` legacy hoặc `/what-if` chưa có baseline. Môn,
  tín chỉ, giải thích và tiên quyết đều lấy từ API/catalog, không tạo dữ liệu giả.
- Lưu chỉ khi người dùng bấm; `/me/semester-plans` tiếp tục kiểm tra CSRF,
  ownership, snapshot basis, tín chỉ, nhóm và tiên quyết ở server.
- Mốc tốt nghiệp là mục tiêu người dùng, không là dự báo được xác nhận. Không
  bịa lịch mở lớp, workload metadata, môn ở kỳ tương lai hoặc phần trăm phù hợp.
- Preview/unready/401/409/503, kết quả rỗng/trùng nhau và lỗi một phương án có
  thông báo cùng hành động phù hợp. Không tắt các gate học vụ để chạy giao diện.

## Kế hoạch kiểm chứng

Test model cho payload, budget/quota, duplicate/conditional/excluded rows và
so sánh. Chrome mới với API giả lập chặn mạng thật: wizard, lựa chọn lại, request,
ba kết quả, drawer/focus, compare, save thật vs lỗi, logout/race, VI/EN, themes,
1440/1024/390, reduced motion, không overflow. Chạy regression map/saved plans,
offline suite và kiểm tra assets trên local. Không dùng tài khoản/điểm thật.

## Kết quả triển khai

Tab `#recommend` có hội thoại chọn định hướng, tải học, ngân sách mặc định
20 tín chỉ, mốc tốt nghiệp và nhánh tốt nghiệp theo catalog. Có thể sửa từng
câu trả lời hoặc bổ sung mong muốn bằng văn bản. Lộ trình bên phải cập nhật
theo lựa chọn và phương án đang xem; mobile dùng bottom sheet. Công cụ học vụ
và các phương án đã lưu được giữ trong phần thu gọn bên dưới.

Ba phương án dùng cùng context/revision đã xác minh, với trọng số khác nhau:

| Phương án | Topic | Keyword | Required course type | Workload |
| --- | ---: | ---: | ---: | ---: |
| Cân bằng | 0.35 | 0.20 | 0.35 | 0.10 |
| Ưu tiên tốt nghiệp | 0.15 | 0.15 | 0.65 | 0.05 |
| Sát định hướng | 0.65 | 0.25 | 0.05 | 0.05 |

`preference.course_type=required` giúp thành phần môn bắt buộc có hiệu lực
trong bộ chấm điểm hiện có. Workload chỉ khớp khi catalog thực sự có metadata;
không suy độ nặng từ tên môn. Orientation/difficulty có trọng số 0 vì giao diện
không thu thập các lựa chọn đó. Không cam kết ba tập môn luôn khác nhau;
giao diện giải thích khi chúng giống nhau hoặc khi một phương án gặp lỗi.
Mục tiêu tốt nghiệp chưa được dùng như một thuật toán tối ưu nhiều học kỳ.

Thẻ môn mở giải thích API và điều kiện tiên quyết AND/OR từ catalog, kèm mã
và tên môn. So sánh dựa trên các mã môn thật. Kết quả hiển thị được lọc lại
theo ngân sách, quota và khả năng lập kế hoạch hiện tại; môn nối tiếp chỉ
được hiển thị trên bản đồ không tự trở thành môn được phép lưu cùng kỳ.
Server tiếp tục là nơi kiểm tra quyết định cuối cùng.

Lưu phương án gọi API hiện có, chỉ báo thành công sau phản hồi thành công.
Nếu mất phản hồi hoặc hết thời gian chờ 60 giây, UI yêu cầu kiểm tra danh sách
đã lưu và chặn gửi lặp từ nút đó. Đây là bảo vệ ở giao diện; không tuyên bố API
lưu đã có idempotency key ở server. Logout/đổi tài khoản/revision hủy kết quả
cũ, đóng nội dung cá nhân và không lưu cuộc hội thoại vào browser storage.

Animation mới gồm entrance có điều phối, lựa chọn bay vào phần tóm tắt,
chuyển câu hỏi, card xuất hiện theo nhịp và đổi vị trí bằng FLIP, vẽ đường
SVG tiên quyết, mở bảng so sánh/bottom sheet và xác nhận lưu. Loading giấy
chạy khi đang xử lý. Hiệu ứng dừng khi ẩn tab và tôn trọng reduced motion.
Cuốn sách nền hiện có tránh các khối hội thoại, lộ trình và tiêu đề mới.

## Bằng chứng kiểm chứng ngày 01/11/2026

- **611 offline tests passed**, 90 trường hợp DB/full-source deselected;
  một warning Starlette/httpx có sẵn. Không chạy lại PostgreSQL acceptance
  vì thay đổi này không sửa backend, schema hoặc dữ liệu nguồn.
- Node model checks đạt: payload nguồn, revision, preference/trọng số,
  ngân sách/quota, excluded/conditional/duplicate và so sánh mã môn.
- Smoke contract lấy payload trực tiếp từ module JS và gọi bộ chấm điểm Python
  thật trên dữ liệu giả: nhánh tốt nghiệp ưu tiên required (0.65 > 0.30),
  nhánh định hướng ưu tiên chủ đề (0.90 > 0.05), workload có metadata làm
  thay đổi điểm. Không gọi provider/model bên ngoài.
- **7 Chrome suites đạt**: recommendation workspace, course status, semester
  plans, VNU-only, presentation, study desk và motion. Bộ mới kiểm tra wizard,
  ba API fixtures, context chưa đủ, lỗi một/toàn bộ phương án, prerequisite
  details, compare, lỗi lưu 409, lưu thành công, mất phản hồi sau commit,
  race khi logout, VI/EN, 1440/1024/390, sáng/tối và reduced motion.
- Regression presentation dùng pixel đã render để đo gradient nút đăng nhập;
  giữ ngưỡng contrast 4.5 thay vì nhầm backgroundColor trong suốt là nền trắng.
  Các công cụ kế hoạch được mở qua summary thật trong browser checks.
- Ruff toàn repo, JS syntax và `git diff --check` đạt.
- `/health`, `/ready`, homepage trả 200; **22 assets HTML và module `.mjs`
  import khớp disk**; module có MIME JavaScript. Endpoint cá nhân ẩn danh
  vẫn trả 401. Đã xem screenshot sáng desktop và tối mobile.

Chạy UI mới: `.venv/Scripts/python.exe -X utf8 -m tests.frontend.check_recommendation_workspace`.
Chạy model checks: `node tests/frontend/check_recommendation_model.mjs`.
Screenshots, video, JSON và JUnit nằm dưới `backups/`, được Git ignore;
video `backups/recommendation_workspace_20261101/recommendation-preview.webm`
chỉ dùng dữ liệu giả để kiểm thử, không phải kết quả gợi ý cho tài khoản thật.

Chưa đo FPS bằng profiler, tải đồng thời, hoặc kiểm thử Firefox/Safari;
chưa đăng nhập VNU thật hay gọi model/provider để kiểm thử đầu cuối. Tính năng
gợi ý/lưu thật vẫn cần context học vụ đủ xác minh theo quy định hiện có.

## Bàn giao local

HEAD sau pull từ `origin/main` là `5239b73`. Sau nghiệm thu local, người dùng
yêu cầu tạo branch mới `feat/recommendation-conversation-ui` và chia thành
19 commit có nội dung riêng trước khi push. Phần này ghi kế hoạch publication;
trạng thái push và commit cuối phải đối chiếu Git/GitHub. Không deploy hoặc
merge vào main trong lượt publication này. Local phục vụ tại
<http://127.0.0.1:8000/#recommend>, không dùng Uvicorn reload trên Windows.
Đã bật lại Docker Desktop và container `se_hus_db` với volume có sẵn;
không migration/seed/publication dữ liệu. Launcher PID 20012, server PID 14416
là số ghi nhận lúc kiểm tra; phải xác minh process trước khi dừng.
