# Sửa ngôn ngữ sau A7 — ba ca diagnostic đã trả lời có nguồn

Ngày **12/11/2026**, nhánh `hus-llm-rag`, HEAD nền `f61b0fd` + WIP. Sửa baseline
theo yêu cầu, không chạy phép A7 mới. Giữ v4/lexical/LLM tắt; không gọi Google,
đổi dữ liệu/retrieval ranking hoặc đọc key/file cấu hình riêng.

## Nguyên nhân và cách sửa chung

| Diagnostic đã lộ | Nguyên nhân | Thay đổi |
| --- | --- | --- |
| A7P-Q013 | “Đào tạo thí điểm” bị hiểu là thi/điểm, route F3 và không search | Chỉ bỏ nghĩa assessment của “thí điểm” trong cụm đào tạo/chương trình/triển khai/đề án; câu thi/điểm thật ở cùng câu vẫn được giữ. |
| A7P-Q020 | Guard giữ từ yêu cầu “tìm hiểu”; token `tim` không có trong đoạn đã lấy | Nhận “tìm hiểu” ở vị trí mệnh lệnh đầu clause; không bỏ từ này khi là năng lực học tập cần bằng chứng. |
| A7P-Q027 | Guard đòi đúng chữ “dựa trên”, trong khi nguồn nói “là tiền đề” | Câu học tiếp vẫn phải có mọi chủ đề được hỏi; chỉ nhận cách diễn đạt căn cứ khi nguồn cùng scope có quan hệ nền tảng/tiền đề khẳng định. Đoạn nêu quan hệ phải được hiển thị, không mượn từ nguồn/phiên bản khác. |

Ca âm tính phát hiện thêm rủi ro: “định lượng” và “thứ tự” có thể cung cấp hai
token của “lượng tử” dù không có chủ đề đó. Các cụm khoa học dễ nhập nhằng đã
được nhận diện trong routing nay phải xuất hiện **liền nhau trong một body**;
không ghép từ qua nhiều đoạn hoặc dùng title/metadata thay bằng chứng chủ đề.

Chỉ sửa `app/hus/question_routing.py` và `app/hus/answer_support.py`; thêm
`tests/hus/test_followup_language.py`. Không có QID/gold/run hoặc import evaluator
trong runtime. Không nới filter ngành/phiên bản/hệ/review, quyền F3, facts F2,
nguồn/citation, prompt/model hoặc ngân sách LLM.

## Kiểm chứng dev, không đổi điểm A7 cũ

- **39 regression mới**: câu có/không dấu, pilot và thi thật, mệnh lệnh/năng lực,
  căn cứ khẳng định/phủ định, thiếu chủ đề, sai scope/edition/thời lượng, ghép
  token, AI opt-out và assessment không có nguồn. Ban đầu18 fail/17 pass;
  bốn ca ghép cụm bổ sung cũng đỏ trước khi siết guard. Cả39 đã xanh sau sửa.
- Diagnostic mới chạy48 raw request đã lộ: **36/36 positive answered**,
  source audit **48/48**; chỉ response Q013/Q020/Q027 đổi. **12 F2 và12 control
  exact như cũ**, retrieval calls của47 ca còn lại nguyên vẹn; Q013 nay có search.
- Root AI đọc exact ba response mới, đối chiếu quote/target; đoạn cần thiết có
  trong câu trả lời, F3 giữ `generated/needs_review`/nhãn kiến thức AI, F1 giữ
  scope/hiệu lực unknown. Đây là review AI dev, không xác minh học vụ hoặc
  nghiệm thu độc lập; trả lời có thêm ngữ cảnh nguồn, chưa đo mức tập trung/dễ đọc.
- **593 test routing/RAG/API đạt**, gồm39 regression mới; **489 test LLM đạt**.
  Mỗi lượt có một cảnh báo Starlette/httpx đã có. Ruff đạt; không chạy lại full
  repo/browser hoặc cộng các mốc kiểm giao nhau thành tổng nghiệm thu.
- Kết quả A7 đã seal **23/24 Recall,33/36 đủ ý** và review/run/gold cũ giữ nguyên.
  Bộ `a7_postfix_20261112_r1` nay **đã dùng tuning, giữ làm dev**. Con số36/36
  answered ở đây không thay điểm đủ ý/Recall A7 hoặc làm thành holdout mới.

[Receipt diagnostic](../data/hus/qa/20261112/a7_followup_language_dev_r1/report.json)
lưu response/audit/pins và kiểm bảo toàn. Log, diagnostic trước sửa và chi tiết
test ở `backups/hus_a7_language_followup_20261112/`. Receipt chốt số kiểm rộng
và hash trên code cuối; không cộng các nhóm test giao nhau thành full-suite claim.

## Việc tiếp theo và artifact đã cũ

1. Freeze **bộ A7 mới tối thiểu48 câu/12 mỗi ngành** từ nguồn trước inference,
   ghim baseline cuối và exposure/reviewer. Không dùng lại bộ vừa tuning như
   đánh giá độc lập; giữ mục tiêu Routed Recall@5 ≥90% cùng facts/citation/đủ ý/controls.
2. L5 v3 prepared `llm_v3_v4_prepared_20261112_r1` không còn khớp pins runtime.
   Giữ receipt cũ, prepare/preflight lại trước phép A/B; không đổi retrieval/
   snapshot giữa A và B. Google vẫn cần ngân sách mới,24 calls cũ đã hết.
3. Gói nộp r2/checker chuyển máy ghim baseline **trước lần sửa này**, vẫn là
   snapshot cũ có kiểm local; không ghi đè ZIP/receipt hoặc gọi đó là gói code
   mới. Nếu chọn baseline mới cho máy nộp, tạo gói mới/hash/checker phù hợp và
   kiểm cài/browser/nguồn/rollback trên chính máy nộp Windows64-bit/Python3.11.

Chưa bật L6, tạo điểm A7 mới, commit/push hoặc deploy.
