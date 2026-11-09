# Holdout mới v2 — candidate chờ người thật review

Ngày03/11/2026. Có56 câu nháp/14 câu mỗi ngành; chưa chạy RAG và chưa dùng tuning.
**0 câu được người thật duyệt. Chỉ có thể chốt holdout sau ít nhất40 câu được
reviewer thật duyệt; công cụ và AI không thay người review.**

Bạn đã nhận review trong hội thoại. Chưa ghi tên hay chữ ký vì chưa có quyết định
từng câu. Reviewer cần độc lập với việc chỉnh runtime từ bộ câu hỏi này.

Đây là bản nháp do AI soạn từ record/quote/policy, không lấy prediction làm gold.
Phiên soạn tách biệt không hoàn thành do giới hạn sử dụng; agent chính tiếp quản
và đã biết runtime/dev trước đó. Vì vậy KHÔNG tuyên bố độc lập người soạn hoặc
độc lập ngữ nghĩa. Reviewer phải kiểm trùng ý, sửa/loại câu bị lộ, và có thể tự
viết lại trước khi freeze phiên bản mới. Không chỉ thay tên/mã trong câu dev rồi
coi là câu độc lập. F1 dùng cùng kho nguồn nên có thể chia sẻ chủ đề/evidence.

questions chỉ chứa request; gold/evidence tách riêng. reviewer_packet có câu,
đáp án nháp, quote và locator/hash. review_decisions giữ toàn bộ pending/null.
Manifest ghim nguồn, bộ dev/old questions, runtime tại lúc soạn bằng hash; agent
soạn không sửa code, không chạy retrieval hoặc đọc prediction để chọn gold.

Mẫu review mở rộng, báo cáo trùng từ và nguồn thay thế ở ../holdout_v2_review/.
Các đề xuất nguồn thay thế chỉ tương thích scope, chưa được duyệt tương đương ý.
Reviewer mở nguồn thật, kiểm đáp án, đọc top neighbors và tự xét semantic overlap,
ghi accept/reject/revise cùng tên thật, thời gian có múi giờ, lý do và từng check.
Mọi revise tạo candidate phiên bản mới, ghim/review lại; không sửa frozen v2 để
hợp thức hóa kết quả. Dòng reject/revise/pending không tính vào40 accepted.

F3 chỉ kiến thức AI với opt-in; không official syllabus/assessment. Trạng thái
draft/sign-off cấp dự án không trở thành chứng nhận của trường. Null chỉ nói
thiếu bằng chứng trong snapshot, không chứng minh dữ kiện ngoài đời không có.
Không chạy bộ mới qua app, không tuning theo câu hỏi/đáp án trước khi chốt.

Lệnh kiểm kỹ thuật, KHÔNG inference:
python -X utf8 -m tools.validate_hus_holdout --pack data/hus/evaluation/holdout_v2_candidate
python -X utf8 -m tools.validate_hus_holdout_review
