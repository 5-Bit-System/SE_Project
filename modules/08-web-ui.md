# Module 08 — Giao diện web

## Mục tiêu

Hiển thị đầy đủ pipeline cho người dùng demo mà không làm thay đổi rule backend.

## Phạm vi

Trang chính gồm:

1. Chọn đúng một ngành.
2. Chọn/nhập môn đã hoàn thành.
3. Xem tiến độ, tín chỉ và GPA.
4. Xem eligible courses.
5. Xem blocked courses và lý do.
6. Nhập yêu cầu recommendation.
7. Xem 3–5 recommendation có explanation và warning.
8. Thử What-if trên cùng eligible set.
9. Mở floating advisor chat.

## Không làm

- Không tự lọc course bằng JavaScript để thay backend.
- Không hiển thị course bị blocked như recommendation.
- Không gửi API key.
- Không tạo màn hình đăng nhập.
- Không tạo trang timetable hoặc xác nhận offering.
- Không yêu cầu database để chạy demo.

## Trạng thái bắt buộc

- selectedProgram.
- transcript selection.
- latestEligibility.
- latestRecommendation.
- session chat history.
- what-if preference state.

Khi selectedProgram thay đổi, phải xóa transcript, eligibility, recommendation và chat context của ngành cũ.

## Hiển thị cảnh báo

- Catalog đang ở trạng thái nháp/chưa xác minh.
- Prerequisite external/unverified.
- Workload/difficulty/topic chưa có dữ liệu.
- Offering hiện tại chưa được xác nhận.
- Kết quả chỉ hỗ trợ tham khảo, không phải quyết định học vụ.

## Tiêu chí hoàn thành

- Người dùng không thể trộn transcript giữa hai ngành.
- UI hiển thị riêng eligible và blocked.
- Gợi ý chỉ hiển thị mã môn do backend trả về.
- What-if không mở khóa course.
- Có happy-path demo từ chọn ngành đến xem explanation.
