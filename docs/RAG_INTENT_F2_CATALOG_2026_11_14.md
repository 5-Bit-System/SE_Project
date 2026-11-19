# Hiểu câu hỏi tự do và tra danh mục F2 — 14/11/2026

Đã thêm phép đếm/liệt kê danh mục và bộ nhận diện ý định dùng Gemini khi luật
chưa nhận ra loại câu hỏi. Triển khai và kiểm bằng provider giả lập; **chưa gọi
Google thật cho tính năng mới**. Không thay dữ liệu v4 hoặc kết quả đo trước đó.

## Luồng xử lý

1. Giữ luật cho câu rõ ràng/menu; kiểm ngành, phiên bản, hệ và yêu cầu ngoài phạm vi.
2. Trong launcher Gemini, nếu luật trả `routing_unknown`, gửi câu hỏi, ngành/phiên
   bản đang chọn, danh mục mã/tên môn công khai và danh sách thao tác được hỗ trợ
   cho model nhận diện ý định. Không gửi lịch sử, tài khoản hoặc bảng điểm.
3. Model chỉ trả JSON `kind/dataset/field/major/course_code`. Backend kiểm khóa,
   kiểu, enum và định danh môn; không nhận câu hỏi viết lại, SQL, URL hay giá trị
   dữ kiện. Giữ câu gốc, phiên bản, mã môn đã gửi và quyền F3.
4. Backend lấy bằng chứng hoặc tính từ F2. Sau đó adapter hiện có mới diễn đạt;
   F2 vẫn chỉ cho model chọn cách trình bày, mọi dữ kiện/danh sách do backend tạo.

Một câu có thể cần **hai call**: hiểu ý định và diễn đạt. Câu đã rõ chỉ dùng
call diễn đạt; chào hỏi và các lỗi phạm vi rõ ràng không gọi bước hiểu ý định.
Giữ cap1.024 output token/call, không retry/đổi model. Trần prompt hiểu ý định
16.000 ký tự, output JSON2.048 ký tự; quá trần báo lỗi an toàn.

`interpretation` và `generation` là hai metadata riêng trong API, có model trả
về/prompt hash/usage khi có. `interpretation.used=true` không có nghĩa đã sinh
và dùng câu trả lời cuối. Không lưu raw output bị từ chối hoặc key.

## Đếm và liệt kê

- `program_course_count`: đếm mã môn duy nhất trong F2 đúng ngành/phiên bản.
- `program_course_list`: trả toàn bộ mã/tên môn theo cùng phạm vi, sắp theo mã.
- `catalog_course_count` khác `student_required_course_count`; trường thứ hai
  giữ `null`. Danh mục có tự chọn nên không phải số môn mọi sinh viên phải học.
- Citation giữ nguồn/review/release và các pointer dòng nguồn, cùng metadata
  phép tính `count_unique_course_code`; không giả câu kết luận tính toán là
  nguyên văn trong PDF. Không đếm mục menu hoặc dựa vào số model đưa ra.
- Chưa hỗ trợ lọc bắt buộc/tự chọn/nhóm/học kỳ/chủ đề hoặc tính số môn cần tốt
  nghiệp; hỏi lại rõ ràng thay vì dùng tổng danh mục cho các yêu cầu đó.

Ví dụ nhập tự do:

| Câu hỏi | Cách xử lý |
| --- | --- |
| Ngành khoa học máy tính có bao nhiêu môn học? | Nếu đang chọn KHDL, yêu cầu chọn KHMTTT; sau khi chọn đúng thì tính từ F2 KHMTTT của phiên bản đang chọn. |
| Ngành Toán học có bao nhiêu môn học? | Với QD3565-2023, đếm90 mã duy nhất; ghi rõ đây là danh mục, không là số môn phải học. |
| Liệt kê các môn trong chương trình | Trả mã/tên đầy đủ từ F2 đã chọn; không cần nút menu. |
| Đếm học phần giúp tôi | Luật chưa đủ; JSON ý định được kiểm rồi mới đếm đúng phạm vi. |
| MAT2300 được tính mấy TC? | Model có thể chọn `f2/credits/MAT2300`; backend lấy4 tín chỉ từ nguồn. Luồng này đã kiểm mock, chưa xác nhận Gemini thật. |
| Có bao nhiêu môn bắt buộc? | Làm rõ; không lấy tổng danh mục để trả lời. |

## Giới hạn giữ lại

Không âm thầm đổi ngành. Môn phải có mã trong câu hoặc tên đầy đủ khớp duy nhất
trong danh mục; hint mã môn đã gửi phải nhất quán. Chưa đoán từ “môn đó” hoặc mô tả mơ hồ. Câu có
điều kiện/phủ định/chuyển đổi đơn vị mà F2 chưa hỗ trợ cần làm rõ, dù JSON hợp lệ.
Không quy đổi “đơn vị học trình” thành tín chỉ.

Fallback ý định chỉ áp dụng khi luật chưa hiểu; chưa xử lý mọi trường hợp luật
chọn nhầm field, guard từ chối bằng chứng, thiếu nguồn, edition hoặc câu nhiều ý.
Các điểm này vẫn cần bước sửa riêng, không coi có bộ hiểu ý định là đã giải quyết
mọi câu ngoài menu.

HTTP429 ở **bất kỳ bước gọi model nào** khóa gọi tiếp đến khi restart; dùng
đường RAG offline hiện có. Câu chưa hiểu offline có thể vẫn cần làm rõ. Các lỗi
khác/JSON bị chặn báo lỗi an toàn (API502), không trả offline thay thế. Startup
không gọi provider. Launcher offline và API opt-in cũ giữ hành vi cũ; Gemini
launcher tự bật `HUS_LLM_INTENT_ENABLED=true` trong process.

## Kiểm chứng

Các ca mới kiểm bốn ngành, đếm/liệt kê, source pointers, giới hạn scope/filter,
schema JSON, mã môn/hệ mâu thuẫn, qualifier, prompt, hai call HTTP giả lập,
403/429/503, quota đồng thời và thông báo trên browser. Số kiểm cuối được ghi
trong [kế hoạch tiến độ](RAG_PROGRESS_AND_NEXT_PLAN.md): nhóm liên quan177 đạt;
lượt cuối140 ca mới/browser/scope đạt (có giao nhau, không cộng thành317).
Ruff13 file đạt; `--check` môi trường tối thiểu đạt20API/2.124menu/4hash nguồn.
Chỉ có warning Starlette cũ. Reviewer đã xác nhận ba lỗi phát hiện được sửa;
regression cuối cũng kiểm tên môn có “ứng dụng” không bị hiểu nhầm thành phủ định.

Giữ nguyên các run/gold/review/CSV cũ, chỉ kiểm local. Không stage/commit/push/PR,
Actions hoặc deploy. Kiểm Gemini thật tiếp theo cần thống nhất budget mới,
tính cả call nhận diện ý định.
