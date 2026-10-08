# Module 11: Web Portal & Interactive Dashboard (`web_ui`)

## 1. Bản chất & Vai trò trong Hệ thống
Một hệ thống thông minh chỉ phát huy tối đa giá trị khi có một giao diện người dùng (User Interface) trực quan, hiện đại, thẩm mỹ và thân thiện với sinh viên. 
Module **Web Portal & Interactive Dashboard** là điểm tiếp xúc trực tiếp (Front-facing Interface) kết nối người học với toàn bộ 10 module backend bên dưới, mang lại trải nghiệm mượt mà qua quy trình 4 bước liền mạch, hệ thống thẻ KPI trực quan, bản đồ lộ trình học tập 4 năm tô màu sinh động, bộ điều khiển What-if sliders tức thì và bong bóng trợ lý học vụ AI (Floating Chat Widget) thường trực.

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - **Khu vực Nhập liệu & Nhận diện Ngành (Tab 1 — Bảng điểm):**
    - Hỗ trợ kéo-thả hoặc chọn file bảng điểm (kết nối Module 01 OCR/Parser).
    - Hỗ trợ nút nạp nhanh 12 Hồ sơ sinh viên mẫu (Demo Quick-Load) phục vụ trình diễn.
    - Bộ chọn ngành học thủ công hoặc tự động nhận diện từ bảng điểm qua API `/transcript/detect-program`.
    - **Cơ chế Reset cô lập ngành (Major Isolation):** Khi người dùng đổi ngành, giao diện tự động xóa toàn bộ môn đã chọn và kết quả cũ, nạp lại danh mục môn của ngành mới.
  - **Bảng Điều khiển Tiến độ & Điều kiện (Tab 2 — Điều kiện):**
    - Hiển thị thẻ KPI: Tổng tín chỉ tích lũy, GPA thang 10 & thang 4, số môn đã đạt.
    - Lưới môn học đủ điều kiện kỳ tới (`eligible`) và môn bị chặn (`blocked`) kèm lý do chi tiết.
  - **Bản đồ Lộ trình 4 Năm (Tab 3 — Lộ trình):**
    - Hiển thị trực quan 4 cột/khối đại diện cho Năm 1, Năm 2, Năm 3, Năm 4.
    - Mã màu trực quan: Đã hoàn thành (Xanh lá), Đủ điều kiện kỳ tới (Xanh dương), Bị khóa (Xám/Đỏ), Kỳ tương lai (Tím/Trung tính).
  - **Bộ Gợi ý & Điều khiển What-If (Tab 4 — Đề xuất):**
    - 5 thanh trượt What-If Sliders (Mục tiêu nghề nghiệp, Định hướng chuyên sâu, Điểm số an toàn, Tải học, Thực hành).
    - Bảng xếp hạng môn học tự động cập nhật thời gian thực khi kéo thanh trượt kèm thẻ giải thích minh bạch (`eligible_because`, `fit_reasons`).
  - **Bong bóng Trợ lý Học vụ AI nổi (Floating Chat Bubble):**
    - Nút tròn cố định ở góc dưới bên phải màn hình (`position: fixed; z-index: 99999;`), thường trực trên toàn bộ 4 tab.
    - Bấm vào mở popup kích thước chuẩn ~1/4 màn hình (`410px × 580px`).
    - Nút phóng to toàn màn hình (`⛶`) và thu nhỏ (`🗗`), nút đóng (`✕`) và hỗ trợ phím tắt `Esc`.
    - Khung chat hỗ trợ render Markdown, gợi ý câu hỏi nhanh (Quick Prompts).
- **Ngoài phạm vi:**
  - Không tự tính toán điều kiện tiên quyết ở client (nguồn chân lý bắt buộc ở backend Module 05).
  - Không tự tạo môn học hoặc lý do học vụ giả mạo ở JavaScript.

---

## 3. Kiến trúc Nội bộ Module

```text
app/static/
├── index.html                  # Cấu trúc HTML5 ngữ nghĩa, bố cục 4 tab + Floating Chat Widget
├── css/
│   ├── main.css                # Hệ thống Design System: Biến CSS, màu sắc HSL hiện đại, typography
│   ├── components.css          # Thẻ KPI, Lưới môn học, Sliders, Badge trạng thái
│   └── chat-widget.css         # Styling cho Bong bóng chat nổi, hiệu ứng mở popup, responsive
└── js/
    ├── api.js                  # Lớp Client gọi REST API backend
    ├── state.js                # Quản lý State tập trung (Ngành đã chọn, Bảng điểm, Kết quả gợi ý)
    ├── roadmap.js              # Logic vẽ và tương tác Lộ trình 4 năm
    ├── whatif.js               # Lắng nghe sự kiện kéo slider và gửi request What-if
    └── chat.js                 # Xử lý hội thoại AI, phím Esc, phóng to/thu nhỏ khung chat
```

---

## 4. Hợp đồng Giao tiếp với Backend APIs
Module Web UI tương tác với các API endpoints được cung cấp bởi các module backend:
1. `GET /programs` $\rightarrow$ Nạp danh sách 4 ngành học.
2. `GET /courses?program_id={id}` $\rightarrow$ Nạp danh mục môn học của ngành.
3. `POST /transcript/detect-program` $\rightarrow$ Tự động nhận diện ngành học từ mã môn.
4. `POST /transcript/summary` $\rightarrow$ Tính toán chỉ số tín chỉ và GPA.
5. `POST /eligibility` $\rightarrow$ Nhận danh sách môn đủ điều kiện và môn bị chặn.
6. `POST /roadmap` $\rightarrow$ Nhận cấu trúc lộ trình 4 năm theo trạng thái học tập.
7. `POST /recommendations` $\rightarrow$ Nhận danh sách môn xếp hạng kèm điểm What-if và giải thích.
8. `POST /advisor/chat` $\rightarrow$ Gửi câu hỏi và nhận câu trả lời tư vấn từ AI Advisor.

---

## 5. Quy tắc Thiết kế & Trải nghiệm Người dùng (UX Invariants)
1. **Thiết kế Thẩm mỹ Hiện đại (Premium Aesthetics):**
   - Sử dụng bảng màu phối hợp hài hòa (Tailored HSL Color Palette), hỗ trợ chế độ tương phản rõ ràng.
   - Typography hiện đại (Google Fonts Inter / Be Vietnam Pro cho tiếng Việt).
   - Hiệu ứng vi mô (Micro-animations, smooth transition khi kéo slider hoặc mở popup chat).
2. **Xử lý Ngoại lệ Thân thiện (Graceful Error States):**
   - Khi mất mạng hoặc backend lỗi, hiển thị thông báo nhẹ nhàng (Toast notification), không làm vỡ giao diện.
   - Khi ngành chưa có môn học, hiển thị màn hình trống có hướng dẫn (Empty State with Action).
3. **Responsive Design:**
   - Tương thích tốt trên màn hình máy tính để bàn (Desktop), máy tính xách tay (Laptop) và máy tính bảng/điện thoại di động.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** Chuyển đổi giữa 4 tab mượt mà, giữ nguyên trạng thái dữ liệu đã nhập.
- **TC-02:** Bong bóng chat AI Advisor luôn hiển thị cố định ở góc dưới bên phải trên tất cả 4 tab, mở/đóng và phóng to/thu nhỏ chính xác, phím `Esc` đóng popup mượt mà.
- **TC-03:** Đổi ngành học lập tức xóa toàn bộ dữ liệu môn đã chọn trước đó, không gây lẫn lộn mã môn giữa các ngành.
- **TC-04:** Kéo các thanh trượt What-If Sliders cập nhật bảng xếp hạng trong thời gian thực dưới $300$ms.

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🟡 **Đã xong 60%** — Giao diện 4 tab tĩnh và widget AI Advisor hoạt động tốt.
- **Hiện có trong codebase:** Thư mục [`app/static/`](file:///e:/SE_Project/app/static/) (`index.html`, `app.js`, `styles.css`) đã có:
  - Bố cục 4 tab chuyển đổi mượt mà.
  - Floating Chat Widget AI Advisor có nút phóng to (`⛶`) / thu nhỏ (`🗗`), đóng (`✕`) và phím `Esc`.
  - Hiển thị môn đủ điều kiện, môn bị chặn và lộ trình 4 năm.
- **Nhiệm vụ cần thực hiện:**
  1. Thêm vùng Upload file bảng điểm kéo-thả (kết nối Module 01).
  2. Bổ sung các thanh trượt What-if Sliders trực quan trên Tab 4 (kết nối Module 07).
  3. Thêm thanh chọn nạp nhanh 12 hồ sơ mẫu (Quick-load Demo Profiles) để demo tiện lợi.
