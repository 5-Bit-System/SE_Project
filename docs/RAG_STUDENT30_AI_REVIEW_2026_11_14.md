# Rà soát sơ bộ30 câu — bản AI để nhóm đối chiếu

**Người rà soát sơ bộ: Codex (AI), ngày14/11/2026.** Đã đọc30 phản hồi thực tế, quote/nguồn và dữ kiện đã lưu. Đây chưa phải review của thành viên nhóm hoặc nghiệm thu học thuật.

## Nhóm dùng bản nào?

Mở [bản CSV trả riêng](../data/hus/review/student_content_ai_draft_20261114_r1/review_group_return.csv). Các cột `ai_*` có nhận xét sơ bộ. Nhóm điền các cột `nguoi_review`, `ngay_review`, `dung_y`, `du_y`, `dung_du_kien`, `dung_citation`, `ghi_chu` và cập nhật `review_nhom`. Không cần đổi bảng gốc; bản trả riêng đã giữ câu hỏi/đáp án/nguồn và kết quả cũ.

Cả30 xác nhận của nhóm vẫn pending. Run cũ vẫn23 câu dùng Gemini/1 fallback/6 control. Lần MAT2300 xác nhận prompt mới thành công được [ghi riêng](RAG_F2_PROMPT_CONFIRMATION_2026_11_14.md), không thay kết quả003 của bộ này.

## Các điểm nên xem trước

- **005/011/017/023:** có đúng chủ đề được hỏi, nhưng kèm tổng quan và các unit lân cận. Cần thu gọn nguồn khi người dùng chỉ rõ một chủ đề; không nhầm đầy đủ với trả lời đúng trọng tâm.
- **005:** ví dụ phép chiếu cần làm rõ giả định mặt phẳng qua gốc khi nói về ánh xạ tuyến tính/hạt nhân. **017:** ví dụ khác biệt kết quả giữa nghiên cứu nên làm rõ giả thiết minh họa/khả năng thay vì đọc như kết luận nhân quả. Đây là ghi chú AI để nhóm xem, chưa sửa hồ sơ.
- **001/002/007/008:** ngắt dòng và citation dày làm khó đọc;007 có cụm “các việc nghiên cứu” ngay trong quote. **019:** lỗi chữ “dữ iệu” cũng nằm trong nguồn. Không tự chỉnh dữ liệu chỉ để review đẹp hơn.
- **F2:**4/3/3/3 tín chỉ và các dòng tiên quyết khớp nguồn; MAT2300 có ô tiên quyết trống nên vẫn là chưa rõ. Không suy điều kiện đăng ký hoặc đổi xuống dòng thành AND/OR.
- **F3:** citation đúng hồ sơ AI không chứng minh nội dung là đề cương chính thức. **F1 KHDL:** edition/hệ unknown được giữ nguyên; các nguồn2015/2023 không được suy là đang có hiệu lực.

## Nhận xét từng câu

| Mã | Ngành/nhóm | Nhận xét sơ bộ AI | Nhóm xác nhận |
| --- | --- | --- | --- |
| SV30-001 | Toán học / f1 | Giữ đủ nhóm nơi làm việc và giảng dạy trong quote2015. Xuống dòng giữa câu và citation dày gây khó đọc; chưa xác minh hiệu lực hiện tại. | pending |
| SV30-002 | Toán học / f1 | Giữ vai trò kiến thức/kỹ năng làm tiền đề học tiếp và điều kiện nhu cầu cá nhân/công việc. Nên nối dòng trình bày; không suy thành cam kết tuyển cao học. | pending |
| SV30-003 | Toán học / f2 | Đáp án hiển thị đúng4 tín chỉ và PDFtrang9. Đây vẫn là fallback trong run gốc; lần xác nhận prompt mới dùng Gemini được ghi riêng, không thay ô Gemini_used của dòng này. | pending |
| SV30-004 | Toán học / f2 | Nguồn tiên quyết null; trả chưa rõ và không kết luận không có tiên quyết hoặc đủ điều kiện đăng ký là phù hợp. | pending |
| SV30-005 | Toán học / f3 | Có đủ phần Ma trận và ánh xạ tuyến tính[2], nhưng thêm tổng quan[1] và Hạt nhân/ảnh/hạng[3]. Ví dụ phép chiếu tuyến tính nên làm rõ mặt phẳng qua gốc; hồ sơ AI hiện cũng chưa nêu giả định này. Cần nhóm xem lại, chưa sửa dữ liệu. | pending |
| SV30-006 | Toán học / f3 | Giữ đủ5 mục tiêu trong hồ sơ AI và cảnh báo tham khảo; phù hợp câu hỏi mục tiêu, chưa là chuẩn đầu ra chính thức. | pending |
| SV30-007 | Toán tin / f1 | Đủ hai nhóm làm việc/giảng dạy theo quote2015. Cụm “các việc nghiên cứu” có ngay trong nguồn, không coi là model tự thêm; nên đối chiếu bản gốc trước khi sửa. | pending |
| SV30-008 | Toán tin / f1 | Giữ đủ điều kiện/nhu cầu và bậc Thạc sĩ, Tiến sĩ theo nguồn; không biến khả năng học tiếp thành bảo đảm nhập học. | pending |
| SV30-009 | Toán tin / f2 | Tên/mã MAT1202 và3 tín chỉ khớp dòng nguồn QD3567-2023, trangPDF10; trạng thái draft_unverified được giữ. | pending |
| SV30-010 | Toán tin / f2 | Giữ nguyên tiên quyết MAT2505 và cảnh báo không kết luận điều kiện đăng ký; không thêm môn hoặc diễn giải luật đăng ký. | pending |
| SV30-011 | Toán tin / f3 | Phần Giao diện và phân chia trách nhiệm[3] đúng yêu cầu, nhưng kèm tổng quan và3 unit khác. Có đủ ý được hỏi nhưng quá rộng; ưu tiên chỉ chọn unit được gọi tên. | pending |
| SV30-012 | Toán tin / f3 | Giữ đủ4 mục tiêu OOP trong quoteAI; không gán thành đề cương/chuẩn đầu ra chính thức. | pending |
| SV30-013 | KHMTTT / f1 | Đủ bốn hướng kỹ thuật, dự ánCNTT, nghiên cứu và giảng dạy theo DOCX2023; giữ điều kiện/mức độ trong nguồn và cảnh báo chưa xác minh hiệu lực. | pending |
| SV30-014 | KHMTTT / f1 | Giữ đủ điều kiện/nhu cầu, bậc học và các lĩnh vực học tiếp trong nguồn2023; không khẳng định đủ điều kiện của từng sinh viên. | pending |
| SV30-015 | KHMTTT / f2 | MAT1204 có3 tín chỉ khớp nguồn QD3568-2023/PDFtrang10. verified được giải thích là sign-off dự án, không phải chứng nhận của trường. | pending |
| SV30-016 | KHMTTT / f2 | Hai dòng MAT3507/MAT3514 giữ đúng raw nguồn. Không tự chuyển xuống dòng thành luật AND/OR hoặc xét đủ điều kiện cho tài khoản. | pending |
| SV30-017 | KHMTTT / f3 | Đúng phần Tài liệu và cấu trúc bằng chứng[3] nhưng trả thêm tổng quan và3 unit khác. Ví dụ hai nghiên cứu khác kết quả “vì” khác nhóm/cách đo nên nêu rõ là giả thiết minh họa hoặc khả năng, không tự coi là chứng minh nhân quả. | pending |
| SV30-018 | KHMTTT / f3 | Giữ đủ4 mục tiêu nghiên cứu/phạm vi/tài liệu/thiết kế/truy vết trong hồ sơAI; cảnh báo tham khảo còn nguyên. | pending |
| SV30-019 | KHDL / f1 | Đủ4 nhóm nghề nghiệp và điều kiện “tùy theo năng lực”. Hệ/edition nguồn unknown vẫn giữ; lỗi chữ “dữ iệu” có trong nguồn, cần review nguồn trước khi chỉnh. | pending |
| SV30-020 | KHDL / f1 | Giữ đủ khả năng học sau đại học/nghiên cứu/ứng dụng theo quote. Các mô tả “uy tín” là lời nguồn, không phải kiểm chứng độc lập; scope nguồn vẫn unknown. | pending |
| SV30-021 | KHDL / f2 | MAT2034 có3 tín chỉ, khớp dòng nguồn QD3569-2023/PDFtrang10; giữ trạng thái draft_unverified. | pending |
| SV30-022 | KHDL / f2 | Giữ nguyên MAT2502/MAT2403 theo raw nguồn và cảnh báo; không suy thành đánh giá đăng ký cá nhân. | pending |
| SV30-023 | KHDL / f3 | Phần Nội suy và xấp xỉ hàm[3] đủ ý yêu cầu nhưng thêm tổng quan, Nghiệm phi tuyến[2] và Tích phân số[4]. Không thiếu phần được hỏi, nhưng cần thu gọn phạm vi bằng chứng. | pending |
| SV30-024 | KHDL / f3 | Giữ đủ5 mục tiêu giải tích số theo quoteAI; có nhãn/cảnh báo tham khảo, chưa xác nhận học thuật/đề cương. | pending |
| SV30-025 | Toán học / control | Chào hỏi đúng ngữ cảnh, không cần nguồn và không gọi model. | pending |
| SV30-026 | KHMTTT / control | Chào kèm lời chúc được xử lý như hội thoại cơ bản, không gọi model hoặc tạo nguồn giả. | pending |
| SV30-027 | KHDL / control | Yêu cầu làm rõ khi thiếu mã/tên môn là đúng. Phiên bản đã có trong request nên lời nhắc có thể chỉ hỏi phần thông tin còn thiếu. | pending |
| SV30-028 | KHDL / control | Thông báo không có môn MAT9999 trong đúng ngành/phiên bản đã chọn; không suy rộng thành không tồn tại ở mọi chương trình, không tạo tín chỉ. | pending |
| SV30-029 | KHMTTT / control | Yêu cầu bật quyền F3 trước khi trả nội dung tham khảo; không tự cho phép AI hoặc gọi Gemini. | pending |
| SV30-030 | Toán tin / control | Từ chối thao tác chuyển tiền đúng phạm vi chatbot; không gọi model hoặc thực hiện hành động. | pending |

## Phạm vi đã kiểm

Đối chiếu32 quote F1/F3 và8 dữ kiện F2 với snapshot đã lưu;6 control không gọi model. Không tải lại web, không review toàn bộ PDF/DOCX, không gọi Google/tokenizer hoặc sửa runtime. Các nhận xét về đúng/đủ ý là sơ bộ AI, không phải điểm A7 mới; không có điểm accuracy mới.

Đáp án và quote đầy đủ nằm ở [gói30 câu](RAG_STUDENT_CONTENT_30_LIVE_2026_11_14.md). Nhóm có thể sửa hoặc không đồng ý với nhận xét AI và ghi lý do trong bản trả riêng.
