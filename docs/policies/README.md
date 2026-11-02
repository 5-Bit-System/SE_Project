# Quy chế đánh giá kết quả học tập VNU 3626/2022

Nguồn PDF chính thức (truy cập 25/10/2026):
[website ĐH KHXH&NV – ĐHQGHN](https://ussh.vnu.edu.vn/vi/van-ban/detail/Quy-che-dao-tao-dai-hoc-tai-Dai-hoc-Quoc-gia-Ha-Noi-Ap-dung-tu-khoa-QH-2022-X-19452/?download=1&id=0).
Danh mục [quy chế đại học HUS](https://hus.vnu.edu.vn/tai-lieu-bieu-mau/quy-dinh-quy-che/dao-tao/dai-hoc)
cũng dẫn Quyết định 3626 ngày 21/10/2022. Bản PDF 52 trang được lưu nguyên bản
tại `vnu_3626_2022.pdf`, SHA-256
`244addf2f614dec7a8804264a5ac966c3785bc7a49d8f23daf1069df05298f93`.

Phần được triển khai trong `app/academic_policies.py`:

- Điều 41(2), trang PDF 42–43: các mức A+, A, B+, B, C+, C, D+, D, F;
  D từ 4,0 là mức đạt; P là đạt không phân mức, từ 5,0. I/X là điểm chưa đủ.
- Điều 43(1), trang PDF 45: dùng hệ 4 có sẵn trong nguồn để kiểm tra tính nhất
  quán với điểm chữ/hệ 10. Không tính lại GPA hoặc sửa các cột điểm nguồn.
- Điều 21(4–5), trang PDF 19: học lại F và cải thiện D/D+. Chỉ khi cùng mã,
  tín chỉ khớp, mọi cột điểm cuối cùng đều nhất quán và học kỳ được xác định
  rõ, kết quả công bố ở kỳ sau được dùng thay kết quả F/D/D+ trước đó. Không
  lấy điểm cao nhất. Cách hiểu một hàng điểm cuối cùng công bố ở kỳ sau là bằng
  chứng lần học được tiếp nhận là **quy tắc diễn giải của connector**, có phiên
  bản; nguồn thiếu kỳ, trùng kỳ, điểm chờ hoặc chuỗi cải thiện ngoài F/D/D+
  vẫn cần review. Không xử lý tự động thay thế bằng một mã môn khác.
- Điều 51, trang PDF 52: phạm vi khóa tuyển sinh từ 2022; ứng dụng tương ứng
  K67 trở đi. Nguồn/cohort và chương trình vẫn phải được chủ tài khoản xác nhận.

Các phần chưa tự quyết định: R/miễn/chuyển đổi không có đủ căn cứ, mã có hậu tố,
tương đương khác mã, điều kiện tốt nghiệp hoặc hiệu lực các văn bản sửa đổi
chưa được đối chiếu. PDF này không thay việc xác nhận tính áp dụng CTĐT.
Đợt tích hợp hiện tại chỉ dùng bốn catalog HUS đang có. Toán tài năng và các
phần tra cứu mở rộng của nhánh nguồn chưa được đưa vào runtime này.

Độ đầy đủ của bảng điểm là điều kiện riêng: không suy từ tổng tín chỉ, số hàng,
ngành/khóa hoặc một checkbox. Bộ đọc kiểm tra bố cục toàn bảng do người dùng
quan sát/xác nhận ngày 25/10/2026: HTTPS, đúng host/path/container, đúng một
bảng, ba lần đọc liên tiếp ổn định, không còn request đọc dữ liệu, không có lọc
hạn chế bản ghi/phân trang/hàng ẩn/virtualization/loading và không còn hàng chưa
hiểu. Chẩn đoán thực sau đó phát hiện checkbox mặc định tắt, nhãn bắt đầu bằng
“Xem cả môn …”, handler `submit_d`, ở ngoài bảng. Bộ đọc chọn đúng tùy chọn nguồn
này để yêu cầu toàn bộ các lượt học; chỉ khi checkbox đó đang bật mới coi là
không hạn chế bản ghi. Checkbox/bộ lọc khác vẫn chưa được tự bỏ qua. Module nằm
trong namespace `/ListPoint/`, được đối chiếu với menu VNU đã mở và cùng HTTPS
host; không tự gọi URL suy đoán. Không thay đổi điểm hoặc hồ sơ sinh viên.
Đây là hợp đồng cho bố cục portal hiện tại, không chứng nhận mọi bố cục VNU
trong tương lai. Bất kỳ kiểm tra nào không đạt đều giữ `completeness=unknown`
và không được ghi đè snapshot cũ khi dữ liệu thay đổi.
