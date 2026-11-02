# Module 04 — Preference, xếp hạng và what-if

Cập nhật: 23/10/2026. **Hiện trạng:** có extractor/ranker/fallback; còn lỗi normalization và thiếu baseline revision.

## Trách nhiệm và hợp đồng

app/recommendation/preference.py, scoring.py, ranking.py, llm.py cùng app/services/recommendation_service.py xếp hạng chỉ các môn 03 cho phép.

Đầu vào: eligible set, metadata có sẵn, goal/structured preference, limit/max_credits và weights. Đầu ra: mã môn theo thứ tự, score/fit signals, preference, backend/version và warnings. Module 05 kiểm tra output và dựng explanation.

## Quy tắc

- LLM là extractor/ranker tùy chọn; lỗi provider/output dùng fallback có căn cứ.
- Tie-break offline ổn định theo mã môn; loại mã lạ/trùng trước selection.
- Áp cả limit và tổng max_credits. Không dùng prerequisite_tolerance để nới tiên quyết.
- Metadata thiếu không là bằng chứng môn phù hợp/dễ/nhẹ. Chỉ dùng workload/difficulty/orientation khi có dữ liệu và trọng số tương ứng.

## Kế hoạch input và giới hạn

Sửa lỗi raw_goal tối đa 500 nhưng career_goal chỉ 200 ký tự và lỗi target credits/count ngoài khoảng khiến fallback cũng lỗi. Chuẩn hóa từng trường, phản hồi rõ yêu cầu ngoài hỗ trợ.

Hiện selection dùng request.limit/max_credits, chưa áp các target đọc từ câu. Đề xuất contract: lựa chọn form/structured override rõ ràng ưu tiên; câu tự nhiên bổ sung phần chưa chọn. API phải phân biệt explicit value với default, trả effective constraints và cảnh báo xung đột. Đây là hợp đồng đề xuất, chưa triển khai.

## Kế hoạch what-if

Baseline gồm catalog revision, transcript/context digest, track/path, budget và rule/ranker version. Chỉ thay trọng số/preference xếp hạng. Context đổi yêu cầu baseline mới; response cũ bị loại. Rank delta chỉ có khi baseline hợp lệ; hiện chưa có baseline pinning/rank delta.

## Tiêu chí hoàn thành

Cùng input cho cùng thứ hạng offline; không lọt blocked/completed/foreign, không vượt ngân sách. Kiểm tra câu dài, số ngoài khoảng, yêu cầu 1 môn và mâu thuẫn form/câu. What-if giữ eligible set với cùng context và phát hiện mismatch. Preference thiếu/không hiểu được không làm fallback lỗi ngoài dự kiến.
