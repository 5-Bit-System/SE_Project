# Module 10: Synthetic Data & Evaluation Benchmark (`benchmark_evaluator`)

## 1. Bản chất & Vai trò trong Hệ thống
Để đảm bảo an toàn thông tin và quyền riêng tư theo tiêu chuẩn kỹ thuật phần mềm, dự án tuyệt đối **không sử dụng dữ liệu sinh viên thật (PII)**. Thay vào đó, hệ thống xây dựng **Bộ sinh dữ liệu giả lập (Synthetic Profile Generator)** để tạo ra các hồ sơ sinh viên kiểm thử chân thực, tuân thủ nghiêm ngặt đồ thị Topo của chương trình đào tạo.
Module **Synthetic Data & Evaluation Benchmark** chịu trách nhiệm tạo ra **12 Hồ sơ sinh viên mẫu chuẩn hóa** (3 hồ sơ/ngành cho 4 ngành đào tạo) và vận hành bộ công cụ đo lường tự động (Benchmark Suite) để kiểm chứng chất lượng, độ an toàn và hiệu năng của toàn bộ hệ thống trước khi nghiệm thu.

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - **Sinh 12 Hồ sơ sinh viên mẫu (Synthetic Profiles):**
    - 4 ngành $\times$ 3 mốc học vụ = 12 Profiles:
      1. Sinh viên đầu khóa (Năm 1, Kỳ 2): Đang học đại cương, số tín chỉ ít.
      2. Sinh viên giữa khóa (Năm 2 - Năm 3, Kỳ 4 - Kỳ 5): Đã qua cơ sở ngành, bắt đầu chọn chuyên ngành.
      3. Sinh viên năm cuối (Năm 4, Kỳ 7): Đã tích lũy $>100$ tín chỉ, chuẩn bị làm Khóa luận tốt nghiệp hoặc học môn thay thế.
    - **Quy tắc Topo bắt buộc:** Mọi lịch sử môn đã học trong hồ sơ sinh viên giả lập bắt buộc phải tuân thủ thứ tự Topo (không thể có chuyện sinh viên học Giải tích 2 mà chưa học Giải tích 1).
  - **Đo lường Chỉ số Chất lượng Hệ thống (System Quality Metrics):**
    1. *Eligibility Violation Rate:* Tỷ lệ vi phạm điều kiện tiên quyết (Yêu cầu nghiêm ngặt: Phải bằng $0.0\%$).
    2. *Explanation Coverage:* Tỷ lệ môn đề xuất có đầy đủ lý do giải thích minh bạch (Yêu cầu: $100\%$).
    3. *What-If Sensitivity:* Đo mức độ phản hồi của thứ hạng khi thay đổi trọng số sliders.
    4. *System Latency:* Thời gian xử lý từ lúc nhận request đến khi trả kết quả (Yêu cầu: Heuristic $< 200$ms, có LLM $< 3000$ms).
  - **Tự động xuất báo cáo đánh giá (Benchmark Report):** Định dạng JSON và Markdown phục vụ báo cáo kỹ thuật dự án.
- **Ngoài phạm vi:**
  - Không phục vụ trực tiếp sinh viên cuối trên Web UI.
  - Không lưu trữ dữ liệu thật của sinh viên trường.

---

## 3. Kiến trúc Nội bộ Module

```text
app/modules/benchmark_evaluator/
├── __init__.py
├── profile_generator.py        # Thuật toán sinh hồ sơ sinh viên ngẫu nhiên có kiểm soát topo
├── synthetic_dataset.py        # Định nghĩa và lưu trữ 12 profile mẫu tại data/synthetic/
├── metrics.py                  # Các hàm tính toán chỉ số: Violation rate, Coverage, NDCG
├── runner.py                   # Runner chạy tự động toàn bộ 12 profile và xuất báo cáo
└── schemas.py                  # Pydantic models: SyntheticStudentProfile, BenchmarkReport
```

---

## 4. Hợp đồng Giao tiếp Dữ liệu (Data Contracts)

### Model: `SyntheticStudentProfile`
```python
class SyntheticStudentProfile(BaseModel):
    student_id: str                             # "math_01", "khdl_02", "khmtt_03", ...
    program_id: str                             # "khdl_7460108_2022"
    academic_year_stage: Literal["early", "mid", "senior"]
    current_term: int                           # 2, 5, hoặc 7
    earned_credits: int
    current_gpa: float
    completed_courses: list[CourseGradeEntry]   # Tuân thủ Topo 100%
    career_goal: str                            # "Data Engineer", "Quant Analyst", ...
    default_preferences: WhatIfPreferences
```

### Model: `BenchmarkReport`
```python
class ProfileEvaluationResult(BaseModel):
    profile_id: str
    program_id: str
    eligible_count: int
    blocked_count: int
    violation_rate: float                       # 0.0
    explanation_coverage: float                 # 1.0
    execution_time_ms: float

class BenchmarkReport(BaseModel):
    timestamp: str
    total_profiles_evaluated: int               # 12
    overall_violation_rate: float               # Bắt buộc 0.0%
    overall_explanation_coverage: float         # Bắt buộc 100.0%
    average_latency_ms: float
    all_tests_passed: bool                      # True
    results: list[ProfileEvaluationResult]
```

---

## 5. Thuật toán & Quy tắc Xử lý Cốt lõi
1. **Thuật toán Sinh Lịch sử Điểm Hợp lệ Topo (Topo-Compliant Transcript Generator):**
   - Lấy đồ thị tiên quyết DAG của ngành từ Module 04.
   - Với số môn cần sinh $K$: Duyệt đồ thị theo thứ tự Topo. Chỉ chọn môn $C$ khi và chỉ khi toàn bộ tổ tiên của $C$ đã được thêm vào danh sách học phần hoàn thành với điểm số $\ge 5.0$.
   - Sinh điểm số ngẫu nhiên theo phân phối chuẩn Gaussian quanh GPA mục tiêu (ví dụ $\mu = 7.5, \sigma = 1.0$) bảo đảm dữ liệu tự nhiên.
2. **Quy tắc Kiểm tra Độ vi phạm (Zero-Violation Checker):**
   - Với mỗi môn được hệ thống gợi ý: Truy vết ngược lại điều kiện tiên quyết trong Catalog.
   - Nếu phát hiện bất kỳ môn tiên quyết nào chưa nằm trong `completed_courses`, ghi nhận vi phạm và đánh dấu test FAIL ngay lập tức.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** Sinh thành công và lưu trữ đủ 12 hồ sơ mẫu hợp lệ trong `data/synthetic/` (3 hồ sơ $\times$ 4 ngành).
- **TC-02:** $100\%$ các hồ sơ mẫu vượt qua bài kiểm tra chất lượng dữ liệu: không có môn học nào học trước môn tiên quyết của nó.
- **TC-03:** Chạy Benchmark Suite trên toàn bộ 12 hồ sơ mẫu: Tỷ lệ vi phạm tiên quyết phải đạt $0.0\%$ trên $100\%$ các lần thử nghiệm.
- **TC-04:** Xuất báo cáo benchmark tự động phục vụ hồ sơ nghiệm thu kỹ thuật của đồ án.

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🔴 **Chưa làm (20%)** — Mới có dữ liệu test giả lập phân tán.
- **Hiện có trong codebase:** Các test case trong `tests/` sử dụng dữ liệu cứng (hardcoded fixtures) nhỏ lẻ.
- **Nhiệm vụ cần thực hiện:**
  1. Tạo thư mục `data/synthetic/` lưu trữ 12 file JSON chuẩn: 3 hồ sơ/ngành (Đầu khóa, Giữa khóa, Năm cuối) tuân thủ thứ tự Topo.
  2. Xây dựng runner `benchmark_evaluator/runner.py` tự động chạy đánh giá hệ thống qua 12 hồ sơ này.
  3. Đo lường và xuất báo cáo: Eligibility Violation Rate (=0.0%), độ trễ, và độ phủ giải thích.
