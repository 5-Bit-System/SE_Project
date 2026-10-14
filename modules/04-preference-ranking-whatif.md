# Module 04 — Preference, xếp hạng và What-if

## Mục tiêu

Biến yêu cầu tự nhiên thành preference có cấu trúc và xếp hạng chỉ trên tập eligible.

## Phạm vi

- Preference schema gồm workload, difficulty, orientation, interest topics, career goal, target credits, target course count, course type và prerequisite tolerance.
- Fallback extraction bằng rule/keyword khi LLM không có.
- Ranking deterministic bằng metadata catalog.
- What-if thay đổi trọng số hoặc preference trên cùng eligible set.
- Tie-break ổn định bằng course code.

## Không làm

- Không đánh giá eligibility.
- Không đưa blocked/completed course vào ranking.
- Không tự tạo metadata thiếu.
- Không khẳng định môn dễ, nhẹ hoặc phù hợp nếu catalog không có dữ liệu.
- Không dùng model training hoặc collaborative filtering.

## Dữ liệu đầu vào

- Preference text hoặc structured preference.
- eligible_courses đã được Module 03 xác nhận.
- Course metadata có sẵn.
- What-if weights nếu có.

## Dữ liệu đầu ra

- Danh sách course code theo thứ tự.
- Score hoặc fit signals.
- Preference đã được kiểm tra hợp lệ.
- Ranking backend/version.
- Các thuộc tính còn thiếu dữ liệu.
- Rank delta khi chạy What-if nếu có baseline.

## Quy tắc chấm điểm

Có thể dùng các tín hiệu:

- topic/interest match.
- career goal/orientation match.
- workload match nếu metadata tồn tại.
- difficulty match nếu metadata tồn tại.
- course type/hands-on match nếu metadata tồn tại.

Thuộc tính thiếu phải được giữ là chưa biết và không được chấm như phù hợp hoặc không phù hợp một cách chắc chắn.

## Tiêu chí hoàn thành

- Cùng input và version cho cùng thứ hạng.
- LLM/ranker trả mã lạ bị loại.
- What-if chỉ đổi score/rank, không đổi eligible set.
- Có deterministic fallback khi LLM lỗi hoặc không có API key.
