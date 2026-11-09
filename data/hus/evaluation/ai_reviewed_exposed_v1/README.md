# AI-reviewed exposed evaluation v1

56 câu, 14 mỗi ngành; F1=12, F2=16, F3=8, thiếu nguồn=8, ngoài phạm vi=8,
chưa opt-in=4. Dùng AI review theo chỉ dẫn người dùng ngày03/11/2026.
Không phải holdout độc lập; người soạn đã biết runtime/dev và nhiều dữ kiện
đã lộ trong tập cũ. Giữ nguyên câu hỏi; sửa gold Q043/Q044 và diễn giải Q048
trước inference. Mọi gold được đánh dấu ai_reviewed, không thay source review.

48 evidence IDs; bốn phần bổ sung cùng nguồn là thành phần cần thiết của
đáp án đầy đủ, không là bốn nguồn thay thế độc lập. Review nguồn/ngành/phiên
bản/variant, F3 AI opt-in và draft được giữ nguyên. Blank prerequisites không
cho phép suy đủ điều kiện học. Q024 chỉ từ chối official assessment theo nguồn
được phép dùng cho bản2023, không khẳng định không tồn tại đề cương ứng viên.

Gold không lấy từ dự đoán RAG. Cấm sửa bộ đã freeze dựa trên kết quả chạy;
mọi tuning sau đó phải dùng bản dev và lập phép đo khác. Kết quả API/scorer
và review ngữ nghĩa AI phải báo riêng. Recall>=90% trên bộ đã lộ không chứng
minh ngưỡng chất lượng độc lập. Bản gốc/worksheet/baseline không đổi.

[Review và lý do](../holdout_v2_ai_review_v1/README.md).
