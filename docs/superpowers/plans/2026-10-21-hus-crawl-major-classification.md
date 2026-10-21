# Kế Hoạch Triển Khai: Phân Loại Dữ Liệu Crawl Theo Ngành Học & Tài Liệu Chung (HUS Module)

> **Mục tiêu:** Nâng cấp HUS Crawler & Document Pipeline để tự động phân loại tài liệu thu thập được theo 4 ngành đào tạo mục tiêu (`mathematics`, `mathematics_informatics`, `computer_science`, `data_science`) hoặc tài liệu dùng chung (`general`). Đồng thời cập nhật nhãn cho 98 tài liệu đã crawl sẵn trong kho dữ liệu mà không cần crawl lại từ đầu.

---

## 1. Phân Tích Hiện Trạng & Yêu Cầu

### 1.1. Hiện trạng
- **Model `HUSDocument`** ([`app/hus/models.py`](file:///f:/SE_Project/app/hus/models.py)): Hiện chỉ có `document_type` (`regulation`, `announcement`, `curriculum`, `form`, `general_info`) và `publisher` (`HUS`, `MIM`, `TUYENSINH`). Chưa có trường xác định ngành học.
- **Làm sạch `cleaning.py`** ([`app/hus/cleaning.py`](file:///f:/SE_Project/app/hus/cleaning.py)): Mới chỉ có hàm [`infer_document_type(title, content)`](file:///f:/SE_Project/app/hus/cleaning.py#L106-L122).
- **Dữ liệu hiện có** ([`data/hus/processed/catalog.json`](file:///f:/SE_Project/data/hus/processed/catalog.json)): 98 tài liệu đã crawl chứa thông tin ngành rõ ràng trong URL slug (`/toanhoc/`, `/toantin/`, `/khmt-tt/`, `/khoa-hoc-du-lieu/`) và trong tiêu đề.

### 1.2. Yêu cầu mới
1. Bổ sung trường `major` (kiểu `MajorCategory` enum) vào schema `HUSDocument`.
2. Tạo hàm trích xuất/suy luận ngành học `infer_major(title: str, url: str, content: str = "") -> MajorCategory`.
3. Tích hợp `infer_major` vào `HUSPipeline.process_document()`.
4. Viết script/chức năng gắn nhãn (backfill/migrate) cho toàn bộ 98 tài liệu hiện có trong `data/hus/processed/catalog.json`.
5. Đảm bảo toàn bộ test case cũ và mới đều pass 100%.

---

## 2. Thiết Kế Chi Tiết

### 2.1. Enum `MajorCategory` ([`app/hus/models.py`](file:///f:/SE_Project/app/hus/models.py))

```python
class MajorCategory(str, Enum):
    MATHEMATICS = "mathematics"                     # Ngành Toán học (kể cả CNTN Toán)
    MATHEMATICS_INFORMATICS = "mathematics_informatics" # Ngành Toán - Tin
    COMPUTER_SCIENCE = "computer_science"           # Ngành Máy tính & Khoa học thông tin
    DATA_SCIENCE = "data_science"                   # Ngành Khoa học dữ liệu
    GENERAL = "general"                             # Thông tin chung / Quy chế toàn trường
```

Trường bổ sung vào `HUSDocument`:
```python
major: MajorCategory = Field(
    default=MajorCategory.GENERAL,
    description="Ngành học áp dụng của tài liệu (hoặc 'general' nếu là quy định chung toàn trường)",
)
```

### 2.2. Logic Suy Luận Ngành `infer_major` ([`app/hus/cleaning.py`](file:///f:/SE_Project/app/hus/cleaning.py))

Thứ tự ưu tiên nhận diện:
1. **Khớp theo URL slug của Khoa Toán - Cơ - Tin học (MIM):**
   - Chứa `/category/khoa-hoc-du-lieu/` hoặc `/khoa-hoc-du-lieu` -> `DATA_SCIENCE`
   - Chứa `/category/khmt-tt/` hoặc `/khmt-tt` -> `COMPUTER_SCIENCE`
   - Chứa `/category/toantin/` hoặc `/toantin` -> `MATHEMATICS_INFORMATICS`
   - Chứa `/category/toanhoc/` hoặc `/toanhoc` -> `MATHEMATICS`
2. **Khớp theo từ khóa trong Tiêu đề (Title) & Đoạn đầu nội dung:**
   - **Khoa học dữ liệu:** `"khoa học dữ liệu"`, `"data science"`, `"khdl"`
   - **Máy tính & KH Thông tin:** `"máy tính và khoa học thông tin"`, `"khoa học máy tính"`, `"khmt-tt"`, `"khmttt"`, `"mt&khtt"`
   - **Toán - Tin:** `"toán - tin"`, `"toán tin"`, `"toantin"`, `"toán học và tin học"`, `"toán ứng dụng"`
   - **Toán học:** `"toán học"`, `"cử nhân tài năng toán"`, `"cntn toán"`, `"toán cơ"`
3. **Mặc định:**
   - Nếu không khớp hoặc thuộc quy chế tuyển sinh/đào tạo chung toàn trường -> `GENERAL`.

---

## 3. Các Bước Thực Hiện (Task-by-Task Implementation)

### Task 1: Cập nhật Models & Viết Unit Test cho `MajorCategory`
- **File sửa:** [`app/hus/models.py`](file:///f:/SE_Project/app/hus/models.py)
- **File test:** [`tests/hus/test_models.py`](file:///f:/SE_Project/tests/hus/test_models.py)
- **Hành động:**
  1. Thêm `MajorCategory` enum vào `models.py`.
  2. Bổ sung trường `major: MajorCategory = MajorCategory.GENERAL` vào `HUSDocument`.
  3. Viết test kiểm tra serialization/deserialization JSON có chứa trường `major`.
  4. Chạy `pytest tests/hus/test_models.py` xác nhận pass.

### Task 2: Hiện thực `infer_major` trong `cleaning.py` (TDD)
- **File sửa:** [`app/hus/cleaning.py`](file:///f:/SE_Project/app/hus/cleaning.py)
- **File test:** [`tests/hus/test_cleaning.py`](file:///f:/SE_Project/tests/hus/test_cleaning.py)
- **Hành động:**
  1. Viết test suite cho `infer_major` trong `test_cleaning.py` với các URL và tiêu đề mẫu của cả 4 ngành và tài liệu chung.
  2. Chạy test xác nhận fail.
  3. Viết hàm `infer_major(title: str, url: str, content: str = "") -> MajorCategory`.
  4. Chạy `pytest tests/hus/test_cleaning.py` xác nhận pass.

### Task 3: Tích hợp vào `HUSPipeline`
- **File sửa:** [`app/hus/pipeline.py`](file:///f:/SE_Project/app/hus/pipeline.py)
- **File test:** [`tests/hus/test_pipeline.py`](file:///f:/SE_Project/tests/hus/test_pipeline.py)
- **Hành động:**
  1. Trong `HUSPipeline.process_document()`, gọi `major = infer_major(title, raw_doc.url, text_content)`.
  2. Truyền `major=major` khi khởi tạo `HUSDocument`.
  3. Cập nhật và chạy test pipeline.

### Task 4: Viết migration script cập nhật nhãn cho 98 tài liệu hiện có
- **File tạo:** [`tools/migrate_catalog_majors.py`](file:///f:/SE_Project/tools/migrate_catalog_majors.py) (hoặc thêm flag `--reclassify-majors` vào [`tools/crawl_hus.py`](file:///f:/SE_Project/tools/crawl_hus.py))
- **Hành động:**
  1. Đọc file [`data/hus/processed/catalog.json`](file:///f:/SE_Project/data/hus/processed/catalog.json).
  2. Duyệt qua từng tài liệu, chạy `infer_major(doc.title, doc.source_url, doc.content_markdown)`.
  3. Cập nhật trường `major` và ghi lại file `catalog.json`.
  4. Xuất bảng thống kê số lượng tài liệu theo từng ngành (`mathematics`, `mathematics_informatics`, `computer_science`, `data_science`, `general`).

### Task 5: Chạy toàn bộ Test Suite và xác nhận chất lượng
- **Lệnh chạy:**
  - `python -m pytest tests/hus/`
  - `python -m ruff check app/hus tests/hus tools/`
- **Xác nhận:**
  - Toàn bộ test HUS pass 100%.
  - Dữ liệu `catalog.json` được phân loại chuẩn xác theo ngành.
