# Kế hoạch xử lý dữ liệu cho luồng tra cứu thông tin HUS bằng RAG

Ngày lập: **22/10/2026**. Trạng thái: **kế hoạch cho giai đoạn retrieval, trả lời và phát hành**, chưa có corpus RAG active.

Kết quả và toàn bộ phần việc tiền xử lý HUS được ghi **chỉ tại** [kế hoạch và tiến độ tiền xử lý](KE_HOACH_TIEN_XU_LY_DATA_HUS.md). Tài liệu này bắt đầu từ bước chọn index, đánh giá retrieval, hỏi đáp và phát hành.

## Giai đoạn 4 — Lập chỉ mục và tích hợp truy xuất

Đầu tiên tạo baseline tìm kiếm từ khóa để biết corpus đã tìm được câu trả lời chưa. Sau đó so sánh với vector và kết hợp hai kết quả trên cùng bộ đánh giá. Truy vấn chứa mã môn, mã biểu mẫu, số quyết định cần được đánh giá riêng; truy vấn diễn đạt tự nhiên cần mẫu tiếng Việt thực tế. Chỉ thêm bước xếp hạng lại nếu kết quả đánh giá cho thấy cần thiết.

Chưa chốt model embedding hoặc vector store trong kế hoạch này. Khi chọn, ghi nhận khả năng tiếng Việt, chất lượng trên bộ câu hỏi, chi phí, yêu cầu vận hành và phiên bản/dimension. Cache embedding theo hash nội dung thực đưa vào model, model/version và cấu hình. Không dùng lẫn index của hai cấu hình embedding.

Có thể cân nhắc PostgreSQL với vùng dữ liệu RAG riêng nếu phù hợp môi trường thực tế, nhưng không bắt buộc thêm extension hoặc sửa schema nghiệp vụ ngay. Index là artifact có thể dựng lại từ corpus đã chuẩn hóa.

Luồng runtime dự kiến:

1. Xác định câu hỏi tra cứu hay nghiệp vụ môn học; xác định bậc học (đại học/thạc sĩ/tiến sĩ), ngành, chương trình và năm/khóa nếu câu hỏi yêu cầu.
2. Chọn release active một lần cho toàn request.
3. Truy xuất tài liệu được include; lọc bậc học và ngành/chương trình phù hợp, xét thêm tài liệu chung đã review. Không dùng nhãn `unknown` để tự kết luận phạm vi.
4. Khi thiếu năm/khóa làm thay đổi câu trả lời, hỏi lại hoặc trình bày rõ phạm vi nguồn tìm được. Giữ nguồn cũ cho câu hỏi lịch sử.
5. Chọn các đoạn đủ hỗ trợ câu trả lời; xử lý mâu thuẫn theo bằng chứng phạm vi/hiệu lực. Nếu không đủ căn cứ ưu tiên nguồn nào, trình bày sự khác biệt và chưa kết luận.
6. Sinh câu trả lời từ các đoạn đã lấy, kèm trích dẫn do backend ánh xạ từ chunk. Không cho mô hình tự tạo URL nguồn.

Nội dung tài liệu được coi là dữ liệu tham khảo; chỉ dẫn nằm trong trang crawl không được thay đổi quy tắc hệ thống hoặc kích hoạt công cụ. Khi không có bằng chứng hoặc index lỗi, trả thông báo phù hợp, không chuyển sang câu trả lời học vụ dựa trên suy đoán của model.

**Hoàn thành khi:** câu trả lời truy vết được tới đoạn nguồn trong cùng release và luồng eligibility/recommendation vẫn dùng nghiệp vụ hiện có.

## Giai đoạn 5 — Đánh giá trước khi phát hành

Soạn tối thiểu 40 câu hỏi từ tài liệu đã chọn, do người review xác định nguồn và đoạn trả lời kỳ vọng. Chia tập hiệu chỉnh và tập giữ lại trước khi tối ưu. Có câu hỏi về bốn ngành, lộ trình học tiếp thạc sĩ/tiến sĩ khi đã có nguồn tuyển sinh được duyệt, tài liệu chung, bảng/số liệu, mã chính xác, diễn đạt lại, phạm vi bậc học/năm/khóa, nguồn mâu thuẫn, tài liệu bị loại và câu hỏi không có đáp án.

Ngưỡng đề xuất ban đầu, cần chốt trước khi đánh giá bản phát hành:

| Nội dung | Điều kiện |
| --- | --- |
| Kiểm kê | 100% tài liệu có quyết định; không index pending_ocr hoặc needs_review |
| Truy vết | 100% chunk có nguồn, locator, hash và release_id hợp lệ |
| Truy xuất | Ít nhất 90% câu hỏi có đáp án trong tập giữ lại lấy được đoạn đúng trong top 5; báo số tuyệt đối và từng nhóm |
| Câu trả lời | Không có lỗi nghiêm trọng về số tiền, hạn nộp, điều kiện hoặc ngành/khóa trong tập kiểm tra |
| Trích dẫn | Mọi khẳng định thực tế trong câu trả lời kiểm tra đều được nguồn trích dẫn hỗ trợ; link và locator hợp lệ |
| Thiếu/mâu thuẫn nguồn | Các ca đã định nghĩa phải hỏi lại, nêu giới hạn hoặc từ chối kết luận đúng kỳ vọng |
| Phiên bản | Request không trộn release; build/publish lỗi giữ nguyên bản active trước đó |

Ghi cả lỗi và trường hợp chưa bao phủ. Tập nhỏ đạt ngưỡng không chứng nhận toàn bộ dữ liệu học vụ. Đo thời gian truy xuất, thời gian trả lời, số token và chi phí để chốt mục tiêu vận hành trước khi publish; chưa có số đo ở thời điểm lập kế hoạch.

## Giai đoạn 6 — Đóng gói và phát hành

Snapshot crawl candidate vẫn được giữ để tham khảo khi nhóm chốt kế hoạch; các đầu ra tiền xử lý/chunk thử đã bị xóa. Trước v1 chính thức, rà cấu hình nguồn, thực hiện đợt crawl phát hành đã thống nhất, rồi chạy lại pipeline và review trên snapshot mới. Nếu muốn sử dụng lại candidate làm nguồn chính thức, cần ghi nhận thay đổi quyết định phát hành rõ ràng.

Mỗi release chứa manifest nguồn, bảng review, corpus chuẩn hóa, chunks, cấu hình index/model, hash, phiên bản pipeline và báo cáo đánh giá. Chỉ chuyển con trỏ active sau khi toàn bộ artifact sẵn sàng và bản phát hành được duyệt. Giữ release cũ để rollback; chuẩn bị hoặc kích hoạt lỗi không làm mất bản đang dùng.

Ứng dụng không crawl khi khởi động, theo request hoặc theo lịch tuần. Cập nhật tương lai là release v2/v3 chủ động. Không gộp toàn nhánh crawler vào codebase chỉ để sử dụng dữ liệu; phần mã cần tích hợp phải được chọn và review riêng.

## Tài liệu tham chiếu nội bộ

- [Memory và quy tắc dự án](../.agent/AGENTS.md)
- [Candidate README](../data/hus/releases/2026-10-22-3a45aae-candidate/README.md)
- [Candidate manifest](../data/hus/releases/2026-10-22-3a45aae-candidate/manifest.json)
- [Đặc tả hệ thống](SYSTEM_SPECIFICATION.md)
- [Phạm vi nghiệm thu PDF HUS](HUS_PDF_ACCEPTANCE_REVIEW.md)
- [Vận hành catalog HUS](../database/HUS_RUNTIME.md)
