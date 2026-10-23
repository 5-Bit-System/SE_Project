# Module 09 — Kết nối cổng đào tạo và lấy bảng điểm

Cập nhật chốt phiên: 23/10/2026. **Hiện trạng:** connector chọn lọc từ
`origin/feat/login` tại `b790d6a` đã tích hợp local với UI/API và PostgreSQL;
người dùng xác nhận đăng nhập và thấy bảng điểm. **Họ tên/ngành/khóa vẫn trống
dù đã đăng nhập lại; lỗi CHƯA GIẢI QUYẾT.** Các sửa parser/lưu/hiển thị và đọc
sớm `default.asp` mới qua kiểm thử tổng hợp, chưa khớp nguồn thật được xác minh.
Xem [bàn giao lỗi và bước tiếp theo](../docs/PORTAL_INTEGRATION_STATUS_2026_10_23.md).
Không coi module hoàn tất hoặc quy lỗi cho việc chỉ F5. Không commit/push.
**Người phụ trách connector ban đầu:** bạn của người dùng; tiếp tục tái sử dụng
connector, không triển khai lại đăng nhập mặc định.

[Kế hoạch tích hợp chi tiết](../docs/KE_HOACH_TICH_HOP_PORTAL_BANG_DIEM_2026_10_23.md): người dùng đã chốt localhost trước, đợt đầu có profile và lưu bảng điểm nguồn theo tài khoản vào PostgreSQL; chưa review/apply vào gợi ý. Đăng nhập bằng VNU, không tạo mật khẩu riêng; chỉ cấp phiên web sau xác thực thành công và không lưu mật khẩu VNU. Yêu cầu lưu profile này thay thế giới hạn chỉ dùng dữ liệu portal trong phiên; cookie VNU vẫn không lưu lâu dài. Phiên thử thành công không thay thế nghiệm thu độ đầy đủ, nhiều tài khoản hoặc CAPTCHA/OTP.

## Trách nhiệm

Nhận thao tác chủ động của sinh viên, đăng nhập cổng đào tạo và lấy bảng điểm trong phiên tạm. Người phụ trách khảo sát URL, API/HTTP/browser automation, SSO/CAPTCHA/OTP và định dạng dữ liệu. Hệ thống chính phát triển bằng mock contract trước khi connector sẵn sàng.

Không trực tiếp cập nhật transcript đang dùng, tính GPA, quyết định eligibility hoặc đăng ký/hủy môn. OCR bảng điểm không nằm trong phạm vi.

## Hợp đồng bàn giao dự kiến

Đầu vào: yêu cầu kết nối/ngắt kết nối, phiên người dùng và thông tin xác thực qua giao diện được thiết kế phù hợp. Tạo định danh profile đã xác minh để sở hữu dữ liệu lưu; dùng đăng nhập VNU, không tạo mật khẩu Sổ học tập riêng.

Đầu ra cho module 02:

- Import/session ID không chứa credentials, thời điểm lấy và phiên bản connector/schema.
- Ngành, khóa, phiên bản chương trình nếu nguồn có; null khi chưa biết.
- Từng lần học: mã/tên môn, tín chỉ nguồn, học kỳ/năm, điểm số/điểm chữ, trạng thái và locator bản ghi nguồn.
- GPA portal nếu có, nhãn nguồn rõ, không thay bằng GPA tự tính.
- Các trường thiếu, mức đầy đủ/phân trang và lỗi có cấu trúc: cần tương tác, sai xác thực, hết phiên, timeout, nguồn đổi, dữ liệu thiếu.

Tên trường/route và cơ chế gọi phải chốt bằng schema cùng mẫu đã ẩn danh với người phụ trách. Contract không phải API đang hoạt động.

## Phiên và credentials

Chỉ kết nối host portal/SSO và redirect đã review. Không gửi mật khẩu tới URL tùy ý. Mật khẩu không lưu database, browser storage, log, trace, prompt hoặc corpus; bảng accounts.password_hash không phải nơi lưu mật khẩu portal.

Cookies/token giữ tạm phía server, tách từng người dùng, có TTL và hủy khi disconnect. Không dùng cookie jar chung hoặc tự reconnect bằng mật khẩu lưu sẵn. CAPTCHA/OTP/SSO tương tác cần cơ chế người dùng hoàn thành được hỗ trợ; không giả định username/password là đủ.

Không chuyển HTML thô, tên/MSSV hoặc token sang LLM. Chỉ lấy dữ liệu của sinh viên đã chủ động kết nối, không ghi dữ liệu lên cổng.

## Kế hoạch và tiêu chí nghiệm thu

1. Bàn giao schema, mock adapter và mẫu ẩn danh bao gồm học lại/thiếu điểm/phân trang.
2. Kiểm tra sai xác thực, cần tương tác, hết phiên, timeout, hủy và nguồn thay đổi.
3. Hai người dùng không dùng chung phiên, cookies, draft hoặc bảng điểm.
4. Lỗi/hủy không đổi transcript đã áp dụng; response muộn sau đổi ngành/phiên bị loại khi tích hợp.
5. Tích hợp thật chỉ kiểm tra khi connector sẵn sàng và có tài khoản thử nghiệm được phép; không ghi credentials vào bằng chứng.

Liên quan: [02 Transcript](02-transcript-profile.md), [07 API](07-recommendation-api.md), [08 Web](08-web-ui.md).
