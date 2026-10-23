# Module 05 — Kiểm tra đầu ra và giải thích gợi ý

Cập nhật: 23/10/2026. **Hiện trạng:** có validation mã ranking và explanation template từ facts backend.

## Trách nhiệm và hợp đồng

app/recommendation/validation.py lọc ranker output; explanation.py dựng diễn giải. Đầu vào: eligible set, thứ tự ranker, metadata/score/fit facts và trạng thái nguồn. Đầu ra: recommendation hợp lệ, lý do đủ điều kiện, lý do phù hợp và cảnh báo.

## Quy tắc

- Code thuộc eligible set, không trùng và không completed/blocked/foreign.
- Giới hạn số môn/tín chỉ do 04/service áp sau validation; không tin giới hạn do LLM tự khai.
- Tách lý do đủ điều kiện và phù hợp; chỉ khẳng định điều được facts hỗ trợ.
- Không bịa prerequisite, quota, workload, difficulty, offering hoặc metadata thiếu.
- Output ranker lỗi dùng fallback hợp lệ; cảnh báo catalog chưa xác minh/offering chưa biết đến được UI.
- Provider keys, thông tin định danh và credentials portal không vào prompt/response.

## Kế hoạch và ranh giới

Recommendation hiện dùng template, không có bước bắt buộc LLM viết lại mọi explanation. Giữ cơ chế này; thêm LLM prose chỉ khi cần và có kiểm tra facts/fallback riêng. Đặc tả cũ nói LLM viết explanation cần được hiểu là đề xuất, không phải hiện trạng.

Advisor 06 có đường prose riêng; kiểm tra mã không chứng minh mọi câu văn đúng. Grounding/citations HUS do 11 phụ trách; nguồn RAG không thay quyền quyết định eligibility.

## Tiêu chí hoàn thành

Có ca output sai kiểu, mã bịa, duplicate, blocked/completed/foreign, provider lỗi và không có key. Explanation vẫn có nghĩa khi score=0 hoặc thiếu metadata. API có đủ facts để UI hiển thị từng lý do. Nếu mở rộng LLM prose, kiểm tra khẳng định không có căn cứ và quay về template.
