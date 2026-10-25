# Dữ liệu HUS (crawl)

Crawler hiện dùng `config/sources.json` để quyết định host, path và seed. Crawler kiểm tra `robots.txt` khi chạy. Kiểm tra cấu hình mà không gửi HTTP:

```powershell
python -X utf8 -m tools.run_hus_crawler --dry-run
```

- `path_prefixes` khớp theo ranh giới path: `/vi/news` không khớp `/vi/newsletter`.
- Lệnh crawl: `python -X utf8 -m tools.run_hus_crawler`; ghi `processed/catalog.json`, Markdown và raw. Đây là tác vụ mạng, không phải bước tái tạo corpus offline.
- `processed/` và các HTML đã chọn được theo dõi trong Git; `raw/documents/` và `state/` hiện bị Git ignore. Thiếu PDF/DOCX phải được ghi rõ, không suy rằng text đã trích xuất là bản gốc.
- `allowlist.json` rỗng; `tools.build_hus_index` chỉ còn kiểm tra cấu hình/dry-run. Đường xuất index trực tiếp từ crawl đã bị vô hiệu hóa vì không có hồ sơ duyệt.
- Không trộn với `data/curricula`. Fixture ở `tests/fixtures/hus/` là HTML giả, không phải nguồn HUS thật.

Quy trình chuẩn bị corpus offline và cách lấy đúng snapshot: [HUS_CORPUS_PREPARATION.md](../../docs/HUS_CORPUS_PREPARATION.md).
Contract đầu vào được lưu tại `corpus/{source_manifest.json,review_decisions.json,build_config.json}`.
Chạy từ thư mục gốc repository, dùng một tên build mới:

```powershell
python -X utf8 -m tools.prepare_hus_corpus build --out backups/rag_preparation/p0-build01
python -X utf8 -m tools.prepare_hus_corpus verify --out backups/rag_preparation/p0-build01
```

Baseline mới có 106 tài liệu: 100 `needs_review`, 6 `pending_ocr`, 0 `include`.
Không nhập lại quyết định 6 `include` của build07 vì hồ sơ review đó chưa có trong checkout.
Corpus rỗng là kết quả minh bạch của baseline này; công cụ không tự xác nhận học vụ hay phát hành RAG.

Pipeline 1.2 giữ cổng duyệt chung của 1.1 với `HUSIndex` và `chunk_document()`. `include` phải có
URL nguồn, hash nội dung/raw, reviewer, `reviewed_at` có múi giờ và locator bằng chứng.
Hiệu lực chưa rõ giữ `unknown` và chỉ dùng cho thông tin mô tả. Xem mục review trong hướng dẫn
để cấu hình `as_of` khi xuất dữ liệu được xác minh là hiện hành.

Raw mới lưu bất biến theo SHA-256 kèm `raw/provenance.jsonl` và `HUSDocument.raw_source`.
Đã nhập 2 PDF local có text khớp catalog; vẫn chưa xác minh phiên bản gốc. Có hàng đợi 49 URL
còn thiếu tại `recovery/20261026-local-originals-final/recovery_queue.jsonl`. Nguồn/corpus ghim
snapshot cũ được giữ nguyên. Xem [quy trình provenance và recovery](../../docs/HUS_RAW_PROVENANCE.md).

Pipeline hiện tại là **1.4**, giữ `corpus/applicability.json` tách proposal/verified cho đủ 106 ID.
Hai trang Địa chất/Địa lý có proposal out_of_scope và bị chặn xuất; 53 nguồn còn unknown, không
coi là general. Mọi verified metadata khác unknown cần locator khớp nguồn, reviewer và thời gian.
Snapshot nguồn giữ nguyên; dùng metadata bổ sung để sửa phạm vi sử dụng. Xem
[hướng dẫn metadata áp dụng](../../docs/HUS_APPLICABILITY_METADATA.md). Build 1.4 có 120 artifact.

Chất lượng/OCR được báo cáo từng trang PDF; bảng giữ riêng raw và bản hiển thị, có ID hàng/cột/ô,
header, ô gộp và locator nguồn. Corpus/index bắt buộc hồ sơ đối chiếu từng trang/bảng/ô, không tự
duyệt từ trạng thái active. Tạo báo cáo bằng `python -X utf8 -m tools.inspect_hus_source_quality --out backups/rag_preparation/quality01`.
Xem [hướng dẫn đối chiếu nguồn](../../docs/HUS_SOURCE_QUALITY.md) và [báo cáo local](quality/20261026/report.json).
