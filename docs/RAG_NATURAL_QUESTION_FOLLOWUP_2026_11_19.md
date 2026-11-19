# Kiểm lại câu hỏi tự nhiên sau sửa — 19/11/2026

Lượt kiểm riêng trên `hus-data-20261111-v4`, BM25 lexical, Windows và Python
3.11. Dữ kiện và nguồn lấy từ snapshot thật. Hai câu F2 dùng đầu ra trình bày
giả lập để kiểm adapter và validator. Lượt này có **0 lời gọi Google**.

| Câu hỏi và phạm vi | Kết quả mới |
| --- | --- |
| “Sau khi tốt nghiệp ngành Toán tin, em có thể làm việc ở những đâu?” | F1 trả lời từ `CTDT-TTUD-130815.pdf`. Citation khớp câu tương đương bỏ xưng hô. |
| “MAT2300 thi gi?” · Toán học/QD3565-2023, cho phép F3 | `retrieval_empty`. Thông báo nêu thiếu dữ liệu đánh giá và hướng người hỏi đối chiếu đề cương nếu cần cách thi chính thức. |
| “Đếm học phần giúp tôi” · Toán tin/QD3567-2023 | F2 đếm **68 mã duy nhất** từ `canonical_f2`. Số môn mỗi sinh viên phải học vẫn để chưa xác định. |
| “Cho mình xem toàn bộ danh sách học phần” · Toán học/QD3565-2023 | F2 trả **90 mã và tên môn** từ `canonical_f2`. |
| “Tốt nghiệp Toán tin thì em làm việc về vật lý lượng tử ở đâu?” | `evidence_rejected`. Chủ đề cụ thể vẫn cần nguồn hỗ trợ. |
| “Nếu chưa đủ điều kiện thì có thể học tiếp sau đại học?” · Toán học | `evidence_rejected`. Điều kiện phủ định vẫn có hiệu lực. |
| “Đếm học phần bắt buộc giúp tôi” · Toán tin, có gợi ý thao tác đếm F2 | `needs_clarification/unsupported_operation`. Dữ kiện và citation rỗng. |
| Hỏi số môn của KHMTTT khi đang chọn Toán tin | `scope_conflict`. Gợi ý chọn ngành KHMTTT. |

Hai câu đếm/liệt kê nhận diện bằng luật theo ngành và phiên bản đã chọn. Mỗi
câu cần **0 lượt hiểu ý định và 1 lượt trình bày giả lập** qua
`HUSGroundedAdapter`. Kiểm thử xác nhận toàn bộ `hus_answer` sau adapter khớp
bản RAG, gồm dữ kiện, citation và cảnh báo.

Prompt F2 giờ hiển thị một mẫu JSON với đúng khóa cấp ngoài và ID nguồn của
từng yêu cầu. Với cả hai câu đếm/liệt kê ở trên, mẫu gửi đi là:

```json
{"kind":"facts","style":"direct","fact_keys":["field","program_id","review_status","value"],"citation_ids":["1"]}
```

Model chỉ chọn `style`. Validator tiếp tục kiểm tập khóa, kiểu dữ liệu, ID và
trùng lặp. Các trường như `courses` và `catalog_course_count` vẫn nằm trong
`facts.value` và do backend dựng.

Lượt [ý định/F2 live](RAG_INTENT_F2_CONTENT_REVIEW_2026_11_15.md) giữ kết quả
IF2-002 bị chặn ở `fact_keys` và IF2-004 cần làm rõ. Kết quả mới xác nhận
đường xử lý offline và mẫu JSON qua mock. Hiệu quả của prompt mới với Gemini
thật cần một lượt kiểm riêng có ngân sách. [Lượt 24 câu cũ](RAG_ROUTER_CONTENT_REVIEW_2026_11_15.md).

**260 test liên quan đạt**, với một cảnh báo deprecation của Starlette.
Regression kiểm cách hỏi tương tự, điều kiện/phủ định, sai phạm vi, khóa F2
không hợp lệ và chính sách lỗi provider. Lệnh `tools.run_hus_rag --check` đạt
20 ca API, 2.124 câu trong menu và 4 hash nguồn. Ruff và kiểm cú pháp JavaScript đạt.
