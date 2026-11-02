# Module 08 — Giao diện web học tập

Cập nhật: 23/10/2026. **Hiện trạng:** đã thiết kế lại giao diện tĩnh; chưa có import portal/RAG citations.

## Trách nhiệm và code

app/static/index.html, styles.css, app.js và favicon.svg cung cấp workspace chọn chương trình → bảng điểm → điều kiện → gợi ý/what-if, cùng floating advisor.

Giữ HTML/CSS/JavaScript và backend hiện có. Runtime HUS cần PostgreSQL/backend sẵn sàng. Nhập tay là dự phòng; OCR/upload ảnh bảng điểm không nằm trong kế hoạch.

## Kế hoạch màn hình

- Kết nối portal: các trạng thái theo contract 09, lỗi/hết phiên/ngắt kết nối và bước tương tác cần thiết.
- Review import: ngành/khóa, record khớp/chưa rõ, điểm/lần học, nguồn; xác nhận trước apply, cancel giữ transcript cũ.
- Track/path đặt trong workspace vì ảnh hưởng eligibility; đồng bộ với chat.
- Hiển thị progress theo khối/nhóm từ API; quota chưa biết giữ chưa biết.
- RAG: hiển thị citations URL/tiêu đề/trang-mục từ backend, thiếu nguồn hoặc hiệu lực chưa rõ.

## State và quy tắc

Context gồm program/revision, transcript/draft, eligibility, recommendation/baseline, effective constraints, track/path và chat history. Đổi ngành xóa dữ liệu liên quan và loại response muộn. UI không tự quyết định eligibility.

Không lưu credentials, cookie portal, transcript hoặc history lâu dài trong browser storage. Dữ liệu ngoài dùng textContent hoặc sanitizer được kiểm tra; không chèn HTML portal/crawl trực tiếp.

Nút mẫu năm học hiện dùng year trong khi HUS year=null; cần ẩn/vô hiệu hóa, không dùng null <= year để tạo điểm giả. Profile fixture chỉ phục vụ kiểm thử, không yêu cầu runtime có 12 profile.

## Tiêu chí hoàn thành

Responsive desktop/mobile, focus/keyboard/label rõ, reduced motion, trạng thái loading/empty/error. Kiểm tra nhập điểm/tìm kiếm/đổi ngành/track-path/what-if/chat; bổ sung cancel/apply/citation khi tính năng sẵn sàng. Cảnh báo nguồn nháp/offering chưa biết hiển thị nhất quán.

Bằng chứng hiện có: [báo cáo frontend](../docs/FRONTEND_REDESIGN_2026_10_23.md); không chứng nhận luồng portal/RAG chưa triển khai.
