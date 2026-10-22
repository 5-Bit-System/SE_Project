# Đặc tả và kế hoạch các module AI-07

Cập nhật: **23/10/2026**. Phạm vi người dùng xác nhận: chỉ viết tài liệu Markdown cho từng module, chưa triển khai chức năng.

## Kiến trúc mục tiêu

Sinh viên chủ động kết nối cổng đào tạo để lấy bảng điểm; module kết nối do bạn của người dùng phụ trách. Hệ thống chính chuẩn hóa dữ liệu, cho xem trước/xác nhận, tính tiến độ, kiểm tra điều kiện rồi xếp hạng môn. Nhập tay được giữ làm phương án dự phòng.

OCR bảng điểm được bỏ khỏi kế hoạch. OCR PDF tài liệu HUS khi cần vẫn thuộc chuẩn bị corpus tra cứu. Không đưa bảng điểm, credentials hoặc hội thoại vào corpus.

## Danh mục

| Module | Trách nhiệm | Trạng thái local |
| --- | --- | --- |
| [01 Catalog](01-curriculum-catalog.md) | Chương trình, provenance, revision/publication | Có HUS runtime; nguồn draft_unverified |
| [02 Transcript/progress](02-transcript-profile.md) | Chuẩn hóa bảng điểm và tính tiến độ | Có nhập tay; import/attempt policy chưa có |
| [03 Eligibility](03-eligibility-engine.md) | Cổng kiểm tra điều kiện tất định | Có; cần regression với dữ liệu import |
| [04 Ranking/what-if](04-preference-ranking-whatif.md) | Preference, xếp hạng và gói môn | Có; còn lỗi input và thiếu baseline revision |
| [05 Explanation/validation](05-explanation-llm-validation.md) | Kiểm tra ranker và giải thích từ facts | Có template và validation |
| [06 Advisor](06-advisor-chat.md) | Tư vấn môn và phân luồng câu hỏi | Có course advisor; chưa nối RAG |
| [07 API](07-recommendation-api.md) | Điều phối và hợp đồng tích hợp | Có API hiện hành; import/RAG chưa có |
| [08 Web](08-web-ui.md) | Workspace, review import, kết quả và chat | Có giao diện mới; import/citations chưa có |
| [09 Portal](09-portal-transcript-import.md) | Kết nối cổng và lấy bảng điểm | Bạn của người dùng phụ trách; chưa có code local |
| [10 Corpus](10-hus-corpus-release.md) | Chuẩn bị/index/phát hành dữ liệu HUS | Có candidate 106 tài liệu; chưa active |
| [11 RAG](11-hus-rag-qa.md) | Tra cứu và trả lời có nguồn | Chưa có service runtime |

## Luồng nghiệp vụ

```mermaid
flowchart TD
    P[09 Portal hoặc nhập tay từ 08] --> T[02 Chuẩn hóa và xác nhận]
    C[01 Catalog đúng ngành và khóa] --> T
    T --> E[03 Eligibility]
    C --> E
    E --> R[04 Ranking]
    R --> X[05 Validation và explanation]
    X --> U[07 API và 08 Web]
    Q[06 Phân luồng hội thoại] --> R
    Q --> H[11 HUS RAG]
    D[10 Corpus release] --> H
    H --> U
```

Sơ đồ biểu diễn phụ thuộc nghiệp vụ; API điều phối, không yêu cầu service gọi HTTP vòng qua chính ứng dụng. Progress nằm trong module 02, không cần tạo module trùng.

## Bất biến

- Mọi context gắn đúng một ngành/khóa/catalog revision. Đổi ngành xóa transcript, draft import, recommendation/chat context; loại phản hồi cũ.
- Eligibility chạy trước ranking. LLM, importer và RAG không được tự mở khóa môn hoặc gán tương đương mã môn.
- Dữ liệu chưa biết giữ nguyên; không xác nhận offering, thời khóa biểu hoặc quyết định học vụ.
- Bảng điểm/hội thoại dùng trong phiên; không tự thêm lưu hồ sơ lâu dài. Credentials không vào database/log/prompt/index.
- Catalog và corpus có phiên bản riêng. Runtime không crawl theo request/startup/lịch tuần.
- HUS dùng công cụ migration/publication riêng; giữ legacy database để rollback.

## Thứ tự thực hiện sau khi được yêu cầu triển khai

Sửa lỗi PDF acceptance, preference/fallback và mẫu năm học; thống nhất contract portal; triển khai chuẩn hóa/review/import; đồng bộ advisor/what-if; triển khai corpus/RAG và kiểm tra đầu cuối.

Bộ tài liệu này thay thế phạm vi OCR bảng điểm, nguồn JSON-only và demo profile bắt buộc của các đặc tả module cũ. Việc viết lại tài liệu không sửa các lỗi code hoặc chứng nhận tính năng đã hoạt động.

Tham chiếu: [audit và kế hoạch sửa](../docs/RA_SOAT_MODULE_VA_KE_HOACH_CHINH_SUA_2026_10_23.md), [kế hoạch RAG](../docs/KE_HOACH_XU_LY_DATA_RAG_HUS.md), [vận hành HUS](../database/HUS_RUNTIME.md).
