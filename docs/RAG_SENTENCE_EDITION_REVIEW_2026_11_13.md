# Gói review từng câu/ví dụ và chuỗi áp dụng — 13/11/2026

Nhánh `hus-llm-rag`, chỉ local. Người dùng xác nhận **chưa có reviewer chuyên môn, chuẩn bị gói trước**. Đã lập gói cho bốn hồ sơ đang có ma trận; **human/expert review vẫn pending**, không nghiệm thu toàn bộ 174 mã/290 hồ sơ hoặc nâng nhãn official/academic_verified.

## Gói đã chuẩn bị

| Thành phần | Phạm vi |
| --- | --- |
| Trường nội dung | **58**: 4 tổng quan, 18 giải thích, 18 ví dụ, 18 mục tiêu. |
| Câu cần review | **80**, giữ nguyên text, JSON pointer, offset và hash của câu/trường/record/file. Một câu có thể chứa nhiều mệnh đề; phải kiểm tất cả. |
| Từ khóa/tiêu đề | 18 unit giữ nguyên concept tags/title để đối chiếu ma trận cũ; không tính tags là câu đã nghiệm thu. |
| Reference | Kiểm lại **51 anchor** bằng hash nguồn/text và range; từng câu nối bundle anchor của trường, chưa chứng minh entailment mọi mệnh đề. |
| Ví dụ | 18 minh họa AI, có ghi giả thiết. **12 kiểm/phân tích minh họa** riêng, không gọi là regression repository hay review chuyên môn độc lập. |

[Danh sách 80 câu](../data/hus/review/sentence_edition_20261113_r1/sentences.json), [58 trường và ghi chú](../data/hus/review/sentence_edition_20261113_r1/fields.json), [reference/locator](../data/hus/review/sentence_edition_20261113_r1/reference_anchors.json), [registry URL/hash](../data/hus/review/sentence_edition_20261113_r1/reference_registry.json), [kiểm minh họa](../data/hus/review/sentence_edition_20261113_r1/illustration_checks.json).

Không thay định nghĩa hoặc 36 trạng thái `core_supported` cũ. Những trạng thái đó chỉ xác nhận khái niệm cốt lõi, không chứng minh đủ mọi câu/ví dụ, kết quả học tập hoặc yêu cầu HUS. Tổng quan là tổng hợp AI; mục tiêu là ý định của nội dung tham khảo, chưa chứng minh người học đạt năng lực.

## Ba ví dụ cần chốt wording/giả thiết trước candidate

| Hồ sơ | Vị trí | Điểm cần reviewer quyết định |
| --- | --- | --- |
| MAT1204 — KHMTTT | `/profile/units/1/example` | “Kết quả khác nhau vì nhóm/cách đo khác” cần được hiểu là tình huống giả định hoặc khả năng giải thích, không gán nguyên nhân cho hai nghiên cứu thực tế khi chưa có bằng chứng. |
| MAT2300 — Toán học | `/profile/units/2/example` | Tập vectơ sinh đường thẳng phải có vectơ khác 0. Tập chỉ gồm 0 sinh không gian chiều 0; cần chốt phạm vi của cách diễn đạt hiện tại. |
| MAT2300 — Toán học | `/profile/units/4/example` | Cách nói kernel/ảnh cần phép chiếu tuyến tính lên mặt phẳng qua gốc; chiếu lên `z=1` là affine. Tính toàn ánh còn phụ thuộc đối miền. |

Đây là **điểm cần phân xử**, chưa tự kết luận ba câu sai hoặc sửa v4. Các giả thiết khác đã ghi theo trường: hệ phải tương thích khi đếm chiều nghiệm; biến đổi hàng trên cả hệ; Newton là hội tụ cục bộ; residual tuyệt đối phụ thuộc scale; Runge không xảy ra với mọi hàm; tách lớp/đóng gói/test không tự bảo đảm invariant hay thay thế backend an toàn. [Ghi chú đầy đủ](../data/hus/review/sentence_edition_20261113_r1/fields.json).

## Bằng chứng mới về văn bản áp dụng

Từ [trang HUS đúng Khoa](https://hus.vnu.edu.vn/dao-tao/bac-dai-hoc/toan-toan-ung-dung-va-tin-hoc), tải được **bốn binary PDF** chuẩn; tất cả khớp SHA với bản trong `docs/pdf`. Đã xem trang vật lý 1–2 của mỗi PDF, có thông tin ban hành/điều khoản cohort; không nhận là đọc toàn bộ nội dung bốn PDF hoặc xác minh chữ ký số.

| Ngành | Văn bản trên PDF | Điều 2 |
| --- | --- | --- |
| KHMTTT | [3568/QĐ-ĐHKHTN, 18/10/2023](https://hus.vnu.edu.vn/DATA/IMAGES/2024/06/104.-khmttt-chuan-final-qd-3568-scan-final.pdf), mã 7480113QTD | Áp dụng từ khóa tuyển sinh 2022. |
| Toán học | [3565/QĐ-ĐHKHTN, 18/10/2023](https://hus.vnu.edu.vn/DATA/IMAGES/2024/06/101.-toan-hoc-chuan-final-qd-3565-scan.pdf), mã 7460101 | Áp dụng từ khóa tuyển sinh 2022. |
| Toán tin | [3567/QĐ-ĐHKHTN, 18/10/2023](https://hus.vnu.edu.vn/DATA/IMAGES/2024/06/103.-toan-tin-chuan-final-qd-3567-scan.pdf), mã 7460117 | Áp dụng từ khóa tuyển sinh 2022. |
| KHDL | [3569/QĐ-ĐHKHTN, 18/10/2023](https://hus.vnu.edu.vn/DATA/IMAGES/2024/06/105.-khoa-hoc-du-lieu-chuan-final-qd-3569-scan.pdf), mã 7460108 | Áp dụng từ khóa tuyển sinh 2022. |

Đã xem lại ảnh bìa/mục lục S06 năm 2024 (capture cũ khớp hash, không tải lại). Bìa ghi QĐ2385 ngày31/07/2024 và tham chiếu CTĐT3568/2023; mã MAT1204 ở mục lục dẫn tới trang52. Đọc lại text trang52–54 cho thấy phần giao nhau về nghiên cứu, nguồn và báo cáo; còn thiếu các mục cơ sở dữ liệu khoa học, vai trò/bản quyền tác giả, công cụ/thuyết trình, làm việc nhóm/tự chủ. Không gắn “đủ đề cương” từ việc khớp mã/tên. Ba hồ sơ còn lại chưa có đối chiếu đề cương chi tiết đúng scope được duyệt; MAT3372 hoặc MAT1202 ở ngành khác không thay thế được. [Đối chiếu](../data/hus/review/sentence_edition_20261113_r1/syllabus_comparison.json).

[Tư vấn VNU2012](https://vnu.edu.vn/truc-tuyen-tu-van-tuyen-sinh-dai-hoc-2012-tren-website-dhqghn-post12528.html) có phát biểu trực tiếp về năm tuyển khóa đầu của **ngành**, nay đã ghim range/hash riêng. Câu đó chưa gắn trực tiếp hệ chuẩn. PDF chuẩn2012 và bài tổng kết2020 là các nút bổ sung; chưa đủ tự suy nhánh hệ cho chunk Q001, tương đương mọi mã ngành hoặc chuỗi thay thế2012→2023. Không mượn CLC2018 để lấp liên kết còn thiếu. Giữ scope unknown và gold cũ.

Chưa xác nhận toàn bộ sửa đổi sau2023/hiệu lực hiện hành. `3568/QĐ-ĐHQGHN/2014` về tổ chức là văn bản khác `3568/QĐ-ĐHKHTN/2023` về CTĐT. Đầu mối đề án2021 vẫn lỗi khi lấy trực tiếp, chỉ mục là lead; không nhận đã có binary. MIT2011/2014/2016, Oracle JDK8 và các reference khác vẫn là bổ sung khái niệm, không đổi edition HUS. [Chuỗi và khoảng thiếu](../data/hus/review/sentence_edition_20261113_r1/q001_chain.json).

## Cách giao reviewer

1. Chọn người có chuyên môn phù hợp từng môn. Ghi tên thật, chuyên môn, phạm vi, ngày và exposure; không gán review AI thành review giảng viên.
2. Sao chép [template](../data/hus/review/sentence_edition_20261113_r1/human_review_template.json) ra **file trả về riêng**; điền manifest hash của gói. Giữ sentence ID/hash; không sửa gói đã seal, text runtime hoặc artifact cũ.
3. Với mỗi câu, kiểm từng mệnh đề/điều kiện/ví dụ từ URL và locator. Ghi `supported_with_assumptions`, `needs_revision`, `insufficient_evidence` hoặc để `pending`, kèm lý do và nguồn. Kiểm reference entailment và áp dụng đề cương HUS thành hai nhận xét riêng; không bỏ câu để làm đầy coverage.
4. Registry có đường dẫn capture/text trong workspace và URL công khai. Capture reference nằm trong `backups` local, không mặc định đi cùng clone/packet; nếu chuyển máy cần bàn giao capture riêng hoặc tải lại/ghi drift. Hash/range của bản cũ không tự chứng minh một trang web đã đổi nội dung.
5. Khi có kết quả, lập quyết định theo câu và phạm vi. Bất kỳ sửa nội dung/reference để dùng trong chatbot đều cần **candidate mới, tích hợp/kiểm và rollback riêng**; không chép đè v4 hoặc đổi điểm/gold cũ.

## Kiểm chứng và trạng thái

**2.971 file bảo vệ nguyên SHA**; không đổi runtime, test cũ, data/gold/run/review cũ. Kiểm đủ58 pointer/field hash,80 sentence range/hash và51 anchor cũ. Replay cached A7R tái hiện điểm cũ; code bindings LLM khớp receipt diagnostic gần nhất. Không inference RAG/Google, chạy lại suite, prepare L5 hoặc thay cờ. V4/lexical/LLMoff, mọi budget đã hết; pins r5 vẫn stale.

Network capture:6 nguồn200 (4PDF+2HTML), một lỗi đề án2021; bảy lỗi sandbox ban đầu giữ riêng, không coi là site hỏng. Web tool không tải được các PDF lớn; direct GET công khai đã lấy được bốn binary. Đã xem8 ảnh mới của bốn CTĐT và2 ảnh bìa/mục lục S06 cũ; không nhận đã xem mọi trang.

[Report gói](../data/hus/review/sentence_edition_20261113_r1/report.json) · [Receipt](../data/hus/qa/20261113/sentence_edition_r1/report.json). Manifest review `5c9755787347a55663c95c774f485db63e369f7767fb01cd9df8747fca8e7203`; QA `765e281376bcb39b241496ded68273c8643ac023b74154084bab3451ca11e3a8`.

Bước tiếp theo của mục này là chỉ định reviewer và nhận review có hash, tiếp tục tìm liên kết tuyển khóa đầu–hệ chuẩn/chuỗi sửa đổi còn mở. Đây là gói chuẩn bị, **chưa phải nghiệm thu chuyên môn hoặc full coverage**. Không stage/commit/push/PR/Actions/deploy.
