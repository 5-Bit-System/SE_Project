# Nối bảng điểm với điều kiện học — 25/10/2026

## Kết quả nghiệm thu nguồn thực cuối lượt sửa

Snapshot mới đã được lưu với `completeness=complete`, giữ binding ngành/khóa;
tất cả cờ kiểm tra nguồn đạt và không còn hàng chưa hiểu. Chẩn đoán xác nhận
nhãn checkbox không khớp mẫu hẹp “Xem cả môn”, nhưng khớp “Xem cả các/những
môn”. Đã sửa grammar, chỉ chấp nhận control có đúng handler `submit_d`, kích
hoạt qua DOM để hỗ trợ vị trí ngoài viewport, rồi kiểm tra lại trạng thái
checked và toàn bộ bằng chứng. Không tự cấp cờ đầy đủ cho snapshot cũ.

Audit chỉ đọc, đúng phạm vi chương trình/khóa của chủ tài khoản, dùng binding,
quy chế và catalog hiện hành: context ready, không còn kết quả cần đối chiếu.
Khi chưa chọn nhánh tốt nghiệp, bản đồ theo thiết kế hiện tại vẫn partial và
tạm dừng kế hoạch. Cả hai nhánh hợp lệ trong nguồn đều cho bản đồ ready với đủ
ba nhóm và kế hoạch gợi ý 20 tín chỉ. Chủ tài khoản cần chọn nhánh đúng trên
giao diện; không tự chọn thay. Không lưu số liệu học tập cá nhân vào tài liệu.

Đã gỡ toàn bộ probe/helper/wait/reload/phase và ba flag opt-in tạm. Không restart
server/phiên ở bước cuối. Chrome kiểm tra grammar, checkbox ngoài viewport,
native form tải lại, đọc lặp không trùng, control lạ và route sai đều đạt.
Các phần “đang chờ” dưới đây là trạng thái lịch sử đã được thay thế ở mục này.

## Chẩn đoán lần đồng bộ bị từ chối và mất thông báo

Người dùng đã xác nhận khung nhưng ba ô vẫn chờ; cập nhật yêu cầu mật khẩu rồi
quay về hồ sơ không rõ kết quả. Kiểm tra cờ kỹ thuật xác nhận binding đã có,
snapshot cũ vẫn unknown. `load()` trên visibilitychange đã có thể ghi đè trạng
thái đang cập nhật/thất bại bằng “Đã tải hồ sơ”. Đã tái hiện và sửa lỗi này.

Session giờ giữ riêng báo cáo kỹ thuật của lần đọc mới nhất (chỉ các cờ kiểm
tra và số lượng), kể cả khi snapshot mới bị từ chối. `/me/profile` và bản đồ
trả báo cáo cho đúng session; không thay snapshot cũ, không đổi schema. Chỉ
báo cáo đã allowlist được ghi vào log khi từ chối, không có URL, control value,
điểm, tên, mã sinh viên hoặc mã môn. Logout/reset xóa chẩn đoán ở giao diện.
Trạng thái đang chạy/thất bại không bị passive refresh che; nút trong form
cập nhật ghi đúng tác vụ. Ba ô chờ ghi rõ điều kiện chặn, không dùng mẫu chung.

Người dùng đăng nhập lại để chẩn đoán. Báo cáo kỹ thuật thực tế cho thấy chỉ
`source_path_valid` và `filters_absent` chưa đạt; một bảng, ba đọc ổn định,
network idle, không phân trang/hàng ẩn/virtualization/loading/hàng chưa hiểu.
Đã sửa nhận diện module được mở từ literal route của menu `Xem điểm sinh viên`
(showApp/ListPoint/listpoint.asp), kể cả khi shell đặt module trong thư mục sâu.
Chỉ cùng HTTPS host và đúng route nguồn; không tự điều hướng URL phỏng đoán.
Các control disabled/readonly không phải bộ lọc hoạt động; các control có thể
lọc vẫn chặn. Các kiểm tra đầy đủ khác và rollback snapshot vẫn giữ nguyên.

Kiểm chứng: 499 offline passed / 40 deselected trước thay đổi client cuối;
165 integration passed / 5 deselected sau thay đổi client; Chrome source
collection mới kiểm tra module frame sâu, readonly metadata, active filters,
route sai, paging/hidden/multiple tables và profile đều đạt. Chrome sync mới
kiểm tra progress/error còn sau visibilitychange/reload, lý do cụ thể, VI/EN,
logout. Các regression portal, binding và bản đồ đạt. Ảnh tổng hợp cảnh báo
đã xem. Server launcher 26476; health/ready 200. Client chạy trong worker mới
mỗi sync nên bản sửa client sau cùng không cần restart server/phiên nữa.

Lần cập nhật thực tiếp theo vẫn chưa qua hai cờ; bản sửa menu literal/readonly
chưa khớp biến thể thực tế. Probe local sau đó nhận được cấu trúc root module
`/ListPoint/`, menu literal đã xác nhận, đúng một checkbox nằm ngoài bảng.
Đã sửa nhận diện namespace nguồn này theo menu đã bấm và HTTPS host; kiểm thử
Chrome thêm module hợp lệ/sai target và active filter đều đạt. Không ghi URL
nguyên bản hay dữ liệu cá nhân. Đã gỡ probe/flag và đoạn giữ/reload worker.
Probe checkbox sau đó cho biết nhãn bắt đầu bằng “Xem cả môn …”, trạng thái
unchecked, handler `submit_d` có submit/query. Đây là lọc thật, không phải tùy
chọn trình bày. Bộ đọc chọn đúng checkbox đã nhận diện trước khi thu bảng; chỉ
miễn kiểm tra restrictive-filter cho checkbox này khi checked. Không bỏ qua
checkbox tùy ý. Chrome xác nhận lấy thêm môn bị ẩn ở chế độ mặc định, cả onclick/
onchange; unknown checkbox vẫn chặn. Đã gỡ toàn bộ probe/wait/reload/flag tạm.
499 offline passed / 40 deselected sau thay đổi client cuối. Đang chờ một lần
đồng bộ của chủ tài khoản để nghiệm thu nguồn thực; phiên nguồn cũ đã đóng.

Tìm thêm lỗi passive refresh có thể đóng form khi đang nhập mật khẩu; đã giữ
form đang sửa và có Chrome regression. Không tự sửa completeness, binding hoặc
điểm nguồn để làm đầy ba cột. Ba cột trên tài khoản thật vẫn chưa được nghiệm thu.

## Sửa tiếp sau phản hồi vẫn chưa thấy kết quả

Người dùng xác nhận đúng URL local. Ảnh thiếu biểu mẫu xác nhận mới; snapshot
đang lưu vẫn có cờ bộ đọc cũ/unknown và không có binding, được kiểm tra bằng
truy vấn chỉ đọc tổng hợp trạng thái kỹ thuật, không xuất danh tính/điểm/mã môn.
Chưa thể xác nhận từ ảnh rằng cache là nguyên nhân duy nhất.

HTML giờ trả no-store, gắn hash nội dung vào URL asset; static dùng no-cache.
Portal tự tải hồ sơ theo phiên còn hiệu lực khi trang mở, khắc phục việc reload
phải vào tab hồ sơ mới phát dữ liệu cho bản đồ. Deep link
`/?course-mode=personal#rules` mở đúng chế độ. Nút Cập nhật bảng điểm VNU trong
thông báo nguồn chưa đủ mở form cập nhật sẵn có; không tự đăng nhập hoặc gửi
credential. Dữ liệu nguồn cũ vẫn cần đồng bộ, rồi xác nhận ngành/khóa.

Suite mới 497 passed / 40 deselected; Ruff/JS/diff đạt. Chrome mô phỏng script
cũ ở URL chưa version, khôi phục hồ sơ bằng HTTP thật qua fixture và kiểm tra
form xác nhận, nút mở cập nhật, hai owner và phản hồi cũ. Portal/VNU-only/bản
đồ/workspace/charts đạt. Năm test PostgreSQL trước đó không chạy lại vì không
đổi store/schema. Chỉ khởi động lại project server, launcher PID 17036; các
endpoint health/ready và asset có version trả 200, cache headers được kiểm tra.
Restart kết thúc phiên RAM cũ; chưa nghiệm thu phân loại dữ liệu thật.

## Phạm vi và căn cứ

Người dùng yêu cầu hoàn thiện Điều kiện học với các khung trong bộ ZIP 2023,
chỉ K67 trở đi, ngân sách mặc định 20 tín chỉ có thể đổi. Sau khi bổ sung tra
cứu công khai, bản đồ cá nhân vẫn trống vì chưa có bằng chứng lấy đủ bảng điểm,
binding ngành/khóa hoặc quy chế. Đợt này xử lý các phần đó theo từng tài khoản.
Thông tin ngành/khóa người dùng cung cấp không trở thành mặc định toàn hệ thống.

Người dùng xác nhận trang VNU hiện toàn bộ học kỳ cùng lúc, không có bộ lọc
hoặc phân trang. Đây là căn cứ cho hợp đồng bộ đọc `vnu-full-table-20261025`,
không phải bằng chứng mọi snapshot cũ đầy đủ. PDF quy chế 3626/2022 và phạm vi
diễn giải được lưu tại [policies/README.md](policies/README.md).

## Hành vi đã triển khai

- Collector kiểm tra host/path HTTPS, container bảng, số bảng, nguồn ổn định
  ba lần, không còn request đọc dữ liệu, lọc/phân trang/hàng ẩn/virtualization/
  loading và không có hàng chưa hiểu. Không lưu giá trị điều khiển hoặc URL
  vào chẩn đoán. Kiểm tra không đạt giữ unknown và bảo vệ snapshot trước đó.
- Chủ tài khoản xác nhận chương trình và khóa khớp nguồn. Request chỉ chứa
  lựa chọn và revision, không nhận owner, điểm, passed set hoặc verified flag.
  Cookie/session, generation, snapshot digest và enrollment scope được kiểm
  tra; ghi binding dưới khóa owner bằng transaction. Đồng bộ đổi ngành/khóa
  hủy binding; đổi tên riêng lẻ giữ binding.
- Có năm khung để đối chiếu. Bốn khung thường dùng runtime hiện có; Toán tài
  năng được đọc từ nguồn tra cứu đã kiểm tra, không công bố catalog DB mới.
  Nhãn Toán học không rõ hệ chuẩn/tài năng không tự chọn khung đầu tiên.
- Quy chế được đánh phiên bản. Mã môn phải khớp chính xác, tín chỉ và các cột
  điểm phải nhất quán. Học lại chỉ giải quyết chuỗi F/D/D+ sang kết quả cuối
  kỳ sau rõ ràng theo cách diễn giải đã ghi; các chuỗi khác vẫn cần review.
- Bản đồ có thể hiển thị các kết quả riêng lẻ đã giải quyết khi context còn
  partial. Môn chưa rõ không thỏa tiên quyết hoặc được chọn cho kỳ sau. Mã
  ngoài khung, thiếu chọn hướng/nhánh, hoặc mâu thuẫn quy tắc sẽ dừng kế hoạch.
  Tổng tích lũy partial được ghi rõ chỉ là phần đã đối chiếu được.
- Eligibility, recommendation, advisor và progress đầy đủ tiếp tục yêu cầu
  context ready. Không chuyển partial thành ready hay dùng input thủ công.
- Giao diện có xác nhận riêng từng tài khoản, ngân sách 20 mặc định/1–30,
  tìm kiếm, lý do cần review, VI/EN, mobile và bỏ qua phản hồi đã cũ sau logout.

## Kiểm chứng

Suite offline với nguồn `docs/acceptance/hus_2022`: **495 passed / 40 deselected**,
một cảnh báo Starlette/httpx đã có. Năm ca store PostgreSQL đạt trên database
kiểm thử riêng, bao gồm owner isolation, giữ/hủy binding khi refresh, rollback
nguồn unknown thay đổi và generation chống ghi sau delete. Không đọc hồ sơ
thật để nghiệm thu kết quả cá nhân.

Chrome với dữ liệu tổng hợp kiểm tra hai owner, hai ngành/khóa, xác nhận nguồn,
ba trạng thái, ngân sách, VI/EN/mobile, phiên/logout và phản hồi cũ. Các fixture
nguồn kiểm tra đăng nhập mới và thu toàn bảng có/không có dấu hiệu thiếu dữ
liệu. Các fixture portal nguồn dùng proxy localhost đóng để chặn request chưa
mock. Fixture profile giả lập URL đã tới default.asp bằng history API; không
coi đó là kiểm thử native HTTP 302. Trong lần sửa harness, một redirect giả
đã dẫn tới trang đăng nhập VNU công khai; không gửi thông tin đăng nhập thật
hoặc truy cập hồ sơ thật. Harness đã được sửa và kiểm tra lại.

Local đã nạp lại tại http://127.0.0.1:8000; health/ready/PDF quy chế trả 200,
endpoint binding chưa đăng nhập trả 401. Hai script bản đồ/portal được phục vụ
khớp hash file workspace. Năm khung công khai và ngân sách 20 mặc định đã kiểm
tra qua HTTP; Chrome tra cứu `--live` đạt sau restart. Phiên RAM cũ kết thúc,
chủ tài khoản cần đăng nhập lại. Không đọc endpoint hồ sơ thật khi kiểm tra.

Ảnh xác nhận và bản đồ tổng hợp ở `backups/personal_academic_20261025/ui/`
(ignored), gồm desktop/390px, đã xem trực quan. Ruff, JS syntax và diff được
kiểm tra khi hoàn tất. Tệp cấu hình database đã bỏ repr chứa credential và có
regression test, sau một traceback cục bộ vô tình hiện URL kết nối khi gọi sai
method. Không sao chép giá trị đó vào repo; không tự đổi mật khẩu hoặc .env.

## Giới hạn và thao tác tiếp theo

Chưa nghiệm thu trên bảng điểm thật. Sau khi nạp lại local, chủ tài khoản cần
đăng nhập hoặc cập nhật hồ sơ/bảng điểm để chạy collector mới, rồi xác nhận
ngành/khóa tại Điều kiện học → Theo bảng điểm VNU. Refresh riêng bản đồ không
lấy lại nguồn VNU. Bố cục chưa hỗ trợ, điểm chưa cuối cùng hoặc mã cần tương
đương vẫn hiển thị lý do chờ đối chiếu. Không đảm bảo mọi tài khoản sẽ ready.

Các khung vẫn draft_unverified; chưa rà mọi sửa đổi áp dụng khóa sau K67. Toán
tài năng chưa lập kế hoạch tự động vì nguồn mâu thuẫn quy tắc chọn hướng. Môn
màu vàng không xác nhận lớp mở kỳ tới. Không đổi schema, migration, .env, dữ
liệu điểm nguồn, active catalog revision hoặc RAG. Chưa commit/push.
