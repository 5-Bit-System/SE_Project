# Chất lượng nguồn, bảng và OCR theo trang

Pipeline corpus **1.4**, ngày 2026-10-26, thêm báo cáo chất lượng và hồ sơ đối chiếu
vào cổng duyệt chung của corpus, `chunk_document()` và `HUSIndex`. Phạm vi xuất vẫn là
toàn tài liệu: còn một trang/ô chưa kiểm tra thì cả tài liệu chưa được xuất. Chưa hỗ trợ
phát hành riêng một phần tài liệu hoặc chạy OCR để sửa nội dung.

## Tạo báo cáo

Chạy từ repository root, chọn thư mục output mới:

```powershell
python -X utf8 -m tools.inspect_hus_source_quality --out backups/rag_preparation/quality01
```

Lệnh kiểm tra nguồn theo `data/hus/corpus/source_manifest.json`, không sửa raw, catalog,
Markdown hoặc quyết định review. Muốn phân tích thêm hai candidate đã thu hồi trên máy này:

```powershell
python -X utf8 -m tools.inspect_hus_source_quality --recovery data/hus/recovery/20261026-local-originals-final/inventory.jsonl --out backups/rag_preparation/quality-recovery01
```

Recovery phải khớp document ID, URL và SHA-256. Hai binary recovery ở ngoài Git; máy khác
cần có đúng các file/hash trong inventory trước khi dùng tùy chọn này. Không có binary thì
chạy lệnh đầu: giữ blocker cho 51 attachment của snapshot cũ. Tham khảo
[provenance/recovery](HUS_RAW_PROVENANCE.md) để phân biệt candidate với phiên bản gốc đã xác minh.

| Output | Nội dung |
| --- | --- |
| `source_quality.jsonl` | Report theo document ID, raw path/hash/encoding, hash report, nội dung hiển thị và kiểm tra khớp catalog. |
| `page_quality.jsonl` | Từng trang PDF: ID, số trang từ 1, text thô/hiển thị, số ký tự, ảnh, nét/shape và locator. |
| `tables.jsonl` | Bảng có ID hàng/cột/ô, giá trị thô, bản hiển thị, header, spans và locator nguồn. |
| `ocr_queue.jsonl` | Từng trang ít text cần kiểm tra trực quan/OCR, kèm URL, hash và page ID; không tự chạy OCR. |
| `source_blockers.jsonl` | Thiếu raw hoặc lỗi phân tích; không bịa số trang cho file chưa có. |
| `review_queue.jsonl` | Mỗi trang/bảng/ô cần đối chiếu: ID, locator, hash unit/report, trạng thái `needs_review`; không có reviewer giả. |
| `report.json` | Số lượng, blocker, hash đầu vào/mã công cụ/output; không tự cấp xác minh hoặc kích hoạt RAG. |

Không có timestamp hiện tại hoặc đường dẫn tuyệt đối máy trong report. Cùng nguồn và mã công cụ
tạo cùng output. CLI từ chối ghi đè một lần chạy cũ. Corpus build cũng xuất
`source_quality.jsonl`, `ocr_queue.jsonl`, `quality_blockers.jsonl`, được checksum trong manifest.

## Trang và bảng được biểu diễn thế nào

Ngưỡng nghi vấn OCR là **dưới 50 ký tự đã làm sạch trên từng trang**, thay phép lấy trung bình
toàn PDF. PDF có trang text dài và trang scan xen giữa vẫn có `needs_ocr=true`. Đây là tín hiệu
sàng lọc; mọi trang PDF đều cần hồ sơ kiểm tra trước khi xuất, kể cả trang trên ngưỡng.

Trang ít text không tự được coi là trắng. Người kiểm tra phải xem trang gốc và ghi
`blank_verified` (không text, ảnh hoặc graphic) hoặc `short_text_verified` (có text ngắn,
không ảnh) nếu có căn cứ. Trang ảnh/scan chưa xử lý vẫn bị chặn. `ocr_pending` không được xuất.
Sau OCR cần quy trình xuất bản trích xuất được đối chiếu, snapshot/review mới; hiện chưa có
đường đưa kết quả OCR tùy ý vào index.

`SourceTable.raw_rows` giữ giá trị trích xuất, bao gồm dòng trống, khoảng trắng và `null`.
`display_markdown`/`display_value` là bản trình bày riêng. Không dùng thao tác pad cột, bỏ dòng
trống hay làm sạch ký tự để khẳng định nguồn đúng. `presence` phân biệt `present`, `empty`,
`missing`, `covered` và `unresolved`. Ô bị che bởi ô gộp có `covered_by`; ô gốc có `rowspan`/
`colspan`. Header có hàng, đường dẫn theo cột, vai trò và scope từng ô; đề xuất header chưa phải
kết quả duyệt. HTML phân biệt header hàng với header cột. Hồ sơ bảng ghi các hàng header đã
đối chiếu; consumer cần dùng hồ sơ này khi dựng ngữ cảnh bảng.

Locator PDF chứa trang/bbox và tọa độ hàng/cột; DOCX chứa vị trí block/XPath; XLSX chứa sheet/
địa chỉ ô; HTML chứa thứ tự table trong DOM gốc và hàng/cột. Hàng/cột bắt đầu từ 0. Locator
luôn đi cùng URL, encoding và hash raw trong report. HTML và DOCX/XLSX không được gán số trang
vì chưa có bản render cố định. Công thức XLSX giữ nguyên công thức, chưa coi là số đã tính.
Ô thiếu, công thức chưa có kết quả nguồn được duyệt, span chồng lấn hoặc grid không giải quyết
được đều bị chặn; phải sửa quy trình trích xuất/nguồn và đối chiếu lại.

Các table detector còn giới hạn: PDF có thể bỏ sót bảng không đường kẻ, ảnh hoặc cấu trúc
phức tạp; ngưỡng ký tự không đo độ đúng OCR. Người kiểm tra trang phải phát hiện những trường
hợp này. Không có điểm OCR accuracy hoặc chứng nhận số liệu được suy ra từ số ký tự.

## Ghi hồ sơ đối chiếu và xuất

Model nằm tại `app/hus/quality_models.py`; kiểm tra tại `app/hus/quality.py`.
Trong `ReviewDecision.source_quality`, điền:

- `report_sha256`: hash canonical của report, gồm cả raw hash và nội dung hiển thị.
- `page_checks`: key là page ID; từng trang có `outcome`, `expected_sha256`, `locator`,
  `reviewer`, `reviewed_at` có múi giờ và `resolution`.
- `table_checks`: key là table ID; cùng thông tin trên, thêm `confirmed_header_rows`.
- `cell_checks`: key là cell ID; mỗi ô gốc, kể cả ô rỗng, cần `observed_value` đúng giá trị
  đã đọc từ nguồn. Ô `covered` được đối chiếu qua hình học/spans của bảng và ô gốc.

Dùng `review_queue.jsonl` để tìm đúng unit và hash, rồi mở raw tại locator để đối chiếu.
Không chuyển cả queue thành `verified` tự động. Chỉ người đã đối chiếu mới ghi tên/thời gian
và outcome `verified`. Bản chưa duyệt có thể để thiếu check; cổng xuất sẽ chặn. Giữ nguyên
các điều kiện P0: crawler active, review include, bằng chứng nguồn, content/raw hash đúng và
hiệu lực phù hợp. Dùng `utf8-lf` cho HTML snapshot Git, `binary` cho byte HTTP hoặc attachment;
hai kiểu checksum/report không hoán đổi cho nhau.

Lúc xuất, gate **đọc lại raw và trích xuất lại**. Không tin report cache trong catalog/index.
Phải có đúng tập ID trang/bảng/ô; thiếu, thừa, outcome chưa verified, sai locator/value/hash
hoặc review sau `as_of` đều bị chặn. Markdown sửa số nhưng giữ raw/report cũ cũng bị chặn,
kể cả đã đổi content hash và duyệt lại ở cấp document. Parser lỗi làm export thất bại; index
nạp/lưu sẽ bỏ bản ghi không còn hợp lệ. Thay đổi raw hoặc extractor buộc đối chiếu report mới.

Chunks/source map mang `source_quality_sha256` và `source_unit_ids` ở phạm vi **toàn tài liệu**.
Tra ID trong report để tới trang/bảng/ô, không diễn giải chúng như ánh xạ chính xác từng ký tự
chunk tới ô. Markdown có thể làm phẳng header hoặc cắt bảng qua nhiều chunk; khi xây bộ trả lời
phải lấy cấu trúc bảng và hồ sơ đã duyệt làm ngữ cảnh, không tự suy header từ đoạn Markdown.
Module retrieval/trả lời và đánh giá RAG chưa thuộc lần bổ sung này.

## Kết quả nguồn hiện có

Báo cáo nhỏ tại `data/hus/quality/20261026/`; output đầy đủ ở
`backups/rag_preparation/20261026-source-quality-inspection02/` trên máy đã kiểm tra.
Đã phân tích 55 HTML và 2 PDF recovery (17 trang), nhận diện 25 bảng. Tất cả trang/ô vẫn chờ
đối chiếu, 0 được cấp verified. 49 tài liệu thiếu raw, gồm cả 6 tài liệu pending_ocr nên chưa
biết số/trạng thái trang của chúng. Hàng đợi OCR rỗng của 17 trang đã đọc **không** chứng minh
đã xử lý xong 6 tài liệu OCR hoặc 49 nguồn thiếu. Hai PDF vẫn chưa xác minh phiên bản gốc.

Baseline corpus 1.4 giữ snapshot/review cũ: 106 tài liệu, 0 include/chunk, 51 binary thiếu
trong snapshot, 55 quality report. Recovery bổ sung không tự thay manifest hoặc mở cổng duyệt.

Kiểm tra offline:

```powershell
python -m pytest -q tests/hus/test_quality.py tests/hus/test_review_gate.py tests/hus/test_corpus.py
python -m ruff check .
```
