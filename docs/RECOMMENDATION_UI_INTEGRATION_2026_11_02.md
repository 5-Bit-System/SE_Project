# Tích hợp giao diện tư vấn môn học — 02/11/2026

Người dùng yêu cầu tích hợp giao diện tư vấn môn học vào hệ thống hiện tại,
tạo commit, PR và issue. Theo dõi tại [issue #67](https://github.com/5-Bit-System/SE_Project/issues/67).

## Phạm vi và lịch sử

- Nền: main `5239b7333a8f8cdf0f919e6b0505af0def99fe23`.
- Nguồn: feat/recommendation-conversation-ui
  `c823aa5ca1b8453f5b151574caf41ed88a6cc22a`.
- Nhánh tích hợp: integration/recommendation-conversation-ui-20261102.
- Nguồn nối thẳng từ main, có 19 commit riêng. Merge local
  `93167bdb3f1912bfd5a2105881b9f0c9279a004c` giữ nguyên các commit và tác giả.
  Không có conflict. Tree ngay sau merge giống hệt tree nguồn.
- Không đưa nhánh admin đang review hoặc HUS data v3 vào lần tích hợp này.
  Các ghi chú memory local có trước được sao lưu và giữ ngoài commit tích hợp.

Giao diện bổ sung hội thoại thu thập mong muốn, ba phương án với trọng số khác
nhau, lộ trình tóm tắt, chi tiết tiên quyết AND/OR, so sánh và lưu/chỉnh sửa qua
API hiện có. Source gates, context revision, CSRF và server validation tiếp tục
áp dụng. Không bổ sung LLM extraction, thuật toán xếp hạng mới hoặc RAG; mốc tốt
nghiệp là mục tiêu, chưa phải kết quả tối ưu nhiều học kỳ.

## Điều chỉnh khi tích hợp

`check_vnu_only` trước đây cho request HTML/static đi tới server thật ở cổng 8000.
Lần chạy trên worktree sạch đã phát hiện phụ thuộc này qua ERR_CONNECTION_REFUSED.
Đã dùng lại `common_route` để phục vụ tài nguyên từ đúng worktree, giữ nguyên mọi
assertion và API giả lập. Lần chạy sau đạt mà không cần server HTTP. README frontend
bổ sung lệnh kiểm tra UI/model mới và dependency quay video của Playwright.

## Kiểm chứng local

- 621 test offline/PDF đạt, 80 PostgreSQL deselected; dùng explicit `tests` và
  `--full-catalog-root docs/acceptance/hus_2022`.
- Một Starlette/httpx deprecation warning có sẵn.
- 7 bộ Chrome đạt: recommendation workspace, course status, semester plans,
  VNU-only, presentation, study desk và motion.
- Model JS, analytics JS, Ruff, cú pháp các module thay đổi, hai catalog builder
  và diff whitespace đạt.
- UI kiểm thử bằng dữ liệu giả lập: wizard, ba phương án, ngân sách/quota,
  tiên quyết, so sánh, lưu thành công/409/mất phản hồi, logout race, Việt/Anh,
  sáng/tối, desktop/mobile và reduced motion.
- Không gọi model/provider, đăng nhập VNU thật hoặc đọc hồ sơ/điểm thật.
  Không có thay đổi schema, migration hay dữ liệu cần publish.

Các kiểm chứng trên chạy trước publication. Trạng thái PR, CI trên commit tích hợp,
merge GitHub và kích hoạt checkout local phải được xác minh từ Git/GitHub; báo cáo
này không tự khẳng định những bước đó đã hoàn tất. Bằng chứng local và receipt nằm
trong thư mục bị Git ignore `backups/recommendation_integration_20261102/`.
