# LLM v3 — triển khai offline ID nguồn gọn và giữ bullet

Ngày 11/11/2026 · `hus-llm-rag` · Theo [thiết kế đã duyệt](superpowers/specs/2026-11-11-hus-llm-compact-layout-design.md).

**Đã triển khai đường diễn đạt v3 cho F1/F3; chưa đo Gemini thật trên v3.**
LLM vẫn mặc định tắt, lexical và CURRENT v4 giữ nguyên. F2 vẫn presentation với
canonical/facts/citation/review nguyên vẹn. Không sửa baseline routing/retrieval
để nâng kết quả A7, không có lời gọi Google hoặc ngân sách mới.

## Thay đổi

- `build_evidence()` dùng bundle đã kiểm scope/identity để tạo document v3 cho
  F1/F3. Tách dòng tại LF/CRLF, giữ nguyên mọi source unit/span, marker/indentation
  và citation mapping ở backend. Mỗi đoạn chữ chỉ xuất hiện một lần trong wire;
  không lặp full quote vào output. CR đơn/Unicode separator không chia một unit.
- Model trả strict JSON `rewrite_v3/items`, mỗi item chỉ có ID khối và text.
  Phải đủ/unique/đúng ID; output order không đổi display order. Backend phục hồi
  skeleton, từng bullet và citation, kiểm toàn bộ rồi mới tạo `HUSTextRewrite`.
- Giữ guard từ ngữ v2 trong đúng leaf: đủ từ theo thứ tự của từng unit, số/mã/
  điều kiện/phủ định/ký hiệu. Anchor mở rộng nội bộ không cấp quyền dùng atom của
  leaf khác. Thêm guard v3 giữ ký hiệu/toán tử và vị trí tương đối với từ nguồn.
- Text model không được thêm newline/list/heading/HTML/link/citation markup.
  Hợp đồng kết quả giữ leading indentation, vẫn từ chối reply chỉ có whitespace.
  Sai/thiếu/quá trần → exact canonical A; source/canonical fault vẫn fail closed.
- Client và trace measurement ghi diagnostic enum/count-only: finish reason
  chuẩn hóa, content type/length/tool-presence, validation stage và ID đã biết.
  Không lưu raw output bị loại hoặc provider error/header; chặn lộ input qua
  chained traceback của JSON/Pydantic. API vẫn dùng các fallback reason cũ.
- Default adapter, prepare và export payload dùng cùng dispatcher/prompt v3.
  `build_bundle()` và validator v2 còn cho consumer legacy rõ phiên bản; không
  tự nhận output `rewrite/points/anchor_quote` trong lời gọi v3. Replay lịch sử
  dùng observation/score cũ, không chạy validator mới để đổi kết quả.

Giới hạn giữ nguyên: **12.000 prompt chars, 8.192 raw chars, 1.024 output token**,
HTTPX 20 giây mỗi pha, một lời gọi/process, không retry/stream/redirect. V3 có
64 leaf/128 coverage unit/document; 3.000 ký tự/leaf gồm prefix, kiểm trước/sau.
Không cắt hay bỏ nguồn để vừa ngân sách, không gửi tài khoản/bảng điểm/history/key.

## Diagnostic bằng output synthetic

Giữ nguyên canonical A của cohort L5 v4 cũ, không retrieval/provider mới. Dựng
JSON chép đủ text từng leaf để kiểm hợp đồng; đây **không phải generation thật**.

| Ca đã lộ | Leaf / coverage unit | Raw JSON v3 | Kết quả synthetic |
| --- | --- | --- | --- |
| Q005/Q013/Q029 — F3 MAT3148 | 19 / 39 | 2.710 chars | Giữ đủ nguồn, chấp nhận; bỏ leaf bị chặn |
| Q021 — F3 MAT3311 | 23 / 41 | 2.842 chars | Không còn trần 20 points trên v3; giữ đủ nguồn |
| Q022 — mục tiêu MAT3418 | 5 / 5 | 383 chars | Bốn bullet riêng, canonical không đổi |

Không suy token từ ký tự hoặc gọi synthetic acceptance là model thành công.
Ngân sách 1.024 token vẫn có thể không đủ; chưa biết tỷ lệ used/fallback, latency
và cải thiện diễn đạt thật của v3. Source F3 vẫn là tham khảo AI, chưa được xác minh
đề cương HUS. Schema/lexical/symbol checks chưa chứng minh entailment hoặc chặn
mọi câu bổ sung sai; paraphrase hợp lý vẫn có thể fallback.

## Review và kiểm chứng

82 regression mới về document/prompt/validator/pipeline/diagnostics được kiểm trong
bộ LLM cuối **480 passed** (129,64 giây). Bộ rộng trước lần chốt câu nhắc toán tử/
guard tỷ lệ đạt **647 passed** (487,56 giây), gồm API/UI/quyền/rollback và A7;
hai số có giao nhau, không cộng. Ruff/diff-check đạt; một warning Starlette đã có.
Test bao
gồm nguồn nhiều citation, CR/Unicode, list số/lồng, ID lạ/lặp/thiếu, merge/bỏ ý,
mượn số/nguồn, phủ định/điều kiện, newline/link/HTML, các cap và quyền/canonical.

Review kỹ thuật **0 Critical/1 Important/0 Minor**. Đã tái hiện lỗi giữ từ nhưng
đổi `x ≠ y` thành `x = y`; 10 regression RED→GREEN bổ sung ký hiệu/toán tử và vị
trí của chúng, thêm case Unicode/neutral connector hợp lệ. Sau đó ratio-colon và
câu nhắc giữ toán tử cũng có RED→GREEN trước bộ LLM cuối. Guard mới chỉ thuộc
v3, legacy v2 không đổi. Không có independent re-review hoặc chứng nhận ngữ nghĩa.

[A7](RAG_A7_V4_2026_11_11.md) r1 được khóa trước thay đổi; r2 ghim code cuối và
kiểm lại cùng questions/gold/evidence. **48/48 exact response/trace giống r1**,
Recall@5 vẫn 19/24 và đủ ý 27/36, chưa đạt. Review AI được tái gắn sau kiểm mọi
hash, không phải holdout/review độc lập mới. LLM chỉ nhận canonical đã answered
nên v3 không chữa các ca RAG từ chối. Pins r2 khớp, r1 và các điểm cũ giữ nguyên.

Archive/hash/log/diagnostic ở `backups/hus_llm_compact_20261111/` (ignored).
[Receipt triển khai offline](../data/hus/qa/20261111/llm_compact_v3_r1/report.json)
ghim các kiểm chứng và giới hạn; không phải receipt nghiệm thu Gemini thật.
2.375 file dữ liệu/evidence cũ và 45 file frontend giữ SHA; canonical RAG ngoài
package LLM không đổi. Bốn artifact L5 và hai A7 r1 replay được bằng cache;
pins cũ là lịch sử, không nhận là nghiệm thu code v3 hiện tại.
Không sửa snapshot/gold/run/review cũ, không commit/push/deploy hoặc bật model.
Muốn đo L5 v3 thật cần chuẩn bị cohort/pins và duyệt ngân sách Google riêng.

[Roadmap](RAG_PROGRESS_AND_NEXT_PLAN.md) · [Package LLM](../app/hus/llm/README.md)
