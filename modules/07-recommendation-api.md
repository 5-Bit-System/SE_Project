# Module 07 — API và điều phối pipeline gợi ý

## Mục tiêu

Nối các module thành một pipeline API nhất quán, giữ đúng thứ tự xử lý và hợp đồng response cho frontend/chatbot.

## Phạm vi

- Validate program_id và request.
- Load đúng catalog.
- Chuẩn hóa transcript.
- Gọi eligibility trước ranking.
- Gọi preference extraction, ranking và explanation theo thứ tự.
- Validate output ở từng boundary.
- Dùng fallback khi LLM/service lỗi.
- Trả warnings và catalog status.
- Bảo đảm request không làm lộ API key.

## Các endpoint cốt lõi

- GET /programs hoặc /catalogs.
- GET /courses?program_id=...
- POST /eligibility.
- POST /recommendations.
- POST /advisor/chat.
- GET /health.

## Nội dung tối thiểu của request gợi ý

- program_id.
- passed_course_codes hoặc transcript records.
- user_request.
- limit.
- max_credits.
- optional preference/what-if override.

## Nội dung tối thiểu của response gợi ý

- program_id.
- catalog_status.
- recommendations.
- eligible_count.
- blocked_count hoặc blocked summary.
- preference đã chuẩn hóa nếu phù hợp.
- ranking backend/version.
- warnings.

## Bất biến bắt buộc

- program_id request phải khớp catalog.
- Mọi recommendation code phải nằm trong eligible set.
- Không trả completed/blocked course.
- max_credits và limit được áp dụng sau validation code.
- LLM failure không làm endpoint thất bại nếu fallback chạy được.
- Mọi recommendation có offering uncertainty warning khi chưa có nguồn xác minh.

## Tiêu chí hoàn thành

- Có integration test cho happy path.
- Có test major isolation.
- Có test LLM malformed output và fallback.
- Có test không có API key.
- API response đủ dữ liệu để frontend hiển thị explanation.
