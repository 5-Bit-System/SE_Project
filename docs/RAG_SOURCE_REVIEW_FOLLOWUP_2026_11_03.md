# Rà soát tiếp nguồn RAG — 03/11/2026

Đã tiếp tục kiểm kỹ thuật trên nguồn đã ghim, **chưa có quyết định duyệt của người
review**. Người dùng đã nhận review; các trường tên/ngày/quyết định vẫn để trống
cho tới khi người thật kiểm từng mục. Không đổi release, CURRENT, registry,
review gốc hoặc runtime; official F3 vẫn chưa bật.

Gói mới: [p13_scope_followup_20261103](../data/hus/review/p13_scope_followup_20261103/report.json).
Các gói P1-3 cũ giữ nguyên byte. Các phát hiện mới không sửa hay diễn giải lại
receipt cũ thành kết quả của lần này.

## Phạm vi release và nguồn cần ưu tiên

Đã lập [worksheet106 nguồn](../data/hus/review/p13_scope_followup_20261103/source_scope_inventory.jsonl),
ghi trạng thái hiện hành, đề xuất phạm vi và bằng chứng người review cần cung cấp.

| Nhóm | Số nguồn | Xử lý trong phạm vi hiện tại |
| --- | ---: | --- |
| F1 mô tả đã nằm trong release |15 |Giữ đúng review/cảnh báo gốc; không cấp xác minh học vụ mới |
| Có original nhưng chưa được chọn |52 |Chỉ xét khi bổ sung đúng field/scope; không index toàn bộ hoặc index trùng |
| Hai bộ đề cương KHMTTT/Toán tin |2 |Candidate chờ identity, edition/cohort và người duyệt; không nối official F3 |
| Raw thiếu — sau đại học |24 |Đề xuất hoãn ngoài phạm vi release cử nhân hiện tại; giữ archive |
| Raw thiếu — seminar |1 |Đề xuất hoãn ngoài F1/F2/F3 hiện tại |
| Raw thiếu — tuyển sinh |5 |Tách phạm vi/năm tuyển sinh; không trộn với CTĐTcohort2022 |
| Raw thiếu — ma trận/sơ đồ CTĐT |3 |Candidate có thể hữu ích, cần original và edition trước khi quyết định |
| Raw thiếu — bản scan có thể là alias |4 |Ưu tiên chứng minh binding URL/document_id/binary; PDF liên quan không thay bằng chứng gốc |

Các phân loại nguồn thiếu vẫn dựa trên archive/URL, **chưa phải review original**.
Không có nguồn F1 mặc định trong37 raw thiếu. Vì vậy không cần coi cả37 là blocker
đồng mức của release F1 đang dùng; vẫn giữ từng blocker cho phần dữ liệu tương ứng.
Không xóa archive hoặc tự phê duyệt đề xuất hoãn. Chi tiết37 dòng:
[missing_raw_decisions.jsonl](../data/hus/review/p13_scope_followup_20261103/missing_raw_decisions.jsonl).

## Kiểm ảnh/bảng sau OCR

Lần này đã mở và quan sát **19 ảnh trang thật** đã ghim hash:13 trang bảng CTĐT,
5 trang header đề cương được kiểm lại và1 trang bảng Toán tin để đối chiếu edition.
Đây là số trang kiểm trong lượt này, có cả trang đã từng được kiểm trước đó.

Đã đối chiếu đủ **45 occurrence** mà OCR không tìm thấy token mã: tất cả45 mã
được thấy bằng quan sát ảnh trong cột mã môn của13 trang bảng. Ghi thêm số tín chỉ,
ba cột giờ và từng dòng ô tiên quyết được quan sát; ô trống vẫn giữ ý nghĩa
“ảnh không ghi”, không biến thành xác nhận học vụ rằng không có tiên quyết.

| PDF/CTĐT ghim | Trang vật lý xem bảng | Occurrence từng bị OCR bỏ sót |
| --- | --- | ---: |
| Toán học QD3565-2023, SHA bắt đầu`e6e33a8a489f` |8,9 |6 |
| Toán tin QD3567-2023, SHA bắt đầu`6c19e390ba61` |8,9,10 |9 |
| KHMTTT QD3568-2023, SHA bắt đầu`bc070d7ae371` |9,10,11,12,13 |20 |
| KHDL QD3569-2023, SHA bắt đầu`b4b0289701a6` |9,10,11 |10 |

[table_visual_observations.jsonl](../data/hus/review/p13_scope_followup_20261103/table_visual_observations.jsonl)
ghi45 dòng, hash ảnh, hash PDF, trang vật lý và dữ kiện AI đã đọc. Reviewer cần mở
lại ảnh/PDF kiểm quan hệ ô/dòng, tên Việt/Anh và applicability. Đây **không phải**
full297-occurrence acceptance; không suy252 token OCR đã thấy là252 dòng đã đúng.
Chưa kiểm hết1.788 vùng confidence thấp hoặc mọi ô của72 trang đã OCR. Không sửa
F2 từ các quan sát ảnh này và không tạo prerequisite edge mới.

## Bốn đề xuất liên kết identity và một xung đột phải giữ

Đã kiểm lại5 header/case. Có **4 proposed canonical links**, và1 case xung đột
đang không gắn canonical ID; không phải5 link đã được chấp nhận.

| Candidate/nguồn | So sánh kỹ thuật | Quyết định còn cần người review |
| --- | --- | --- |
|`098df9e79c1391af:3:2502`,PDF2024 tr23 |Nguồn in`2502`; tên Giải tích2,4 tín chỉ,giờ40/40/120,tiên quyếtMAT2501. Bảng CTĐT2023 tr10 dòng20 in`MAT2502` cùng các trường đó |Xác nhận missing-prefix/identity và phạm vi áp dụng; chưa tự thêmMAT |
|`...:12:MAT3550E`,PDF2024 tr74 |Nguyên lý/lí hệ điều hành,3 tín chỉ,30/30/90,MAT2505; bảng2023 tr11 dòng29 cùng mã/dữ kiện |Xác nhận khác cách viết không che khác edition; chưa nâng duyệt |
|`...:14:MAT1202`,PDF2024 tr86 |Lập trình hướng đối tượng,3 tín chỉ,22/46/82,MAT2505; bảng2023 tr11 dòng31 tương ứng |Có thể là link đúng nhưng duplicate trong nguồn vẫn phải được xử lý riêng |
|`...:27:MAT1202`,PDF2024 tr162 |Nguồn thực inMAT1202 cho Xây dựng hệ thống nhúng,2 tín chỉ,0/30/70; ô tiên quyết lại cóMAT1202 vàMAT3505. Bảng CTĐT2023 tr12 dòng44 in**MAT1208**,cùng tên/tín chỉ/giờ/tiên quyết |Đây là **errata lead chưa duyệt**, không tự đổi mã hoặc gắn nội dung nhúng vàoMAT1202. Cần xác nhận đính chính/identity |
|`bc0a1f59b7ab202c:54:MAT3561`,PDF2021 tr256 |Xử lý/lí ngôn ngữ tự nhiên và ứng dụng; nguồn2021 ghiMAT3508/MAT3509. Bảng QD3567-2023 tr12 dòng54 ghiMAT3533 |Khác cách viết không chứng minh tương đương edition/tiên quyết; giữ blocker2021↔2023 |

Mỗi case trong [identity_decisions.jsonl](../data/hus/review/p13_scope_followup_20261103/identity_decisions.jsonl)
có ảnh/hash/trang và quyết định pending. Không áp dụng4 link cũ hoặc errata lead mới.

## Edition, cohort, hiệu lực và6 blocker

Hai bộ đề cương vẫn cần xác nhận riêng trong
[edition_decisions.jsonl](../data/hus/review/p13_scope_followup_20261103/edition_decisions.jsonl):

- KHMTTT: bản bìa đã ghim tuyên bố QĐ2385 ngày31/07/2024 và dẫn chương trình
  QĐ3568 ngày18/10/2023 hệ chuẩn. Cần bằng chứng áp dụng cho cohort2022 và rà soát
  sửa đổi sau văn bản; không suy hiệu lực chỉ vì số quyết định khớp.
- Toán tin: nguồn đề cương ghi2021; canonical làcohort2022/QD3567-2023. Không tự
  hợp nhất chỉ vì mã/tên gần giống; giữ rõ khác tiên quyếtMAT3561.

**Cả6 blocker OCR lịch sử vẫn mở**:

| Document ID | Trạng thái còn thiếu |
| --- | --- |
|`554827330988bff8`,`7b0e9c679a8eb75a`,`a090bd625a439d9b`,`a8f161744d0c9907` |Chưa chứng minh liên kết original từ URL/document_id đến binary liên quan; OCR và việc xem bảng không phục hồi binding |
|`c1c50f5ba9094527`,`d988fffe2a509f23` |Đã có recovered capture và OCR; còn review ảnh/bảng của người thật,applicability/hiệu lực. Chưa tự đóng chỉ vì lượt AI xem thêm bảng |

[blocker_decisions.jsonl](../data/hus/review/p13_scope_followup_20261103/blocker_decisions.jsonl)
ghi6 dòng và điều kiện đóng cụ thể. Không có raw mới được thu hồi trong lượt này.
Sáu lần fetch timeout cũ không phải HTTP404 hoặc chứng minh tài liệu đã bị thu hồi.

## Kiểm tra nguồn chính thức mới, giới hạn kết luận

Đã thực hiện4 truy vấn giới hạn trên domain HUS vào03/11/2026. Nguồn tìm được có
[thông báo tuyển CTĐT đặc biệt năm2026](https://hus.vnu.edu.vn/thong-bao/dao-tao-tuyen-sinh/thong-bao-xet-tuyen-sinh-vien-vao-cac-chuong-trinh-dao-tao-dac-biet-nam-2026-ap-dung-cho-doi-tuong-sinh-vien-da-trung-tuyen-vao-truong-145802)
ngày14/08/2026, nêu chương trình tích hợp cử nhân–thạc sĩ tài năng STEM KHDL.
Đó là chương trình/năm tuyển sinh khác, không xác nhận CTĐTcohort2022 hiện tại.
[Tin gặp mặt QH2026](https://hus.vnu.edu.vn/mot-vong-quanh-hus/dien-dan-thay-va-tro/truong-dai-hoc-khoa-hoc-tu-nhien-gap-mat-tan-145879)
đăng19/09/2026 cũng chỉ mô tả sự kiện18/09/2026 và chương trình mới.

Tìm kiếm này chưa thu được chuỗi văn bản áp dụng/sửa đổi đủ để xác nhận hiệu lực
QD3567/QD3568 hoặc nối đề cương2021 vớicohort2022. Không suy “không có điều chỉnh”
từ việc tìm không thấy. Không mở rộng runtime sang chương trình2026. Truy vấn,
URL/ngày và giới hạn lưu trong
[source_search_notes.json](../data/hus/review/p13_scope_followup_20261103/source_search_notes.json).

## Cách người review xử lý gói này

1. Ưu tiên5 identity/case và2 edition decisions; mở đúng binary/hash/trang,
   xác nhận include/reject/defer và phạm vi ngành/cohort/decision bằng chứng thật.
2. Review45 ô bảng đã đánh dấu, rồi các vùng OCR còn lại khi chúng phục vụ field
   định đưa vào release. Ghi rõ ô/dòng nào đã kiểm, không ký cả72 trang từ một mẫu.
3. Chốt đề xuất phạm vi37 raw:25 ngoài scope,5 tuyển sinh riêng,7 bản gốc/binding
   cần ưu tiên. Giữ pending nếu chưa có byte/version/áp dụng đủ căn cứ.
4. Ghi kết quả vào bản quyết định mới với tên thật, thời gian có múi giờ, hash,
   locator và lý do. Không sửa pack cũ để hợp thức hóa kết quả.
5. Chỉ sau các quyết định cần thiết mới chuẩn bị release mới, kiểm citation và
   nghiệm thu. Official F3/candidate vẫn không bật mặc định trong bước review này.

Script tạo worksheet không chạy RAG, không truy vấn provider/DB/VNU và không ghi
nguồn/runtime. Các kiểm tra kỹ thuật xác nhận173 input hashes giữ nguyên,106/37/6
ID joins và45 dòng quan sát gắn đúng13 ảnh/SHA. Không có chữ ký học vụ hoặc nghiệm thu mới.
