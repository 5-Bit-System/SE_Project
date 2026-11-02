# Module 07 — API và điều phối hệ thống

Hướng mới 25/10/2026: [Module 12](12-system-authentication.md) và
[kế hoạch tài khoản](../docs/KE_HOACH_TAI_KHOAN_HE_THONG_2026_10_25.md) sẽ thêm
auth/email/admin API, dependency quyền và resolver VNU theo account. Người dùng
đã yêu cầu kiến trúc account riêng, thay giới hạn lịch sử không thêm account
AI-07 bên dưới. Chưa triển khai các API mới trong lượt lập kế hoạch.

Cập nhật: 23/10/2026. **Hiện trạng:** có FastAPI pipeline hiện hành; import portal/RAG API chưa có.

## Trách nhiệm

app/api/routes.py điều phối load catalog → normalize/validate → eligibility → preference/ranking → validation/explanation → response. app/main.py phục vụ UI, startup/readiness và lỗi storage. Không đặt parser portal hoặc policy học vụ riêng trong route.

## Endpoint hiện có

| Method | Route | Vai trò |
| --- | --- | --- |
| GET | /programs, /courses?program_id=... | Chương trình và môn |
| GET | /profiles, /profiles/{profile_id} | Profile theo adapter; HUS hiện rỗng |
| GET | /profiles/{profile_id}/transcript/summary | Tóm tắt profile nếu có |
| POST | /transcript/summary | GPA, tín chỉ, progress |
| POST | /eligibility | Điều kiện học |
| POST | /recommendations, /recommendations/what-if | Gợi ý/xếp hạng lại |
| POST | /advisor/chat | Course advisor |
| GET | /health, /ready | Tiến trình và storage/catalog |

## Hợp đồng

Validate program_id, mã môn, điểm, track/path và limits tại boundary. Phân biệt input sai, source invalid, storage unavailable và provider failure. Không che lỗi HUS bằng JSON fallback, không trả secrets/raw upstream exception.

Response mục tiêu gồm catalog status/revision, effective constraints, backend/version, warnings và baseline khi cần. /ready hiện không kiểm tra portal/RAG; cần trạng thái riêng cho từng khả năng khi mở rộng.

## Kế hoạch

Điều phối draft/review/apply/cancel/disconnect với adapter 09 và validation 02. Cô lập phiên người dùng, giới hạn request/timeout, loại draft và response cũ. Import lỗi giữ transcript cũ. Thêm routing 06→11 và citations đã kiểm tra.

Tên route/schema mới phải chốt với contract connector; không coi là endpoint đã chạy. Không tự thêm tài khoản AI-07/persistence hồ sơ để kết nối portal.

## Tiêu chí hoàn thành

Integration tests cho happy path, major isolation, invalid input, provider fallback và storage error. Khi thêm import/RAG: session isolation, cancel/apply, connector failure, context mismatch, retrieval unavailable và citation validity. PostgreSQL tests tuân thủ validator đích test hiện có.
