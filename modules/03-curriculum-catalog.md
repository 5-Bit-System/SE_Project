# Module 03: Curriculum Catalog Manager (`curriculum_catalog`)

## 1. Bản chất & Vai trò trong Hệ thống
Module **Curriculum Catalog Manager** là kho lưu trữ và quản lý tri thức của toàn bộ các Chương trình Đào tạo (CTĐT) trong hệ thống. Module này chịu trách nhiệm chuẩn hóa, xác thực và cung cấp dữ liệu học vụ từ 4 file PDF nguồn của trường Đại học Khoa học Tự nhiên (VNU-HUS) cho 4 ngành:
1. Toán học (`toan_hoc_7460101_2022`)
2. Toán - Tin học (`toan_tin_7460117_2022`)
3. Khoa học Máy tính và Thông tin (`khmtt_7480113qtd_2022`)
4. Khoa học Dữ liệu (`khdl_7460108_2022`)

Module bảo đảm việc lưu trữ độc lập giữa các ngành và giữ nguyên vẹn tính toàn vẹn của dữ liệu gốc.

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - Nạp và quản lý 4 bộ dữ liệu CTĐT độc lập (`curriculum.json`, `courses.json`, `source_rows.json`).
  - Quản lý metadata ngành: Mã ngành, Tên ngành, Số quyết định ban hành, Năm áp dụng, Tổng tín chỉ yêu cầu tốt nghiệp (thường 130–135 TC).
  - Quản lý cấu trúc môn học: Mã môn học chuẩn (`course_code`), Tên môn học tiếng Việt & tiếng Anh, Số tín chỉ lý thuyết/thực hành, Khối kiến thức (`knowledge_block`), Học kỳ khuyến nghị theo khung đào tạo.
  - Quản lý quan hệ tiên quyết thô từ tài liệu nguồn (bao gồm cả các môn tiên quyết liên ngành).
  - Ghi vết nguồn gốc dữ liệu: Đánh dấu số trang trong tài liệu PDF gốc (`source_page`), đánh dấu cờ `unverified` cho các môn học tham chiếu bên ngoài chưa thể kiểm chứng.
- **Ngoài phạm vi:**
  - Không tạo cấu trúc đồ thị DAG hay kiểm tra chu trình (thuộc Module 04).
  - Không đánh giá điều kiện sinh viên có được học hay không (thuộc Module 05).

---

## 3. Kiến trúc Nội bộ Module

```text
app/modules/curriculum_catalog/
├── __init__.py
├── repository.py               # Repository đọc dữ liệu từ data/curricula/
├── validator.py                # Kiểm tra tính toàn vẹn dữ liệu, tổng tín chỉ, khối kiến thức
└── schemas.py                  # Pydantic models: Course, Program, KnowledgeBlock, Catalog
```

---

## 4. Hợp đồng Giao tiếp Dữ liệu (Data Contracts)

### Model: `Course`
```python
class Course(BaseModel):
    code: str                                   # Ví dụ: "MAT1041"
    name: str                                   # Ví dụ: "Giải tích 1"
    credits: int                                # Số tín chỉ (ví dụ: 4)
    knowledge_block: str                        # "general", "foundation", "specialized", "elective"
    recommended_semester: int                   # Học kỳ đề xuất (1 -> 8)
    recommended_year: int                       # Năm học đề xuất (1 -> 4)
    prerequisites_raw: list[list[str]]          # [[A, B], [C]] -> (A hoặc B) và C
    source_page: int | None = None              # Trang PDF gốc
    is_verified: bool = True                    # False nếu có mã tiên quyết ngoài chưa xác minh
```

### Model: `ProgramCatalog`
```python
class ProgramInfo(BaseModel):
    program_id: str                             # "khdl_7460108_2022"
    name: str                                   # "Khoa học Dữ liệu"
    decision_number: str                        # Số quyết định
    total_required_credits: int                 # 135 tín chỉ
    knowledge_blocks: list[dict]

class Catalog(BaseModel):
    program: ProgramInfo
    courses: list[Course]
```

---

## 5. Thuật toán & Quy tắc Xử lý Cốt lõi
1. **Quy tắc Cô lập Tuyệt đối giữa các Ngành (Isolation):**
   - Dữ liệu của 4 ngành được lưu trong các thư mục riêng biệt tại `data/curricula/`.
   - Khi hệ thống nạp catalog theo `program_id`, chỉ trả về đúng danh sách môn học của ngành đó. Trùng mã môn giữa hai ngành (ví dụ môn Triết học `PHI1006` có mặt ở cả 4 ngành) vẫn được quản lý thành hai thực thể độc lập trong ngữ cảnh của từng ngành.
2. **Quy tắc Kiểm tra Cơ cấu Tín chỉ (Credit Balance Validation):**
   - Đối chiếu tổng số tín chỉ của các môn bắt buộc + hạn ngạch các nhóm môn tự chọn với tổng chỉ tiêu trong khung CTĐT.
   - Nếu phát hiện độ lệch giữa tổng các hàng chi tiết và số tổng ghi trên tiêu đề PDF (ví dụ lỗi nguồn của KHDL ghi 28/63 TC nhưng thực tế 28/57 TC), hệ thống ghi log cảnh báo và giữ nguyên số liệu bảng chi tiết kèm ghi chú giải thích.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** Nạp thành công toàn bộ 4 Catalog độc lập từ đĩa mà không phát sinh lỗi dữ liệu.
- **TC-02:** Mọi môn học trong Catalog đều có `code` không rỗng, `credits > 0`, và thuộc một khối kiến thức hợp lệ.
- **TC-03:** Các trường hợp tham chiếu môn tiên quyết ngoài CTĐT tự động được gán nhãn `is_verified = False` và cảnh báo rõ ràng.
- **TC-04:** Báo lỗi `CatalogNotFoundError` (HTTP 404) khi truy vấn một `program_id` không tồn tại.

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🟢 **Đã xong 95%** — Dữ liệu và loader hoàn chỉnh.
- **Hiện có trong codebase:**
  - Thư mục [`data/curricula/`](file:///e:/SE_Project/data/curricula/) chứa đầy đủ 4 thư mục ngành: `toan_hoc_7460101_2022`, `toan_tin_7460117_2022`, `khmtt_7480113qtd_2022`, `khdl_7460108_2022` với `courses.json`, `curriculum.json`, `source_rows.json`.
  - File [`app/catalog.py`](file:///e:/SE_Project/app/catalog.py) quản lý nạp dữ liệu, kiểm tra lỗi và cô lập ngành.
  - Các API: `GET /programs`, `GET /courses?program_id=...`.
  - Bộ test dữ liệu [`tests/test_curriculum_data.py`](file:///e:/SE_Project/tests/test_curriculum_data.py) (11 tests pass).
- **Nhiệm vụ cần thực hiện:**
  1. Duy trì cập nhật nếu có điều chỉnh bổ sung từ phía hội đồng đào tạo.
