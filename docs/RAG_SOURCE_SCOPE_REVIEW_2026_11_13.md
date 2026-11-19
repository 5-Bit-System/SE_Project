# Review nguồn bổ sung và cấu hình bàn giao — 13/11/2026

Nhánh `hus-llm-rag`, nền `f61b0fd` + WIP. Đã review thêm Q001 và bốn hồ sơ F3
trên bốn ngành. **Giữ scope unknown của chunk cũ, F3 AI/needs_review và v4/
lexical/LLM tắt**; không đổi nguồn runtime, gold, run hoặc review đã seal.
Review là root AI đã biết nguồn, human0, không phải nghiệm thu học vụ độc lập.

**Bổ sung ở lượt sau cùng ngày:** [review từng ý/edition](RAG_FIELD_EDITION_REVIEW_2026_11_13.md)
đã tải được PDF chuẩn 2012 từ một URL VNU khác và lập ma trận 36 mục F3.
Kết quả 404 của URL HUS dưới đây là lịch sử; receipt cũ giữ nguyên. Mốc tuyển
khóa đầu hệ chuẩn và chuỗi áp dụng vẫn chưa được xác nhận.

## Q001: thêm liên kết lịch sử, chưa sửa scope cũ

Bài HUS công bố28/12/2020 đặt chương trình chuẩn trong cùng dòng lịch sử với
phê duyệt thí điểm2012 và việc mở thêm CLC2018. Đây là bằng chứng liên kết hệ
đáng review tiếp; chưa thay một phát biểu trực tiếp về tuyển khóa đầu hệ chuẩn.
[Bài HUS](https://hus.vnu.edu.vn/tin-tuc-su-kien/hoi-nghi-tong-ket-va-danh-gia-chuong-trinh-dao-tao-chuan-trinh-do-dai-hoc-nganh-may-tinh-va-khoa-hoc-thong-tin-71731).

Danh sách tuyển sinh ĐHQGHN2012 có ngành mãD480105, nhưng “chính quy” không tự
đồng nghĩa “hệ chuẩn”. Chưa dùng bảng đó để relabel đoạn tuyển sinh cũ.
[Danh sách ĐHQGHN](https://vnu.edu.vn/thong-tin-va-chi-tieu-truyen-sinh-dai-hoc-chinh-quy-nam-2012-vao-cac-nganh-thuoc-dhqghn-chinh-sua-cap-nhat-2322012-post12413.html).

Đầu mối `09_0.pdf` vẫn **404 khi tải trực tiếp**. Web tool trả bản trích chỉ mục
10 trang có nhãn chuẩn/quyết định4115/2012; hai yêu cầu screenshot đều cache miss.
Không có binary/ảnh mới để báo là đã khôi phục. “Vào danh mục ngành” cũng khác
“tuyển khóa đầu”. [Đầu mối PDF](https://hus.vnu.edu.vn/sites/default/files/huongdan/09_0.pdf).

Kết luận: có thêm căn cứ lịch sử để reviewer xét trong lượt tích hợp nguồn mới,
**không đổi `program_variant=unknown` của chunk `f526a537e9132345485d15b065a5697b`**,
không mượn CLC, sửa gold hoặc chấm lại A7V4-Q001. Hiệu lực hiện tại/chuỗi văn bản
áp dụng vẫn cần kiểm riêng.

## F3: thêm bốn hồ sơ, tám field

Đã đọc `content`/`objectives`:18 chủ đề và18 mục tiêu. So sánh dưới đây có phạm
vi giới hạn, không xác nhận toàn bộ174 mã/290 hồ sơ hoặc mọi câu trong references.

| Hồ sơ | Điều đối chiếu được và phần chưa đủ |
| --- | --- |
| MAT1204 — KHMTTT | Bản AI có câu hỏi/phạm vi, tài liệu, thiết kế, quản lý dữ liệu và báo cáo. Đề cương2024 trang52–54 khớp mã/tên nhưng còn mục tiêu công bố/tác giả, cơ sở dữ liệu khoa học, công cụ/thuyết trình/làm việc nhóm chưa được bao phủ rõ. Link declared QD3568-2023 không tự xác nhận áp dụng hiện tại. ORI chỉ hỗ trợ phần liêm chính/quản lý dữ liệu, không chứng minh toàn bộ phương pháp. |
| MAT2034 — KHDL | FNC hỗ trợ phân biệt điều kiện bài toán và ổn định thuật toán, ví dụ triệt tiêu chữ số. Còn cần ánh xạ riêng điều kiện/section cho tìm nghiệm, LU, nội suy và tích phân; chưa có candidate đề cương KHDL cho hồ sơ này. |
| MAT2300 — Toán học | MIT calendar có khử, không gian con, cơ sở/số chiều và các không gian cơ bản. Đó là đối chiếu chủ đề, chưa là kiểm từng định lý/ví dụ hoặc bằng chứng HUS; khi rà sâu cần nêu phạm vi/giả thiết như hữu hạn chiều. Chưa có candidate đề cương của đúng hồ sơ. |
| MAT1202 — Toán Tin | Các ý bất biến/giao diện/thay thế/hợp thành có phạm vi khái niệm; Python Classes/UML landing page không chứng minh mọi nguyên tắc thiết kế. **OOP ở PDF2021 trang167–168 thuộc header MAT3372**, không phải MAT1202: từ chối mượn nội dung, tiên quyết hay đánh giá của học phần khác. `syllabus_links` hiện không có candidate cho MAT1202 ngành này. |

References đã mở/ghim bản chụp: [ORI](https://ori.hhs.gov/ori-introduction-responsible-conduct-research),
[quản lý dữ liệu](https://ori.hhs.gov/education/products/n_illinois_u/datamanagement/dmtopics.html),
[FNC conditioning](https://fncbook.com/conditioning/), [FNC stability](https://fncbook.com/stability/),
[MIT calendar](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/pages/calendar/),
[Python Classes](https://docs.python.org/3/tutorial/classes.html), [UML](https://www.omg.org/spec/UML/).
Chúng là nguồn khái niệm, không cấp quyền gắn nhãn official HUS. Reference URL
không pin phiên bản trong runtime; bản chụp review chỉ ghi nội dung thấy lúc tải.

PDF S06/S07 dùng lại capture12/11 có hash khớp; **không tải lại hai PDF trong
lượt này**. Đã render7 trang, xem ảnh5 trang52–54 của S06 và167–168 của S07.
Trang169–170 chỉ đọc text/bối cảnh, không tuyên bố đã xem ảnh hoặc rà cả tài liệu.

Toàn bộ290 F3 record vẫn generated/needs_review/disclosure, academic_verified=false,
official content/objectives/assessment null.106 candidate vẫn ngoài retrieval mặc
định. Review mới không biến định danh F2 hoặc reference khái niệm thành đề cương.

## Cấu hình bàn giao

Luồng chính là [source quickstart](HUS_RAG_QUICKSTART.md): Python3.11,
requirements tối thiểu/lock, dữ liệu v4, lexical và LLMoff; người nhận source
đầy đủ chạy `python -m tools.run_hus_rag --check` trên máy mình. Không cần key/DB
hoặc máy demo của tác giả. Gemini rewrite là tùy chọn riêng cần key/backend.

Chưa có nhu cầu bàn giao offline mới nên **không tạo kit revision mới**. Các kit
Windows cũ giữ nguyên, chứa code trước sửa scope/assessment; không coi receipt
của kit cũ là nghiệm thu code hiện tại. Khi cần bàn giao thì tạo revision mới,
ghim hash/checker và kiểm cấu hình đích riêng. Máy nộp khác Windows64/Python3.11
vẫn chưa được cài/check thực tế; điều đó không chặn việc test source trên máy khác.
Linux/macOS chưa được kiểm ở lượt này. Không publish/deploy; cấu hình public cần
nghiệm thu API/secret/load/health/log/rollback riêng khi có yêu cầu.

## Bằng chứng và phần tiếp theo

[Gói review](../data/hus/review/source_scope_20261113_r1/report.json),
[Q001](../data/hus/review/source_scope_20261113_r1/q001_review.json),
[bốn hồ sơ F3](../data/hus/review/source_scope_20261113_r1/f3_review.json),
[receipt kiểm chứng](../data/hus/qa/20261113/source_scope_r1/report.json).

11 HTTP capture thành công/1 HTTP404; chín lỗi kết nối sandbox ban đầu được
ghi riêng, không coi là website hỏng. Bản chụp có URL/thời điểm/bytes/hash;
nguồn phản hồi200 chỉ xác nhận truy cập tại thời điểm đó, không chứng minh hiệu lực.

**70 test nguồn/F3 release/API đạt**, một warning Starlette/httpx đã có;
**2.848 file cũ giữ SHA**, gồm runtime/data/gold/run/review đã ghim. Cached replay
A7S/A7F/L5 v3 tái hiện; pins A7S và prepared L5 r3 còn khớp. Không có Google call,
thay cờ, stage/commit/push/PR/Actions/deploy trong lượt review.

| Binding | SHA-256 |
| --- | --- |
| Review manifest |`25e05ab52c58b5b15155ed33309cacd1edaacc4e24fb3b5c7800b90448d83162`|
| QA manifest |`315885f767f867df4bbbca9302ad4abefed718619dfbdc762718308e8d9b87be`|

Tiếp theo: reviewer kiểm liên kết tuyển sinh–hệ chuẩn và chuỗi áp dụng; tiếp tục
ánh xạ reference theo từng ý/field/edition F3. Nếu cần thay dữ liệu, tạo candidate
và lượt tích hợp/kiểm riêng, không chép đè snapshot v4 hoặc làm tăng điểm run cũ.
LLM tiếp tục tắt, đề nghị1call diagnostic còn chưa được duyệt; không gọi Google.
