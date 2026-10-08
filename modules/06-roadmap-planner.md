# Module 06: Curriculum Roadmap Allocator (`roadmap_planner`)

## 1. Bản chất & Vai trò trong Hệ thống
Sinh viên không chỉ quan tâm đến việc kỳ tới nên học môn gì, mà còn cần một cái nhìn trực quan toàn diện về **bức tranh lộ trình học tập 4 năm (8 học kỳ)** của mình: Môn nào nên học ở Năm 1, Năm 2, Năm 3, Năm 4; môn nào là điều kiện tiên quyết mở đường cho các năm sau; và hiện tại sinh viên đang đứng ở đâu trong lộ trình đó.
Module **Curriculum Roadmap Allocator** đảm nhận việc ánh xạ và phân bổ toàn bộ danh mục môn học của chương trình đào tạo vào 4 năm học bảo đảm tính topo của đồ thị, đồng thời gắn nhãn trạng thái thời gian thực của sinh viên lên từng môn.

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - Tiếp nhận Catalog ngành từ Module 03, đồ thị môn học từ Module 04, và kết quả kiểm tra điều kiện từ Module 05.
  - Phân bổ môn học vào 4 mốc năm học chính:
    - **Năm 1 (Kỳ 1, Kỳ 2):** Khối kiến thức đại cương, toán cơ bản, lập trình nhập môn.
    - **Năm 2 (Kỳ 3, Kỳ 4):** Cơ sở nhóm ngành và cơ sở khối ngành.
    - **Năm 3 (Kỳ 5, Kỳ 6):** Các môn chuyên ngành cốt lõi và môn tự chọn chuyên sâu.
    - **Năm 4 (Kỳ 7, Kỳ 8):** Thực tập doanh nghiệp, các chuyên đề nâng cao, khóa luận tốt nghiệp hoặc các học phần thay thế.
  - Gắn nhãn trạng thái sinh viên cho từng môn trong lộ trình:
    - `completed` (Đã hoàn thành - Xanh lá).
    - `eligible` (Đủ điều kiện đăng ký kỳ tiếp theo - Xanh dương).
    - `blocked` (Bị khóa do còn thiếu môn tiên quyết - Đỏ/Xám).
    - `upcoming` (Kỳ sau nữa theo tiến độ chuẩn).
- **Ngoài phạm vi:**
  - Không xếp thời khóa biểu chi tiết (thứ, tiết học, phòng học).
  - Không xếp hạng độ ưu tiên môn học (thuộc Module 07).

---

## 3. Kiến trúc Nội bộ Module

```text
app/modules/roadmap_planner/
├── __init__.py
├── allocator.py                # Thuật toán phân bổ môn theo năm và kiểm tra topo
└── schemas.py                  # Pydantic models: CurriculumRoadmap, YearPlan, CourseRoadmapItem
```

---

## 4. Hợp đồng Giao tiếp Dữ liệu (Data Contracts)

### Model: `CurriculumRoadmap`
```python
class CourseRoadmapItem(BaseModel):
    code: str
    name: str
    credits: int
    knowledge_block: str
    recommended_semester: int
    status: Literal["completed", "eligible", "blocked", "upcoming"]
    missing_prerequisites: list[str] = []

class KnowledgeBlockSummary(BaseModel):
    block_name: str
    total_credits: int
    courses: list[CourseRoadmapItem]

class YearRoadmap(BaseModel):
    year: int                                   # 1, 2, 3, 4
    title: str                                  # "Năm 1: Nền tảng Đại cương", ...
    total_credits: int
    blocks: list[KnowledgeBlockSummary]

class CurriculumRoadmap(BaseModel):
    program_id: str
    program_name: str
    years: list[YearRoadmap]                    # 4 năm học
    overall_progress_percentage: float          # Tỷ lệ hoàn thành toàn khóa
```

---

## 5. Thuật toán & Quy tắc Xử lý Cốt lõi
1. **Thuật toán Phân bổ Năm học (Year Allocation Algorithm):**
   - Lấy học kỳ khuyến nghị `recommended_semester` ($1 \dots 8$) từ khung CTĐT chuẩn.
   - Gán chỉ số năm học: $\text{year} = \lceil \text{recommended\_semester} / 2 \rceil$.
   - **Kiểm định Topo ngược (Reverse Topo Constraint):**
     Nếu môn $B$ được xếp ở Năm $k$, thì mọi môn tiên quyết $A$ của môn $B$ bắt buộc phải được xếp ở Năm $j \le k$. Nếu phát hiện mâu thuẫn trong dữ liệu gốc, hệ thống tự động đẩy môn $B$ sang năm tiếp theo để bảo đảm tính sư phạm và khả năng tiếp thu kiến thức.
2. **Quy tắc Gắn Trạng thái Động (Dynamic Status Tagging):**
   - Với mỗi môn $C$ trong khung 4 năm:
     - Nếu $C \in \text{PassedCourses} \implies \text{status} = \text{"completed"}$.
     - Nếu $C \notin \text{PassedCourses}$ và $C \in \text{EligibleCourses} \implies \text{status} = \text{"eligible"}$.
     - Nếu $C \notin \text{PassedCourses}$ và $C \in \text{BlockedCourses} \implies \text{status} = \text{"blocked"}$.
     - Các môn còn lại theo tiến độ năm sau $\implies \text{status} = \text{"upcoming"}$.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** Lộ trình trả về luôn đủ 4 năm (Năm 1 $\rightarrow$ Năm 4) cho toàn bộ 4 ngành đào tạo.
- **TC-02:** Không bao giờ xuất hiện trường hợp môn học có trạng thái `eligible` lại thiếu môn tiên quyết.
- **TC-03:** Khi sinh viên đã vượt qua một môn (ví dụ `MAT1041`), trạng thái của môn đó trong Năm 1 phải đổi thành `completed` và các môn Năm 2 phụ thuộc vào nó (như `MAT1042`) phải chuyển từ `blocked` sang `eligible`.
- **TC-04:** Tổng số tín chỉ phân bổ qua 4 năm bằng đúng tổng số tín chỉ của chương trình đào tạo.

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🟢 **Đã xong 90%** — Hoàn thiện phân bổ 4 năm và gắn nhãn trạng thái sinh viên.
- **Hiện có trong codebase:** File [`app/planner.py`](file:///e:/SE_Project/app/planner.py) và API `GET /roadmap`, `POST /roadmap` đã xử lý:
  - Phân bổ toàn bộ môn học vào Năm 1, 2, 3, 4 theo khối kiến thức.
  - Gắn trạng thái sinh viên (`completed`, `eligible`, `blocked`, `upcoming`).
  - Toàn bộ 5 bài test trong [`tests/test_planner.py`](file:///e:/SE_Project/tests/test_planner.py) đều PASS.
- **Nhiệm vụ cần thực hiện:**
  1. Hỗ trợ hiển thị trực quan dạng sơ đồ đồ thị tương tác (Visual Flowchart) trên Web UI.
