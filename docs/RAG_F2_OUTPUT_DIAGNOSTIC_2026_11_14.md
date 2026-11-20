# F2 fallback — đã bổ sung diagnostic offline

**Đã sửa khoảng trống diagnostic; chưa xác định được nhánh lỗi của call cũ.**
Không gọi Google, không sửa dữ kiện/schema/prompt hoặc nới validator.

Ca `SV30-003` hỏi tín chỉ MAT2300: Google trảHTTP200, finish=`stop`,695 ký tự,
255 output token; sau đó pipeline trả `invalid_output`. Metadata này cho thấy
không phải lỗi kết nối hoặc vượt trần output. Raw output không được lưu và trace
không có nhãn nhánh validation, nên **chưa thể kết luận lỗi JSON, style, khóa nào
hoặc model đã thay dữ kiện**. Giá trị hiển thị vẫn là **4 tín chỉ** từ RAG.

Đã xác định trong code: F2 trước đây gộp lỗi parser/schema/result thành
`invalid_output`, không gắn diagnostic. Các kiểm danh sách khóa/nguồn cũng thiếu
nhãn phân biệt. Guard chống echo key ở adapter chưa có nhãn F2 riêng.

| Stage mới trong trace nội bộ | `facts_issue` cố định |
| --- | --- |
| `output_budget` | `budget` |
| `output_json` | `json` (gồm JSON sai, fence, key JSON trùng, hằng không hữu hạn) |
| `output_schema` | `kind`, `style`, `schema`, `presentation`, `credential_echo` |
| `output_coverage` | `duplicate_fact_keys`, `duplicate_citation_ids`, `fact_keys`, `citation_ids` |

Đây là nhãn allowlist, không chứa text/giá trị/key lạ của model. Nhãn chỉ hợp lệ ở
stage tương ứng. Mã lỗi và response công khai giữ nguyên; backend tiếp tục giữ
facts, citation và bản trích nguồn khi fallback. Diagnostic cũ không tự được bổ
sung nhãn mới.

Kiểm chứng:

- TDD ban đầu18fail/8pass, sau sửa26pass; thêm kiểm result, ca MAT2300 từ bản lưu và model echo: **29 regression cuối đạt**.
- Nhóm LLM **668pass**, một warning Starlette cũ; lượt này thu test trước khi thêm tham số model-echo cuối, sau đó nhóm29 đã chạy lại. Không cộng các nhóm hoặc gọi là full-repo.
- **61 đầu ra giả** đối chiếu với validator trước sửa:4 chấp nhận/57 từ chối, toàn bộ quyết định và mã lỗi giữ nguyên.
- Test pipeline/mock trace nhận nhãn; lỗi schema giả lập trên ca MAT2300 giữ nguyên4 tín chỉ/citation/reply. Đây không phải tái tạo output cũ.
- Ruff4 file đạt; reviewer code ở context riêng không có finding đáng kể. Đã bổ sung test model-echo từ góp ý nhỏ; không phải review nội dung học thuật.

**3.069 file cũ nguyên SHA**, chỉ ba file runtime dự kiến đổi và thêm test mới.
Run/gold/review/CSV cũ giữ nguyên:23 dùng Gemini/1 fallback/6 control. Pins lượt
đo cũ nay lệch sau bản sửa diagnostic; không sửa pins hoặc chấm lại.

Nếu muốn biết nhánh lỗi khi gọi model thật, cần budget mới và lượt kiểm mới trên
code/prompt được ghim, chỉ lưu nhãn an toàn. Ngay cả khi call mới thành công hoặc
có nhãn khác, vẫn không chứng minh nguyên nhân chính xác của call cũ. Giữ LLM
mặc định tắt; không đổi key/billing.

[Receipt](../data/hus/qa/20261114/f2_output_diagnostic_r1/report.json).
