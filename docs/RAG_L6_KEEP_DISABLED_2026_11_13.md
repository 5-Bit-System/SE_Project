# L6 — giữ tắt, assessment code hiện tại và kiểm rollback

Ngày **13/11/2026**, nhánh `hus-llm-rag`, nền `f61b0fd` + WIP.
Đã ghi **assessment r2** theo code sau thay đổi diagnostic/circuit:
**`keep_disabled`**, `eligible_for_manual_acceptance=false`, không activation.
Không có run sinh thật trên pins hiện tại để nghiệm thu facts/citation/đủ ý,
gain hoặc latency model. **L6 chưa được nghiệm thu bật mặc định.**

## Bằng chứng và phần còn thiếu

| Điều kiện | Trạng thái hiện tại |
| --- | --- |
| Live output trên đúng code/data/prompt/model | Chưa có. L5 v3 gần nhất24 HTTP403,0 used/24 fallback; pins khác code hiện tại. |
| Facts/citation/đủ ý của bản sinh thực | Chưa đo được ở lượt v3 này.24 fallback đủ ý không là thành công LLM. |
| Gain diễn đạt và không hồi quy | Chưa có bằng chứng trên bản sinh v3. Không thay bằng kết quả protocol v2 cũ hoặc output mock. |
| Latency used trên máy demo | Không có mẫu used; p50/p95 null.722/799ms fallback là latency lỗi403 lịch sử, không phải latency sinh nội dung. |
| Fallback/rollback kỹ thuật |60 test readiness/rollback pass, gồm6 regression mới cho401/403. Đây là kiểm offline bằng transport giả. |
| Operator nghiệm thu nội dung/latency/rollback | Chưa có; không ký thay operator hoặc dùng review AI thành nghiệm thu độc lập. |
| Mặc định vận hành |Giữ `HUS_LLM_ENABLED=false`, lexical/CURRENTv4; không đổi cấu hình riêng hay process demo đang chạy trong bước kiểm này. |

Assessment r2 ràng buộc exact review/response/source manifest của run L5 v3 cũ;
checker chỉ đọc cache/hash, không dựng lại câu trả lời hoặc gọi model/retrieval.
Các lý do chặn:

```text
latency_unavailable
no_generated_output
no_supported_readability_gain
no_used_output_f1
no_used_output_f2
no_used_output_f3
observed_model_changed
pins_changed
```

`observed_model_changed` ở đây do observed models rỗng, không có bằng chứng
model thực bị đổi. Pins recorded `c8b580a…`, hiện tại `33ab82ee…`; prepared
`llm_v3_v4_prepared_20261113_r2` khớp code mới nhưng **chỉ là prepared**, chưa có
run Google mới. Assessment r1 và các run/review/gold cũ giữ nguyên.

## Kiểm fallback/rollback offline

Đã chạy `test_activation.py`, `test_readiness_v4.py`, `test_rollback.py`:
**60 passed**, một warning Starlette/httpx đã có; Ruff đạt.
Sáu ca mới thêm401/403 vào F1/F2/F3, dùng RAG/adapter/client thật với transport
HTTP giả và key tổng hợp trong process test; không đọc key/backend `.env`.

- Off → on giả lập → off trên12 tổ hợp4 ngành ×3 family: giữ nguyên canonical;
  khi tắt, API trả ba key cũ và `/hus/config` báo không khả dụng cho rewrite.
- Timeout/transport/429/401/403/invalid output → fallback → off: reply và
  `hus_answer` bằng baseline, không lộ error text/key/project ID; không gọi
  provider thêm sau tắt. F2 facts/citation không được model sửa.
- Cờ off không cần key hoặc URL/model hợp lệ; server bật vẫn cần opt-in rewrite
  và quyền F3 riêng. Nguồn canonical hỏng vẫn503, không che bằng fallback LLM.

Chỉ thay test rollback; không đổi runtime/prompt/validator/dữ liệu trong bước
này. Không coi thời gian test/mock là latency Gemini hoặc nghiệm thu UI/máy nộp.
519 test LLM đã pass ở bước trước có phần giao nhau với60 này, không cộng tổng.
**2.777/2.778 file cũ giữ SHA**, chỉ test rollback đổi. Prepared r2 vẫn khớp
pins; ba L5 lịch sử và A7 mới replay được, không sửa điểm hoặc receipt cũ.

## Cảnh báo AI Studio người dùng vừa cung cấp

Người dùng báo banner “You are approaching a bandwidth limit” kèm đề nghị
configure billing. Đây là thông báo **gần giới hạn**, không chứa error body403
hoặc trạng thái cụ thể của key/project. Chưa đủ bằng chứng gán nguyên nhân403
cho quota, billing hoặc key bị chặn; chưa xác nhận đã khắc phục quyền.

Google công bố giới hạn RPM/TPM/RPD áp dụng theo project/model/tier; cần xem
các giới hạn thực trong AI Studio. [Rate limits chính thức](https://aistudio.google.com/docs/rate-limits).
Với403, kiểm thông báo riêng về trạng thái project/key để xử lý đúng trường hợp;
không suy việc bật billing chắc chắn sửa được lỗi này.
[Hướng dẫn403 của Google](https://aistudio.google.com/docs/troubleshooting#project-unavailable).

Không thay key, bật billing hoặc gọi API mới từ banner. Hai budget24 calls đã
hết; đề nghị chẩn đoán1 call ở bước L5 vẫn chưa được duyệt.

## Điều kiện xét lại

1. Xử lý quyền Google theo trạng thái thực; có ngân sách chẩn đoán/cohort mới
   riêng. Không chạy lại run cũ hoặc tự retry/đổi model.
2. Kiểm pins, tạo run mới có đầu ra thực cho F1/F2/F3. Review exact response,
   gồm fallback, facts/citation/đủ ý và bố cục; giữ đủ ý, cap1.024 token.
3. Tách used/fallback, số mẫu, token/lỗi, gain và latency. Đo trên máy demo,
   phân biệt thời gian provider/incremental rewrite với thời gian người dùng
   chờ; operator ghi ngưỡng chấp nhận trước khi quyết định, không bịa SLO.
4. Kiểm lại off/rollback và UI trên môi trường sẽ dùng. Operator ghi người/
   thời điểm/run manifest/phạm vi và quyết định trong **receipt mới**.
   Checker đạt chỉ là điều kiện xem xét, không tự bật.

[Mẫu ghi nhận operator](../data/hus/qa/20261113/l6_keep_disabled_r1/operator_acceptance_template.json)
còn pending, không phải giấy chấp nhận hoặc đầu vào tự động bật cờ. Khi có run
mới, tạo bản ghi mới; không điền đè file/assessment đã seal của bước này.

[Assessment r2](../data/hus/evaluation/runs/llm_l6_v3_readiness_20261113_r2/assessment.json),
[receipt kiểm chứng](../data/hus/qa/20261113/l6_keep_disabled_r1/report.json),
[runbook rollback](HUS_LLM_OPERATIONS.md#rollback-về-bản-trích-nguồn),
[L5 diagnostic/prepared r2](RAG_LLM_ACCESS_DIAGNOSTIC_2026_11_13.md).

Manifest assessment `8486f8c1333de047d1677b070e88d575722b7f4232ceffa6d33e9cefd9da80a5`;
manifest QA `1258cd84c9e45e1c98875ad63ca9003471e3993889f5c136e9eee32b9af145a2`.
