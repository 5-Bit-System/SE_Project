# Kế hoạch học kỳ — 28/10/2026

Tính năng lưu nhiều phương án theo tài khoản trong tab **Điều kiện học**.
Đây là bản nháp cá nhân, không đăng ký môn trên VNU hoặc xác nhận lịch mở lớp.

## Sử dụng

1. Đăng nhập VNU, cập nhật nguồn và xác nhận CTĐT/hướng/nhánh theo luồng hiện có.
2. Chọn môn đủ điều kiện và ngân sách 1–30 tín chỉ. Các môn dự kiến không được
   coi là đã hoàn thành để mở tiên quyết khác trong cùng kỳ.
3. Đặt tên phương án, năm bắt đầu (2026 nghĩa là 2026–2027), chọn học kỳ 1/2/3.
4. Chọn **Kiểm tra và lưu phương án**. Có thể lưu bản nháp chưa chọn môn.
5. Chọn **Phương án mới** để lưu thêm lựa chọn; mở phương án cũ để thêm/bỏ môn
   bằng checkbox hoặc nút Bỏ môn, sửa ngân sách và lưu lại. F5 không xóa bản đã lưu.
6. Xóa phương án có bước xác nhận. Đổi phương án khi có chỉnh sửa chưa lưu cũng
   cần xác nhận. Bản đã bấm Lưu được ghi vào database; chỉnh sửa chưa bấm Lưu
   được giữ tạm trong `sessionStorage` của tab, gắn với account và app session.
   F5 khôi phục tên/học kỳ/ngân sách/hướng/nhánh, bộ lọc và môn đang chọn sau khi
   xác minh phiên ở server. Không lưu điểm, bảng điểm, cookie hay token trong đó.
   Đăng xuất/hết phiên/đổi phiên hoặc tài khoản sẽ xóa bản nháp; không chia sẻ
   bản nháp sang thiết bị khác. Phiên tab kết thúc thì không có bảo đảm khôi phục
   như phương án đã lưu database.

Tối đa 100 phương án/tài khoản. Tên giống nhau được phép, có học kỳ/năm và ID
riêng. Việc chốt chương trình/đủ nguồn theo quy tắc học vụ vẫn bắt buộc. Một số
context partial được phép lập kế hoạch với môn đã xác định; context không đủ
bằng chứng, chưa chọn hướng/nhánh hoặc đang dừng kế hoạch không được lưu mới.

## Khi dữ liệu thay đổi

Kế hoạch lưu code/tên/tín chỉ tại thời điểm lưu, ngân sách, tổng tín chỉ do server
kiểm tra, program/track/path và dấu vết nguồn/catalog/policy/binding. Không lưu
mật khẩu hay cookie. Dấu vết không chứa token phiên: đăng nhập lại không tự làm
kế hoạch lỗi thời. Đồng bộ lại nội dung giống nhau không tạo cảnh báo giả do thời gian.

Mỗi lần đọc danh sách, server đối chiếu dữ liệu hiện tại. Nếu nguồn, catalog,
policy hoặc binding đổi/biến mất, phương án được đánh dấu **cần kiểm tra lại**.
Không tự xóa/chỉnh các môn cũ và không tự xác nhận lại chương trình.
Mở bản cũ vẫn thấy các môn đã lưu; môn không còn đủ điều kiện được đánh dấu.
Bỏ các môn không hợp lệ, đối chiếu phần còn lại rồi lưu để cập nhật dấu vết.
Việc mở bản cũ chỉ kiểm tra nguồn đã lưu trong DB, không tự đăng nhập/lấy điểm VNU.

## API

| Method | Endpoint | Hành vi |
|---|---|---|
| GET | `/me/semester-plans` | Danh sách của tài khoản hiện tại, kèm `needs_review` |
| POST | `/me/semester-plans` | Tạo phương án, trả 201 |
| PUT | `/me/semester-plans/{id}` | Cập nhật, yêu cầu `expected_version` |
| DELETE | `/me/semester-plans/{id}?expected_version=...` | Xóa theo phiên bản |

Body create/update: `title`, `academic_year_start`, `semester`, `max_credits`,
`selected_track_id`, `selected_graduation_path_id`, `course_codes`,
`expected_basis` (từ `/me/course-status.plan_basis`). PUT thêm `expected_version`.
Không nhận owner, tổng tín chỉ, điểm hoặc program từ trình duyệt. Ngành được lấy
qua binding đã xác minh phía server. Tín chỉ và tính hợp lệ được tính lại trong
transaction; request có khóa lạ bị từ chối. Các POST/PUT/DELETE giữ origin/CSRF.

409 `context_changed`: nguồn/basis đã đổi, tải lại trước khi lưu.
409 `semester_plan_conflict`: một tab khác đã sửa bản này, mở lại rồi đối chiếu.
409 `semester_plan_course_unavailable`, `semester_plan_group_full` hoặc
`semester_plan_budget_exceeded`: chọn môn/budget không hợp lệ.
404 trả cho plan không tồn tại hoặc thuộc tài khoản khác. Người khác không đọc
được plan qua danh sách cá nhân hoặc sửa/xóa bằng ID.

## Lưu trữ và triển khai

Migration `hus_20261028_08` tạo `semester_plans`, FK tới UUID của `accounts`.
Dữ liệu học kỳ/ngành/hướng/nhánh/ngân sách/tổng tín chỉ có cột riêng; danh sách
môn và basis là JSONB. Version tăng mỗi lần cập nhật chống ghi đè đa tab.
Transaction khóa account/session → owner → catalog → plan, dùng lại quy trình
kiểm tra tài khoản/link hiện có. Không ghi plan khi phiên đã thu hồi.

Trước triển khai, sao lưu database; chạy trong Conda `SE_Project`:

```bash
python -m database.tools.migrate upgrade
python -m database.tools.migrate current
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Head mong đợi `hus_20261028_08`; tải lại tài nguyên giao diện sau cập nhật.
Migration chưa được agent chạy trên Neon hoặc database chứa dữ liệu người dùng.
Không tự seed, publish catalog hay sửa điểm để bật tính năng.

## Kiểm tra

- `tests/eligibility/test_semester_plan_validation.py`: prerequisites/quota/budget.
- `tests/integrations/test_semester_plans_api.py`: auth/CSRF/body/basis qua phiên mới.
- `tests/integrations/test_semester_plans_store.py`: CRUD, nhiều phương án, quyền
  sở hữu, stale data, phiên bản trên PostgreSQL tạm.
- `python -m tests.frontend.check_semester_plans`: API giả lập, lưu/tải lại,
  nhiều phương án, cảnh báo nguồn thay đổi, VI/EN/mobile và xóa dữ liệu UI khi logout.

## Giữ trạng thái Điều kiện học

Chuyển tab rồi quay lại dùng bảng đã đọc trong bộ nhớ nếu snapshot và hồ sơ
không đổi. Các event hồ sơ lặp lại không xóa lựa chọn. Sau F5, app xác minh
phiên và đọc lại API học vụ một lần để không dùng kết quả cũ; bản nháp và bộ
lọc vẫn được khôi phục. Thao tác này không tự đăng nhập lại VNU. Khi nguồn thật
sự đổi, tải lại bảng và giữ bản nháp để người dùng đối chiếu; save vẫn kiểm tra
server theo nguồn hiện tại. Trình duyệt chặn sessionStorage vẫn dùng được bản
nháp trong bộ nhớ, nhưng không bảo đảm giữ qua F5.

Khi F5, màn hình dùng trạng thái “Đang khôi phục phiên đăng nhập…” trong lúc
chờ `/auth/session`; không nháy form đăng nhập trước khi nhận được kết quả.
Phiên hợp lệ chuyển thẳng vào workspace; hết phiên hoặc lỗi thì mới hiện form
và thông báo tương ứng. `tests/frontend/check_session_restore.py` kiểm tra
phản hồi chậm, reload, hết phiên và lỗi bằng API giả lập.
