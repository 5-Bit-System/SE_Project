# Đặc tả các module — AI-07

Bộ module này mô tả phần cần thiết cho pipeline hiện hành. Đây là tài liệu phân việc, chưa phải code implementation.

## Trạng thái hiện tại (2026-10-17)

| Module | Trạng thái runtime |
| --- | --- |
| 01 Catalog | Đã có repository HUS và bốn catalog versioned; dữ liệu vẫn `draft_unverified`. |
| 02 Transcript/profile | Đã nhập bảng điểm thủ công; HUS chưa có hồ sơ sinh viên hay portal sync. |
| 03 Eligibility | Đã triển khai kiểm tra điều kiện theo ngành. |
| 04 Ranking/What-if | Đã triển khai xếp hạng, tiến độ và What-if. |
| 05 Giải thích/LLM | Đã có giải thích và kiểm tra đầu ra LLM; provider tùy cấu hình. |
| 06 Advisor | Đã có course advisor; HUS document Q&A/RAG mới là đề xuất. |
| 07 API | Đã triển khai FastAPI cho pipeline hiện hành. |
| 08 Web | Đã triển khai giao diện web tĩnh. |
| 09 OCR | Chưa triển khai, chỉ là đề xuất. |

Chi tiết vận hành hiện tại ở [README](../README.md) và [HUS_RUNTIME](../database/HUS_RUNTIME.md). Các mục bên dưới mô tả trách nhiệm dự kiến, không tự xác nhận mức độ hoàn thành.

## Nguyên tắc chung

- Hệ thống hiện tại dùng FastAPI, Pydantic và PostgreSQL runtime; JSON trong data/ là nguồn validation/seed.
- PostgreSQL, Alembic và Docker database đã được cho phép ngày 2026-10-14; xem docs/DATABASE_DESIGN.md. Các module dưới đây là đặc tả trách nhiệm, không phải bằng chứng implementation đã hoàn tất.
- Mọi xử lý phải cô lập theo đúng một program_id.
- Eligibility chạy trước ranking; LLM không có quyền mở khóa môn.
- Dữ liệu chưa xác minh phải giữ trạng thái và phải xuất cảnh báo.
- Lịch sử chat chỉ sống trong phiên làm việc; không lưu dữ liệu cá nhân.
- Không dùng dữ liệu sinh viên thật.

## Thứ tự phụ thuộc giữa các module

1. 01 — Quản lý catalog chương trình đào tạo
2. 02 — Bảng điểm và hồ sơ demo
3. 03 — Bộ máy kiểm tra điều kiện học
4. 04 — Preference, xếp hạng và What-if
5. 05 — Giải thích và kiểm tra kết quả LLM
6. 06 — Chatbot tư vấn học tập
7. 07 — API và điều phối pipeline gợi ý
8. 08 — Giao diện web
9. 09 — Nhập bảng điểm từ ảnh bằng OCR (planned)

Luồng chính:

    Catalog + Hồ sơ
        -> Kiểm tra điều kiện
        -> Trích xuất preference
        -> Xếp hạng chỉ các môn hợp lệ
        -> Kiểm tra kết quả xếp hạng
        -> Giải thích có căn cứ
        -> Phản hồi API
        -> Giao diện web / chatbot

## Chưa làm ở giai đoạn core

- Recommendation audit persistence (catalog/profile persistence đã triển khai).
- OCR/PDF transcript upload — planned, chưa triển khai code.
- Tự động nhận diện ngành.
- Lập thời khóa biểu và kiểm tra trùng lịch.
- Kiểm tra môn có mở trong học kỳ.
- HUS crawler, embedding index và RAG đầy đủ.
- Collaborative filtering hoặc model training.
- Benchmark/fairness dashboard nâng cao.

Các phần trên chỉ được thêm khi scope được chốt lại.
