# Bàn giao tích hợp RAG vào main — P0-4

Đây là gói local reviewable được tái tạo và kiểm thử; chưa merge/push.

- `main.patch`: thay đổi nhỏ trên main cùng module UI/service/test mới.
- `manifest.json`: main base, hash patch, 77 input dùng lại từ crawldata và hash 34
  source outputs đã nghiệm thu. Code dùng UTF-8/LF để so hash; data giữ nguyên bytes.
- [Biên bản, kiến trúc và test](../../docs/RAG_P04_MAIN_INTEGRATION.md).
- [Công cụ tái tạo](../../tools/prepare_hus_main_integration.py).

Main base: `5239b7333a8f8cdf0f919e6b0505af0def99fe23`.
Worktree thực hiện: `backups/hus_integration/p04-main/`.
Branch: `integration/hus-rag-p04-20261102`.

Từ root crawldata:

```powershell
python -X utf8 -m tools.prepare_hus_main_integration --target backups/hus_integration/p04-new
```

Công cụ tạo **worktree mới** và kiểm hash sau apply. Nếu thiếu object main đã ghim,
fetch commit đó trước. Công cụ không ghi đè checkout hiện có, không commit/push và
không thêm review cho dữ liệu. Giữ đủ input trong crawldata; source đã đổi sẽ bị từ
chối để tránh ghép các phiên bản.

Đã kiểm bản tái tạo tại `backups/hus_integration/p04-replay-check03/`: output source/
data khớp, 41 test backend và 9 test Node đạt. Khi phát hành main, dùng feature branch
và PR, giữ ancestry/contribution của các nhánh nguồn; patch không thay thế lịch sử Git.
