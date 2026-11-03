# Bảo toàn nguồn raw và thu hồi tài liệu HUS

Phạm vi P1 ngày 2026-10-26: giữ byte gốc theo SHA-256, lịch sử từng lần thu thập và liên kết
document ID; sửa conditional fetch khi thiếu raw; đối chiếu hai PDF local và lập hàng đợi các
nguồn còn lại. Không duyệt học vụ, không sửa catalog/Markdown nguồn và không tự nâng review.

## 1. Kho raw mới

`RawStorage` dùng `RawArchive` trong `app/hus/provenance.py`. Đường dẫn có dạng:

```text
raw/html/<major>/<slug>--<url_hash>--<full_sha256>.html
raw/documents/<major>/<slug>--<url_hash>--<full_sha256>.<ext>
raw/provenance.jsonl
```

SHA-256 tính trên **đúng byte nhận được**, không chuẩn hóa newline/Unicode. Cùng URL và nội dung
với cùng tên/phân loại dùng lại file; lần thu thập mới vẫn có event riêng. Nội dung đổi tạo file
khác, giữ phiên bản cũ. Nếu file mang hash đã tồn tại nhưng byte sai, công cụ báo lỗi; không ghi
đè để che mất bằng chứng. Các file legacy không có SHA trong tên không bị di chuyển hoặc sửa.

`provenance.jsonl` là acquisition ledger local, mỗi dòng có event ID, document ID, URL thực,
thời điểm quan sát UTC và kind `fetched`, `not_modified`, `local_import` hoặc `failed`.
Capture thành công có `RawSourceReference`: đường dẫn tương đối, SHA-256, kích thước, loại file,
Content-Type nếu có, fetched_at và version_status. Document ID dùng cùng canonical URL/thuật toán
với catalog. Ledger hỏng phải sửa từ bằng chứng/backup; công cụ không âm thầm bỏ lịch sử.
Chỉ chạy một writer trên cùng root; đây chưa phải kho hỗ trợ nhiều tiến trình ghi đồng thời.

- `captured`: byte gắn với lần tải hiện tại, không xác nhận học vụ hoặc hiệu lực.
- `unverified`: bản nhập local chưa chứng minh cùng phiên bản byte của snapshot cũ.
- Với local import, `observed_at` là lúc nhập; `fetched_at` vẫn null nếu thiếu bằng chứng lần tải
  gốc. Không dùng ngày trong tên thư mục, mtime hoặc ngày review để bịa thời điểm tải.

Raw mới và ledger được Git ignore để giữ byte nguyên vẹn, tránh chuyển CRLF/LF và commit binary
ngoài ý muốn. Các HTML legacy đã được track vẫn giữ nguyên. Trước bàn giao trên máy khác, phải
đóng gói các path được tham chiếu và ledger vào archive bất biến, ghi vị trí lấy và checksum;
không coi file tồn tại local là đã có trên GitHub. Recovery report có URL và hash bản đã tìm
được để đối chiếu khi thu hồi lại; không có kho archive từ xa mới được tự động tạo trong P1.

## 2. Liên kết trong pipeline

Tài liệu được crawl mới có `HUSDocument.raw_source`. Trang cha có `attachments[].raw_path`
được cập nhật sau khi lưu tệp đính kèm. Raw vẫn được giữ khi trích xuất thất bại và có event lỗi.
Phản hồi 200 được lưu kể cả khi text sạch không đổi, vì HTML/attachment byte có thể khác.

Chỉ gửi ETag/Last-Modified khi raw hiện tại còn tồn tại, hash đúng và khớp cặp document/raw đã
lưu. Nếu không có raw hoặc chỉ có bản local chưa xác minh, request bỏ validator. Nếu vẫn nhận
304 mà thiếu raw hoặc tài liệu cache, thử lại một lần với headers rỗng; không có body usable
thì ghi `source_blockers`, `failures` và event `failed`, không giả vờ thành công.
304 hợp lệ ghi một event kiểm tra mới, không thay fetched_at của byte gốc bằng ngày kiểm tra.
Khi phiên bản mới nhất bị mất, không lấy phiên bản cũ hơn để giả thành cache hiện tại.

Snapshot builder dùng raw_source tường minh khi có, kiểm tra document ID, URL, path và hash;
raw capture mới có checksum encoding `binary` kể cả HTML. Legacy snapshot tiếp tục dùng
`utf8-lf` đã khai báo. Corpus pipeline 1.2 giữ cùng cổng duyệt của 1.1 và xuất thêm raw_capture
để chunk/document dẫn về capture cụ thể. Nguồn mới chưa qua review vẫn không được xuất RAG.

## 3. Kết quả hai PDF local

Acquisition record ban đầu:
`data/hus/state/p2-attachments-live-20261021/validation.json` (local, Git ignored).
Báo cáo có thể kiểm tra: `data/hus/recovery/20261026-local-originals-final/`.

| Document ID | SHA-256 của byte đã tìm lại | Trang | Kết quả trích xuất |
| --- | --- | ---: | --- |
| `a211ab8040a69821` | `a79cfa67f594cc34915b5bf8560d26fa9ded844c620f6c745022a4f0b251ffdd` | 8 | Khớp chính xác text catalog, không cần OCR theo extractor hiện tại. |
| `ac3d4c08968d577f` | `3daa8575092b510f722818e3e262c7c6a6d152d3603c07c492bdd7efb204a51a` | 9 | Khớp chính xác text catalog; có dấu DỰ THẢO trong text, không tự xác minh hiệu lực. |

Đây là kiểm tra URL trong acquisition record, kích thước, hash-prefix của filename cũ, full hash
hiện tại, số trang và text trích xuất bằng mã hiện tại. Không có full hash byte gốc từ snapshot,
nên exact text match không chứng minh byte-identical với phiên bản crawl cũ, cũng không thay
việc đọc/đối chiếu số liệu và hiệu lực học vụ. Cả hai giữ `version_status: unverified`,
`review_status: needs_review`, `original_fetched_at: null` và blocker rõ ràng.

Trong 51 URL đính kèm: **2 recovered candidates, 49 queued, 0 verified original versions**.
Inventory giữ đủ 51 ID, queue có 49 ID còn thiếu, comparisons có 2 kết quả đối chiếu.
PDF mới được lưu vào raw/documents và liên kết ID qua ledger/report, không chèn ngược vào
catalog/Markdown hay source manifest bất biến của snapshot 0404f37. Vì vậy báo cáo corpus ghim
snapshot cũ vẫn ghi 51 `original_attachment_missing`; đây là số thiếu trong snapshot đó,
khác với 49 URL còn cần lấy trong hàng đợi recovery mới.

## 4. Chạy lại và bàn giao hàng đợi

```powershell
python -X utf8 -m tools.recover_hus_sources --root data/hus --candidates data/hus/state/p2-attachments-live-20261021/validation.json --out data/hus/recovery/NEW_RUN_NAME
```

Lệnh offline chỉ nhận những candidate khai báo tường minh, có URL trong catalog và file nằm
trong source root; không quét test cache để coi fixture là nguồn. Acquisition record phải có
`final_url`, `raw_path`, `bytes`; tên file cũ kết thúc bằng 12 ký tự đầu SHA-256 để kiểm tra.
Thư mục report phải mới. Khi dùng máy khác, cung cấp lại acquisition record/file gốc đúng hash;
đường dẫn local từ máy hiện tại không phải địa chỉ tải công khai.

Artifact: `report.json`, `inventory.jsonl`, `recovery_queue.jsonl`, `comparisons.jsonl`.
Mỗi queue item giữ document ID, URL, loại file, hash text catalog, expected_original_sha256 null,
blocker và bước tiếp theo. Công cụ không tự đánh dấu nguồn chưa thử là HTTP unavailable.
Đối với 49 URL queued, bước tiếp theo là lấy bằng crawler theo allowlist/robots và không gửi
validator khi raw chưa có; giữ URL cuối, thời điểm, hash và loại response; lỗi HTTP được ledger
ghi riêng. Bản tải mới khác hash candidate/không có expected hash gốc vẫn cần kiểm tra phiên bản.
Không chạy lại toàn bộ web hoặc tự tải cả 49 URL trong nhiệm vụ nhập hai bản local này.

```powershell
python -m pytest -q tests/hus/test_provenance.py
```

Test kiểm tra giữ phiên bản/lịch sử, mất phiên bản mới nhất, file/ledger hỏng, liên kết ID,
HTML/PDF bị mất được tải không validator, HTTP 304 không có body, lỗi nguồn, raw reference
trong snapshot mới và import giữ nguyên catalog, không bịa fetch time/approval.
