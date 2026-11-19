# Kịch bản demo chatbot HUS — 5 đến7phút

Phạm vi đồ án sinh viên, cập nhật14/11/2026. Dùng source/venv trên máy người
trình bày, không cần đường dẫn tác giả, database hoặc Playwright để mở giao diện.
[Báo cáo phân hệ](HUS_RAG_PROJECT_REPORT.md) · [Quickstart](HUS_RAG_QUICKSTART.md).

## 1. Chuẩn bị trước buổi trình bày

Cài theo quickstart trên Windows64-bit/Python3.11. Tại thư mục source, chạy:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_rag --check
.\.venv\Scripts\python.exe -X utf8 -m tools.run_hus_rag
```

Mở **http://127.0.0.1:8011/**. Nếu đổi cổng bằng `--port 8012`, mở cổng8012.
Giữ terminal, Ctrl+C để dừng. Không mở file HTML trực tiếp.

Lệnh này luôn tắt LLM và không gọi Google. **F3 vẫn dùng hồ sơ AI đã lưu**;
phải giải thích rõ đây là nội dung tham khảo, không phải model vừa sinh câu trả
lời. Không cần Playwright/Chromium riêng cho người chỉ muốn dùng ứng dụng.

Chuẩn bị sẵn [bảng30 câu và nguồn](RAG_STUDENT_CONTENT_30_LIVE_2026_11_14.md),
[call F2 xác nhận](RAG_F2_PROMPT_CONFIRMATION_2026_11_14.md) và
[CSV nhóm review](../data/hus/review/student_content_ai_draft_20261114_r1/review_group_return.csv)
để minh họa kết quả đã lưu khi không chạy Gemini live.

## 2. Trình bày RAG và giao diện — không tiêu call Google

| Thời gian | Thao tác | Nội dung giải thích/kỳ vọng |
| --- | --- | --- |
| 0:00–0:40 |Giới thiệu bốn ngành và chọn KHMTTT |“Chatbot tra thông tin ngành, dữ kiện chương trình và nội dung môn từ dữ liệu đã lưu.” Chỉ rõ ngành/phiên bản đang chọn. |
| 0:40–1:30 |Hỏi “Cho em hỏi cơ hội nghề nghiệp ngành KHMTTT như thế nào?” |F1 trả theo nguồn; mở thẻ nguồn khi có link. Đọc edition/hệ thực tế trên thẻ, không mặc định tài liệu đang có hiệu lực. |
| 1:30–2:20 |Đổi sang Toán học, hỏi “MAT2300 có bao nhiêu tín chỉ?” |F2 phải hiện **4 tín chỉ**, giữ tên/mã và nguồn PDF. Mở thẻ PDF để chỉ vị trí nguồn, không suy thành xác nhận điều kiện học. |
| 2:20–2:50 |Hỏi “Tiên quyết MAT2300 là gì?” |Nguồn trống → **chưa rõ**; không nói chắc “không có tiên quyết”. |
| 2:50–3:40 |Đổi KHMTTT, bật “Cho phép kiến thức AI tham khảo”, hỏi “Mục tiêu MAT1204?” |F3 có nhãn **kiến thức AI**, không giả link đề cương chính thức. Checkbox diễn đạt đang tắt nên không gọi Google. |
| 3:40–4:20 |Hỏi “Môn đó có bao nhiêu tín chỉ?”, rồi “Hãy chuyển tiền giúp tôi.” |Câu đầu cần làm rõ mã môn; câu sau ngoài phạm vi. Không lấy môn ngầm từ lịch sử hoặc thực hiện hành động. |
| 4:20–4:50 |Đổi sang KHDL |Hội thoại/nguồn cũ bị bỏ, quyền F3 tắt lại. Khi backend có quyền diễn đạt, quyền đó cũng reset. |
| 4:50–6:00 |Mở bảng kết quả đã lưu |Giải thích23 dùng Gemini/1 fallback/6 control; call F2 thành công sau sửa là lượt riêng. Nêu review nhóm còn pending và vài giới hạn. |

Giữ phần trả lời gọn. Nếu câu trả lời dài hoặc dữ liệu khác kỳ vọng, ghi nguyên
câu hỏi/ngành/phiên bản/kết quả, dùng mục lỗi thực tế bên dưới; không chỉnh đáp
án tại chỗ để khớp kịch bản.

## 3. Đoạn Gemini thật — chỉ khi đã có key/backend và ngân sách phù hợp

Đây là đoạn **tùy chọn**, không tự chạy khi đọc tài liệu. Trong phiên làm việc
với trợ lý, mọi budget test trước đã dùng hết; trợ lý chỉ thực hiện call mới sau
khi thống nhất số call. Thành viên sử dụng app trực tiếp chịu quota/chi phí của
project Google đã cấu hình, cần dự trù trước buổi demo.

1. Dừng launcher RAG. Dùng [profile Gemini của quickstart](HUS_RAG_QUICKSTART.md): `python -m tools.run_hus_llm` tự đọc key backend đã lưu.
2. Tải lại trang, chọn Toán học. Kiểm thông báo **Tự động dùng Gemini**; không cần tick diễn đạt. Quyền F3 không cần cho câu F2 này.
3. Nếu có ngân sách cho một call, hỏi **“MAT2300 có bao nhiêu tín chỉ?”** đúng một lượt.
4. Đọc trạng thái thực tế: chỉ nói “đã dùng Gemini” nếu có nhãn **AI diễn đạt từ nguồn**. Giá trị vẫn phải4 tín chỉ và có nguồn.
5. Nếu hiện **Bản trích nguồn**, trình bày đó là fallback, không gọi là model thành công. Không gửi lại tự động để cố lấy kết quả đẹp.

Lần xác nhận đã lưu trả HTTP200/`used=true`, khoảng1,62giây; đây là một lần đã
đo, không hứa lần demo tiếp theo có cùng thời gian hoặc luôn thành công. Không
hiển thị key hay raw lỗi provider lên slide, frontend hoặc chat.

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

## 6. Bằng chứng hiện có và phần chưa làm

Đã kiểm local29 test browser; source chuyển thư mục + venv tối thiểu mới đạt
`--check`20 ca API/2.124 menu/4 hash nguồn, server HTTP5 chat. Đây là kiểm **cùng
máy Windows**, không phải máy khác/clone remote; xem [receipt](RAG_UI_QUICKSTART_2026_11_14.md).
Nhận xét AI30 câu không thay review nhóm. F3 còn câu dư chủ đề và ví dụ cần xem
lại; nguồn chưa có xác nhận hiệu lực/học vụ toàn bộ.

Hướng dẫn này thay lệnh demo cũ gắn đường dẫn cá nhân/venv trong `backups/`.
Các receipt/trạng thái kiểm lịch sử vẫn giữ nguyên; không cần tạo ZIP, chạy CI
hoặc deploy để thực hiện kịch bản local này.
