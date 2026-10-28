# F1 hiện tại: duyệt thêm 10 nguồn Markdown theo yêu cầu người dùng

Theo yêu cầu “bỏ trang nghề nghiệp trộn Toán Cơ; duyệt 10 tài liệu còn lại”, tập F1 hiện
có **15 nguồn, 66 đơn vị nội dung và 69 chunks RAG**. Tập dùng chung được cập nhật tại
`data/hus/rag/f1/`; F2 và F3 được giữ nguyên.

- 5 nguồn trước đã qua đối chiếu HTML và review toàn tài liệu.
- 10 nguồn bổ sung được duyệt **các phần F1 trên Markdown đã crawl**: mục tiêu cấp chương
  trình/chuẩn đầu ra, nghề nghiệp và hướng học tiếp. Đây là quyết định dùng dữ liệu mô tả
  theo sự cho phép mới của người dùng, không khẳng định đã đối chiếu PDF/DOCX gốc.
- Trang `1f6ad01008734152` có Toán Cơ bị loại khỏi phần bổ sung. HTML/Markdown gốc vẫn
  được giữ làm bằng chứng; không còn chunk của trang này trong tập F1 hiện tại.
- `pending_F1_sections.jsonl` hiện rỗng: cả mười tài liệu đã được xử lý, không còn đoạn chờ.

## Phạm vi và bằng chứng review

`contract/markdown_review_decisions.json` ghi đủ 10 quyết định, hash nội dung và file Markdown,
URL, reviewer thực tế là Codex, timestamp có múi giờ, 24 đoạn đã đọc và vị trí ký tự chính xác.
`reviewed_spans.json` lưu bố trí các đoạn đã chọn. Những phần tuyển sinh, F2 và mục lục bị
trích lẫn trong hàng đợi trước được cắt khỏi phạm vi duyệt.

| Nguồn | Ngành/hệ theo nội dung Markdown | Phiên bản ghi trong Markdown |
| --- | --- | --- |
| `23a0c1df14a5708a` | Toán tin, chuẩn | 2015 |
| `1e3ad5f9915aa051` | KH máy tính và thông tin, chuẩn | 2015 |
| `89d4b39494d72217` | Toán học, chuẩn | 2015 |
| `d4fae066858f0b94` | Toán học, tài năng | 2015 |
| `1c16ddf8a6f1f409` | KH máy tính và thông tin, CLC | 2019 |
| `8afffd3cada3d048` | KH máy tính và thông tin, CLC | 2019 |
| `f7f470e712738589` | KH máy tính và thông tin, chuẩn | 2023 |
| `0dd9aaaeefcbd7d7` | Chuẩn đầu ra Toán tin | unknown |
| `31b55b4ee6f451a6` | Chuẩn đầu ra KH máy tính và thông tin, chuẩn | 2023 |
| `d006f60211246633` | Toán học, tiên tiến | 2008 |

Các giá trị năm/hệ trên phản ánh văn bản đã crawl, không tự xác nhận hiệu lực hiện tại
hoặc áp dụng cho khóa 2022. Không điền số quyết định/ngày ban hành còn để trống trong nguồn.

Đối với nguồn bổ sung, metadata luôn ghi:

```json
{
  "review_status": "include_markdown",
  "review_basis": "extracted_markdown",
  "review_scope": "selected_F1_sections",
  "raw_original_verified": false,
  "academic_verified": false,
  "validity_status": "unknown",
  "usage_scope": "descriptive"
}
```

Chỉ `source_quote` được coi là trích nguyên văn; bản hiển thị bỏ dòng số trang và comment
ngắt trang, giữ nguyên từ ngữ/lỗi glyph trích xuất. Mỗi chunk có cảnh báo rõ chưa đối chiếu
PDF/DOCX gốc, kèm edition và nguồn để RAG không trộn nội dung 2008/2015/2019/2023.

Hai bản CLC có ba phần F1 giống nhau: giữ đủ hai nguồn và quyết định review, nhưng chỉ index
nội dung một lần cho cùng ngành/hệ/năm/trường; `alternate_source_provenance` giữ nguồn thứ hai.
Vì vậy 66 đơn vị nội dung không bị xem thành 66 đoạn độc lập hoàn toàn; RAG có 69 chunks sau
chia phần dài và loại trùng. Không có nội dung F1 AI sinh.

## Tệp và cách dùng

- `release/rag_chunks.jsonl`: 69 chunks F1 hiện tại, gồm cả `include` và `include_markdown`.
  Giữ review_basis/edition/variant khi truy xuất; trả lời theo nguồn mô tả, không xác nhận
  điều kiện hiện hành. Thay tập cũ khi index, không nạp thêm cả bản cũ để tránh lặp.
- `release/documents.jsonl`: 15 nguồn; 10 nguồn bổ sung chỉ xuất những đoạn F1 đã duyệt.
- `release/f1_units.jsonl`, `release/source_map.jsonl`: đoạn nguồn và locator.
- `release/markdown_review_decisions.json`: bản sao contract duyệt Markdown.
- `release/source_inventory.jsonl`: đủ 106 nguồn, 15 được dùng F1 và 91 loại khỏi F1.
- `release/pending_F1_sections.jsonl`: rỗng, giữ tên file để không phá cấu trúc bàn giao.
- `release/manifest.json`: số lượng, hash và hai cấp độ bằng chứng được ghi tách biệt.

Review gate nguồn gốc trong `app/hus/review.py` không bị đổi. Những nguồn thiếu original vẫn
không đủ điều kiện giả thành `ReviewDecision.include` ở corpus nguồn hoặc `HUSIndex` cũ.
Ngoại lệ được người dùng cho phép chỉ áp dụng trong adapter F1 Markdown; không dùng nó cho
F2, F3, số liệu học vụ hoặc khẳng định bản PDF đã chính xác. Các release cũ được giữ nguyên.

## Tái tạo

```powershell
python -X utf8 -m tools.prepare_hus_f1 verify --markdown-reviews data/hus/qa/20261028/f1_markdown_approved/contract/markdown_review_decisions.json --out data/hus/qa/20261028/f1_markdown_approved/release
python -X utf8 -m tools.prepare_hus_f1 build --markdown-reviews data/hus/qa/20261028/f1_markdown_approved/contract/markdown_review_decisions.json --out backups/rag_preparation/f1-markdown-new01
python -m pytest -q tests/hus/test_f1_markdown_review.py
```

Không dùng các lệnh verify không truyền `--markdown-reviews` cho bản này; chế độ cũ chỉ
tái tạo năm nguồn/42 chunks. Việc đóng gói sang `data/hus/rag/f1` giữ nguyên byte và cập nhật
manifest chung. Chưa tạo vector index hoặc triển khai chatbot.

Nghiệm thu thực chạy: 15 test mới đạt; toàn repository **541 passed, 26 skipped**, Ruff
và diff check đạt. Release chín file tái tạo byte-identical; 19 payload trong thư mục
bàn giao khớp từng byte với nguồn. Các skip cần PostgreSQL/full-source cấu hình riêng;
không dùng kết quả test để khẳng định đã kiểm PDF/DOCX hoặc hiệu lực hiện tại.
