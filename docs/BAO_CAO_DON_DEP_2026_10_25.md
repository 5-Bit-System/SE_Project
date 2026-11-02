# Rà soát và dọn file local — 25/10/2026

Đã rà soát dung lượng, danh mục file, trạng thái Git và các tham chiếu trong code,
test, tài liệu. Phạm vi là vệ sinh workspace, đặc biệt `backups`; không thay đổi
nghiệp vụ, schema, dữ liệu runtime hay cài đặt phụ thuộc.

## Kết quả

| Chỉ số | Kết quả |
| --- | --- |
| File đã xóa | 5.869 |
| Dung lượng giải phóng | 1.049.153.955 byte, khoảng 1.001 MiB |
| `backups` trước | khoảng 1.008 MiB |
| `backups` sau | khoảng 10 MiB, giảm gần 99% |
| File nguồn/cấu hình đối chiếu hash | 530 file giữ nguyên trước khi ghi báo cáo/memory này |

Đã xóa profile/cache Chrome không có tiến trình dùng, thư viện Playwright/node
cài riêng cho trial cũ, checkout/archive review đã khôi phục được từ Git,
ảnh/log kiểm thử cũ, fixture/credential của database test đã drop, bản sao crawl
trùng byte, và cache Python/pytest/Ruff ngoài môi trường cài đặt.

Checkout review có 495 file khớp commit `586d659` sau chuẩn hóa xuống dòng CRLF;
phần thêm chỉ là cache và ảnh kiểm thử. Archive crawl được kiểm tra khớp với bản
đã giải nén trước khi xóa; các payload crawl chỉ bị xóa khi trùng SHA-256 với
candidate corpus còn giữ. Các biến thể README/config/tài liệu nguồn khác biệt
vẫn giữ tại `backups/crawldata-results-3a45aae/data/hus/`.

## File được giữ

- 9 database dump, bằng chứng checksum/rollback và cấu hình legacy phục hồi.
- 5 PDF gốc trong `docs/pdf/`, nguồn catalog và candidate corpus; báo cáo học vụ,
  OCR TXT/TSV, CSV và JUnit có ích cho đối chiếu/nguồn gốc.
- `.env`, `.env.auth`, cấu hình Docker, `.venv`, `.git`, toolkit local và toàn bộ
  mã nguồn/test đang sửa dở. Mã legacy còn phục vụ tham chiếu/rollback được giữ.
- Log của app đang chạy dưới `backups/vnu_signin_20261025/` và ba ảnh kiểm thử
  VNU/admin mới nhất trong `backups/system_auth_20261025/browser_4e62b1e236/`.
- File bàn giao gốc `backups/system_auth_20261025/accounts.private.txt` được giữ
  theo memory; đây là mật khẩu tạm lịch sử, không phải thông tin admin hiện tại.

Một file credential giả cũ, 248 byte, trong thư mục `browser_f8654fdd83` không
xóa được do ACL riêng. Không đổi ACL để ép xóa. Các ảnh và file có thể dọn trong
thư mục đó đã được xóa; file này không được ứng dụng sử dụng. Một số credential
test nhỏ khác cũng được giữ khi metadata bị ACL từ chối truy cập.

Danh sách chính xác, lý do, thống kê và kết quả đối chiếu được lưu local, ignored:
`backups/cleanup_20261025/manifest.json`, `result.json`, `preserved_hashes.json`.
Không có nội dung mật khẩu hoặc bảng điểm trong các báo cáo dọn dẹp này.

## Kiểm tra sau dọn

- 440 offline passed / 71 deselected, gồm acceptance PDF HUS. Tắt ghi bytecode
  và pytest cache để không tái tạo các cache vừa xóa.
- Ruff toàn repo `--no-cache` và `git diff --check` đạt. Còn cảnh báo
  Starlette/httpx đã có từ trước.
- `/health`, `/ready`, `/auth/session` 200; phiên không cookie vẫn anonymous.
  Toàn bộ 13 asset local được HTML hiện tại tham chiếu đều tải được với 200.
- Không restart app, gọi VNU, đọc điểm thật, đổi tài khoản/mật khẩu, cấu hình
  SMTP, database hoặc Docker volume. Không commit/push/PR.

Dung lượng giảm là dung lượng workspace local; không phải bằng chứng tăng tốc
API hay giảm kích thước lịch sử Git. Không xóa dependency hoặc nguồn nghiệp vụ
chỉ vì chưa thấy được tải trên giao diện hiện tại.
