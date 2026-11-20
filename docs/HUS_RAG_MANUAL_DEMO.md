# Kịch bản demo chatbot HUS — 6 phút

Phạm vi đồ án sinh viên, cập nhật **19/11/2026**. Kịch bản chính dùng
**v4 / lexical / legacy** trên Windows 64-bit/Python 3.11, với source và venv
của người trình bày.
[Báo cáo phân hệ](HUS_RAG_PROJECT_REPORT.md) · [Quickstart](HUS_RAG_QUICKSTART.md).

## 1. Chuẩn bị trước buổi trình bày

Cài theo quickstart trên Windows 64-bit với Python 3.11. Tại thư mục gốc, chạy:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_rag --check
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_rag
```

Mở **http://127.0.0.1:8011/**. Nếu đổi cổng bằng `--port 8012`, mở cổng8012.
Giữ terminal, Ctrl+C để dừng. Không mở file HTML trực tiếp.

Lệnh này tắt LLM. **F3 hiển thị hồ sơ AI tham khảo đã lưu** khi người dùng bật
quyền F3. Thành viên có thể dùng trình duyệt đang có trên máy.

Trong **Danh mục câu hỏi**, mở một nhóm F1, F2, F3 hoặc Hướng dẫn, rồi bấm câu hỏi để gửi.
Có thể tìm theo tên, mã môn hoặc nội dung câu hỏi bằng tiếng Việt không dấu.
F1 ghi phiên bản và hệ của nguồn. F2 và F3 dùng chương trình đã chọn.

Bản chạy trong Workspace mở qua tab **Tra cứu thông tin** của ứng dụng chính.
Các bước và số liệu trong kịch bản này được ghi trên demo độc lập.

Chuẩn bị sẵn [bộ 30 câu](RAG_STUDENT_CONTENT_30_LIVE_2026_11_14.md) và
[lượt Gemini focused](RAG_FOCUSED_LIVE_2026_11_19.md) để mở ở phút cuối.

## 2. Trình bày RAG và giao diện — không tiêu call Google

| Thời gian | Thao tác | Nội dung giải thích/kỳ vọng |
| --- | --- | --- |
| 0:00–0:40 |Giới thiệu bốn ngành và chọn KHMTTT |“Chatbot tra thông tin ngành, dữ kiện chương trình và nội dung môn từ dữ liệu đã lưu.” Chỉ rõ ngành/phiên bản đang chọn. |
| 0:40–1:30 | Hỏi “Cho em hỏi cơ hội nghề nghiệp ngành KHMTTT như thế nào?” | F1 trả về các hướng nghề nghiệp. Mở nguồn DOCX, chỉ rõ phiên bản/hệ của tài liệu và trạng thái xác minh. |
| 1:30–2:20 | Đổi sang Toán học, hỏi “MAT2300 có bao nhiêu tín chỉ?” | F2 hiển thị **4 tín chỉ**. Mở PDF trang 9 và đối chiếu mã môn, tên môn, tín chỉ. |
| 2:20–2:50 | Hỏi “Tiên quyết MAT2300 là gì?” | Ô nguồn trống. Hệ thống trả **chưa rõ từ nguồn**. |
| 2:50–3:40 | Đổi KHMTTT, hỏi “Mục tiêu MAT1204?” khi quyền F3 đang tắt. Bật “Cho phép kiến thức AI tham khảo” rồi hỏi lại. | Lần đầu nhắc bật quyền. Lần sau hiện mục tiêu tham khảo và nhãn **kiến thức AI**. |
| 3:40–4:20 | Hỏi “Môn đó có bao nhiêu tín chỉ?”, rồi “Hãy chuyển tiền giúp tôi.” | Câu đầu cần làm rõ môn. Câu sau nhận phản hồi ngoài phạm vi. |
| 4:20–4:50 | Đổi sang KHDL | Hội thoại và nguồn của ngành cũ được xóa, quyền F3 tắt lại. |
| 4:50–6:00 | Mở kết quả Gemini đã lưu | Giải thích bảng dưới và phân biệt lượt demo offline, câu dùng Gemini, lỗi, fallback và đối chứng. |

| Lượt đã lưu | Dùng đầu ra Gemini | Lỗi | Fallback | Đối chứng không gọi model |
| --- | ---: | --- | ---: | ---: |
| Bộ 30 câu | 23/24 call | 1 đầu ra F2 bị từ chối, chính là ca fallback | 1 | 6 |
| `focused` ngày 19/11 | 3/3 call | 0 | 0 | 2 |

Giữ phần trả lời gọn. Nếu câu trả lời dài hoặc dữ liệu khác kỳ vọng, ghi nguyên
câu hỏi/ngành/phiên bản/kết quả, dùng mục lỗi thực tế bên dưới; không chỉnh đáp
án tại chỗ để khớp kịch bản.

## 3. Đoạn Gemini thật — chỉ khi đã có key/backend và ngân sách phù hợp

Đây là đoạn **tùy chọn**, không tự chạy khi đọc tài liệu. Trong phiên làm việc
với trợ lý, mọi budget test trước đã dùng hết; trợ lý chỉ thực hiện call mới sau
khi thống nhất số call. Thành viên sử dụng app trực tiếp chịu quota/chi phí của
project Google đã cấu hình, cần dự trù trước buổi demo.

1. Dừng launcher RAG. Chạy `.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_llm` từ thư mục gốc. Launcher tự đọc key backend đã lưu. [Quickstart Gemini](HUS_RAG_QUICKSTART.md#2-bật-gemini-thật-trên-backend--tùy-chọn).
2. Tải lại trang, chọn Toán học. Kiểm thông báo **Tự động dùng Gemini**; không cần tick diễn đạt. Quyền F3 không cần cho câu F2 này.
3. Nếu có ngân sách cho một call, hỏi **“MAT2300 có bao nhiêu tín chỉ?”** đúng một lượt.
4. Đọc trạng thái thực tế: chỉ nói “đã dùng Gemini” nếu có nhãn **AI diễn đạt từ nguồn**. Giá trị vẫn phải4 tín chỉ và có nguồn.
5. Nếu hiện **Bản trích nguồn**, trình bày đó là fallback, không gọi là model thành công. Không gửi lại tự động để cố lấy kết quả đẹp.

Lần xác nhận đã lưu trả HTTP 200, `used=true`, khoảng 1,62 giây. Khi demo, ghi
trạng thái thực tế của lần chạy và dùng mã lỗi an toàn nếu có.

### Minh họa chọn nguồn với focused

Để làm thêm một ca offline, khởi động lại bằng launcher RAG và thêm
`--answer-policy focused`. Chọn KHMTTT và hỏi “Ngành KHMTTT có thể học tiếp
sau đại học như thế nào?”. Chọn tài liệu hệ chuẩn **2023** trong danh sách rồi
kiểm tra câu trả lời giữ đúng nguồn đã chọn. Có thể dùng ca này thay phần
câu ngoài phạm vi trong kịch bản chính. [Đáp án đã lưu](RAG_FOCUSED_LIVE_2026_11_19.md).

## 4. Giải thích khi lỗi hoặc không có mạng

| Hiện tượng | Cách trình bày |
| --- | --- |
| Không có key/backend Gemini |Dùng phần RAG offline và kết quả live đã lưu, nói rõ đâu là trực tiếp/đâu là bằng chứng lịch sử. |
| Checkbox AI bị khóa |Launcher offline luôn tắt LLM. Chỉ đổi sang profile Gemini nếu buổi demo cần và đã chuẩn bị key/quota. |
| Quyền401/403 |Profile tự động báo lỗi, không thay bằng offline; không công khai key hoặc tự đổi billing. |
| Hạn mức429 |Chuyển RAG offline và ngừng gọi đến khi restart; thử lại Gemini sau khi hạn mức hồi phục. |
| Timeout/mạng/503 |Profile tự động báo lỗi, không tự chuyển offline. Có thể chủ động dừng rồi chọn launcher RAG cho buổi demo offline. |
| Model output bị validator chặn |Báo lỗi, không trả output bị chặn hoặc thay bằng offline trong profile tự động. |
| Thiếu bằng chứng |Hỏi lại/làm rõ hoặc báo chưa có thông tin, không tự dựng citation. |

Không cần cố tình gọi Google bằng key sai để minh họa lỗi. Có thể mở dòng
`SV30-003` trong [run cũ](RAG_STUDENT_CONTENT_30_LIVE_2026_11_14.md): fallback vẫn
trả4 tín chỉ. Sau đó mở [xác nhận riêng sau sửa](RAG_F2_PROMPT_CONFIRMATION_2026_11_14.md)
để giải thích thay đổi; không gộp thành24/24 của lượt đo cũ.

## 5. Checklist nhóm điền sau khi thực hiện

Các ô dưới đang để trống/chưa kiểm. Người thật điền tên/ngày/kết quả; tài liệu
không tự xác nhận nhóm hoặc máy khác đã chạy thành công.

| Nội dung | Kết quả thực tế | Người/ngày | Ghi chú lỗi |
| --- | --- | --- | --- |
| Nhận đủ source và cài đúng Python3.11/venv |Chưa điền | | |
| Cài dependency và chạy `--check` |Chưa điền | | |
| Thử F1/F2/F3, mở nguồn và đổi ngành |Chưa điền | | |
| Review30 câu đúng/đủ ý/dữ kiện/citation |Chưa điền | | |
| Nếu có demo Gemini: key/backend, quota và số call dự kiến |Chưa điền | | |
| Xử lý lỗi/fallback và dừng server sau demo |Chưa điền | | |

Nếu thành viên khác gặp lỗi, ghi: hệ điều hành/kiến trúc, phiên bản Python,
lệnh đã chạy, mã lỗi an toàn và câu hỏi/ngành/phiên bản. Không đính kèm key,
file secret hoặc bảng điểm.

## 6. Kết quả chạy thử local

Ngày 19/11, kịch bản chính chạy **7 lượt hỏi trên Chromium**. Đã kiểm hash
nguồn DOCX/PDF trả qua API, nhãn AI của F3 và thao tác đổi ngành. `--check`
đạt **20 ca API, 2.124 câu menu và 4 hash nguồn**. Lượt chạy thử có 0 lời
gọi Google.

Sáu test Chromium liên quan đạt, gồm chọn nguồn `focused`, chế độ Gemini tự
động, lỗi dịch vụ, lỗi kiểm đầu ra và fallback 429. Các test gọi Gemini dùng
provider giả lập. Có cảnh báo deprecation từ dependency.

Nhóm điền checklist khi chạy trên máy thành viên và đối chiếu đáp án với
nguồn. [Bằng chứng cài đặt trước đây](RAG_UI_QUICKSTART_2026_11_14.md) ·
[Bảng 12 câu ngoài menu](RAG_STUDENT_CONTENT_FOLLOWUP_2026_11_19.md).
