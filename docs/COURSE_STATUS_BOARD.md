# Điều kiện học theo bảng điểm VNU

Tích hợp 26/10/2026 từ commit `5e1a9bf` của nhánh
`feat/vnu-curriculum-planning`, trên cơ chế tài khoản/phiên hiện hành của main.

## Cập nhật bản đồ — 31/10/2026

Theo yêu cầu mới của người dùng, quy tắc hiển thị bên dưới thay thế mặc định
ngày 28/10 cho ba cột trên bản đồ:

- Bỏ checkbox “Chọn cho kế hoạch kỳ tới” trên các thẻ học phần.
- Ẩn mọi môn không tính vào tín chỉ tích lũy khỏi cả ba cột và số đếm/tìm kiếm.
  Áp dụng cả cờ của môn và danh sách loại trừ của chương trình. Bảng điểm nguồn
  và cách tính tín chỉ đã hoàn thành giữ nguyên.
- Nếu mọi mệnh đề tiên quyết còn thiếu đều có một lựa chọn trong nhóm **Có thể
  học**, đưa môn nối tiếp vào cùng nhóm, lặp đến khi không còn môn mới. Điều
  kiện AND/OR được giữ nguyên; vòng lặp không có môn đầu vào không tự mở khóa.
  Thẻ ghi rõ tiên quyết cần hoàn thành trước, không coi các môn đó là đã đạt.
- Tiên quyết hiển thị dạng **mã môn: tên môn**, tên được in đậm, trong cả nhóm
  Có thể học và Chưa thể học. Tra tên theo đúng catalog hiện tại kể cả khi môn
  đó không hiện trong ba cột/tìm kiếm; hỗ trợ tên tiếng Anh nếu có. Mã ngoài
  catalog chưa có tên vẫn giữ nguyên mã, không suy đoán hoặc tạo tên giả.
- Các lý do chặn khác (nguồn/tiên quyết chưa rõ, hướng/nhánh, nhóm tự chọn đã
  đủ tín chỉ) vẫn được giữ. Khóa kế hoạch toàn cục vẫn có hiệu lực.
- Việc tạm dừng kế hoạch hoặc kết quả của chính môn còn chờ đối chiếu không
  được đẩy môn đã thỏa tiên quyết sang nhóm đỏ. Khôi phục những môn này vào
  nhóm vàng trước, rồi mới lan truyền sang các môn được chúng làm tiên quyết.
  Chỉ khóa thao tác lập/lưu kế hoạch tương ứng; không coi môn là đã hoàn thành.

`course_board_display()` chỉ chiếu kết quả cho `/me/course-status`; bộ phân loại
gốc và các API eligibility/progress/recommendation vẫn dùng điểm đạt thực tế.
Môn nối tiếp được đánh dấu `eligibility_basis=available_prerequisites`, có
`prerequisite_clauses`. Môn chỉ bị chặn bởi đối chiếu kế hoạch có
`eligibility_basis=completed_prerequisites`. Cả hai loại hiển thị bổ sung có
`planning_eligible=false`, không tự được gợi ý hay chấp nhận lưu cùng kỳ khi
điều kiện lập kế hoạch chưa đủ. Gợi ý mặc định 20 tín chỉ vẫn điều chỉnh được;
phương án lưu sẵn tiếp tục mở, bỏ môn, lưu và xóa như trước. Môn bị ẩn không
còn nằm trong gợi ý mới của bản đồ; không xóa nội dung phương án cũ trong DB.

## Mặc định môn có thể học — 28/10/2026 (lịch sử)

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

### Bản xem trước khi metadata chưa xác minh

Nếu bảng điểm đã được lấy đầy đủ, ngành/khóa và quy chế đã được xác nhận nhưng
catalog hoặc metadata môn còn `draft_unverified`, **Điều kiện học** vẫn hiển thị
bản đồ xem trước từ các dữ liệu hiện có. Kết quả xanh/vàng trong bản này là tạm
tính; kết quả học chưa rõ không mở khóa môn khác. Tiến độ được ghi là tạm tính.
Kế hoạch, checkbox chọn môn và thao tác lưu phương án bị khóa cho đến khi
catalog, thông tin môn và tiên quyết được xác minh. Các API eligibility,
recommendation, advisor và academic-progress vẫn giữ kiểm tra nghiêm ngặt.

Preview không thay đổi bảng điểm, trạng thái xác minh hay catalog đã xuất bản.
Nếu nguồn bảng điểm chưa đầy đủ, chưa xác nhận đúng ngành/khóa hoặc chưa có quy
chế áp dụng, màn hình tiếp tục yêu cầu xử lý điều kiện đó trước khi hiển thị.

Phân loại tách khỏi việc lập kế hoạch: nếu còn thiếu chọn hướng/nhánh, có mã
ngoài khung hoặc quy tắc chương trình chưa rõ, các môn mặc định vẫn hiện màu
vàng nhưng kế hoạch tạm dừng, không tự chọn môn và khóa checkbox. Khi được
phép lập kế hoạch, vẫn mặc định 20 tín chỉ, tổng tải học tính cả tín chỉ môn
ngoại khóa đã chọn; các môn bị loại trừ vẫn không cộng vào tín chỉ tích lũy.


## Luồng sử dụng

1. Đăng nhập VNU như hiện tại; mở **Điều kiện học**.
2. Nếu nguồn chưa đủ bằng chứng, chọn **Cập nhật bảng điểm VNU**. Luồng dùng lại
   phiên nguồn hiện có; chỉ yêu cầu xác thực lại khi phiên VNU không còn hiệu lực.
3. Đối chiếu và xác nhận ngành/khóa từ hồ sơ VNU cho tài khoản hiện tại.
4. Chọn hướng/nhánh tốt nghiệp nếu chương trình yêu cầu, rồi xem ba nhóm môn:
   đã hoàn thành, đủ điều kiện và bị chặn cùng lý do.
5. Lập kế hoạch mặc định 20 tín chỉ, điều chỉnh 1–30. Chọn môn không làm môn
   đó trở thành đã đạt để mở tiên quyết khác trong cùng kỳ.

Ngân sách chỉ giới hạn bộ môn dự kiến, không thay đổi tập môn đủ điều kiện.
Nhóm tự chọn đã đủ yêu cầu không tiếp tục được gợi ý. Kế hoạch có thể lưu thành nhiều phương án theo tài khoản; xem
[SEMESTER_PLANS.md](SEMESTER_PLANS.md). Bản chưa lưu vẫn chỉ tồn tại trên trang. Không xác nhận lịch mở lớp hay hạn mức
đăng ký chính thức của nhà trường.

## Phạm vi

Dùng bốn catalog HUS hiện có. Không bổ sung màn hình tra cứu công khai, xuất
CSV hoặc catalog Toán tài năng trong lần tích hợp này. Tên ngành Toán học chưa
phân biệt hệ không được tự chọn khung; người dùng chỉ xác nhận nếu thuộc khung
chuẩn đang được hỗ trợ. Các trường hợp chưa nhận diện phải chờ đối chiếu.

Giữ đăng nhập sinh viên VNU, admin, quyền sở hữu một–một, app session trong
PostgreSQL, VNU cookies trong RAM, resume/reauth và nhắc đồng bộ 7 ngày.
Dashboard, biểu đồ và trang gợi ý hiện tại giữ hành vi riêng; luồng mới không
kích hoạt RAG, what-if hoặc cho phép điểm do trình duyệt tự khai báo.

## Nguồn và phân loại

Bộ đọc kiểm tra nguồn HTTPS/host/path/container, đúng một bảng, ba lần đọc ổn
định, không còn request và không có phân trang/lọc hạn chế/hàng ẩn/virtualized/
loading/hàng chưa hiểu. Chỉ tùy chọn đã nhận diện “Xem cả các/những môn …” có
handler submit_d được dùng để yêu cầu chế độ đầy đủ. Mọi kiểm tra không đạt
giữ completeness unknown; snapshot cũ không được tự nâng cờ.

Policy điểm có phiên bản và nguồn [3626/2022](policies/README.md). Mã môn phải
khớp chính xác, tín chỉ/điểm phải nhất quán. Các trường hợp chưa rõ như tương
đương khác mã, miễn/chuyển đổi hay học lại không được hỗ trợ vẫn chờ đối chiếu.
Không sửa điểm nguồn hoặc tính lại GPA của VNU.

Các catalog vẫn draft_unverified; chưa đối chiếu mọi sửa đổi theo từng khóa.

## API và lưu trữ

```text
GET  /me/academic-program
POST /me/academic-program
GET  /me/course-status?max_credits=20
GET  /academic-policy/vnu-3626-2022
```

Các API cá nhân dùng app session hiện tại; POST có origin và CSRF. Request
không nhận owner/điểm/passed set/cờ verified. Xác nhận dùng digest snapshot,
source_scope và catalog revision để chống phản hồi cũ.

Binding có phiên bản cấu trúc, lưu tại portal_users.profile.academic_binding.
Transaction kiểm tra account/session/link rồi khóa owner; không ghi nếu phiên
bị thu hồi hoặc nguồn thay đổi. Xác nhận không thay thời gian đồng bộ.
Đồng bộ giữ binding khi ngành/khóa giữ nguyên, hủy khi enrollment đổi; chỉ đổi
tên không hủy. Hàm lưu bảo toàn đồng thời binding và _last_synced_at.

Không có migration mới, không đổi bốn active catalog hoặc seed tài khoản.
Chỉ lần đọc nguồn mới mới lưu thêm snapshot/evidence qua bảng portal hiện có.
Chẩn đoán lần đọc bị từ chối nằm trong session RAM, tách khỏi snapshot được giữ,
chỉ gồm cờ kỹ thuật/số lượng và bị xóa khi thu hồi phiên.
