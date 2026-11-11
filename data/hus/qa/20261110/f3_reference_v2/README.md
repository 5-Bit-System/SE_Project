# F3 tham khảo AI v2 — nội dung học phần chi tiết

Theo yêu cầu mở rộng cho cả bốn ngành, **không có bài tập hoặc tiêu chí đánh
giá**. Hồ sơ mới tập trung vào tổng quan, chủ đề giải thích chi tiết, khái
niệm thành phần, ví dụ minh họa và mục tiêu tham khảo.

Đây là **candidate riêng, chưa thay dữ liệu chatbot đang chạy**. Nội dung do
AI biên soạn, chưa được xác nhận là đề cương HUS. Dữ kiện danh tính học phần
lấy đúng snapshot `hus-data-20261031-v3`; references dùng kiểm tra khái niệm,
không dùng để khẳng định trường giảng dạy nội dung này.

| Phạm vi | Hồ sơ môn–ngành |
| --- | ---: |
| Toán học | 90 |
| Toán tin | 68 |
| Khoa học máy tính và thông tin | 67 |
| Khoa học dữ liệu | 65 |
| **Tổng** | **290** |

174 hồ sơ theo mã có **703 đơn vị chủ đề và 704 mục tiêu**, xuất thành
**1.753 đoạn RAG** theo môn–ngành. Các số này có tính nội dung dùng chung ở
mã tương ứng, không phải số khái niệm độc lập. Mỗi mã có 4–5 chủ đề được giải
thích và 4–5 mục tiêu; ví dụ nằm cùng chủ đề để không bị tách mất ngữ cảnh.

## File dữ liệu

- `inputs/profiles_a.jsonl`, `profiles_b.jsonl`, `profiles_c.jsonl`: hồ sơ theo
  174 mã môn; các mã cùng tên có thể chia sẻ nội dung khái niệm phù hợp.
- `release/records.jsonl`: hồ sơ riêng theo từng môn–ngành, giữ nguyên dữ
  kiện F2 và phạm vi phiên bản; các trường nội dung chính thức vẫn null.
- `release/rag_documents.jsonl`: toàn bộ nội dung được render, có nhãn AI.
- `release/rag_chunks.jsonl`: đoạn tổng quan, từng chủ đề nguyên vẹn kèm ví
  dụ, và mục tiêu. Chỉ có field `content`, `objectives`.
- `release/profiles.jsonl`, `identity_f2.jsonl`, `coverage.jsonl` và
  `manifest.json`: input đóng gói, provenance, coverage và checksum tái lập.
- [Ví dụ đọc nội dung](SAMPLES.md), [báo cáo kiểm chứng](QUALITY_REPORT.md).

## Kiểm tra và truy vấn riêng

```powershell
python -X utf8 -m tools.prepare_hus_f3_detail verify --out data/hus/qa/20261110/f3_reference_v2/release
# Tạo bản khác; --out phải chưa tồn tại.
python -X utf8 -m tools.prepare_hus_f3_detail build --out backups/f3-detail-new-candidate
python -m pytest tests/hus/test_f3_detail.py -q
```

```python
from pathlib import Path
from app.hus.f3_detail import load_candidate
from app.hus.retrieval import HUSRAGRetriever

data = load_candidate(
    Path("data/hus/qa/20261110/f3_reference_v2/release"), allow_generated=True)
hits = HUSRAGRetriever(data).search(
    "Nội dung Toán rời rạc MAT3500", dataset="f3", major="data_science",
    version="QD3569-2023", course_code="MAT3500", field="content",
    allow_generated=True)
for hit in hits:
    print(hit.chunk.text)
```

Bộ đọc này chỉ dành cho F3 candidate và kiểm tra offline, không phục vụ F1/F2
hoặc ghép ngầm với dữ liệu F3 cũ. Câu hỏi đánh giá không có field tương ứng.
Các truy vấn trên tên chủ đề là kiểm dev đã lộ, không phải nghiệm thu retrieval
độc lập. Số lượng/chất lượng cấu trúc không chứng minh tính chính xác học thuật.

Chưa đổi `CURRENT.json`, rebuild vector/hybrid, gọi Gemini hoặc bật LLM.
Bước tiếp theo là review nội dung và tích hợp qua release mới; khi đó phải
đo lại A/B với code/data/prompt mới, kể cả fallback dưới ngân sách LLM cũ.
