# Tích hợp hỏi đáp F1/F2/F3 — đã kiểm offline

Đã nối luồng **chọn bằng chứng RAG → LLM → kiểm đầu ra → câu trả lời** bằng client,
retrieval và UI hiện có. F1/F3 không cần dựng xong câu trả lời trích nguồn trước khi
gọi model. Backend vẫn dựng bản canonical để trả trong `hus_answer` và dùng làm
fallback; F2 giữ nguyên dữ kiện, chỉ cho model chọn cách trình bày.

| Phần | Hành vi đã kiểm |
| --- | --- |
| **F1** | Hỏi thông tin ngành/học tiếp/nghề nghiệp từ đúng nguồn. Nhận cụm “vào năm”, cách hỏi học nâng cao/cơ sở và source locator “Nguồn giới thiệu…”. |
| **F2** | Tín chỉ/tiên quyết, trạng thái chưa rõ và dòng nguồn giữ nguyên khi qua model. Không dùng LLM để suy điều kiện đăng ký. |
| **F3** | Nội dung/mục tiêu có nhãn “kiến thức AI”, giữ quyền dùng nội dung tham khảo. Cụm “hồ sơ môn…/mục tiêu học tập…” được nhận; tự ghi “tôi đồng ý” trong câu hỏi không thay quyền API. |
| **Tên chủ đề** | Tên có “kiểm tra” được đối chiếu với tiêu đề unit của đúng môn/ngành/phiên bản. Không coi tên đã khớp là yêu cầu đánh giá; câu hỏi thêm đánh giá vẫn xử lý riêng. |
| **Giao tiếp** | Nhận “Cho em hỏi…”, chào kèm lời chúc đơn giản; không nuốt câu hỏi hoặc thao tác ở mệnh đề sau. Câu cấp chương trình không bị hỏi nhầm mã môn. |
| **Lỗi/thiếu nguồn** | Thiếu nguồn hoặc mơ hồ không gọi model; API lỗi giữ nguyên bản RAG và metadata fallback. Server tắt giữ response cũ. |

Một số câu đã kiểm: “Cho em hỏi cơ hội nghề nghiệp ngành như thế nào?”, “Số tín chỉ
MAT2403?”, “Mục tiêu MAT1204?”, “Nội dung MAT3370: Dự báo và kiểm tra mô hình?”.
Luôn chọn đúng ngành/phiên bản; F3 cần bật quyền tham khảo AI.

**66 test mới** kiểm luồng, cách hỏi, negative và API bốn ngành. Các nhóm liên quan
đạt1.057 test ở giai đoạn đầu; nhóm API/scope/topic/F3 đạt181, API bốn ngành có
tiên quyết/quyền đạt24; sau sửa cuối, nhóm support/language/topic/luồng đạt256.
Các nhóm giao nhau, không cộng tổng và không gọi là full-repo. Ruff8 file đạt;
có một warning Starlette cũ. Không sửa test/gold/run/review lịch sử hoặc chấm lại
A7B. DEV-Q002 và các hợp đồng scope cũ còn mở.

**Giới hạn:** provider trong lượt này hoàn toàn giả lập, **0 Google call**, không
đọc key hoặc kiểm browser. Câu F1 live thành công ở bước trước là kết quả lịch sử;
chưa xác nhận live F2/F3 trên code mới. Validator vẫn bảo toàn từ ngữ nguồn nên
chưa chứng minh cải thiện diễn đạt. Nội dung F3 dài có thể fallback vì ngân sách.
Không tuyên bố mọi cách hỏi đều đã hỗ trợ.

Giữ v4/lexical/LLM mặc định tắt. Dữ liệu và3.032 file cũ nguyên SHA; chỉ bốn file
runtime dự kiến đổi và thêm bốn file test. Bước tiếp theo là bộ khoảng30 câu để
nhóm kiểm nội dung; mọi đợt Google mới cần thống nhất số call.
[Receipt](../data/hus/qa/20261114/evidence_first_integration_r1/report.json).
