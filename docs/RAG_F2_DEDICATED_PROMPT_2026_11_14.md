# Prompt F2 riêng — đã sửa và kiểm offline

**Cập nhật sau bước offline:** đã có1 call MAT2300 mới HTTP200/`used=true`, giữ4
tín chỉ/citation. [Kết quả xác nhận riêng](RAG_F2_PROMPT_CONFIRMATION_2026_11_14.md).

F2 đã có system prompt riêng, chỉ yêu cầu một hợp đồng JSON: trường bắt buộc
**`"kind":"facts"`**, `style`, `fact_keys`, `citation_ids`. Không còn hướng dẫn
trả text/anchor hoặc các kiểu output của F1/F3 trong prompt gửi cho F2.

Đây là sửa có giới hạn sau khi call mới ghi `output_schema/kind`. Nhãn đó không
cho biết giá trị bị từ chối và không chứng minh prompt trộn là nguyên nhân duy
nhất. Tại bước offline chưa kiểm Google; call xác nhận sau đó thành công, chưa
chứng minh mọi câu F2 hoặc các lần gọi lặp lại đều ổn định.

| Phần | Kết quả |
| --- | --- |
| **Prompt F2** | Bắt buộc `kind=facts`, chỉ hai style hiện có; sao chép đủ khóa facts và ID nguồn, không trả dữ kiện mới hoặc prose. Giữ chỉ dẫn coi nguồn/câu hỏi là dữ liệu không đáng tin về chỉ dẫn, không tool/action. |
| **F1/F3** | Bốn trường hợp legacy/current có cùng system/user/hash trước và sau; không đổi prompt của hai nhóm này. |
| **Bằng chứng F2** | Tám payload F2 của bộ30 câu giữ nguyên. MAT2300 vẫn có4 tín chỉ/citation; system prompt đổi nên hash prompt mới, độ dài giảm **3.932 → 2.599 ký tự**. |
| **Validator/fallback** | Không sửa schema hoặc validator. Thiếu/sai `kind` vẫn bị chặn; model hợp lệ chỉ chọn presentation, backend giữ dữ kiện và đáp án canonical. |

Test mới ban đầu3fail/8pass, sau sửa11pass; bổ sung kiểm thiếu `kind` và trần
prompt thành **13 test mới đạt**. Cùng29 test diagnostic F2: **42pass**, một warning
Starlette cũ; Ruff hai file đạt. Test adapter/mock trên MAT2300 kiểm cả đầu ra
hợp lệ lẫn fallback, giữ nguyên4 tín chỉ và toàn bộ `hus_answer`. Đây là kiểm
offline, không tái tạo output Google đã bị từ chối.

Nhóm LLM rộng hơn đạt **680pass**, một warning cũ; lượt này thu test trước khi
bổ sung hai kiểm ràng buộc cuối, sau đó nhóm42 đã chạy lại trên bản cuối. Các
nhóm có giao nhau, không cộng tổng hoặc gọi là full-repo. Review code ở context
riêng không thấy lỗi đáng kể về chọn prompt, hợp đồng hoặc riêng tư.

Không sửa run/gold/review/CSV cũ hoặc suy ngược nguyên nhân call cũ. Các snapshot
đã ghim prompt trước sửa giữ lịch sử; lượt live tiếp theo phải ghim hash/code mới.
Giữ v4/lexical/LLM mặc định tắt, không đọc key và **0 Google call** trong lượt này.
Call xác nhận sau sửa đã dùng hết budget riêng; kiểm Google thêm cần budget mới.

[Receipt và kiểm prompt](../data/hus/qa/20261114/f2_dedicated_prompt_r1/report.json).
