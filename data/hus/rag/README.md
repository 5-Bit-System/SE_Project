# Dữ liệu F1, F2, F3 dùng chung

**Bản chuẩn bị mới nhất — 31/10/2026:** đọc `CURRENT.json` và
`releases/hus-data-20261031-v3/`. Bản này có schema thống nhất: **65 F1 + 336 F2 +
870 F3 = 1.271 chunks**, F2 đồng bộ main 94b7d05 và giữ sign-off KHMTTT. Cả 15 nguồn
F1 có original khả dụng; 24 phần từ 10 nguồn Markdown khớp prose của bản tải mới.
Mã đọc ở `app.hus.release_reader`, kiểm tra ở `tools.prepare_hus_data_release` và
`tools.check_hus_data`. Chi tiết tại [bàn giao](../../../docs/HUS_DATA_HANDOFF_2026_10_31.md).

Chỉ index `chunks.jsonl` trong release mới, hoặc chọn các file family tương đương;
không index cả hai cách hoặc thêm bản lịch sử. F3 vẫn là AI tham khảo có opt-in.
`CURRENT` là pointer tới bộ **đã chuẩn bị**, chưa kích hoạt runtime.

Phần phía dưới mô tả cấu trúc bàn giao trước để giữ khả năng tái tạo. `f2/` đã được
đồng bộ canonical input mới; F1/F3 bên dưới là bản xuất lịch sử, không phải entrypoint
được khuyến nghị cho bước tích hợp mới.

Đây là thư mục bàn giao chung hiện tại để quản lý dữ liệu hỏi đáp. Các đầu ra gốc dưới
`data/hus/qa/20261028/` được giữ nguyên để bảo toàn review, provenance và quy trình tái tạo.

```text
data/hus/rag/
├── f1/
│   ├── rag_chunks.jsonl           # 69 đoạn F1 hiện tại
│   ├── documents.jsonl            # 15 nguồn: 5 đối chiếu raw, 10 duyệt Markdown
│   ├── f1_units.jsonl
│   ├── source_map.jsonl
│   ├── source_inventory.jsonl
│   ├── pending_F1_sections.jsonl   # Hiện rỗng: đã xử lý các tài liệu chờ
│   ├── markdown_review_decisions.json # Hồ sơ duyệt thêm 10 nguồn Markdown
│   ├── acceptance_questions.jsonl
│   └── manifest.json
├── f2/
│   ├── hus_source.json            # F2 đủ 4 ngành: 290 môn–ngành / 297 dòng nguồn
│   └── source_comparison.json     # Đối chiếu nguồn main, commit/blob và số lượng
├── f3/
│   ├── rag_chunks.jsonl           # 870 đoạn AI sinh tham khảo
│   ├── rag_documents.jsonl        # 290 tài liệu văn bản
│   ├── records.jsonl              # 290 hồ sơ cấu trúc
│   ├── source_map.jsonl
│   ├── coverage.jsonl
│   ├── acceptance_questions.jsonl
│   ├── manifest.json
│   └── inputs/blueprints.psv      # Phác thảo nội dung và mục tiêu theo mã môn
├── manifest.json                 # Danh sách bản sao, đường nguồn và SHA-256
└── README.md
```

## Các tệp chính

| Phần | Tệp chính | Trạng thái |
| --- | --- | --- |
| F1: giới thiệu, mục tiêu, nghề nghiệp ngành | [f1/rag_chunks.jsonl](f1/rag_chunks.jsonl) | 69 chunks từ 15 nguồn: 5 nguồn đối chiếu HTML và 10 nguồn duyệt phần F1 trên Markdown theo yêu cầu người dùng; chỉ dùng mô tả, chưa xác minh hiệu lực hiện tại. |
| F2: chương trình, môn, tín chỉ, tiên quyết | [f2/hus_source.json](f2/hus_source.json) | Nguồn cấu trúc đủ bốn ngành từ main đã ghim; giữ `draft_unverified` và các mâu thuẫn/điều kiện chưa xác minh. |
| F3: nội dung, mục tiêu, gợi ý đánh giá học phần | [f3/rag_chunks.jsonl](f3/rag_chunks.jsonl) | AI sinh tham khảo, phải giữ nhãn generated; không phải đề cương chính thức. |

F2 là JSON cấu trúc gồm các bảng trong `tables`, không phải file chunks RAG. F3 cấu trúc
đầy đủ ở [f3/records.jsonl](f3/records.jsonl); các trường `official_*`, tỷ lệ điểm và hình
thức thi chính thức vẫn null. Giữ metadata ngành/phiên bản và nhãn nguồn khi truy xuất.
Hàng đợi F1 hiện rỗng; trang nghề nghiệp trộn Toán Cơ đã bị loại khỏi phần bổ sung.
Không index toàn inventory. Các chunk `include_markdown` phải giữ nhãn chưa đối chiếu PDF/DOCX
gốc; hồ sơ duyệt không tự xác nhận chính xác bản gốc hoặc hiệu lực học vụ.

## Nguồn gốc và cập nhật

Các file dữ liệu được sao chép nguyên byte; `manifest.json` ở thư mục này ghi `origin`,
SHA-256 và kích thước của từng bản sao. Hai manifest riêng F1/F3 được giữ nguyên từ release
gốc. Chỉ dùng một bản dữ liệu khi index để tránh nạp lặp cả bản tại đây và bản trong `qa/`.

Đây là bản đóng gói dữ liệu trong repository, chưa phải archive nguồn độc lập: các trường
F1 `markdown_path`/`raw_path` vẫn tính từ `data/hus`, còn `review.evidence_locator` tính từ
repository root. Những nguồn đó vẫn tồn tại ở vị trí cũ. Blueprint F3 được đặt ở
`f3/inputs/blueprints.psv` để giữ đúng locator của hồ sơ F3.

Khi tái tạo hoặc cập nhật một phần, kiểm lại release gốc rồi đồng bộ bản sao và manifest
chung. Hướng dẫn tái tạo đầy đủ vẫn ở
[F1](../qa/20261028/f1_markdown_approved/README.md) và
[F3](../qa/20261028/f3_reference/README.md).
Các lệnh verify pipeline gốc áp dụng cho thư mục release gốc; thư mục bàn giao F3 ở đây
có thêm inputs nên kiểm các bản sao bằng manifest chung.

Thư mục này chưa được nạp vector index hoặc phát hành thành hệ thống đang chạy.
