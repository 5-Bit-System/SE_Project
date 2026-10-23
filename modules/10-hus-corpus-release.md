# Module 10 — Chuẩn bị và phát hành corpus HUS

Cập nhật: 23/10/2026. **Hiện trạng:** đầu ra tiền xử lý thử đã được xóa theo yêu cầu người dùng; [tài liệu tiến độ](../docs/KE_HOACH_TIEN_XU_LY_DATA_HUS.md) chỉ còn giá trị lịch sử. Chưa có corpus/index active.

## Trách nhiệm và đầu vào

Chuẩn bị nguồn tra cứu được tuyển chọn, giữ provenance và đóng gói release bất biến cho 11. Candidate ở data/hus/releases/2026-10-22-3a45aae-candidate/, từ commit 3a45aae của crawldata. Không sửa candidate hoặc mặc định merge cả nhánh crawler.

## Pipeline dự kiến

1. Kiểm kê URL/file/hash, trùng lặp, lỗi thiếu nội dung và nhãn loại/ngành; không tin nhãn crawler chưa review.
2. Ghi include/exclude/needs_review/pending_ocr và lý do; chỉ include vào index phục vụ trả lời.
3. Làm sạch menu/footer, chuẩn hóa Unicode, giữ bảng/đơn vị/chú thích/điều kiện; gộp bản trùng theo hash/nội dung.
4. Trích xuất PDF text; OCR PDF scan theo trang và review nội dung dùng trả lời. Đây không phải OCR bảng điểm sinh viên.
5. Chuẩn hóa publisher/type, bậc đại học/thạc sĩ/tiến sĩ, ngành/chương trình/general/unknown, ngày ban hành, khóa/năm/hiệu lực. Không suy năm áp dụng từ ngày crawl hoặc bậc học đã xác minh từ riêng tiêu đề.
6. Chia theo mục/điều/bảng; chunk giữ document_id/release_id/locator/hash và ánh xạ nguồn, không tách mất ngoại lệ.
7. Đo baseline từ khóa rồi vector/kết hợp trên bộ câu hỏi; chốt model/storage bằng bằng chứng. Cache embedding theo nội dung thực đưa vào model và cấu hình/version.
8. Đóng gói manifest, review log, corpus/chunks/index config và báo cáo đánh giá; duyệt trước atomic active switch.

## Release và giới hạn

Candidate dùng prototype. V1 chính thức theo quyết định crawl tại thời điểm phát hành rồi review/publish; dùng lại candidate cần quyết định thay đổi rõ. Build/publish lỗi giữ active cũ; giữ phiên bản cũ để rollback.

Không crawl khi startup/request hoặc theo lịch tuần. V2/v3 là release chủ động. Không đưa transcript/credentials/cookies/history vào corpus hoặc ghi dữ liệu crawl thành course facts.

## Tiêu chí hoàn thành

Mọi tài liệu có review decision; mọi chunk có nguồn/locator/hash/release; không index pending_ocr/needs_review. Cấu hình/pipeline/index pin phiên bản, có khả năng dựng lại và rollback. Đánh giá retrieval/citations theo [kế hoạch RAG](../docs/KE_HOACH_XU_LY_DATA_RAG_HUS.md). Nhãn active của crawler không chứng minh văn bản được duyệt/còn hiệu lực.
