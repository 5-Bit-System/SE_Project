# Phạm vi RAG trên crawldata — 02/11/2026

Yêu cầu mới nhất của người dùng: nhánh này phục vụ F1/F2/F3 và trò chuyện cơ bản,
không nối với gợi ý môn, ranking hoặc explanation. Yêu cầu này thay thế cách mô tả
router chung trong tài liệu trước. Không commit/push khi chưa có yêu cầu riêng.

Luồng hiện hành cần là: chọn ngành/phiên bản được hỗ trợ → nhập câu hỏi → trò chuyện
cơ bản hoặc tra F1/F2/F3 → câu trả lời có nguồn hoặc chưa đủ căn cứ. Không lấy bảng
điểm, tính tiến độ, eligibility, preference hoặc gọi provider cho luồng RAG.

## Cách thực hiện

Quyết định kỹ thuật của agent: thêm bộ xử lý chat và ứng dụng demo FastAPI riêng,
dùng lại nguyên loader/retriever/answerer/citation hiện có. Demo chỉ nạp release qua
CURRENT, dùng giao diện chat riêng và các ngành/phiên bản thật trong release.
Các endpoint recommendation của sản phẩm rộng hơn tiếp tục thuộc module riêng.

Đã cân nhắc tiếp tục dùng /me/advisor/chat với monkeypatch hoặc dựng demo RAG riêng.
Router chung dễ vô tình chạy fallback chọn môn và buộc demo phụ thuộc catalog giả,
nên chọn demo độc lập. Đây là lựa chọn triển khai của agent cho scope người dùng
đã xác định, không phải tuyên bố người dùng đã phê duyệt một API production mới.

## Contract

- Chat nhận HUSQuestion hiện có, trả mode=basic_chat|hus_rag, reply và hus_answer.
- Chào hỏi/cảm ơn/tạm biệt/hướng dẫn trả lời mẫu cố định, không có citation giả.
- Tra cứu F1/F2/F3 dùng HUSAnswer hiện có, giữ metadata/review và citation contract.
- F1 chọn edition nguồn độc lập; F2/F3 ghim version ngành. F3 opt-in mặc định tắt,
  nhãn “kiến thức AI”; PDF mở binary/hash/trang; web mở URL nguồn.
- Câu chọn môn/ngoài phạm vi không chuyển tiếp, không sinh facts thiếu căn cứ.
- Đổi ngành xóa hội thoại/opt-in, bỏ response cũ. Không lưu hội thoại cá nhân.
- Demo bind loopback, không DB/auth/VNU/provider. Bản tích hợp production vẫn cần
  verified account, CSRF/Origin, binding và revision theo yêu cầu P0-4 trước đây.

P0-4/P0-5 và receipt cũ giữ nguyên dưới dạng bằng chứng lịch sử, không chứng nhận
scope mới. Trước phát hành main phải thay router chung bằng endpoint HUS có bảo vệ
tương đương, rồi nghiệm thu/CI trên commit mới. Chưa kích hoạt production.
