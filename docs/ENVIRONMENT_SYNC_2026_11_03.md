# Đồng bộ mã nguồn và sửa dependency — 03/11/2026

Đã đồng bộ local `main` bằng fast-forward từ `af8d4db` tới `11db811`
(merge PR #6, `crawldata`), giữ lịch sử commit/tác giả. Bản sửa nằm trên nhánh
`fix/dependency-sync-20261103` để commit và theo dõi bằng issue GitHub.
Trạng thái công bố được xác nhận bằng lịch sử Git và issue; main chưa nhận bản sửa.
208 dòng memory local có trước được giữ cùng memory mới của upstream.
`.vscode/`, `previews/`, cấu hình, dữ liệu và các bản bàn giao cũ được giữ riêng.

## Nguyên nhân và bản sửa

- Upstream dev yêu cầu Playwright `>=1.58,<1.59`, lock ghim `1.58.0`, trong khi
  connector VNU ghim `1.64.1`. Cài theo hướng dẫn dev rồi portal không thể thỏa
  đồng thời các khai báo. Bộ dev hiện nạp trực tiếp bộ portal, dùng chung bản
  `1.64.1`; lock được cập nhật tương ứng.
- `.venv` thiếu các dependency HUS mới: Beautiful Soup, python-docx, openpyxl,
  PyYAML, pdfplumber và dependency bắc cầu. Đã cài bằng lock; mọi pin đều khớp.
- Cache browser chưa có Chromium revision `1248` và FFmpeg revision `1013`
  tương ứng Playwright đang dùng. Đã cài Chromium, headless shell và FFmpeg.
- Bốn job CI thêm `pip check` sau cài đặt. Job browser vẫn dùng Ubuntu 24.04.
- Script `check_program_binding` còn tìm form xác nhận ở bản đồ môn học. Đã dùng
  tab Gợi ý kỳ tới và mở phần công cụ học vụ qua điều khiển UI hiện có; vẫn giữ
  kiểm tra hai tài khoản, CSRF, xác nhận, nguồn chưa đủ và phản hồi sau logout.
- Cập nhật hướng dẫn cài đặt, phân biệt Chrome cho VNU/UI sản phẩm với Chromium
  cho RAG, và yêu cầu cài lại browser binary khi đổi phiên bản Playwright.

## Kiểm chứng local

| Kiểm tra | Kết quả |
|---|---|
| Cài dev + portal cùng lock từ venv mới | Thành công |
| `pip check` trên `.venv` và venv mới | Không có dependency hỏng |
| Đối chiếu mọi pin với package trong `.venv` | Không sai khác |
| Pytest offline và PDF acceptance | **1.230 passed**, 80 DB deselected |
| Chrome: course status, semester plans, recommendation workspace, VNU-only, program binding, session restore, charts | **7 bộ đạt** |
| Chromium RAG trên `.venv` và venv mới | Mỗi môi trường **50 tình huống đạt**, có kiểm tra đổi scope và hai trang cùng PDF |
| Node citation, analytics, recommendation model | Đạt; citation có 5 ca |
| Ruff, JS syntax, hai bộ catalog builder, diff check | Đạt |
| Tái lập corpus candidate offline | 120 file giống từng byte |
| Chrome truy cập form VNU công khai | Thành công, không gửi thông tin đăng nhập |

Pytest còn một cảnh báo Starlette/httpx đã tồn tại trước đợt sửa. Đây là cảnh báo
deprecation của test client; không có lỗi import, resolver hoặc test thất bại.
Không đổi HTTP client của toàn bộ bộ test trong phạm vi sửa môi trường này.
Corpus candidate có 106 tài liệu/chưa có chunk được duyệt; không phải corpus
portable v3 dùng cho RAG. Không crawl hoặc publish lại dữ liệu.

GitHub báo bốn check của upstream `11db811` đều thành công: offline, postgres,
hus_postgres, rag_demo. Đây là CI của upstream, chưa phải CI cho bản sửa local.
Không chạy lại 80 ca PostgreSQL local trong đợt sửa dependency; không sửa schema,
migration hay database sản phẩm.

App sản phẩm tại `127.0.0.1:8000` không phản hồi khi kiểm tra cuối. Không khởi động
hoặc dừng app/Docker trong đợt này. Các server RAG kiểm thử dùng port loopback
tạm thời và đã kết thúc. HUS RAG vẫn là demo riêng; không tự gắn vào product API.

## Dùng môi trường đã sửa

Từ PowerShell ở thư mục dự án:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip check
# Khi database đã chạy và được cấu hình:
python -m tools.run_local
# Hoặc mở riêng demo RAG, không cần database/tài khoản:
python -m tools.run_hus_rag_demo
```

Cài mới hoặc cập nhật máy khác:

```powershell
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
python -m pip check
python -m playwright install chromium ffmpeg
```

Chrome cần được cài riêng cho worker VNU. Mỗi phiên bản Playwright cần binary
tương ứng: [hướng dẫn Playwright](https://playwright.dev/python/docs/browsers).
Log, XML và manifest kiểm tra nằm trong
`backups/dependency_sync_20261103/`; ảnh/receipt RAG dưới `backups/hus_rag_demo/`.
