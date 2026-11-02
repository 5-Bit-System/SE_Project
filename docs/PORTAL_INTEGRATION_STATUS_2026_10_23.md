# Trạng thái tích hợp đăng nhập VNU — 23/10/2026

## Chốt phiên và chuẩn bị công bố main — 23/10/2026

Ảnh UI mới của người dùng đã cho thấy đủ tên/ngành/khóa sau sửa connector.
Đây là xác nhận hiển thị, không phải nghiệm thu độc lập completeness/quy chế.
Ngành/khóa theo chữ Lớp quản lý và cấu trúc người dùng xác nhận; chỉ đọc nguồn,
không submit form cập nhật VNU. Không lưu giá trị cá nhân từ ảnh vào tài liệu.

UI đã bỏ nhập điểm/upload/demo, selector bốn ngành và nút hồ sơ trùng trên
header. Sidebar lấy ngành/khóa từ profile; VIE/EN dùng hai nút giống Sáng/Tối.
Nhãn tổng tín chỉ/điểm trung bình đổi ngôn ngữ, số nguồn giữ nguyên. Điều kiện
học/gợi ý còn chờ chuyển đổi: completeness unknown, binding/policy chưa review,
what-if baseline và UI kết quả chưa hoàn chỉnh. Không suy binding từ tên ngành.
API legacy nhận điểm thủ công vẫn còn; chưa hoàn tất đóng API cũ.

Kiểm tra cuối: **398 offline passed / 39 deselected** với explicit HUS acceptance
root; Ruff toàn repo, JS syntax/diff và bốn Chrome regression VNU-only/profile/
workspace/charts đạt. Warning Starlette/httpx cũ. Không chạy lại PostgreSQL,
gọi VNU thật, sửa dữ liệu thật hoặc restart ở lượt chốt phiên.

Người dùng yêu cầu memory rồi commit/push **main**, thay các ghi chú không push
lịch sử của tập thay đổi này. Trước công bố main/origin/main cùng 3129f7c;
kiểm tra Git cho hash kết quả. Các checkpoint bên dưới là lịch sử.

## Nguồn Lớp quản lý — tên đã hiển thị, chờ thử khóa/ngành

Người dùng xác nhận bản sửa trước đã lấy được tên. Ảnh VNU mới cho thấy
**Cập nhật hồ sơ sinh viên → Thông tin nhập học → Lớp quản lý**. Người dùng
xác nhận cấu trúc chữ đang chọn là `[khóa dạng số] [tên ngành]`; không dùng
selector “Khóa” riêng cho giá trị hiển thị này. Không lưu giá trị cá nhân từ ảnh.

Đã bổ sung mở menu bằng nhãn hiện có, giữ tên từ trang hồ sơ, chờ và đọc chữ
của option đang chọn trong ô Lớp quản lý (kể cả select disabled). Không điền,
đổi lựa chọn hoặc submit form trên VNU. Parser tách khóa/ngành chỉ khi một giá
trị rõ ràng đúng cấu trúc; thiếu/sai/mâu thuẫn vẫn unknown. Đây chỉ là thông tin
hiển thị, không xác minh binding CTĐT/quy chế. Store/schema/snapshot digest và
changed-unknown rollback giữ nguyên.

UI hiển thị hai trường từ profile như tên; nút đổi thành “Cập nhật hồ sơ và
bảng điểm” ở cả Việt/Anh. **398 offline passed / 39 deselected** (HUS acceptance
root), Chrome source/profile UI và Ruff/JS syntax đạt; warning Starlette/httpx
cũ. Fixture dùng dữ liệu tổng hợp, có select disabled/nhiều option, chuyển frame
tải chậm, giữ tên/bảng điểm, VI/EN/mobile/logout. Đã xem ảnh mobile tổng hợp.
Không đăng nhập VNU thật, chạy lại PostgreSQL, đổi DB/.env, restart, commit/push.
Worker mới áp dụng ở lần login/sync kế tiếp; cần người dùng thử để nghiệm thu.

## Sửa mở module hồ sơ và đọc ô bảng — chờ xác nhận thật

Người dùng mở lại công việc và cung cấp ảnh **trang VNU gốc**. Ảnh cho thấy mục
“Hồ sơ sinh viên” và bảng nhiều cột nhãn/giá trị; chưa thấy nhãn ngành/khóa trong
vùng chụp. Không sao chép giá trị cá nhân vào tài liệu hoặc fixture.

Phát hiện hai khoảng trống trong code: connector chỉ đọc shell `default.asp`,
chưa bấm menu hồ sơ; parser văn bản bỏ qua dòng nhiều cặp nhãn/giá trị. Đã sửa
client gọi handler của menu đúng nhãn, chờ tên có nhãn trong trang/frame tải về,
và đọc từng cặp ô liền nhau thành dòng riêng. Hỗ trợ ô text/select hiển thị;
bỏ qua ô ẩn, bảng lồng, nhãn gia đình và giá trị mơ hồ. Không đoán ID module,
URL nội dung, nhãn mới hoặc binding chương trình/quy chế.

Chrome fixture đạt điều hướng module, iframe tải chậm, hàng nhiều cột, control,
nhãn vắng, ô ẩn/gia đình, đối chiếu danh tính và bảo toàn bảng điểm. Chrome auth,
Ruff đạt; toàn bộ offline **390 passed / 39 deselected** với HUS acceptance root,
có warning Starlette/httpx cũ. Không sửa store/schema/completeness/rollback;
không chạy lại PostgreSQL hay đăng nhập VNU thật. Health/ready 200, không restart.

Worker mới chạy mỗi lần login/sync: cần thử **Cập nhật bảng điểm** để xác nhận.
Chưa tuyên bố lỗi tài khoản thật đã hết. Nếu tên đã có nhưng ngành/khóa còn thiếu,
cần bằng chứng nhãn/bố cục vùng nguồn tương ứng. Không commit/push.

Các mục bên dưới là lịch sử trước bản sửa này.

## Chốt phiên — lỗi thông tin hồ sơ CHƯA GIẢI QUYẾT

**Trạng thái cuối cùng ngày 23/10/2026:** người dùng đăng nhập được và nhìn thấy
bảng điểm, nhưng **Họ và tên, Ngành học, Khóa học vẫn “Chưa có thông tin”**.
Người dùng xác nhận đã đăng nhập lại sau các bản sửa. Không quy lỗi cho việc
chỉ F5, cache hoặc chưa kết nối lại; không yêu cầu lặp lại cùng thao tác khi
chưa có thay đổi/chẩn đoán mới.

Kiểm tra database chỉ đọc, chỉ trả số lượng trường có giá trị, xác nhận cả ba
trường vẫn chưa được lưu giá trị khác null. Không in định danh hay điểm cá nhân.
Vấn đề nằm trên đường lấy/parse/lưu dữ liệu nguồn; **chưa xác định chính xác
khâu lỗi**. Cần kiểm tra cả việc save bị từ chối/rollback, không chỉ parser.
API vẫn có thể trả profile thành công với trường trống nên F12 không báo lỗi
không chứng minh trích xuất thành công.

Các sửa đổi đọc sớm `default.asp`, parser nhãn, lưu JSONB và hiển thị UI mới chỉ
được kiểm chứng bằng dữ liệu tổng hợp; **chưa sửa được lỗi của tài khoản thật**.
Ảnh người dùng gửi là UI Sổ học tập, không phải bố cục trang VNU nguồn. Truy cập
công khai `default.asp` chuyển về login; chưa quan sát DOM/nhãn/frame/control
và thời điểm tải của trang nguồn sau xác thực.

Bước tiếp theo khi mở lại công việc:

1. Lấy bằng chứng bố cục nguồn: ảnh vùng thông tin trên VNU đã che giá trị cá
   nhân nhưng giữ nhãn/bố cục, hoặc chẩn đoán tối thiểu trong phiên được phép.
   Đã đề nghị ảnh nguồn; chưa nhận được. Không yêu cầu gửi credentials vào chat.
2. Đối chiếu lần lượt thu thập → parser → save/rollback → API → UI, không ghi
   dữ liệu cá nhân/DOM thô/cookies vào log, fixture hay Git. Sửa theo bằng chứng,
   không tiếp tục thêm quy tắc đoán nhãn.
3. Regression phù hợp và nghiệm thu thật ba trường; chỉ khi đó mới đánh dấu
   lỗi được giải quyết. Giữ bảng điểm đã lưu, cổng completeness và giới hạn
   không suy CTĐT/quy chế từ mã sinh viên hoặc chuỗi ngành/khóa hiển thị.

Ước tính ~90% trước đây là tiến độ code, không phải nghiệm thu hoàn tất. Các
cổng alias/completeness/cập nhật/xóa/đăng nhập lại vẫn cần bằng chứng tương ứng.
Chốt phiên theo yêu cầu; chỉ cập nhật tài liệu, không sửa runtime, restart,
gọi portal hoặc commit/push. Các checkpoint bên dưới là lịch sử, không thay
thế trạng thái chưa giải quyết ở mục này.

## Đọc thông tin từ default.asp trước bảng điểm — 23/10/2026

Người dùng xác định trang `https://daotao.vnu.edu.vn/dkmh/default.asp` chứa
thông tin hồ sơ. Truy cập công khai chuyển về login; chưa quan sát cấu trúc
authenticated thật. Đã sửa worker để đọc trang đích cố định này ngay sau xác
thực, trước `open_transcript()` có thể thay nội dung trang chính. Các nhãn danh
tính trước/sau đều được đối chiếu bằng cơ chế hiện có; không dùng giá trị hồ sơ
làm bằng chứng xác thực và không suy ngành/khóa.

Chrome fixture `check_portal_profile_source.py` đạt hai luồng: portal redirect
về default.asp và cần điều hướng đến URL này. Kiểm tra giả lập thông tin bị xóa
khỏi trang khi mở điểm, thông tin thu trước vẫn còn, đọc bảng điểm không đổi.
17 test worker/parser và Ruff đạt. Không thay schema/repository trong lượt này.
Worker mới chạy mỗi login/sync nên không cần restart server. Chờ người dùng
thử Cập nhật bảng điểm; nếu vẫn trống cần bố cục nguồn đã che giá trị cá nhân.
Chưa khẳng định bộ đọc nhãn hiện tại khớp trang thật.

## Bổ sung trường thông tin hồ sơ — 23/10/2026

Người dùng xác nhận đăng nhập và nhìn thấy bảng điểm thật; tên/ngành/khóa vẫn
trống. Đây là bằng chứng do người dùng báo, chưa phải đối chiếu độc lập nguồn.
Đã phát hiện UI gắn cố định cả ba ô là chưa có thông tin, worker chưa trích
xuất và repository chưa ghi JSONB profile sẵn có.

Đã nối worker → lưu profile theo owner → API → UI. Parser chỉ nhận nhãn rõ ràng
Họ và tên/Họ tên, Ngành học/Ngành, Khóa học/Khoá học cùng giá trị sau dấu hai
chấm hoặc tab trên một dòng trong trang/frame authenticated đã mở. Thiếu,
mâu thuẫn hoặc nhiều trường chung một dòng không được đoán thành giá trị.
Không tự truy cập mục thông tin sinh viên khác khi chưa xác định cấu trúc nguồn.
Ngành/khóa ở đây là chuỗi hiển thị, không phải binding chương trình/quy chế.

Thông tin profile lưu nguyên tử cùng lần save; digest bảng điểm giữ nguyên.
Cùng digest có thể bổ sung profile mà không tạo snapshot; changed unknown
snapshot vẫn bị chặn và rollback cả thay đổi profile. Không sửa schema/dữ liệu
nguồn, không chuyển điểm sang học vụ. Các trường profile được xóa khỏi DOM khi
đăng xuất/hết phiên; ngôn ngữ UI không dịch giá trị nguồn.

Kiểm chứng: **390 offline passed, 39 deselected**, **4 portal PostgreSQL passed**
trên database tạm tự dọn, Chrome profile fixture regression và Ruff/JS/diff
checks đạt. Có một warning Starlette/httpx từ trước.

Đã xác minh và restart đúng Uvicorn cổng 8000 để nạp backend mới; health/ready
200. Đính chính: lượt start ghi ở checkpoint trước thất bại do port bận,
health/ready khi đó đến server đang tồn tại. Lần này log xác nhận server mới
khởi động thành công; phiên cũ mất, bảng điểm lưu giữ nguyên. Không gọi portal
thật hoặc đọc dữ liệu cá nhân trong quá trình sửa.

Chờ người dùng thử đăng nhập lại và cho biết vị trí các trường trên VNU gốc.
Nếu nguồn đặt ở trang riêng/khác định dạng, cần bổ sung connector dựa trên
bằng chứng đó. Chưa khẳng định ba trường đã có giá trị với tài khoản thật.
Tiến độ tổng portal vẫn khoảng 90%; không commit/push.

## Tiếp tục module đăng nhập — 23/10/2026

Người dùng yêu cầu tiếp tục kế hoạch và đồng ý thử đăng nhập trực tiếp tại UI.
Yêu cầu này mở lại phần đăng nhập đã hoãn. Đợt này không thay schema, `.env`,
catalog, policy hoặc dữ liệu thật; không commit/push.

- Kiểm tra lại phiên sau khi đọc profile từ storage; không trả dữ liệu nếu
  phiên hết hạn hoặc bị thu hồi trong lúc đọc.
- Job đồng bộ kiểm tra phiên trước khi bắt đầu lưu. Phiên hết hạn/thu hồi
  trước mốc này không ghi snapshot. Nếu transaction đã bắt đầu, vẫn đợi kết
  quả thật theo contract trước đó; không báo đã rollback khi DB đang commit.
- Logout thu hồi phiên trước khi đợi job đang lưu, xóa cookie kể cả khi
  không còn phiên và có thể gọi lặp lại. Mutation vẫn yêu cầu đúng origin.
- UI xóa dữ liệu ngay khi chọn đăng xuất; phản hồi profile bắt đầu trước
  logout không khôi phục bảng điểm/biểu đồ. Phản hồi cũ không xóa phiên UI mới;
  các lượt load có thứ tự để tránh ghi đè bằng response cũ.
- Nhận diện CAPTCHA/OTP qua control hiển thị rõ (captcha input/widget,
  one-time-code input); trả `interaction_required` / HTTP 409 với lời giải
  thích VI/EN và giữ dữ liệu cũ. Control ẩn không bị coi là challenge.
  Đây là nhận diện các control đã test, không phải hỗ trợ hoàn tất CAPTCHA/OTP
  hoặc bảo đảm nhận ra mọi biến thể portal.
- Timeout của Playwright được trả thành `timeout`, tách khỏi lỗi danh tính.
  Body đăng nhập JSON không đúng cấu trúc/encoding trả 400, không echo secrets.

Kiểm chứng mới: **386 passed, 38 deselected** (offline, explicit
`--full-catalog-root docs/acceptance/hus_2022`), một warning Starlette/httpx có
sẵn. Chrome fixture checks: `check_portal_auth.py`, `check_portal.py`,
`check_workspace.py`, `check_charts.py` đạt. Có kiểm tra challenge trước/sau
POST, widget ẩn, phản hồi muộn sau logout, đăng nhập lại và hết phiên, thông báo
VI/EN; các kiểm tra UI chỉ dùng dữ liệu tổng hợp và chặn endpoint cá nhân.
Ruff, JS syntax và diff checks đạt. Không chạy lại PostgreSQL vì không sửa
schema/repository. Đã xem ảnh fixture dark mobile.

Port 8000 không có listener khi tiếp tục; đã khởi động Uvicorn ẩn với access
log tắt, `/health` và `/ready` đều 200. Log kỹ thuật ở thư mục ignored
`backups/portal_resume_20261023/`. Không gọi VNU thật. Người dùng đang được
mời Ctrl+F5 rồi thử `/#profile`; chưa có kết quả thử mới tại thời điểm ghi.

Tiến độ tổng kế hoạch portal vẫn khoảng **90%**, không tăng phần nghiệm thu
khi chưa có bằng chứng. Alias khác MSSV chưa hỗ trợ; completeness vẫn unknown,
changed unknown snapshot không thay bản lưu. Cần đối chiếu nguồn thật và
nghiệm thu reload/update/delete/relogin theo kế hoạch. Bảng điểm VNU chưa được
đưa vào eligibility/recommendations.

Đã triển khai code local theo kế hoạch. **Chưa nghiệm thu đăng nhập thật qua
luồng API/profile mới; không coi đợt đầu đã hoàn tất.** Không commit/push.

Tiếp theo: người dùng đã gửi ảnh hồ sơ thật hiển thị sau sửa UTF-8; chưa đối
chiếu độc lập tính đầy đủ. Frontend đã chuyển hồ sơ từ dialog thành trang
`/#profile`, Dashboard mặc định `/#dashboard`. Xem
[bàn giao giao diện](WORKSPACE_DASHBOARD_PROFILE_2026_10_23.md). Module đăng nhập
và việc rà lỗi 401 được người dùng để sang lượt sau. Các mô tả “dialog” bên
dưới phản ánh lần triển khai đầu.

Sửa lỗi sau lượt thử của người dùng: POST auth trả 502 do worker xuất JSON tiếng
Việt qua stdout Windows `cp1252`, làm tiến trình lỗi và parent nhận dữ liệu rỗng.
Đã tái hiện bằng tiến trình thật không dùng credentials thật. Worker nay xuất
byte UTF-8 trực tiếp, parent decode UTF-8 và phân biệt exit lỗi/JSON lỗi bằng
mã an toàn. Test subprocess ép `cp1252` xác nhận roundtrip tiếng Việt thành công.
Đây là kiểm chứng kênh worker; vẫn cần thử lại luồng portal thật từ UI.

## Đã có

- Connector lấy chọn lọc từ `b790d6af`, parser giữ điểm nguồn, ô trống, học lại,
  học kỳ, tổng kết và hàng chưa hiểu. Không ghép catalog hoặc suy đạt/trượt.
- Worker Playwright/Chrome riêng, tối đa hai lượt chạy, timeout 120 giây;
  credentials qua stdin, stderr không đưa ra log. Browser/cookies chỉ trong job.
- API `/auth/portal`, `/auth/me`, `/auth/logout`, `/me/profile`,
  `/me/portal-sync`, trạng thái/hủy job và `/me/portal-data`.
- Cookie HttpOnly/SameSite Strict, phiên 30 phút trong RAM; restart cần đăng
  nhập lại. Kiểm tra origin cho mutation, ownership và `Cache-Control: no-store`.
  Bản này chỉ nhận `http://127.0.0.1:8000` hoặc `http://localhost:8000`.
- Migration `hus_20261023_03` đã áp local sau backup. Các bảng portal độc lập,
  snapshot/attempt theo owner; FK bảo đảm con trỏ thuộc owner, transaction,
  idempotency, giữ tối đa hai snapshot, xóa cả owner/snapshot/attempt và thu hồi
  phiên. Không thay catalog, `.env`, accounts/students/course_attempts.
- Giao diện “Hồ sơ của tôi” theo skill `.github/skills/frontend-design`, giữ
  palette/font Sổ học tập, sáng/tối và Việt/Anh. Bảng điểm nguồn được giữ nguyên,
  nhóm học kỳ mới nhất trước; có tổng kết nguồn, thời điểm lấy, đăng nhập,
  cập nhật/hủy, đăng xuất và xác nhận xóa. Profile không vào localStorage.

## Giới hạn bắt buộc trước khi nghiệm thu thật

1. Người dùng đã thử luồng thật và gặp `identity_unverified`: yêu cầu bắt buộc
   nhãn MSSV đã chặn tài khoản. Đã thay bằng bằng chứng lượt xác thực mới:
   browser không có cookie portal, trang đầu chưa có menu authenticated,
   form POST HTTPS đúng host/action, tài khoản trong POST đúng giá trị đã điền,
   response 2xx/3xx, menu authenticated xuất hiện và form login biến mất.
   Nếu portal có nhãn mã sinh viên thì vẫn bắt buộc khớp; không dùng bảng điểm
   không rỗng làm bằng chứng xác thực. Không có nhãn được chấp nhận chỉ sau
   khi toàn bộ các kiểm tra login trên thành công. Cần người dùng thử lại thật;
   bản sửa đã kiểm tra bằng browser với response portal giả lập, gồm các ca
   mật khẩu sai, HTTP lỗi, cookie/menu có sẵn và form tới host khác đều bị chặn.
   Username alias khác MSSV vẫn chưa hỗ trợ ánh xạ; không suy cùng người.
2. Chưa xác minh pagination/filter/loading hoặc toàn lịch sử. Snapshot luôn
   `completeness=unknown`. Lần đầu có thể lưu với cảnh báo rõ; digest giống thì
   không tạo bản mới. Dữ liệu thay đổi chưa được xác minh đầy đủ **không thay
   snapshot đã lưu** (`incomplete_snapshot`). Vì vậy nút cập nhật chưa được
   nghiệm thu cho trường hợp điểm nguồn thay đổi. Không tự gán `complete`.
3. CAPTCHA/OTP chưa có luồng tương tác riêng; lỗi portal hiện trả thông báo
   an toàn chung. Chưa có nghiệm thu server/HTTPS/nhiều người dùng thật.
4. Chưa kiểm tra live reload/restart với profile thật hoặc đối chiếu toàn bộ
   hàng/học kỳ/tổng kết. Test DB dùng dữ liệu tổng hợp trên database tạm.

Không lưu mật khẩu VNU, không có mật khẩu local. Chưa apply điểm portal sang
GPA, progress, eligibility, nhập tay, chat hoặc gợi ý môn.

## Chạy và tiếp tục

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-portal.txt
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Máy local đã cài Playwright 1.64.1; worker dùng Chrome đã cài trên máy
(`channel="chrome"`). Mở “Hồ sơ của tôi” và nhập credentials trực tiếp tại UI.
Không đưa credentials vào chat, Git, fixture hoặc log. Chưa tạo dữ liệu portal
thật trong đợt triển khai này. CLI chẩn đoán chỉ in bảng khi có
`--show-transcript`; không dùng tùy chọn này với log dùng chung.

Backup và ảnh/test evidence dùng fixture nằm trong thư mục ignored
`backups/portal_integration_20261023/`. Backup trước migration là
`before-portal.dump`; không ghi đè. Bốn revision catalog active được đối chiếu
trước/sau migration và giữ nguyên. App đã restart với code mới; kiểm tra lại
`/health` và `/ready` khi tiếp tục, không suy từ process cũ.

## Kiểm chứng

- PostgreSQL HUS sau sửa compatibility migration head: **22 passed**, gồm
  ba test portal transaction/ownership/idempotency/delete/rollback/concurrent
  và regression HUS trên database tạm. JUnit: `hus-tests.xml` trong evidence.
- Chrome với fixture: login, giữ điểm nguồn và học lại, escape text, thứ tự
  học kỳ, Việt/Anh, sáng/tối, desktop/390px, xác nhận xóa/hủy và logout xóa DOM.
  Không có JS exception; đã xem ảnh dark mobile. Lệnh:
  `.venv/Scripts/python.exe tests/frontend/check_portal.py`.
- Health/readiness thật sau restart trả 200; auth/profile chưa login trả 401
  kèm `no-store`. Không gọi portal thật trong các kiểm tra này.
- Kết quả offline/lint cuối cùng ghi trong memory sau lần kiểm tra chốt.

Kế hoạch gốc: [tích hợp portal](KE_HOACH_TICH_HOP_PORTAL_BANG_DIEM_2026_10_23.md).
