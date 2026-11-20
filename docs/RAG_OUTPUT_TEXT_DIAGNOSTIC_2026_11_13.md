# HUS LLM — Diagnostic output_text offline

Ngày **13/11/2026**, nhánh `hus-llm-rag`, chỉ thay đổi local. Mục tiêu là phân biệt nhánh từ chối text trong những lần đo sau, giữ nguyên validator và fallback.

## Kết luận từ bằng chứng hiện có

Call sau thay key đã trả HTTP200 nhưng dừng ở `invalid_output/output_text/b001`, không dùng bản sinh. **Raw output không được lưu nên không xác định được nhánh cụ thể của call đó.** Bản vá này không khôi phục dữ liệu đã bỏ, không chứng minh model sai facts/thiếu ý, không sửa chất lượng model hoặc cấp nghiệm thu L5/L6. [Kết quả lịch sử](RAG_GOOGLE_DIAGNOSTIC_2026_11_13.md).

## Diagnostic mới

Giữ `code=invalid_output`, `stage=output_text`, `leaf_id` đã biết; thêm `text_issue` tùy chọn chỉ cho stage này:

| Nhãn | Nhánh kiểm đầu tiên không đạt |
| --- | --- |
| `blank` | Text rỗng sau trim; item chuỗi rỗng từ đầu vẫn bị schema chặn trước. |
| `raw_line_break` | Text sau trim còn ký tự xuống dòng. |
| `decoded_line_break` | Có xuống dòng sau double HTML decode và NFKC. |
| `structure` | Có marker bullet/số/heading ở đầu phần model viết. |
| `link_or_html` | Có mẫu link/HTML/citation inline bị cấm; nhãn gom các mẫu này. |
| `restored_length` | Text cộng prefix backend vượt trần 3.000 ký tự. |

Đây là **nhánh đầu tiên**, không phải danh sách mọi lỗi hoặc chứng minh entailment. Giữ đúng thứ tự cũ, trim/normalization/double decode, schema và các guard facts/đủ ý/symbol phía sau. Không xóa bullet model gửi để chấp nhận đầu ra; bố cục nguồn vẫn do backend phục hồi. Item quá dài từ đầu vẫn là `output_schema`.

Nhãn là enum cố định, không chứa đoạn text, URL, key/header hoặc ID riêng. Diagnostic cũ thiếu nhãn vẫn đọc được; `exclude_none=True` không thêm field null. Trace nội bộ của runner đo L5 tự truyền nhãn qua allowlist hiện có. Response người dùng chỉ giữ fallback_reason cũ; không thêm diagnostic vào `hus_answer` hoặc generation công khai. Không lưu raw output mới.

## Kiểm offline và giới hạn

**43 regression mới đạt**, gồm sáu nhánh, Unicode/entity, nhiều lỗi đồng thời, biên schema/prefix, trim ở hai đầu, legacy serialization, allowlist và privacy. TDD **29 fail/14 pass →43 pass**. Mock L5 giữ model/token và đúng canonical fallback F1/F3, F2 vẫn dùng presentation như cũ; replay mock tái hiện. Đây là test dữ liệu giả, không thành công model thật.

Đối chiếu validator gốc với bản có diagnostic trên **42 ca giả: 5 chấp nhận/37 từ chối**, toàn bộ quyết định và kết quả/error cũ giống nhau khi bỏ field nhãn mới. Đây là corpus hữu hạn, không chứng minh mọi đầu vào; code review riêng xác nhận các predicate/normalization/thứ tự được giữ. Review không có finding; Ruff phạm vi thay đổi đạt.

Bộ kiểm bị ảnh hưởng `tests/hus/llm` và `tests/hus/test_llm_rewrite_ui.py`: **607 pass**, không fail/skip, một warning Starlette/TestClient cũ, 168,02 giây. Audit **2.963/2.965 file bảo vệ nguyên SHA**; chỉ hai file runtime nêu dưới đổi, test mới thêm riêng. Cached replay A7R giữ điểm cũ; pins r5 lệch tổng năm runtime artifact, gồm ba của bản sửa baseline trước và hai của diagnostic này. [Receipt](../data/hus/qa/20261113/output_text_diagnostic_r1/report.json), [bindings](../data/hus/qa/20261113/output_text_diagnostic_r1/code_bindings.json), manifest `d63cd2c40c1923bfa3db9210bbb65ed02e71c29cfb665dd87764b31f10e5edbd`.

Chỉ sửa `app/hus/llm/diagnostics.py`, `output_v3.py` và thêm file regression. Không đổi prompt, retrieval, dữ liệu, test/gold/run/review cũ. Bộ HUS rộng hơn **2.442 pass/1 fail DEV-Q002/2 skip** là kết quả lượt sửa trước, không chạy lại hoặc gọi xanh trong lượt diagnostic này.

## Bước tiếp theo

**Không gọi Google trong lượt này; mọi budget đã hết.** L6 tiếp tục off. R5 đã stale sau sửa baseline; bản diagnostic làm pins thay đổi thêm. Khi có budget mới: fresh prepare/preflight trên code/config cuối, giữ A/retrieval/snapshot giữa A/B, ghi actual model/token/latency/used/fallback và review exact output, gồm cả fallback. Giữ cap1.024 output token/call, không retry/đổi model trong đo; bật mặc định cần gain/bảo toàn ý/facts/citation/latency thật và operator chấp nhận.

Quyết định: thực hiện phạm vi diagnostic đã chọn trong WIP local, giữ workspace bằng chứng vì không có Git checkpoint được phép. Lệnh kiểm đầu tiên dùng nhầm tên file UI và không thu test; đã sửa đường dẫn kiểm, không sửa product/test cho lỗi harness này. Review không phân xử nguyên nhân lịch sử, hành vi provider thật, chất lượng hoặc bật mặc định; các mục đó vẫn chưa nghiệm thu. Không có finding minor hoãn.
