# Xác nhận prompt F2 mới — một call đã dùng được Gemini

Đã kiểm câu **“MAT2300 có bao nhiêu tín chỉ?”** trên prompt F2 riêng và code hiện
tại. Dùng đúng **1/1 call mới được duyệt**, không retry hoặc đổi model.

| Mục | Kết quả |
| --- | --- |
| Google |HTTP200, actual model `gemini-3.5-flash-lite` |
| Pipeline |**`used=true`**, không fallback, không có lỗi validation |
| Dữ kiện |**4 tín chỉ**, facts/citation và `hus_answer` nguyên trạng; reply giữ khối dữ kiện canonical |
| Prompt |2.599 ký tự; hash mới đã ghim trước call |
| Usage |775 input/53 output token, tổng828; dưới cap1.024 output token |
| Thời gian provider |Khoảng **1,62 giây** trong một lượt local, không phải cam kết latency |

Key backend chỉ dùng trong bộ nhớ. Không lưu key hoặc raw output bị từ chối,
không chỉnh key/billing/default. Chi phí thực chưa tính. Budget1 call đã hết.

Verification chỉ đọc xác nhận **3.091 file cũ nguyên SHA**, pins khớp,4 tín chỉ
và nguồn giữ nguyên. Không sửa runtime hoặc chạy lại suite vì code không đổi
trong lượt xác nhận. Các test offline đã được lưu ở [bước sửa prompt](RAG_F2_DEDICATED_PROMPT_2026_11_14.md).

Run30 câu và CSV nhóm vẫn giữ **23 dùng Gemini/1 fallback/6 control** của lần đo
đó. Call lỗi `kind` trước sửa vẫn là kết quả lịch sử, không được gán thành công
hoặc suy nguyên nhân ngược từ call mới. Đây là **một xác nhận mới thành công**,
chưa chứng minh mọi câu F2 đều ổn định hoặc thay review nội dung của nhóm.

Giữ v4/lexical/LLM mặc định tắt. Nhóm có thể tiếp tục review30 câu và hoàn thiện
báo cáo; khi cần kiểm Google thêm, thống nhất ngân sách mới.

[Receipt live](../data/hus/qa/20261114/f2_prompt_confirmation_r1/report.json) ·
[Verification](../data/hus/qa/20261114/f2_prompt_confirmation_verification_r1/report.json).
