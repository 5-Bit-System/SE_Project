# Module 05: Rule-Based Eligibility Engine (`eligibility_rules`)

## 1. Bản chất & Vai trò trong Hệ thống
Module **Rule-Based Eligibility Engine** là **cổng chặn bắt buộc (Hard Constraint Gate)** của hệ thống. Trong tư vấn học vụ, việc gợi ý cho sinh viên một môn học mà sinh viên chưa đủ điều kiện tiên quyết là một sai sót nghiêm trọng.
Do đó, Module này chịu trách nhiệm kiểm tra tất cả các quy tắc đào tạo cứng. **Nguyên tắc bất biến của hệ thống: Tỷ lệ vi phạm điều kiện học vụ (Eligibility Violation Rate) bắt buộc phải tuyệt đối bằng 0.0%**. Tuyệt đối không để bất kỳ môn học nào chưa đủ điều kiện lọt sang bước xếp hạng (Ranking) hay trợ lý AI.

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - Nhận vào Catalog của ngành đã chọn và danh sách các môn sinh viên đã hoàn thành (từ Module 02).
  - Loại bỏ các môn học sinh viên đã hoàn thành (điểm $\ge 5.0$).
  - **Đánh giá biểu thức tiên quyết Boole phức tạp:** Xử lý đầy đủ quan hệ dạng `AND` và `OR` (ví dụ: `[[A, B], [C]]` tức là *(A hoặc B) VÀ C*).
  - Kiểm tra điều kiện số tín chỉ tích lũy tối thiểu (ví dụ: yêu cầu $\ge 105$ tín chỉ để được đăng ký Khóa luận tốt nghiệp hoặc Thực tập doanh nghiệp).
  - Kiểm tra hạn mức tín chỉ tối đa sinh viên được phép đăng ký trong một học kỳ (mặc định tối đa 24 tín chỉ).
  - Kiểm tra hạn ngạch của nhóm tự chọn (Elective Group Quota): Nếu sinh viên đã hoàn thành đủ số tín chỉ tự chọn yêu cầu của nhóm thì đánh dấu nhóm đã đầy.
  - Phân loại rạch ròi 2 tập môn: **Tập đủ điều kiện (`eligible_courses`)** và **Tập bị chặn (`blocked_courses`)** kèm mã lý do cụ thể.
- **Ngoài phạm vi:**
  - Không xếp hạng môn nào nên học hơn (thuộc Module 07).
  - Không sinh câu trả lời chat tự nhiên (thuộc Module 09).

---

## 3. Kiến trúc Nội bộ Module

```text
app/modules/eligibility_rules/
├── __init__.py
├── engine.py                   # Bộ máy duyệt điều kiện tiên quyết Boole (AND/OR)
├── credit_checker.py           # Bộ kiểm tra điều kiện tín chỉ và hạn ngạch tự chọn
└── schemas.py                  # Pydantic models: EligibilityResult, BlockedCourseDetail
```

---

## 4. Hợp đồng Giao tiếp Dữ liệu (Data Contracts)

### Model: `EligibilityRequest` & `EligibilityResult`
```python
class EligibilityRequest(BaseModel):
    program_id: str
    passed_course_codes: list[str]
    max_credits: int = 24                       # Giới hạn đăng ký cho kỳ tiếp theo

class BlockedCourseDetail(BaseModel):
    course_code: str
    course_name: str
    credits: int
    missing_prerequisites: list[list[str]]      # Các nhóm điều kiện chưa thỏa
    blocked_reasons: list[str]                  # "missing_prerequisite", "credit_threshold_not_met", "group_quota_full"
    explanation_text: str                       # Giải thích dạng văn bản ngắn gọn

class EligibilityResult(BaseModel):
    program_id: str
    eligible_courses: list[Course]              # Danh sách Course đủ điều kiện
    blocked_courses: list[BlockedCourseDetail]  # Danh sách môn bị chặn kèm lý do
    total_eligible_credits: int
    violation_rate: float = 0.0                 # Bắt buộc bằng 0.0
```

---

## 5. Thuật toán & Quy tắc Xử lý Cốt lõi
1. **Thuật toán Đánh giá Tiên quyết Boole (Conjunctive Normal Form - CNF):**
   - Biểu thức tiên quyết được cấu trúc dạng mảng 2 chiều:
     $$\text{Prereq} = [G_1, G_2, \dots, G_m] \quad \text{với } G_i = [c_{i1}, c_{i2}, \dots, c_{ik}]$$
   - Môn học được coi là thỏa mãn điều kiện tiên quyết khi và chỉ khi:
     $$\forall i \in \{1, \dots, m\}, \quad \exists c \in G_i: c \in \text{PassedCourses}$$
   - Nếu tồn tại bất kỳ nhóm $G_i$ nào mà sinh viên chưa học môn nào trong nhóm đó, môn học lập tức bị xếp vào tập `blocked_courses` và ghi nhận nhóm $G_i$ vào `missing_prerequisites`.
2. **Quy tắc Kiểm tra Ngưỡng Tín chỉ Tích lũy:**
   - Nếu môn có thuộc tính `min_earned_credits_required` (ví dụ 105 TC cho Khóa luận tốt nghiệp):
   - So sánh $\text{CurrentEarnedCredits} \ge \text{min\_earned\_credits\_required}$. Nếu không đạt, chặn với lý do `credit_threshold_not_met`.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** Môn không có điều kiện tiên quyết (ví dụ: `MAT1041`, `PHI1006`) phải luôn nằm trong tập `eligible` nếu sinh viên chưa học.
- **TC-02:** Môn có điều kiện dạng AND (`[[MAT1041], [MAT1093]]`): chỉ eligible khi sinh viên đã hoàn thành CẢ HAI môn. Thiếu 1 trong 2 phải bị chặn.
- **TC-03:** Môn có điều kiện dạng OR (`[[MAT1041, MAT1042]]`): eligible nếu sinh viên đã hoàn thành ÍT NHẤT 1 TRONG 2 môn.
- **TC-04:** Tỷ lệ vi phạm điều kiện (`violation_rate`) được đo lường tự động trên toàn bộ kết quả phải luôn luôn bằng $0.0\%$.
- **TC-05:** Cung cấp đầy đủ danh sách môn tiên quyết còn thiếu cho 100% các môn bị chặn.

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🟢 **Đã xong 85%** — Cổng lọc điều kiện cứng hoàn thiện và an toàn.
- **Hiện có trong codebase:** File [`app/rules.py`](file:///e:/SE_Project/app/rules.py) và API `POST /eligibility` đã xử lý:
  - Lọc bỏ môn đã học.
  - Đánh giá biểu thức Boole AND/OR đầy đủ.
  - Phân loại rõ `eligible_courses` và `blocked_courses` kèm danh sách môn thiếu.
  - Đảm bảo tỷ lệ vi phạm = 0.0% trên toàn bộ các test cases tại [`tests/test_rules.py`](file:///e:/SE_Project/tests/test_rules.py).
- **Nhiệm vụ cần thực hiện:**
  1. Bổ sung kiểm tra ngưỡng tín chỉ tích lũy tối thiểu để vào chuyên ngành / làm khóa luận ($\ge 105$ TC).
  2. Bổ sung ràng buộc hạn ngạch tín chỉ tự chọn theo nhóm (Elective Group Quota).
