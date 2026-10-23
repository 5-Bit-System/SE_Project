# Tiến độ chuyển học vụ sang bảng điểm VNU — 23/10/2026

Triển khai theo [kế hoạch chuyển đổi](KE_HOACH_CHUYEN_SANG_BANG_DIEM_VNU_2026_10_23.md)
bằng project-toolkit. Tiến độ ước tính toàn kế hoạch: **30%**. Đây là nền tảng
backend đã kiểm thử offline; chưa phải bản chuyển đổi hoàn chỉnh để dùng dữ liệu thật.

Người dùng xác nhận chưa biết ngành/khóa và muốn làm đăng nhập, database sau.
Đợt này không sửa luồng đăng nhập, schema, dữ liệu thật hoặc cấu hình môi trường;
API mới tái sử dụng bộ đọc profile/snapshot và kiểm tra phiên hiện có.

## Đã thực hiện

- `app/academic_context.py`: tạo context từ snapshot theo chủ tài khoản,
  catalog và policy có phiên bản. Không đưa dữ liệu nguồn vào `TranscriptRecord`
  vốn có ngưỡng điểm và xử lý học lại không phù hợp để dùng trực tiếp.
- Giữ tham chiếu từng hàng nguồn; không sửa snapshot, chọn điểm cao nhất/lần
  cuối, bỏ hậu tố mã môn hoặc suy ngành/khóa từ mã sinh viên.
- Chặn nguồn chưa đầy đủ, schema/hàng không hợp lệ, thiếu bằng chứng gắn chương
  trình, thiếu policy, học lại chưa rõ, mã chưa khớp và điểm mâu thuẫn.
  Thiếu điểm không mặc định đạt; điểm 0 vẫn khác dữ liệu chưa biết.
- `app/api/academic.py`: thêm API `/me/academic-context`, `/me/eligibility`,
  `/me/academic-progress`, `/me/recommendations`, `/me/advisor/chat`.
  Lấy owner từ phiên và bảng điểm từ backend; từ chối owner/records/passed set
  trong request. Điều kiện học, tiến độ, gợi ý và advisor dùng cùng context.
- Revision phụ thuộc phiên, snapshot, nội dung catalog, binding, policy và
  track/path. Gợi ý/chat kiểm tra lại sau tác vụ chậm; nguồn đổi trả 409,
  phiên mất/hết hạn trả 401. Các response cá nhân có `Cache-Control: no-store`.
- Không tự tính GPA dự án từ nguồn. GPA trên hồ sơ vẫn là thông tin nguồn;
  API tiến độ mới trả `gpa: null`.

## Chưa thực hiện / điều kiện chuyển đổi

1. Chưa chứng minh connector đã lấy toàn bộ bảng điểm: parser hiện trả
   `completeness=unknown`. Không đổi thành complete từ số hàng/tổng tín chỉ.
2. Chưa có binding chương trình/quy chế được xác minh cho tài khoản thật.
   Registry policy production đang rỗng; không có endpoint cho sinh viên tự
   đặt cờ đã xác minh. Policy/binding trong test là giả lập và không áp dụng thật.
3. Catalog revision hiện là fingerprint nội dung để kiểm thử nền tảng,
   chưa phải khóa revision được ràng buộc trong database. Phần lưu/review
   binding và policy thuộc đợt database sau.
4. `/me/recommendations/what-if` mới có kiểm tra readiness và trả
   `academic_baseline_not_available` nếu context đã sẵn sàng; chưa triển khai
   baseline do server quản lý. Không coi đây là tính năng what-if hoàn chỉnh.
5. Chưa nối frontend sang API mới, chưa xóa UI nhập điểm và API cũ. Chỉ xóa
   cùng đợt khi luồng VNU thay thế qua điều kiện nghiệm thu của kế hoạch.
6. Chưa nghiệm thu live, chạy kiểm thử PostgreSQL hoặc kiểm thử trình duyệt
   cho luồng mới. Không restart server, không gọi portal hoặc dùng credentials.

## Kiểm chứng

42 test mới dùng dữ liệu tổng hợp trong `tests/integrations/test_academic_context.py`
và `test_academic_api.py`; chỉ thay bộ đọc storage tại boundary để kiểm thử API.
Domain rules/progress/recommendation/advisor fallback chạy thật trong các ca
context sẵn sàng. Không lưu bảng điểm hay thông tin cá nhân thật vào fixtures.

```powershell
.venv/Scripts/python.exe -m pytest tests -q -m "not postgres and not hus_postgres" --full-catalog-root docs/acceptance/hus_2022 --tb=short
```

Kết quả: **377 passed, 38 deselected**; một cảnh báo deprecation có sẵn của
Starlette/httpx. Ruff trên code/test thay đổi và `git diff --check` đạt.

Review inline theo checklist toolkit: context và API mới chỉ là nền tảng,
không công bố sẵn sàng cho tài khoản thật. Các phần chưa review live, UI,
DB/binding và baseline được giữ trong danh sách trên; không âm thầm bỏ scope.
Không commit/push. Các thay đổi portal/frontend từ đợt trước được giữ nguyên.

## Nguồn đã tra, chưa xác nhận áp dụng cho tài khoản

[Danh mục quy chế đại học HUS](https://hus.vnu.edu.vn/tai-lieu-bieu-mau/quy-dinh-quy-che/dao-tao/dai-hoc)
và [bản quy chế 3626 trên website đơn vị thuộc VNU](https://ussh.vnu.edu.vn/vi/van-ban/detail/Quy-che-dao-tao-dai-hoc-tai-Dai-hoc-Quoc-gia-Ha-Noi-Ap-dung-tu-khoa-QH-2022-X-19452/?download=1&id=0).
Việc tìm thấy quy chế chưa đủ để tự gắn chương trình/khóa hoặc quyết định
policy học lại, miễn/chuyển đổi cho dữ liệu thật.
