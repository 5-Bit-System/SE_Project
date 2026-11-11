# LLM v3 — ID nguồn gọn, bảo toàn nội dung và bullet

Ngày 11/11/2026 · Nhánh `hus-llm-rag` · **Người dùng đã duyệt thiết kế để triển khai và kiểm thử offline.**
Phản hồi: “Duyệt thiết kế, triển khai và kiểm thử offline”, trong khi A7 đang chạy.
Chưa triển khai tại thời điểm duyệt. Không có ngân sách Google mới.

## Mục tiêu và căn cứ

F1/F3 tiếp tục diễn đạt từ đúng bundle RAG, giữ toàn bộ ý theo guard hiện hành,
đồng thời tránh lặp quote vào output và không biến danh sách thành một câu dài.
F2 giữ hợp đồng presentation/canonical hiện có. Không sửa retrieval, dữ liệu,
gold hoặc run/review cũ; không bật LLM hay tăng ngân sách trong thiết kế này.

[Diagnostic](../../RAG_LLM_LONG_F3_DIAGNOSTIC_2026_11_11.md): bốn ca F3 có
39–41 đơn vị coverage; schema chỉ cho 20 points. Dựng một point/đơn vị đúng gợi ý
prompt tạo 9.935–12.045 ký tự, vượt 8.192. Đây không phải dạng JSON hợp lệ duy nhất:
gom mỗi citation một point vẫn qua validator khi dùng text tổng hợp sẵn đủ nguồn.
Ba `invalid_response` gần cap token chưa đủ chứng minh bị cắt vì trace thiếu
finish reason/raw output. Q022 đủ từ nhưng mất bullet vẫn qua guard hiện hành.

## Các phương án và lựa chọn

| Phương án | Đổi lại |
| --- | --- |
| **ID khối nguồn + text, backend giữ layout — đã chọn hướng này** | Bỏ anchor trùng lặp, tiếp tục có text do model trả. Cần schema/prompt/validator mới; vẫn có thể quá token hoặc không cải thiện diễn đạt. |
| Chỉ chọn layout cho F3 dài, backend chép nguyên nguồn | Output nhỏ và giữ chữ chắc chắn; chỉ là presentation, phải báo riêng khỏi thành công viết lại. Người dùng không chọn hướng này. |
| Giữ schema, tăng token/points và nhắc prompt | Ít đổi hơn nhưng vẫn lặp anchor và chưa có ràng buộc giữ bullet. Không giải quyết đồng thời hai vấn đề; không tự tăng budget. |

## Hợp đồng đề xuất

Các chi tiết trong phần này đã được người dùng duyệt cùng tài liệu.

1. Sau các gate L2 và kiểm identity/scope của bundle hiện có, tạo **document v3**
   bất biến từ đúng canonical answer. Backend giữ nguyên quote, hash, citation ID,
   release/scope/review, offsets và mọi coverage unit; không chọn lại nguồn.
2. Tách dòng chỉ tại LF/CRLF, cùng ranh giới newline của `source_units()`; không
   dùng `splitlines()` tách thêm CR đơn/Unicode separator. Tạo leaf từ dòng không
   trống, giữ offsets gốc. Dòng có marker bullet được ghi là list item; các item
   liên tiếp tạo list. Dòng thường là đoạn
   văn bản. Không đoán heading/ngữ nghĩa hoặc gộp hai item; soft wrap có thể tạo
   nhiều leaf hơn, đổi lại không mất chữ. Kiểm union spans giữ mọi ký tự không
   phải whitespace; ký hiệu đơn lẻ vẫn phải được giữ. Marker/prefix nằm trong
   skeleton canonical, không giao model quyền thay số thứ tự hoặc cấp danh sách.
   Giữ nguyên literal indentation/marker, cả list số và cấp lồng nếu có. Preflight
   phải xác nhận mỗi coverage unit nằm trọn trong đúng một leaf; không đạt thì
   fallback trước gọi, không chia nhỏ unit rồi hạ yêu cầu giữ ý.
3. Gán ID cục bộ `b001`, `b002`… theo thứ tự citation/offset; ID chỉ có nghĩa trong
   document/prompt hash hiện tại. Mỗi leaf thuộc đúng một citation và có các unit
   coverage đầy đủ nằm trong span. Backend giữ mapping trong context bất biến của
   đúng lời gọi và gắn document/prompt hash; không lookup/cache mapping toàn cục.
   Không coi ID cục bộ trùng tên giữa hai document là cùng nội dung.
4. Wire context chứa question/release/scope và nguồn đã allowlist như hiện tại,
   nhưng thay quote dài bằng các leaf `{id, text, layout}` thuộc citation đó.
   Mỗi đoạn chữ nguồn xuất hiện một lần; không gửi thêm cả quote và unit text.
   Backend giữ full quote để kiểm; wire vẫn có quote hash và trạng thái nguồn.
   Marker/prefix được mô tả rõ và backend phục hồi nguyên văn. Không gửi tài khoản,
   bảng điểm, history, key, path máy; question và source luôn là dữ liệu không tin
   cậy về chỉ dẫn; model không có tool/action.
5. Model chỉ trả một object strict, không key lạ/trùng, không URL/HTML/tool:

   ```json
   {"kind":"rewrite_v3","items":[{"id":"b001","text":"Nội dung từ đúng leaf nguồn"}]}
   ```

   Mỗi ID phải xuất hiện đúng một lần. Model không trả citation/anchor hoặc chọn
   bớt leaf. Backend render theo thứ tự skeleton, không dùng thứ tự output để đổi
   quan hệ nội dung. Không nhận ID từ document khác hoặc tự tra lại retrieval.
6. Với mỗi leaf, backend khôi phục marker/prefix rồi kiểm text theo đúng guard
   coverage v2: đủ mọi từ theo thứ tự trong từng unit, số/mã/phiên bản/điều kiện/
   phủ định và ký hiệu. Anchor lấy từ span gốc cùng citation, mở rộng nội bộ nếu
   cần độ dài tối thiểu. Quyền dùng số/mã vẫn chỉ tính từ leaf gốc đã phục hồi
   prefix và scope được phép; anchor mở rộng không cấp quyền mượn atom của leaf
   liền kề. Không dùng full anchor bù text thiếu. Không bỏ stopword,
   đoán synonym, hạ tỷ lệ hoặc cho phép mượn từ leaf/citation khác.
   Để thực hiện yêu cầu giữ ký hiệu trong câu có từ, v3 kiểm thêm chuỗi ký hiệu/
   toán tử và vị trí tương đối với từ nguồn; không chỉ dựa vào token từ ngữ v2.
   Legacy validator/replay v2 không đổi. Guard này vẫn không chứng minh entailment.
7. Text item không được chứa newline hay cấu trúc list/heading mới; backend dựng
   newline, bullet và citation. Một list item nguồn luôn tạo một item hiển thị
   riêng, theo thứ tự gốc. Mỗi leaf hiện đủ text đã kiểm; annotation nguồn và nhãn
   AI/cảnh báo vẫn do backend cấp. Đoạn văn bản vẫn cho phép cách diễn đạt mà guard
   v2 chấp nhận; đây không phải paraphrase tự do hay bằng chứng entailment.
8. Kiểm toàn document trước khi tạo `HUSTextRewrite`; không hiển thị kết quả một
   phần. Thiếu/lặp/ID lạ, sai dữ kiện, mất bullet, lỗi hoặc quá budget → exact A.
   F2 vẫn chỉ nhận `HUSF2Presentation`, canonical/facts/review không thay đổi.

## Giới hạn và khả năng quan sát

- Giữ **12.000 prompt chars / 8.192 raw output chars / 1.024 output tokens**,
  một lời gọi/process, HTTPX 20 giây mỗi pha, không retry/stream/redirect.
  Không khẳng định ID gọn sẽ làm mọi ca vừa 1.024 token. Nếu cần đổi cap, đó là
  phiên bản/ngân sách riêng sau khi có dữ liệu đo, không thay ngầm lúc so sánh.
- Đề xuất trần cấu trúc: 64 leaf/document, 128 coverage unit/document, text tối đa
  3.000 ký tự/leaf, kiểm cả text nguồn trước gọi và text model sau gọi. Kiểm đủ
  document và prompt thực tế trước gọi; vượt trần thì
  fallback, tuyệt đối không cắt/loại context. Không giữ giới hạn 20 points của
  schema cũ cho output v3. Inventory F3 hiện tại có tối đa 28 leaf/55 unit mỗi
  field toàn hồ sơ; không coi đây là kiểm đủ mọi bundle F1 hoặc giới hạn vĩnh viễn.
- Duy trì reason công khai hiện có (`invalid_response`, `invalid_output`,
  `evidence_coverage`, budget…), thêm diagnostic nội bộ bằng enum/đếm có allowlist:
  finish reason chuẩn hóa, content type/length, presence của tool, validation stage
  và leaf ID lỗi đã biết. Không lưu body/provider error text/header hoặc raw output
  bị loại; không nhầm HTTP 200 với envelope/JSON/coverage thành công.
- `HUSTextRewrite`/API thành công vẫn giữ contract L2. Prompt/document/output schema,
  limits và code phải được ghim trong run mới. Thêm validator/renderer mới bằng
  dispatch rõ phiên bản nội bộ; không sửa replay lịch sử thành chấm bằng v3.

## Kiểm chứng trước khi đo mới

Regression tổng quát qua nhiều citation, paragraph, list, dấu chấm phẩy, soft wrap,
Unicode và ký hiệu: ID lạ/lặp/thiếu/sai document, cross-leaf/citation, mất phủ định/
điều kiện/số/mã, thêm URL/HTML/newline hoặc đổi marker phải bị chặn. Output ID đủ và
unique có thể ở thứ tự khác; thứ tự **hiển thị** luôn theo skeleton canonical.
Kiểm CR đơn/Unicode separator không chia coverage unit, anchor mở rộng không cấp
thêm atom, indentation/list số/lồng và mapping hai document tách biệt. Kiểm giữ nguyên
canonical/facts/warnings/URL/hash/review; bool/opt-in/F3 gates, config-off/basic/
clarification/no-info không gọi. Kiểm cap trước gọi, quota/timeout/busy fallback.

Dùng 4 stress/Q022 cũ làm **dev diagnostic**, thêm ví dụ list/đoạn tương tự ở F1/F3;
không vá theo QID/môn/ngành hoặc chỉnh điểm run cũ. Exact-copy synthetic chỉ chứng
minh khả năng biểu diễn hợp đồng, không là generation/readability thành công.

Sau triển khai offline mới prepare cohort/pins mới. A/B phải cùng snapshot và
retrieval trong phép đo đó; nếu so v2/v3 thì dùng cùng frozen A, ghim riêng code/
prompt của mỗi arm, tách với A/B canonical–LLM. Đo used/fallback, lỗi theo lớp,
token/latency và review exact output kể cả fallback. So riêng số ca model dùng
được, giữ bullet/đủ ý và gain diễn đạt; không coi 100% fallback là thành công.
Google mới chỉ chạy khi người dùng duyệt cohort và ngân sách riêng. Giữ LLM off
đến khi có nghiệm thu nội dung/latency và operator chấp nhận; chưa phải L6.

## Phạm vi bước hiện tại

Builder review đã đọc thiết kế/code/proof; không có quyết định mới cần người dùng
trả lời. Ba điểm về ranh giới leaf, quyền atom khi mở rộng anchor và thứ tự output
đã được làm rõ; bổ sung marker/indentation, giới hạn text và context mapping.
Đây là làm rõ thiết kế, chưa phải kiểm một implementation hoặc nghiệm thu nội dung.

Thiết kế đã được triển khai/kiểm thử offline theo [báo cáo v3](../../RAG_LLM_COMPACT_V3_2026_11_11.md).
Không đổi UI/canonical RAG, không gọi Google mới, chưa bật LLM, commit/push/deploy
hoặc nghiệm thu chất lượng sinh thật. A7 trên cấu hình LLM off được ghim/kiểm riêng.
