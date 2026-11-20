# Bộ30 câu — kết quả Gemini thật và gói nhóm review

Ngày14/11/2026. Giữ cùng câu hỏi/baseline/bằng chứng của bộ offline; không đổi nguồn, gold hoặc code sau khi đo.

**Đã dùng 24/24 call được duyệt: 23 câu dùng Gemini thật, 1 câu fallback, 0 câu chưa chạy.** Sáu control không gọi Google. **0/30 review người thật, cả30 pending.**

Fallback giữ đáp án RAG gốc; HTTP200 không đồng nghĩa bản sinh được dùng. Không lưu text bị từ chối hoặc body lỗi, nên chỉ kết luận theo metadata an toàn đã thu. Kết quả đúng schema/nguồn chưa chứng minh đủ ý hoặc cải thiện diễn đạt.

## Tóm tắt theo nhóm

| Nhóm | Call | Gemini used | Fallback | Chưa chạy |
| --- | --- | --- | --- | --- |
| f1 | 8 | 8 | 0 | 0 |
| f2 | 8 | 7 | 1 | 0 |
| f3 | 8 | 8 | 0 | 0 |
| control | 0 | 0 | 0 | 0 |

## Nhóm thực hiện

Mở [review.csv](../data/hus/review/student_content_live_20261114_r1/review.csv), sao chép thành file trả riêng và điền tên/ngày, đúng ý, đủ ý, dữ kiện, citation, lỗi còn lại. Đọc cả câu fallback, không chỉ câu dùng được Gemini. [Template JSON](../data/hus/review/student_content_live_20261114_r1/team_review_template.json) đã gắn hash từng phản hồi. Nguồn F1 KHDL vẫn unknown; F3 giữ nhãn AI, chưa nghiệm thu học thuật.

## Bảng kết quả

| Mã | Ngành | Nhóm | HTTP | Gemini used | Fallback | Cờ tự động |
| --- | --- | --- | --- | --- | --- | --- |
| SV30-001 | Toán học | f1 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-002 | Toán học | f1 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-003 | Toán học | f2 | 200 | False | invalid_output | Live fallback: invalid_output |
| SV30-004 | Toán học | f2 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-005 | Toán học | f3 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-006 | Toán học | f3 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-007 | Toán tin | f1 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-008 | Toán tin | f1 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-009 | Toán tin | f2 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-010 | Toán tin | f2 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-011 | Toán tin | f3 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-012 | Toán tin | f3 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-013 | KHMTTT | f1 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-014 | KHMTTT | f1 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-015 | KHMTTT | f2 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-016 | KHMTTT | f2 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-017 | KHMTTT | f3 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-018 | KHMTTT | f3 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-019 | KHDL | f1 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-020 | KHDL | f1 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-021 | KHDL | f2 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-022 | KHDL | f2 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-023 | KHDL | f3 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-024 | KHDL | f3 | 200 | True | None | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-025 | Toán học | control | None | False | basic_chat | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-026 | KHMTTT | control | None | False | basic_chat | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-027 | KHDL | control | None | False | not_answered | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-028 | KHDL | control | None | False | not_answered | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-029 | KHMTTT | control | None | False | not_answered | Không bị cờ tự động; nhóm chưa duyệt |
| SV30-030 | Toán tin | control | None | False | not_answered | Không bị cờ tự động; nhóm chưa duyệt |

## Đáp án và nguồn từng câu

### SV30-001 — Toán học / f1

**Câu hỏi:** Cho em hỏi cơ hội nghề nghiệp ngành Toán học như thế nào?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

4. Vị trí việc làm mà sinh viên có thể đảm nhiệm sau khi tốt nghiệp [1]
Cử nhân khoa học ngành Toán học có năng lực làm việc tại các trung tâm, các [1]
viện nghiên cứu phát triển trong các viện nghiên cứu và công ty, các cơ quan quản lý [1]
kinh tế, tài chính, các cơ sở sản xuất và kinh doanh, ngân hàng, tổ chức bảo hiểm….; [1]
Sinh viên tốt nghiệp cũng có thể giảng dạy các môn liên quan tới ngành của mình [1]
tại các trường đại học, cao đẳng, trung học phổ thông. [1]

**Nguồn trả về:**

- [1] Tài liệu đính kèm: CTDT-Toanhoc-130815.pdf; review=include_markdown; loại=pdf; mở=/hus/sources/2bc81e20fa37d37234cdb50862bdcbd2c1ae0fb4b136a7612a56da34fb712920?page=9#page=9

> 4. Vị trí việc làm mà sinh viên có thể đảm nhiệm sau khi tốt nghiệp
> Cử nhân khoa học ngành Toán học có năng lực làm việc tại các trung tâm, các
> viện nghiên cứu phát triển trong các viện nghiên cứu và công ty, các cơ quan quản lý
> kinh tế, tài chính, các cơ sở sản xuất và kinh doanh, ngân hàng, tổ chức bảo hiểm….;
> Sinh viên tốt nghiệp cũng có thể giảng dạy các môn liên quan tới ngành của mình
> tại các trường đại học, cao đẳng, trung học phổ thông.

### SV30-002 — Toán học / f1

**Câu hỏi:** Khả năng học tiếp của sinh viên ngành Toán học ra sao?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp [1]
Chương trình đào tạo bậc đại học ngành Toán học chủ yếu cung cấp cho sinh viên [1]
những kiến thức, kỹ năng cơ bản và quan trọng hơn cả là phương pháp tư duy logic, [1]
phương pháp lập luận, phân tích và giải quyết vấn đề; phương pháp tư duy trừu tượng, [1]
mô hình hóa; phân tích, mô phỏng - thiết lập bài toán và sử dụng công cụ toán học để [1]
giải quyết; [1]
Những kỹ năng này là tiền đề để mỗi cá nhân người học có thể tiếp tục học, nâng [1]
cao trình độ trong lĩnh vực chuyên môn của mình, phù hợp với nhu cầu của bản thân, [1]
của công việc và của nền kinh tế. [1]

**Nguồn trả về:**

- [1] Tài liệu đính kèm: CTDT-Toanhoc-130815.pdf; review=include_markdown; loại=pdf; mở=/hus/sources/2bc81e20fa37d37234cdb50862bdcbd2c1ae0fb4b136a7612a56da34fb712920?page=9#page=9

> 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp
> Chương trình đào tạo bậc đại học ngành Toán học chủ yếu cung cấp cho sinh viên
> những kiến thức, kỹ năng cơ bản và quan trọng hơn cả là phương pháp tư duy logic,
> phương pháp lập luận, phân tích và giải quyết vấn đề; phương pháp tư duy trừu tượng,
> mô hình hóa; phân tích, mô phỏng - thiết lập bài toán và sử dụng công cụ toán học để
> giải quyết;
> Những kỹ năng này là tiền đề để mỗi cá nhân người học có thể tiếp tục học, nâng
> cao trình độ trong lĩnh vực chuyên môn của mình, phù hợp với nhu cầu của bản thân,
> của công việc và của nền kinh tế.

### SV30-003 — Toán học / f2

**Câu hỏi:** MAT2300 có bao nhiêu tín chỉ?

**Kết quả:** HTTP=200; Gemini used=False; fallback=invalid_output; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

MAT2300 — Đại số tuyến tính 1 (QD3565-2023)
Số tín chỉ: 4

Trạng thái xác minh: draft_unverified; dữ kiện chép từ nguồn, chưa xác minh học vụ.

Nguồn [1]: 101. Toán học-chuẩn final QD 3565 Scan.pdf; trang PDF 9; /hus/sources/e6e33a8a489f7ab77f3db0c727cc4c837ba86f8f17a7eae17c9da08d3c066bd0?page=9#page=9; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.

**Nguồn trả về:**

- [1] 101. Toán học-chuẩn final QD 3565 Scan.pdf; review=draft_unverified; loại=pdf; mở=/hus/sources/e6e33a8a489f7ab77f3db0c727cc4c837ba86f8f17a7eae17c9da08d3c066bd0?page=9#page=9

> {"entry_id": 370, "curriculum_id": 1, "group_key": "IV.1", "source_row_number": 18, "course_code": "MAT2300", "credits_in_source": 4, "prerequisite_source_text": null, "prerequisite_parse_status": "none", "pdf_document": "101. Toán học-chuẩn final QD 3565 Scan.pdf", "pdf_page": 9}

**Cờ tự động:** Live fallback: invalid_output

### SV30-004 — Toán học / f2

**Câu hỏi:** Theo chương trình đã lưu, tiên quyết của MAT2300 là gì?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Thông tin theo nguồn đã chọn:

MAT2300 — Đại số tuyến tính 1 (QD3565-2023)
Điều kiện tiên quyết theo dòng nguồn: Chưa rõ từ nguồn
[1] Dòng nguồn không ghi điều kiện tiên quyết

Trạng thái xác minh: draft_unverified; dữ kiện chép từ nguồn, chưa xác minh học vụ.

Chưa đủ căn cứ để kết luận “không có tiên quyết”: ô nguồn trống vẫn là chưa rõ.

Thông tin theo nguồn không kết luận bạn đủ điều kiện đăng ký học phần.

Nguồn [1]: 101. Toán học-chuẩn final QD 3565 Scan.pdf; trang PDF 9; /hus/sources/e6e33a8a489f7ab77f3db0c727cc4c837ba86f8f17a7eae17c9da08d3c066bd0?page=9#page=9; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.

**Nguồn trả về:**

- [1] 101. Toán học-chuẩn final QD 3565 Scan.pdf; review=draft_unverified; loại=pdf; mở=/hus/sources/e6e33a8a489f7ab77f3db0c727cc4c837ba86f8f17a7eae17c9da08d3c066bd0?page=9#page=9

> {"entry_id": 370, "curriculum_id": 1, "group_key": "IV.1", "source_row_number": 18, "course_code": "MAT2300", "credits_in_source": 4, "prerequisite_source_text": null, "prerequisite_parse_status": "none", "pdf_document": "101. Toán học-chuẩn final QD 3565 Scan.pdf", "pdf_page": 9}

### SV30-005 — Toán học / f3

**Câu hỏi:** Nội dung MAT2300: Ma trận và ánh xạ tuyến tính?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.

Tổng quan tham khảo: [1]
Đại số tuyến tính 1 xây dựng ngôn ngữ cho hệ phương trình, không gian vectơ và ánh xạ tuyến tính. Nội dung tham khảo đặt phép tính ma trận trong quan hệ với không gian nghiệm, cơ sở và số chiều, giúp giải thích ý nghĩa của phép khử thay vì chỉ ghi nhớ quy tắc biến đổi ký hiệu. [1]
Các chủ đề tham khảo: [1]
- Hệ tuyến tính và phép khử [1]
- Ma trận và ánh xạ tuyến tính [1]
- Không gian con, sinh và độc lập [1]
- Cơ sở, số chiều và tọa độ [1]
- Hạt nhân, ảnh và hạng [1]

Ma trận và ánh xạ tuyến tính [2]
Các cột của ma trận là ảnh của vectơ cơ sở chuẩn, nhờ đó phép nhân ma trận biểu diễn tác động của ánh xạ lên mọi vectơ. Tích ma trận tương ứng hợp thành ánh xạ theo thứ tự, giải thích vì sao nhìn chung đổi thứ tự hai ma trận sẽ làm đổi kết quả. [2]
Khái niệm thành phần: cột ma trận; ánh xạ tuyến tính; hợp thành; ma trận đơn vị. [2]
Ví dụ minh họa do AI biên soạn: Trong mặt phẳng, co theo một trục rồi quay thường cho kết quả khác quay trước rồi mới co theo trục cố định, phản ánh tính không giao hoán của tích ma trận. [2]

Hạt nhân, ảnh và hạng [3]
Hạt nhân chứa những hướng bị ánh xạ đưa về không, còn ảnh chứa các đầu ra có thể đạt được. Định lý hạng và số chiều hạt nhân liên kết phần thông tin bị mất với phần được giữ; nhờ đó tính đơn ánh và toàn ánh có thể được phân tích bằng cấu trúc không gian. [3]
Khái niệm thành phần: hạt nhân; ảnh; hạng; định lý hạng. [3]
Ví dụ minh họa do AI biên soạn: Phép chiếu không gian ba chiều xuống một mặt phẳng mất thành phần theo phương vuông góc; phương bị mất tạo hạt nhân còn mặt phẳng là ảnh. [3]

**Nguồn trả về:**

- [1] kiến thức AI — MAT2300 — Đại số tuyến tính 1; review=needs_review; loại=ai; mở=không có link

> Tổng quan tham khảo:
> Đại số tuyến tính 1 xây dựng ngôn ngữ cho hệ phương trình, không gian vectơ và ánh xạ tuyến tính. Nội dung tham khảo đặt phép tính ma trận trong quan hệ với không gian nghiệm, cơ sở và số chiều, giúp giải thích ý nghĩa của phép khử thay vì chỉ ghi nhớ quy tắc biến đổi ký hiệu.
> Các chủ đề tham khảo:
> - Hệ tuyến tính và phép khử
> - Ma trận và ánh xạ tuyến tính
> - Không gian con, sinh và độc lập
> - Cơ sở, số chiều và tọa độ
> - Hạt nhân, ảnh và hạng

- [2] kiến thức AI — MAT2300 — Đại số tuyến tính 1; review=needs_review; loại=ai; mở=không có link

> Ma trận và ánh xạ tuyến tính
> Các cột của ma trận là ảnh của vectơ cơ sở chuẩn, nhờ đó phép nhân ma trận biểu diễn tác động của ánh xạ lên mọi vectơ. Tích ma trận tương ứng hợp thành ánh xạ theo thứ tự, giải thích vì sao nhìn chung đổi thứ tự hai ma trận sẽ làm đổi kết quả.
> Khái niệm thành phần: cột ma trận; ánh xạ tuyến tính; hợp thành; ma trận đơn vị.
> Ví dụ minh họa do AI biên soạn: Trong mặt phẳng, co theo một trục rồi quay thường cho kết quả khác quay trước rồi mới co theo trục cố định, phản ánh tính không giao hoán của tích ma trận.

- [3] kiến thức AI — MAT2300 — Đại số tuyến tính 1; review=needs_review; loại=ai; mở=không có link

> Hạt nhân, ảnh và hạng
> Hạt nhân chứa những hướng bị ánh xạ đưa về không, còn ảnh chứa các đầu ra có thể đạt được. Định lý hạng và số chiều hạt nhân liên kết phần thông tin bị mất với phần được giữ; nhờ đó tính đơn ánh và toàn ánh có thể được phân tích bằng cấu trúc không gian.
> Khái niệm thành phần: hạt nhân; ảnh; hạng; định lý hạng.
> Ví dụ minh họa do AI biên soạn: Phép chiếu không gian ba chiều xuống một mặt phẳng mất thành phần theo phương vuông góc; phương bị mất tạo hạt nhân còn mặt phẳng là ảnh.

### SV30-006 — Toán học / f3

**Câu hỏi:** Hồ sơ môn MAT2300 có mục tiêu học tập nào?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.

Mục tiêu tham khảo do AI đề xuất: [1]
- Giải thích cấu trúc nghiệm hệ tuyến tính bằng phần tử trụ và biến tự do. [1]
- Liên hệ phép nhân ma trận với tác động và hợp thành ánh xạ tuyến tính. [1]
- Phân biệt tập sinh, độc lập tuyến tính và cơ sở của không gian. [1]
- Diễn giải tọa độ theo cơ sở và ý nghĩa số chiều. [1]
- Phân tích hạt nhân, ảnh và hạng để nhận ra thông tin bị mất qua ánh xạ. [1]

**Nguồn trả về:**

- [1] kiến thức AI — MAT2300 — Đại số tuyến tính 1; review=needs_review; loại=ai; mở=không có link

> Mục tiêu tham khảo do AI đề xuất:
> - Giải thích cấu trúc nghiệm hệ tuyến tính bằng phần tử trụ và biến tự do.
> - Liên hệ phép nhân ma trận với tác động và hợp thành ánh xạ tuyến tính.
> - Phân biệt tập sinh, độc lập tuyến tính và cơ sở của không gian.
> - Diễn giải tọa độ theo cơ sở và ý nghĩa số chiều.
> - Phân tích hạt nhân, ảnh và hạng để nhận ra thông tin bị mất qua ánh xạ.

### SV30-007 — Toán tin / f1

**Câu hỏi:** Cho em hỏi cơ hội nghề nghiệp ngành Toán tin như thế nào?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

4. Vị trí việc làm mà sinh viên có thể đảm nhận sau khi tốt nghiệp [1]
- Làm việc tại các trung tâm, các việc nghiên cứu phát triển, các cơ quan quản [1]
lý kinh tế, tài chính, các cơ sở sản xuất, kinh doanh có sử dụng kiến thức Toán ứng [1]
dụng hay công nghệ thông tin [1]
- Làm công tác giảng dạy tại các trường đại học, cao đẳng, trung học chuyên [1]
nghiệp, dạy nghề và trung học phổ thông trong lĩnh vực Toán học và Khoa học [1]
thông tin [1]

**Nguồn trả về:**

- [1] Tài liệu đính kèm: CTDT-TTUD-130815.pdf; review=include_markdown; loại=pdf; mở=/hus/sources/e8a9524ff81bfec2038760970327650c005f31cbadb7be8ad2abe2f141c8978f?page=9#page=9

> 4. Vị trí việc làm mà sinh viên có thể đảm nhận sau khi tốt nghiệp
> - Làm việc tại các trung tâm, các việc nghiên cứu phát triển, các cơ quan quản
> lý kinh tế, tài chính, các cơ sở sản xuất, kinh doanh có sử dụng kiến thức Toán ứng
> dụng hay công nghệ thông tin
> - Làm công tác giảng dạy tại các trường đại học, cao đẳng, trung học chuyên
> nghiệp, dạy nghề và trung học phổ thông trong lĩnh vực Toán học và Khoa học
> thông tin

### SV30-008 — Toán tin / f1

**Câu hỏi:** Khả năng học tiếp của sinh viên ngành Toán tin ra sao?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp [1]
- Sinh viên đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh [1]
vực chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ. [1]

**Nguồn trả về:**

- [1] Tài liệu đính kèm: CTDT-TTUD-130815.pdf; review=include_markdown; loại=pdf; mở=/hus/sources/e8a9524ff81bfec2038760970327650c005f31cbadb7be8ad2abe2f141c8978f?page=9#page=9

> 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp
> - Sinh viên đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh
> vực chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ.

### SV30-009 — Toán tin / f2

**Câu hỏi:** MAT1202 có bao nhiêu tín chỉ?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Thông tin theo nguồn đã chọn:

MAT1202 — Lập trình hướng đối tượng (QD3567-2023)
Số tín chỉ: 3

Trạng thái xác minh: draft_unverified; dữ kiện chép từ nguồn, chưa xác minh học vụ.

Nguồn [1]: 103. Toán tin-chuẩn final QD 3567 Scan.pdf; trang PDF 10; /hus/sources/6c19e390ba61c1766e2826b055fe39b3987db25ef707263f60ce337347d87df8?page=10#page=10; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.

**Nguồn trả về:**

- [1] 103. Toán tin-chuẩn final QD 3567 Scan.pdf; review=draft_unverified; loại=pdf; mở=/hus/sources/6c19e390ba61c1766e2826b055fe39b3987db25ef707263f60ce337347d87df8?page=10#page=10

> {"entry_id": 425, "curriculum_id": 2, "group_key": "V.1", "source_row_number": 32, "course_code": "MAT1202", "credits_in_source": 3, "prerequisite_source_text": "MAT2505", "prerequisite_parse_status": "normalized", "pdf_document": "103. Toán tin-chuẩn final QD 3567 Scan.pdf", "pdf_page": 10}

### SV30-010 — Toán tin / f2

**Câu hỏi:** Theo chương trình đã lưu, tiên quyết của MAT1202 là gì?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Thông tin theo nguồn đã chọn:

MAT1202 — Lập trình hướng đối tượng (QD3567-2023)
Điều kiện tiên quyết theo dòng nguồn: Có ghi điều kiện trong nguồn
[1] MAT2505

Trạng thái xác minh: draft_unverified; dữ kiện chép từ nguồn, chưa xác minh học vụ.

Thông tin theo nguồn không kết luận bạn đủ điều kiện đăng ký học phần.

Nguồn [1]: 103. Toán tin-chuẩn final QD 3567 Scan.pdf; trang PDF 10; /hus/sources/6c19e390ba61c1766e2826b055fe39b3987db25ef707263f60ce337347d87df8?page=10#page=10; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.

**Nguồn trả về:**

- [1] 103. Toán tin-chuẩn final QD 3567 Scan.pdf; review=draft_unverified; loại=pdf; mở=/hus/sources/6c19e390ba61c1766e2826b055fe39b3987db25ef707263f60ce337347d87df8?page=10#page=10

> {"entry_id": 425, "curriculum_id": 2, "group_key": "V.1", "source_row_number": 32, "course_code": "MAT1202", "credits_in_source": 3, "prerequisite_source_text": "MAT2505", "prerequisite_parse_status": "normalized", "pdf_document": "103. Toán tin-chuẩn final QD 3567 Scan.pdf", "pdf_page": 10}

### SV30-011 — Toán tin / f3

**Câu hỏi:** Nội dung MAT1202: Giao diện và phân chia trách nhiệm?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.

Tổng quan tham khảo: [1]
Lập trình hướng đối tượng tổ chức phần mềm thành các đối tượng có trạng thái và hành vi, giao tiếp qua những giao diện xác định. Nội dung tham khảo tập trung vào cách giữ bất biến dữ liệu, phân chia trách nhiệm và thay thế cách cài đặt; kế thừa và đa hình được xem trong quan hệ với thiết kế có thể mở rộng và hiểu được. [1]
Các chủ đề tham khảo: [1]
- Đối tượng, lớp và bất biến [1]
- Giao diện và phân chia trách nhiệm [1]
- Kế thừa, đa hình và khả năng thay thế [1]
- Hợp thành và kiểm tra hành vi [1]

Đối tượng, lớp và bất biến [2]
Lớp mô tả kiểu trạng thái và thao tác, còn đối tượng là một thể hiện cụ thể với vòng đời riêng. Đóng gói giúp các thay đổi đi qua những thao tác có kiểm soát, nhờ đó bất biến của đối tượng được duy trì thay vì để mọi phần chương trình sửa trực tiếp dữ liệu. [2]
Khái niệm thành phần: lớp; đối tượng; đóng gói; bất biến. [2]
Ví dụ minh họa do AI biên soạn: Đối tượng giỏ hàng chỉ nhận số lượng không âm qua thao tác cập nhật, giúp các phần giao diện không vô tình tạo một giỏ có số lượng âm. [2]

Giao diện và phân chia trách nhiệm [3]
Giao diện cho biết dịch vụ mà một đối tượng cung cấp mà không buộc nơi sử dụng biết chi tiết lưu trữ. Khi mỗi lớp giữ một trách nhiệm rõ, thay đổi trong một cơ chế có thể được giới hạn; liên kết chặt giữa nhiều lớp khiến tác động thay đổi lan rộng hơn. [3]
Khái niệm thành phần: giao diện; trách nhiệm; kết dính; phụ thuộc. [3]
Ví dụ minh họa do AI biên soạn: Màn hình hiển thị gọi một giao diện tra cứu sách, nên chuyển kho dữ liệu từ tệp sang cơ sở dữ liệu không nhất thiết làm đổi mã hiển thị. [3]

Kế thừa, đa hình và khả năng thay thế [4]
Kế thừa biểu diễn quan hệ chuyên biệt hóa, còn đa hình cho phép cùng lời gọi được xử lý theo kiểu đối tượng thực tế. Khả năng thay thế đòi hỏi lớp con giữ được những cam kết mà nơi sử dụng mong đợi, chứ không chỉ có cùng tên phương thức. [4]
Khái niệm thành phần: kế thừa; đa hình; ghi đè; khả năng thay thế. [4]
Ví dụ minh họa do AI biên soạn: Các loại bộ xuất tài liệu cùng nhận nội dung và tạo kết quả; nơi gọi không cần phân nhánh theo từng loại nếu mọi bộ xuất giữ đúng hợp đồng chung. [4]

Hợp thành và kiểm tra hành vi [5]
Hợp thành tạo hành vi phức tạp bằng cách kết nối các đối tượng nhỏ, thường làm rõ sự phụ thuộc hơn một cây kế thừa sâu. Kiểm tra tập trung vào hành vi quan sát được, trạng thái biên và tương tác, nhờ đó có thể thay cài đặt mà vẫn giữ ý nghĩa dịch vụ. [5]
Khái niệm thành phần: hợp thành; ủy quyền; hành vi quan sát được; trạng thái biên. [5]
Ví dụ minh họa do AI biên soạn: Một dịch vụ mượn sách dùng riêng đối tượng kiểm tra tồn kho và đối tượng ghi giao dịch, nên có thể thay cơ chế ghi mà vẫn giữ quy tắc mượn. [5]

**Nguồn trả về:**

- [1] kiến thức AI — MAT1202 — Lập trình hướng đối tượng; review=needs_review; loại=ai; mở=không có link

> Tổng quan tham khảo:
> Lập trình hướng đối tượng tổ chức phần mềm thành các đối tượng có trạng thái và hành vi, giao tiếp qua những giao diện xác định. Nội dung tham khảo tập trung vào cách giữ bất biến dữ liệu, phân chia trách nhiệm và thay thế cách cài đặt; kế thừa và đa hình được xem trong quan hệ với thiết kế có thể mở rộng và hiểu được.
> Các chủ đề tham khảo:
> - Đối tượng, lớp và bất biến
> - Giao diện và phân chia trách nhiệm
> - Kế thừa, đa hình và khả năng thay thế
> - Hợp thành và kiểm tra hành vi

- [2] kiến thức AI — MAT1202 — Lập trình hướng đối tượng; review=needs_review; loại=ai; mở=không có link

> Đối tượng, lớp và bất biến
> Lớp mô tả kiểu trạng thái và thao tác, còn đối tượng là một thể hiện cụ thể với vòng đời riêng. Đóng gói giúp các thay đổi đi qua những thao tác có kiểm soát, nhờ đó bất biến của đối tượng được duy trì thay vì để mọi phần chương trình sửa trực tiếp dữ liệu.
> Khái niệm thành phần: lớp; đối tượng; đóng gói; bất biến.
> Ví dụ minh họa do AI biên soạn: Đối tượng giỏ hàng chỉ nhận số lượng không âm qua thao tác cập nhật, giúp các phần giao diện không vô tình tạo một giỏ có số lượng âm.

- [3] kiến thức AI — MAT1202 — Lập trình hướng đối tượng; review=needs_review; loại=ai; mở=không có link

> Giao diện và phân chia trách nhiệm
> Giao diện cho biết dịch vụ mà một đối tượng cung cấp mà không buộc nơi sử dụng biết chi tiết lưu trữ. Khi mỗi lớp giữ một trách nhiệm rõ, thay đổi trong một cơ chế có thể được giới hạn; liên kết chặt giữa nhiều lớp khiến tác động thay đổi lan rộng hơn.
> Khái niệm thành phần: giao diện; trách nhiệm; kết dính; phụ thuộc.
> Ví dụ minh họa do AI biên soạn: Màn hình hiển thị gọi một giao diện tra cứu sách, nên chuyển kho dữ liệu từ tệp sang cơ sở dữ liệu không nhất thiết làm đổi mã hiển thị.

- [4] kiến thức AI — MAT1202 — Lập trình hướng đối tượng; review=needs_review; loại=ai; mở=không có link

> Kế thừa, đa hình và khả năng thay thế
> Kế thừa biểu diễn quan hệ chuyên biệt hóa, còn đa hình cho phép cùng lời gọi được xử lý theo kiểu đối tượng thực tế. Khả năng thay thế đòi hỏi lớp con giữ được những cam kết mà nơi sử dụng mong đợi, chứ không chỉ có cùng tên phương thức.
> Khái niệm thành phần: kế thừa; đa hình; ghi đè; khả năng thay thế.
> Ví dụ minh họa do AI biên soạn: Các loại bộ xuất tài liệu cùng nhận nội dung và tạo kết quả; nơi gọi không cần phân nhánh theo từng loại nếu mọi bộ xuất giữ đúng hợp đồng chung.

- [5] kiến thức AI — MAT1202 — Lập trình hướng đối tượng; review=needs_review; loại=ai; mở=không có link

> Hợp thành và kiểm tra hành vi
> Hợp thành tạo hành vi phức tạp bằng cách kết nối các đối tượng nhỏ, thường làm rõ sự phụ thuộc hơn một cây kế thừa sâu. Kiểm tra tập trung vào hành vi quan sát được, trạng thái biên và tương tác, nhờ đó có thể thay cài đặt mà vẫn giữ ý nghĩa dịch vụ.
> Khái niệm thành phần: hợp thành; ủy quyền; hành vi quan sát được; trạng thái biên.
> Ví dụ minh họa do AI biên soạn: Một dịch vụ mượn sách dùng riêng đối tượng kiểm tra tồn kho và đối tượng ghi giao dịch, nên có thể thay cơ chế ghi mà vẫn giữ quy tắc mượn.

### SV30-012 — Toán tin / f3

**Câu hỏi:** Hồ sơ môn MAT1202 có mục tiêu học tập nào?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.

Mục tiêu tham khảo do AI đề xuất: [1]
- Phân biệt lớp và đối tượng, giải thích cách đóng gói duy trì bất biến. [1]
- Thiết kế giao diện theo trách nhiệm và nhận diện phụ thuộc giữa các lớp. [1]
- Giải thích đa hình cùng điều kiện để một kiểu chuyên biệt thay thế kiểu chung. [1]
- So sánh kế thừa với hợp thành và mô tả hành vi cần giữ khi đổi cài đặt. [1]

**Nguồn trả về:**

- [1] kiến thức AI — MAT1202 — Lập trình hướng đối tượng; review=needs_review; loại=ai; mở=không có link

> Mục tiêu tham khảo do AI đề xuất:
> - Phân biệt lớp và đối tượng, giải thích cách đóng gói duy trì bất biến.
> - Thiết kế giao diện theo trách nhiệm và nhận diện phụ thuộc giữa các lớp.
> - Giải thích đa hình cùng điều kiện để một kiểu chuyên biệt thay thế kiểu chung.
> - So sánh kế thừa với hợp thành và mô tả hành vi cần giữ khi đổi cài đặt.

### SV30-013 — KHMTTT / f1

**Câu hỏi:** Cho em hỏi cơ hội nghề nghiệp ngành KHMTTT như thế nào?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

## 4. Vị trí việc làm mà sinh viên có thể đảm nhiệm sau khi tốt nghiệp [1]

Sinh viên tốt nghiệp ngành Khoa học Máy tính và Thông tin có thể: [1]

Làm chuyên gia kĩ thuật tại các cơ quan quản lí và các doanh nghiệp có hệ thống thông tin và nhu cầu tổ chức, khai thác thông tin hiệu quả; [1]

Đảm nhiệm các vai trò tư vấn, quản lí, phân tích, thiết kế, lập trình cho các dự án công nghệ thông tin; [1]

Làm nghiên cứu viên tại các viện, các trung tâm nghiên cứu và phát triển trong lĩnh vực khoa học và công nghệ thông tin, đặc biệt là phát triển nền tảng trí tuệ nhân tạo; [1]

Làm công tác giảng dạy tại các trường đại học, cao đẳng, trung học chuyên nghiệp, dạy nghề trong lĩnh vực khoa học máy tính và khoa học thông tin. [1]

**Nguồn trả về:**

- [1] Tài liệu đính kèm: 104.-KHMTTT-chuẩn-04.11.2023.docx; review=include_markdown; loại=file; mở=/hus/sources/4838b51f795e858c0672883ff0994a82b8be70e379260189c034e166a0f63517

> ## 4. Vị trí việc làm mà sinh viên có thể đảm nhiệm sau khi tốt nghiệp
> 
> Sinh viên tốt nghiệp ngành Khoa học Máy tính và Thông tin có thể:
> 
> Làm chuyên gia kĩ thuật tại các cơ quan quản lí và các doanh nghiệp có hệ thống thông tin và nhu cầu tổ chức, khai thác thông tin hiệu quả;
> 
> Đảm nhiệm các vai trò tư vấn, quản lí, phân tích, thiết kế, lập trình cho các dự án công nghệ thông tin;
> 
> Làm nghiên cứu viên tại các viện, các trung tâm nghiên cứu và phát triển trong lĩnh vực khoa học và công nghệ thông tin, đặc biệt là phát triển nền tảng trí tuệ nhân tạo;
> 
> Làm công tác giảng dạy tại các trường đại học, cao đẳng, trung học chuyên nghiệp, dạy nghề trong lĩnh vực khoa học máy tính và khoa học thông tin.

### SV30-014 — KHMTTT / f1

**Câu hỏi:** Khả năng học tiếp của sinh viên ngành KHMTTT ra sao?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

## 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp [1]

Sinh viên tốt nghiệp đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh vực chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ các chuyên ngành thuộc các lĩnh vực Khoa học Máy tính và Thông tin, Khoa học dữ liệu, Trí tuệ nhân tạo, Toán ứng dụng và các lĩnh vực khác liên quan. [1]

**Nguồn trả về:**

- [1] Tài liệu đính kèm: 104.-KHMTTT-chuẩn-04.11.2023.docx; review=include_markdown; loại=file; mở=/hus/sources/4838b51f795e858c0672883ff0994a82b8be70e379260189c034e166a0f63517

> ## 5. Khả năng học tập, nâng cao trình độ sau khi tốt nghiệp
> 
> Sinh viên tốt nghiệp đủ điều kiện và có nhu cầu học tập nâng cao trình độ trong lĩnh vực chuyên môn của mình sẽ có thể học tiếp ở bậc Thạc sĩ, Tiến sĩ các chuyên ngành thuộc các lĩnh vực Khoa học Máy tính và Thông tin, Khoa học dữ liệu, Trí tuệ nhân tạo, Toán ứng dụng và các lĩnh vực khác liên quan.

### SV30-015 — KHMTTT / f2

**Câu hỏi:** MAT1204 có bao nhiêu tín chỉ?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Thông tin theo nguồn đã chọn:

MAT1204 — Phương pháp nghiên cứu khoa học (QD3568-2023)
Số tín chỉ: 3

Trạng thái: verified theo sign-off cấp dự án đã ghi trong nguồn; không phải chứng nhận của trường.

Nguồn [1]: 104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf; trang PDF 10; /hus/sources/bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab?page=10#page=10; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.

**Nguồn trả về:**

- [1] 104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf; review=verified; loại=pdf; mở=/hus/sources/bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab?page=10#page=10

> {"entry_id": 499, "curriculum_id": 3, "group_key": "IV", "source_row_number": 25, "course_code": "MAT1204", "credits_in_source": 3, "prerequisite_source_text": "MAT3507\nMAT3514", "prerequisite_parse_status": "normalized", "pdf_document": "104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf", "pdf_page": 10}

### SV30-016 — KHMTTT / f2

**Câu hỏi:** Theo chương trình đã lưu, tiên quyết của MAT1204 là gì?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Thông tin theo nguồn đã chọn:

MAT1204 — Phương pháp nghiên cứu khoa học (QD3568-2023)
Điều kiện tiên quyết theo dòng nguồn: Có ghi điều kiện trong nguồn
[1] MAT3507
MAT3514

Trạng thái: verified theo sign-off cấp dự án đã ghi trong nguồn; không phải chứng nhận của trường.

Thông tin theo nguồn không kết luận bạn đủ điều kiện đăng ký học phần.

Nguồn [1]: 104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf; trang PDF 10; /hus/sources/bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab?page=10#page=10; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.

**Nguồn trả về:**

- [1] 104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf; review=verified; loại=pdf; mở=/hus/sources/bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab?page=10#page=10

> {"entry_id": 499, "curriculum_id": 3, "group_key": "IV", "source_row_number": 25, "course_code": "MAT1204", "credits_in_source": 3, "prerequisite_source_text": "MAT3507\nMAT3514", "prerequisite_parse_status": "normalized", "pdf_document": "104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf", "pdf_page": 10}

### SV30-017 — KHMTTT / f3

**Câu hỏi:** Nội dung MAT1204: Tài liệu và cấu trúc bằng chứng?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.

Tổng quan tham khảo: [1]
Phương pháp nghiên cứu khoa học tiếp cận việc tạo tri thức bằng một chuỗi có thể truy vết từ câu hỏi đến bằng chứng và kết luận. Nội dung tham khảo phân biệt mục tiêu mô tả, giải thích và so sánh; nhấn mạnh vai trò của tài liệu, thiết kế phương pháp, quản lý dữ liệu và trình bày giới hạn của lập luận. [1]
Các chủ đề tham khảo: [1]
- Câu hỏi, phạm vi và khái niệm [1]
- Tài liệu và cấu trúc bằng chứng [1]
- Thiết kế phương pháp và quản lý dữ liệu [1]
- Lập luận và liêm chính trong báo cáo [1]

Câu hỏi, phạm vi và khái niệm [2]
Câu hỏi nghiên cứu xác định hiện tượng, đối tượng và kiểu hiểu biết cần đạt, còn phạm vi giới hạn điều có thể kết luận. Một khái niệm trừu tượng cần được định nghĩa và gắn với dấu hiệu quan sát phù hợp để tránh thu thập dữ liệu không trả lời được câu hỏi ban đầu. [2]
Khái niệm thành phần: câu hỏi nghiên cứu; phạm vi; khái niệm; thao tác hóa. [2]
Ví dụ minh họa do AI biên soạn: Nghiên cứu về thói quen đọc phân biệt số lần mượn sách với thời gian đọc thực tế vì hai chỉ báo biểu diễn những khía cạnh khác nhau của khái niệm. [2]

Tài liệu và cấu trúc bằng chứng [3]
Tổng quan tài liệu đặt các công trình trong quan hệ về câu hỏi, phương pháp và kết quả thay vì nối các bản tóm tắt rời nhau. Phân biệt công trình gốc với lời dẫn lại giúp truy nguồn một phát biểu và nhận diện chỗ còn bất đồng hoặc thiếu dữ liệu. [3]
Khái niệm thành phần: công trình gốc; tổng quan tài liệu; trích dẫn; khoảng trống tri thức. [3]
Ví dụ minh họa do AI biên soạn: Hai bài cùng nghiên cứu một hiện tượng có kết quả khác nhau vì dùng nhóm đối tượng và cách đo khác; bảng đối chiếu phương pháp làm rõ nguồn khác biệt. [3]

Thiết kế phương pháp và quản lý dữ liệu [4]
Phương pháp phải liên kết câu hỏi với cách tạo và phân tích bằng chứng, đồng thời chỉ rõ giả định. Lưu dữ liệu gốc, phiên bản xử lý và quyết định loại bỏ giúp người khác hiểu quá trình hình thành kết quả; kết luận không thể mạnh hơn thiết kế cho phép. [4]
Khái niệm thành phần: thiết kế nghiên cứu; giả định; dữ liệu gốc; khả năng tái lập. [4]
Ví dụ minh họa do AI biên soạn: Một nghiên cứu quan sát ghi nhận quan hệ giữa hai biến vẫn cần nêu các yếu tố chưa kiểm soát, vì dữ liệu tương quan chưa xác lập được tác động nhân quả. [4]

Lập luận và liêm chính trong báo cáo [5]
Báo cáo tách câu hỏi, phương pháp, kết quả và diễn giải để người đọc nhận ra điều đã quan sát và điều được suy ra. Trích nguồn chính xác, mô tả giới hạn và không lược bỏ kết quả trái mong đợi là các cách bảo vệ tính kiểm tra được của tri thức. [5]
Khái niệm thành phần: kết quả; diễn giải; liêm chính; giới hạn nghiên cứu. [5]
Ví dụ minh họa do AI biên soạn: Một phép đo không khớp giả thuyết ban đầu vẫn được báo cáo cùng điều kiện thực hiện, nhờ vậy người đọc thấy cả bằng chứng thuận và bằng chứng bất lợi. [5]

**Nguồn trả về:**

- [1] kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; review=needs_review; loại=ai; mở=không có link

> Tổng quan tham khảo:
> Phương pháp nghiên cứu khoa học tiếp cận việc tạo tri thức bằng một chuỗi có thể truy vết từ câu hỏi đến bằng chứng và kết luận. Nội dung tham khảo phân biệt mục tiêu mô tả, giải thích và so sánh; nhấn mạnh vai trò của tài liệu, thiết kế phương pháp, quản lý dữ liệu và trình bày giới hạn của lập luận.
> Các chủ đề tham khảo:
> - Câu hỏi, phạm vi và khái niệm
> - Tài liệu và cấu trúc bằng chứng
> - Thiết kế phương pháp và quản lý dữ liệu
> - Lập luận và liêm chính trong báo cáo

- [2] kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; review=needs_review; loại=ai; mở=không có link

> Câu hỏi, phạm vi và khái niệm
> Câu hỏi nghiên cứu xác định hiện tượng, đối tượng và kiểu hiểu biết cần đạt, còn phạm vi giới hạn điều có thể kết luận. Một khái niệm trừu tượng cần được định nghĩa và gắn với dấu hiệu quan sát phù hợp để tránh thu thập dữ liệu không trả lời được câu hỏi ban đầu.
> Khái niệm thành phần: câu hỏi nghiên cứu; phạm vi; khái niệm; thao tác hóa.
> Ví dụ minh họa do AI biên soạn: Nghiên cứu về thói quen đọc phân biệt số lần mượn sách với thời gian đọc thực tế vì hai chỉ báo biểu diễn những khía cạnh khác nhau của khái niệm.

- [3] kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; review=needs_review; loại=ai; mở=không có link

> Tài liệu và cấu trúc bằng chứng
> Tổng quan tài liệu đặt các công trình trong quan hệ về câu hỏi, phương pháp và kết quả thay vì nối các bản tóm tắt rời nhau. Phân biệt công trình gốc với lời dẫn lại giúp truy nguồn một phát biểu và nhận diện chỗ còn bất đồng hoặc thiếu dữ liệu.
> Khái niệm thành phần: công trình gốc; tổng quan tài liệu; trích dẫn; khoảng trống tri thức.
> Ví dụ minh họa do AI biên soạn: Hai bài cùng nghiên cứu một hiện tượng có kết quả khác nhau vì dùng nhóm đối tượng và cách đo khác; bảng đối chiếu phương pháp làm rõ nguồn khác biệt.

- [4] kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; review=needs_review; loại=ai; mở=không có link

> Thiết kế phương pháp và quản lý dữ liệu
> Phương pháp phải liên kết câu hỏi với cách tạo và phân tích bằng chứng, đồng thời chỉ rõ giả định. Lưu dữ liệu gốc, phiên bản xử lý và quyết định loại bỏ giúp người khác hiểu quá trình hình thành kết quả; kết luận không thể mạnh hơn thiết kế cho phép.
> Khái niệm thành phần: thiết kế nghiên cứu; giả định; dữ liệu gốc; khả năng tái lập.
> Ví dụ minh họa do AI biên soạn: Một nghiên cứu quan sát ghi nhận quan hệ giữa hai biến vẫn cần nêu các yếu tố chưa kiểm soát, vì dữ liệu tương quan chưa xác lập được tác động nhân quả.

- [5] kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; review=needs_review; loại=ai; mở=không có link

> Lập luận và liêm chính trong báo cáo
> Báo cáo tách câu hỏi, phương pháp, kết quả và diễn giải để người đọc nhận ra điều đã quan sát và điều được suy ra. Trích nguồn chính xác, mô tả giới hạn và không lược bỏ kết quả trái mong đợi là các cách bảo vệ tính kiểm tra được của tri thức.
> Khái niệm thành phần: kết quả; diễn giải; liêm chính; giới hạn nghiên cứu.
> Ví dụ minh họa do AI biên soạn: Một phép đo không khớp giả thuyết ban đầu vẫn được báo cáo cùng điều kiện thực hiện, nhờ vậy người đọc thấy cả bằng chứng thuận và bằng chứng bất lợi.

### SV30-018 — KHMTTT / f3

**Câu hỏi:** Hồ sơ môn MAT1204 có mục tiêu học tập nào?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.

Mục tiêu tham khảo do AI đề xuất: [1]
- Chuyển một mối quan tâm thành câu hỏi có đối tượng và phạm vi rõ ràng. [1]
- Đối chiếu tài liệu theo phương pháp, nguồn gốc và quan hệ giữa các kết quả. [1]
- Liên hệ thiết kế nghiên cứu với loại kết luận mà bằng chứng có thể hỗ trợ. [1]
- Tổ chức dữ liệu và báo cáo để giả định, kết quả và giới hạn có thể truy vết. [1]

**Nguồn trả về:**

- [1] kiến thức AI — MAT1204 — Phương pháp nghiên cứu khoa học; review=needs_review; loại=ai; mở=không có link

> Mục tiêu tham khảo do AI đề xuất:
> - Chuyển một mối quan tâm thành câu hỏi có đối tượng và phạm vi rõ ràng.
> - Đối chiếu tài liệu theo phương pháp, nguồn gốc và quan hệ giữa các kết quả.
> - Liên hệ thiết kế nghiên cứu với loại kết luận mà bằng chứng có thể hỗ trợ.
> - Tổ chức dữ liệu và báo cáo để giả định, kết quả và giới hạn có thể truy vết.

### SV30-019 — KHDL / f1

**Câu hỏi:** Cho em hỏi cơ hội nghề nghiệp ngành KHDL như thế nào?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

nhà quản lý dữ liệu, chuyên gia phân tích dữ liệu, chuyên gia dữ liệu lớn, chuyên gia tư vấn tại các doanh nghiệp cho các dự án quản lý và khai thác dữ iệu; [1]

Lập trình viên, quản trị dự án, trưởng phòng (tùy theo năng lực) tại các doanh nghiệp, trung tâm công nghệ thông tin; [2]

Nghiên cứu viên tại các trung tâm nghiên cứu và phát triển (R&D) trong lĩnh vực khoa học dữ liệu; [3]

Giảng viên, nghiên cứu viên, chuyên viên kỹ thuật tại các đơn vị trường, viện trong lĩnh vực khoa học dữ liệu. [4]

**Nguồn trả về:**

- [1] Khoa học Dữ liệu; review=include; loại=web; mở=http://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu

> nhà quản lý dữ liệu, chuyên gia phân tích dữ liệu, chuyên gia dữ liệu lớn, chuyên gia tư vấn tại các doanh nghiệp cho các dự án quản lý và khai thác dữ iệu;

- [2] Khoa học Dữ liệu; review=include; loại=web; mở=http://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu

> Lập trình viên, quản trị dự án, trưởng phòng (tùy theo năng lực) tại các doanh nghiệp, trung tâm công nghệ thông tin;

- [3] Khoa học Dữ liệu; review=include; loại=web; mở=http://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu

> Nghiên cứu viên tại các trung tâm nghiên cứu và phát triển (R&D) trong lĩnh vực khoa học dữ liệu;

- [4] Khoa học Dữ liệu; review=include; loại=web; mở=http://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu

> Giảng viên, nghiên cứu viên, chuyên viên kỹ thuật tại các đơn vị trường, viện trong lĩnh vực khoa học dữ liệu.

### SV30-020 — KHDL / f1

**Câu hỏi:** Khả năng học tiếp của sinh viên ngành KHDL ra sao?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.

Sau khi tốt nghiệp, sinh viên còn có khả năng theo học sau đại học tại các khoa hoặc các trường Đại học khác có uy tín trong nước cũng như trên thế giới, tham gia nghiên cứu, triển khai ứng dụng khoa học công nghệ trong các trường ĐH, viện nghiên cứu, doanh nghiệp và cơ sở sản xuất. [1]

**Nguồn trả về:**

- [1] Khoa học Dữ liệu; review=include; loại=web; mở=http://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu

> Sau khi tốt nghiệp, sinh viên còn có khả năng theo học sau đại học tại các khoa hoặc các trường Đại học khác có uy tín trong nước cũng như trên thế giới, tham gia nghiên cứu, triển khai ứng dụng khoa học công nghệ trong các trường ĐH, viện nghiên cứu, doanh nghiệp và cơ sở sản xuất.

### SV30-021 — KHDL / f2

**Câu hỏi:** MAT2034 có bao nhiêu tín chỉ?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Thông tin theo nguồn đã chọn:

MAT2034 — Giải tích số (QD3569-2023)
Số tín chỉ: 3

Trạng thái xác minh: draft_unverified; dữ kiện chép từ nguồn, chưa xác minh học vụ.

Nguồn [1]: 105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf; trang PDF 10; /hus/sources/b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2?page=10#page=10; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.

**Nguồn trả về:**

- [1] 105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf; review=draft_unverified; loại=pdf; mở=/hus/sources/b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2?page=10#page=10

> {"entry_id": 563, "curriculum_id": 4, "group_key": "V.1", "source_row_number": 26, "course_code": "MAT2034", "credits_in_source": 3, "prerequisite_source_text": "MAT2502\nMAT2403", "prerequisite_parse_status": "normalized", "pdf_document": "105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf", "pdf_page": 10}

### SV30-022 — KHDL / f2

**Câu hỏi:** Theo chương trình đã lưu, tiên quyết của MAT2034 là gì?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Thông tin theo nguồn đã chọn:

MAT2034 — Giải tích số (QD3569-2023)
Điều kiện tiên quyết theo dòng nguồn: Có ghi điều kiện trong nguồn
[1] MAT2502
MAT2403

Trạng thái xác minh: draft_unverified; dữ kiện chép từ nguồn, chưa xác minh học vụ.

Thông tin theo nguồn không kết luận bạn đủ điều kiện đăng ký học phần.

Nguồn [1]: 105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf; trang PDF 10; /hus/sources/b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2?page=10#page=10; Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.

**Nguồn trả về:**

- [1] 105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf; review=draft_unverified; loại=pdf; mở=/hus/sources/b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2?page=10#page=10

> {"entry_id": 563, "curriculum_id": 4, "group_key": "V.1", "source_row_number": 26, "course_code": "MAT2034", "credits_in_source": 3, "prerequisite_source_text": "MAT2502\nMAT2403", "prerequisite_parse_status": "normalized", "pdf_document": "105.-Khoa-học-dữ-liệu-chuẩn final QĐ 3569 Scan.pdf", "pdf_page": 10}

### SV30-023 — KHDL / f3

**Câu hỏi:** Nội dung MAT2034: Nội suy và xấp xỉ hàm?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.

Tổng quan tham khảo: [1]
Giải tích số nghiên cứu cách tính gần đúng các đại lượng toán học bằng thuật toán hữu hạn. Nội dung tham khảo phân biệt độ nhạy của bài toán với tính ổn định của phương pháp, rồi kết nối giải phương trình, nội suy và tích phân với sai số; kết quả số luôn được hiểu cùng giả định và nguồn sai lệch. [1]
Các chủ đề tham khảo: [1]
- Sai số, điều kiện và ổn định [1]
- Nghiệm phi tuyến và phép lặp [1]
- Hệ tuyến tính và phép phân rã [1]
- Nội suy và xấp xỉ hàm [1]
- Tích phân số và ước lượng sai lệch [1]

Nghiệm phi tuyến và phép lặp [2]
Phương pháp chia đôi giữ một khoảng chứa nghiệm dựa trên tính liên tục và đổi dấu, còn Newton sử dụng thông tin đạo hàm để cập nhật xấp xỉ. Tốc độ hội tụ và độ tin cậy phụ thuộc điều kiện; sai số dư nhỏ chưa chắc đồng nghĩa nghiệm xấp xỉ gần nghiệm thật nếu bài toán nhạy. [2]
Khái niệm thành phần: chia đôi; Newton; sai số dư; hội tụ. [2]
Ví dụ minh họa do AI biên soạn: Với một hàm rất phẳng gần nghiệm, giá trị hàm có thể nhỏ trên một đoạn khá rộng, nên chỉ nhìn độ nhỏ của giá trị hàm dễ đánh giá quá cao độ chính xác vị trí nghiệm. [2]

Nội suy và xấp xỉ hàm [3]
Nội suy buộc hàm xấp xỉ đi qua các nút dữ liệu, còn chất lượng giữa các nút phụ thuộc độ trơn, vị trí nút và dạng hàm. Đa thức bậc cao trên các nút cách đều có thể dao động mạnh, nên chia khoảng và dùng đa thức từng đoạn thường là một lựa chọn quan trọng. [3]
Khái niệm thành phần: nút nội suy; đa thức nội suy; spline; dao động. [3]
Ví dụ minh họa do AI biên soạn: Một đường nội suy đi chính xác qua mọi số đo vẫn có thể tạo đỉnh giả giữa hai điểm, cho thấy khớp tại nút chưa đủ bảo đảm hình dạng hợp lý. [3]

Tích phân số và ước lượng sai lệch [4]
Công thức tích phân số thay diện tích dưới hàm bằng tổng có trọng số các giá trị hàm. Độ chính xác phụ thuộc độ trơn và kích thước bước; so sánh các mức chia lưới có thể gợi ý độ ổn định của xấp xỉ nhưng cần thận trọng với điểm kỳ dị hoặc dao động nhanh. [4]
Khái niệm thành phần: quy tắc hình thang; Simpson; bước lưới; tích phân thích nghi. [4]
Ví dụ minh họa do AI biên soạn: Một hàm có đỉnh rất hẹp giữa hai nút có thể bị bỏ sót trên lưới thưa, dù các giá trị tại nút đều nhỏ và tổng có vẻ đã ổn định. [4]

**Nguồn trả về:**

- [1] kiến thức AI — MAT2034 — Giải tích số; review=needs_review; loại=ai; mở=không có link

> Tổng quan tham khảo:
> Giải tích số nghiên cứu cách tính gần đúng các đại lượng toán học bằng thuật toán hữu hạn. Nội dung tham khảo phân biệt độ nhạy của bài toán với tính ổn định của phương pháp, rồi kết nối giải phương trình, nội suy và tích phân với sai số; kết quả số luôn được hiểu cùng giả định và nguồn sai lệch.
> Các chủ đề tham khảo:
> - Sai số, điều kiện và ổn định
> - Nghiệm phi tuyến và phép lặp
> - Hệ tuyến tính và phép phân rã
> - Nội suy và xấp xỉ hàm
> - Tích phân số và ước lượng sai lệch

- [2] kiến thức AI — MAT2034 — Giải tích số; review=needs_review; loại=ai; mở=không có link

> Nghiệm phi tuyến và phép lặp
> Phương pháp chia đôi giữ một khoảng chứa nghiệm dựa trên tính liên tục và đổi dấu, còn Newton sử dụng thông tin đạo hàm để cập nhật xấp xỉ. Tốc độ hội tụ và độ tin cậy phụ thuộc điều kiện; sai số dư nhỏ chưa chắc đồng nghĩa nghiệm xấp xỉ gần nghiệm thật nếu bài toán nhạy.
> Khái niệm thành phần: chia đôi; Newton; sai số dư; hội tụ.
> Ví dụ minh họa do AI biên soạn: Với một hàm rất phẳng gần nghiệm, giá trị hàm có thể nhỏ trên một đoạn khá rộng, nên chỉ nhìn độ nhỏ của giá trị hàm dễ đánh giá quá cao độ chính xác vị trí nghiệm.

- [3] kiến thức AI — MAT2034 — Giải tích số; review=needs_review; loại=ai; mở=không có link

> Nội suy và xấp xỉ hàm
> Nội suy buộc hàm xấp xỉ đi qua các nút dữ liệu, còn chất lượng giữa các nút phụ thuộc độ trơn, vị trí nút và dạng hàm. Đa thức bậc cao trên các nút cách đều có thể dao động mạnh, nên chia khoảng và dùng đa thức từng đoạn thường là một lựa chọn quan trọng.
> Khái niệm thành phần: nút nội suy; đa thức nội suy; spline; dao động.
> Ví dụ minh họa do AI biên soạn: Một đường nội suy đi chính xác qua mọi số đo vẫn có thể tạo đỉnh giả giữa hai điểm, cho thấy khớp tại nút chưa đủ bảo đảm hình dạng hợp lý.

- [4] kiến thức AI — MAT2034 — Giải tích số; review=needs_review; loại=ai; mở=không có link

> Tích phân số và ước lượng sai lệch
> Công thức tích phân số thay diện tích dưới hàm bằng tổng có trọng số các giá trị hàm. Độ chính xác phụ thuộc độ trơn và kích thước bước; so sánh các mức chia lưới có thể gợi ý độ ổn định của xấp xỉ nhưng cần thận trọng với điểm kỳ dị hoặc dao động nhanh.
> Khái niệm thành phần: quy tắc hình thang; Simpson; bước lưới; tích phân thích nghi.
> Ví dụ minh họa do AI biên soạn: Một hàm có đỉnh rất hẹp giữa hai nút có thể bị bỏ sót trên lưới thưa, dù các giá trị tại nút đều nhỏ và tổng có vẻ đã ổn định.

### SV30-024 — KHDL / f3

**Câu hỏi:** Hồ sơ môn MAT2034 có mục tiêu học tập nào?

**Kết quả:** HTTP=200; Gemini used=True; fallback=None; model trả về=gemini-3.5-flash-lite. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Nội dung tham khảo do AI biên soạn; chưa đối chiếu đề cương chính thức HUS. Ví dụ chỉ minh họa kiến thức, không phải yêu cầu học hoặc thi của trường.

Mục tiêu tham khảo do AI đề xuất: [1]
- Phân biệt nguồn sai số, độ nhạy bài toán và tính ổn định thuật toán. [1]
- Giải thích điều kiện và hành vi hội tụ của phương pháp tìm nghiệm. [1]
- Liên hệ phân rã ma trận, chọn trụ và sai số dư khi giải hệ tuyến tính. [1]
- Phân tích ảnh hưởng của vị trí nút và độ trơn đến nội suy. [1]
- Diễn giải kết quả tích phân số cùng bước lưới và khả năng bỏ sót cấu trúc hàm. [1]

**Nguồn trả về:**

- [1] kiến thức AI — MAT2034 — Giải tích số; review=needs_review; loại=ai; mở=không có link

> Mục tiêu tham khảo do AI đề xuất:
> - Phân biệt nguồn sai số, độ nhạy bài toán và tính ổn định thuật toán.
> - Giải thích điều kiện và hành vi hội tụ của phương pháp tìm nghiệm.
> - Liên hệ phân rã ma trận, chọn trụ và sai số dư khi giải hệ tuyến tính.
> - Phân tích ảnh hưởng của vị trí nút và độ trơn đến nội suy.
> - Diễn giải kết quả tích phân số cùng bước lưới và khả năng bỏ sót cấu trúc hàm.

### SV30-025 — Toán học / control

**Câu hỏi:** Xin chào bạn!

**Kết quả:** HTTP=None; Gemini used=False; fallback=basic_chat; model trả về=None. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Chào bạn! Bạn muốn tìm hiểu về ngành học, chương trình đào tạo hay một học phần?

**Nguồn trả về:**

Không có nguồn.

### SV30-026 — KHMTTT / control

**Câu hỏi:** Chào bạn, chúc bạn một ngày tốt lành!

**Kết quả:** HTTP=None; Gemini used=False; fallback=basic_chat; model trả về=None. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Chào bạn! Bạn muốn tìm hiểu về ngành học, chương trình đào tạo hay một học phần?

**Nguồn trả về:**

Không có nguồn.

### SV30-027 — KHDL / control

**Câu hỏi:** Môn đó có bao nhiêu tín chỉ?

**Kết quả:** HTTP=None; Gemini used=False; fallback=not_answered; model trả về=None. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Chưa có thông tin đủ căn cứ để trả lời. Cần mã học phần và phiên bản chương trình.

**Nguồn trả về:**

Không có nguồn.

### SV30-028 — KHDL / control

**Câu hỏi:** Số tín chỉ MAT9999?

**Kết quả:** HTTP=None; Gemini used=False; fallback=not_answered; model trả về=None. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Chưa có thông tin đủ căn cứ để trả lời. Không có môn này trong ngành và phiên bản đã chọn.

**Nguồn trả về:**

Không có nguồn.

### SV30-029 — KHMTTT / control

**Câu hỏi:** Mục tiêu MAT1204?

**Kết quả:** HTTP=None; Gemini used=False; fallback=not_answered; model trả về=None. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Chưa có thông tin đủ căn cứ để trả lời. Cần bật cho phép kiến thức AI tham khảo để dùng dữ liệu F3 AI sinh.

**Nguồn trả về:**

Không có nguồn.

### SV30-030 — Toán tin / control

**Câu hỏi:** Hãy chuyển tiền giúp tôi.

**Kết quả:** HTTP=None; Gemini used=False; fallback=not_answered; model trả về=None. **Nhóm review: pending.**

**Đáp án hiển thị thực tế (gồm cả fallback):**

Chưa có thông tin đủ căn cứ để trả lời. Phạm vi hỏi đáp không hỗ trợ xếp hạng, chọn môn hoặc thao tác bên ngoài.

**Nguồn trả về:**

Không có nguồn.
