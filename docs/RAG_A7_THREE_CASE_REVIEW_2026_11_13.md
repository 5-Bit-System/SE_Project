# A7 — review ba ca trước khi chọn sửa

**Cập nhật sau review:** đã triển khai sửa chung CLC/assessment và chốt chính sách
nguồn cho cohort sau; xem [báo cáo triển khai](RAG_SCOPE_ASSESSMENT_PORTABLE_2026_11_13.md).
Phần dưới ghi trạng thái tại thời điểm review; run/gold/review và điểm cũ giữ nguyên.

Ngày **13/11/2026**, nhánh `hus-llm-rag`, nền `f61b0fd` + WIP hiện có.
Đã review Q002/Q003/Q011 từ exact response, trace, nguồn local và code hợp đồng.
**Chưa sửa baseline hoặc chấm lại A7**: giữ Routed Recall@5 **24/24**, đủ ý
**34/36**, controls **11/12**. Review là AI, không blind/độc lập, human0.

| Ca | Kết luận review | Hướng xử lý đề xuất |
| --- | --- | --- |
| A7F-Q002 | Lỗi guard/scope alias CLC: target đúng ở rank1 nhưng `clc` bị đòi trong body. | Chuẩn hóa alias hệ thành ràng buộc scope có kiểm chứng; nội dung nghề nghiệp vẫn phải có trong body. |
| A7F-Q003 | Nguồn DOCX2023 hỗ trợ câu trả lời thực; chưa chứng minh đủ danh sách web đã ghim. Câu hỏi không chọn edition nguồn F1. | Giữ completeness fail cũ; chốt cách ghim nguồn hoặc xử lý nguồn thay thế trước cohort mới, không sửa ranking để ép target. |
| A7F-Q011 | Classifier nhận assessment, nhưng guard nhiều field đếm thêm “nội dung”. Cụm này có thể bổ nghĩa cho gợi ý đánh giá. | Đề xuất nhận một ý trong cấu trúc bổ nghĩa rõ; giữ clarification cho hai yêu cầu độc lập. Chưa triển khai quy tắc. |

## Q002 — đúng bằng chứng, vướng alias hệ

Câu đã đo: “Cơ hội nghề nghiệp ngành Máy tính và Khoa học thông tin CLC với
vai trò tư vấn, phân tích và thiết kế dự án?”

Target `291b6949cf13e7e60e54762b0d09ae77` ở **rank1**, thuộc
`computer_science / careers / high_quality / unknown`. Trích nguồn:

> Đảm nhiệm các vai trò tư vấn, quản lí, phân tích, thiết kế, lập trình cho các dự án công nghệ thông tin.

Title nguồn là “Máy tính và Khoa học thông tin CLC”, scope đã ghi
`high_quality`; body không có chữ CLC. Các token riêng của guard là
`clc / thiet / tich`; target chỉ thiếu `clc`. Replay guard trên top5 đã lưu
trả rỗng. Bỏ chữ CLC trong **probe chẩn đoán riêng** thì guard giữ target;
đây không phải sửa câu hỏi/gold của phép đo.

`effective_request.program_variant` và filter retrieval đều null: alias CLC
trong câu tự nhiên chưa thành bộ lọc hệ. Top5 còn có nguồn standard. Vì vậy
**không nên chỉ bỏ `clc` khỏi tập từ cần kiểm tra**: cách đó có thể chọn sai hệ.
Probe đổi thành “hệ chất lượng cao” chọn nguồn2019 khác, cũng cho thấy đổi chữ
không đảm bảo giữ nguyên nguồn/edition.

Hướng sửa chung: hiểu CLC/hệ chất lượng cao theo cùng quy tắc scope; chỉ cho
metadata đã xác định hệ đáp ứng qualifier đó, vẫn kiểm nội dung factual trong
body. `unknown` không thành `high_quality`; title đơn lẻ không thay metadata
hoặc bằng chứng. Ràng buộc hệ/edition mâu thuẫn phải được xử lý rõ, không tự
bỏ qualifier. Không sửa source, ranking hay ghim chunk ID trong runtime.

## Q003 — nguồn thay thế không đồng nghĩa cùng danh sách

Câu đã đo: “Học tiếp ngành KHMTTT ở bậc Thạc sĩ, Tiến sĩ có những lĩnh vực nào
theo nguồn?” Raw request có selector `QD3568-2023`, nhưng hợp đồng chat hiện có
bỏ decision version F2/F3 khi route F1. **F1 source edition không tự ghim theo
selector này**; effective version null, program variant null.

| Bằng chứng | Scope và danh sách |
| --- | --- |
| Gold web, target rank2 `e29e0cbb74eb7a68f3992ec91f5dd4e9` | Edition/hệ unknown; Công nghệ thông tin, Cơ sở toán học cho Tin học, Khoa học dữ liệu. |
| Output DOCX, rank1 `e5a82ded76438ecd8803b9c5e5d2e9c1` | Edition2023/hệ standard; Khoa học Máy tính và Thông tin, Khoa học dữ liệu, Trí tuệ nhân tạo, Toán ứng dụng và lĩnh vực liên quan. |

Cả hai nguồn đều giữ điều kiện **đủ điều kiện và có nhu cầu học tiếp**; không
nguồn nào tự xác nhận một sinh viên đủ điều kiện tuyển sinh sau đại học.
Đã kiểm archive hash/locator của hai đoạn và đọc đoạn tương ứng trong binary
DOCX local SHA256 `4838b51f795e858c0672883ff0994a82b8be70e379260189c034e166a0f63517`.
Text đoạn trả lời khớp DOCX sau chuẩn hóa khoảng trắng; không xác minh toàn tài
liệu hoặc hiệu lực hiện hành, không nâng review/academic_verified của nguồn.

Guard chấp nhận từng nguồn này khi xét riêng; đảo thứ tự hai cached hit làm
guard chọn web thay DOCX. Đây là việc chọn nhóm nguồn được hỗ trợ theo thứ tự
retrieval, **không phải bằng chứng DOCX mới nhất/ưu tiên học vụ**. Không tìm thấy
lý do để sửa ranking chỉ nhằm đưa gold lên đầu.

Kết luận: entailment pass theo DOCX vẫn hợp lý; completeness fail so với target
web giữ nguyên. Không coi “Toán ứng dụng” tương đương “Cơ sở toán học cho Tin
học”, không gán hệ unknown thành chuẩn hoặc gộp hai edition thành một danh sách.

Trước cohort sau, nên phân biệt:

- Câu yêu cầu một nguồn/edition/hệ: ghi rõ ngay trong câu hỏi hoặc scope hợp lệ,
  đóng băng target tương ứng trước inference; thiếu scope thì làm rõ.
- Câu rộng không chọn nguồn: công bố trước cách đánh giá nguồn thay thế và đủ ý
  theo yêu cầu; nguồn được chọn phải có citation/scope/cảnh báo, giữ điều kiện.
  Các danh sách không tương đương không được thay nhau bằng suy luận từ tên gọi.

**Còn mở:** người review độc lập/chuyên môn cần phân xử nếu muốn công nhận ánh
xạ các lĩnh vực hoặc dùng một danh sách để xác nhận bao phủ danh sách khác.
Trong review này không có xác nhận đó; không cần giả định tương đương để sửa
hai lỗi kỹ thuật còn lại. Không sửa gold/review/denominator của run hiện tại.

## Q011 — một ý đánh giá hay hai loại thông tin?

Câu đã đo: “Gợi ý đánh giá MAT3557 theo phần tham khảo AI đã lưu có nội dung gì?”
Classifier trả `f3 / suggested_assessment`; `requested_course_fields` trả
`content + suggested_assessment`. Guard nhiều field chạy trước retrieval, vì
vậy response là `needs_clarification`, **0 search**, không có facts/citation.
Gold là `no_information`; mismatch1/12 được giữ nguyên.

Đề xuất đọc câu này là một ý: hỏi nội dung **của phần gợi ý đánh giá**, không
hỏi riêng nội dung môn học. Cụm “nội dung” có thể là bổ nghĩa, nên không nên
áp dụng ưu tiên assessment toàn cục để sửa. Ví dụ sau phải còn phân biệt:

| Cách hỏi | Hợp đồng đề xuất cho lượt sửa sau |
| --- | --- |
| “Gợi ý đánh giá MAT3557 … có nội dung gì?”; “Nội dung của phần gợi ý đánh giá …” | Một field assessment; nếu không có nguồn thì no_information. |
| “Nội dung MAT3557 và gợi ý đánh giá MAT3557?” | Hai yêu cầu độc lập → needs_clarification, không trả riêng một ý. |
| “MAT3557 có bao nhiêu tín chỉ và thi thế nào?” | Hai field → needs_clarification. |
| “Không hỏi nội dung …, chỉ hỏi gợi ý đánh giá.” | Chỉ assessment; không khôi phục field đã phủ định. |
| “Nội dung MAT3557?” | Chỉ content; vẫn kiểm opt-in AI và scope môn. |
| “Tỷ lệ thi cuối kỳ chính thức MAT3557 …?” | Yêu cầu chính thức; không dùng AI để điền quy định thiếu. |

V4 chỉ có **1.463 content +290 objectives**, không có assessment chunk.
Record MAT3557/KHMTTT có `official_assessment=null`, profile không có assessment,
vẫn generated/needs_review/academic_verified=false. Do đó nhận đúng một ý
assessment cũng không tạo được câu trả lời có bằng chứng trong snapshot này.
Không thêm assessment hoặc sinh dữ liệu mới để làm control thành answered.

## Ranh giới regression cần có khi triển khai

| Nhóm | Positive cần phủ | Negative/ràng buộc phải giữ |
| --- | --- | --- |
| Scope hệ F1 | CLC và tên đầy đủ, cách viết/câu tương tự; qualifier được metadata phù hợp đáp ứng. | Cùng body nhưng standard/unknown; thiếu hệ được hỏi; hệ và edition xung đột; factual topic/số không có trong body; không mượn nguồn khác. |
| Nguồn thay thế F1 | Câu có edition chọn đúng scope; câu rộng hiển thị nguồn/điều kiện của nguồn đã chọn. | Không gộp scope/edition, không suy tương đương danh sách, không bỏ điều kiện học tiếp; unknown không thành standard. |
| Bổ nghĩa assessment | Cấu trúc hỏi nội dung của gợi ý đánh giá và các cách hỏi một ý tương tự. | Hai ý nối “và”/mệnh đề độc lập; tín chỉ + thi; phủ định; opt-in tắt; môn/ngành sai; yêu cầu tỷ lệ chính thức; thiếu assessment vẫn no_information. |

Đây là **ma trận đề xuất**, chưa phải test regression mới đã pass hoặc sửa
runtime. Khi triển khai, dùng các ca này làm dev cùng câu tương tự/negative;
nếu dùng cohort A7 này tuning thì giữ nó làm dev, freeze bộ khác sau sửa.
Không sửa QID đặc biệt, gold/run/review cũ hoặc giảm tiêu chí để đổi điểm.

## Kiểm chứng và bước tiếp theo

Đã chạy **23 probe pure guard/router** từ cached hit/câu diagnostic, kiểm10
source hash/locator và1 đoạn DOCX binary; không gọi lại API/answerer/search/model.
Cached measurement/review replay tái hiện; pins khớp. Đây không phải A7 mới hoặc
nghiệm thu học thuật. **2.722 file cũ đã ghim giữ SHA**; không đổi runtime/test/
evaluator/data, CURRENTv4/lexical/LLMoff. Không gọi Google, đọc/chỉnh key/env,
commit/push/deploy. L5 budget vẫn đã hết và L6 vẫn keep_disabled.

1. Ưu tiên sửa chung **scope alias CLC và cấu trúc một ý assessment**, kèm positive/
   negative theo ma trận; chưa triển khai ở bước review này.
2. Chốt quy tắc nguồn thay thế/edition cho cohort tiếp theo; chỉ cần review
   chuyên môn nếu muốn xác nhận các danh sách học thuật tương đương.
3. Sau sửa và regression, freeze A7 khác ≥48 câu/12 mỗi ngành, ghim nguồn/gold/
   code/config/exposure/reviewer trước inference. Đánh giá Routed Recall@5 gồm
   no-call cùng facts/citation/đủ ý/controls; không lấy AI review làm độc lập.

[Diagnostic và các binding](../data/hus/qa/20261113/a7_three_case_review_r1/diagnostics.json),
[kết luận review](../data/hus/qa/20261113/a7_three_case_review_r1/review.json),
[receipt bảo toàn](../data/hus/qa/20261113/a7_three_case_review_r1/report.json),
[run/review A7 lịch sử](RAG_A7_AFTER_FOLLOWUP_2026_11_12.md).
