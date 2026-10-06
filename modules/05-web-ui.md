# Module 05 — Giao diện và thử tình huống (what-if)

**Nhánh:** `feat/ui`

**Use case:** UC01, UC02, UC03, UC06, UC07

**Trạng thái:** giao diện trong `app/static/` đã chọn ngành, đánh dấu môn đã qua, nhập mục tiêu/TC và hiển thị kết quả. Chưa có bảng so sánh hai tình huống hay lý do môn bị loại.

## Mục tiêu

Làm luồng demo dễ hiểu cho sinh viên: chọn **một** ngành, khai báo môn đã qua, nhập mục tiêu, xem gợi ý có lý do/cảnh báo và thử thay đổi đầu vào để so sánh. UI không được che trạng thái catalog nháp.

## File phụ trách

- `app/static/index.html`, `app/static/app.js`, `app/static/styles.css`.
- Test UI/checklist demo. Module 02 phụ trách endpoint/schema trong `app/main.py`, `app/models.py`, `app/service.py`; trao đổi yêu cầu UI với người đó trước khi đổi hợp đồng.

## Việc cần làm

1. Hiển thị rõ tên, mã ngành, trạng thái `draft_unverified`/`verified`, số môn đã nhập; catalog rỗng cần thông báo việc nhóm phải nhập dữ liệu, không hiện gợi ý giả.
2. Khi đổi ngành, bỏ các môn đã chọn của ngành trước và tải lại danh sách; kết quả cũ cũng phải xóa. Chỉ gửi `program_id` hiện tại và mã môn của ngành đó.
3. Cho nhập mục tiêu, giới hạn TC; kiểm tra đầu vào cơ bản và hiển thị lỗi 404/422 thân thiện. Sau khi API trả kết quả, hiện mã, tên, TC, lý do và cảnh báo; không dùng HTML không an toàn từ chuỗi LLM.
4. Thêm what-if: lưu tạm tình huống A trên trình duyệt, thay mục tiêu hoặc môn đã qua để chạy B, hiển thị điểm khác nhau (môn thêm/bớt hoặc thứ tự đổi). Không ghi thay đổi vào catalog.
5. Khi Module 03 có mã lý do môn bị loại, thêm vùng xem lý do; nếu API chưa hỗ trợ thì chờ hợp đồng được chốt, không giả lập lý do trong JavaScript.

## Đầu ra và nghiệm thu

- Demo chọn hai ngành liên tiếp không lẫn môn đã qua/kết quả; catalog rỗng có cảnh báo; API lỗi không làm vỡ trang; giao diện dùng được ở màn hình điện thoại.
- Test hoặc checklist có ảnh/chụp màn hình cho ba ca: bình thường, ngành chưa có môn, what-if. `python -m pytest -q` vẫn đạt.
- PR không đưa thư viện frontend lớn vào nếu chưa trao đổi với nhóm; bản nền hiện chỉ cần HTML/CSS/JavaScript.

## Ranh giới

Người nhận module còn nhập và review lô dữ liệu theo [bản phân công](../docs/PHAN_CHIA_CONG_VIEC.md). Có thể phát triển UI bằng mock response trong lúc chờ các module backend; mock chỉ dùng thử, không trở thành catalog của người dùng.

UI chỉ trình bày kết quả backend. Không tính tiên quyết hay quota ở client làm nguồn sự thật; không tự tạo môn hoặc lý do học vụ.
