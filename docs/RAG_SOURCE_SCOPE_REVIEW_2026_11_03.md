# Review nguồn và phạm vi release — 03/11/2026

Đã kiểm ảnh đủ **297 occurrence F2 trên 22 trang bảng**, xác minh bốn liên kết
URL–binary bằng bản tải hiện tại và thu được ba tài liệu ma trận/sơ đồ mới.
Đã chốt phạm vi cho việc giữ nguyên release v3: F1 mô tả, F2 chép nguồn và F3
AI có opt-in. **Sáu blocker đầy đủ vẫn mở; official F3 chưa bật mặc định.**

[Gói review mới](../data/hus/review/p13_release_scope_v2/report.json),
[phạm vi JSON](../data/hus/review/p13_release_scope_v2/release_scope.json),
[bảng 106 nguồn CSV](../data/hus/review/p13_release_scope_v2/source_scope_decisions.csv)
và [receipt kiểm chứng](acceptance/hus_source_scope_review_v2_report.json).
Các gói review, baseline, release, CURRENT, registry và runtime cũ giữ nguyên.
Reviewer là AI, số review người thật thực tế bằng0; không cấp chứng nhận học vụ.

## Nguồn thuộc phạm vi đã chốt

Phạm vi này giữ dữ liệu đang được chọn, không mở rộng sang nguồn mới hoặc nâng
thành trả lời quy định hiện hành. [Danh sách dependency](../data/hus/review/p13_release_scope_v2/release_source_dependencies.jsonl)
ghi hash, origin, ngành, phiên bản và các occurrence cụ thể; không coi cả catalog
106 tài liệu là dữ liệu được phép trả lời.

| Phần | Phạm vi giữ lại | Giới hạn |
| --- | --- | --- |
| F1 | 15 nguồn metadata,65 chunk mô tả;5 nguồn include và10 include_markdown | Giữ phiên bản/hệ/cảnh báo gốc;14 nguồn là citation chính, nguồn CLC còn lại chỉ giữ provenance trùng đã deduplicate |
| F2 | 290 membership/297 occurrence, bốn CTĐT chuẩn từ canonical JSON và bốn PDF ghim hash | Giữ223 draft_unverified/67 verified theo review dự án; không thành xác nhận của trường hoặc tài khoản người học |
| F3 | 290 record/870 chunk do AI sinh | Bắt buộc nhãn AI và opt-in; các field official vẫn null |
| Đề cương official | Hai bộ KHMTTT2024/Toán tin2021,106 candidate giữ làm metadata review | Không có chunk official vào mặc định; chưa áp dụng identity hoặc edition mới |
| Ngoài selection | Nguồn sau đại học, seminar, tuyển sinh riêng và tài liệu chưa được chọn | Giữ archive; chỉ đưa vào release khác khi có scope/field/edition rõ |

Nguồn F1 `8afffd3cada3d048` không có chunk citation chính vì ba đoạn đã được
deduplicate qua `1c16ddf8a6f1f409`. Không cộng nó như một nguồn retrieval bổ sung.
Các URL scan mới khôi phục liên quan đúng byte F2 hiện có; không index thêm một
bản sao và không thay provenance Git/canonical đã ghim.

Việc phân loại scope không phải duyệt học vụ. Các nguồn thiếu chỉ chặn phần mở
rộng hoặc tuyên bố mà chúng cần hỗ trợ; không biến37 URL thiếu thành37 blocker
đồng mức của release hiện có. Chất lượng RAG vẫn chưa đạt mục tiêu90% ở phép đo
80% đã lưu; review nguồn này không cấp quyền xuất bản/triển khai.

## Kiểm ảnh/bảng sau OCR

[297 dòng quan sát](../data/hus/review/p13_release_scope_v2/table_visual_review.jsonl)
bao phủ toàn bộ290 record F2: Toán học96 occurrence,Toán tin69,KHMTTT67,KHDL65.
45 dòng cũ được kiểm lại,252 dòng được bổ sung. Mã và tín chỉ khớp occurrence;
194 ô tiên quyết có dữ kiện khớp raw sau khi bỏ khoảng trắng,103 ô trống giữ
nghĩa chưa biết. Không tạo cạnh tiên quyết hoặc kết luận đủ điều kiện học.

- KHMTTT `MAT3554E`,PDF vật lý12/STT47: ảnh in **Formal Language and Automata**,
  canonical ghi **Formal Languages and Automata**. Ghi một khác biệt tên tiếng
  Anh, không sửa source hoặc release cũ.
- Toán học `MAT3360`: `hoá`/`hóa` là biến thể đặt dấu được ghi riêng.
- Giữ nguyên các ô giờ đáng chú ý:Toán tin `MAT4082`75/62/275,KHMTTT `MAT4080`
  70/60/215; `HUS1022` của Toán học12/24/64 nhưng ba CTĐT khác24/12/64. Không
  lấy ô ngành khác để chuẩn hóa. F2 record hiện không có trường giờ để so sánh.
- Trang cuối cả bốn bảng ghi dấu `/` trong tiên quyết mang nghĩa “hoặc”. Giữ raw
  dấu gạch, ngoặc và xuống dòng; không suy mọi xuống dòng thành điều kiện AND.

Tổng lượt này quan sát **48 trang PDF duy nhất**, gồm bảng, quyết định, mục lục,
header/continuation và ba trang ma trận/sơ đồ mới.19 trang trùng lượt19 ảnh trước,
29 trang nằm ngoài lượt đó. [Index ảnh](../data/hus/review/p13_release_scope_v2/image_evidence_index.jsonl)
đếm theo hash PDF/trang vật lý, không cộng lặp các renderer hoặc các reviewer.
DOCX được kiểm XML/table, không có tuyên bố đã render trang Word.
Chưa kiểm mọi ô ma trận/sơ đồ, toàn bộ prose72 trang OCR hoặc tất cả1.788 vùng
confidence thấp. Kết quả OCR72/72 lịch sử không đổi và không được tính thành
chứng nhận nội dung.

## Bốn đề xuất identity và xung đột bổ sung

[Quyết định AI theo từng case](../data/hus/review/p13_release_scope_v2/identity_edition_review.jsonl)
tách identity dự kiến khỏi quyền áp dụng vào bản CTĐT hiện tại.

| Case | Kết quả kỹ thuật | Phần chưa cho phép |
| --- | --- | --- |
| Giải tích2,header2024 tr23 in2502 | Chấp nhận identity ứng viên MAT2502: mục lục cùng PDF tr2 chỉ rõ MAT2502→tr23; bảng2023 tr10 và continuation tr24 khớp | Chưa áp dụng mapping hoặc official F3; vẫn giữ mã nguồn in thiếu tiền tố |
| MAT3550E,tr74 | Chấp nhận identity ứng viên; mã/tên/3 tín chỉ/giờ/tiên quyết và continuation tr75 hỗ trợ | Chưa nâng thành duyệt field/hiệu lực |
| MAT1202 OOP,tr86 | Chấp nhận identity trong đúng span; mục lục tách OOP tr86 và nhúng tr162,continuation tr87 hỗ trợ OOP | Không gắn mọi occurrence MAT1202 vào cùng record |
| MAT3561 Toán tin2021→CTĐT2023 | Hoãn link:2021 tr256 ghiMAT3508/MAT3509,2023 tr12 ghiMAT3533 | Không mang tiên quyết/assessment2021 sang bản2023 |
| Header nhúng tr162 lại inMAT1202 | Bác gắn vào MAT1202/OOP. Mục lục tr2 ghiMAT1208→tr162; bảng2023 tr12 và continuation tr163 hỗ trợ ứng viên MAT1208 kèm erratum | Không tự sửa mã hoặc áp dụng link mới |

Phát hiện thêm: mục lục KHMTTT2024 tr2 ghi **MAT2505→tr4**, nhưng header tr4 in
**MAT2316** cho Lập trình cơ bản. Giữ như errata lead mới. Vì có các bất nhất nội
bộ, việc bìa tham chiếu đúng QĐ không đủ duyệt toàn bộ đề cương.
[Queue sai khác](../data/hus/review/p13_release_scope_v2/source_discrepancy_queue.jsonl)
giữ các phát hiện cần xử lý ở bản dữ liệu tiếp theo.

## Edition, cohort và hiệu lực

Đã nhìn trực tiếp Điều2 ở trang vật lý2 của **cả bốn QĐ3565/3567/3568/3569-2023**:
tài liệu tuyên bố áp dụng từ khóa tuyển sinh2022.
[Bằng chứng theo từng CTĐT](../data/hus/review/p13_release_scope_v2/cohort_declarations.jsonl).
Đây là xác nhận nội dung mà bản ghim tuyên bố, không phải kết luận tài liệu chưa
bị sửa đổi hoặc ràng buộc của một sinh viên cụ thể.

Bìa đề cương KHMTTT2024 ghi QĐ2385 ngày31/07/2024 và dẫn QĐ3568 ngày18/10/2023;
có đủ căn cứ cho liên hệ được bìa tuyên bố. Chưa có chuỗi văn bản áp dụng/sửa đổi
đủ để xác nhận hiệu lực hiện tại hoặc mọi field. Toán tin2021 giữ edition riêng,
không suy tương đương2023 từ tên/mã môn giống nhau. Tìm kiếm giới hạn không thấy
đính chính không chứng minh không có đính chính.

## 37 raw thiếu: bảy bản tải hiện tại,30 chưa thử lại

[Review37 nguồn](../data/hus/review/p13_release_scope_v2/missing_raw_review.jsonl)
và [bốn binding mới](../data/hus/review/p13_release_scope_v2/binding_review.jsonl)
ghi URL yêu cầu/cuối,thời điểm,HTTP200,Content-Type,byte/hash và kiểm định dạng.
Bảy URL tải được tạo sáu binary duy nhất; ba hash mới thuộc tài liệu ma trận/sơ đồ,
ba hash còn lại đã là PDF F2 trong registry. Hai URL KHMTTT trả cùng một hash.

| Nhóm lịch sử | Số URL | Xử lý hiện tại |
| --- | ---: | --- |
| Scan có thể là alias |4 | Đã chứng minh binding của bản tải hiện tại bằng hash trùng PDF F2; không còn chỉ là suy đoán từ tên |
| Ma trận/sơ đồ |3 | Đã lấy DOCX/PDF gốc hiện tại; giữ candidate ngoài selection, chưa xác định đủ edition/cohort |
| Sau đại học |24 | Hoãn ngoài release cử nhân; không thử tải lại lượt này |
| Tuyển sinh |5 | Hoãn sang scope/năm riêng; một archive có URL phụ lục2 nhưng nội dung/hash trùng phụ lục1 |
| Seminar |1 | Ngoài F1/F2/F3 hiện hành; không thử tải lại |

Số37 trong pack lịch sử giữ nguyên. Bản dẫn xuất có **7 current capture và30 chưa
khôi phục/thử lại trong lượt này**;30 không phải30 lỗi HTTP. File mới lưu local
ở `backups/p13_release_scope_v2/raw/`,chưa đưa vào portable release hoặc Git assets.
HTTP gốc thành công; web tool tự nâng HTTPS đã timeout/cache miss,không phải404.
Hash đối chiếu với binary Git có sẵn tăng căn cứ về byte; không tuyên bố transport
HTTPS hoặc byte ngày22/10 bằng byte tải hiện tại.

Ba tài liệu mới còn giới hạn cụ thể: DOCX chỉ có bảng chuẩn đầu ra45 dòng STT17–61,
filename nói2023 nhưng XML metadata ghi2025,không in QĐ/cohort; matrix Toán tin6
trang không có đủ binding edition; sơ đồ1 trang mất29/64 token mã và mất geometry
trong archive chữ. Không biến outcome hoặc mũi tên thành prerequisite edges.

## Sáu blocker: đã giải quyết phần nào, còn thiếu gì

[Ma trận theo sáu ID](../data/hus/review/p13_release_scope_v2/blocker_scope_matrix.jsonl)
giữ **0 full blocker đóng**. Bốn ID `554827330988bff8`,`7b0e9c679a8eb75a`,
`a090bd625a439d9b`,`a8f161744d0c9907` đã giải quyết phần binding cho bản tải hiện
tại. Hai ID `c1c50f5ba9094527`,`d988fffe2a509f23` giữ recovered capture trước đó.
Toàn bộ dòng F2 liên quan đã được AI so ảnh trong lượt này.

Phần còn mở là byte lịch sử chưa chứng minh,hiệu lực/sửa đổi/applicability chưa
xác minh và các quyết định nguồn mới chưa áp dụng. Không tiếp tục ghi thiếu ảnh
297 dòng như thể chưa làm,không đóng toàn bộ blocker chỉ vì một phần đã giải quyết.
Không bắt thu hồi mọi tài liệu ngoài scope trước khi giữ selection cũ.

## Kiểm chứng và việc còn lại

**34 test source/OCR/supplement đạt**. Kiểm bổ sung đối chiếu đúng297 occurrence,
290 record,37/106/6 ID,hash ảnh/binary/capture và302 file được bảo vệ. Bộ cũ,review
nguồn/canonical,CURRENT,registry,runtime và các phép đo RAG giữ nguyên.

Tiếp theo cần xử lý sai khác tên/errata ở phiên bản dữ liệu riêng nếu chọn nâng
dữ liệu; thu thập văn bản áp dụng/đính chính cho các field official định release.
Nguồn ngoài phạm vi chỉ mở lại khi có yêu cầu field/scope rõ. Chưa áp dụng mapping,
chưa bật official F3,chưa xuất bản hoặc triển khai.
