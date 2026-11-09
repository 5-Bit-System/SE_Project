# P1-3 — Review nguồn, hiệu lực, đề cương và OCR

Ngày rà soát: **02/11/2026**. Trạng thái: **đã audit nguồn, OCR72/72 trang và bổ sung50
quote; review ảnh/bảng, học vụ và hiệu lực hiện tại còn chờ**. Không bật official F3 hoặc đưa thêm
candidate vào tập trả lời mặc định.

## Lần tiếp tục — bổ sung trích đoạn và OCR

Đã khôi phục **50 trích đoạn bị bộ trích cũ bỏ sót**, gồm **46 assessment, 3 objectives
và 1 content**. Cả50 khớp nguyên văn/offset/trang trong capture và được tìm lại bằng
PDFium trên binary đúng hash.44 mục assessment KHMTTT sử dụng tiêu đề mục9 mà bộ trích
cũ chưa nhận diện; hai mục assessment Toán tin còn lại có định dạng tiêu đề khác.
Các đoạn này nằm trong **gói chờ review**, không được nối vào release/runtime.

| Trường trong106 candidate thuộc hai PDF đề cương | Snapshot v3 | Có text khi cộng supplement chờ review |
| --- | ---: | ---: |
| Nội dung |105 |106 |
| Mục tiêu |102 |105 |
| Đánh giá |60 |106 |

Không suy các số trên thành độ phủ official F3 cho cả bốn ngành. Mục tiêu `PEC1008`
vẫn thiếu: ảnh trang PDF10 chỉ có tiêu đề mục6 rồi chuyển sang mục7 Chuẩn đầu ra.
Ba tiêu đề Tiếng Anh B1/GDTC/GDQPAN ở trang41 không có mã hay đề cương chi tiết;
trang42 đã sang `INM1000`, vì vậy không tự tạo thêm ba hồ sơ.

Đã hoàn tất OCR **72/72 trang** bằng EasyOCR1.7.2, tiếng Việt/Anh, CPU, ảnh144dpi:
**7.136 vùng chữ**, trong đó1.788 vùng có confidence dưới0,8 được gắn cờ để kiểm tra.
Mô hình lấy từ [release chính thức EasyOCR](https://github.com/JaidedAI/EasyOCR), kiểm
checksum upstream và lưu SHA-256. Tool chạy offline, ghi text, từng bbox/confidence,
hash ảnh và checkpoint. Tesseract vẫn không có; OCR dùng engine khác đã cài sẵn.
Confidence chưa được hiệu chuẩn và không chứng minh độ đúng của bảng/ô.

Đối chiếu chẩn đoán với297 occurrence mã/trang cũ thấy token mã trên252 occurrence;
45 occurrence chưa thấy token đúng trong text OCR của trang. Đây **không phải độ
chính xác297 dòng**: token có thể nằm trong ô tiên quyết hoặc dòng khác, chưa xác
minh quan hệ ô/bảng. Danh sách45 trường hợp chỉ dùng ưu tiên review ảnh, không sửa
F2 theo OCR hoặc coi các occurrence đã thấy token là các dòng đã duyệt.

Đã xem ảnh **6 trang ít chữ**:5 trang chỉ có địa điểm/năm hoặc footer; trang281
đề cương Toán tin có nội dung Map/Filter/Reduce. Capture PyMuPDF cũ đã giữ nội dung
này, còn PDFium bỏ sót; không gọi đây là mất text trong corpus gốc. Đã xem thêm5
header mã/tên và ghi4 đề xuất identity chưa áp dụng. Hai trường hợp là khác cách
viết lí/lý; mã `2502` thực sự thiếu tiền tố trong nguồn; `MAT1202` thực sự in cho
cả Lập trình hướng đối tượng và Xây dựng hệ thống nhúng, khác tên và tín chỉ.
Riêng `MAT3561`, trang256 nguồn2021 ghi tiên quyết khác ô54/trang12 bản2023;
không dùng tên gần trùng để đồng nhất phiên bản hay đè F2.

Đã thử lại **6 URL cho4 hồ sơ OCR lịch sử**, gồm URL lưu trữ và phương án sửa mojibake;
tất cả timeout, không nhận được HTTP status từ origin hoặc PDF mới.37 raw vẫn chưa
thu hồi. Phân loại đề xuất theo Markdown lưu trữ:24 sau đại học,5 tuyển sinh,3 ma trận/
sơ đồ CTĐT,4 hồ sơ scan cần chứng minh liên kết và1 seminar. Phân loại chưa phải review
bản gốc. Tìm kiếm bổ sung trên nguồn HUS có tin giới thiệu/kiểm định, chưa đủ chứng
minh hiệu lực các edition đang dùng hoặc không có điều chỉnh sau văn bản.

| Gói bổ sung | Nội dung |
| --- | --- |
| [p13_syllabus_supplement_v1](../data/hus/review/p13_syllabus_supplement_v1/report.json) |50 quote/offset/page;1 trường mục tiêu chưa đủ nguồn;3 header chưa có đề cương chi tiết |
| [p13_ocr_v1](../data/hus/review/p13_ocr_v1/report.json) |72 trang OCR, model/version/parameter/input hashes, checkpoint `pages/` và tổng hợp `ocr_pages.jsonl`;78 input pins không đổi |
| [p13_followup_v1](../data/hus/review/p13_followup_v1/reviewer_packet.md) |15 trang được AI quan sát trực quan,4 identity proposals chưa áp dụng, ưu tiên37 raw, theo dõi6 blocker và packet cho reviewer |
| [p13_source_retry_v1](../data/hus/review/p13_source_retry_v1/attempts.jsonl) |6 lần thử URL có thời điểm/kết quả; không kết luận404 hoặc hết hiệu lực từ timeout |

OCR và đối chiếu kỹ thuật không thêm chữ ký học vụ. F2 giữ67 sign-off dự án/223 draft;
F3 giữ290 hồ sơ AI tham khảo và nhãn/warning. CURRENT, binary registry, candidate/review
nguồn và toàn bộ code runtime giữ nguyên. P1-3 vẫn chờ review ảnh/bảng, binding nguồn
thiếu và xác nhận edition/hiệu lực.

Kiểm tra tiếp tục: **102 test pass**, Ruff đạt; chạy lại `--resume` kiểm checkpoint,
ảnh và input pins để tái dùng text đã lưu. Receipt mới:
[hus_p13_continued_review_report.json](acceptance/hus_p13_continued_review_report.json).
Receipt/audit ban đầu phía dưới giữ nguyên ý nghĩa snapshot, không đại diện cho lần
OCR/bổ sung này. Các thay đổi vẫn local, chưa commit/push.

```powershell
# Cần môi trường EasyOCR và hai model đúng hash trong run_inputs.json.
# Sau khi tải model vào cache, OCR runner không truy cập mạng.
python -X utf8 -m tools.ocr_hus_review --out data/hus/review/p13_ocr_v1 --resume
python -X utf8 -m tools.prepare_hus_syllabus_supplement --out data/hus/review/p13_supplement_new
```

## Kết quả audit ban đầu (snapshot giữ nguyên)

| Hạng mục | Kết quả |
| --- | --- |
| Payload portable release | Kiểm lại hash/size của 46 payload và định danh release đã chọn |
| File nguồn | **17/17** khớp SHA-256: **15 PDF + 2 DOCX**; gồm registry cũ, PDF chương trình và hai PDF đề cương đã có trong Git |
| Trang PDF được trích lại/triage | **787 trang**, nguồn thực, không tạo PDF thay thế |
| Candidate đề cương | **106 mục**: 44 KHMTTT, 62 Toán tin; **84 mục có liên kết canonical** |
| Quote/trang | **273/273** khớp offset/capture hash, phạm vi trang vật lý và tìm thấy lại bằng PDFium trên binary đúng hash |
| Trang ít text | **72** trang cần kiểm ảnh/OCR; không tự coi là trang trắng hoặc scan đã xử lý |
| Nguồn lịch sử | **69/106** khả dụng, **37** chưa có bản gốc trong phạm vi kiểm; không có nguồn F1 mặc định nằm trong nhóm thiếu |
| Pending OCR lịch sử | **6 mục** chưa đóng: 2 đã có binary trong lần audit, 4 vẫn thiếu; có binary không tự giải quyết trạng thái OCR |
| Bằng chứng mã môn cũ | Tham chiếu **297 dòng** code/page audit; đây không phải full-text OCR hay xác minh mọi ô bảng |
| Nâng duyệt / xác nhận hiệu lực mới | **0 / 0** |

“Đã kiểm kỹ thuật” nghĩa là byte/locator/text có thể truy vết. Nó không xác nhận mọi
nội dung đúng học vụ, còn hiệu lực, tương đương byte của lần crawl lịch sử hoặc áp
dụng cho hồ sơ sinh viên hiện tại. Text PDF và bảng vẫn cần review trực quan/ngữ nghĩa.

## Hai PDF đề cương được tái dùng

Đọc nguyên binary từ commit upstream `a543cf8d1fac273db41a65a14fb7ae0a05b2d965`, giữ
provenance/tác giả nguồn. Cache chỉ nằm trong `backups/hus_source_review/p13/originals/`,
không chép vào `citation_assets` hoặc release đang dùng.

| Nguồn | SHA-256 / trang | Nội dung bìa đã quan sát |
| --- | --- | --- |
| [KHMTTT — PDF ghim](https://raw.githubusercontent.com/5-Bit-System/SE_Project/a543cf8d1fac273db41a65a14fb7ae0a05b2d965/data/hus/recovery/20261031/files/56d751cc897fe12626f05ebaa28842440e3b6402dede058bd280d6f3c1def2d0.pdf#page=1) | `56d751cc897fe12626f05ebaa28842440e3b6402dede058bd280d6f3c1def2d0`, **256 trang** | Trang bìa ghi QĐ đề cương **2385/QĐ-ĐHKHTN, 31/07/2024**; dẫn QĐ chương trình **3568/QĐ-ĐHKHTN, 18/10/2023**, hệ chuẩn |
| [Toán tin — PDF ghim](https://raw.githubusercontent.com/5-Bit-System/SE_Project/a543cf8d1fac273db41a65a14fb7ae0a05b2d965/data/hus/recovery/20261031/files/6e049389bc467f41ea6d48cffd66182c50bf52e77efdbb57868dbe6f14f33b7b.pdf#page=1) | `6e049389bc467f41ea6d48cffd66182c50bf52e77efdbb57868dbe6f14f33b7b`, **281 trang** | Trang bìa ghi ngành Toán Tin, mã 7460117, bậc đại học, **Hà Nội 2021** |

Đã render và đọc bìa bằng AI hỗ trợ, đối chiếu text; chưa có người duyệt học vụ ký.
Các số quyết định/năm trên là **tuyên bố trong bản tài liệu đã ghim**, không phải
kết luận hiệu lực vào 02/11/2026. Nguồn Toán tin2021 không được tự gắn với CTĐT
cohort2022/QD3567-2023: trong84 liên kết,47 mục nguồn2021 được gắn blocker edition cũ.
Ngay cả KHMTTT có decision trùng canonical cũng cần xác nhận phạm vi áp dụng.

Đã thử mở lại hai URL gốc trên `mim.hus.vnu.edu.vn`; công cụ fetch timeout, không có
HTTP status từ server nguồn hoặc hash binary live. Hai truy vấn giới hạn trên domain
chính thức không có kết quả. Điều này **không chứng minh 404, tài liệu bị thu hồi hoặc
hết hiệu lực**. Xem [web_checks.jsonl](../data/hus/review/p13_source_audit_v1/web_checks.jsonl).

## Candidate nào vẫn bị chặn

Giữ nguyên toàn bộ106 mục là `source_extracted_candidate`,
`academic_verified=false`, `candidate_not_in_default_retrieval`; không parse tỷ lệ thi
từ text thành official facts. Số lỗi identity được kế thừa từ release:

| Vấn đề | Số lượt |
| --- | ---: |
| Mã ngoài canonical của ngành | 18 |
| Mã/tên không thống nhất | 3 |
| Mã lặp trong nguồn đề cương | 2 |
| Mã thiếu tiền tố | 1 |

Một candidate có thể có nhiều lỗi.84 liên kết canonical chỉ là bước liên kết identity,
không phải84 đề cương đã được phê duyệt. Chưa có candidate đề cương nguồn thật trong
bộ này cho Toán học/KHDL; không suy ra ngoài đời không có đề cương của hai ngành.

Các trường tìm thấy trong snapshot v3 ban đầu: content105, objectives102, assessment60. Tương ứng
còn1/4/46 mục thiếu trường đó. Không lấp chỗ trống bằng nội dung AI rồi gọi là nguồn
chính thức. F3 runtime vẫn là290 hồ sơ AI tham khảo, ba trường official giữ null;
sign-off F2 vẫn67 verified cấp dự án và223 draft, không có xác minh của trường mới.

## OCR và nguồn còn thiếu

[ocr_queue.jsonl](../data/hus/review/p13_source_audit_v1/ocr_queue.jsonl) liệt kê72
trang có dưới50 ký tự không-whitespace, gắn hash PDF và số trang. Trong đó22 trang
đã có bằng chứng code/page audit cũ; bằng chứng này chỉ kiểm mã môn, không thay văn
bản OCR đầy đủ hoặc review mọi ô. Các trang còn lại cũng chưa được coi là trắng.

Lần audit ban đầu chưa chạy OCR. Không tìm thấy Tesseract trên PATH hoặc hai thư mục
cài đặt Windows thông dụng đã kiểm; công cụ audit ban đầu chỉ đọc text layer bằng
PDFium. Lần tiếp tục sử dụng EasyOCR như ghi ở trên. Ngay cả715 trang không bị heuristic ít text đánh dấu
cũng chưa có chứng nhận độ đúng text/bảng.

[missing_sources.jsonl](../data/hus/review/p13_source_audit_v1/missing_sources.jsonl)
ghi37 nguồn thiếu, tách khỏi72 trang có binary và cần OCR/visual check.
[historical_ocr_blockers.jsonl](../data/hus/review/p13_source_audit_v1/historical_ocr_blockers.jsonl)
giữ6 blocker cũ; 2 đã có nguồn để kiểm tiếp, không tự đóng review. Không cộng các tập
này như những tài liệu độc lập: có giao nhau, và đơn vị đếm trang khác tài liệu.

## Artifact và cách kiểm lại

| File trong review pack | Vai trò |
| --- | --- |
| [report.json](../data/hus/review/p13_source_audit_v1/report.json) / [manifest.json](../data/hus/review/p13_source_audit_v1/manifest.json) | Tổng hợp, hash đầu vào/output/tool và giới hạn |
| [binary_assets.jsonl](../data/hus/review/p13_source_audit_v1/binary_assets.jsonl) |17 file, hash, nguồn/binding, page count; hai syllabus là review-only |
| [page_triage.jsonl](../data/hus/review/p13_source_audit_v1/page_triage.jsonl) |787 trang, text hash, số ký tự và trạng thái pending |
| [candidate_reviews.jsonl](../data/hus/review/p13_source_audit_v1/candidate_reviews.jsonl) |106 candidate,273 span checks, link canonical, blocker và reviewer/time null |
| [source_inventory_review.jsonl](../data/hus/review/p13_source_audit_v1/source_inventory_review.jsonl) |106 nguồn lịch sử và cơ sở kiểm khả dụng; hash UTF8-LF archive không bị gọi là hash byte HTTP |
| [Biên bản chuẩn bị P1-3](acceptance/hus_p13_source_review_report.json) | Cover observations, kiểm thử, bảo toàn dữ liệu và phần còn chờ |

```powershell
python -m pytest tests/hus/test_source_review_audit.py -q
python -X utf8 -m tools.audit_hus_source_review --out data/hus/review/p13_new_audit --web-checks data/hus/review/p13_source_audit_v1/web_checks.jsonl
```

Lệnh thứ hai tạo thư mục mới, dùng lại hồ sơ web check cũ (không có truy cập web
mới). Cache phải ở thư mục riêng trong `backups/`, tách output; tool từ chối mọi cache
trong cây nguồn/runtime **trước khi ghi**. Khi thiếu Git object upstream trên clone
mới, lấy lại commit đã ghim hoặc cung cấp cache đúng SHA; không tạo file thay thế.
Hai PDF hơn22MB chỉ nằm trong cache ignored, không nhân bản vào Git review pack.

Một ca thử đường dẫn ban đầu đã tạo6 bản sao PDF tạm ở cây nguồn; đã kiểm đúng hash
rồi xóa6 bản sao, giữ nguyên original/registry/release. Test đã đổi sang sentinel
chặn thao tác mkdir và guard được sửa; trạng thái Git của các cây nguồn sạch sau
kiểm tra. Bản audit cuối được chạy lại bằng tool đã sửa; không giữ kết quả cũ như
thể dùng code mới. Chi tiết trong biên bản kỹ thuật.

## Việc còn lại để nghiệm thu P1-3

1. Người có thẩm quyền xác nhận edition/decision/cohort và hiệu lực hiện tại; ưu tiên
   84 liên kết canonical, xử lý riêng các identity blocker. Lưu reviewer, ngày và
   evidence thực; không ký thay người duyệt.
2. Review ảnh/text/table của72 trang đã OCR, tái dùng code audit cũ đúng phạm vi;
   ưu tiên45 occurrence chưa thấy token mã và1.788 vùng có confidence thấp.
   OCR ra text vẫn phải đối chiếu từng ô/quan hệ bảng, không tự cấp approval.
3. Thu hồi37 raw còn thiếu có chọn lọc trong phạm vi dự án; giữ blocker nếu chưa có
   byte/version đủ căn cứ. Xử lý6 pending OCR theo từng tài liệu.
4. Chỉ sau review đủ căn cứ mới chuẩn bị release mới, đăng ký binary/citation và
   nghiệm thu lại. P1-3 hiện không đổi CURRENT, active resolver hoặc policy official F3.

Các thay đổi đang local trên crawldata; chưa commit/push hoặc kích hoạt production.
