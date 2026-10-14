# Module 02 — Bảng điểm và hồ sơ demo

## Mục tiêu

Quản lý context học tập tổng hợp của người dùng: ngành đã chọn, môn đã hoàn thành, điểm, tín chỉ và tiến độ.

## Phạm vi

- Nhận transcript thủ công bằng mã môn và điểm/trạng thái.
- Chuẩn hóa mã môn và program_id.
- Kiểm tra transcript chỉ thuộc catalog ngành đang chọn.
- Tính passed, failed, earned credits và GPA khi đủ dữ liệu.
- Cung cấp 12 demo profiles, ba profile cho mỗi ngành.
- Bảo đảm profile fixture tuân theo thứ tự prerequisite hợp lệ.

## Không làm

- Không OCR hoặc upload PDF ở core phase.
- Không tự động nhận diện ngành.
- Không lưu tài khoản hoặc hồ sơ sinh viên thật.
- Không giữ transcript khi người dùng đổi ngành.
- Không quyết định eligibility.

## Dữ liệu đầu vào

- program_id đã được người dùng chọn.
- Danh sách transcript records.
- Catalog tương ứng.
- Demo profile fixtures.

## Dữ liệu đầu ra

- Student context trong session.
- passed_course_codes.
- failed_course_codes.
- grade_map.
- earned credits.
- GPA thang 10 nếu có điểm.
- danh sách foreign course codes và validation errors.

## Quy tắc bắt buộc

- Grade nằm trong 0..10.
- Có grade thì passed được xác định theo ngưỡng 5.0, trừ trạng thái miễn.
- Môn ngoài catalog phải bị báo lỗi, không được âm thầm nhập vào context.
- Đổi ngành phải xóa transcript selection và recommendation context cũ.
- Chỉ môn thuộc cùng catalog được tính tín chỉ và GPA.

## Tiêu chí hoàn thành

- Có 12 profile hợp lệ, 3 profile/ngành.
- Profile đầu vào sai ngành bị từ chối.
- Tính GPA/tín chỉ nhất quán với catalog.
- Có test đổi ngành và test transcript foreign course.
