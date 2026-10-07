# Module 05 — Giao diện và thử tình huống (what-if)

**Use case:** UC01, UC02, UC03, UC06, UC07

**Trạng thái:** giao diện trong `app/static/` đã chọn ngành, đánh dấu môn đã qua, nhập mục tiêu/TC và hiển thị kết quả. Chưa có bảng so sánh hai tình huống hay lý do môn bị loại.

## Mục tiêu

Làm luồng demo dễ hiểu cho sinh viên: chọn **một** ngành, khai báo môn đã qua, nhập mục tiêu, xem gợi ý có lý do/cảnh báo và thử thay đổi đầu vào để so sánh. UI không được che trạng thái catalog nháp.

## Đầu vào và đầu ra

- Đầu vào: thao tác của sinh viên và response từ API chương trình, danh sách môn, gợi ý.
- Đầu ra: hồ sơ gửi tới API và màn hình danh sách môn/lý do/cảnh báo.
- What-if lưu tạm hai tình huống trong trình duyệt và gửi lại yêu cầu; không sửa dữ liệu chương trình.

## Thành phần triển khai

- `app/static/index.html`, `app/static/app.js`, `app/static/styles.css`.
- Test UI/checklist demo. Endpoint/schema nằm trong Module 02 (`app/main.py`, `app/models.py`, `app/service.py`); UI sử dụng hợp đồng API, không truy cập JSON trên server trực tiếp.

## Chức năng cần đáp ứng

1. Hiển thị rõ tên, mã ngành, trạng thái `draft_unverified`/`verified`, số môn; catalog rỗng cần thông báo chưa có dữ liệu, không hiện gợi ý giả.
2. Khi đổi ngành, bỏ các môn đã chọn của ngành trước và tải lại danh sách; kết quả cũ cũng phải xóa. Chỉ gửi `program_id` hiện tại và mã môn của ngành đó.
3. Cho nhập mục tiêu, giới hạn TC; kiểm tra đầu vào cơ bản và hiển thị lỗi 404/422 thân thiện. Sau khi API trả kết quả, hiện mã, tên, TC, lý do và cảnh báo; không dùng HTML không an toàn từ chuỗi LLM.
4. Thêm what-if: lưu tạm tình huống A trên trình duyệt, thay mục tiêu hoặc môn đã qua để chạy B, hiển thị điểm khác nhau (môn thêm/bớt hoặc thứ tự đổi). Không ghi thay đổi vào catalog.
5. Khi Module 03 có mã lý do môn bị loại, thêm vùng xem lý do; nếu API chưa hỗ trợ thì chờ hợp đồng được chốt, không giả lập lý do trong JavaScript.

## Đầu ra và nghiệm thu

- Demo chọn hai ngành liên tiếp không lẫn môn đã qua/kết quả; catalog rỗng có cảnh báo; API lỗi không làm vỡ trang; giao diện dùng được ở màn hình điện thoại.
- Test hoặc checklist có ảnh/chụp màn hình cho ba ca: bình thường, ngành chưa có môn, what-if. `python -m pytest -q` vẫn đạt.
- Bản nền dùng HTML/CSS/JavaScript, không cần framework frontend lớn để đáp ứng các màn hình trong phạm vi hiện tại.

## Ranh giới

Module này gọi API của Module 02; có thể dùng mock response để kiểm thử độc lập với backend. Mock chỉ dùng thử, không trở thành catalog của người dùng.

UI chỉ trình bày kết quả backend. Không tính tiên quyết hay quota ở client làm nguồn sự thật; không tự tạo môn hoặc lý do học vụ.
