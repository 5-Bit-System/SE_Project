# Kiểm lại lexical và hybrid cho demo — 19/11/2026

**Hai chế độ cùng trả lời được 13/20 câu.** Hybrid chạy đúng index v4 và
chưa cho thấy lợi ích retrieval rõ ràng trong bộ này. Trên máy đo, median
thời gian RAG của các câu có search là **0,0035 giây với lexical và 1,522 giây
với hybrid**.

## Thiết lập

- Cùng 20 câu dev đã lưu, code hiện tại, snapshot `hus-data-20261111-v4` và
  chính sách `legacy`. Hai lần đo mỗi câu cho mỗi chế độ, đảo thứ tự chạy
  trong lần thứ hai. Bật cache E5 local và chặn đường gọi mạng/model.
- Cả hai chế độ chạy trên cùng máy Windows và cùng process. Hybrid dùng
  BM25, E5 và ChromaDB, gộp bằng RRF. Cả 20 lần search hybrid thuộc 10 câu
  đều có ứng viên từ hai nhánh, chạy đúng index
  `1188901040ec83539b3c0ffe72991bd6feb8cf2737610d9ece922ebaa60d43c6`
  và có 0 fallback retrieval. LLM tắt, 0 lời gọi Google.
- Cùng câu và scope retrieval ở từng cặp. Hai lần chạy của mỗi chế độ cho
  cùng đáp án và trace. Các đoạn tham chiếu dev chỉ dùng khi đọc kết quả.
  SHA256 của 52 file lịch sử giữ nguyên.

## Độ trễ

Đơn vị giây. Mỗi dòng có 20 quan sát cho mỗi chế độ từ 10 câu, hai lần đo mỗi câu.

| Phần đo | Lexical min / median / max | Hybrid min / median / max |
| --- | ---: | ---: |
| Toàn bộ lượt RAG có search | 0,0019 / **0,0035** / 0,0196 | 1,345 / **1,522** / 1,766 |
| Riêng retrieval | 0,00018 / 0,00089 / 0,00145 | 1,343 / 1,519 / 1,752 |
| Toàn bộ lượt RAG không search | 0,00069 / 0,01038 / 0,13367 | 0,00078 / 0,00974 / 0,03471 |

Khởi tạo và warmup hybrid mất **103,563 giây** trong lượt này, được đo riêng.
Mốc **6,591 → 3,327 giây** của lần tối ưu trước thuộc một phép đo khác. Bảng
trên dùng để so lexical với hybrid ở cấu hình hiện tại. Các số đo là RAG local.
[Lượt tối ưu trước](RAG_HYBRID_LATENCY_2026_11_15.md).

## Khác biệt về kết quả

Mỗi chế độ có **13 answered, 4 no-information và 3 cần làm rõ**. Có 18/20
response giống nhau. Trong 10 câu có search, 9 câu có cùng tập top 5, trong đó
5 câu đổi thứ tự. Chưa có ca nào thêm được đoạn tham chiếu dev vào top 5 hoặc
có thêm đáp án. Một đoạn tham chiếu xuống hạng.

| Ca | Quan sát |
| --- | --- |
| HN20-004 · Khái niệm trong Đại số tuyến tính 1 | Cùng hồ sơ AI MAT2300 và cùng phiên bản. Hybrid lấy đoạn tổng quan vào top 5 và bỏ đoạn giải thích riêng về hạt nhân, ảnh và hạng. Ba chủ đề này vẫn có tên trong tổng quan. Lexical giải thích chi tiết hơn về chúng. |
| HN20-012 · Hướng học tiếp sau KHMTTT | Câu chưa chọn edition. Lexical dùng DOCX hệ chuẩn 2023, có cả bậc học và lĩnh vực. Hybrid dùng PDF 2015, nêu bậc Thạc sĩ/Tiến sĩ. Hai câu đều có nguồn, nhưng khác mức chi tiết. |
| HN20-009 · Đối tượng và kế thừa của MAT1202 | Đoạn tham chiếu từ hạng 1 xuống hạng 2 trong hybrid. Đáp án và nguồn hiển thị giống nhau. |
| HN20-019 · Mô hình học thuộc dữ liệu | Cả hai tìm thấy đoạn tham chiếu ở hạng 3. Guard vẫn trả thiếu thông tin trong chính sách `legacy`. |

Với bộ này, **giữ lexical mặc định cho demo hỏi đáp** để giảm độ trễ. Hybrid
vẫn là lựa chọn khi cần minh họa tìm kiếm vector. Khi demo câu có nhiều phiên
bản nguồn, chế độ `focused` hỗ trợ chọn nguồn trước khi trả lời. Lượt này đo
`legacy` và dùng bộ dev đã xem trước, còn phần review của nhóm.

[CSV 20 câu và độ trễ từng ca](../data/hus/review/hybrid_demo_paired_20261119_r1/comparison.csv) ·
[Đáp án và trace](../data/hus/evaluation/runs/hybrid_demo_paired_20261119_r1/observations.json) ·
[Phạm vi và pin](../data/hus/evaluation/runs/hybrid_demo_paired_20261119_r1/protocol.json) ·
[Manifest](../data/hus/evaluation/runs/hybrid_demo_paired_20261119_r1/manifest.json).
