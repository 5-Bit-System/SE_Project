# Module 07: Multi-Objective Ranking & What-If Engine (`recommender_ranking`)

## 1. Bản chất & Vai trò trong Hệ thống
Sau khi Module 05 lọc ra tập hợp các môn học **Đủ điều kiện (`eligible`)**, sinh viên thường đối mặt với việc có quá nhiều môn mở trong kỳ mà không biết nên chọn môn nào trước. 
Module **Multi-Objective Ranking & What-If Engine** chịu trách nhiệm chấm điểm và xếp hạng danh sách môn học đủ điều kiện dựa trên mục tiêu cá nhân của sinh viên (nghề nghiệp, cải thiện điểm số, cân bằng khối lượng học, thực hành). Đồng thời, module cung cấp cơ chế **What-If Analysis** cho phép người dùng điều chỉnh các thanh trượt trọng số ưu tiên trong thời gian thực để quan sát sự thay đổi thứ hạng đề xuất.

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - **Chỉ nhận đầu vào là tập môn `eligible` từ Module 05** (Tuyệt đối không xếp hạng môn bị `blocked`).
  - **Mô hình tính điểm Đa mục tiêu Heuristic / Content-based (5 tiêu chí What-If):**
    1. $G$ (Goal Fit): Độ tương thích giữa mục tiêu nghề nghiệp và nội dung/chủ đề môn học.
    2. $T$ (Track Fit): Độ phù hợp với nhánh chuyên sâu sinh viên lựa chọn.
    3. $P$ (Performance Support): Khả năng học tốt dựa trên kết quả các môn tiên quyết liên quan.
    4. $W$ (Workload Balance): Độ cân bằng tải học tập (tránh dồn các môn quá nặng lý thuyết).
    5. $H$ (Hands-on Fit): Mức độ thực hành / đồ án thực tế.
  - **Bộ điều khiển What-If (What-If Sliders):** Tiếp nhận trọng số $w \in [1, 5]$ từ người dùng, chuẩn hóa trọng số về tổng bằng $1.0$, tính toán lại thứ hạng và trả về độ chênh lệch thứ hạng (`rank_delta`).
  - **Adapter tích hợp LLM có kiểm soát:** Gọi mô hình ngôn ngữ lớn (Gemini) để hỗ trợ xếp hạng khi có API key; tích hợp cơ chế **Validator kiểm tra mã môn nghiêm ngặt**: Nếu LLM trả về mã môn lạ, môn không thuộc tập eligible hoặc môn bị blocked, hệ thống lập tức từ chối và fallback về Ranker Heuristic an toàn.
- **Ngoài phạm vi:**
  - Không tự ý quyết định môn nào đủ điều kiện đăng ký (thuộc Module 05).
  - Không sinh văn bản giải thích chi tiết (thuộc Module 08).

---

## 3. Kiến trúc Nội bộ Module

```text
app/modules/recommender_ranking/
├── __init__.py
├── ranker.py                   # Heuristic Content-based Ranker 5 tiêu chí What-If
├── whatif_simulator.py         # Bộ tính toán độ nhạy trọng số và rank delta
├── llm_adapter.py              # LLM Ranking Adapter có JSON schema validation & fallback
└── schemas.py                  # Pydantic models: RankingRequest, RankedCourseItem
```

---

## 4. Hợp đồng Giao tiếp Dữ liệu (Data Contracts)

### Model: `WhatIfPreferences` & `RankingRequest`
```python
class WhatIfPreferences(BaseModel):
    goal_weight: float = 3.0                    # 1.0 -> 5.0 (Mục tiêu nghề nghiệp)
    track_weight: float = 3.0                   # 1.0 -> 5.0 (Định hướng chuyên ngành)
    performance_weight: float = 3.0             # 1.0 -> 5.0 (An toàn điểm số)
    workload_weight: float = 3.0                # 1.0 -> 5.0 (Cân bằng tải học)
    hands_on_weight: float = 3.0                # 1.0 -> 5.0 (Tính thực hành)

class RankingRequest(BaseModel):
    program_id: str
    eligible_courses: list[Course]
    career_goal: str | None = None              # "AI Engineer", "Data Scientist", ...
    target_track: str | None = None
    preferences: WhatIfPreferences
    use_llm: bool = False
```

### Model: `RankedCourseItem` & `RankingResponse`
```python
class FactorContribution(BaseModel):
    factor_name: str                            # "goal", "track", "performance", "workload", "hands_on"
    score_value: float                          # [0.0, 1.0]
    weighted_contribution: float                # weight * score_value

class RankedCourseItem(BaseModel):
    rank: int                                   # Thứ hạng (1, 2, 3, ...)
    course_code: str
    course_name: str
    credits: int
    total_score: float                          # Điểm tổng hợp [0.0, 1.0]
    rank_delta: int = 0                         # Thay đổi thứ hạng so với lần chạy trước (+2, -1, 0)
    factor_contributions: list[FactorContribution]

class RankingResponse(BaseModel):
    ranked_courses: list[RankedCourseItem]
    algorithm_used: Literal["heuristic_5_factors", "validated_llm", "fallback_heuristic"]
```

---

## 5. Thuật toán & Quy tắc Xử lý Cốt lõi
1. **Công thức Chấm điểm Đa mục tiêu Tuyến tính:**
   - Chuẩn hóa các trọng số người dùng:
     $$\hat{w}_i = \frac{w_i}{\sum_{j=1}^{5} w_j} \quad \implies \sum_{i=1}^{5} \hat{w}_i = 1.0$$
   - Điểm tổng hợp của mỗi môn học $c \in \text{EligibleCourses}$:
     $$\text{Score}(c) = \hat{w}_g \cdot G(c) + \hat{w}_t \cdot T(c) + \hat{w}_p \cdot P(c) + \hat{w}_w \cdot W(c) + \hat{w}_h \cdot H(c)$$
   - Sắp xếp các môn học theo $\text{Score}(c)$ giảm dần. Trường hợp bằng điểm (Tie-break), ưu tiên môn có độ sâu tiên quyết lớn hơn (từ Module 04) rồi đến mã môn theo bảng chữ cái.
2. **Cơ chế Bảo vệ Adapter LLM (LLM Guardrails):**
   - Prompt chỉ gửi danh sách các mã môn thuộc tập `eligible_courses`.
   - Kết quả LLM trả về phải tuân thủ JSON Schema nghiêm ngặt.
   - **Validation Filter:**
     $$\forall c \in \text{LLM\_Result}, \quad c \in \text{EligibleCourses} \land c \notin \text{PassedCourses}$$
   - Nếu phát hiện bất kỳ mã môn không hợp lệ hoặc hallucination, hệ thống tự động loại bỏ mã đó hoặc chuyển toàn bộ kết quả sang Ranker Heuristic.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** Toàn bộ môn trong danh sách xếp hạng bắt buộc phải thuộc tập `eligible_courses`. Tỷ lệ vi phạm môn blocked $= 0\%$.
- **TC-02:** Thay đổi thanh trượt What-if (ví dụ: kéo `hands_on_weight` từ 1 lên 5) phải làm tăng thứ hạng của các môn thực hành/đồ án.
- **TC-03:** Khi LLM gặp sự cố (mất mạng, timeout, không có API key, trả về mã môn lạ), hệ thống tự động fallback về Ranker Heuristic trong dưới $100$ms mà không làm gián đoạn trải nghiệm người dùng.
- **TC-04:** Kết quả xếp hạng có tính tất định (Deterministic): Với cùng một bộ trọng số và đầu vào, thuật toán Heuristic luôn trả về cùng một thứ tự môn học.

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🟡 **Sơ khai (30%)** — Mới có KeywordRanker đơn giản.
- **Hiện có trong codebase:** File [`app/ranking.py`](file:///e:/SE_Project/app/ranking.py) và [`app/service.py`](file:///e:/SE_Project/app/service.py) có:
  - `KeywordRanker` so khớp từ khóa mục tiêu (`goal`) với tên môn học.
  - Bộ guard loại trừ môn ngoài ngành và môn trùng lặp.
- **Nhiệm vụ cần thực hiện:**
  1. Nâng cấp mô hình chấm điểm đa mục tiêu Heuristic với 5 trọng số: Goal ($G$), Track ($T$), Performance ($P$), Workload ($W$), Hands-on ($H$).
  2. Bổ sung tính toán `rank_delta` khi người dùng kéo thanh trượt What-if.
  3. Xây dựng LLM Ranking Adapter có JSON schema validation nghiêm ngặt.
