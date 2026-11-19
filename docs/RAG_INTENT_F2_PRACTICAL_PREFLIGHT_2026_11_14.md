# Kiểm thực tế ý định/F2 — gói đã tiền kiểm, chưa gọi Gemini

**Cập nhật sau tiền kiểm:** người dùng đã cấp budget12 call mới; lượt live đã
kết thúc với11 call,6 đáp án dùng model/1 lỗi/1 cần làm rõ/4 control.
[Kết quả live riêng](RAG_INTENT_F2_PRACTICAL_LIVE_2026_11_14.md). Phần bên dưới và
artifact tiền kiểm giữ nguyên trạng thái lịch sử, không thay bằng kết quả live.

Đã chuẩn bị **12 câu trên cả bốn ngành**:8 câu F2 và4 control. Luồng thật của
backend/JSON validator/adapter được chạy với provider giả lập; **Google0**, chưa
được cấp budget live mới. Đây là câu do Codex(AI) soạn, có cách hỏi đã dùng trong
regression; chưa là câu nhóm tự viết hoặc đánh giá độc lập.

Gói: [cases](../data/hus/evaluation/intent_f2_student_20261114_r1/cases.json),
[preflight/pins](../data/hus/evaluation/intent_f2_student_20261114_r1/preflight.json),
[prompt dự kiến](../data/hus/evaluation/intent_f2_student_20261114_r1/planned_calls.json),
[đáp án/nguồn offline](../data/hus/evaluation/intent_f2_student_20261114_r1/offline_observations.json),
[CSV nhóm điền bản riêng](../data/hus/evaluation/intent_f2_student_20261114_r1/review_template.csv).

## Câu hỏi và kỳ vọng trước live

Phiên bản tương ứng: Toán học QD3565-2023, Toán tin QD3567-2023,
KHMTTT QD3568-2023, KHDL QD3569-2023; cùng snapshot `hus-data-20261111-v4`.
Số môn bên dưới là mã duy nhất trong danh mục theo phiên bản, **không là số môn
mỗi sinh viên phải học** và không xác nhận hiệu lực học vụ hiện tại.

| ID | Ngành chọn | Câu hỏi | Kỳ vọng theo F2/guard | Call tối đa |
| --- | --- | --- | --- | --- |
|001 |Toán học |Ngành Toán học có bao nhiêu môn học? |90 mã danh mục |1 diễn đạt |
|002 |Toán học |Cho mình xem toàn bộ danh sách học phần |Đủ90 mã/tên môn |1 hiểu +1 diễn đạt |
|003 |Toán tin |Liệt kê các môn trong chương trình |Đủ68 mã/tên môn |1 diễn đạt |
|004 |Toán tin |Đếm học phần giúp tôi |68 mã danh mục |1 hiểu +1 diễn đạt |
|005 |KHMTTT |Ngành khoa học máy tính có bao nhiêu môn học? |67 mã danh mục |1 diễn đạt |
|006 |KHMTTT |MAT1204 được tính mấy TC? |3 tín chỉ theo nguồn |1 hiểu +1 diễn đạt |
|007 |KHDL |Liệt kê các môn trong chương trình |Đủ65 mã/tên môn |1 diễn đạt |
|008 |KHDL |MAT3533 được tính mấy TC? |3 tín chỉ theo nguồn |1 hiểu +1 diễn đạt |
|009 |KHDL |Ngành khoa học máy tính có bao nhiêu môn học? |Yêu cầu chọn KHMTTT trước |0 |
|010 |Toán học |Ngành Toán học phải học bao nhiêu môn? |Làm rõ, không lấy90 làm số môn phải học |0 |
|011 |KHDL |Nội dung MAT3533? (chưa bật F3) |Yêu cầu quyền F3, không lấy nội dung AI |0 |
|012 |KHDL |MAT9999 có bao nhiêu tín chỉ? |Không có môn trong phạm vi, không đoán |0 |

Các số90/68/67/65 và3 tín chỉ được đối chiếu với các record F2 đúng scope, không
lấy từ menu. Danh sách đủ mã/tên và citation/locator/review có trong file đáp án
offline. CSV không điền người/ngày hoặc kết quả live giả.

## Đề nghị budget live — chờ xác nhận mới

- Tối đa **12 Google call** cho8 câu:4 hiểu ý định và8 diễn đạt;4 control không gọi.
- Model `gemini-3.5-flash-lite`, không đổi model, không retry; cách ít nhất5 giây
  giữa thời điểm bắt đầu các call, gồm hai call trong cùng câu.
- Tổng prompt dự kiến **64.137 ký tự công khai**; tối đa1.024 output token/call,
  tối đa12.288 output token. Input token và chi phí thực chưa biết; không gọi
  tokenizer/model-list/smoke để ước tính.
- Dừng gọi tiếp sau401/403/429 hoặc hai503 liên tiếp. Nếu JSON ý định bị chặn
  hoặc model yêu cầu làm rõ, không ép sang đáp án kỳ vọng; có thể dùng ít call hơn.
- Key chỉ do backend dùng trong bộ nhớ sau khi được phép chạy; không in/lưu key,
  body lỗi hoặc text bị validator từ chối. Không đổi key/billing/cấu hình mặc định.
- Kiểm pins trước chạy, tạo thư mục kết quả live mới. Không sửa pack này hoặc
  run/gold/review cũ để khớp kết quả mới. Code thay đổi thì prepare revision mới.

F2 tra/tính trực tiếp từ cấu trúc; lượt này không gọi vector và không đánh giá
hybrid/ChromaDB/latency embedding. Budget gồm hai giai đoạn nhưng không cam kết
model sẽ hiểu đúng: intent giả lập trong tiền kiểm được chọn theo kỳ vọng.

## Nhóm cần đọc gì?

Sao chép CSV thành bản trả riêng, ghi người/ngày. Đọc đúng câu và scope; kiểm
count/list với record nguồn, tín chỉ, citation và cảnh báo. Với control, kiểm
phản hồi làm rõ/từ chối có hợp lý; mục không áp dụng ghi N/A.

Khi có live, ghi riêng `interpretation.used/model/prompt_sha256/usage` và
`generation.used/model/prompt_sha256/usage`, số call, latency và lỗi từng giai
đoạn. Không lấy `interpretation.used=true` làm bằng chứng đáp án cuối đã dùng
Gemini. Model F2 chỉ chọn cách trình bày; số liệu/danh sách vẫn do backend giữ.

429 mới cho phép đường offline; lỗi khác báo lỗi theo profile hiện tại. Đọc cả
đáp án offline/clarification nếu có. `used=true`, schema đúng và tiền kiểm đạt
không thay việc nhóm đọc nội dung. **Hiện review người thật và live đều pending.**

[Kế hoạch tiến độ](RAG_PROGRESS_AND_NEXT_PLAN.md)
