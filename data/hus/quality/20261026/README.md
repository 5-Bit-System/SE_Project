# Báo cáo chất lượng local — 2026-10-26

Lệnh đã chạy:

```powershell
python -X utf8 -m tools.inspect_hus_source_quality --recovery data/hus/recovery/20261026-local-originals-final/inventory.jsonl --out backups/rag_preparation/20261026-source-quality-inspection02
```

Các file trong thư mục này là bản sao nguyên byte từ lần chạy trên:

- `report.json`: 57 nguồn, 17 trang PDF, 25 bảng, 2.093 đơn vị cần đối chiếu;
  checksum đầu vào/mã/output đầy đủ nằm trong report.
- `page_quality.jsonl`: đủ 17 trang đã phân tích, giữ text thô và chỉ số từng trang.
- `ocr_queue.jsonl`: rỗng trong 17 trang này; chưa chạy OCR hoặc duyệt trang nào.
- `source_blockers.jsonl`: 49 tài liệu chưa có raw, trong đó có cả 6 tài liệu pending_ocr.

`source_quality.jsonl`, `tables.jsonl`, `review_queue.jsonl` đầy đủ ở thư mục output local
nêu trên, có hash trong report; tạo lại bằng CLI thay vì nhân bản toàn bộ trong Git.
Không có source/report nào tự được duyệt: verified_pages = verified_cells = 0.
Hai PDF recovery khớp text catalog nhưng phiên bản byte gốc vẫn unverified; cần đúng các
binary/hash trong recovery inventory để tái tạo phần PDF trên máy khác.

25 bảng có 2.029 ô chứa text, 22 ô rỗng và 79 vị trí được ô gộp che. Không phát hiện lỗi grid
trong các bảng nhận diện được; đây chưa phải xác nhận đầy đủ bảng/giá trị của nguồn.
0 hàng OCR không kết luận các tài liệu thiếu raw không cần OCR. Baseline corpus vẫn 0 include.

Quy trình đối chiếu và giới hạn: [HUS_SOURCE_QUALITY.md](../../../../docs/HUS_SOURCE_QUALITY.md).
