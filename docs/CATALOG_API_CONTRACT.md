# Hợp đồng API Catalog — P1-03

Hai endpoint đọc catalog dùng JSON và trả danh sách trực tiếp. Schema thực thi nằm ở `ProgramResponse`, `CourseResponse`, `CatalogErrorResponse` trong `app/models.py`; OpenAPI ở `/openapi.json`, giao diện tài liệu ở `/docs`.

Hiện handler nằm trong `app/main.py`. Khi refactor, chuyển hai handler và schema sang `app/modules/catalog/router.py`, `schemas.py`; `app/main.py` đăng ký router Catalog. Giữ nguyên URL, query, mã trạng thái và response theo tài liệu này. API gợi ý thuộc Recommendation.

## GET /programs

Không có query bắt buộc. `200 application/json` trả `ProgramResponse[]`, sắp xếp theo `program_id` của các thư mục hợp lệ. Với dữ liệu hiện tại có bốn ngành: KHDL 65 môn, KHMTTT 67, Toán học 90 và Toán tin 68. Thư mục catalog hợp lệ nhưng trống trả `[]`.

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `program_id` | string | ID dùng nguyên vẹn cho query `/courses` và hồ sơ gợi ý |
| `name` | string | Tên hiển thị |
| `total_credits` | integer > 0 | Tổng TC yêu cầu của chương trình |
| `catalog_status` | `draft_unverified` hoặc `verified` | Trạng thái review catalog |
| `source_file`, `source_pages` | string | Thông tin PDF nguồn |
| `notes` | string[] | Ghi chú/cảnh báo; mặc định `[]` |
| `choice_groups` | object[] | Mỗi nhóm có `id`, `name`, `required_credits` ≥ 0; mặc định `[]` |
| `course_count` | integer ≥ 0 | Số mã môn duy nhất của chính ngành đó |

Metadata mở rộng từ curriculum được giữ, gồm `blocks`, `track_selection`, `graduation_selection`, `source_issues`, `digitization` và metadata nhóm. UI phải chấp nhận trường bổ sung và không dùng `course_count` làm tổng TC. Lỗi bất kỳ catalog nào trả `503`, tránh trả danh sách ngành thiếu mà UI tưởng đã đầy đủ.

Ví dụ trích các trường của một mục trong danh sách (các trường nguồn, nhóm và metadata mở rộng được lược bỏ):

```json
[
  {
    "program_id": "toan_hoc_7460101_2022",
    "name": "Toán học (khóa 2022)",
    "total_credits": 135,
    "catalog_status": "draft_unverified",
    "course_count": 90
  }
]
```

## GET /courses?program_id=...

`program_id` bắt buộc, là chuỗi không rỗng lấy từ `/programs`. Loader đối chiếu ID với thư mục hợp lệ; đường dẫn tuyệt đối và chuỗi traversal bị từ chối. `200 application/json` trả `CourseResponse[]` chỉ của ngành đã chọn, giữ thứ tự catalog; catalog có danh sách môn rỗng trả `[]`.

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `code`, `name`, `block` | string | Mã, tên Việt, khối kiến thức |
| `credits` | integer > 0 | TC của môn |
| `name_en` | string hoặc null | Tên Anh nếu có |
| `prerequisites` | string[][] | AND giữa các danh sách; OR giữa mã trong một danh sách; `[]` là không có tiên quyết |
| `prerequisites_raw` | string | Điều kiện chép nguyên văn |
| `prerequisite_status` | `transcribed` hoặc `source_conflict` | Môn có xung đột nguồn phải được giữ trạng thái |
| `prerequisite_variants` | string[][][] | Các bản tiên quyết từ mọi lần xuất hiện trong nguồn |
| `external_prerequisite_codes` | string[] | Tham chiếu ngoài bảng ngành, chưa xác minh tương đương |
| `choice_group_ids` | string[] | Môn có thể thuộc nhiều nhóm |
| `source_page` | integer hoặc null | Trang PDF của lần xuất hiện đầu |
| `source_rows` | integer[] | Các STT nguồn; môn không đánh STT có thể là `[]` |

Các danh sách trên mặc định `[]`, `prerequisites_raw` mặc định `""`, `name_en`/`source_page` mặc định null và `prerequisite_status` mặc định `transcribed` nếu thiếu trong model. Metadata mở rộng như `hours`, `counted_in_total`, `requirement_type`, `graduation_path_ids` vẫn được giữ. UI dùng mã làm định danh trong **ngành đang chọn**, không gộp hoặc giữ lựa chọn chỉ vì hai ngành cùng mã.

Ví dụ một mục đầy đủ trong response Toán học (response thực tế có 90 mục):

```json
[
  {
    "code": "MAT2505",
    "name": "Lập trình cơ bản",
    "credits": 3,
    "block": "group",
    "prerequisites": [["HUS1011"]],
    "prerequisite_status": "transcribed",
    "choice_group_ids": ["programming"],
    "source_page": 10,
    "name_en": "Introduction to Programming",
    "requirement_type": "elective",
    "counted_in_total": true,
    "hours": {"lecture": 22, "practice": 46, "self_study": 82},
    "instruction_language": null,
    "prerequisites_raw": "HUS1011",
    "prerequisite_variants": [[["HUS1011"]]],
    "external_prerequisite_codes": [],
    "graduation_path_ids": [],
    "source_rows": [32]
  }
]
```

Với KHMTTT, cùng mã có `block = "discipline"` và `choice_group_ids = []`. Response đầy đủ của cả bốn ngành được kiểm tra với catalog thật trong `tests/test_catalog_api.py`.

## Status và lỗi

| Endpoint | Status | Điều kiện | Body |
|---|---:|---|---|
| Cả hai | 200 | Đọc và kiểm tra thành công | Danh sách tương ứng |
| `/courses` | 404 | Ngành không tồn tại hoặc nhập đường dẫn tùy ý | `{"detail": "Không tìm thấy chương trình: <program_id>"}` |
| `/courses` | 422 | Thiếu/rỗng query `program_id` | `{"detail": [...]}` theo validation FastAPI |
| Cả hai | 503 | Thư mục/file thiếu, đọc lỗi, JSON sai hoặc catalog không hợp lệ | `{"detail": "Không thể tải dữ liệu catalog. Vui lòng thử lại sau."}` |

`404`/`503` dùng `detail` dạng string. `422` dùng danh sách lỗi, mỗi lỗi có `loc`, `msg`, `type`; các trường bổ sung có thể thay đổi. Ví dụ thiếu query:

```json
{"detail": [{"type": "missing", "loc": ["query", "program_id"], "msg": "Field required", "input": null}]}
```

Lỗi dữ liệu nội bộ giữ nguyên nguyên nhân ở loader nhưng không gửi đường dẫn máy chủ trong response `503`. `source_conflict` đã được ghi nhận không làm endpoint thất bại; API trả nguyên các biến thể để module luật xử lý, không tự chọn điều kiện từ PDF.

## Bàn giao kiểm thử với Người 2 và Người 5

Các test dưới đây chạy tự động tại workspace; review chung với thành viên nhóm chưa được ghi nhận.

Kết quả ngày 09/10/2026: `python -m pytest -q` đạt **122 passed, 1 skipped**, gồm test trình duyệt Chromium. Test bị bỏ qua là ca tạo symlink của loader do quyền môi trường, không phải test UI. `git diff --check` đạt.

| Người phối hợp | Ca kiểm tra | Bằng chứng tự động |
|---|---|---|
| Người 2 | `200`, schema JSON, metadata và số môn cả bốn ngành | `tests/test_catalog_api.py` |
| Người 2 | `404` ngành lạ/path, `422` thiếu/rỗng query, `503` lỗi nguồn | `tests/test_catalog_api.py` |
| Người 2 | Cùng mã giữ nhóm/ngành riêng, xung đột tiên quyết còn đủ bản | `tests/test_catalog_api.py` |
| Người 5 | Đổi qua bốn ngành, chỉ hiện môn đúng ngành, xóa checkbox/kết quả cũ | `tests/test_catalog_ui.py` |
| Người 5 | Đổi nhanh A → B → A; bỏ qua response môn cũ cả thành công và lỗi | `tests/test_catalog_ui.py` |
| Người 5 | Gợi ý đang chờ rồi đổi ngành; response gợi ý cũ không được hiện | `tests/test_catalog_ui.py` |
| Người 5 | Loading/lỗi tải môn khóa nút gửi; đổi ngành tải lại rồi gửi đúng ID/mã | `tests/test_catalog_ui.py` |

Chạy API và toàn bộ test Python:

```powershell
python -m pytest -q
```

Để chạy cả test trình duyệt khi máy chưa có Playwright/Chromium:

```powershell
python -m pip install -r requirements-ui.txt
python -m playwright install chromium
python -m pytest -q tests/test_catalog_ui.py
```

Test trình duyệt dùng HTML/JS thật và FastAPI TestClient, điều khiển thứ tự response qua interception; không cần khởi động uvicorn. Nếu chưa cài Playwright hoặc Chromium, các test UI được đánh dấu skipped; kết quả này không xác nhận UI đã đạt.

Checklist review trực tiếp dành cho Người 5: chạy app trên trình duyệt, đổi qua cả bốn ngành; bật giới hạn tốc độ mạng rồi đổi nhanh; đánh dấu môn và nhận gợi ý trước khi đổi ngành; kiểm tra tên ngành, số môn, checkbox và kết quả đều thuộc lựa chọn cuối. Ghi người review, ngày và kết quả sau khi thực hiện; phần này đang chờ review chung.
