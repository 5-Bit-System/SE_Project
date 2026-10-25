# Điều kiện học theo bảng điểm VNU

Tích hợp 26/10/2026 từ commit `5e1a9bf` của nhánh
`feat/vnu-curriculum-planning`, trên cơ chế tài khoản/phiên hiện hành của main.

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
Nhóm tự chọn đã đủ yêu cầu không tiếp tục được gợi ý. Kế hoạch tồn tại trong
trang, chưa được lưu qua lần tải lại. Không xác nhận lịch mở lớp hay hạn mức
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

Partial có thể hiển thị các môn đã xác định. Môn chưa rõ không thỏa tiên quyết
hoặc được chọn vào kế hoạch. Mã ngoài khung, thiếu hướng/nhánh hoặc nguồn mâu
thuẫn có thể dừng kế hoạch. API học thuật đầy đủ tiếp tục yêu cầu context ready.
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
