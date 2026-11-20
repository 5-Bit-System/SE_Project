# Review nội dung lượt live ý định/F2 — 15/11/2026

Đã đối chiếu lại **12 kết quả đã lưu**, không chạy inference hoặc gọi Google.
Sáu đáp án được dùng khớp dữ kiện/nguồn, hai câu vẫn chưa có đáp án; bốn control
giữ phản hồi đúng biên trong phạm vi bộ này. Nhận xét là **bản nháp Codex(AI)**,
chưa thay xác nhận của nhóm và không tạo điểm đánh giá mới.

Giữ nguyên lượt live: **11 call = 4 hiểu ý định + 7 diễn đạt; 6 used, 0 fallback**.
Một call chưa dùng của budget12 đã đóng, không dùng lại để retry.

## IF2-002: đã hiểu, bị chặn khi diễn đạt

“Cho mình xem toàn bộ danh sách học phần”, Toán học/QD3565-2023:

- Một call hiểu ý định đã qua kiểm, sau đó có một call generation; cả hai HTTP200.
- API báo `output_rejected`; diagnostic generation là `output_coverage/fact_keys`.
  Không có đáp án bị chặn được hiển thị và không thay bằng offline.
- Bundle generation đã chuẩn bị yêu cầu đúng bốn khóa **ở cấp ngoài của facts**:
  `field`, `program_id`, `review_status`, `value`; citation ID `1`.
  `courses`, `catalog_course_count`, `student_required_course_count` nằm trong
  `value`, không phải bốn khóa ngoài này. Danh sách backend có90 mã.
- Prompt đã yêu cầu copy mọi khóa facts đúng một lần; validator vẫn kiểm tập
  khóa bằng phép so sánh tập chính xác. Đây không phải lỗi `kind` đã sửa trước đó.

**Chưa biết model đã trả khóa nào.** Không có raw output để xác định khóa cụ thể
thiếu/thừa/trùng, việc nhầm cấp lồng hay nguyên nhân model chọn sai. Không dùng
độ dài176 ký tự hoặc71 output token để dựng lại JSON, không kết luận model đếm
sai90 môn.90 chỉ là dữ liệu backend có thể cung cấp, không là đáp án live của002.

Nếu chọn sửa: có thể làm prompt rõ hơn bằng danh sách khóa ngoài/ID cần copy
được backend dựng trực tiếp, kèm ví dụ F2 count/list. Cần regression cho valid,
khóa thiếu/thừa/trùng và khóa lồng; giữ nguyên schema/validator. Đây là đề xuất
giảm lỗi tuân thủ, **chưa chứng minh chữa được call cũ hoặc live tương lai**.

## IF2-004: làm rõ chưa phải kết quả đếm

“Đếm học phần giúp tôi”, Toán tin/QD3567-2023:

- Có **một call hiểu ý định**, HTTP200; không gọi generation.
- Response là `needs_clarification/clarification_required`, facts/citation rỗng.
  `interpretation.used=true` chỉ nói kết quả hiểu đã được xử lý; chưa trả được số.
- Nguồn có68 mã trong danh mục Toán tin; preflight giả lập đã tra được số này.
  Đó là khả năng tra F2, **không phải model đã trả68 trong lượt live**.
- Không lưu JSON hiểu ý định để biết lý do model yêu cầu làm rõ. Không khẳng
  định model thiếu ngành/mã môn hoặc prompt gây lỗi chỉ từ response chung.

Lời nhắc hiện tại hỏi chung “thông tin ngành, dữ kiện chương trình hay nội dung
môn nào”, chưa tập trung vào việc đếm toàn danh mục hay đếm theo điều kiện.
Nếu chọn cải thiện: nhận câu mệnh lệnh đếm đơn giản trong scope ngành/phiên bản
đã chọn, hoặc bổ sung ví dụ vào prompt ý định. Giữ riêng “phải học”, bắt buộc,
tự chọn, phủ định và điều kiện; không mặc định mọi câu chứa “đếm” thành tổng danh
mục. Cần regression tương tự/negative và kết quả mới, không sửa kỳ vọng cũ.

## Review cả12 câu

| Ca | Nhận xét từ đáp án và nguồn |
| --- | --- |
|001 |Đúng90 mã duy nhất Toán học; giữ cảnh báo danh mục khác số môn mỗi sinh viên phải học, trạng thái draft_unverified. |
|002 |Lỗi đầu ra generation như trên; chưa có đáp án để nghiệm thu nội dung. |
|003 |Đủ68 mã/tên Toán tin; mọi dòng mã/tên trong nguồn đều có trong reply. Không đổi danh mục thành danh sách môn bắt buộc. |
|004 |Làm rõ như trên, không tính là đếm thành công. |
|005 |Đúng67 mã KHMTTT; đúng scope/QD3568-2023. verified là review cấp dự án, không xác nhận hiệu lực hiện tại cho cá nhân. |
|006 |MAT1204/KHMTTT giữ3 tín chỉ theo PDF trang10; giữ cảnh báo sign-off dự án không là chứng nhận của trường. |
|007 |Đủ65 mã/tên KHDL; mọi dòng có trong reply, giữ draft_unverified và cảnh báo số danh mục. |
|008 |MAT3533/KHDL giữ3 tín chỉ theo PDF trang11; giữ cảnh báo unresolved MAT2406, không tự sửa tiên quyết. |
|009 |Chọn KHDL nhưng hỏi KHMTTT: yêu cầu chọn đúng ngành, không gọi provider. |
|010 |Hỏi số môn phải học: làm rõ phép đếm/điều kiện, không lấy90 môn danh mục thay đáp án. Không gọi provider. |
|011 |Chưa cho phép F3: nhắc quyền AI, không trả nội dung AI hoặc gọi provider. |
|012 |MAT9999 không có trong dữ liệu scope đã chọn: từ chối thiếu nguồn, không bịa tín chỉ hoặc gọi provider. |

Kiểm kỹ thuật bổ sung: sáu canonical answer/facts/citation/warnings/release và
reply vẫn bằng preflight đã lưu; bốn control cũng khớp preflight. Với hai danh
sách003/007 đã so toàn bộ mã/tên và từng dòng reply, không chỉ so số lượng.
Các phép kiểm này không chứng minh cải thiện diễn đạt hoặc nghiệm thu học thuật.

## Nhóm review và bước tiếp theo

- Đọc [đáp án live nguyên văn](RAG_INTENT_F2_PRACTICAL_LIVE_RESPONSES_2026_11_14.md),
  [response/nguồn và đối chiếu](../data/hus/review/intent_f2_content_20261115_r1/responses_and_sources.json).
- Điền tên/ngày/nhận xét vào [CSV nhóm mới](../data/hus/review/intent_f2_content_20261115_r1/review_group_return.csv).
  Cả12 xác nhận còn pending. [Nhận xét AI riêng](../data/hus/review/intent_f2_content_20261115_r1/AI_review.csv)
  không điền thay người thật hoặc ghi đè CSV cũ.
- Chọn sửa prompt F2/nhận câu đếm khi cần; thêm regression offline, giữ schema,
  dữ kiện, scope và chính sách offline chỉ sau429. Lượt này **chưa sửa runtime/prompt**.
- Trước Google tiếp: prepare revision mới vì code pins cũ khác tại
  `app/hus/vector_query.py` sau tối ưu latency. Các file intent/prompt/validator
  được đối chiếu vẫn khớp pins lúc live; không sửa packet cũ để khớp code mới.
  Thống nhất budget mới, tính cả call hiểu ý định; không chuyển1 call cũ sang retry.

## Tính nguyên vẹn

Đã kiểm manifest pack/live,19 file được bảo vệ của pack/run/review cũ và pack/run
RC24 vừa đo giữ nguyên hash. [Review/checks/pins](../data/hus/review/intent_f2_content_20261115_r1/review.json)
được lưu riêng; manifest mới không khóa CSV người thật sau khi nhóm điền.
Manifest live vẫn
`3618cebce80c052b4969633da6f591ad2830cb2678dbab01b0a9f3a109e9c2f3`.

Không đọc key/file môi trường, gọi provider, sửa gold/run/review lịch sử, thay
default hoặc đưa code lên GitHub. Không chạy lại test rộng khi chỉ review tài
liệu/nguồn; không lấy số test lịch sử thành bằng chứng mới.

[Tiến độ và các bước tiếp theo](RAG_PROGRESS_AND_NEXT_PLAN.md)
