# Thiết kế lại giao diện AI-07

Ngày: 23/10/2026. Hoàn thành thay đổi giao diện local, chưa commit/push.

## Hướng thiết kế

Áp dụng `project-toolkit` cùng skill người dùng tải tại `.github/skills/frontend-design/SKILL.md`. Giữ FastAPI và frontend HTML/CSS/JavaScript của dự án.

Thiết kế dành cho sinh viên lập kế hoạch môn học: thanh bên thể hiện đúng ba bước bảng điểm → kiểm tra điều kiện → gợi ý. Căn trái nội dung; bảng môn và thao tác nhập điểm là trọng tâm. Mobile chuyển điều hướng thành hàng ngang và các khối nội dung về một cột.

```text
Desktop: thương hiệu | chương trình và lựa chọn hiển thị
         trạng thái nguồn và giới hạn dữ liệu
         điều hướng | tiêu đề, lưu ý nguồn
                    | tiến độ, bảng môn / điều kiện / gợi ý
Mobile:  header → lựa chọn ngành → điều hướng ngang → nội dung
```

| Token | Giá trị |
| --- | --- |
| Nền | #F0F4F7 |
| Bề mặt | #FFFFFF |
| Chữ chính | #193348 |
| Hành động | #087B78 |
| Chữ phụ | #526877 |
| Cảnh báo | #8B5A15 |

Font Be Vietnam Pro, có fallback Segoe UI/sans-serif khi không tải được Google Fonts. Headline 23–32px, tiêu đề khối 17–18px; nội dung và dữ liệu căn trái. Các chỉ số nằm chung một dải, bảng môn dùng hàng phân cách để dễ quét. Đã xem lại phương án trước khi dựng: dùng giao diện làm việc với dữ liệu thật, hạn chế trang trí và không tạo các số tiến độ giả.

## Thay đổi

- Thay stylesheet cũ bằng thiết kế sáng, responsive; cập nhật bố cục và favicon.
- Giữ ID và kết nối API; thêm điều hướng tab bằng phím mũi tên, Home/End, tabindex và liên kết ARIA.
- Thêm tên truy cập cho ô tìm kiếm, lọc, điểm số và checkbox môn học; hiển thị focus bàn phím.
- Điều chỉnh nhãn tiếng Việt cho trạng thái nguồn, khối kiến thức và năm chưa biết; bỏ khẳng định tuyệt đối về độ đúng của quy định.
- Khung tư vấn đồng bộ màu sắc, hỗ trợ mở/đóng, phóng to và trả focus về nút mở.

## Bằng chứng kiểm tra

Kiểm tra bằng Chrome headless có sẵn qua Chrome DevTools Protocol; Playwright chưa có và cài gói bị chặn mạng. Dùng FastAPI local và catalog runtime, chế độ gợi ý offline. Chỉ nhập dữ liệu phiên trình duyệt cho kiểm tra.

- Desktop 1440×1080, mobile 390×844: không tràn ngang; đã xem ảnh bảng điểm và màn hình gợi ý.
- Tải đủ 4 ngành; số môn lần lượt 65/67/90/68.
- Ba tab và điều hướng bàn phím, tìm kiếm không có kết quả, đánh dấu môn đã học hoạt động.
- Gợi ý và what-if đều render 5 môn.
- Mở/phóng to/đóng chat hoạt động; chưa gửi hội thoại đến nhà cung cấp AI.
- Đổi sang từng ngành còn lại reset số môn đã hoàn thành về 0.
- Không có Runtime.exceptionThrown trong lượt kiểm tra; `node --check app/static/app.js` và diff whitespace của phần frontend đạt.

Ảnh và script kiểm tra ở `backups/frontend_redesign_20261023/` (Git bỏ qua): `desktop.png`, `mobile.png`, `recommend.png`, `report.json`, `browser.mjs`. Chưa kiểm tra toàn bộ trình duyệt/kích thước hoặc nội dung hội thoại LLM. Không thay đổi backend, nguồn catalog hoặc triển khai RAG trong lần thiết kế này.
