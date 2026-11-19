# Kiểm focused với Gemini — 19/11/2026

**3/3 lời gọi Gemini trả HTTP 200 và được dùng trong câu trả lời.** Hai ca
đối chứng không gọi model. Có 0 lỗi, 0 lần chuyển sang offline vì HTTP 429.
Model thực tế của cả ba lượt là `gemini-3.5-flash-lite`.

## Kết quả theo câu

| Ca | Phạm vi và kết quả | Gemini | Toàn lượt | Token vào/ra |
| --- | --- | ---: | ---: | ---: |
| FOC-01 · F1 chưa chọn nguồn | Hỏi hướng học tiếp sau KHMTTT. Hệ thống đưa 5 lựa chọn nguồn và chờ người dùng chọn. | 0 call | 0,003 s | — |
| FOC-02 · F1 chọn nguồn | Chọn hồ sơ KHMTTT hệ chuẩn 2023. Đáp án giữ đủ điều kiện, nhu cầu, bậc Thạc sĩ/Tiến sĩ và các lĩnh vực trong đoạn nguồn. Citation đúng hồ sơ đã chọn. | 2,290 s | 2,305 s | 719/127 |
| FOC-03 · F3 bật quyền | MAT1202, Toán tin. Đáp án giữ đủ hai đoạn về đối tượng và kế thừa, gồm cam kết lớp con trong đoạn kế thừa. Giữ cảnh báo nội dung tham khảo AI. | 1,263 s | 3,967 s | 919/159 |
| FOC-04 · F3 tắt quyền | Cùng câu MAT1202. Hệ thống yêu cầu bật quyền AI tham khảo. | 0 call | 0,027 s | — |
| FOC-05 · F2 đối chiếu | Danh mục Toán học/QD3565-2023. Gemini trả cấu trúc trình bày hợp lệ. Backend giữ đủ 90 dòng mã–tên học phần và để trống số môn mỗi sinh viên phải học. | 1,598 s | 5,291 s | 3.274/31 |

Tổng **4.912 token vào, 317 token ra**. Cột Gemini đo từ client đến khi đọc và
kiểm envelope. Cột toàn lượt gồm xử lý RAG, validator và thời gian chờ giữa
các cuộc gọi để giữ khoảng cách tối thiểu 5 giây. Đây là số đo của lượt này.

## Đối chiếu nội dung

- F1 và F3 dùng `focused_rewrite_v1`. Cả hai câu hiển thị đủ các đoạn bắt buộc
  và các đoạn đó có trong quote canonical tương ứng. Nguồn F1 giữ trạng thái
  `include_markdown`. Hai đoạn F3 giữ nhãn AI và trạng thái `needs_review`.
- F2 dùng prompt trình bày F2 mới. Cả 90 dòng mã–tên trong câu trả lời khớp
  danh mục backend theo đúng thứ tự. `hus_answer` của cả ba ca dùng Gemini
  khớp bản RAG đối chiếu, gồm facts, citation và cảnh báo.
- Hai ca đối chứng giữ nguyên phản hồi RAG. Preflight mock đã kiểm một phản hồi
  429 chuyển về bản RAG và dừng gọi, cùng một phản hồi 403 báo lỗi và dừng.
  Lượt thật có cả ba phản hồi HTTP 200.

Đã dùng đủ **3/3 lời gọi được duyệt**. Lượt dùng v4/lexical và các câu đã dùng
trong quá trình phát triển. Kết quả xác nhận ba trường hợp cụ thể. Nhóm còn cần
đọc đáp án và nguồn trước khi chọn `focused` cho demo. Chế độ mặc định là
`legacy`. Việc so độ dễ đọc hoặc kiểm thêm câu tự nhiên cần lượt riêng.

## Hồ sơ lượt kiểm

- [Bộ chuẩn bị](../data/hus/evaluation/focused_live_20261119_r1/prepared.json)
  chứa snapshot, 82 pin code/dữ liệu, ba prompt và bản RAG đối chiếu. Tổng
  14.338 ký tự prompt, trần 1.024 output token mỗi lời gọi.
- [Kết quả và câu trả lời](../data/hus/evaluation/runs/focused_live_20261119_r1/observations.json)
  chứa trạng thái, model, token, độ trễ và đáp án được hiển thị. Hash và prompt
  của từng lượt khớp bộ chuẩn bị. [Manifest](../data/hus/evaluation/runs/focused_live_20261119_r1/manifest.json).

[Tiến độ và các bước tiếp theo](RAG_PROGRESS_AND_NEXT_PLAN.md)
