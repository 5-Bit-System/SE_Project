# Natural20 — đáp án và nguồn đã ghi nhận

Đây là lượt RAG local, không gọi Gemini. Câu hỏi và nhận xét do Codex(AI) soạn; nhóm chưa nghiệm thu. Không sửa output hoặc ghép hai edition để làm đủ ý.

[Báo cáo ngắn](RAG_HYBRID_NATURAL20_2026_11_14.md) · [Packet nguồn kỳ vọng trước inference](../data/hus/evaluation/hybrid_natural20_20261114_r1/source_packets.json).

## HN20-001

**Câu hỏi:** Ngành Toán học đào tạo người học theo định hướng nào?

**Phạm vi:** mathematics / QD3565-2023

**Kỳ vọng AI trước đo:** f1/objectives; **route thực:** f1 / introduction

**Nhận xét AI sơ bộ:** Câu định hướng được kỳ vọng vào objectives nhưng router chọn introduction; cả hai lấy cùng đoạn giới thiệu rồi bị guard chặn. Wording có thể cần làm rõ; không kết luận sai nội dung chỉ từ field kỳ vọng của AI.

### lexical

Thời gian 0.007482s; search=True; diagnostic=evidence_rejected; target rank=N/A.

```text
Chưa có thông tin đủ căn cứ để trả lời. Đã tìm thấy đoạn liên quan nhưng chưa đủ căn cứ cho đúng yêu cầu/điều kiện trong câu hỏi. Hãy làm rõ ý cần hỏi.
```

Top5 trước guard:

- 1. `e7864b281332873d47213bf53a1bf0f7` — f1/introduction, version=unknown, unit=None; Khoa Toán - Cơ - Tin học có 2 chương trình đào tạo cử nhân hệ chuẩn và hệ cử nhân tài năng ngành Toán học

Guard chọn: (không có).

### hybrid

Thời gian 5.813042s; search=True; diagnostic=evidence_rejected; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

Top5 trước guard:

- 1. `e7864b281332873d47213bf53a1bf0f7` — f1/introduction, version=unknown, unit=None; Khoa Toán - Cơ - Tin học có 2 chương trình đào tạo cử nhân hệ chuẩn và hệ cử nhân tài năng ngành Toán học

Guard chọn: (không có).

## HN20-002

**Câu hỏi:** Tốt nghiệp Toán học thì có thể làm việc ở những đâu?

**Phạm vi:** mathematics / QD3565-2023

**Kỳ vọng AI trước đo:** f1/careers; **route thực:** f3 / suggested_assessment

**Nhận xét AI sơ bộ:** Cụm có “thì” bị route F3/suggested_assessment, đòi mã môn thay vì nghề nghiệp. Chưa search. Bỏ riêng “thì” trong diagnostic vẫn chưa nhận diện được ý nghề nghiệp; không coi sửa một token là đã chữa hết.

### lexical

Thời gian 0.032315s; search=False; diagnostic=clarification_required; target rank=N/A.

```text
Chưa có thông tin đủ căn cứ để trả lời. Cần mã học phần để tránh nhầm nội dung giữa các môn.
```

### hybrid

Thời gian 0.029859s; search=False; diagnostic=clarification_required; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

## HN20-003

**Câu hỏi:** Môn Đại số tuyến tính 1 có số tín chỉ là mấy?

**Phạm vi:** mathematics / QD3565-2023

**Kỳ vọng AI trước đo:** f2/credits; **route thực:** f2 / credits

**Nhận xét AI sơ bộ:** Cả hai trả MAT2300/Đại số tuyến tính 1 đúng4 tín chỉ theo PDFtrang9; giữ draft_unverified. Không dùng vector, không suy hiệu lực học vụ hiện tại.

### lexical

Thời gian 0.114058s; search=False; diagnostic=none; target rank=N/A.

```text
MAT2300 — Đại số tuyến tính 1 (QD3565-2023)
Số tín chỉ: 4

Trạng thái xác minh: draft_unverified; dữ kiện chép từ nguồn, chưa xác minh học vụ.

Nguồn [1]: 101. Toán học-chuẩn final QD 3565 Scan.pdf; trang PDF 9; /hus/sources/e6e33a8a489f7ab77f3db0c727cc4c837ba86f8f17a7eae17c9da08d3c066bd0?page=9#page=9; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.
```

### hybrid

Thời gian 0.069559s; search=False; diagnostic=none; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

## HN20-004

**Câu hỏi:** Tôi muốn biết trong môn Đại số tuyến tính 1 sẽ gặp các khái niệm gì?

**Phạm vi:** mathematics / QD3565-2023

**Kỳ vọng AI trước đo:** f3/content; **route thực:** ? / ?

**Nhận xét AI sơ bộ:** “Sẽ gặp các khái niệm gì” chưa được nhận diện thành nội dung môn; không search. Tên môn đã đầy đủ, nên bổ sung mã/menu chỉ là workaround, không phải giải pháp hiểu câu hỏi.

### lexical

Thời gian 0.001733s; search=False; diagnostic=routing_unknown; target rank=N/A.

```text
Chưa có thông tin đủ căn cứ để trả lời. Chưa hiểu loại thông tin bạn muốn hỏi. Hãy nêu rõ ngành/môn và nội dung cần biết.
```

### hybrid

Thời gian 0.001999s; search=False; diagnostic=routing_unknown; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

## HN20-005

**Câu hỏi:** Nếu tính mỗi mã học phần một lần thì ngành Toán học có bao nhiêu môn trong danh mục?

**Phạm vi:** mathematics / QD3565-2023

**Kỳ vọng AI trước đo:** f2/program_course_count; **route thực:** f3 / suggested_assessment

**Nhận xét AI sơ bộ:** Câu đếm có “thì” bị route assessment trước khi tới nhãn unsupported_operation. Sau lỗi cú pháp vẫn cần triển khai phép đếm danh mục F2. Packet có90 mã duy nhất, không có nghĩa sinh viên phải học90 môn.

### lexical

Thời gian 0.034447s; search=False; diagnostic=clarification_required; target rank=N/A.

```text
Chưa có thông tin đủ căn cứ để trả lời. Cần mã học phần để tránh nhầm nội dung giữa các môn.
```

### hybrid

Thời gian 0.028409s; search=False; diagnostic=clarification_required; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

## HN20-006

**Câu hỏi:** Cho mình một bức tranh khái quát về ngành Toán tin.

**Phạm vi:** mathematics_informatics / QD3567-2023

**Kỳ vọng AI trước đo:** f1/introduction; **route thực:** f1 / introduction

**Nhận xét AI sơ bộ:** Đã lấy đoạn introduction Toán tin được ghim ở rank1, nhưng guard từ chối cả hai. “Bức tranh khái quát” là diễn đạt cần review như request grammar/paraphrase, không thiếu vector target.

### lexical

Thời gian 0.003040s; search=True; diagnostic=evidence_rejected; target rank=1.

```text
Chưa có thông tin đủ căn cứ để trả lời. Đã tìm thấy đoạn liên quan nhưng chưa đủ căn cứ cho đúng yêu cầu/điều kiện trong câu hỏi. Hãy làm rõ ý cần hỏi.
```

Top5 trước guard:

- 1. `44d598308d53629fef5b3c8a7ec61495` — f1/introduction, version=unknown, unit=None; Chương trình đào tạo ngành Toán Tin (trước đây là Toán - Tin ứng dụng) trình độ đại học đã được bắt đầu đào tạo tại Khoa Toán - Cơ - Tin học từ năm 1993. Cùng với các ngành đào tạo gắn với lĩnh vực Công nghệ thông tin, chương trình đào tạo Toán Tin là một trong các chương trình không ngừng được cập nhật để bắt kịp với sự phát triển của lĩnh vực này.

Guard chọn: (không có).

### hybrid

Thời gian 6.351574s; search=True; diagnostic=evidence_rejected; target rank=1.

Đáp án trùng nguyên văn bản lexical bên trên.

Top5 trước guard:

- 1. `44d598308d53629fef5b3c8a7ec61495` — f1/introduction, version=unknown, unit=None; Chương trình đào tạo ngành Toán Tin (trước đây là Toán - Tin ứng dụng) trình độ đại học đã được bắt đầu đào tạo tại Khoa Toán - Cơ - Tin học từ năm 1993. Cùng với các ngành đào tạo gắn với lĩnh vực Công nghệ thông tin, chương trình đào tạo Toán Tin là một trong các chương trình không ngừng được cập nhật để bắt kịp với sự phát triển của lĩnh vực này.

Guard chọn: (không có).

## HN20-007

**Câu hỏi:** Học xong Toán tin có thể tiếp tục học lên những bậc nào?

**Phạm vi:** mathematics_informatics / QD3567-2023

**Kỳ vọng AI trước đo:** f1/further_study; **route thực:** f1 / further_study

**Nhận xét AI sơ bộ:** Cả hai nêu bậc Thạc sĩ/Tiến sĩ và giữ điều kiện đủ điều kiện/có nhu cầu. Quote web có lỗi khoảng trắng “Tiến sĩ.trong”; giữ source unknown, chưa xác minh học vụ.

### lexical

Thời gian 0.004351s; search=True; diagnostic=none; target rank=1.

```text
Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

[1] - Sinh viên đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh vực chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ.trong lĩnh vực Công nghệ thông tin, Cơ sở toán học cho Tin học, Khoa học dữ liệu hoặc Toán ứng dụng.
Nguồn [1]: Ngành Toán Tin; http://mim.hus.vnu.edu.vn/vi/toantin; URL web nguồn; chưa kiểm tra truy cập lại trong request.; phiên bản: unknown; hệ: unknown
```

Top5 trước guard:

- 1. `06eab91c8c35db1572e17ad73748840b` — f1/further_study, version=unknown, unit=None; - Sinh viên đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh vực chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ.trong lĩnh vực Công nghệ thông tin, Cơ sở toán học cho Tin học, Khoa học dữ liệu hoặc Toán ứng dụng.
- 2. `658c9ab088735ae6c0d75ff4278f5bef` — f1/further_study, version=2015, unit=None; 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp

Guard chọn: 06eab91c8c35db1572e17ad73748840b.

### hybrid

Thời gian 5.816829s; search=True; diagnostic=none; target rank=1.

Đáp án trùng nguyên văn bản lexical bên trên.

Top5 trước guard:

- 1. `06eab91c8c35db1572e17ad73748840b` — f1/further_study, version=unknown, unit=None; - Sinh viên đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh vực chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ.trong lĩnh vực Công nghệ thông tin, Cơ sở toán học cho Tin học, Khoa học dữ liệu hoặc Toán ứng dụng.
- 2. `658c9ab088735ae6c0d75ff4278f5bef` — f1/further_study, version=2015, unit=None; 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp

Guard chọn: 06eab91c8c35db1572e17ad73748840b.

## HN20-008

**Câu hỏi:** Muốn học Lập trình hướng đối tượng thì phải hoàn thành môn nào trước?

**Phạm vi:** mathematics_informatics / QD3567-2023

**Kỳ vọng AI trước đo:** f2/prerequisites; **route thực:** f3 / suggested_assessment

**Nhận xét AI sơ bộ:** Hỏi tiên quyết OOP bị route assessment, rồi yêu cầu quyền F3. Đây không phải thiếu opt-in của người hỏi: F2 không cần quyền F3. Cần sửa nhận diện “thì” và cú pháp “phải hoàn thành ... trước”, không hướng người dùng bật AI để chữa route.

### lexical

Thời gian 0.029037s; search=False; diagnostic=permission_required; target rank=N/A.

```text
Chưa có thông tin đủ căn cứ để trả lời. Cần bật cho phép kiến thức AI tham khảo để dùng dữ liệu F3 AI sinh.
```

### hybrid

Thời gian 0.019690s; search=False; diagnostic=permission_required; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

## HN20-009

**Câu hỏi:** Trong nội dung MAT1202, các đối tượng và kế thừa được giải thích thế nào?

**Phạm vi:** mathematics_informatics / QD3567-2023

**Kỳ vọng AI trước đo:** f3/content; **route thực:** f3 / content

**Nhận xét AI sơ bộ:** Có giải thích kế thừa/đa hình; trả thêm tổng quan và hợp thành. Source target từ rank1 lexical thành rank2 hybrid; đáp án cuối giống nhau. Nhóm cần xem phần đối tượng đã đủ ý chưa, tránh coi hit target là đủ mọi ý.

### lexical

Thời gian 0.032499s; search=True; diagnostic=none; target rank=1.

```text
Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.

[1] Tổng quan tham khảo:
Lập trình hướng đối tượng tổ chức phần mềm thành các đối tượng có trạng thái và hành vi, giao tiếp qua những giao diện xác định. Nội dung tham khảo tập trung vào cách giữ bất biến dữ liệu, phân chia trách nhiệm và thay thế cách cài đặt; kế thừa và đa hình được xem trong quan hệ với thiết kế có thể mở rộng và hiểu được.
Các chủ đề tham khảo:
- Đối tượng, lớp và bất biến
- Giao diện và phân chia trách nhiệm
- Kế thừa, đa hình và khả năng thay thế
- Hợp thành và kiểm tra hành vi
Nguồn [1]: kiến thức AI — MAT1202 — Lập trình hướng đối tượng; phiên bản: QD3567-2023; hệ: standard

[2] Kế thừa, đa hình và khả năng thay thế
Kế thừa biểu diễn quan hệ chuyên biệt hóa, còn đa hình cho phép cùng lời gọi được xử lý theo kiểu đối tượng thực tế. Khả năng thay thế đòi hỏi lớp con giữ được những cam kết mà nơi sử dụng mong đợi, chứ không chỉ có cùng tên phương thức.
Khái niệm thành phần: kế thừa; đa hình; ghi đè; khả năng thay thế.
Ví dụ minh họa do AI biên soạn: Các loại bộ xuất tài liệu cùng nhận nội dung và tạo kết quả; nơi gọi không cần phân nhánh theo từng loại nếu mọi bộ xuất giữ đúng hợp đồng chung.
Nguồn [2]: kiến thức AI — MAT1202 — Lập trình hướng đối tượng; phiên bản: QD3567-2023; hệ: standard

[3] Hợp thành và kiểm tra hành vi
Hợp thành tạo hành vi phức tạp bằng cách kết nối các đối tượng nhỏ, thường làm rõ sự phụ thuộc hơn một cây kế thừa sâu. Kiểm tra tập trung vào hành vi quan sát được, trạng thái biên và tương tác, nhờ đó có thể thay cài đặt mà vẫn giữ ý nghĩa dịch vụ.
Khái niệm thành phần: hợp thành; ủy quyền; hành vi quan sát được; trạng thái biên.
Ví dụ minh họa do AI biên soạn: Một dịch vụ mượn sách dùng riêng đối tượng kiểm tra tồn kho và đối tượng ghi giao dịch, nên có thể thay cơ chế ghi mà vẫn giữ quy tắc mượn.
Nguồn [3]: kiến thức AI — MAT1202 — Lập trình hướng đối tượng; phiên bản: QD3567-2023; hệ: standard
```

Top5 trước guard:

- 1. `571f815f9fbe0e6d32d0c4061c1273d5` — f3/content, version=QD3567-2023, unit=2; Kế thừa, đa hình và khả năng thay thế
- 2. `ac957870ee51d7e485956bae14962db3` — f3/content, version=QD3567-2023, unit=None; Tổng quan tham khảo:
- 3. `9bdfb7fc10a3f6ae786c7579e6d60b4d` — f3/content, version=QD3567-2023, unit=3; Hợp thành và kiểm tra hành vi
- 4. `2a7593fe45600a82e5e97ee008ef7062` — f3/content, version=QD3567-2023, unit=1; Giao diện và phân chia trách nhiệm
- 5. `aec1732cc5511ce494b74818dd12477d` — f3/content, version=QD3567-2023, unit=0; Đối tượng, lớp và bất biến

Guard chọn: ac957870ee51d7e485956bae14962db3, 571f815f9fbe0e6d32d0c4061c1273d5, 9bdfb7fc10a3f6ae786c7579e6d60b4d.

### hybrid

Thời gian 6.555713s; search=True; diagnostic=none; target rank=2.

Đáp án trùng nguyên văn bản lexical bên trên.

Top5 trước guard:

- 1. `ac957870ee51d7e485956bae14962db3` — f3/content, version=QD3567-2023, unit=None; Tổng quan tham khảo:
- 2. `571f815f9fbe0e6d32d0c4061c1273d5` — f3/content, version=QD3567-2023, unit=2; Kế thừa, đa hình và khả năng thay thế
- 3. `aec1732cc5511ce494b74818dd12477d` — f3/content, version=QD3567-2023, unit=0; Đối tượng, lớp và bất biến
- 4. `9bdfb7fc10a3f6ae786c7579e6d60b4d` — f3/content, version=QD3567-2023, unit=3; Hợp thành và kiểm tra hành vi
- 5. `2a7593fe45600a82e5e97ee008ef7062` — f3/content, version=QD3567-2023, unit=1; Giao diện và phân chia trách nhiệm

Guard chọn: ac957870ee51d7e485956bae14962db3, 571f815f9fbe0e6d32d0c4061c1273d5, 9bdfb7fc10a3f6ae786c7579e6d60b4d.

## HN20-010

**Câu hỏi:** Ngành Khoa học dữ liệu có định hướng nghề nghiệp nào?

**Phạm vi:** mathematics_informatics / QD3567-2023

**Kỳ vọng AI trước đo:** f1/careers; **route thực:** f1 / careers

**Nhận xét AI sơ bộ:** Cả hai nêu đang chọn Toán tin nhưng hỏi KHDL, hướng dẫn chọn lại; không search, không đổi ngành ngầm.

### lexical

Thời gian 0.001869s; search=False; diagnostic=scope_conflict; target rank=N/A.

```text
Chưa có thông tin đủ căn cứ để trả lời. Bạn đang chọn Toán tin nhưng câu hỏi nhắc đến Khoa học dữ liệu. Hãy chọn Khoa học dữ liệu ở ô ngành rồi hỏi lại.
```

### hybrid

Thời gian 0.002177s; search=False; diagnostic=scope_conflict; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

## HN20-011

**Câu hỏi:** Người tốt nghiệp KHMTTT có thể đảm nhiệm những công việc gì?

**Phạm vi:** computer_science / QD3568-2023

**Kỳ vọng AI trước đo:** f1/careers; **route thực:** f1 / careers

**Nhận xét AI sơ bộ:** Cả hai dùng DOCX2023, nêu các vai trò kỹ thuật/tư vấn-quản lý/lập trình/nghiên cứu/giảng dạy. Có warning review Markdown/chưa xác minh hiệu lực; chưa là xác nhận học vụ độc lập.

### lexical

Thời gian 0.032472s; search=True; diagnostic=none; target rank=1.

```text
Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

[1] ## 4. Vị trí việc làm mà sinh viên có thể đảm nhiệm sau khi tốt nghiệp

Sinh viên tốt nghiệp ngành Khoa học Máy tính và Thông tin có thể:

Làm chuyên gia kĩ thuật tại các cơ quan quản lí và các doanh nghiệp có hệ thống thông tin và nhu cầu tổ chức, khai thác thông tin hiệu quả;

Đảm nhiệm các vai trò tư vấn, quản lí, phân tích, thiết kế, lập trình cho các dự án công nghệ thông tin;

Làm nghiên cứu viên tại các viện, các trung tâm nghiên cứu và phát triển trong lĩnh vực khoa học và công nghệ thông tin, đặc biệt là phát triển nền tảng trí tuệ nhân tạo;

Làm công tác giảng dạy tại các trường đại học, cao đẳng, trung học chuyên nghiệp, dạy nghề trong lĩnh vực khoa học máy tính và khoa học thông tin.
Nguồn [1]: Tệp DOCX — Tài liệu đính kèm: 104.-KHMTTT-chuẩn-04.11.2023.docx; /hus/sources/4838b51f795e858c0672883ff0994a82b8be70e379260189c034e166a0f63517; Tệp DOCX nguồn; không phải PDF.; phiên bản: 2023; hệ: standard
```

Top5 trước guard:

- 1. `3d5549c23ea06616555c5f6917ccfa12` — f1/careers, version=2023, unit=None; ## 4. Vị trí việc làm mà sinh viên có thể đảm nhiệm sau khi tốt nghiệp
- 2. `490cb4103718f52c80496be4f8d33a69` — f1/careers, version=2019, unit=None; 5. Vị trí việc làm mà sinh viên có thể đảm nhiệm sau khi tốt nghiệp
- 3. `291b6949cf13e7e60e54762b0d09ae77` — f1/careers, version=unknown, unit=None; - Đảm nhiệm các vai trò tư vấn, quản lí, phân tích, thiết kế, lập trình cho các dự án công nghệ thông tin.
- 4. `cc9519ceb5c2b5eb461ebfbd3e813e6f` — f1/careers, version=2015, unit=None; 4. Vị trí việc làm mà sinh viên có thể đảm nhận sau khi tốt nghiệp
- 5. `e3dc4d4d8054d927400b121d04d92bef` — f1/careers, version=unknown, unit=None; - Phát triển phần mềm tại các cơ quan, doanh nghiệp công nghệ thông tin.

Guard chọn: 3d5549c23ea06616555c5f6917ccfa12.

### hybrid

Thời gian 5.836858s; search=True; diagnostic=none; target rank=1.

Đáp án trùng nguyên văn bản lexical bên trên.

Top5 trước guard:

- 1. `3d5549c23ea06616555c5f6917ccfa12` — f1/careers, version=2023, unit=None; ## 4. Vị trí việc làm mà sinh viên có thể đảm nhiệm sau khi tốt nghiệp
- 2. `490cb4103718f52c80496be4f8d33a69` — f1/careers, version=2019, unit=None; 5. Vị trí việc làm mà sinh viên có thể đảm nhiệm sau khi tốt nghiệp
- 3. `291b6949cf13e7e60e54762b0d09ae77` — f1/careers, version=unknown, unit=None; - Đảm nhiệm các vai trò tư vấn, quản lí, phân tích, thiết kế, lập trình cho các dự án công nghệ thông tin.
- 4. `cc9519ceb5c2b5eb461ebfbd3e813e6f` — f1/careers, version=2015, unit=None; 4. Vị trí việc làm mà sinh viên có thể đảm nhận sau khi tốt nghiệp
- 5. `e3dc4d4d8054d927400b121d04d92bef` — f1/careers, version=unknown, unit=None; - Phát triển phần mềm tại các cơ quan, doanh nghiệp công nghệ thông tin.

Guard chọn: 3d5549c23ea06616555c5f6917ccfa12.

## HN20-012

**Câu hỏi:** Nếu muốn học tiếp sau KHMTTT thì có những hướng nào?

**Phạm vi:** computer_science / QD3568-2023

**Kỳ vọng AI trước đo:** f1/further_study; **route thực:** f1 / further_study

**Nhận xét AI sơ bộ:** Đáp án khác duy nhất: lexical dùng DOCX2023 có bậc và các lĩnh vực học tiếp; hybrid chọn PDF2015 chỉ nêu bậc Thạc sĩ/Tiến sĩ. Câu “những hướng nào” có thể cần lĩnh vực: bản hybrid ít chi tiết hơn. Chưa ghim edition trong câu hỏi nên cần quy tắc nguồn/review, không ép ranking theo packet hoặc coi hai bản tương đương.

### lexical

Thời gian 0.006415s; search=True; diagnostic=none; target rank=1.

```text
Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

[1] ## 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp

Sinh viên tốt nghiệp đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh vực chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ các chuyên ngành thuộc các lĩnh vực Khoa học Máy tính và Thông tin, Khoa học dữ liệu, Trí tuệ nhân tạo, Toán ứng dụng và các lĩnh vực khác liên quan.
Nguồn [1]: Tệp DOCX — Tài liệu đính kèm: 104.-KHMTTT-chuẩn-04.11.2023.docx; /hus/sources/4838b51f795e858c0672883ff0994a82b8be70e379260189c034e166a0f63517; Tệp DOCX nguồn; không phải PDF.; phiên bản: 2023; hệ: standard
```

Top5 trước guard:

- 1. `e5a82ded76438ecd8803b9c5e5d2e9c1` — f1/further_study, version=2023, unit=None; ## 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp
- 2. `b45d00fe80539319273406967ae12a65` — f1/further_study, version=2015, unit=None; 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp
- 3. `56dc11d1be420dbfde4bcc3786d1276b` — f1/further_study, version=unknown, unit=None; Sinh viên sau khi tốt nghiệp sinh viên có khả năng theo học sau đại học tại các trường đại học uy tín trên thế giới cũng như trong nước, tham gia nghiên cứu, triển khai ứng dụng khoa học công nghệ trong các trường đại học, viện nghiên cứu và cơ sở sản xuất.
- 4. `e29e0cbb74eb7a68f3992ec91f5dd4e9` — f1/further_study, version=unknown, unit=None; - Sinh viên đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh vực chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ trong lĩnh vực Công nghệ thông tin, Cơ sở toán học cho Tin học, Khoa học dữ liệu.
- 5. `7770981a0105a0e83d57880b591dd3b7` — f1/further_study, version=2019, unit=None; 6. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp

Guard chọn: e5a82ded76438ecd8803b9c5e5d2e9c1.

### hybrid

Thời gian 5.733668s; search=True; diagnostic=none; target rank=1.

```text
Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

[1] 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp
- Sinh viên đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh vực
chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ.
Nguồn [1]: Tài liệu đính kèm: CTDT-MT&KHTT-130815.pdf; trang PDF 10; /hus/sources/ec3123312b52b36ac9e612344fca7ab7898532942d468a7fa5fc6901c5e46212?page=10#page=10; Bản PDF khôi phục; chưa xác minh tương đương bản gốc lịch sử.; phiên bản: 2015; hệ: standard
```

Top5 trước guard:

- 1. `b45d00fe80539319273406967ae12a65` — f1/further_study, version=2015, unit=None; 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp
- 2. `e5a82ded76438ecd8803b9c5e5d2e9c1` — f1/further_study, version=2023, unit=None; ## 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp
- 3. `56dc11d1be420dbfde4bcc3786d1276b` — f1/further_study, version=unknown, unit=None; Sinh viên sau khi tốt nghiệp sinh viên có khả năng theo học sau đại học tại các trường đại học uy tín trên thế giới cũng như trong nước, tham gia nghiên cứu, triển khai ứng dụng khoa học công nghệ trong các trường đại học, viện nghiên cứu và cơ sở sản xuất.
- 4. `7770981a0105a0e83d57880b591dd3b7` — f1/further_study, version=2019, unit=None; 6. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp
- 5. `e29e0cbb74eb7a68f3992ec91f5dd4e9` — f1/further_study, version=unknown, unit=None; - Sinh viên đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh vực chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ trong lĩnh vực Công nghệ thông tin, Cơ sở toán học cho Tin học, Khoa học dữ liệu.

Guard chọn: b45d00fe80539319273406967ae12a65.

## HN20-013

**Câu hỏi:** Cho mình biết số tín chỉ của môn Phương pháp nghiên cứu khoa học.

**Phạm vi:** computer_science / QD3568-2023

**Kỳ vọng AI trước đo:** f2/credits; **route thực:** f2 / credits

**Nhận xét AI sơ bộ:** Cả hai giữ MAT1204 đúng3 tín chỉ/PDFtrang10; verified theo sign-off dự án, không phải chứng nhận trường. Không gọi vector.

### lexical

Thời gian 0.090184s; search=False; diagnostic=none; target rank=N/A.

```text
MAT1204 — Phương pháp nghiên cứu khoa học (QD3568-2023)
Số tín chỉ: 3

Trạng thái: verified theo sign-off cấp dự án đã ghi trong nguồn; không phải chứng nhận của trường.

Nguồn [1]: 104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf; trang PDF 10; /hus/sources/bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab?page=10#page=10; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.
```

### hybrid

Thời gian 0.055113s; search=False; diagnostic=none; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

## HN20-014

**Câu hỏi:** Nội dung MAT1204 hướng dẫn đặt câu hỏi nghiên cứu và giới hạn phạm vi ra sao?

**Phạm vi:** computer_science / QD3568-2023

**Kỳ vọng AI trước đo:** f3/content; **route thực:** f3 / content

**Nhận xét AI sơ bộ:** Có unit câu hỏi/phạm vi/khái niệm đúng ý hỏi, nhưng trả thêm tổng quan và ba unit khác. Target rank1 cả hai; đáp án giống nhau. Cần thu gọn theo câu hỏi, không coi nhiều nguồn hơn là chất lượng cao hơn.

### lexical

Thời gian 0.031757s; search=True; diagnostic=none; target rank=1.

```text
Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.

[1] Tổng quan tham khảo:
Phương pháp nghiên cứu khoa học tiếp cận việc tạo tri thức bằng một chuỗi có thể truy vết từ câu hỏi đến bằng chứng và kết luận. Nội dung tham khảo phân biệt mục tiêu mô tả, giải thích và so sánh; nhấn mạnh vai trò của tài liệu, thiết kế phương pháp, quản lý dữ liệu và trình bày giới hạn của lập luận.
Các chủ đề tham khảo:
- Câu hỏi, phạm vi và khái niệm
- Tài liệu và cấu trúc bằng chứng
- Thiết kế phương pháp và quản lý dữ liệu
- Lập luận và liêm chính trong báo cáo
Nguồn [1]: kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; phiên bản: QD3568-2023; hệ: standard

[2] Câu hỏi, phạm vi và khái niệm
Câu hỏi nghiên cứu xác định hiện tượng, đối tượng và kiểu hiểu biết cần đạt, còn phạm vi giới hạn điều có thể kết luận. Một khái niệm trừu tượng cần được định nghĩa và gắn với dấu hiệu quan sát phù hợp để tránh thu thập dữ liệu không trả lời được câu hỏi ban đầu.
Khái niệm thành phần: câu hỏi nghiên cứu; phạm vi; khái niệm; thao tác hóa.
Ví dụ minh họa do AI biên soạn: Nghiên cứu về thói quen đọc phân biệt số lần mượn sách với thời gian đọc thực tế vì hai chỉ báo biểu diễn những khía cạnh khác nhau của khái niệm.
Nguồn [2]: kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; phiên bản: QD3568-2023; hệ: standard

[3] Tài liệu và cấu trúc bằng chứng
Tổng quan tài liệu đặt các công trình trong quan hệ về câu hỏi, phương pháp và kết quả thay vì nối các bản tóm tắt rời nhau. Phân biệt công trình gốc với lời dẫn lại giúp truy nguồn một phát biểu và nhận diện chỗ còn bất đồng hoặc thiếu dữ liệu.
Khái niệm thành phần: công trình gốc; tổng quan tài liệu; trích dẫn; khoảng trống tri thức.
Ví dụ minh họa do AI biên soạn: Hai bài cùng nghiên cứu một hiện tượng có kết quả khác nhau vì dùng nhóm đối tượng và cách đo khác; bảng đối chiếu phương pháp làm rõ nguồn khác biệt.
Nguồn [3]: kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; phiên bản: QD3568-2023; hệ: standard

[4] Thiết kế phương pháp và quản lý dữ liệu
Phương pháp phải liên kết câu hỏi với cách tạo và phân tích bằng chứng, đồng thời chỉ rõ giả định. Lưu dữ liệu gốc, phiên bản xử lý và quyết định loại bỏ giúp người khác hiểu quá trình hình thành kết quả; kết luận không thể mạnh hơn thiết kế cho phép.
Khái niệm thành phần: thiết kế nghiên cứu; giả định; dữ liệu gốc; khả năng tái lập.
Ví dụ minh họa do AI biên soạn: Một nghiên cứu quan sát ghi nhận quan hệ giữa hai biến vẫn cần nêu các yếu tố chưa kiểm soát, vì dữ liệu tương quan chưa xác lập được tác động nhân quả.
Nguồn [4]: kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; phiên bản: QD3568-2023; hệ: standard

[5] Lập luận và liêm chính trong báo cáo
Báo cáo tách câu hỏi, phương pháp, kết quả và diễn giải để người đọc nhận ra điều đã quan sát và điều được suy ra. Trích nguồn chính xác, mô tả giới hạn và không lược bỏ kết quả trái mong đợi là các cách bảo vệ tính kiểm tra được của tri thức.
Khái niệm thành phần: kết quả; diễn giải; liêm chính; giới hạn nghiên cứu.
Ví dụ minh họa do AI biên soạn: Một phép đo không khớp giả thuyết ban đầu vẫn được báo cáo cùng điều kiện thực hiện, nhờ vậy người đọc thấy cả bằng chứng thuận và bằng chứng bất lợi.
Nguồn [5]: kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; phiên bản: QD3568-2023; hệ: standard
```

Top5 trước guard:

- 1. `bb93fa28e9829ba7f5d46fc4ece9a19f` — f3/content, version=QD3568-2023, unit=0; Câu hỏi, phạm vi và khái niệm
- 2. `fbef7824e6826bc004fbc9bc02a993d9` — f3/content, version=QD3568-2023, unit=3; Lập luận và liêm chính trong báo cáo
- 3. `06a4f73df61f8a9493c5f7ee296b1824` — f3/content, version=QD3568-2023, unit=1; Tài liệu và cấu trúc bằng chứng
- 4. `277fe511403034379893f46341b6b429` — f3/content, version=QD3568-2023, unit=None; Tổng quan tham khảo:
- 5. `34d0edb54b3722c051ba1b9e2eb07334` — f3/content, version=QD3568-2023, unit=2; Thiết kế phương pháp và quản lý dữ liệu

Guard chọn: 277fe511403034379893f46341b6b429, bb93fa28e9829ba7f5d46fc4ece9a19f, 06a4f73df61f8a9493c5f7ee296b1824, 34d0edb54b3722c051ba1b9e2eb07334, fbef7824e6826bc004fbc9bc02a993d9.

### hybrid

Thời gian 6.566124s; search=True; diagnostic=none; target rank=1.

Đáp án trùng nguyên văn bản lexical bên trên.

Top5 trước guard:

- 1. `bb93fa28e9829ba7f5d46fc4ece9a19f` — f3/content, version=QD3568-2023, unit=0; Câu hỏi, phạm vi và khái niệm
- 2. `fbef7824e6826bc004fbc9bc02a993d9` — f3/content, version=QD3568-2023, unit=3; Lập luận và liêm chính trong báo cáo
- 3. `277fe511403034379893f46341b6b429` — f3/content, version=QD3568-2023, unit=None; Tổng quan tham khảo:
- 4. `06a4f73df61f8a9493c5f7ee296b1824` — f3/content, version=QD3568-2023, unit=1; Tài liệu và cấu trúc bằng chứng
- 5. `34d0edb54b3722c051ba1b9e2eb07334` — f3/content, version=QD3568-2023, unit=2; Thiết kế phương pháp và quản lý dữ liệu

Guard chọn: 277fe511403034379893f46341b6b429, bb93fa28e9829ba7f5d46fc4ece9a19f, 06a4f73df61f8a9493c5f7ee296b1824, 34d0edb54b3722c051ba1b9e2eb07334, fbef7824e6826bc004fbc9bc02a993d9.

## HN20-015

**Câu hỏi:** Giải thích nội dung MAT1204 giúp mình.

**Phạm vi:** computer_science / QD3568-2023

**Kỳ vọng AI trước đo:** f3/content; **route thực:** f3 / content

**Nhận xét AI sơ bộ:** Cả hai yêu cầu quyền F3 trước khi dùng nội dung AI; không search. Đây là control hợp lệ, khác với008 bị nhầm F2 thành F3.

### lexical

Thời gian 0.020289s; search=False; diagnostic=permission_required; target rank=N/A.

```text
Chưa có thông tin đủ căn cứ để trả lời. Cần bật cho phép kiến thức AI tham khảo để dùng dữ liệu F3 AI sinh.
```

### hybrid

Thời gian 0.018056s; search=False; diagnostic=permission_required; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

## HN20-016

**Câu hỏi:** Theo tài liệu ngành, sinh viên KHDL có thể làm những loại công việc nào?

**Phạm vi:** data_science / QD3569-2023

**Kỳ vọng AI trước đo:** f1/careers; **route thực:** f1 / careers

**Nhận xét AI sơ bộ:** Cả hai trả bốn nhóm công việc KHDL và giữ “tùy theo năng lực”; nguồn unknown edition/hệ. Lỗi chữ “dữ iệu” đã nằm trong nguồn; không tự gán hệ chuẩn hoặc sửa dữ liệu ở lượt đo.

### lexical

Thời gian 0.004638s; search=True; diagnostic=none; target rank=1.

```text
Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

[1] nhà quản lý dữ liệu, chuyên gia phân tích dữ liệu, chuyên gia dữ liệu lớn, chuyên gia tư vấn tại các doanh nghiệp cho các dự án quản lý và khai thác dữ iệu;
Nguồn [1]: Khoa học Dữ liệu; http://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu; URL web nguồn; chưa kiểm tra truy cập lại trong request.; phiên bản: unknown; hệ: unknown

[2] Lập trình viên, quản trị dự án, trưởng phòng (tùy theo năng lực) tại các doanh nghiệp, trung tâm công nghệ thông tin;
Nguồn [2]: Khoa học Dữ liệu; http://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu; URL web nguồn; chưa kiểm tra truy cập lại trong request.; phiên bản: unknown; hệ: unknown

[3] Nghiên cứu viên tại các trung tâm nghiên cứu và phát triển (R&D) trong lĩnh vực khoa học dữ liệu;
Nguồn [3]: Khoa học Dữ liệu; http://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu; URL web nguồn; chưa kiểm tra truy cập lại trong request.; phiên bản: unknown; hệ: unknown

[4] Giảng viên, nghiên cứu viên, chuyên viên kỹ thuật tại các đơn vị trường, viện trong lĩnh vực khoa học dữ liệu.
Nguồn [4]: Khoa học Dữ liệu; http://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu; URL web nguồn; chưa kiểm tra truy cập lại trong request.; phiên bản: unknown; hệ: unknown
```

Top5 trước guard:

- 1. `251ab61e0d6a58faa68914d59fa45516` — f1/careers, version=unknown, unit=None; Lập trình viên, quản trị dự án, trưởng phòng (tùy theo năng lực) tại các doanh nghiệp, trung tâm công nghệ thông tin;
- 2. `940a3740794040de84617af7e9aa78fd` — f1/careers, version=unknown, unit=None; Giảng viên, nghiên cứu viên, chuyên viên kỹ thuật tại các đơn vị trường, viện trong lĩnh vực khoa học dữ liệu.
- 3. `52b2b2acd330744f909bc2ea49cf5fb7` — f1/careers, version=unknown, unit=None; Nghiên cứu viên tại các trung tâm nghiên cứu và phát triển (R&D) trong lĩnh vực khoa học dữ liệu;
- 4. `d844e5fa88b2bf746f918a39a67aa2bb` — f1/careers, version=unknown, unit=None; nhà quản lý dữ liệu, chuyên gia phân tích dữ liệu, chuyên gia dữ liệu lớn, chuyên gia tư vấn tại các doanh nghiệp cho các dự án quản lý và khai thác dữ iệu;

Guard chọn: d844e5fa88b2bf746f918a39a67aa2bb, 251ab61e0d6a58faa68914d59fa45516, 52b2b2acd330744f909bc2ea49cf5fb7, 940a3740794040de84617af7e9aa78fd.

### hybrid

Thời gian 6.058134s; search=True; diagnostic=none; target rank=1.

Đáp án trùng nguyên văn bản lexical bên trên.

Top5 trước guard:

- 1. `251ab61e0d6a58faa68914d59fa45516` — f1/careers, version=unknown, unit=None; Lập trình viên, quản trị dự án, trưởng phòng (tùy theo năng lực) tại các doanh nghiệp, trung tâm công nghệ thông tin;
- 2. `940a3740794040de84617af7e9aa78fd` — f1/careers, version=unknown, unit=None; Giảng viên, nghiên cứu viên, chuyên viên kỹ thuật tại các đơn vị trường, viện trong lĩnh vực khoa học dữ liệu.
- 3. `52b2b2acd330744f909bc2ea49cf5fb7` — f1/careers, version=unknown, unit=None; Nghiên cứu viên tại các trung tâm nghiên cứu và phát triển (R&D) trong lĩnh vực khoa học dữ liệu;
- 4. `d844e5fa88b2bf746f918a39a67aa2bb` — f1/careers, version=unknown, unit=None; nhà quản lý dữ liệu, chuyên gia phân tích dữ liệu, chuyên gia dữ liệu lớn, chuyên gia tư vấn tại các doanh nghiệp cho các dự án quản lý và khai thác dữ iệu;

Guard chọn: d844e5fa88b2bf746f918a39a67aa2bb, 251ab61e0d6a58faa68914d59fa45516, 52b2b2acd330744f909bc2ea49cf5fb7, 940a3740794040de84617af7e9aa78fd.

## HN20-017

**Câu hỏi:** Bạn mô tả ngắn gọn ngành Khoa học dữ liệu đang học những lĩnh vực gì được không?

**Phạm vi:** data_science / QD3569-2023

**Kỳ vọng AI trước đo:** f1/introduction; **route thực:** f3 / content

**Nhận xét AI sơ bộ:** Câu hỏi cả ngành nhưng “học những” dẫn vào F3/content, rồi đòi mã môn. Có thể đang hỏi khái quát ngành hoặc nội dung chương trình; cần làm rõ đối tượng, không kết luận sai chỉ từ kỳ vọng F1 của AI.

### lexical

Thời gian 0.019589s; search=False; diagnostic=clarification_required; target rank=N/A.

```text
Chưa có thông tin đủ căn cứ để trả lời. Cần mã học phần để tránh nhầm nội dung giữa các môn.
```

### hybrid

Thời gian 0.025772s; search=False; diagnostic=clarification_required; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

## HN20-018

**Câu hỏi:** MAT3533 được ghi nhận bao nhiêu tín chỉ trong khung chương trình?

**Phạm vi:** data_science / QD3569-2023

**Kỳ vọng AI trước đo:** f2/credits; **route thực:** f2 / credits

**Nhận xét AI sơ bộ:** Cả hai giữ MAT3533/Học máy đúng3 tín chỉ/PDFtrang11; còn cảnh báo mã tiên quyết MAT2406 chưa giải quyết. Không dùng vector và không suy đủ điều kiện đăng ký.

### lexical

Thời gian 0.051553s; search=False; diagnostic=none; target rank=N/A.

```text
MAT3533 — Học máy (QD3569-2023)
Số tín chỉ: 3

Trạng thái xác minh: draft_unverified; dữ kiện chép từ nguồn, chưa xác minh học vụ.

Mã tiên quyết chưa giải quyết: MAT2406

Nguồn [1]: 105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf; trang PDF 11; /hus/sources/b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2?page=11#page=11; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.
```

### hybrid

Thời gian 0.096896s; search=False; diagnostic=none; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.

## HN20-019

**Câu hỏi:** Nội dung MAT3533 lý giải chuyện mô hình học thuộc dữ liệu cũ nhưng dự đoán kém trên dữ liệu mới như thế nào?

**Phạm vi:** data_science / QD3569-2023

**Kỳ vọng AI trước đo:** f3/content; **route thực:** f3 / content

**Nhận xét AI sơ bộ:** Cả hai đã lấy unit Khái quát và điều chuẩn ở rank3 nhưng guard từ chối câu diễn đạt “học thuộc dữ liệu cũ/dự đoán kém”. Unit liên quan không tự chứng minh entailment toàn câu; đây là ca cần review guard/paraphrase, không phải mất target.

### lexical

Thời gian 0.032145s; search=True; diagnostic=evidence_rejected; target rank=3.

```text
Chưa có thông tin đủ căn cứ để trả lời. Đã tìm thấy đoạn liên quan nhưng chưa đủ căn cứ cho đúng yêu cầu/điều kiện trong câu hỏi. Hãy làm rõ ý cần hỏi.
```

Top5 trước guard:

- 1. `e3016230b7adc54e13dfa486fd969847` — f3/content, version=QD3569-2023, unit=3; Phân tích hành vi mô hình
- 2. `a3e9d09144bd6da73e8d355722b4e7f3` — f3/content, version=QD3569-2023, unit=None; Tổng quan tham khảo:
- 3. `273e8ece7e6db1f8c532c7975f9021e4` — f3/content, version=QD3569-2023, unit=2; Khái quát và điều chuẩn
- 4. `096e4f54f1338174cf06aad0e18a2da8` — f3/content, version=QD3569-2023, unit=1; Mô hình và hàm mất mát
- 5. `dd643c3c0c3230450d67f473878f0ddd` — f3/content, version=QD3569-2023, unit=0; Dữ liệu và biểu diễn

Guard chọn: (không có).

### hybrid

Thời gian 6.290706s; search=True; diagnostic=evidence_rejected; target rank=3.

Đáp án trùng nguyên văn bản lexical bên trên.

Top5 trước guard:

- 1. `a3e9d09144bd6da73e8d355722b4e7f3` — f3/content, version=QD3569-2023, unit=None; Tổng quan tham khảo:
- 2. `e3016230b7adc54e13dfa486fd969847` — f3/content, version=QD3569-2023, unit=3; Phân tích hành vi mô hình
- 3. `273e8ece7e6db1f8c532c7975f9021e4` — f3/content, version=QD3569-2023, unit=2; Khái quát và điều chuẩn
- 4. `dd643c3c0c3230450d67f473878f0ddd` — f3/content, version=QD3569-2023, unit=0; Dữ liệu và biểu diễn
- 5. `096e4f54f1338174cf06aad0e18a2da8` — f3/content, version=QD3569-2023, unit=1; Mô hình và hàm mất mát

Guard chọn: (không có).

## HN20-020

**Câu hỏi:** Mã MAT9999 có số tín chỉ là bao nhiêu?

**Phạm vi:** data_science / QD3569-2023

**Kỳ vọng AI trước đo:** f2/credits; **route thực:** f2 / credits

**Nhận xét AI sơ bộ:** Cả hai báo không có MAT9999 trong ngành/phiên bản đã chọn, không dựng dữ kiện/nguồn và không search vector.

### lexical

Thời gian 0.018678s; search=False; diagnostic=evidence_unavailable; target rank=N/A.

```text
Chưa có thông tin đủ căn cứ để trả lời. Không có môn này trong ngành và phiên bản đã chọn.
```

### hybrid

Thời gian 0.019692s; search=False; diagnostic=evidence_unavailable; target rank=N/A.

Đáp án trùng nguyên văn bản lexical bên trên.
