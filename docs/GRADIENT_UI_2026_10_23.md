# Giao diện gradient sáng và tối

Ngày: 23/10/2026. Thực hiện theo `.github/skills/frontend-design/SKILL.md`,
frontend-design và webapp-testing được chọn qua `project-toolkit/SKILL.md`.

## Hướng thiết kế

Hai giao diện do người dùng chọn ở đầu trang. Gradient tập trung ở nền,
thanh điều hướng, vùng giới thiệu và nút chính; bảng điểm và nội dung dùng
bề mặt rõ màu để đọc số liệu. Bố cục bảng theo học kỳ/năm thực tế được giữ.

| Vai trò | Sáng | Tối |
| --- | --- | --- |
| Nền gốc | #EEF2FF | #101A32 |
| Bề mặt nội dung | #FFFFFF | #15223B |
| Chữ chính | #253654 | #E6EDFC |
| Chữ phụ | #52617B | #BAC8DF |
| Điểm nhấn xanh | #3658AD | #B0C6FF |
| Điểm nhấn tím | #6552A0 | #C9B5FF |

Gradient sáng chuyển xanh lam–tím nhạt–xanh ngọc. Bản tối dùng xanh đêm–chàm–
xanh ngọc trầm. Chữ Be Vietnam Pro, Segoe UI dự phòng; nội dung căn trái.
Độ tương phản và sự ổn định khi đọc bảng là ưu tiên; không thêm chuyển động nền.

```
Sổ học tập     [Ngôn ngữ] [Chương trình] [Dữ liệu mẫu] [Sáng | Tối]
Điều hướng | Vùng giới thiệu gradient
           | Thông báo nguồn
           | Bảng điểm / Điều kiện học / Gợi ý
```

## Cách triển khai

- `app/static/theme.js` chạy trước CSS để khôi phục lựa chọn trước khi vẽ trang.
- Chỉ chấp nhận `light`/`dark`; lần đầu theo chế độ hệ điều hành.
- Nút native có `aria-pressed`, sử dụng được bằng bàn phím.
- Lưu riêng tùy chọn `study-workspace-theme` trong localStorage; lỗi lưu trữ
  không ngăn đổi màu trong phiên. Đồng bộ thay đổi tùy chọn giữa các tab.
- `themes.css` chứa biến màu và trạng thái cho bảng điểm, điều kiện học,
  gợi ý, form, badge, cảnh báo và chat. Native input/select dùng color-scheme
  tương ứng. Meta theme-color cũng được cập nhật.
- Đổi giao diện không cập nhật state bảng điểm, chat hoặc yêu cầu API.

## Kết quả kiểm tra

Chrome headless qua DevTools Protocol vì môi trường chưa có Playwright.
Kịch bản và ảnh ở `backups/semester_ui_20261023/gradient-*` và `theme-check.mjs`,
được Git bỏ qua. Mẫu bảng điểm cá nhân tiếp tục chỉ nằm ngoài Git.

- Cả hai chế độ: gradient hiện ở nền/vùng giới thiệu/điều hướng, bảng mẫu
  hiển thị đủ 36 dòng, luồng gợi ý trả 5 môn, chat mở/đóng bình thường.
- Đổi giao diện giữ nguyên bảng điểm nhập tay; không tự đổi dữ liệu nguồn.
- Kiểm tra nút bằng Enter, trạng thái aria-pressed, khôi phục sau reload,
  mặc định hệ điều hành, lựa chọn cá nhân ưu tiên hơn hệ điều hành, và tình
  huống getItem/setItem bị chặn đều đạt.
- Desktop 1440×1080 và mobile 390×844 không tràn ngang trang; bộ chọn sử dụng
  được trên điện thoại. Đã xem ảnh sáng/tối, chat và màn hình gợi ý.
- Đo 5 cặp chữ/nền nội dung ở mỗi chế độ: cả 10 cặp đạt trên 4.5:1.
  Đây là kiểm tra các cặp màu chính, không phải chứng nhận accessibility toàn bộ.
- Không ghi nhận JavaScript exception; `node --check` cho theme.js/app.js
  và `git diff --check` đạt. `/ready` trả ok với PostgreSQL.

Không thay đổi backend; không chạy lại Python/PostgreSQL hoặc hội thoại LLM
cho lần chỉnh màu này. Các thay đổi vẫn local, chưa commit/push.
