# Module 09: Academic Advisor with Scope Guardrails (`academic_advisor`)

## 1. Bản chất & Vai trò trong Hệ thống
Bên cạnh danh sách môn gợi ý tĩnh, sinh viên rất cần một người bạn đồng hành — **Trợ lý Học vụ AI (AI Academic Advisor)** để giải đáp các thắc mắc chuyên sâu: *"Em muốn làm Kỹ sư AI thì kỳ này nên học môn nào?", "Môn X có quá nặng so với môn Y không?", "Tại sao môn Z lại bị khóa?"*. 
Module **Academic Advisor with Scope Guardrails** đóng vai trò là trợ lý hội thoại thông minh (tích hợp Gemini API) hiển thị dưới dạng **Bong bóng chat nổi (Floating Chat Bubble)** trên giao diện web, có khả năng nạp toàn bộ ngữ cảnh học vụ thực tế của sinh viên, đồng thời được trang bị **Hàng rào bảo vệ (Scope Guardrails)** để nhận biết và từ chối các câu hỏi ngoài phạm vi nghiệp vụ.

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - **Tiếp nhận Context Học vụ Toàn diện:** Tự động nạp thông tin Ngành học, Danh sách môn đã hoàn thành + Điểm số, Tập môn đủ điều kiện kỳ tới (từ Module 05), và Lộ trình 4 năm (từ Module 06) vào ngữ cảnh của trợ lý.
  - **Hàng rào Kiểm soát Phạm vi (Scope Guardrails):**
    - *Câu hỏi HỢP LỆ (Tiếp nhận & Trả lời sâu sắc):* Định hướng nghề nghiệp (AI, Data, Phần mềm, Tài chính), tư vấn chọn môn tự chọn, giải thích thứ tự học môn, lộ trình kiến thức.
    - *Câu hỏi NGOÀI PHẠM VI (Phát hiện & Từ chối lịch sự):*
      1. Yêu cầu xếp thời khóa biểu đẹp, tránh trùng lịch học, chọn ca học sáng/chiều (hệ thống giải thích rõ hệ thống không có dữ liệu lịch thi/thời khóa biểu phòng học).
      2. Yêu cầu đánh giá giảng viên dễ tính hay khó tính, giảng viên nào chấm điểm cao (hệ thống từ chối vì lý do đạo đức học thuật và không có dữ liệu giảng viên).
      3. Các câu hỏi hoàn toàn ngoài lề xã hội, thời tiết, giải trí.
  - **Cơ chế Heuristic Fallback ngoại tuyến:** Khi chưa cấu hình Gemini API key hoặc khi mất kết nối mạng, module tự động chuyển sang bộ máy tư vấn Heuristic cục bộ, phân tích trực tiếp tập môn `eligible`/`blocked` để trả lời câu hỏi của sinh viên mà không bị đơ hoặc báo lỗi hệ thống.
- **Ngoài phạm vi:**
  - Không tự ý sửa đổi danh sách môn đủ điều kiện (phải tuân theo Module 05).
  - Không thay đổi kết quả điểm số thực tế của sinh viên.

---

## 3. Kiến trúc Nội bộ Module

```text
app/modules/academic_advisor/
├── __init__.py
├── chatbot.py                  # Điều phối hội thoại và gọi Gemini API
├── guardrails.py               # Bộ lọc từ khóa và phân loại ý định (Intent Classifier)
├── prompt_templates.py         # Hệ thống System Prompts có Grounding tri thức CTĐT
├── fallback.py                 # Bộ tư vấn Heuristic Rule-based khi không có LLM
└── schemas.py                  # Pydantic models: AdvisorRequest, AdvisorResponse
```

---

## 4. Hợp đồng Giao tiếp Dữ liệu (Data Contracts)

### Model: `AdvisorRequest` & `AdvisorResponse`
```python
class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str | None = None

class AdvisorRequest(BaseModel):
    program_id: str
    query: str                                  # Câu hỏi của sinh viên
    passed_course_codes: list[str] = []
    current_term: int = 3
    conversation_history: list[ChatMessage] = []

class AdvisorResponse(BaseModel):
    answer: str                                 # Câu trả lời dạng Markdown
    is_out_of_scope: bool = False               # True nếu vi phạm Scope Guardrails
    guardrail_reason: str | None = None         # "schedule_optimization", "instructor_review", ...
    suggested_followups: list[str] = []         # Gợi ý 2-3 câu hỏi tiếp theo
    used_fallback: bool = False                 # True nếu dùng Heuristic Fallback
```

---

## 5. Thuật toán & Quy tắc Xử lý Cốt lõi
1. **Kiến trúc Lớp Guardrails Độc lập (Two-Tier Guardrails):**
   - **Tầng 1 — Regex & Keyword Intent Filter:**
     Phát hiện các từ khóa bị cấm:
     - Lịch học / Thời khóa biểu: `r"(thời khóa biểu|trùng lịch|lịch học|tiết|xếp lịch|thứ mấy|phòng học)"`.
     - Đánh giá giảng viên: `r"(thầy nào dễ|cô nào dễ|giảng viên nào khó|chấm điểm gắt|cho điểm cao)"`.
     Nếu khớp pattern, trả về ngay thông điệp từ chối chuẩn hóa thân thiện trong vòng $2$ms mà không cần gọi LLM (tiết kiệm chi phí và độ trễ).
   - **Tầng 2 — System Instruction Grounding:**
     Hướng dẫn LLM nghiêm ngặt: Chỉ căn cứ vào dữ liệu môn học trong CTĐT, nếu người dùng cố tình bẻ khóa (Jailbreak), LLM phải kiên quyết giữ vững phạm vi tư vấn học vụ.
2. **Cơ chế Fallback Heuristic Cục bộ:**
   - Phân tích câu hỏi người dùng bằng Intent Matcher:
     - Hỏi về môn bị chặn: Liệt kê các môn `blocked` kèm lý do.
     - Hỏi về môn nên học kỳ tới: Đề xuất các môn `eligible` có tín chỉ cơ sở ngành.
     - Hỏi về định hướng: Lọc các môn theo từ khóa `AI`, `Dữ liệu`, `Toán`.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** Từ chối $100\%$ các câu hỏi về xếp thời khóa biểu và nhận xét giảng viên, trả về thông điệp từ chối lịch sự và hướng dẫn quay lại chủ đề học tập.
- **TC-02:** Trả lời chính xác, sâu sắc các câu hỏi hợp lệ về định hướng chuyên ngành và thứ tự học môn dựa trên đúng CTĐT của sinh viên.
- **TC-03:** Hoạt động trơn tru ở chế độ Heuristic Fallback khi biến môi trường `GEMINI_API_KEY` để trống.
- **TC-04:** Giữ được lịch sử hội thoại trong cùng một phiên để hỗ trợ các câu hỏi ngữ cảnh liên tiếp (Contextual Follow-up).

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🟢 **Đã xong 95%** — Hoàn thiện toàn diện và đã kết nối thành công với cổng Beeknoee.
- **Hiện có trong codebase:** File [`app/advisor.py`](file:///e:/SE_Project/app/advisor.py) và API `POST /advisor/chat` đã xử lý:
  - Scope Guardrails chặn chính xác câu hỏi xếp thời khóa biểu và đánh giá giảng viên.
  - Tích hợp cổng Beeknoee với model `bee/gemini-3.8-flash` qua OpenAI-compatible API.
  - Tự động fallback Heuristic an toàn khi không có key.
  - Toàn bộ 7 bài test trong [`tests/test_advisor.py`](file:///e:/SE_Project/tests/test_advisor.py) đều PASS 100%.
- **Nhiệm vụ cần thực hiện:**
  1. Hỗ trợ hiển thị Markdown đẹp mắt hơn (thẻ môn học có thể bấm xem chi tiết) trên khung chat của Web UI.
