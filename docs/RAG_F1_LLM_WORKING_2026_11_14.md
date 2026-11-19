# F1 qua Gemini — đã có câu trả lời được dùng

Đã hoàn thành bước1 của kế hoạch đồ án: **một câu F1 được Gemini trả lời, qua
validator và được `generate_reply` dùng thật**, có citation. Chưa bật LLM mặc định.

Câu hỏi: **“Ra trường KHMTTT có những hướng công việc nào trong bản chương trình
đã lưu?”** Nguồn: thông tin nghề nghiệp KHMTTT bản2023 trong RAG v4.

| Lượt | Kết quả |
| --- | --- |
| **Call1 — trước sửa** | HTTP200, nhưng `output_text/b001/structure`; fallback, `used=false`. |
| **Call2 — sau sửa** | HTTP200, actual model `gemini-3.5-flash-lite`, **`used=true`**, không fallback. Provider≈**1,89s**;935 input/243 output token, tổng1.178. Chi phí thực chưa tính. |

Nguồn có tiêu đề `## 4. …`. Bộ tách cũ chỉ giữ `## ` ở backend, để `4. …` trong
text gửi model; ngay cả khi chép đúng nội dung nguồn, validator vẫn có thể chặn vì
nhận đó là prefix danh sách. Đã sửa chung việc tách nhiều marker liên tiếp: backend
giữ nguyên cả `## 4. ` rồi phục hồi khi hiển thị. Không sửa validator, nội dung
nguồn, số mục, dữ kiện hoặc citation. Đây không phải lỗi riêng theo mã câu hỏi.

Câu trả lời thực tế giữ đủ bốn hướng: chuyên gia kỹ thuật; tư vấn/quản lý/phân
tích/thiết kế/lập trình; nghiên cứu; giảng dạy. Mỗi đoạn có `[1]` liên kết citation
của backend. Nội dung gần nguyên nguồn; **chưa kết luận có cải thiện diễn đạt**.

Kiểm chứng:

- 14 regression mới: trước sửa8fail/6pass, sau sửa14pass. Nhóm compact document/output/pipeline/diagnostic liên quan **139pass**, một warning Starlette cũ; Ruff đạt.
- Replay local `POST /hus/chat` dùng kết quả Gemini đã nhận: HTTP200, `generation.used=true`, reply khớp live, `hus_answer` và citation nguyên trạng. Đây là kiểm API với kết quả đã lưu, không phải call Google thứ ba hoặc kiểm browser.
- 3.027 file cũ nguyên SHA; trong snapshot chỉ `app/hus/llm/document.py` đổi như dự kiến. Test mới được thêm riêng. Không đổi `.env`, key, dữ liệu, default hoặc artifact cũ. Preparedr6 nay stale sau sửa document; từng call mới ghi pins/prompt riêng.

Được duyệt tối đa3 call, **đã dùng2 và dừng khi thành công**;1 call chưa dùng,
không gọi tiếp trong tác vụ này. Không retry tự động/đổi model; cap1.024 token.
Một câu F1 thành công chưa chứng minh F2/F3 hoặc toàn bộ chatbot hoạt động tốt.

[Receipt call1](../data/hus/qa/20261114/f1_live_attempt_1/report.json) ·
[Receipt call2 và câu trả lời](../data/hus/qa/20261114/f1_live_attempt_2/report.json) ·
[Kiểm API/integrity](../data/hus/qa/20261114/f1_live_verification_r1/report.json).
