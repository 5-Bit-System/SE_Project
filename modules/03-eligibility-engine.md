# Module 03 — Bộ máy kiểm tra điều kiện học

## Mục tiêu

Là cổng chặn tất định để tạo tập môn đủ điều kiện và tập môn bị chặn trước mọi ranking hoặc LLM call.

## Phạm vi

Eligibility phải xử lý:

1. Môn đã đạt.
2. Môn ngoài ngành.
3. Prerequisite AND/OR.
4. External hoặc unverified prerequisite.
5. Choice group và quota nếu catalog biểu diễn được.
6. Track và graduation branch nếu người dùng đã chọn và catalog có rule.
7. Credit limit dùng để lọc/giải thích theo request.

## Không làm

- Không xếp hạng.
- Không gọi LLM.
- Không mở khóa môn dựa trên sở thích.
- Không tự đoán prerequisite bị thiếu.
- Không kiểm tra lịch học hoặc môn có mở kỳ hiện tại.

## Dữ liệu đầu vào

- Catalog đúng một program_id.
- passed_course_codes và transcript context.
- track/path selection nếu có.
- credit constraints nếu có.

## Dữ liệu đầu ra

EligibilityResult gồm:

- eligible_courses.
- blocked_courses.
- completed_course_codes.
- reason code và message cho từng blocked course.
- missing prerequisite groups/options.
- catalog/source warnings.

## Cách diễn giải rule

- Các group prerequisite khác nhau của một môn là AND.
- Các mã trong một group là OR.
- Mã external/unverified không thỏa prerequisite.
- Course đã passed không xuất hiện trong eligible.
- Course blocked tuyệt đối không xuất hiện trong candidate set gửi ranking.

## Bất biến bắt buộc

- Eligibility violation rate = 0%.
- Kết quả chỉ phụ thuộc input, catalog version và rule version.
- Không có course ngoài catalog.
- Không trộn dữ liệu giữa hai ngành.
- What-if không được gọi lại eligibility để mở khóa môn.

## Tiêu chí hoàn thành

- Test AND, OR, thiếu một group, external code và source conflict.
- Test choice group quota.
- Test track/graduation branch khi catalog có dữ liệu.
- Test blocked course không lọt sang recommendation.
