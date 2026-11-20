# Đối chiếu đáp án và thử câu ngoài menu — 19/11/2026

Đã đối chiếu bộ 30 câu đã chạy Gemini với snapshot v4 và thử **12 câu mới
ngoài menu** trên Windows/Python 3.11, lexical/`legacy`. Lượt mới dùng RAG
offline và có 0 lời gọi Google. Nhận xét dưới đây là rà soát sơ bộ của Codex.

## Bộ 30 câu đã chạy Gemini

- Đáp án hiển thị trong CSV khớp kết quả đã lưu. Dữ kiện, citation và cảnh
  báo của bản canonical được giữ. Đã kiểm **40 citation** với snapshot v4,
  gồm 32 citation F1/F3 và các dòng nguồn của tám ca F2.
- F2 giữ đúng 4 tín chỉ MAT2300 và 3 tín chỉ ở ba ca còn lại. Ô tiên quyết
  MAT2300 trống vẫn được trả là chưa rõ. Các dòng nhiều mã giữ nguyên
  xuống dòng. F3 giữ nhãn AI tham khảo.
- Kết quả lịch sử là **23 câu dùng Gemini, 1 fallback và 6 ca đối chứng
  không gọi model**. Nhóm còn 30 dòng cần xác nhận. [CSV 30 câu để nhóm ghi nhận](../data/hus/review/student_content_ai_draft_20261114_r1/review_group_return.csv).

## 12 câu ngoài menu

Có **7 câu trả lời và 5 câu thiếu thông tin**. Đây là trạng thái backend.
Nhận xét theo đúng ý, đủ ý, dữ kiện và nguồn nằm trong bảng dưới.

| Ca | Ngành và phiên bản đang chọn | Kết quả và nhận xét |
| --- | --- | --- |
| FREE-01 · Nghề nghiệp sau tốt nghiệp, mở đầu bằng “Em” và có “rồi” | Toán học · QD3565-2023 | `evidence_rejected`. Backend báo đã tìm thấy đoạn liên quan nhưng guard từ chối. |
| FREE-02 · Lĩnh vực có thể làm việc sau khi học xong | Toán tin · QD3567-2023 | Đúng ý. Có doanh nghiệp, nghiên cứu, tài chính và giảng dạy theo trang ngành. Phiên bản và hệ của nguồn F1 vẫn chưa rõ. |
| FREE-03 · Tín chỉ Đại số tuyến tính 1 theo tên | Toán học · QD3565-2023 | Đúng **4 tín chỉ** cho MAT2300, PDF trang 9. |
| FREE-04 · Tín chỉ MAT1204 trong khung KHMTTT | KHMTTT · QD3568-2023 | Đúng **3 tín chỉ**, PDF trang 10. Cảnh báo xác minh của nguồn được giữ. |
| FREE-05 · “Trước khi học … thì em cần hoàn thành môn nào?” | Toán tin · QD3567-2023 | `routing_unknown` trước retrieval dù v4 có dòng tiên quyết của MAT1202. |
| FREE-06 · Học phần cần hoàn thành trước MAT3533 | KHDL · QD3569-2023 | Đúng dòng PDF trang 11. Giữ `MAT2406/` rồi xuống dòng `MAT2323`, kèm cảnh báo mã chưa giải quyết. |
| FREE-07 · Đóng gói bảo vệ trạng thái đối tượng | Toán tin · QD3567-2023 | Có ý cần hỏi trong đoạn “Đối tượng, lớp và bất biến”. Kèm thêm tổng quan và đoạn hợp thành nên câu trả lời rộng. Nguồn là hồ sơ AI MAT1202. |
| FREE-08 · Mô hình khớp quá sát dữ liệu huấn luyện | KHDL · QD3569-2023 | Giải thích đúng ý theo đoạn “Khái quát và điều chuẩn”. Phần biểu diễn dữ liệu và phân tích hành vi làm câu trả lời dài. Nguồn là hồ sơ AI MAT3533. |
| FREE-09 · Hỏi khung KHMTTT khi chọn KHDL | KHDL · QD3569-2023 | `scope_conflict`. Gợi ý chọn KHMTTT. |
| FREE-10 · Hỏi khác biệt giữa lớp và đối tượng, quyền F3 tắt | Toán tin · QD3567-2023 | Không trả nội dung AI. Thông báo `routing_unknown` vì câu chưa được nhận diện là yêu cầu F3. |
| FREE-11 · Tỷ trọng thi cuối kỳ | Toán học · QD3565-2023 | `evidence_unavailable`. Nêu thiếu dữ liệu xác minh về hình thức đánh giá chính thức. |
| FREE-12 · Học phần cần hoàn thành trước MAT2300 | Toán học · QD3565-2023 | PDF trang 9 để trống ô tiên quyết. Trả “chưa rõ từ nguồn”. |

## Các ca cần nhóm xem trước

- **FREE-01:** Bỏ riêng “Em” hoặc “rồi” thì vẫn bị guard từ chối. Bỏ cả hai,
  cùng ngành và phiên bản đã chọn, thì có đáp án F1. Hai thử nghiệm đơn lẻ
  giúp khoanh vùng cách hỏi, chưa xác định chính xác token nội bộ bị giữ.
- **FREE-05:** Cùng phạm vi Toán tin/QD3567-2023, hỏi “Để học Lập trình hướng
  đối tượng cần hoàn thành môn nào trước?” trả dòng nguồn `MAT2505`.
- **FREE-10:** Đổi “Trong phần học MAT1202” thành “Trong nội dung MAT1202”
  thì backend nhận diện F3 và nhắc bật quyền AI. Quyền vẫn tắt trong cả hai ca.
- **FREE-07 và FREE-08:** Cả hai có đoạn trả lời trực tiếp. Nhóm đọc thêm để
  nhận xét độ dài và phạm vi phần giải thích hữu ích.

Các biến thể chẩn đoán được chạy riêng. Bộ 12 câu và bộ 30 câu giữ kết quả
từng lượt. [CSV 12 câu để nhóm điền](../data/hus/review/student_content_followup_20261119_r1/review_group_return.csv) ·
[Câu hỏi và phạm vi](../data/hus/evaluation/runs/student_content_followup_20261119_r1/cases.json) ·
[Đáp án, nguồn và dữ kiện](../data/hus/evaluation/runs/student_content_followup_20261119_r1/observations.json).
