# Bổ sung nguồn cho 21 khoảng thiếu F3 — 13/11/2026

Nhánh `hus-llm-rag`, nền `f61b0fd` + WIP local. Lượt r2 bổ sung đoạn đối chiếu
trực tiếp cho **19 partial và 2 open** của ma trận r1; giữ nguyên 15 dòng core cũ,
định nghĩa trạng thái và toàn bộ item/hash của snapshot v4.

**36/36 nay có căn cứ cho khái niệm cốt lõi** (`core_supported`). Điều này
**không xác nhận đủ mọi câu/ví dụ, năng lực người học hoặc đề cương/hiệu lực HUS**.
Các giới hạn đó vẫn ghi từng dòng, không chuyển thành `official` hoặc học vụ đã
nghiệm thu. Reviewer là root AI đã thấy nguồn/runtime, human0, không độc lập.

[Ma trận mới](../data/hus/review/field_edition_20261113_r2/field_matrix.json) ·
[21 thay đổi và trạng thái cũ](../data/hus/review/field_edition_20261113_r2/delta.json) ·
[53 locator/hash](../data/hus/review/field_edition_20261113_r2/anchors.json) ·
[Receipt](../data/hus/qa/20261113/field_edition_r2/report.json).

## Các đoạn mới đối chiếu

| Hồ sơ | Số mục bổ sung | Nguồn và giới hạn |
| --- | --- | --- |
| MAT1204 — KHMTTT | 6 | [Purdue](https://owl.purdue.edu/owl/research_and_citation/conducting_research/writing_a_literature_review.html) và [Cornell](https://guides.library.cornell.edu/critically_analyzing/home) hỗ trợ tổng hợp/so sánh phương pháp, truy nguồn và khoảng trống; [GMU](https://writingcenter.gmu.edu/writing-resources/research-based-writing/how-to-write-a-research-question) hỗ trợ thu hẹp câu hỏi. [OpenStax 2e](https://openstax.org/books/psychology-2e/pages/2-3-analyzing-findings) có thao tác hóa, tương quan/nhân quả và giới hạn thiết kế. Không chuyển mọi quy tắc viết luận thành quy tắc phổ quát của nghiên cứu khoa học. |
| MAT2034 — KHDL | 4 | [SciPy bisect](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.bisect.html) ghi điều kiện liên tục/đổi dấu và tolerance; [FNC Runge](https://fncbook.com/python/stability-1/) có sai số/nút cách đều/dao động. Giữ các giả thiết Newton cục bộ, độ trơn và số học hữu hạn; không bảo đảm hội tụ toàn cục. |
| MAT2300 — Toán học | 5 | MIT 2011 có [ma trận và hợp thành](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/resources/mit18_06scf11_ses3-6sum/), [không gian con](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/resources/mit18_06scf11_ses1-5sum/); [Margalit–Rabinoff 2019](https://textbooks.math.gatech.edu/ila/bases-as-coord-systems.html) có tọa độ duy nhất và đổi cơ sở. Giới hạn không gian vectơ thực hữu hạn chiều; không suy mọi mệnh đề trừu tượng. |
| MAT1202 — Toán Tin | 6 | [Liskov–Wing 1994](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf), trang vật lý1/13, có quan hệ subtype và điều kiện hành vi. [MIT 6.005 năm2014](https://web.mit.edu/6.005/www/fa14/classes/14-inheritance/) đối chiếu kế thừa/hợp thành; [2016](https://web.mit.edu/6.005/www/fa16/classes/03-testing/) có blackbox/boundary/integration; [Martin 2014](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html) giải thích trách nhiệm/cohesion/coupling. Đây là hướng dẫn thiết kế theo ngữ cảnh; không mượn MAT3372 hoặc yêu cầu Java của HUS. |

MIT2011 khác MIT2010 trong hồ sơ; Oracle JDK8 ở lượt trước và các tài liệu mới
là **reference bổ sung**, không đổi edition HUS/link runtime. PDF GMU có footer
©2024 dù tên file chứa2018; SciPy là bản docs1.18.0 đã chụp. Registry ghim URL,
thời điểm, byte/hash và đường dẫn text; không dùng homepage thay đoạn đối chiếu.

## Q001 và chuỗi áp dụng vẫn còn mở

Đã kiểm thêm [bài HUS20/03/2014](https://hus.vnu.edu.vn/tin-tuc-su-kien/dao-tao-tuyen-sinh/cac-nganh-dao-tao-dai-hoc-tai-khoa-toan-co-tin-hoc-52443)
và [tư vấn tuyển sinh VNU2012](https://vnu.edu.vn/truc-tuyen-tu-van-tuyen-sinh-dai-hoc-2012-tren-website-dhqghn-post12528.html).
Chúng bổ sung mốc ngành được đưa vào danh mục2012 và cơ chế hỗ trợ từ khóa2012;
chưa ghi trực tiếp **tuyển khóa đầu hệ chuẩn**. Chữ “chuẩn/tài năng” ở phần ngành
Toán không được chuyển sang KHMTTT; cơ chế tài chính không tự xác định hệ.

PDF chuẩn2012/QĐ4115 đã có ở r1 vẫn là bằng chứng lịch sử, chưa có chuỗi ban hành/
sửa đổi/áp dụng theo cohort nối tới edition đang khai báo2023. Bản2022 thiếu số/
ngày quyết định chưa giải quyết được điều này. Một URL HUS trả200 nhưng body
gộp nhiều ngành cũng không xác nhận đúng chương trình từ tên đường dẫn.
Giữ `program_variant=unknown`, không suy không có văn bản sửa đổi hoặc thay gold.
[Chain và giới hạn](../data/hus/review/field_edition_20261113_r2/q001_chain.json).

## Kiểm chứng và bước tiếp theo

- Kiểm đủ36 pointer/item hash và53 locator range/hash; **2.893 file cũ nguyên SHA**.
  Có21 HTTP capture200, ba lỗi: Cornell URL cũ404, GMU HTML502, URL tọa độ đoán404.
  Đã lấy PDF GMU từ link chính thức và trang tọa độ đúng; giữ cả lịch sử lỗi.
- Render12 trang, thực sự xem6 ảnh: Liskov–Wing1/13, MIT transformations3/4,
  MIT subspaces2, GMU1. Không nhận là đã đọc/xem toàn bộ năm PDF.
- Ba kiểm đại số minh họa chính xác cho thứ tự co/quay, đường thẳng không qua
  gốc và hai hệ tọa độ. Đây là kiểm root AI, không là trích dẫn hoặc nghiệm thu
  độc lập mọi ví dụ. Không thêm/lặp test repository khi runtime không đổi.
- Cached replay giữ điểm A7S23/24–32/36–12/12, pins A7S vẫn lịch sử; L5 prepared
  r4 còn khớp. Cả290 F3 vẫn AI/needs_review, official fields null; không tích hợp
  nguồn mới vào retrieval, chọn release hoặc stage/commit/push/PR/Actions/deploy.

Review manifest: `77b49fd7bb847b568416cd8336733055e0b467c583a80383016eee813e6f57a1`.
QA manifest: `a44a270c56ad3e95c14bffe2fab94039e514b462e2bc83d6d5cb2781a017cc4e`.

Tiếp theo: review đầy đủ từng câu/ví dụ và áp dụng học vụ với người có chuyên môn;
tìm văn bản nối tuyển khóa đầu–hệ chuẩn/cohort. Nếu sửa nội dung hoặc đưa reference
vào chatbot, tạo candidate/lượt tích hợp và kiểm rollback riêng, không chép đè v4
hoặc đổi điểm cũ. Trong lượt này có **một call Google riêng đã được người dùng cấp**,
không dùng để tạo/review nội dung F3: [kết quả key bị Google báo lộ](RAG_GOOGLE_DIAGNOSTIC_2026_11_13.md).
