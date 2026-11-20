# Review theo từng ý F3 và edition nguồn — 13/11/2026

**Lượt bổ sung r2:** [21 khoảng thiếu đã có đoạn đối chiếu trực tiếp](RAG_SOURCE_GAP_CLOSURE_2026_11_13.md).
Ma trận và receipt r1 dưới đây giữ nguyên; các con số15/19/2 là lịch sử r1,
không thay bằng kết quả mới trong artifact cũ.

Nhánh `hus-llm-rag`, nền `f61b0fd` + WIP; chỉ làm local. Đã ánh xạ riêng
**18 chủ đề và18 mục tiêu** của bốn hồ sơ F3 với đoạn reference, đồng thời tìm
thêm bằng chứng lịch sử Q001. Không sửa snapshot v4, scope/gold/run/review cũ,
không gọi Google hoặc bật LLM.

[Gói review](../data/hus/review/field_edition_20261113_r1/report.json),
[ma trận36 mục](../data/hus/review/field_edition_20261113_r1/field_matrix.json),
[29 locator nguồn](../data/hus/review/field_edition_20261113_r1/anchors.json),
[receipt](../data/hus/qa/20261113/field_edition_r1/report.json).

## Q001 và chuỗi văn bản

Đã tải được binary10 trang CTĐT chuẩn2012 từ **files.vnu.edu.vn** và xem ảnh
trang1–2. Bìa ghi mã52480105, QĐ4115/QĐ-ĐT ngày30/11/2012. Điều này bổ sung
bằng chứng thực cho chương trình chuẩn trong năm2012; không còn chỉ dựa vào
text chỉ mục của đầu mối HUS09_0.pdf đã trả404 ở lượt trước.
[PDF trên VNU](https://files.vnu.edu.vn/data/upload/2013/10/15061/52480105%20May%20tinh%20va%20Khoa%20hoc%20thong%20tin%20-%20HUS%20-%20Chuan%20Dai%20hoc.pdf).

Đây là bản từ URL khác có hash mới, **chưa chứng minh bằng byte với09_0.pdf**.
Nội dung nói về đưa ngành vào danh mục và quy tắc tuyển sinh; chưa trực tiếp
ghi mốc tuyển khóa đầu riêng hệ chuẩn. Vì vậy giữ unknown của chunk cũ và điểm
A7V4-Q001; chưa suy hiệu lực hiện tại hoặc ánh xạ mọi mã ngành/đổi tên.

Bản CTĐT2022 khác đã tải được14 trang, nhưng ảnh trang1 để trống số/ngày/tháng
quyết định ban hành. Không dùng dòng ban hành chưa hoàn chỉnh đó để xác nhận
áp dụng hiện hành. [Bản2022](https://cdnportal.vnu.edu.vn/data/upload/2022/07/31051/file/CTDT%20chuan%20KHOA%20HOC%20MAY%20TINH%20VA%20THONG%20TIN.pdf).
Đầu mối đề án tuyển sinh2021 chưa tải được binary do ConnectError; text chỉ mục
là lead, không phải chứng cứ ảnh/binary đã kiểm.

[Kết luận và giới hạn Q001](../data/hus/review/field_edition_20261113_r1/q001_chain.json):
liên kết **CTĐT chuẩn2012** đã có binary; liên kết **tuyển khóa đầu–hệ chuẩn**,
chuỗi thay thế/áp dụng theo cohort vẫn còn mở. Muốn dùng nguồn mới trong RAG
phải qua candidate/lượt tích hợp riêng, không relabel đoạn lịch sử đang unknown.

## Ma trận từng ý và giới hạn

Mỗi dòng ghim record/hash, mã/ngành/decision, field, JSON pointer/item hash,
locator reference, khái niệm đã đối chiếu và phần còn thiếu. Locator là offset/
hash trong text chuẩn hóa từ bản chụp, có thể kiểm lại; không chỉ gắn homepage.

| Trạng thái | Số mục | Ý nghĩa |
| --- | --- | --- |
| `core_supported` |15|Có đoạn hỗ trợ khái niệm cốt lõi đã nêu; không là kiểm mọi câu/ví dụ hoặc official HUS.|
| `partial` |19|Một phần được hỗ trợ, phần thiếu/giả thiết còn ghi rõ; không làm tròn thành đạt.|
| `open` |2|Chưa tìm được đoạn trực tiếp trong tập nguồn đã kiểm; không kết luận nội dung sai.|

| Hồ sơ và field | Đã ánh xạ | Phần còn mở tiêu biểu |
| --- | --- | --- |
| MAT1204 — KHMTTT, QD3568-2023 |4 chủ đề +4 mục tiêu. ORI có đoạn cụ thể về chọn dữ liệu theo câu hỏi/phạm vi, phân tích, quản lý phiên bản và báo cáo trung thực.|Hai mục tổng quan/đối chiếu tài liệu còn `open`; chưa có reference phương pháp phù hợp trong tập này. Thiết kế–nhân quả và thao tác hóa chưa đủ. Đề cương2024 đối chiếu trước đó vẫn chưa được xác nhận áp dụng theo cohort.|
| MAT2034 — KHDL, QD3569-2023 |5 chủ đề +5 mục tiêu. FNC có đoạn Newton và điều kiện hội tụ cục bộ, residual/conditioning, LU/pivoting, nội suy, hình thang/Simpson và tích phân thích nghi.|Chưa map trực tiếp chia đôi và Runge/nút cách đều. Ước lượng sai số không là bảo đảm; không suy Newton hội tụ toàn cục hoặc adaptive luôn phát hiện đỉnh hẹp.|
| MAT2300 — Toán học, QD3565-2023 |5 chủ đề +5 mục tiêu. MIT có đoạn khử/pivot, nullspace/column space, độc lập/cơ sở và nullity=n-r trong ghi chú.|Giới hạn ma trận/hữu hạn chiều; hợp thành/đổi cơ sở và một số phản ví dụ chưa có đoạn trực tiếp đủ chi tiết.|
| MAT1202 — Toán Tin, QD3567-2023 |4 chủ đề +4 mục tiêu. Oracle có đoạn state/behaviour/encapsulation, interface contract và polymorphism.|Behavioural substitutability, cohesion/coupling, inheritance-versus-composition và kiểm thử hành vi còn partial. Không dùng MAT3372 làm đề cương MAT1202.|

Nguồn đã đối chiếu gồm [ORI Data Selection](https://ori.hhs.gov/education/products/n_illinois_u/datamanagement/dstopic.html),
[ORI Reporting](https://ori.hhs.gov/education/products/n_illinois_u/datamanagement/dprtopic.html),
[FNC Newton](https://fncbook.com/newton/), [FNC Adaptive](https://fncbook.com/adaptive/),
[MIT ghi chú basis](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/0bbc30e3f1d7933ea07a2d2e9ab050d9_MIT18_06SCF11_Ses1.9sum.pdf),
[Oracle Objects](https://docs.oracle.com/javase/tutorial/java/concepts/object.html),
[Oracle Interfaces](https://docs.oracle.com/javase/tutorial/java/IandI/createinterface.html).
Danh sách đầy đủ, hash/thời điểm và nguồn dùng lại nằm trong registry của gói.

MIT2011 và Oracle JDK8 là **reference bổ sung khác edition** so với link
MIT2010/Python/UML trong hồ sơ; chỉ dùng đối chiếu khái niệm, chưa thêm vào
profile runtime và không đổi edition HUS. Không chuyển kiến thức của một ngôn
ngữ thành yêu cầu dạy/học của trường. Ví dụ AI không được coi là trích dẫn
reference hoặc đã được reviewer độc lập kiểm chứng.

## Kiểm chứng và bước tiếp theo

- 26 HTTP capture mới thành công, một ConnectError; dùng lại hai capture FNC
  trước có hash khớp. Nguồn phản hồi200 chỉ chứng minh truy cập tại thời điểm tải.
- 36 item pointer/hash và 29 locator range/hash đã kiểm đầy đủ. Xem 6 ảnh PDF:
  H01 trang1–2, H03 trang1–2, MIT basis trang1/3; không nhận là đã xem toàn bộ
  ảnh của ba PDF. MIT basis bốn trang đã đọc text.
- **2.867 file cũ giữ SHA**; cả290 F3 vẫn AI/needs_review, official fields null,
  Q001 giữ unknown. Cached replay A7S tái hiện, pins A7S và L5 preparedr3 khớp.
  Không sửa runtime nên không lặp suite70 test của review trước; đây là kiểm
  ma trận/locator/toàn vẹn mới, không là một test suite semantic tự động.
- Root AI đã thấy nguồn/runtime, human0; **không nghiệm thu độc lập/học vụ**.
  Không stage/commit/push/PR/Actions/deploy hoặc tạo kit mới.

| Binding | SHA-256 |
| --- | --- |
| PDF chuẩn2012 |`56bad5aa1a09217baca356d8a61a5e28bb791c517133341c7376b15bae3a89d0`|
| Review manifest |`c31f9eb00b25083e7f44be985da51338363aed224cd3dd1ab46dacfaae68ad44`|
| QA manifest |`882ae7a4dcf7e2fba498fed54e4c0956379904098df42b38be2e2b7a7a8899e4`|

Tiếp theo: bổ sung reference trực tiếp cho19 partial/2 open; reviewer kiểm
chuỗi tuyển sinh/ban hành/áp dụng. Nếu thay dữ liệu, tạo candidate và kiểm tích
hợp/rollback riêng; không chép đè v4, đổi gold hoặc dùng review này tăng điểm cũ.
