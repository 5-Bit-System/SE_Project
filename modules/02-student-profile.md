# Module 02: Student Profile & Progress Tracker (`student_profile`)

## 1. Bản chất & Vai trò trong Hệ thống
Module **Student Profile & Progress Tracker** là trung tâm quản lý dữ liệu học vụ cá nhân của sinh viên trong phiên làm việc. Module này tiếp nhận danh sách môn học đã chuẩn hóa từ Module 01, thực hiện tính toán các chỉ số học vụ học thuật (GPA, số tín chỉ tích lũy hợp lệ), theo dõi tiến độ hoàn thành theo từng khối kiến thức của chương trình đào tạo, và đặc biệt là **tự động phân tích ma trận môn học để nhận diện sinh viên thuộc ngành đào tạo nào**.

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - Nhận diện ngành học (`detect_program`): So khớp tập môn đã học với 4 chương trình đào tạo (Toán học, Toán - Tin, KHMT&TT, KHDL) để xác định ngành có tỷ lệ tương đồng cao nhất.
  - Phân loại trạng thái môn: Môn đã đạt (điểm $\ge 5.0$), Môn chưa đạt / học lại (điểm $< 5.0$).
  - Tính tổng số tín chỉ tích lũy (`earned_credits`): Loại trừ các học phần điều kiện theo quy chế đào tạo (Giáo dục thể chất `PES1000`, Giáo dục quốc phòng `CME1000`).
  - Tính điểm trung bình chung tích lũy (GPA) thang điểm 10 và quy đổi thang điểm 4.
  - Thống kê tỷ lệ hoàn thành theo từng khối kiến thức: Khối đại cương, Cơ sở nhóm ngành, Cơ sở ngành, Chuyên ngành và Tốt nghiệp.
  - Bảo đảm nguyên tắc **Cô lập ngành (Major Isolation)**: Kiểm tra không để sót môn học của ngành khác lẫn vào hồ sơ hiện hành.
- **Ngoài phạm vi:**
  - Không đọc trực tiếp file PDF/ảnh (thuộc Module 01).
  - Không kiểm tra điều kiện tiên quyết cho kỳ tới (thuộc Module 05).

---

## 3. Kiến trúc Nội bộ Module

```text
app/modules/student_profile/
├── __init__.py
├── service.py                  # Dịch vụ tính GPA, tổng tín chỉ, tiến độ khối kiến thức
├── detector.py                 # Thuật toán so khớp ma trận nhận diện ngành học
└── schemas.py                  # Pydantic models: StudentTranscript, ProgressSummary
```

---

## 4. Hợp đồng Giao tiếp Dữ liệu (Data Contracts)

### Input Contract: `TranscriptInput`
```python
class CourseGradeEntry(BaseModel):
    course_code: str
    grade: float | None = None
    passed: bool | None = None

class StudentTranscript(BaseModel):
    program_id: str | None = None               # Ngành được chọn hoặc None (để auto-detect)
    courses: list[CourseGradeEntry] = []
    current_semester: int = 1                   # Kỳ học hiện tại
```

### Output Contract: `StudentProgressSummary`
```python
class BlockProgress(BaseModel):
    block_id: str                               # general, foundation, specialized, elective
    block_name: str
    required_credits: int
    earned_credits: int
    completion_percentage: float

class StudentProgressSummary(BaseModel):
    program_id: str
    program_name: str
    total_earned_credits: int
    gpa_10: float
    gpa_4: float
    passed_course_codes: list[str]
    failed_course_codes: list[str]
    block_progress: list[BlockProgress]
    detected_programs: list[dict]               # Kết quả xếp hạng độ khớp các ngành
    isolation_passed: bool                      # Xác nhận không lẫn môn ngoài ngành
```

---

## 5. Thuật toán & Quy tắc Xử lý Cốt lõi
1. **Thuật toán Nhận diện Ngành học (`detect_program`):**
   - Lấy tập hợp mã môn học sinh viên đã học: $S = \{c_1, c_2, \dots, c_n\}$.
   - Với mỗi ngành $P_k$ trong 4 Catalog, lấy tập mã môn thuộc ngành đó $C_k$.
   - Tính toán chỉ số tương đồng (Jaccard & Specificity):
     $$\text{Overlap}(S, C_k) = |S \cap C_k|$$
     $$\text{Specificity}(S, C_k) = \sum_{c \in S \cap C_k} w(c) \quad \text{với } w(c) \text{ cao nếu } c \text{ chỉ xuất hiện riêng ở ngành } k$$
   - Sắp xếp độ khớp giảm dần và đề xuất ngành có điểm số cao nhất.
2. **Quy tắc Tính Tín chỉ Tích lũy Hợp lệ:**
   - Điều kiện đạt: $\text{grade} \ge 5.0$ hoặc $\text{passed} == \text{True}$.
   - Trừ mã môn điều kiện: Nếu $c \in \{\text{PES1000}, \text{CME1000}\}$ thì không cộng vào tổng tín chỉ tích lũy xét tốt nghiệp.
   - Tránh tính lặp: Nếu sinh viên học cải thiện môn $c$ nhiều lần, chỉ lấy 1 lần điểm đạt cao nhất.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** Tự động nhận diện chính xác ngành học khi nhập danh sách môn có tính đặc thù (ví dụ chứa môn `MAT1093` $\rightarrow$ ưu tiên Toán/Toán-Tin; chứa `INT2202` $\rightarrow$ KHMT&TT; chứa `DSA2001` $\rightarrow$ KHDL).
- **TC-02:** Tính đúng tổng tín chỉ: một sinh viên học 20 tín chỉ gồm 3 TC Thể dục và 4 TC Quân sự thì tổng tín chỉ tích lũy chỉ là $13$ TC.
- **TC-03:** Tính đúng GPA thang 10 có tính trọng số theo số tín chỉ của từng môn học.
- **TC-04:** Xác thực Major Isolation: trả về cảnh báo `foreign_courses_detected` nếu có môn học không thuộc ngành đã chọn.

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🟢 **Đã xong 80%** — Hoàn thành các tính năng học vụ cốt lõi.
- **Hiện có trong codebase:** File [`app/transcript.py`](file:///e:/SE_Project/app/transcript.py) đã thực hiện:
  - Tính tín chỉ tích lũy (loại trừ `PES1000`, `CME1000`).
  - Tính GPA thang 10 có trọng số tín chỉ.
  - Tự động nhận diện ngành học khớp nhất (`detect_program_from_courses`) kèm API `POST /transcript/detect-program`.
  - Kiểm tra cô lập ngành (Major Isolation).
- **Nhiệm vụ cần thực hiện:**
  1. Bổ sung bảng quy đổi GPA sang thang điểm 4 theo chuẩn đại học.
  2. Bổ sung thống kê tiến độ % hoàn thành theo từng khối kiến thức (`BlockProgress`).
