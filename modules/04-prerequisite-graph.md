# Module 04: Prerequisite DAG Graph Engine (`prerequisite_graph`)

## 1. Bản chất & Vai trò trong Hệ thống
Quan hệ tiên quyết giữa các môn học trong một chương trình đào tạo đại học tạo thành một **Đồ thị có hướng (Directed Graph)**. Nếu đồ thị này xuất hiện chu trình (ví dụ: Môn A đòi Môn B, Môn B đòi Môn C, Môn C lại đòi Môn A) thì sinh viên sẽ rơi vào tình trạng bế tắc (Deadlock) không bao giờ đăng ký được môn học.
Module **Prerequisite DAG Graph Engine** sử dụng lý thuyết đồ thị (thư viện `networkx`) để mô hình hóa mạng lưới môn học, thực hiện kiểm định nghiêm ngặt tính không chu trình (Directed Acyclic Graph - DAG), sắp xếp thứ tự học tập hợp lệ (Topological Sort) và phân tích các nút thắt cổ chai học vụ (Bottleneck Courses).

---

## 2. Ranh giới & Trách nhiệm Đơn nhất (Single Responsibility)
- **Thuộc phạm vi:**
  - Chuyển đổi dữ liệu tiên quyết thô từ Module 03 thành cấu trúc đồ thị `networkx.DiGraph`.
  - **Kiểm định chu trình (Cycle Detection):** Sử dụng thuật toán Tarjan / DFS để chứng minh đồ thị hoàn toàn không có chu trình (`is_directed_acyclic_graph == True`).
  - **Sắp xếp thứ tự Topo (Topological Sort):** Sinh ra thứ tự học tập tuyến tính hợp lệ, bảo đảm môn tiên quyết luôn đứng trước môn kế tiếp.
  - **Tính toán đường găng & độ sâu tiên quyết (Prerequisite Depth / Critical Path):** Xác định khoảng cách từ môn cơ sở đến môn chuyên ngành xa nhất.
  - **Phân tích tầm ảnh hưởng của môn học (Downstream Impact):** Đếm số lượng môn phụ thuộc phía sau một môn học để hỗ trợ bộ xếp hạng ưu tiên môn nền tảng quan trọng.
- **Ngoài phạm vi:**
  - Không kiểm tra điểm số cụ thể của từng sinh viên (thuộc Module 05).
  - Không vẽ giao diện hiển thị đồ thị (thuộc Module 11).

---

## 3. Kiến trúc Nội bộ Module

```text
app/modules/prerequisite_graph/
├── __init__.py
├── graph.py                    # Khởi tạo và quản lý cấu trúc nx.DiGraph cho từng ngành
├── cycle_detector.py           # Thuật toán kiểm tra chu trình và trích xuất chu trình lỗi
├── topo_sort.py                # Sắp xếp Topo và tính toán độ sâu tiên quyết
└── schemas.py                  # Pydantic models: GraphAnalysisResult, CourseNode
```

---

## 4. Hợp đồng Giao tiếp Dữ liệu (Data Contracts)

### Model: `GraphAnalysisResult`
```python
class CourseDependencyInfo(BaseModel):
    course_code: str
    prerequisite_depth: int                     # Số cấp tiên quyết tối đa dẫn đến môn này
    direct_prerequisites: list[str]             # Danh sách môn tiên quyết trực tiếp
    all_ancestors: list[str]                    # Toàn bộ các môn tổ tiên cần học trước
    direct_dependents: list[str]                # Các môn trực tiếp cần môn này
    all_descendants: list[str]                  # Toàn bộ các môn bị khóa nếu trượt môn này
    is_bottleneck: bool                         # True nếu có > 3 môn chuyên ngành phụ thuộc

class GraphAnalysisResult(BaseModel):
    program_id: str
    is_dag: bool                                # Bắt buộc True
    detected_cycles: list[list[str]]            # Danh sách chu trình nếu phát hiện lỗi
    topological_order: list[str]                # Thứ tự học tập hợp lệ từ đầu đến cuối
    max_depth: int                              # Độ sâu lớn nhất của đồ thị
    nodes_info: dict[str, CourseDependencyInfo]
```

---

## 5. Thuật toán & Quy tắc Xử lý Cốt lõi
1. **Mô hình hóa Cạnh đồ thị (Graph Edges):**
   - Với môn $Y$ có điều kiện tiên quyết là môn $X$ ($X$ là tiên quyết của $Y$), hệ thống tạo một cạnh có hướng:
     $$X \longrightarrow Y$$
   - Đối với điều kiện dạng `OR` (ví dụ: cần học $A$ hoặc $B$ để học $Y$), hệ thống tạo 2 cạnh phụ trợ dạng lựa chọn, hoặc tạo siêu đỉnh (Hyper-node / Composite node) để biểu diễn quan hệ Boole.
2. **Thuật toán Phát hiện Chu trình (Cycle Detection):**
   - Sử dụng hàm `nx.is_directed_acyclic_graph(G)`.
   - Nếu trả về `False`, gọi `nx.simple_cycles(G)` để chỉ ra chính xác chuỗi mã môn gây ra vòng lặp vô tận nhằm báo cáo cho quản trị viên sửa dữ liệu.
3. **Thuật toán Sắp xếp Topo (Kahn's Algorithm):**
   - Lần lượt lấy ra các đỉnh có bán bậc vào bằng 0 (In-degree = 0, tức là các môn không cần tiên quyết như Giải tích 1, Đại số tuyến tính, Triết học).
   - Xóa đỉnh đó khỏi đồ thị và cập nhật bán bậc vào của các đỉnh kề cho đến khi hết đồ thị.
   - Kết quả thu được là thứ tự Topo chuẩn xác.

---

## 6. Tiêu chí Kiểm thử & Nghiệm thu
- **TC-01:** Xác nhận cả 4 đồ thị của 4 CTĐT trong dữ liệu đều là DAG hợp lệ (`is_dag == True`).
- **TC-02:** Phát hiện ngay lập tức lỗi chu trình khi thêm một cạnh giả định $C \rightarrow A$ vào đồ thị có sẵn $A \rightarrow B \rightarrow C$.
- **TC-03:** Mọi môn học trong thứ tự Topo đều thỏa mãn: nếu $A \rightarrow B$ thì vị trí của $A$ luôn đứng trước $B$ trong mảng kết quả.
- **TC-04:** Tính toán chính xác các môn có tầm ảnh hưởng lớn (ví dụ: `MAT1041 - Giải tích 1` mở khóa cho hàng loạt môn phía sau).

---

## 7. Hiện trạng Triển khai & Kế hoạch Tiếp theo (Implementation Status)
- **Mức độ hoàn thành:** 🟡 **Đã xong 50%** — Đã có kiểm tra Topo trong planner.
- **Hiện có trong codebase:** Logic topo và kiểm tra thứ tự học phần hiện tích hợp bên trong [`app/planner.py`](file:///e:/SE_Project/app/planner.py) và các script kiểm tra dữ liệu ở `tools/`.
- **Nhiệm vụ cần thực hiện:**
  1. Tách thành engine riêng `app/modules/prerequisite_graph/`.
  2. Xây dựng cấu trúc `nx.DiGraph` có sẵn các hàm tra cứu: `get_prerequisite_depth(code)`, `get_all_ancestors(code)`, `get_all_descendants(code)`.
  3. Bổ sung thuật toán xếp hạng ưu tiên các môn "nút thắt cổ chai" (Bottleneck) để hỗ trợ Module 07 Ranking.
