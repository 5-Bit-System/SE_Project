# Review AI bộ H2 — 03/11/2026

Đã review 56/56 câu theo quyết định dùng AI của bạn. Không cần chữ ký người thật
cho đợt này; reviewer_kind=ai, số review người thật thực tế vẫn là 0.

53 câu có gold đủ dùng nguyên bản cho đánh giá đã lộ; 3 câu cần sửa gold/rubric.
54/56 mục có dữ kiện/đáp án gốc đủ căn cứ theo tiêu chí source support; Q048 có
dữ kiện đúng nhưng lời giải chưa đủ. Đây là hai tiêu chí khác nhau.

## Sửa trong bản dẫn xuất trước khi đo

| ID | Phát hiện | Xử lý |
| --- | --- | --- |
| H2-Q043 | Gold chỉ nói chương trình có mục tiêu, chưa trình bày mục tiêu | Bổ sung chunk mục tiêu liền sau, cùng nguồn/ngành/edition chưa biết |
| H2-Q044 | Hỏi toàn bộ nhóm việc làm nhưng gold chỉ có một nhóm | Bổ sung ba nhóm cùng nguồn; giữ điều kiện “tùy theo năng lực” |
| H2-Q048 | Ô tiên quyết trống, raw_variants=[] | Nêu status=unknown; không suy thành không có tiên quyết hoặc đủ điều kiện đăng ký |

Bản gốc và worksheet của người review được giữ nguyên. Bản dẫn xuất mới là
[ai_reviewed_exposed_v1](../ai_reviewed_exposed_v1/README.md); sửa trước inference,
không dùng kết quả chạy để đổi đáp án hoặc runtime.

## Trùng ý và nguồn thay thế

Các câu F1 có chủ đề/anchor đã lộ; 12/16 F2 đã có câu hỏi cùng mã/ngành/field ở
evaluation cũ, bốn câu tra tên có cặp mã/tên đã lộ. Cả tám F3 dương đã có đúng
course/field/anchor trong evaluation cũ. Các ca thiếu nguồn, ngoài phạm vi và
opt-in cũng kiểm lại các hành vi đã có. Không có chứng nhận holdout độc lập.

Trong tám gợi ý nguồn thay thế, bốn là phần bổ sung bắt buộc cho Q043/Q044,
bốn không chứng minh thay thế tương đương: Q002 khác hệ tài năng/chuẩn,
Q031 khác hệ CLC/chương trình thường và mốc tuyển sinh; hai chunk Q045 nêu ý
giới thiệu khác. Không ép citation sai scope để tăng điểm.

Q024 có đề cương ứng viên 2021, chưa duyệt và chưa ràng buộc áp dụng cho bản
2023. Từ chối trả lời assessment official của bản 2023 không có nghĩa không tồn
tại tài liệu khác. F3 giữ nhãn AI/opt-in; draft và review dự án không thành xác
nhận của trường. Review này không xác nhận hiệu lực hiện tại hoặc người học.

## Từng câu

Chi tiết nguồn/trang/hash, đáp án và đối chiếu dev ở
[JSONL](review_decisions.jsonl); bản đọc bằng Excel ở [CSV](review_results.csv).
Khuyến nghị gốc của reviewer F2 là revise khi xét tính mới của holdout. Quyết
định dùng cho đánh giá đã lộ được ghi riêng, không xóa phát hiện trùng ý.

| ID | Nhóm | Gold dùng nguyên bản | Nguy cơ trùng ý |
| --- | --- | --- | --- |
| H2-Q001 | f1 | Đạt | moderate |
| H2-Q002 | f1 | Đạt | high |
| H2-Q003 | f1 | Đạt | high |
| H2-Q004 | f2 | Đạt | high |
| H2-Q005 | f2 | Đạt | high |
| H2-Q006 | f2 | Đạt | high |
| H2-Q007 | f2 | Đạt | high |
| H2-Q008 | f3 | Đạt | high |
| H2-Q009 | f3 | Đạt | high |
| H2-Q010 | missing_evidence | Đạt | high |
| H2-Q011 | missing_evidence | Đạt | high |
| H2-Q012 | out_of_scope | Đạt | high |
| H2-Q013 | out_of_scope | Đạt | high |
| H2-Q014 | opt_in_required | Đạt | high |
| H2-Q015 | f1 | Đạt | moderate |
| H2-Q016 | f1 | Đạt | high |
| H2-Q017 | f1 | Đạt | high |
| H2-Q018 | f2 | Đạt | high |
| H2-Q019 | f2 | Đạt | high |
| H2-Q020 | f2 | Đạt | high |
| H2-Q021 | f2 | Đạt | high |
| H2-Q022 | f3 | Đạt | high |
| H2-Q023 | f3 | Đạt | high |
| H2-Q024 | missing_evidence | Đạt | high |
| H2-Q025 | missing_evidence | Đạt | high |
| H2-Q026 | out_of_scope | Đạt | high |
| H2-Q027 | out_of_scope | Đạt | high |
| H2-Q028 | opt_in_required | Đạt | high |
| H2-Q029 | f1 | Đạt | high |
| H2-Q030 | f1 | Đạt | high |
| H2-Q031 | f1 | Đạt | moderate |
| H2-Q032 | f2 | Đạt | high |
| H2-Q033 | f2 | Đạt | high |
| H2-Q034 | f2 | Đạt | high |
| H2-Q035 | f2 | Đạt | high |
| H2-Q036 | f3 | Đạt | high |
| H2-Q037 | f3 | Đạt | high |
| H2-Q038 | missing_evidence | Đạt | high |
| H2-Q039 | missing_evidence | Đạt | high |
| H2-Q040 | out_of_scope | Đạt | high |
| H2-Q041 | out_of_scope | Đạt | high |
| H2-Q042 | opt_in_required | Đạt | high |
| H2-Q043 | f1 | Cần sửa | moderate |
| H2-Q044 | f1 | Cần sửa | high |
| H2-Q045 | f1 | Đạt | high |
| H2-Q046 | f2 | Đạt | high |
| H2-Q047 | f2 | Đạt | high |
| H2-Q048 | f2 | Cần sửa | high |
| H2-Q049 | f2 | Đạt | high |
| H2-Q050 | f3 | Đạt | high |
| H2-Q051 | f3 | Đạt | high |
| H2-Q052 | missing_evidence | Đạt | high |
| H2-Q053 | missing_evidence | Đạt | high |
| H2-Q054 | out_of_scope | Đạt | high |
| H2-Q055 | out_of_scope | Đạt | high |
| H2-Q056 | opt_in_required | Đạt | high |
