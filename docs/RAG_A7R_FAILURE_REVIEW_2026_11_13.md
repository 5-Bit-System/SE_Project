# A7R — nguyên nhân routing/guard và các hợp đồng còn mở

Ngày13/11/2026, `hus-llm-rag`. **Đã review18 ca chưa đạt:17 refusal và Q025 khác nhánh scope. Chưa sửa runtime/test/retrieval/dữ liệu.** Giữ nguyên Recall20/24, đủ ý18/36, F2 đúng nguồn8/12, controls12/12 và mọi gold/run/review đã seal. Đây là chẩn đoán AI đã xem nguồn/code/output, human0; không phải điểm mới hoặc nghiệm thu độc lập.

[Receipt mới](../data/hus/qa/20261113/a7r_failure_review_r1/report.json) · [trace router/guard](../data/hus/qa/20261113/a7r_failure_review_r1/diagnostic.json) · [probe biên](../data/hus/qa/20261113/a7r_failure_review_r1/boundary_probes.json) · [scope/đoạn nguồn](../data/hus/qa/20261113/a7r_failure_review_r1/source_context.json).

## Routing: tám ca không đến đúng nguồn

| Ca | Nguyên nhân chung | Regression cần có khi triển khai |
| --- | --- | --- |
| Q014 | “Chức danh lập trình viên và quản trị dự án” chưa khớp `CAREER_TERMS`; route null, không search. | Câu chức danh sau tốt nghiệp/tại đơn vị; giữ nguyên “trưởng phòng (tùy theo năng lực)”, không chuyển vị trí dấu ngoặc hay tự áp điều kiện sang vai trò khác. Phân biệt chức danh người thật/đang tuyển/chính thức. |
| Q026 | “Cơ hội giảng dạy tại trường” thiếu cụm nghề nghiệp hiện nhận; route null. | Vai trò giảng dạy của người tốt nghiệp; negative cho năng lực giảng dạy trong mục tiêu môn, trường là chủ thể và danh sách giảng viên hiện tại. |
| Q039 | `_graduate_role_requested()` đòi `vai tro nao/gi` liền nhau; “vai trò **công tác** nào” không khớp dù có nơi làm việc. | Các cách hỏi vai trò công tác tại trường/viện; negative cho vai trò **của** tổ chức, kỹ năng hoặc môn học. Không bỏ giới hạn chủ thể. |
| Q027 | `FURTHER_STUDY_TERMS` thiếu cụm “khả năng học tập nâng cao”; câu ghim rơi xuống introduction vì có “ngành”, search sai field nên rỗng. | Cụm khả năng học tập/nâng cao sau tốt nghiệp và tiêu đề cùng nghĩa; không dùng riêng “nâng cao” để đổi nội dung/mục tiêu môn thành học sau đại học. |
| Q006/Q018/Q030/Q042 | `_course_name_requested()` thiếu “tên tiếng Việt của mã học phần”; bốn route null, không lookup F2. | Tên tiếng Việt/bằng tiếng Việt theo mã, trong đúng ngành/version; phủ định, nhiều field, tên/mã mâu thuẫn và yêu cầu tiếng Anh không được trả tên Việt thay thế. |

Bảy biến thể mới thuộc các nhóm trên cũng chưa route đúng trong probe trực tiếp; không phải lỗi chỉ xảy ra trên QID đã biết. Các probe negative giữ phân biệt vai trò tổ chức, năng lực trình bày/giảng dạy và chủ đề tiếng Việt. Đây là quan sát classifier, chưa chứng minh kết quả API sau một bản sửa tương lai.

Vị trí code: [name request](../app/hus/question_routing.py#L172), [career/further-study/role](../app/hus/question_routing.py#L227). Tám ca này giải thích28/36 router đúng; trong mẫu retrieval, ba no-call và một sai field vẫn tính vào denominator Recall24, không thay bằng conditional Recall.

## Chín refusal đã có target: năm nguyên nhân khác nhau

Trace dùng đúng hit/score/top5 đã lưu và snapshot v4; không search lại. Edition/hệ vẫn được lọc trong guard. Từ còn dư được kiểm trực tiếp tại `supported_hits()`, không suy chỉ từ câu trả lời từ chối.

| Ca | Bằng chứng | Hướng xử lý chung và giới hạn |
| --- | --- | --- |
| Q002/Q038 | Target rank1. Token `pdf` còn bị đòi trong body/purpose; Q002 còn `bo` từ “toàn bộ”. Resolver xác định hai nguồn là PDF có hash, trang4–5, nhưng guard chưa dùng điều đó làm selector. | Cụm **chọn định dạng nguồn** cần đối chiếu metadata/resolver, edition/hệ/review; “toàn bộ” vẫn yêu cầu đủ ý, không tự coi một excerpt là toàn bộ. Regression cho PDF đúng/sai định dạng, thiếu locator, sai edition và thiếu một mục. Không bỏ `pdf`/`bo` toàn cục, vì đọc PDF/bộ nhớ có thể là chủ đề thật. |
| Q003 | Target2015 rank2. Cú pháp “ghi khả năng học tiếp **kèm** điều kiện gì” không khớp detector đang đòi `ghi kem` liền nhau, nên `kem` bị giữ như dữ kiện. | Nhận cấu trúc điều kiện đi kèm có đối tượng ở giữa; vẫn cần điều kiện thật trong cùng nguồn/scope và giữ phủ định/đối tượng điều kiện. |
| Q015 | Target rank1. Chủ ngữ **“Bản nguồn…”** không khớp `_presentation_syntax()`; còn token `bay`. Đổi riêng prefix thành “Nguồn…” trong probe thì qua guard. | Mở cấu trúc chủ ngữ nguồn có giới hạn; giữ năng lực trình bày, máy bay, câu phủ định và claim ở mệnh đề sau. |
| Q009/Q021/Q033/Q045 | Các target objectives F3 rank1. “Trong **hồ sơ AI tham khảo đã lưu**” để lại `ho/so`; source thiếu `ho`, một số source thiếu cả `so`. Bỏ riêng cụm locator trong probe thì qua guard. | Nhận cụm chỉ hồ sơ đã lưu; “lập hồ sơ”, họ phân phối, số liệu hoặc yêu cầu học thuật vẫn là dữ kiện. Giữ đúng môn/ngành/version, nhãn AI và opt-in. |
| Q037 | Target giới thiệu rank1 nhưng còn token `dinh` từ **“định hướng”**. Nguồn có lịch sử/tên trước/mốc1993 và mô tả cập nhật theo CNTT; chưa nêu rõ một định hướng đào tạo cụ thể. | **Chưa kết luận đây là lỗi grammar.** Bỏ “và định hướng” làm probe qua nhưng đã thay ý hỏi. Cần review cách hiểu lịch sử/cập nhật hay mục tiêu đào tạo; không bỏ `dinh` hoặc biến đủ lịch sử thành đủ cả hai ý. |

**Q003 còn lớp lỗi thứ hai:** đổi sang “khả năng học tiếp **được ghi kèm điều kiện gì**” đã bật `condition_requested`, không còn token thiếu, nhưng guard vẫn từ chối. `CONDITION_SOURCE` chỉ nhận các mẫu “nếu/khi/với điều kiện/tùy…”; source thực tế ghi **“Sinh viên đủ điều kiện và có nhu cầu… sẽ có thể học tiếp…”** nên detector không nhận ra điều kiện không có từ “nếu”. Probe cùng ý có “Nếu đủ điều kiện…” thì được nhận.

Do đó, chỉ sửa cú pháp `kèm` chưa đủ. Regression phải giữ cả “đủ điều kiện **và** có nhu cầu”, cùng scope; nguồn chỉ nói có thể học tiếp không được xem là đã nêu điều kiện. Câu “không yêu cầu đủ điều kiện” không được biến thành yêu cầu điều kiện dương; không kết luận người hỏi đủ điều kiện đăng ký. Hai mismatch bare-condition trong probe được lưu nguyên, không nhận suite xanh.

Vị trí code: [condition detectors](../app/hus/answer_support.py#L69), [source-subject syntax](../app/hus/answer_support.py#L91), [coverage và nhóm nguồn](../app/hus/answer_support.py#L249). PDF trên là bản khôi phục/review `include_markdown`, `raw_original_verified=false`; metadata định dạng không xác nhận toàn tài liệu hoặc hiệu lực học vụ, chưa review trực quan PDF mới.

## Q025: cách chọn nguồn chưa xác định duy nhất một nhánh

Câu hỏi chọn **edition chưa xác định**, không chọn **hệ chưa xác định**. Sau lọc edition, hai nhóm cùng trang vẫn hợp lệ theo bộ lọc hiện có:

| Nhánh | Quote/scope đã ghim | Chọn của guard |
| --- | --- | --- |
| Gold `f8458f2…` | “Mục tiêu đào tạo Chương trình đào tạo Toán học nhằm đào tạo các cử nhân khoa học chuyên sâu về Toán học.”; edition unknown, hệ unknown. | Có trong top5, rank4. |
| Output `4104b80…` | “Chương trình đào tạo tài năng ngành Toán học…” với định hướng giảng dạy/nghiên cứu/áp dụng ở trình độ cao; edition unknown, hệ talent. | Rank3; density purpose1, giống nhóm gold; thứ tự BM25 hiện có quyết định tie. |

Guard không nối hai hệ với nhau; output cũng ghi nhãn talent. Vì vậy, chưa có căn cứ gọi đây là lỗi ranking hoặc bỏ qualifier. Sai khác nằm giữa **gold ghim một nhánh** và câu hỏi chưa chọn duy nhất nhánh đó. Giữ completeness fail trong review cũ; không thêm nhánh gold hoặc công nhận tương đương sau inference để nâng18/36 lên19/36.

Đã kiểm ba quote/span/hash của Q025 và DEV-Q002 trong cùng snapshot nguồn. Văn bản xung quanh có link nhãn “hệ chuẩn2023” trước đoạn gold và link “hệ cử nhân tài năng” trước đoạn output. Đây là dấu hiệu vị trí cần review nguồn; link kề bên chưa chứng minh mọi prose sau nó thuộc edition2023 hoặc đang hiệu lực. **Giữ metadata v4 unknown**; nếu cần sửa scope phải làm candidate dữ liệu/review riêng, không gán hệ/edition ngay trong lượt này.

Trước cohort sau, cần chọn một trong các hợp đồng rõ: câu chọn nhánh/nguồn có thể xác định được; hoặc gold có các nhánh thay thế đã được review **trước inference**; hoặc làm rõ khi cần phân biệt. Không ép thứ tự nguồn để khớp gold và không dùng unknown làm tên khác của hệ chuẩn. Xác nhận tương đương học thuật cần reviewer phù hợp.

## DEV-Q002: liệt kê khác so sánh/lọc nhiều hệ

[Review hợp đồng đã lưu](RAG_DEV_Q002_CONTRACT_REVIEW_2026_11_13.md) vẫn đúng: đoạn giới thiệu trực tiếp liệt kê cả hệ chuẩn và cử nhân tài năng, metadata unknown. Runtime nhận hai qualifier và làm rõ **trước search** tại [answering.py](../app/hus/answering.py#L134); test cũ đòi answered nên còn thất bại. Không bác gold hoặc nới guard chỉ để làm xanh.

Nếu chọn hỗ trợ liệt kê sau này, thiết kế cần phân biệt: liệt kê tên chương trình từ **một quote cùng nguồn**; so sánh khác biệt/điều kiện hai hệ; và xung đột với selector đã chọn. Câu “như thế nào” cũ vẫn có thể cần người dùng/reviewer phân xử ý muốn. Không bật truy xuất nhiều hệ rồi ghép thành một chương trình. Regression cần source có đủ cả hai tên, thiếu một tên, hai tên ở nguồn/edition khác nhau, phủ định, một hệ và selector mâu thuẫn. Chưa triển khai hoặc thay assertion cũ.

## Kiểm chứng và bước đề xuất

- **2.939 file bảo vệ nguyên SHA**, gồm runtime/test/data/gold/run/review cũ. Ba file router/guard/answerer dùng trong probe khớp hash lúc đo A7R.0 request RAG end-to-end mới,0 search,0 provider/socket attempt; không đọc key/env/DB.
-18 probe router cho request đã lưu,10 guard probe trên cached hits,9 probe sửa câu có chủ đích,12 router probe câu tương tự/negative,5 detector và12 guard boundary probe. **Đây là diagnostic, không phải regression suite hoặc điểm A7 mới.** Có mismatch đã biết được giữ lại.
- Cached replay A7R tái hiện20/24–18/36–12/12. Pins A7R/L5r4 vẫn stale do bản vá diagnostic trước đó, không vì lượt review này. Không chạy lại suite; DEV-Q002 chưa xử lý, kết quả564 test LLM/UI thuộc receipt trước.
- A7R được dùng để chuẩn bị thiết kế sửa nên giữ làm **dev/exposed**, tương tự A7S đã tuning. Không dùng lại làm nghiệm thu sau sửa. Review này là root AI/nonblind/nonindependent, human0.

Đề xuất bước thực thi tiếp: viết regression tương tự/negative trước cho routing F1/F2, syntax chọn nguồn/hồ sơ và điều kiện không có “nếu”; sửa theo cụm có giới hạn, giữ yêu cầu đủ ý/edition/hệ/review/citation. Chốt Q025/Q037/DEV-Q002 ở phần hợp đồng riêng trước khi chọn hành vi mới. Sau sửa cần freeze bộ khác≥48 câu/12 mỗi ngành, nguồn/gold trước inference và Routed Recall gồm no-call≥90%; L5/Google vẫn theo key/budget riêng, L6 off.

QA manifest SHA256: `2a899923a8b119a9d3920cd343da93d099fbb361637ac175a94dcf5f4dd6ac1b`. Không stage/commit/push/PR/Actions/deploy.
