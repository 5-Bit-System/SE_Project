# Module 08: Explainability & Audit Engine (`explainability_engine`)

## 1. Bản chất & Vai trò trong Hệ thống
Một hạn chế lớn của các hệ thống gợi ý "hộp đen" (Black-box) truyền thống là sinh viên không hiểu được **tại sao** một môn học lại được đề xuất, hoặc **tại sao** một môn mình muốn học lại không xuất hiện trong danh sách. 
Module **Explainability & Audit Engine** chịu trách nhiệm tạo ra **lời giải thích minh bạch, có thể kiểm chứng được (Verifiable & Faithful Explanations)** cho từng môn học được đề xuất và từng môn học bị loại trừ. Đồng thời, module ghi nhận dấu vết kiểm toán (Audit Trail) để đảm bảo tính giải trình và tái lập kết quả trong các buổi đánh giá học vụ.

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - Tiếp nhận thông tin từ Module 05 (Eligibility) và Module 07 (Ranking).
  - **Tạo lời giải thích đa chiều cho môn được đề xuất:**
    - `eligible_because`: Liệt kê chính xác các môn tiên quyết mà sinh viên đã vượt qua kèm điểm số đạt được.
    - `fit_reasons`: Trình bày mức độ đóng góp của từng tiêu chí ưu tiên (Ví dụ: "Phù hợp 92% với mục tiêu kỹ sư AI", "Tải học nhẹ giúp cân bằng kỳ học", "Môn thực hành cao").
  - **Tạo lời giải thích cho môn bị loại (`blocked_reasons`):**
    - Liệt kê chính xác môn tiên quyết còn thiếu hoặc chưa đạt điểm 5.0 (Ví dụ: "Chưa thể học Học máy vì chưa hoàn thành môn Giải tích 2 và Xác suất thống kê").
  - **Bảo đảm tính trung thực (Faithfulness Invariant):** Lời giải thích phải được xây dựng trực tiếp từ các đại lượng đã tính toán trong luật và mô hình điểm số; tuyệt đối không để LLM "tự biên tự diễn" lời giải thích mâu thuẫn với số liệu thực tế.
  - **Audit Logging:** Lưu trữ metadata phiên gợi ý (`request_id`, `timestamp`, `algorithm_version`, `weights_used`, `raw_contributions`).
- **Ngoài phạm vi:**
  - Không xếp hạng môn học (thuộc Module 07).
  - Không đảm nhận giao diện người dùng (thuộc Module 11).

---

## 3. Kiến trúc Nội bộ Module

```text
app/modules/explainability_engine/
├── __init__.py
├── generator.py                # Engine sinh lời giải thích có cấu trúc
├── template_builder.py         # Mẫu giải thích song ngữ (Việt - Anh) chuẩn hóa
├── audit_logger.py             # Bộ ghi nhận dấu vết kiểm toán và tái lập
└── schemas.py                  # Pydantic models: CourseExplanationCard, AuditLogEntry
```

---

## 4. Hợp đồng Giao tiếp Dữ liệu (Data Contracts)

### Model: `CourseExplanationCard`
```python
class FitReasonDetail(BaseModel):
    category: Literal["career_goal", "track", "performance", "workload", "hands_on"]
    title: str                                  # "Phù hợp định hướng nghề nghiệp"
    description: str                            # "Môn học trực tiếp cung cấp kiến thức nền tảng cho vị trí Data Scientist."
    impact_level: Literal["high", "medium", "low"]

class CourseExplanationCard(BaseModel):
    course_code: str
    course_name: str
    is_eligible: bool
    # Dành cho môn ĐỦ ĐIỀU KIỆN:
    eligible_because: list[str]                 # ["Đã hoàn thành Giải tích 1 (Điểm: 8.0)", "Đã đạt Đại số (Điểm: 7.5)"]
    fit_reasons: list[FitReasonDetail]          # Danh sách lý do phù hợp
    top_contributing_factor: str                # Tiêu chí đóng góp điểm số cao nhất
    # Dành cho môn BỊ CHẶN:
    blocked_reasons: list[str]                  # ["Thiếu môn tiên quyết: MAT1042 - Giải tích 2"]
    unblock_action: str | None                  # "Cần đăng ký học và thi đạt môn MAT1042 để mở khóa môn này."
```

### Model: `RecommendationAuditRecord`
```python
class RecommendationAuditRecord(BaseModel):
    audit_id: str                               # UUID
    timestamp: str
    student_program_id: str
    applied_weights: dict[str, float]
    algorithm_version: str
    recommended_courses: list[str]
    explanations_snapshot: list[CourseExplanationCard]
```

---

## 5. Thuật toán & Quy tắc Xử lý Cốt lõi
1. **Thuật toán Tạo Lý do Phù hợp (Feature Attribution Explainer):**
   - Lấy vector đóng góp có trọng số:
     $$C_i = \hat{w}_i \cdot F_i(c) \quad \forall i \in \{\text{goal}, \text{track}, \text{perf}, \text{workload}, \text{hands\_on}\}$$
   - Lựa chọn 2 tiêu chí có giá trị $C_i$ cao nhất để đưa vào thẻ giải thích chính (`primary_fit_reasons`).
   - Ghép với từ điển mô tả ngữ nghĩa (Semantic Template) tương ứng để sinh câu giải thích tự nhiên, dễ hiểu nhưng hoàn toàn chính xác về mặt toán học.
2. **Quy tắc Giải thích Điều kiện Tiên quyết:**
   - Đối soát ma trận tiên quyết từ Module 03 và bảng điểm sinh viên từ Module 02.
   - Trích xuất tên đầy đủ và điểm số của từng môn điều kiện để tạo câu giải thích minh bạch.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** $100\%$ các môn được đề xuất đều có tối thiểu một lý do về điều kiện (`eligible_because`) và một lý do về mức độ phù hợp (`fit_reasons`).
- **TC-02:** $100\%$ các môn bị chặn đều có lý do chặn rõ ràng nêu đích danh môn học còn thiếu (`blocked_reasons`).
- **TC-03:** Không có bất kỳ mâu thuẫn nào giữa lý do giải thích và dữ liệu: Ví dụ nếu điểm môn tiên quyết là 6.0, giải thích không được nói là "chưa đạt".
- **TC-04:** Lưu trữ đầy đủ bản ghi kiểm toán (`audit_id`) cho phép tái lập lại chính xác $100\%$ kết quả khi chạy lại với cùng tham số.

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🟡 **Sơ khai (30%)** — Mới có câu giải thích text cơ bản.
- **Hiện có trong codebase:** Response của API `POST /recommendations` hiện có trường `reason_markdown` nêu sơ lược lý do đề xuất.
- **Nhiệm vụ cần thực hiện:**
  1. Xây dựng cấu trúc thẻ giải thích chi tiết `CourseExplanationCard` gồm:
     - `eligible_because`: Nêu đích danh môn tiên quyết đã đạt và điểm số.
     - `fit_reasons`: Phân tích đóng góp của từng trọng số What-if vào điểm số.
     - `blocked_reasons`: Chỉ rõ môn tiên quyết còn thiếu kèm hành động mở khóa.
  2. Bổ sung ghi nhận `audit_id` cho mỗi lần sinh đề xuất để phục vụ tái lập kết quả.
