# F1 — scope nguồn và cách đóng băng gold cho cohort tiếp theo

Áp dụng cho cohort mới sau sửa scope/assessment ngày13/11/2026. Không chấm lại
run/gold/review cũ hoặc xác nhận hiệu lực học vụ từ quy tắc này.

## Câu chọn nguồn/edition/hệ

- Decision selector F2/F3 (`QD…`) không tự xác định edition F1. Câu hỏi phải
  nêu edition F1 và hệ khi cần ràng buộc đó; dữ kiện nguồn ghi unknown giữ unknown.
- CLC/hệ chất lượng cao là ràng buộc `high_quality`; không bỏ qualifier để
  lấy nguồn standard/unknown. Metadata scope xác định hệ/edition, body phải
  hỗ trợ các dữ kiện/năng lực/chủ đề được hỏi; title không thay bằng chứng.
- Gold ghim một nhóm nguồn cùng major/field/edition/hệ/source identity, gồm
  mọi đoạn cần để trả đủ ý. Không nối các edition/hệ hoặc nguồn khác nhau
  thành một danh sách mà không ghi rõ từng nguồn.
- Nếu source identity không được phân biệt chỉ bằng edition/hệ, tác giả phải
  nêu mô tả nguồn phù hợp trong câu hoặc đánh dấu phạm vi gold cần review
  trước inference. Không tự thêm hint chunk ID cho runtime.

## Câu rộng không chọn nguồn

- Chọn và ghi trước inference liệu câu được chấm theo một nguồn xác định hay
  một tập nguồn thay thế đã review. Câu có nhiều nguồn khác nội dung nhưng
  chỉ ghim một target không được mặc nhiên coi là kiểm bao phủ mọi nguồn.
- Nếu dùng nguồn thay thế, liệt kê sẵn từng source identity/scope/hash và các
  ý cần có của mỗi nhánh. Đánh giá exact output dựa trên nhánh đã chọn và
  yêu cầu thực của câu hỏi; không bổ sung nhánh sau khi xem prediction.
- Không tự coi tên lĩnh vực là tương đương. “Toán ứng dụng” không tự chứng
  minh bao phủ “Cơ sở toán học cho Tin học”. Muốn công nhận ánh xạ đó cần
  reviewer chuyên môn/độc lập ghi nhận, không dùng AI tự ký thay.
- Giữ điều kiện học tiếp trong nguồn, citation/scope/review/cảnh báo; không
  biến lời mô tả thành xác nhận sinh viên đủ điều kiện hay nguồn còn hiệu lực.

## Áp dụng với A7F-Q003 và phép đo mới

Q003 cũ không ghim edition; output DOCX2023 giữ entailment pass nhưng không
chứng minh đủ target web. **Giữ completeness fail và điểm34/36 cũ**; không
đổi ranking/target/gold để đạt. Cohort kế tiếp ưu tiên câu source-scoped với
edition/hệ rõ và gold trích trực tiếp từ snapshot, trước khi chạy answerer.

Freeze tối thiểu48 câu/12 mỗi ngành, đủ F1/F2/F3/controls; ghim code/data/
config/index/model/prompt/exposure/reviewer. Khác câu không chứng minh khác
khái niệm: ghi riêng wording overlap và target/concept reuse; nguồn đã dùng
hoặc được AI thấy không phải holdout độc lập. Bộ dùng tuning giữ làm dev.

Không hạ Routed Recall@5 gồm no-call, facts/citation/đủ ý/controls hoặc đổi
denominator để che ca chưa đạt. Schema/hash/quote đúng không thay entailment
review. LLM giữ tắt; freeze/evaluation offline không cho phép gọi Google.
