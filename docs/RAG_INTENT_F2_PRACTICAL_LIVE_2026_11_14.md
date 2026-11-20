# Kiểm Gemini thật cho ý định/F2 — 14/11/2026

Đã chạy gói được cho phép, dùng **11/12 call**, không retry/đổi model. Kết quả:
**6/8 câu F2 có đáp án dùng model**,1 lỗi output và1 yêu cầu làm rõ;4 control
không gọi Google. Không có fallback offline trong lượt này. Review người thật
còn pending; đây là kiểm chức năng bộ câu do AI soạn, không phải điểm độ chính
xác hoặc nghiệm thu độc lập.

## Bằng chứng

- [Run đã seal](../data/hus/evaluation/runs/intent_f2_student_live_20261114_r1/report.json),
  [observations theo từng call](../data/hus/evaluation/runs/intent_f2_student_live_20261114_r1/observations.json),
  [manifest](../data/hus/evaluation/runs/intent_f2_student_live_20261114_r1/manifest.json).
- [Đáp án nguyên văn](RAG_INTENT_F2_PRACTICAL_LIVE_RESPONSES_2026_11_14.md),
  [CSV nhóm review](../data/hus/review/intent_f2_student_live_20261114_r1/review.csv),
  [tổng hợp riêng](../data/hus/review/intent_f2_student_live_20261114_r1/summary.json).
- [Tiền kiểm lịch sử](RAG_INTENT_F2_PRACTICAL_PREFLIGHT_2026_11_14.md) giữ nguyên
  trạng thái tại lúc chuẩn bị; giấy phép12 call mới nằm trong receipt live.

Snapshot vẫn v4, F2 cấu trúc;74 code pins và toàn bộ prompt đã kiểm khớp trước
gọi.11 call gồm4 hiểu ý định và7 diễn đạt; tất cả HTTP200, actual model
`gemini-3.5-flash-lite`. Tổng **21.316 input/653 output token** (21.969 tổng),
chi phí tiền thực chưa xác định. Tổng thời gian provider15,392s; wall từng câu
có cả chờ pacing, không dùng làm latency riêng của model hoặc hybrid.

| Ca | Thực tế |
| --- | --- |
|001 |Dùng được F2 count90 danh mục Toán học. |
|002 |Hiểu ý định đã qua kiểm để gọi generation; generation bị chặn `output_coverage/fact_keys`, API báo lỗi, không trả offline thay thế. |
|003 |Dùng được danh sách68 mã/tên Toán tin. |
|004 |Một call hiểu ý định, trả yêu cầu làm rõ; không gọi diễn đạt, chưa đếm được từ cách hỏi này. |
|005 |Dùng được F2 count67 danh mục KHMTTT. |
|006 |Hiểu ý định và diễn đạt dùng được; MAT1204/KHMTTT giữ3 tín chỉ. |
|007 |Dùng được danh sách65 mã/tên KHDL. |
|008 |Hiểu ý định và diễn đạt dùng được; MAT3533/KHDL giữ3 tín chỉ. |
|009–012 |Sai ngành/số môn phải học/F3 chưa cho phép/môn không có đều không gọi Google, giữ phản hồi theo guard. |

Sáu đáp án được dùng giữ nguyên canonical/facts/citation/warnings/release so với
tiền kiểm; ở lượt này cả phần trình bày cũng trùng bản tiền kiểm. F2 chỉ cho model
chọn presentation, không phải model tự sinh số hoặc danh sách. Vì vậy chưa có
bằng chứng cải thiện diễn đạt. Số môn danh mục khác số môn mỗi sinh viên phải học.

## Hai ca chưa đạt

**002:** nhãn chỉ xác định tập `fact_keys` không đáp ứng hợp đồng. Không lưu raw
output nên chưa biết key cụ thể thiếu/thừa/trùng; không suy model đổi số môn.
Response lỗi không chứa metadata interpretation, nên báo cáo tổng3
`interpretation.used` ở response không có nghĩa chỉ3 call hiểu ý định đã chạy:
thực tế4 call, và002 đã đi tới generation.

**004:** response là `needs_clarification/clarification_required`; không coi
`interpretation.used=true` là trả được phép đếm. Không lưu JSON raw để suy đoán
nhánh nội bộ xa hơn. Nếu chọn sửa, cần regression/prompt mới và lượt xác nhận riêng.

## Giới hạn thao tác

Code giới hạn tối đa12 call, cách5 giây tại bước reserve monotonic, dừng
401/403/429 hoặc hai503 liên tiếp, không retry/đổi model. Không có timestamp
HTTP-send độc lập để đo lại khoảng cách gửi; pacing có bằng chứng ở code/trace.
Reviewer AI kiểm riêng manifest,74 pins,11 prompt thực, token/model và canonical;
không ghi nhận lỗi receipt quan trọng, không thay review nội dung của nhóm.

Lượt đã kết thúc, **1 call chưa dùng không được tự dùng để retry, sửa điểm hoặc
chuyển sang review guard**. Không in/lưu key, body lỗi hay text bị validator loại;
không đổi key/billing/cấu hình mặc định. Không sửa pack, run/gold/review lịch sử.

[Kế hoạch tiến độ](RAG_PROGRESS_AND_NEXT_PLAN.md)
