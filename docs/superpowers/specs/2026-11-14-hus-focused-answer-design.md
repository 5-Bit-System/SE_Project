# Trả lời theo ý hỏi: nguồn rõ ràng và đủ ý trong context đã chọn

Ngày14/11/2026 · Cập nhật15/11/2026 · Nhánh `hus-llm-rag` · **Đã triển khai lựa chọn
`focused`, kiểm offline; chưa nghiệm thu nội dung/Gemini thật.** Người dùng chọn
triển khai thiết kế ở mục3. Mặc định vẫn legacy/v3; chỉ dùng đường mới khi chọn
`--answer-policy focused`. [Triển khai/giới hạn](../../RAG_FOCUSED_ANSWER_2026_11_15.md).

## Mục tiêu và giới hạn

Chatbot trả đúng ý hỏi, gọn hơn, vẫn giữ facts, điều kiện/phủ định, source identity
và quyền F3. Dùng snapshot/index hiện có, không thay data hoặc dùng target/gold
để chọn nguồn. F2 giữ backend-owned facts/presentation, gồm đếm danh mục.

Giữ Google trực tiếp,1.024 output token/call,12.000 prompt chars/8.192 raw output
chars, một lời gọi đồng thời/process, không retry/đổi model. Bất kỳ call mới nào
cho thiết kế này cần budget riêng;1 call chưa dùng của cohort F2 không chuyển sang.
Auto profile chỉ dùng offline sau429; lỗi provider/output khác báo lỗi. Không
đưa lời khuyên học vụ/đăng ký, kiến thức ngoài bundle hoặc ví dụ mới vào F1/F2.

## Hai hướng thực hiện

| Hướng | Đổi lại |
| --- | --- |
| **Context đúng ý + diễn đạt có ràng buộc — đề xuất cho bước đầu** |Backend chọn đủ đoạn cần trả lời trước gọi model; coverage nghiêm trên các đoạn này, giữ nguyên điều kiện/facts/bullet. Trả gọn hơn mà chưa cần nới lexical validator sang paraphrase tự do. |
| Diễn đạt tự do hơn, kiểm facts/anchors và đánh giá ngữ nghĩa |Linh hoạt ngôn ngữ hơn nhưng kiểm số/ID/anchor không chứng minh đúng/đủ ý định tính. Cần thiết kế kiểm ngữ nghĩa và review riêng; không thay mọi guard bằng similarity hoặc tự khai `covered=true`. |

Hướng đầu giải quyết phạm vi trả lời trước. **Không hứa đã có paraphrase tự do
hoặc suy luận ngoài nguồn.** Giữ v3 để đối chiếu/rollback; các run v2/v3 vẫn đọc
bằng validator lịch sử, không chấm lại bằng protocol mới.

## 1. Hiểu yêu cầu và giải quyết nguồn

- Bounded grammar cho tổng quan006: tiêu thụ cả cụm yêu cầu, không bỏ từ domain
  toàn cục. Giữ điều kiện, phủ định, năm/hệ và topic chưa có nguồn.
- Với019, nhận diện ứng viên quá khớp từ cách hỏi đời thường qua alias chủ đề
  có phiên bản, gắn đúng môn/field và đoạn giải thích đã review. Không quyết định
  chỉ từ title hoặc một từ “kém”; thiếu dấu hiệu/nguồn thì làm rõ. Câu phủ định
  (“không ghi nhớ mà vẫn kém”), câu hỏi nguyên nhân khác và claim “luôn luôn”
  không được nhập chung thành cùng yêu cầu. Giữ câu gốc, không sửa nguồn để khớp.
- Tách yêu cầu thành các ý, ví dụ009 có đối tượng và kế thừa;014 có câu hỏi nghiên
  cứu và phạm vi. Tên môn chỉ là locator khi khớp trọn tên; không neutral hóa từ
  thành phần trùng domain như “đối tượng” trong mọi câu.
- Chốt source scope trước sinh theo [review nguồn](../../RAG_GUARD_EDITION_REVIEW_2026_11_14.md):
  F1 chưa ghim mà có nhiều edition/hệ/source family thì hỏi chọn. Không suy F1
  là hệ chuẩn theo F2 hoặc ưu tiên2023/2015 vì ranking. Không có context đủ một
  scope thì không gọi generation để bù nguồn.

## 2. Tạo gói bằng chứng tập trung trước gọi

Backend tạo một `AnswerPlan` bất biến từ request đã kiểm và các đoạn đúng scope:

```json
{
  "schema_version": "hus-focused-evidence-v1",
  "question": "Câu gốc",
  "release": {"id": "...", "sha256": "..."},
  "scope": {"dataset": "f3", "major": "...", "version": "...", "course_code": "...", "program_variant": "...", "source_id": "..."},
  "aspects": [{"id": "a001", "required_unit_ids": ["u001"]}],
  "units": [{"id": "u001", "citation_id": "1", "quote": "Trọn đoạn liên quan, gồm điều kiện.", "quote_sha256": "..."}]
}
```

- `required_unit_ids` do backend lập trước model, không lấy từ gold hoặc lời
  tự khai của model. Mỗi ý được hỏi phải có mô tả trực tiếp, không chỉ danh mục
  title. Không lấy nhiều unit khớp từng từ rời rạc làm đủ ý.
- Trước hết chọn **trọn đoạn mô tả** liên quan. Giữ câu điều kiện/ngoại lệ/giới
  hạn gắn với kết luận, kể cả ở câu tiếp theo. Nếu không biết đóng context an
  toàn, dùng trọn chunk hoặc làm rõ; không cắt giữa điều kiện và kết luận.
- 009: ứng viên là mô tả đối tượng/lớp và mô tả kế thừa/khả năng thay thế; hợp
  thành chỉ bắt buộc khi câu hỏi thực sự yêu cầu.014: ứng viên là trọn mô tả
  câu hỏi/phạm vi/khái niệm; không tự kèm ba unit khác. Đây là nhận xét nội dung,
  không mã hóa chunk ID/QID hay ép thứ hạng vào thuật toán.
- Ví dụ/keyword list không mặc định phải trả khi chỉ hỏi định nghĩa. Nếu người
  dùng hỏi ví dụ hoặc liệt kê đầy đủ thì phải đưa chúng vào phần bắt buộc. Câu
  hỏi “toàn bộ nội dung/mục tiêu” vẫn cần inventory đầy đủ; không rút gọn để vừa cap.
- Backend giữ citation/source quote gốc, offset thật/hash/scope/review và map
  span nội bộ. Không gửi path/key/history/tài khoản/bảng điểm. Nguồn và câu hỏi
  là dữ liệu không đáng tin về chỉ dẫn; model không có tool/action.

## 3. Prompt/output mới — tên dự kiến `focused_rewrite_v1`

Prompt yêu cầu chỉ trả các ý trong `AnswerPlan`, không bổ sung nội dung từ unit
khác, không lặp tổng quan khi chỉ hỏi một chủ đề. Mỗi ý được giữ đủ giải thích,
điều kiện và cảnh báo; “gọn” không cho phép bỏ phần bắt buộc.

```json
{"kind":"focused_rewrite_v1","items":[{"unit_id":"u001","text":"Nội dung đã kiểm cho đơn vị này"}]}
```

Đầu ra không tự chọn lại source scope, tạo URL/citation, tự đặt danh sách facts
hoặc bỏ unit. Backend giữ thứ tự/bullet và gắn citation. IDs cục bộ chỉ hợp lệ
trong đúng plan/prompt hash. Model có thể dùng câu nối trung tính; giai đoạn đầu
vẫn giữ từ/nghĩa nguồn theo guard nghiêm, chưa cho synonym/reorder tự do.

## 4. Validator và đủ ý

1. Kiểm JSON strict/duplicate/extra/unknown IDs/budgets như hiện có.
2. Mọi unit bắt buộc của **mọi ý hỏi** phải hiện đúng một lần; không nhận text
   có nhãn coverage nhưng thiếu nội dung. IDs của unit ngoài plan bị từ chối.
3. Kiểm số/mã/năm/phiên bản và toán tử theo đúng unit/scope; không mượn atom
   từ unit khác. Giữ unknown/conflict, phủ định, điều kiện, modality “có thể”.
   Không chỉ kiểm các từ nguồn còn đủ: còn phải chặn thêm/đổi vị trí phủ định,
   điều kiện hoặc các khẳng định “luôn/tất cả/chắc chắn”. Phần nối trung tính
   dùng khuôn backend xác định ở ranh giới unit; không cho tùy ý chèn vào giữa
   câu để đổi quan hệ. Test đủ từ nhưng thêm “không” vẫn phải bị từ chối.
4. Coverage lexical/symbols vẫn áp dụng lên **toàn bộ đoạn bắt buộc đã chọn**,
   không hạ threshold hoặc bỏ từ khó để qua. Trước đó phải review việc chọn
   plan: nếu plan thiếu ý, validator không cứu được. Schema đúng không là entailment.
5. Dựng layout/citation bằng backend sau khi toàn output đạt; không hiển thị
   partial output bị loại. Không đổi `hus_answer`, facts, quote/hash/URL/review
   của context đã trao cho adapter; mọi lựa chọn evidence mới xảy ra trước đó.
6. Chỉ trả typed `HUSTextRewrite` sau kiểm; F2 tiếp tục typed `HUSF2Presentation`
   và schema `kind=facts` riêng. Không dùng protocol F1/F3 để cho model viết số F2.

Đổi **phần được hỏi** khác với đổi tiêu chí đủ ý: phải ghim plan/ý bắt buộc trước
generation và review độc lập; không chọn plan theo output đã sinh hoặc cắt ý sau
inference để đổi kết quả. Nếu quá ngân sách, không bớt unit bắt buộc; auto báo lỗi
ngân sách theo policy hiện tại, chỉ quota429 mới đi đường offline.

## 5. Triển khai/kiểm chứng dự kiến

1. Regression trước cho006 grammar,019 alias và negative,009 hai ý,014 scope
   gọn. Thêm câu tương tự/đổi mã/ngành và source thiếu định nghĩa/điều kiện.
2. Source-policy tests độc lập thứ tự top5: nhiều edition/hệ cần chọn; explicit
   selector đúng scope; source unknown không thành chuẩn, không borrow2015/2023.
3. Builder/validator mock: đủ unit/thiếu unit/citation lạ/đổi số/phủ định/toán tử,
   optional example vs hỏi ví dụ, “toàn bộ” và budget; vẫn giữ gate F3/API lỗi429.
4. Protocol mới opt-in ở backend hoặc adapter riêng, chưa thay default v3 khi
   chưa kiểm. So cùng snapshot/retrieval với context/plan/prompt/code được ghim
   trong run mới. Không lấy gold/run20 cũ để công bố điểm sau tuning.
5. Nhóm review exact câu trả lời + plan + source, cả câu lỗi/clarify/offline.
   Live cần budget riêng; `used=true`/hit target/test xanh không thay review.

## Trạng thái và việc chưa làm

Reviewer AI đã kiểm42 quote hashes/21 chunk canonical và tính nhất quán scope/
coverage của đề xuất; không ghi nhận vấn đề quan trọng. Đây không là review
chuyên môn hoặc nghiệm thu nội dung của người thật. `program_variant/source_id`
được ghi rõ trong scope mẫu, luôn do backend xác định từ nguồn đã chọn.

Đã có builder/protocol/validator mới và source policy trong lựa chọn `focused`.
Các nhóm grammar/two-aspect/related-overfitting có regression; scope chưa rõ
được yêu cầu chọn nguồn. Mặc định legacy/v3 vẫn giữ hành vi trước đó; không
chấm lại run cũ bằng protocol mới. [Kế hoạch thực thi](../plans/2026-11-15-hus-focused-answer.md).
Protocol focused ban đầu giữ đúng chuỗi từ/toán tử và literal số, chỉ linh hoạt
case/khoảng trắng/dấu câu trung tính; không cho thêm từ nối tùy ý. Nếu
muốn paraphrase tự do hơn hướng đầu, cần quyết định thiết kế tiếp theo và kiểm
ngữ nghĩa riêng; không quảng cáo đó là khả năng đã có.
