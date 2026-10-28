# Bản đồ học phần — 24/10/2026

## Mặc định môn có thể học — 28/10/2026

Theo yêu cầu người dùng, môn không có tiên quyết hoặc không tính vào tổng tín
chỉ tích lũy/GPA được giữ ở nhóm **Có thể học kỳ tới** khi chưa xác định hoàn
thành, kể cả kết quả của chính môn đó còn chờ đối chiếu. Quy tắc áp dụng theo
metadata của từng khung. Riêng MAT3374 cũng được yêu cầu mặc định có thể học;
môn này vẫn phải thỏa hai tiên quyết MAT1202 và MAT3507 theo khung KHMTTT.
Môn đã xác định hoàn thành vẫn ở nhóm xanh. Bản đồ ghi rõ lý do mặc
định và kết quả đang chờ; không sửa bảng điểm hoặc coi lựa chọn là đã đạt.

Rule engine vẫn kiểm tra tiên quyết có nguồn, xung đột/điều kiện chưa rõ,
hướng/nhánh và hạn mức nhóm trước khi áp dụng mặc định. Môn thiếu tiên quyết
thật vẫn ở nhóm đỏ. Kết quả chưa rõ không được dùng mở khóa môn khác; các API
recommendation/advisor đầy đủ vẫn yêu cầu context ready.

Phân loại tách khỏi việc lập kế hoạch: nếu còn thiếu chọn hướng/nhánh, có mã
ngoài khung hoặc quy tắc chương trình chưa rõ, các môn mặc định vẫn hiện màu
vàng nhưng kế hoạch tạm dừng, không tự chọn môn và khóa checkbox. Khi được
phép lập kế hoạch, vẫn mặc định 20 tín chỉ, tổng tải học tính cả tín chỉ môn
ngoại khóa đã chọn; các môn bị loại trừ vẫn không cộng vào tín chỉ tích lũy.

## Nối bảng điểm cá nhân theo từng tài khoản — 25/10/2026

Nghiệm thu nguồn thực cuối lượt sửa: snapshot mới đã được nhận là đầy đủ, context
ready và tính được cả ba nhóm với ngân sách 20 sau khi chọn nhánh tốt nghiệp.
Lỗi nguồn nằm ở module root `/ListPoint/` và checkbox “Xem cả các/những môn …”
mặc định tắt, handler `submit_d`; đã sửa nhận diện và chọn chế độ đầy đủ.
Nếu đã thấy các môn hoàn thành nhưng kế hoạch còn tạm dừng, chọn **Nhánh tốt
nghiệp** theo chương trình (khóa luận hoặc học phần thay thế), không cần đăng
nhập hay đồng bộ lại chỉ vì bước chọn nhánh này. Không tự mặc định nhánh.

Sửa tiếp khi người dùng vẫn thấy bản đồ rỗng: HTML/script đã có phiên bản theo
nội dung và chính sách cache phù hợp; tải lại trang tự lấy hồ sơ nếu phiên còn
hiệu lực. Có liên kết thẳng `/?course-mode=personal#rules` và nút **Cập nhật
bảng điểm VNU** ở thông báo nguồn chưa đầy đủ để mở ngay form cập nhật.
Đã kiểm tra bằng Chrome cả trường hợp URL script cũ còn giữ bản chưa có form.
Suite mới **497 passed / 40 deselected**; phần PostgreSQL vẫn là bằng chứng 5
ca ở đợt trước. Việc tải đúng giao diện không tự đổi completeness snapshot cũ.

Phần này thay thế các giới hạn cũ về registry rỗng và chưa có luồng binding
ở cuối tài liệu. Bộ tra cứu khung công khai bên dưới vẫn hoạt động độc lập.

Luồng sử dụng mới:

1. Đăng nhập VNU hoặc vào **Hồ sơ của tôi → Cập nhật hồ sơ và bảng điểm**
   để bộ đọc mới kiểm tra toàn bộ bảng điểm. Snapshot cũ không được tự nâng
   trạng thái đầy đủ. Nút Cập nhật ở bản đồ chỉ đọc lại dữ liệu đã lưu.
2. Mở **Điều kiện học → Theo bảng điểm VNU**, đối chiếu và xác nhận chương
   trình/khóa một lần cho tài khoản. Backend yêu cầu lựa chọn khớp thông tin
   ngành/khóa đọc từ VNU, snapshot và phiên bản khung hiện tại.
3. Xem ba nhóm môn, lý do còn vướng và chọn kế hoạch mặc định 20 tín chỉ;
   có thể đổi từ 1–30 khi dữ liệu cho phép lập kế hoạch.

Mỗi tài khoản lưu xác nhận riêng. Không có mặc định KHMT K68 cho mọi người;
đổi tài khoản, đăng xuất hoặc phản hồi chậm không khôi phục trạng thái của
tài khoản trước. Ngành nguồn Toán học chưa phân biệt chương trình chuẩn/tài
năng sẽ yêu cầu chọn rõ. Ngành/khóa chưa nhận diện không bị ép vào khung khác.
Ngành/khóa nguồn thay đổi sẽ hủy binding; thay tên hiển thị không hủy binding.

Đã bổ sung quy chế 3626/2022 từ PDF chính thức, với phạm vi và giới hạn được
ghi tại [policies/README.md](policies/README.md). Chỉ mã khớp chính xác, tín chỉ
khớp và các cột điểm nhất quán mới được xác định kết quả. Không tính lại GPA,
không tự gộp mã tương đương/hậu tố hoặc lấy điểm cao nhất khi học lại.

Người dùng xác nhận portal hiện toàn bộ học kỳ, không lọc/phân trang. Bộ đọc
kiểm tra hợp đồng bố cục toàn bảng: vị trí nguồn, vùng bảng, một bảng dữ liệu,
ba lần đọc ổn định, request tải xong và không có lọc/phân trang/hàng ẩn/loading.
Còn hàng chưa hiểu hoặc kiểm tra không đạt thì giữ `completeness=unknown`;
không bỏ cơ chế bảo vệ snapshot cũ khi dữ liệu mới thay đổi mà chưa đầy đủ.

Khi độ đầy đủ, binding và quy chế hợp lệ nhưng còn vài kết quả cần đối chiếu,
bản đồ có thể hiển thị `partial`: các môn đã xác định đạt vẫn xuất hiện màu
xanh; môn chưa rõ không được dùng thỏa tiên quyết. Các môn thuộc quy tắc mặc
định ở đầu tài liệu vẫn có thể chọn khi được phép lập kế hoạch. Mã ngoài khung,
thiếu chọn hướng/nhánh hoặc quy tắc chương trình mâu thuẫn sẽ tạm dừng kế hoạch.
Toán tài năng vẫn dừng kế hoạch do mâu thuẫn chọn hướng trong nguồn; không sửa
PDF để tạo quy tắc. Các API eligibility/recommendation/advisor/progress đầy đủ
vẫn yêu cầu context `ready`, không dùng `partial` để bỏ qua điều kiện này.

API mới: `GET/POST /me/academic-program` và
`GET /academic-policy/vnu-3626-2022`. Lưu binding trong metadata hồ sơ đã có,
không đổi schema, migration hay công bố catalog PostgreSQL mới.

Kiểm chứng đợt này: **495 offline passed / 40 deselected**, **5 PostgreSQL
passed** trên database dùng riêng cho kiểm thử, Ruff và các regression Chrome
nguồn/binding/UI đạt. Ảnh kiểm thử tổng hợp desktop và 390px đã xem. Đây chưa
phải nghiệm thu phân loại bảng điểm thật; cần lần đồng bộ mới của chủ tài khoản.
Chi tiết tại [VNU_PERSONAL_ACADEMIC_2026_10_25.md](VNU_PERSONAL_ACADEMIC_2026_10_25.md).

## Bổ sung tra cứu đầy đủ theo bộ ZIP — 25/10/2026

Mục **Điều kiện học** có hai chế độ:

- **Tra cứu khung chương trình**: dùng được khi chưa đăng nhập, có đủ năm PDF
  trong bộ ZIP người dùng cung cấp: Toán học chuẩn, Toán học tài năng, Toán tin,
  Khoa học máy tính và thông tin, Khoa học dữ liệu. Chọn khóa từ K67 (2022) đến
  khóa tuyển sinh của năm hiện tại. Người dùng đã xác nhận chỉ cần K67 trở đi.
- **Theo bảng điểm VNU**: giữ bảng ba trạng thái và các điều kiện xác minh cá nhân
  mô tả bên dưới. Chọn khung để tra cứu không đổi ngành hồ sơ hoặc tạo binding.

Tra cứu có danh sách học phần, tìm kiếm không dấu, bộ lọc nhóm/loại/tiên quyết,
chi tiết tiên quyết AND/OR, môn có tham chiếu tiếp, các vị trí xuất hiện trong
nguồn và liên kết mở đúng trang PDF. Số liệu và vấn đề của PDF được giữ nguyên;
không tự sửa mã, gộp chương trình hoặc xác nhận quy chế cho các khóa về sau.

Kế hoạch tham khảo mặc định **20 tín chỉ/kỳ**, điều chỉnh **1–30**. Có chọn/bỏ
môn, gợi ý các môn không ghi tiên quyết, kiểm tra tổng tín chỉ ở backend, chỉ
chọn một ngoại ngữ mỗi mức, cảnh báo tiên quyết/nhóm tín chỉ và tải CSV UTF-8.
Môn được chọn không được coi là đã đạt hoặc dùng mở khóa môn cùng kỳ. Kế hoạch
chỉ tồn tại trong phiên trang; thay chương trình/khóa xóa lựa chọn trước đó.
Đây là kế hoạch tham khảo, chưa đối chiếu kết quả học tập hay lịch mở lớp.

Nguồn đọc riêng cho tra cứu: bốn catalog được build từ export đã có trong Git;
Toán tài năng được chép từ PDF 3566, giữ 97 dòng nguồn / 96 mã / tổng 168 tín chỉ.
Tệp mới nằm tại `data/reference_curricula/mathematics_talented_2022.json`.
Tất cả năm PDF đều khớp SHA-256 của các thành viên ZIP; phục vụ file PDF theo
allowlist/hash, không nhận đường dẫn file từ người dùng. Không thay catalog
PostgreSQL, active revisions, schema hoặc dữ liệu cá nhân.

API bổ sung:

```text
GET  /curricula/reference
GET  /curricula/reference/{program_id}?cohort=67
GET  /curricula/reference/{program_id}/source
POST /curricula/reference/{program_id}/plan
```

API kế hoạch chỉ nhận khóa, ngân sách, mã môn dự kiến và yêu cầu gợi ý; từ chối
owner, records, passed set, policy hoặc cờ verified. Response luôn ghi
`mode=reference`, `academic_eligibility=not_evaluated`. Registry HUS runtime vẫn
chỉ có bốn chương trình; việc tra cứu Toán tài năng không công bố catalog mới.

Kiểm chứng mới: **435 offline passed / 39 deselected**, gồm đủ mười ca HUS PDF
acceptance và 19 ca mới cho năm nguồn, inventory Toán tài năng, phạm vi khóa,
hash/PDF, ngân sách và cách ly kế hoạch với kết quả học tập. Chrome regression
mới kiểm tra đủ năm chương trình, đổi khóa, lọc, tiên quyết/PDF, ngân sách,
CSV, phản hồi chậm sau đổi chương trình, Việt/Anh và 1600/390px. Các regression
Chrome bảng ba trạng thái, VNU-only, workspace và charts cũng đạt. Ruff đạt.
Không chạy PostgreSQL hoặc kết nối VNU thật trong đợt bổ sung này.

Sau đó chạy lại toàn bộ regression tra cứu với `--live` trên HTTP backend mới,
cùng regression Chrome portal: đạt. Backend ở cổng 8000 đã được nạp lại;
`/health`, `/ready`, danh mục năm chương trình và API kế hoạch đều trả 200.
Các thay đổi vẫn local, chưa commit/push.

Các giới hạn xác minh cá nhân dưới đây vẫn áp dụng cho chế độ VNU. Các số test
63 và trạng thái UI chỉ có bảng ba màu bên dưới là bằng chứng của đợt trước.

Mục **Điều kiện học** hiển thị ba nhóm:

- **Xanh:** môn đã đạt/được công nhận tín chỉ theo context đã xác minh.
  Môn từng học nhưng chưa đạt không tự động được tô xanh.
- **Vàng:** môn chưa hoàn thành, đủ điều kiện theo catalog. Hiển thị bắt buộc/
  tự chọn, nhóm còn thiếu tín chỉ và lựa chọn cho kế hoạch kỳ tới.
- **Đỏ:** môn chưa thể học, với lý do tiên quyết AND/OR, nguồn chưa xác minh/
  mâu thuẫn, khác hướng/nhánh hoặc nhóm tự chọn đã đủ tín chỉ.

Kế hoạch mặc định **20 tín chỉ**, điều chỉnh từ 1–30. Đây là ngân sách lập kế
hoạch, không phải kết luận về giới hạn đăng ký chính thức. Thứ tự gợi ý xác định:
ưu tiên môn bắt buộc rồi tự chọn, trong ngân sách và hạn mức nhóm. Không cam kết
mọi ngân sách đều được lấp đầy. Người dùng có thể thay đổi các môn đã chọn.
Việc chọn môn không thay đổi bảng điểm, không mở khóa tiên quyết cho môn khác
trong cùng kỳ và không lưu kế hoạch qua lần tải trang. Đổi ngân sách tính lại
lựa chọn; bộ môn đủ điều kiện không thay đổi theo ngân sách đó.

`GET /me/course-status` lấy owner từ session và program từ `academic_binding`
đã được xác minh ở server. Request chỉ nhận ngân sách và hướng/nhánh; không
nhận owner, bảng điểm, môn đã đạt hoặc program do trình duyệt tự gửi. API dùng
chung AcademicContext, rule engine và progress; kiểm tra lại revision/session
trước khi trả kết quả. Khi cần chọn hướng/nhánh, chưa tạo bộ môn/kế hoạch.

**Giới hạn còn tồn tại:** connector vẫn trả completeness chưa xác minh, registry
quy chế production vẫn rỗng và chưa có binding được review cho hồ sơ thật.
Giao diện hiển thị lý do thiếu dữ liệu cùng ba nhóm rỗng, không suy ngành từ tên
hiển thị, không mặc định bảng điểm rỗng và không tự cấp cờ xác minh. Không đổi
schema, cấu hình, dữ liệu cá nhân, catalog hoặc luồng kết nối VNU trong đợt này.
Màu vàng không chứng minh lớp sẽ được mở; catalog vẫn `draft_unverified`.

Kiểm chứng bằng dữ liệu tổng hợp:

```powershell
.venv/Scripts/python.exe -m pytest tests/eligibility tests/integrations/test_academic_api.py tests/integrations/test_academic_context.py -q -p no:cacheprovider --basetemp backups/local_runtime/pytest-course-board-check
.venv/Scripts/python.exe tests/frontend/check_course_status.py
.venv/Scripts/python.exe tests/frontend/check_vnu_only.py
```

Kết quả: **63 passed**, một cảnh báo Starlette/httpx có sẵn; hai lượt kiểm thử
Chrome đạt. Kiểm tra gồm trạng thái tách biệt, tín chỉ bị loại khỏi tổng, hạn
mức tự chọn, không mở khóa bằng môn dự kiến, nguồn/phiên đổi, chống chèn HTML,
tìm kiếm, VI/EN, hai giao diện và chiều rộng 390px. Ruff, cú pháp JavaScript
và `git diff --check` đạt. `/ready` trả 200 sau khi chạy lại server.
Không gọi VNU hoặc kiểm tra dữ liệu sinh viên thật; đây chưa phải nghiệm thu
phân loại trên hồ sơ thật. Chưa commit/push các thay đổi này.
