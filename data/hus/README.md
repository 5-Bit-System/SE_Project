# Dữ liệu HUS (crawl)

`allowlist.json` quyết định crawler được vào đâu. `sources` đang **rỗng nên không crawl gì**. Chỉ điền sau khi đã đọc `robots.txt` của từng host và chọn path thuộc thông tin đào tạo.

```json
{"host": "mim.hus.vnu.edu.vn",
 "path_prefixes": ["/vi/cacctrdaotao", "/vi/toanhoc"],
 "seeds": ["https://mim.hus.vnu.edu.vn/vi/cacctrdaotao"]}
```

- `path_prefixes` là tiền tố thuần: `/vi/news` cũng khớp `/vi/newsletter`; thêm `/` ở cuối nếu cần.
- Crawler tự đọc robots.txt khi chạy và bỏ qua path bị chặn.
- Lệnh: `python -m tools.build_hus_index --dry-run` rồi `python -m tools.build_hus_index`.
- `index.json` (tài liệu đã làm sạch + chunk) là dữ liệu công khai; `raw/` (HTML gốc) không commit; `failed.json` là lỗi của lần chạy gần nhất.
- Không trộn với `data/curricula`. Fixture ở `tests/fixtures/hus/` là HTML giả, không phải nguồn HUS thật.