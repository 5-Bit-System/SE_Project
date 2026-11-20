# Trả lời tập trung theo nguồn — triển khai offline 15/11/2026

Đã thêm chế độ **`focused`** trên nhánh `hus-llm-rag`, gồm chọn nguồn, gói context
theo ý hỏi và protocol `focused_rewrite_v1`. **Mặc định vẫn legacy/v3**; không
thay các run hoặc điểm cũ. Không gọi Google trong lượt triển khai này.

## Hành vi mới khi chọn focused

- **Chốt nguồn trước tìm kiếm:** dùng inventory đúng ngành/field để kiểm edition,
  hệ, source ID và trạng thái review. Có nhiều scope thì yêu cầu chọn, không tự
  lấy năm mới nhất/top1 hoặc gộp chuẩn–CLC. Unknown vẫn unknown.
- **UI có nút chọn nguồn**, hiện tên/edition/hệ/review thật. Nút gửi lại nguyên
  câu hỏi với source ID được backend kiểm; không bật quyền F3 thay người dùng.
  Đổi ngành vô hiệu response/nút cũ. API cũng nhận `source_id` trong chế độ này.
- **Cả BM25 và vector nhận tập parent thuộc nguồn trước scoring**; Chroma dùng
  bộ lọc parent hiện có, hybrid giữ RRF/candidate budget và kiểm index/snapshot.
  Vector lỗi thì fallback retrieval vẫn giữ tập nguồn đã chọn. Không tạo index mới.
- **Chọn đủ phần mô tả liên quan:** có grammar tổng quan và các nhóm chủ đề được
  kiểm cho đối tượng/kế thừa, câu hỏi nghiên cứu/phạm vi, quá khớp. Không dùng QID,
  target/gold hoặc chunk ID để chọn. Mọi ý phải có mô tả trực tiếp, không lấy
  title/danh sách từ khóa làm đủ định nghĩa. Thiếu ý trong top5 thì không trả một phần.
- **Giữ trọn đoạn và điều kiện:** chọn toàn bộ đoạn giải thích cùng các câu nối
  tiếp. Cấu trúc bất thường, điều kiện trong phần từ khóa hoặc tham chiếu tới
  phần sau sẽ giữ cả chunk. Ví dụ có thể bỏ khi chỉ hỏi định nghĩa và là phần
  minh họa độc lập; hỏi ví dụ/toàn bộ thì không được bỏ inventory tương ứng.
- **Câu quá khớp đời thường chỉ gợi khái niệm liên quan**, giữ “có thể”, nhiễu,
  dữ liệu huấn luyện/mới và cảnh báo không kết luận nguyên nhân duy nhất. Câu
  phủ định/“luôn luôn”/nguyên nhân khác không được nhập chung thành alias này.

Những cách hỏi khác vẫn dùng guard nghiêm hiện có, chưa phải bộ hiểu ngữ nghĩa
tổng quát. F2 vẫn giữ facts/backend và protocol `kind=facts`; không thay prompt
F2 hoặc xử lý hai ca IF2 còn mở trong lượt này.

## Context và kiểm output

Backend tạo plan JSON bất biến trước model: câu gốc, release/scope/source ID,
aspects và mọi unit bắt buộc. Mỗi unit có citation ID, offset **tương đối trong
quote canonical**, hash quote và nguyên đoạn được chọn. Context truyền adapter
giữ citation/quote/locator/hash/review gốc; `hus_answer` không bị model viết lại.
Plan nội bộ không hiển thị trong response API thông thường.

Wire chỉ gửi câu hỏi, scope/release và bằng chứng cần dùng; không gửi path,
history, tài khoản/bảng điểm/key. Nguồn/câu hỏi là dữ liệu không đáng tin về chỉ
dẫn, model không có tool/action. Prompt hash bao phủ đúng hai message.

Output phải đủ mỗi `unit_id` đúng một lần, không thêm key/ID/URL/HTML. Backend
kiểm chuỗi từ/toán tử, **literal số và dấu thập phân**, mã, phủ định/điều kiện;
chặn thêm/chuyển “không”, “nếu”, “luôn luôn” ngay cả khi đủ các từ cũ. Backend
khôi phục thứ tự/bullet/citation sau khi toàn output đạt. Không hiện output dở dang.

Đây là protocol bảo toàn từ/toán tử, chỉ cho thay case/khoảng trắng/dấu câu trung
tính; **chưa có paraphrase tự do**. Tính đầy đủ của plan vẫn cần người đọc nguồn
review; schema/ID/hash đúng không tự chứng minh entailment.

Giữ1.024 output token/call,12.000 prompt chars,8.192 raw output chars và giới hạn
đồng thời hiện có; không bỏ unit để vừa cap. Auto chỉ trả offline sau429; lỗi
401/403/503/output/ngân sách khác báo lỗi. F3 vẫn opt-in và nhãn “kiến thức AI”.

## Kiểm chứng thực tế

- TDD ban đầu14 ca chọn context và17 ca protocol RED trước triển khai. Sau đó
  thêm các regression source format, giả mạo canonical, context sau từ khóa và
  số thập phân; các lỗi mới đều được tái hiện trước sửa.
- Nhóm liên quan rộng **1.072 passed**, một warning Starlette cũ. Lượt tập trung
  sau sửa cuối **49 passed**; có giao nhau, không cộng thành số test khác nhau.
  Ruff17 file đạt. Browser thật kiểm nguồn bằng bàn phím ở viewport460px, giữ
  quyền và xóa nút khi đổi ngành; launcher/service có kiểm lựa chọn explicit.
- `--answer-policy focused --check` trên `.venv` tối thiểu đạt20 ca API/2.124 menu/
  4 hash nguồn, LLM tắt. Giới thiệu KHMTTT yêu cầu chọn nguồn theo đúng policy,
  không ép answered để làm xanh check.
- Reviewer AI riêng phát hiện hai vấn đề quan trọng: dấu thập phân và context
  sau phần từ khóa. Đã thêm regression/sửa; review cuối không còn phát hiện
  quan trọng trong các sửa này. Đây là review code tĩnh, không là nghiệm thu người thật.
- **Native hybrid v4 chạy5 search thật**, đúng index ID, không fallback retrieval,
  tập parent trong Chroma/RRF nằm trong nguồn đã chọn. Cache E5 local, không tải
  model hoặc gọi Google. Không dùng thời gian lượt smoke làm benchmark latency.

Lượt dev mới giữ nguyên câu hỏi đã exposed; không chấm lại bộ20:

| Ca dev | Focused trên hybrid thật |
| --- | --- |
|006 — tổng quan Toán tin |Answered từ nguồn introduction duy nhất, edition/hệ unknown;1 unit. |
|009 — đối tượng và kế thừa |Answered,2 ý/2 đoạn trực tiếp; không kèm hợp thành hoặc tổng quan ngoài ý hỏi. |
|012 — học tiếp KHMTTT, chưa ghim nguồn |Cần làm rõ, không search/generation. Có5 lựa chọn nguồn. |
|014 — câu hỏi nghiên cứu/phạm vi |Answered,2 ý cùng1 đoạn mô tả đầy đủ; giữ câu về định nghĩa/dấu hiệu quan sát. |
|019 — học thuộc/dự đoán kém |Answered bằng1 đoạn khái niệm liên quan, có cảnh báo giới hạn, không khẳng định mọi dự đoán kém là quá khớp. |

Một **request riêng** chọn rõ DOCX2023/hệ chuẩn cho012 cũng trả lời từ đúng nguồn;
không sửa request/điểm của ca chưa chọn. Plan, wire và output copy tổng hợp được
validator kiểm offline; đó là dữ liệu giả lập, **không phải bản sinh Gemini thật
hoặc gain LLM**.84 file lịch sử/data/index/CURRENT được bảo vệ giữ hash.

## Chạy và việc còn lại

[Quickstart/lệnh chạy](HUS_RAG_QUICKSTART.md#thử-câu-trả-lời-tập-trung-và-chọn-nguồn).
Thêm `--answer-policy focused` vào launcher muốn thử; restart server đang chạy.
Bỏ cờ hoặc dùng `--answer-policy legacy` để quay lại protocol cũ. Không sửa key,
release hoặc index; agent chưa restart server đang dùng.

Nhóm đọc [run/plan/quote/trace](../data/hus/evaluation/runs/focused_answer_offline_20261115_r2/observations.json)
và điền [CSV6 tình huống](../data/hus/review/focused_answer_offline_20261115_r2/review_group_return.csv).
Các mục người thật còn pending. Kiểm Gemini tiếp phải prepare/pin revision mới
và thống nhất budget, tính cả call hiểu ý định nếu có. Không dùng1 call IF2 cũ.

Manifest run mới:
`de6c82c2beb208a2cf9e8c12686955ea7ab24843ce8fc4f80d203eb2a423ea0a`.
[Protocol/pins](../data/hus/evaluation/runs/focused_answer_offline_20261115_r2/protocol.json).
Revision r1 diagnostic đã dừng trước native do helper dùng version UI F2 thay
effective version F1; validator từ chối đúng scope. Giữ receipt lỗi riêng, không
ghi đè; r2 sửa helper và là lượt hoàn tất. Không sửa source/validator để né lỗi.

[Kế hoạch triển khai](superpowers/plans/2026-11-15-hus-focused-answer.md) ·
[Tiến độ và việc tiếp theo](RAG_PROGRESS_AND_NEXT_PLAN.md)
