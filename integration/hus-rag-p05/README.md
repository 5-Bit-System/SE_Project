# P0-5 — Gói chuẩn bị phát hành

**Chưa phải bản phát hành production.** Chưa commit/push/merge; chờ yêu cầu riêng.

- `main.patch`: P0-4 + CI, receipt identity và lifecycle P0-5 trên main5239b733.
- `manifest.json`: hash patch,77 input dùng lại từ crawldata, output source hashes.
- `PR_BODY.md`: nội dung review dự thảo, chưa gửi GitHub.
- [Tiến độ, kiểm thử và phần còn lại](../../docs/RAG_P05_RELEASE_PREPARATION.md).

```powershell
python -X utf8 -m tools.prepare_hus_main_integration --bundle integration/hus-rag-p05 --target backups/hus_integration/p05-new
```

Đích phải chưa tồn tại. Công cụ không tạo commit hoặc activate. Data so hash nguyên
byte, code so UTF-8/LF. Giữ P0-4 nguyên trạng để audit. Receipt dirty chỉ ghim snapshot
local; chốt ancestry/commit và test strict trước khi dùng làm bằng chứng phát hành.
