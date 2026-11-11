# Diagnostic F3 dài và bố cục Q022

Ngày 11/11/2026 · `hus-llm-rag` · **Offline, 0 lời gọi Google mới.**

Đã phân tích run L5 v4 và tái hiện các giới hạn của hợp đồng hiện tại. Người dùng
chọn hướng **tiếp tục diễn đạt, dùng ID nguồn gọn và giữ bullet**. Báo cáo này ghi
diagnostic trước triển khai. Sau đó người dùng đã duyệt và [v3 được triển khai
offline](RAG_LLM_COMPACT_V3_2026_11_11.md); chưa khẳng định đã chữa được các ca sinh
thật. Lexical và LLM mặc định tắt, `CURRENT` v4 không đổi.

## Kết quả theo từng ca

| Ca | Nguồn / unit coverage | Prompt chars | Completion tokens thật | Kết quả đã lưu |
| --- | --- | --- | --- | --- |
| Q005 — KHMTTT | 4 / 39 | 6.597 | 1.020 | `invalid_response` |
| Q013 — KHDL | 4 / 39 | 6.577 | 302 | `evidence_coverage` |
| Q021 — Toán học | 5 / 41 | 6.912 | 1.020 | `invalid_response` |
| Q029 — Toán Tin | 4 / 39 | 6.632 | 1.020 | `invalid_response` |
| Q022 — mục tiêu MAT3418 | 1 / 5 | 3.683 | 163 | Dùng, đủ ý nhưng gộp bốn bullet thành một câu |

ID đầy đủ là `L5V4-Qxxx`. Ba ngành có cùng nội dung MAT3148; không coi đó là ba
khái niệm độc lập. Q021 là MAT3311. Target được hỏi nằm trong bundle, nhưng bundle
còn có tổng quan và chủ đề khác: guard v2 yêu cầu giữ **mọi nguồn đã chọn**, không
chỉ target. Không được bỏ phần này rồi coi là giữ nguyên phép so sánh.

## Những gì đã chứng minh offline

**1. Prompt và schema tạo áp lực không cần thiết lên output.**
[Prompt v2](../app/hus/llm/prompts.py) gợi ý một point cho mỗi câu/list item/mệnh đề.
[Coverage](../app/hus/llm/coverage.py) tách cả newline và dấu chấm phẩy, nên bốn ca
dài có 39–41 unit, dù chỉ có 19–23 dòng hiển thị không trống. Trong khi đó
[schema](../app/hus/llm/output.py) giới hạn 20 points, 8.192 raw chars, text 3.000
chars/point; [client](../app/hus/llm/client.py) giới hạn 1.024 output tokens.

| Cách dựng synthetic, giữ đủ nguồn | MAT3148 (Q005/013/029) | MAT3311 (Q021) |
| --- | --- | --- |
| Text + anchor, mỗi citation một point | 4.743 chars / 4 points, qua validator | 4.875 chars / 5 points, qua validator |
| Text + anchor, mỗi coverage unit một point | 12.045 chars / 39 points, quá raw budget và point cap | 9.935 chars / 41 points, quá raw budget và point cap |
| Phác thảo ID leaf + text, chưa là adapter | 2.710 chars / 19 leaf | 2.842 chars / 23 leaf |

Cách dựng per-unit dùng exact unit làm anchor nếu đủ 20 ký tự, nếu ngắn thì dùng
full quote cùng citation. Anchor tổng cộng 7.903/5.662 ký tự, còn text chỉ
2.211/2.249 ký tự. Đây là **một** cách dựng đúng hướng dẫn anchor, không phải cận
dưới hoặc dạng JSON duy nhất. Validator được kiểm riêng để xác nhận lỗi 20 points
ngoài lỗi raw budget; không nới các trần trong runtime.

Exact-copy theo citation được validator chấp nhận chứng minh có biểu diễn hợp lệ
về ký tự/schema; **không chứng minh model đã sinh, vừa token hay cải thiện câu chữ**.
Phác thảo ID chỉ đo kích thước JSON, chưa kiểm schema/validator v3. Không suy token
từ số ký tự. Quét 580 field F3 trên 290 hồ sơ: tối đa 28 leaf và 55 coverage unit
mỗi field toàn hồ sơ; không phải kiểm retrieval hay mọi bundle F1.

**2. `invalid_response` chưa chỉ ra nguyên nhân cụ thể của ba ca thật.**
Client gom nhiều lỗi envelope vào cùng code. Năm envelope HTTP 200 synthetic gồm
`finish_reason=length`, content rỗng, có tool call, thiếu model hoặc thiếu choices
đều trả `invalid_response`. Trace cũ chỉ giữ model/usage/HTTP/error, không giữ
finish reason hoặc output bị loại. Vì vậy 1.020 token gần cap 1.024 là tín hiệu cần
đo thêm, **không phải bằng chứng cả ba bị cắt token**. Cũng chưa biết unit cụ thể
bị thiếu trong Q013, vì output bị loại không được lưu.

**3. Q022 là thiếu ràng buộc bố cục, không phải thiếu dữ kiện đã phát hiện.**
Nguồn có dòng dẫn và bốn bullet mục tiêu. B đã lưu gộp chúng thành một câu. Dựng
JSON diagnostic từ **đúng text B đã hiển thị**, gắn full anchor hợp lệ: validator
hiện tại chấp nhận. Không gọi đó là provider JSON gốc. Giữ nguyên bullet cũng qua;
bỏ bullet cuối vẫn bị `evidence_coverage`. Guard kiểm đủ từ/số/anchor, chưa kiểm
quan hệ list item hoặc readability. Prompt “prefer a point…” không ràng buộc được
schema, renderer chỉ nối các point bằng dòng trống.

**4. Fallback đang giữ đúng hợp đồng an toàn.** Bỏ citation đầu ở cả bốn ca F3
bị `evidence_coverage`; không bỏ tổng quan/nguồn phụ để ép vừa ngân sách. Các B
fallback đã lưu vẫn exact A. Không chạy validator mới lên run cũ để đổi điểm.

## Hướng thiết kế đã chọn và việc còn lại

Đề xuất [document/output v3](superpowers/specs/2026-11-11-hus-llm-compact-layout-design.md):
backend cấp ID cho các leaf từ đúng canonical bundle; model trả text + ID, không
lặp anchor. Backend giữ mapping span/citation, kiểm đủ từng leaf bằng guard v2,
dựng layout và mỗi bullet riêng. Toàn bộ nguồn vẫn được gửi, chỉ đổi cách đóng gói.
F2 và nhãn AI/opt-in/canonical/facts/review giữ hợp đồng hiện có.

Giữ các trần hiện tại; chưa hứa 1.024 token đủ cho F3 dài. Thiết kế chi tiết đã
được duyệt và triển khai offline trong báo cáo v3 riêng; phép đo thật cần prepare mới.
Nếu đo tiếp, cần cohort/pins/ngân sách riêng, báo used/fallback và review cả hai;
không sửa run/gold/review cũ, không coi exact-copy hoặc fallback là gain diễn đạt.
Ngân sách 24 lời gọi trước đã hết; không retry các ca thất bại.

## Evidence và bảo toàn

- [Receipt mới](../data/hus/qa/20261111/llm_long_f3_diagnostic_r1/report.json)
  chứa thống kê 16 ca F1/F3 để đối chiếu ngắn/dài và các proof synthetic.
- Nguồn: [run live bất biến](../data/hus/evaluation/runs/llm_l5_v4_google_20261111_r1/report.json),
  [review exact response](../data/hus/evaluation/reviews/llm_l5_v4_ai_20261111_r1.json).
- Script/evidence cục bộ: `backups/hus_llm_diagnostic_20261111_r1/` (ignored),
  `analyze.py`, `prove.py`, `shape_sizes.py`, stats/details/proof và snapshot SHA.
  Đã chặn external transport trong proof envelope/replay; 5 mock requests,
  không provider/retrieval thật, không đọc `.env` hoặc template.
- 2.550 file code/test/tool/data đã có giữ SHA, prepared r3 pins khớp, replay hai
  artifact live/review tái hiện. Không commit/push/deploy. Nội dung F3 vẫn là
  tham khảo AI, human review = 0; diagnostic không nghiệm thu học thuật hoặc L6.

[Roadmap](RAG_PROGRESS_AND_NEXT_PLAN.md) · [Báo cáo L5 v4](RAG_LLM_L5_V4_2026_11_11.md)
