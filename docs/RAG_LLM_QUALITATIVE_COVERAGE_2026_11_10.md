# Sửa coverage ý định tính — diagnostic DEV-Q025

Ngày10/11/2026, local trên `hus-llm-rag`, base `1aca071` + WIP chưa commit/push.
Phạm vi là bước1 của roadmap: bổ sung guard tổng quát và regression, **không gọi
Google/đo A/B mới, không bật LLM, không sửa run/gold/review/receipt L5/L6 cũ**.

## Nguyên nhân và cách tái hiện

Validator v1 kiểm citation/anchor và atom số/mã, chưa kiểm các ý không chứa số
trong text. `DEV-Q025` giữ năm1993 và tên cũ nhưng bỏ ý cập nhật chương trình.
Một anchor đầy đủ vẫn có thể đi cùng text thiếu ý; việc model tự khai báo coverage
hoặc thêm lời nhắc không đủ để ngăn lớp lỗi này.

Provider JSON gốc không được lưu trong L5. Diagnostic mới ghi rõ **JSON tái dựng**
từ câu B đã hiển thị, với anchor hợp lệ; không gán nó là provider raw response.
Đã thử thêm biến thể giữ nguyên câu đầu nguồn và bỏ câu sau để tách lỗi lược ý
khỏi khác biệt về cách diễn đạt. Kết quả:

| Input tái dựng/candidate | Validator v1 | Validator v2 |
| --- | --- | --- |
| Text B đã lưu, anchor đầy đủ | Chấp nhận | `evidence_coverage` |
| Nguyên câu đầu nguồn, thiếu câu sau | Chấp nhận | `evidence_coverage` |
| Đủ quote nguồn | Chấp nhận | Chấp nhận |

Đây là diagnostic offline, không phải kết quả generation hoặc A/B mới.

## Policy chung đã triển khai

`app/hus/llm/coverage.py` tách quote F1/F3 thành đơn vị tại câu, newline và dấu
chấm phẩy, giữ span gốc và toàn bộ nội dung không phải whitespace. Đây là ranh
giới văn bản phục vụ coverage, không tự nhận đã trích xuất mệnh đề ngữ nghĩa.

Mỗi đơn vị phải có tất cả token từ ngữ theo đúng thứ tự trong text của một point
thuộc **cùng citation**, và anchor point đó phải chứa **nguyên đơn vị**. Chuẩn hóa
NFKC/casefold, giữ dấu, phủ định, điều kiện và từ chức năng; không lọc stopword,
đoán synonym, dùng tỷ lệ hoặc danh sách từ riêng cho Q025/ngành/năm/chủ đề.
Đơn vị chỉ có ký hiệu cần xuất hiện nguyên ký hiệu, không bị bỏ qua vì thiếu từ.

Một point có thể giữ nhiều đơn vị, hoặc mỗi đơn vị một point. Không mượn text/
anchor của citation khác, không dùng full anchor bù text thiếu. `output.py` gọi
guard sau các kiểm v1; lỗi vẫn `evidence_coverage` và L2 trả nguyên canonical.
Prompt chuyển **protocol v2**, nêu rõ giữ cả thông tin ngữ cảnh dù câu hỏi hẹp.
Wire schema không đổi; F2 vẫn return sớm bằng style/fact keys/citation IDs.

Không thay source/RAG/retrieval hoặc tự truncate để ép vừa. Prompt<=12.000 ký tự,
raw output<=8.192 ký tự, output cap1.024 token, HTTPX20s mỗi pha và no-retry giữ nguyên.

## Đổi lại và giới hạn

Đây là policy **giữ từ ngữ có căn cứ, bảo thủ**, cho phép thêm câu nối/định dạng,
không phải viết lại tự do với mọi synonym/đảo từ. Một paraphrase đúng vẫn có thể
bị từ chối; nguồn/câu dài có thể fallback nhiều hơn trong ngân sách cũ.

Giữ đủ từ **không chứng minh entailment hoặc đủ ý ngữ nghĩa**, không ngăn mọi câu
bổ sung sai, đảo phạm vi phủ định, quan hệ hoặc tác động dấu câu. Test mới chứng
minh lớp bỏ từ/đơn vị đã tái hiện bị chặn; không tự công nhận mọi bản dùng là đúng.
Phải đo mới tỷ lệ used/fallback, nội dung/readability/token/latency ở bước2 L5.

## Kiểm chứng và bảo toàn evidence

25 test mới: omission ở F1/F3 qua câu/newline/chấm phẩy, full-anchor giả coverage,
keyword list, điều kiện/phủ định, citation khác, synonym chưa chứng minh, formatting/
Unicode, source spans, ký hiệu, nhiều point và pipeline HTTP200→canonical fallback.
14 test omission fail trên v1 rồi green sau sửa; focused LLM/chat contracts431pass.
Review độc lập **0 Critical/0 Important/0 Minor**; không gọi provider trong review.

Full offline **2.485 passed, 2 skipped, 90 deselected** (540,30 giây); 8 test
JavaScript và Ruff/diff-check đạt. Còn một cảnh báo Starlette đã có từ trước.
SHA code đang dùng khớp code đã test; 15 file artifact L5/L6 cũ không đổi.
Trong 61 file runtime trước sửa, chỉ `output.py`/`prompts.py` đổi và thêm
`coverage.py`; canonical/retrieval/source/gold không đổi. Receipt chi tiết:
`backups/llm_qualitative_20261110/verification.json`.

Evidence mới trong `backups/llm_qualitative_20261110/` (ignored): red/green/focused/
offline XML/log, diagnostic before/after, hash15 file artifact cũ, runtime before/
after và archive61 file runtime v1. Hai file v1 đã tái dựng từ patch được kiểm
**byte-for-byte SHA trước sửa**; archive dùng để tái hiện validator cũ, không chép
đè runtime đang dùng. Không giả định archive là một commit Git mới.

Replay metric/review L5 cũ vẫn tái hiện bằng cache, không chạy validator mới để đổi
kết quả lịch sử. Runtime/prompt pins hiện đã thay đổi, nên **không dùng L5 cũ làm
bằng chứng nghiệm thu v2**. Readiness tiếp tục giữ off; cần run mới và review nội
dung trước L6. [Roadmap](RAG_PROGRESS_AND_NEXT_PLAN.md), [L5 cũ](RAG_LLM_L5_2026_11_10.md).
