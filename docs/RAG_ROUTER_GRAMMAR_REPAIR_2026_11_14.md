# Sửa cú pháp và định tuyến câu tự nhiên — 14/11/2026

Đã sửa trên nhánh `hus-llm-rag`, kiểm offline với v4/lexical. Đây là sửa chung
theo lỗi dev đã biết; **không đo lại hoặc thay điểm của run20 câu đã seal**.
Không gọi Google, không đổi dữ liệu/index/prompt/validator đầu ra LLM.

## Các thay đổi

- Nhận diện đúng trợ từ có dấu **“thì” trước khi bỏ dấu** khi phân tích câu hỏi;
  chuẩn hóa cả Unicode tách dấu. Giữ câu hỏi gốc và các mệnh đề điều kiện/phủ
  định. Không xóa `thi` không dấu hoặc từ “thi” thật; câu thi cuối kỳ/tỷ lệ vẫn
  là yêu cầu đánh giá chính thức chưa có bằng chứng phù hợp.
- Nhận cách hỏi “làm việc ở đâu”, “phải/cần hoàn thành môn nào trước”, “trước khi
  học ... phải học môn nào”, “gặp/học các khái niệm gì” và yêu cầu giải thích
  khái niệm. Dùng cùng nhận diện cho route và kiểm nhiều field.
- Phân biệt “môn X” với “chuyên môn”, “bộ môn”, “liên môn”. Những từ trong tên
  hoặc yêu cầu thực chất vẫn giữ để đối chiếu nguồn; không đưa vào stopwords.
- Câu định hướng chung hoặc “ngành học những môn/lĩnh vực gì” chưa xác định rõ
  cần mục tiêu, nghề nghiệp hay danh mục môn sẽ được hỏi lại. Không mặc định
  câu001 là objectives hoặc câu017 là nội dung một học phần theo bảng kỳ vọng.
- Chỉ coi trọn cụm “nếu tính mỗi mã học phần một lần” là quy tắc đếm danh mục.
  Phần lọc bắt buộc/tự chọn, phủ định hoặc điều kiện khác vẫn bị giữ để làm rõ.
- Guard chỉ trung hòa cách hỏi khái niệm khi thực sự có bằng chứng **F3/content**;
  chủ đề riêng vẫn phải có trong nguồn. Điều kiện thực chất cần bằng chứng cùng
  scope, gồm cả phủ định; “nếu muốn học tiếp” chỉ được coi là câu mở đầu khi
  toàn bộ cụm là nguyện vọng đơn thuần, không có đuôi điều kiện bị bỏ qua.

## Kiểm lại riêng sáu ca đã phơi lộ

Dùng nguyên request từ pack cũ với code mới, lưu diagnostic riêng dưới
`.cache/hus/router_grammar_20261114/postfix_diagnostic.json`. **Không là điểm chất
lượng mới**, không so sánh latency hoặc khẳng định entailment/nghiệm thu người thật.

| Ca dev | Trạng thái sau sửa | Ý nghĩa |
| --- | --- | --- |
| HN20-001 | `needs_clarification`, F1 | Hỏi rõ mục tiêu/giới thiệu, nghề nghiệp hay danh mục môn; không ép sang field gold. |
| HN20-002 | `answered`, F1/careers | Lấy nguồn nghề nghiệp của Toán học, không yêu cầu mã môn/F3. |
| HN20-004 | `answered`, F3/content | Nhận tên Đại số tuyến tính1/MAT2300; cần quyền F3 và giữ nhãn “kiến thức AI”. |
| HN20-005 | `answered`, F2/program_course_count |90 mã duy nhất của danh mục Toán học/QD3565-2023; số môn mỗi sinh viên phải học vẫn `null`. |
| HN20-008 | `answered`, F2/prerequisites |MAT1202/Toán tin/QD3567-2023 lấy dòng tiên quyết MAT2505 từ nguồn; giữ `draft_unverified`, không kết luận đủ điều kiện đăng ký. Không cần quyền F3. |
| HN20-017 | `needs_clarification`, F1 | Hỏi rõ câu cấp ngành trước khi chọn loại tra cứu; không yêu cầu mã cho toàn ngành. |

Các ca tương tự và negative có trong
[test_conditional_question_language.py](../tests/hus/test_conditional_question_language.py).
Bao gồm thi thật/câu không dấu, official assessment, điều kiện phủ định cả hai
chiều, đuôi điều kiện sau “muốn học tiếp”, nguồn sai chủ đề, lọc đếm và API thật
trong process với LLM tắt.

## Kiểm chứng và giới hạn

- Bộ regression mới53 ca đạt; reviewer độc lập cũng chạy53 ca đạt, không còn
  vấn đề quan trọng trong phạm vi này. Nhóm539 ca liên quan đạt trước các sửa
  theo review; lượt rộng cuối **636 ca đạt/207,05s**, gồm các regression mới và
  kiểm program/intent/auto. Hai nhóm có giao nhau, không cộng số test.
- Ruff5 file đạt. `tools.run_hus_llm --check` trên venv tối thiểu đạt20API,
  2.124 mục menu và4 hash nguồn; LLMoff/Google0. Có warning Starlette cũ.
- So hash30 file của pack/run/review20 câu trước–sau: giữ nguyên. Không sửa
  gold/observations/review/CSV hoặc biến diagnostic này thành điểm mới.
- Chưa kiểm live Gemini hay đo lại hybrid/latency. Lỗi guard006/019, chọn edition
  012 và câu trả dư009/014 vẫn cần review riêng. Chưa giải quyết mọi cách hỏi,
  nhiều field, mọi điều kiện hoặc tham chiếu “môn đó” giữa các lượt.
- Chỉ làm local; không stage/commit/push/PR/Actions/deploy, không đọc key hoặc
  file môi trường. Các budget Google trước vẫn đã hết.

[Kế hoạch tiến độ](RAG_PROGRESS_AND_NEXT_PLAN.md) ·
[Run20 câu lịch sử](RAG_HYBRID_NATURAL20_2026_11_14.md)
