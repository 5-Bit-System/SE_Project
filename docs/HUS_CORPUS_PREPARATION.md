# Chuẩn bị corpus HUS có thể tái lập

Phạm vi P0 ngày 2026-10-25: từ catalog, Markdown, raw đã ghim và quyết định review tường minh,
tạo lại inventory, hàng đợi review, bản chuẩn hóa và corpus ứng viên. Công cụ chạy offline,
không crawl, gọi LLM, OCR, cập nhật database hay kích hoạt index của chatbot.

Baseline hiện tại là `hus-0404f37-20261026`, đã cập nhật theo hai commit sửa bảng trên remote
trước khi publish ngày 26/10. Không phải phục dựng build07 được nhắc trong báo cáo
ngày 23/10. Không có hồ sơ build07 trong checkout để nhập quyết định cũ. Baseline mới giữ
100 tài liệu `needs_review`, 6 `pending_ocr`, 0 `include`, 0 `exclude`; do đó corpus/chunks rỗng.
Có thể kiểm chứng luồng xuất corpus không rỗng bằng fixture tổng hợp trong `tests/hus/test_corpus.py`.

## 1. Đầu vào được version trong Git

| File | Vai trò |
| --- | --- |
| `data/hus/corpus/source_manifest.json` | Vị trí snapshot bất biến, đủ 106 ID/URL, đường dẫn Markdown/raw và SHA-256 của 162 file có thật. |
| `data/hus/corpus/review_decisions.json` | Quyết định của đủ 106 ID, gắn với hash nội dung; lý do và bằng chứng review khi có. |
| `data/hus/corpus/build_config.json` | Phiên bản schema/pipeline, phép chuẩn hóa và cấu hình chia chunk. |
| `data/hus/corpus/baseline_validation_report.json` | Kết quả nghiệm thu cấu trúc của baseline; không phải xác nhận học vụ. |
| `data/hus/corpus/baseline_build_manifest.json` | Build ID và checksum 115 output của build nghiệm thu; test đối chiếu toàn bộ manifest tái tạo. |

Snapshot nguồn nằm trong commit đầy đủ `0404f37c1b6c3864b7fe2e9938a8a21f777663f0` của
`https://github.com/5-Bit-System/SE_Project.git`, thư mục `data/hus/`.
Trường `source_location` dùng URI `git+...@<full SHA>#data/hus`; không dùng tên nhánh di động.
File lớn đã có trong commit này được tham chiếu lại, không nhân bản vào thư mục corpus.

Checksum `utf8-lf` là SHA-256 của UTF-8 sau chuyển CRLF/CR thành LF, để cùng snapshot Git
kiểm tra được trên Windows/Linux. Không NFC, cắt khoảng trắng hoặc đổi nội dung trước phép hash
đầu vào. Đây là checksum văn bản trong repository, **không phải hash byte HTTP ban đầu**.
Nếu có bản đính kèm nhị phân, encoding là `binary` và hash đúng từng byte.
Hash bản chuẩn hóa được lưu riêng, không thay thế hash nguồn.

Có 55 raw HTML ánh xạ bằng hash URL trong tên file. 51 bản PDF/DOCX chưa có file gốc tại
snapshot; manifest ghi `raw_path: null`, inventory ghi `original_attachment_missing`.
Hai HTML `diagnostic-*` và các file raw không được manifest liệt kê không tham gia build.

## 2. Chạy build và kiểm chứng

Dùng Python 3.11 và dependency hiện có trong `requirements-dev.txt`/`requirements-lock.txt`.
Không có dependency mới. Chạy tại repository root:

```powershell
python -X utf8 -m tools.prepare_hus_corpus build --out backups/rag_preparation/p0-build01
python -X utf8 -m tools.prepare_hus_corpus verify --out backups/rag_preparation/p0-build01
```

`build` chỉ ghi vào thư mục mới, qua staging rồi đổi tên. Nếu đích đã tồn tại, lệnh fail;
chọn tên build khác. Đích không được trùng, nằm trong hoặc bao trùm cây nguồn.
Không ghi vào catalog, Markdown/raw, config hoặc review đầu vào.

`verify` dựng lại trong bộ nhớ rồi so **từng byte và tập tên file** với build được chỉ định.
Thiếu/thừa file, checksum nguồn sai, nội dung Markdown lệch catalog, quyết định review cũ,
thiếu ID hoặc hash output khác đều làm lệnh trả exit code 1. Thành công trả 0.
Không đưa timestamp hiện tại, đường dẫn máy hay tên thư mục output vào artifact.

Nếu thư mục crawl trên máy đã thay đổi, lấy lại nguồn theo commit cố định, không sửa manifest
để bỏ qua lỗi. Ví dụ dùng object Git đã có trên máy:

```powershell
New-Item -ItemType Directory -Force backups/rag_preparation
git archive --format=zip --output=backups/rag_preparation/hus-0404f37-source.zip 0404f37c1b6c3864b7fe2e9938a8a21f777663f0 data/hus
Expand-Archive -LiteralPath backups/rag_preparation/hus-0404f37-source.zip -DestinationPath backups/rag_preparation/hus-0404f37-source
python -X utf8 -m tools.prepare_hus_corpus build --source-root backups/rag_preparation/hus-0404f37-source/data/hus --out backups/rag_preparation/p0-from-git01
python -X utf8 -m tools.prepare_hus_corpus verify --source-root backups/rag_preparation/hus-0404f37-source/data/hus --out backups/rag_preparation/p0-from-git01
```

Nếu thiếu object, lấy đúng commit từ repository trên trước khi archive; không dùng nội dung
nhánh mới thay cho snapshot. Source manifest kiểm tra từng file sau giải nén, không phụ thuộc
hash của container ZIP. Git object và checksum từng file là cơ chế lấy/kiểm chứng nguồn hiện tại;
không có kho lưu PDF/DOCX gốc bên ngoài được giả định là tồn tại.

## 3. Artifact của mỗi build

| Artifact | Nội dung |
| --- | --- |
| `source_manifest.json`, `build_config.json`, `review_decisions.json` | Bản sao canonical của toàn bộ contract đầu vào. |
| `inventory.jsonl` | Một dòng mỗi ID: nguồn, hash, nhãn crawler, trạng thái review, cờ thiếu nguồn/bảng/OCR/ngày/trùng text. |
| `document_review.jsonl` | Đủ 106 quyết định, lý do, reviewer và bằng chứng; không tự suy quyết định từ nhãn crawler. |
| `normalized/<document_id>.md` | Đủ 106 bản chuẩn hóa NFC, LF, bỏ space/tab cuối dòng và chuẩn hóa newline ngoài cùng. Không sửa số liệu/bảng. |
| `documents.jsonl` | Chỉ tài liệu `include`; metadata và nội dung chuẩn hóa. |
| `chunks.jsonl`, `source_map.jsonl` | Chunk của tập `include`, ID ổn định, URL/hash và locator trong bản chuẩn hóa. |
| `validation_report.json` | Số tài liệu/trạng thái/cờ/chunk; luôn ghi `candidate_only: true`, `active_release: false`. |
| `manifest.json` | Build ID, hash mã công cụ/model, hash contract và SHA-256 của mọi output còn lại. Không tự hash chính nó. |

Chia chunk `utf8-lines-v1`: ưu tiên nguyên dòng, tối đa 2.400 byte UTF-8/chunk, overlap 0.
Dòng dài được cắt tại ranh giới ký tự Unicode; các span liên tiếp ghép lại đúng toàn bộ text.
Đây là baseline kỹ thuật, chưa tối ưu theo tokenizer hoặc chứng minh phù hợp bảng dài.
Locator `normalized_markdown` gồm offset ký tự `[start_char, end_char)` và dòng bắt đầu/kết thúc;
không được diễn giải thành locator trang/ô bảng gốc đã được xác minh.

Text giống nhau chỉ được ghi ứng viên trùng, không tự gộp hoặc bỏ nguồn.
`major`, `document_type` vẫn là nhãn crawler; ngày/năm thiếu vẫn null.
Nội dung crawl được xử lý như dữ liệu, không thực thi chỉ dẫn có trong văn bản.

## 4. Review và snapshot tiếp theo

Mọi quyết định gắn với `content_hash` của catalog; sửa nội dung buộc cập nhật review tường minh.
`active` là trạng thái crawler, không phải đã duyệt. `include` chỉ xuất được khi:

- Nguồn crawler là `active`, có raw được manifest hash và kiểm tra.
- Có `reviewer`, `reason`, `evidence_locator` và `reviewed_source_sha256` khớp raw đã ghim.
- Quyết định thuộc đúng snapshot và đúng hash nội dung.

Cổng này ghi trách nhiệm/bằng chứng review, không tự xác nhận hiệu lực học vụ, độ đúng từng ô
bảng hoặc độ chính xác OCR. Những việc đó vẫn phải thực hiện trước khi reviewer chọn `include`.
Sau OCR phải tạo snapshot/review mới với nội dung và trạng thái tương ứng, không đổi nhãn của
snapshot cũ chỉ để vượt kiểm tra. Không tự dùng 6 trang đã chọn ở build07 khi chưa có hồ sơ.

Để tạo contract cho nguồn mới, dùng tên file/config/build mới và vị trí nguồn bất biến có thật:

```powershell
python -X utf8 -m tools.prepare_hus_corpus manifest --source-root PATH_TO_NEW_SNAPSHOT --snapshot-id NEW_SNAPSHOT_ID --source-location IMMUTABLE_GIT_OR_ARCHIVE_LOCATION --out NEW_CONTRACT_DIR/source_manifest.json
python -X utf8 -m tools.prepare_hus_corpus init-reviews --source-root PATH_TO_NEW_SNAPSHOT --manifest NEW_CONTRACT_DIR/source_manifest.json --out NEW_CONTRACT_DIR/review_decisions.json
```

Hai lệnh này từ chối ghi đè file đã tồn tại. Sao chép cấu hình build sang thư mục contract mới,
đặt đường dẫn manifest/review tương đối với config, review từng ID rồi chạy `build --config ...`.
Nếu nguồn lớn nằm ngoài Git, bên bàn giao phải cung cấp vị trí archive bất biến có thể lấy được;
checksum từng file nằm trong manifest, bao gồm `binary` cho tài liệu gốc. Công cụ không tự tải
archive hoặc credential và không chứng minh một URI bất kỳ đang truy cập được.

## 5. Nghiệm thu và giới hạn

```powershell
python -m pytest -q tests/hus/test_corpus.py
python -m ruff check .
```

Test bao gồm build không rỗng trên nguồn tổng hợp, Unicode/byte limit, ánh xạ chunk về nguồn,
CRLF/LF và đổi đường dẫn máy, thiếu/thay đổi nguồn, review cũ/thiếu/sai snapshot, OCR chưa duyệt,
chặn traversal, phát hiện output sửa, từ chối ghi đè và baseline sản phẩm đủ 106 ID.
CI chạy build + verify offline và giữ artifact để kiểm tra. Dữ liệu sản phẩm chưa được xác minh
học vụ; 0 chunk ở baseline không phải lỗi công cụ và cũng không có nghĩa RAG đã sẵn sàng.

P0 không khôi phục 51 binary còn thiếu, xử lý 6 OCR, duyệt 49 tài liệu có bảng, sửa nhãn ngành,
đánh giá retrieval/citation hay phát hành corpus active. Các phần này là công việc tiếp theo.
