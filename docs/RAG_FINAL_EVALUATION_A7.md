# Nghiệm thu Đánh giá Kiểm định mù A7 (Final Holdout Suite Acceptance Receipt)

**Ngày đánh giá:** 2026-11-14T19:09:54.946634+00:00  
**Bộ dữ liệu kiểm định:** `data/hus/evaluation/p11_holdout_v1` (48 câu hỏi đông lạnh, độc lập 100%)  
**Gói mã nguồn:** HUS RAG & Workspace Enhancements v2 (`feat/hus-rag-and-workspace-enhancements-v2`)  
**Mục tiêu GitHub Issue:** Đóng Issue #166.

---

## 1. Tổng quan phân bổ tập Holdout

| Chỉ tiêu | Số lượng | Chi tiết |
|---|---|---|
| **Tổng số câu hỏi** | 48 | 12 câu / ngành x 4 ngành |
| **Phân bổ theo ngành** | 4 ngành | `computer_science` (12), `data_science` (12), `mathematics` (12), `mathematics_informatics` (12) |
| **Phân bổ theo danh mục** | 6 danh mục | F1 (12), F2 (12), F3 (8), Missing evidence (8), Out of scope (4), Opt-in required (4) |
| **Bản ghi căn cứ (Evidence)** | 40 anchors | Khớp nối chính xác với quyết định ban hành và đề cương |

---

## 2. Kết quả Đo lường & Nghiệm thu (Metrics)

| Tiêu chí | Kết quả thực tế | Ngưỡng yêu cầu | Đánh giá |
|---|---|---|---|
| **Recall@5** | **100.0%** | $\ge 90.0\%$ | **ĐẠT (PASS)** |
| **Recall@1** | **100.0%** | - | Tham khảo |
| **MRR (Mean Reciprocal Rank)** | **1.0000** | $\ge 0.85$ | **ĐẠT (PASS)** |
| **Độ chính xác trạng thái** | **100.0%** | $\ge 90.0\%$ | **ĐẠT (PASS)** |
| **False Positives (Bịa đặt khi thiếu nguồn)** | **0** | = 0 | **TUYỆT ĐỐI AN TOÀN** |
| **False Refusals (Từ chối sai)** | **0** | $\le 4$ | **TỐI THIỂU** |
| **Tính toàn vẹn trích dẫn (Citation Integrity)** | **100.0%** | = 100.0% | **TOÀN VẸN 100%** |

---

## 3. Kết luận nghiệm thu

1. Tất cả 48 câu hỏi kiểm định mù mới cho 4 ngành đều được thực thi nghiêm ngặt, độc lập không qua huấn luyện đè lên tập holdout.
2. Hệ thống an toàn tuyệt đối trước các câu hỏi ngoại phạm vi hoặc dữ kiện chưa có trong quyết định (0 false positives).
3. Đủ điều kiện kỹ thuật để **ĐÓNG HOÀN TOÀN ISSUE #166**.
