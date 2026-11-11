# F3 tham khảo AI chi tiết cho bốn ngành

**Ngày:** 10/11/2026 · **Nhánh:** `hus-llm-rag` · **Trạng thái:** đã cập nhật theo phản hồi duyệt phạm vi: bỏ bài tập và tiêu chí đánh giá.

Candidate đã hoàn thiện ngày 11/11/2026: [dữ liệu và kiểm chứng](../../../data/hus/qa/20261110/f3_reference_v2/README.md). Runtime vẫn dùng v3.

Builder check độc lập: không còn câu hỏi quan trọng cần bổ sung để lập kế hoạch.

## Mục tiêu và lựa chọn

Người dùng chọn mở rộng nội dung tham khảo AI cho cả bốn ngành, giữ nhãn AI.
Phản hồi ngày 10/11: không cần bài tập và tiêu chí đánh giá. Phần mở rộng chỉ
gồm tổng quan, chủ đề giải thích chi tiết kèm ví dụ minh họa và mục tiêu.
Kiểm kê trực tiếp dữ liệu hiện có: 290 hồ sơ môn–ngành, 174 mã môn, tất cả chỉ
có 3 chủ đề, 2 mục tiêu và 2 hoạt động đánh giá gợi ý. Mục tiêu là tăng chiều
sâu theo từng môn, không tăng độ dài bằng lời dẫn hoặc văn mẫu lặp lại.

Đã đưa ra ba hướng: mở rộng AI, thu thập đề cương HUS đã kiểm chứng, hoặc kết
hợp cả hai. Người dùng chọn hướng AI. Hướng này bao phủ được bốn ngành nhưng
không xác nhận nội dung trường thực tế giảng dạy. Thu thập/review đề cương
chính thức là công việc khác; không tự nâng candidate hiện có thành official.

## Hồ sơ nội dung mới

Giữ đủ 290 membership theo đúng F2 và 174 mã môn. Có thể dùng chung nội dung
khái niệm của cùng mã môn, nhưng giữ riêng ngành/phiên bản/provenance; không
suy ra tương đương học vụ. Nội dung được soạn bằng AI của phiên làm việc,
không cần gọi thêm Gemini API hoặc bật cờ LLM để tạo bộ dữ liệu.

Mỗi hồ sơ gồm:

| Phần | Nội dung đề xuất |
| --- | --- |
| Tổng quan | Một đoạn giải thích học phần nghiên cứu gì, cách tiếp cận và ứng dụng ở mức tham khảo. |
| Chủ đề chi tiết | Khoảng 4–8 đơn vị có ý nghĩa theo môn; mỗi đơn vị có tên, giải thích, các khái niệm/kỹ năng thành phần và một ví dụ minh họa. Không ép mọi môn cùng số chương hoặc cùng mẫu kiến thức. |
| Mục tiêu tham khảo | Khoảng 4–6 việc cụ thể người học có thể giải thích, áp dụng, phân tích hoặc thực hiện; tránh mục tiêu chung lặp giữa các môn. |
| Giới hạn | Nhãn tham khảo AI, trạng thái chưa xác minh đề cương, phạm vi ngành/phiên bản; không tự điền dữ kiện chính thức còn thiếu. |

Số lượng trên là mục tiêu biên soạn, không phải bằng chứng chất lượng hay lý
do chèn mục vô nghĩa. Môn xêmina/chuyên đề chọn lọc phải mô tả phương án học
tham khảo và cách làm, không khẳng định chủ đề mà HUS đã quyết định.

Không tạo lịch từng tuần, số tiết, giảng viên, giáo trình bắt buộc, tín chỉ,
quan hệ tiên quyết mới hoặc chuẩn đầu ra chính thức. Tên/mã/tín chỉ và trạng
thái tiên quyết dùng đúng F2 hiện có; kiến thức nền gợi ý nếu có phải được ghi
là gợi ý học tập, không biến thành điều kiện đăng ký. Nếu dùng nguồn chuyên
môn bên ngoài để kiểm tra khái niệm, giữ URL/vai trò kiểm tra riêng và chỉ dùng
nguồn gốc như tài liệu chính thức, giáo trình hoặc công trình; không coi đó là
bằng chứng đề cương HUS hoặc chép dài nguyên văn.

## Dữ liệu, RAG và phạm vi tích hợp

- Tạo bộ input/output **phiên bản mới**, thí dụ
  `data/hus/qa/20261110/f3_reference_v2/`; không sửa bộ 20261028, release v3,
  run/gold/review/receipt cũ hoặc `CURRENT.json`.
- Schema mới lưu riêng tổng quan, đơn vị chủ đề có ví dụ và mục tiêu có cấu
  trúc. Candidate v2 chỉ export hai field RAG `content`, `objectives`; không
  sinh bài tập, rubric, task hoặc tiêu chí đánh giá. Câu hỏi gợi ý đánh giá
  trên candidate này phải báo không có dữ liệu, không mượn bộ cũ để trả lời.
  Exporter/loader v1 và dữ liệu cũ vẫn nguyên để tái lập lịch sử. Mọi phần
  kiến thức mới đều phải render và index, tránh thêm field JSON không lấy được.
- Chia đoạn theo đơn vị nội dung, giữ tên chủ đề, mã/ngành/phiên bản và cảnh
  báo AI. Không cắt giữa ví dụ và giải thích. Có đoạn tổng quan liệt kê đầy đủ
  chủ đề; chi tiết được lấy theo câu hỏi cụ thể. Câu trả lời tổng quan không
  được tự nhận đã trình bày toàn bộ hồ sơ chi tiết.
- Không gửi toàn bộ hồ sơ dài vào mỗi lượt Gemini. Giữ ngân sách prompt/output
  và guard v2; kiểm tra bundle thực tế, đo fallback. Không nới validator để cho
  phép LLM bỏ ý hoặc tăng ngân sách âm thầm. Nếu dữ liệu dài làm giảm chất
  lượng, chỉnh cách chia/chọn đoạn rồi đo bằng run mới.
- Bàn giao candidate có manifest/checksum, README, ví dụ và kiểm chứng nạp RAG
  trong workspace riêng/fixture. Không thay collection/index vector hiện có.
  Release runtime mới và phép A/B tương ứng là bước tiếp theo sau review dữ
  liệu; v3/lexical và LLM tắt vẫn giữ nguyên trong lần tạo dữ liệu này.

## Kiểm chứng và review

1. Chọn vài môn đại diện để chốt cách biên soạn và chia đoạn, sau đó mở rộng
   đủ bốn ngành. Đối chiếu coverage theo membership F2, không đếm số file
   hoặc số từ thành chất lượng.
2. Kiểm schema, F2 identity/provenance, nhãn AI trên mọi chunk, official fields
   vẫn null, không có weights/tiên quyết bịa. Builder tái lập từ input đã ghim.
3. Review nội dung theo nhóm môn: đúng khái niệm, phù hợp tên môn, cụ thể,
   không lặp máy móc, ví dụ minh họa phù hợp. Ghi rõ review AI hay con người;
   không bịa reviewer hoặc gọi đây là đề cương đã xác minh.
4. Regression cho exporter/chunking và truy vấn nội dung/mục tiêu trên bốn
   ngành; câu hỏi đánh giá không có dữ liệu mới, quy định thi chính thức vẫn
   từ chối xác nhận. Tổng quan giữ đủ tên chủ đề và không trộn scope.
5. So SHA nguồn/bộ dữ liệu cũ trước và sau. Không sửa tiêu chí hoặc gold cũ để
   làm đẹp điểm. Bộ mới dùng câu kiểm mới, ghi exposure; không coi là holdout
   độc lập sau khi đã dùng để biên soạn.

## Phân định công việc

Thiết kế này duyệt việc tạo và kiểm chứng **candidate dữ liệu chi tiết**.
Builder được chọn cấu trúc JSON cụ thể, kích thước đoạn dựa trên đo thực tế,
tên phiên bản chưa tồn tại và thứ tự nhóm môn. Không cần thư viện mới.
Tích hợp runtime/đổi release, rebuild vector/hybrid, A/B live và xét bật LLM
không nằm trong bước tạo candidate này. Báo cáo phải nêu phần còn thiếu hoặc
chưa review; không công bố “đầy đủ đề cương HUS” từ dữ liệu AI.
