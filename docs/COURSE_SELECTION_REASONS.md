# Khung lý do chọn và gợi ý môn học (Course Selection & Recommendation Reasons)

Tài liệu này hệ thống hóa các **nhu cầu chọn môn học** của sinh viên và cách hệ thống **Explainable Course Recommender** chuyển đổi các nhu cầu đó thành:
1. **Metadata môn học** làm căn cứ chứng minh (`grounded facts`).
2. **Thuật toán chấm điểm & xếp hạng** (`scoring & ranking weights`).
3. **Lời giải thích minh bạch của AI Advisor** (`explainable recommendation`).

---

## 1. Tổng quan ma trận ánh xạ (Reasoning Matrix)

| # | Nhu cầu của sinh viên | Trường Metadata quyết định | Trọng số Scoring / What-if | Trạng thái kiểm chứng |
|---|---|---|---|---|
| 1 | **Học nhẹ, ít áp lực** | `workload`, `hours.practice`, `credits` | `weights.workload` | Cần metadata `workload` hoặc tỷ lệ giờ |
| 2 | **Học dễ, an toàn, kéo GPA** | `difficulty`, `block`, ít tiên quyết | `weights.difficulty` | Cần metadata `difficulty` |
| 3 | **Định hướng nghề nghiệp** | `career_paths`, `choice_group_ids`, `description` | Phân tích ngữ nghĩa LLM | Khớp vai trò nghề nghiệp |
| 4 | **Thực hành vs Lý thuyết** | `orientation` (`theory` / `practice` / `research`) | `weights.orientation` | Cần metadata `orientation` |
| 5 | **Chủ đề yêu thích** | `topics`, `name`, `name_en` | `weights.topic` (mặc định 60%) | Khớp thẻ chủ đề chuẩn hóa |
| 6 | **Mở khóa môn tiếp theo** | `prerequisites` (DAG), `year`, `suggested_term` | Rule Engine (DAG bottleneck) | Xác định từ cấu trúc đồ thị CTĐT |

---

## 2. Chi tiết 6 nhóm lý do chọn môn học

---

### 2.1. Nhóm 1: "Học nhẹ" (Workload & Cân bằng thời gian)
* **Tình huống sinh viên:** Bận đi làm thêm, ôn thi chứng chỉ ngoại ngữ (IELTS/TOEIC), tham gia nghiên cứu khoa học hoặc muốn một kỳ học giảm tải căng thẳng.
* **Metadata căn cứ:**
  * `workload`: `"light"` (nhẹ), `"moderate"` (vừa phải), `"heavy"` (nặng).
  * `credits`: Môn 2 tín chỉ ưu tiên hơn môn 3–4 tín chỉ khi người dùng muốn học nhẹ.
  * `hours`: Phân bổ giờ `practice` (thực hành) thấp, không yêu cầu khối lượng đồ án lớn.
* **Cách hệ thống tính điểm:**
  * Tăng điểm cho môn có `workload == "light"` khi người dùng chọn slider What-if tải học tập thấp hoặc chat các từ khóa như *"nhẹ"*, *"ít áp lực"*, *"ít bài tập"*.
* **Mẫu câu giải thích của hệ thống:**
  > *"Môn **PEC1008 (Kinh tế chính trị Mác - Lênin)** được gợi ý vì có số tín chỉ thấp (2 TC), khối lượng học tập nhẹ (`workload: light`) và không có đồ án thực hành lớn, phù hợp với mong muốn cân bằng thời gian kỳ này của bạn."*

---

### 2.2. Nhóm 2: "Học dễ / An toàn / Kéo điểm GPA" (Difficulty & Academic Safety)
* **Tình huống sinh viên:** Kỳ trước điểm chưa như ý, đang trong diện cảnh báo học vụ, hoặc cần tích lũy các môn chắc chắn đạt điểm cao để nâng GPA.
* **Metadata căn cứ:**
  * `difficulty`: `"easy"` (nhập môn, cơ bản), `"moderate"` (trung bình), `"advanced"` (nâng cao).
  * `block`: Khối kiến thức chung (`general`) hoặc cơ sở thường có ngưỡng tiếp cận thuận lợi hơn chuyên ngành sâu.
  * `prerequisites`: Môn không có chuỗi tiên quyết dài, ít rủi ro mất gốc kiến thức.
* **Cách hệ thống tính điểm:**
  * Ưu tiên môn có `difficulty == "easy"` khi người dùng chat *"dễ"*, *"kéo điểm"*, *"cải thiện GPA"*, *"an toàn"*.
* **Mẫu câu giải thích của hệ thống:**
  > *"Môn **HIS1056 (Cơ sở văn hóa Việt Nam)** được xếp thứ hạng cao vì có mức độ tiếp cận cơ bản (`difficulty: easy`), không đòi hỏi chuỗi kiến thức tiên quyết phức tạp, giúp bạn an tâm tích lũy tín chỉ và cải thiện GPA học kỳ này."*

---

### 2.3. Nhóm 3: "Định hướng nghề nghiệp & Vị trí công việc" (Career Paths)
* **Tình huống sinh viên:** Đã xác định mục tiêu việc làm tương lai (ví dụ: muốn trở thành Kỹ sư AI, Kỹ sư Dữ liệu, Lập trình viên Backend, Chuyên viên Phân tích nghiệp vụ).
* **Metadata căn cứ:**
  * `career_paths`: Mảng các vai trò nghề nghiệp mục tiêu (`["ai_engineer", "data_analyst", "software_engineer", "quant_analyst", ...]`).
  * `choice_group_ids`: Thuộc nhánh chuyên sâu tương ứng trong CTĐT (ví dụ: nhánh Trí tuệ nhân tạo, nhánh Hệ thống nhúng).
  * `description`: Tóm tắt kỹ năng chuyên môn đạt được sau học phần.
* **Cách hệ thống tính điểm:**
  * Trích xuất `career_goal` từ hội thoại và so khớp với danh sách `career_paths` của môn học.
* **Mẫu câu giải thích của hệ thống:**
  > *"Môn **MAT3517 (Thị giác máy tính)** trực tiếp phục vụ mục tiêu trở thành **AI Engineer** của bạn, cung cấp kiến thức nền tảng về mạng học sâu CNN, Vision Transformer và xử lý dữ liệu hình ảnh trong thực tế."*

---

### 2.4. Nhóm 4: "Phong cách học tập: Thực hành vs Lý thuyết" (Learning Orientation)
* **Tình huống sinh viên:**
  * Muốn code nhiều, làm bài tập lớn, dự án thực tế (`practice`).
  * Hoặc muốn học toán sâu, chứng minh công thức, xây dựng nền tảng lý thuyết vững chắc để thi cao học/nghiên cứu (`theory` / `research`).
* **Metadata căn cứ:**
  * `orientation`:
    * `"practice"`: Định hướng ứng dụng, thực hành, đồ án.
    * `"theory"`: Định hướng lý thuyết, toán học thuần túy, chứng minh.
    * `"research"`: Định hướng nghiên cứu học thuật chuyên sâu.
* **Cách hệ thống tính điểm:**
  * Khớp trực tiếp lựa chọn slider What-if "Tính thực hành" với trường `orientation` của môn học.
* **Mẫu câu giải thích của hệ thống:**
  > *"Môn **INT3202 (Lập trình Web)** được ưu tiên vì có định hướng thực hành cao (`orientation: practice`) với các bài tập lab và sản phẩm cuối kỳ, đúng với mong muốn học thiên về thực hành lập trình của bạn."*

---

### 2.5. Nhóm 5: "Chủ đề kiến thức đam mê" (Specific Interest Topics)
* **Tình huống sinh viên:** Muốn đào sâu vào một chuyên môn cụ thể trong học kỳ (như: Học máy, Bảo mật, Đồ họa máy tính, Tối ưu hóa, Dữ liệu lớn).
* **Metadata căn cứ:**
  * `topics`: Mảng từ khóa chuẩn hóa (ví dụ: `["machine_learning", "deep_learning", "computer_vision"]`).
  * `name` & `name_en`: Tên học phần hỗ trợ từ khóa tự do.
* **Cách hệ thống tính điểm:**
  * Trọng số `topic` chiếm tỷ trọng lớn nhất (mặc định 60% trong công thức scoring).
* **Mẫu câu giải thích của hệ thống:**
  > *"Môn học này được đề xuất vì chứa chính xác các chủ đề bạn yêu cầu: **deep_learning** và **computer_vision**."*

---

### 2.6. Nhóm 6: "Chiến lược mở khóa môn & Tiến độ tốt nghiệp" (DAG Bottleneck Unlocking)
* **Tình huống sinh viên:** Muốn đăng ký môn có tính chiến lược cao để không bị "nghẽn" tiến độ ở các kỳ học năm 3, năm 4.
* **Metadata căn cứ:**
  * `prerequisites` (Đồ thị DAG): Xác định bậc ra (*out-degree*) của môn học trong đồ thị tiên quyết.
  * `year` và `suggested_term`: Khung thời gian khuyến nghị trong CTĐT.
  * `requirement_type`: Môn bắt buộc (`required`) có mức ưu tiên mở khóa cao hơn môn tự chọn.
* **Cách hệ thống tính điểm:**
  * Rule Engine kết hợp Heuristic Ranker nhận diện môn là tiên quyết của nhiều môn chuyên đề phía sau.
* **Mẫu câu giải thích của hệ thống:**
  > *"Môn **MAT1093 (Đại số tuyến tính)** là môn nền tảng bắt buộc của Năm 1. Hoàn thành môn này trong kỳ tới sẽ mở khóa trực tiếp ít nhất 4 môn chuyên ngành ở Năm 2 và Năm 3 (như Học máy, Tối ưu hóa, Xử lý ảnh số)."*

---

## 3. Nguyên tắc giải thích minh bạch (Grounding Principles)

Hệ thống tuân thủ 3 nguyên tắc bất biến khi sinh lời giải thích cho sinh viên:

1. **Phân tách rành mạch 2 vế:**
   * **Vế 1 (Đủ điều kiện):** Giải thích rõ sinh viên đã hoàn thành những môn tiên quyết cụ thể nào để được phép học môn này.
   * **Vế 2 (Độ phù hợp):** Nêu rõ môn này khớp với tiêu chí nào của sinh viên (chủ đề, tải học tập, độ khó, hay hướng nghề nghiệp).
2. **Không suy đoán khi thiếu metadata:**
   * Nếu môn chưa có dữ liệu `workload` hoặc `difficulty`, hệ thống thông báo rõ: *"Catalog hiện chưa có dữ liệu khảo sát độ khó/tải học tập của môn này"*, tuyệt đối không tự gắn mác dễ/khó.
3. **Cảnh báo tính xác thực mở lớp:**
   * Mọi lời khuyên đều đi kèm lưu ý: hệ thống chỉ đánh giá điều kiện học thuật theo CTĐT, sinh viên cần kiểm tra thời khóa biểu chính thức của Nhà trường để biết môn có mở lớp trong học kỳ hay không.
