# Dữ liệu HUS (crawl)

Crawler hiện dùng `config/sources.json` để quyết định host, path và seed. Crawler kiểm tra `robots.txt` khi chạy. Kiểm tra cấu hình mà không gửi HTTP:

```powershell
python -X utf8 -m tools.run_hus_crawler --dry-run
```

- `path_prefixes` khớp theo ranh giới path: `/vi/news` không khớp `/vi/newsletter`.
- Lệnh crawl: `python -X utf8 -m tools.run_hus_crawler`; ghi `processed/catalog.json`, Markdown và raw. Đây là tác vụ mạng, không phải bước tái tạo corpus offline.
- `processed/` và các HTML đã chọn được theo dõi trong Git; `raw/documents/` và `state/` hiện bị Git ignore. Thiếu PDF/DOCX phải được ghi rõ, không suy rằng text đã trích xuất là bản gốc.
- `allowlist.json` rỗng và `tools.build_hus_index` là lối chạy cũ; không tạo corpus ứng viên theo quy trình mới.
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
