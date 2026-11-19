# Kiểm F2 với diagnostic mới — lỗi trường kind

Đã dùng đúng **1/1 Google call mới được duyệt** cho câu “MAT2300 có bao nhiêu tín
chỉ?”. Google trả **HTTP200**, actual model `gemini-3.5-flash-lite`, khoảng
**2,18 giây**;1.058 input/158 output token, tổng1.216. Chi phí thực chưa tính.

Kết quả: **`used=false`, `invalid_output`, `output_schema / facts_issue=kind`**.
Điều này xác định **call mới** không có trường `kind` hợp lệ với hợp đồng F2
(`"kind":"facts"`). Có thể thiếu hoặc sai kiểu/giá trị; diagnostic không giữ giá
trị bị từ chối, cũng không chứng minh không có lỗi schema khác.

Backend tiếp tục trả **4 tín chỉ** cùng nguyên citation và câu trả lời RAG gốc.
Không nới validator, sửa prompt/logic, đổi model, retry hoặc đổi mặc định LLM.

Trước call đã ghim code/prompt và đối chiếu lại baseline. Prompt công khai
**3.932 ký tự**, hash giữ nguyên so với câu cũ; cap1.024 output token. Key backend
chỉ dùng trong bộ nhớ; không in/lưu key hoặc raw output/body lỗi.

Verification chỉ đọc xác nhận **3.077 file cũ nguyên SHA**, pins khớp, fallback
và canonical nguyên trạng. Run30 câu/CSV cũ vẫn23 dùng Gemini/1 fallback; không
gán nhãn `kind` cho call cũ, vì raw output/nhánh cũ vẫn unknown. Không chạy lại
suite khi runtime không đổi, không gọi Google thêm.

**Bước tiếp theo:** sửa prompt F2 để hợp đồng `kind=facts` rõ và tách khỏi hướng
dẫn rewrite F1/F3, kèm test offline. Đây là hướng sửa dựa trên nhánh lỗi mới,
chưa triển khai hoặc chứng minh sẽ khắc phục bằng live. Xác nhận sau sửa cần
budget mới vì1 call đã dùng hết; không sửa kết quả lịch sử để đổi điểm.

[Receipt live](../data/hus/qa/20261114/f2_live_check_r1/report.json) ·
[Verification](../data/hus/qa/20261114/f2_live_check_verification_r1/report.json).
