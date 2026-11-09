# Sửa routing tên/mã và xem trước nội dung — 03/11/2026

Đã hoàn thành mục 1 của kế hoạch: chuyển tám ca đã lộ sang dev mới, sửa nhận diện
tên/mã và phân biệt xem trước nội dung với hỏi tiên quyết. **Routing 0/8→8/8**;
bốn câu tên môn trả đúng nguồn, bốn câu nội dung đã gọi F3 đúng scope. Bốn câu
nội dung gốc vẫn bị gate bằng chứng từ chối; chưa xử lý mục 2 hoặc nghiệm thu RAG.
[Receipt tổng hợp](acceptance/hus_routing_name_preview_report.json).

## Phạm vi thay đổi

Chỉ thay đổi runtime ở [question_routing.py](../app/hus/question_routing.py):

- Nhận diện “nguyên tên/tên của mã”, “tên của môn/học phần” bằng luật tên môn;
  tra F2 theo mã/ngành/phiên bản hiện có, không bổ sung bảng tên hoặc dữ kiện mới.
- Chỉ coi “hình dung/tìm hiểu/xem trước môn” là preview khi có yêu cầu nội dung,
  mục tiêu hoặc đánh giá rõ. Giữ ranh giới mệnh đề; “Tôi muốn tìm hiểu: trước môn
  … cần học gì?” vẫn là câu tiên quyết. “Cần/phải học/hoàn thành” giữ ưu tiên
  tiên quyết cả khi không có dấu phân cách hoặc nằm ở mệnh đề khác.
- Giữ nguyên cách nối các mệnh đề của `requested_text()` cho các guard hiện có.
  Test và review đối chiếu với 264 câu evaluation xác nhận đầu ra không đổi.

Không sửa gate `answer_support`, answerer, retriever, schema, UI, source/review,
CURRENT hoặc release. Giữ scope ngành/phiên bản/mã, xung đột tên–mã, review dự án,
AI opt-in và chặn yêu cầu official/hiện hành/ngoài phạm vi.

## Dev mới và phép đo trước–sau

[diagnostic_dev_v2_routing](../data/hus/evaluation/diagnostic_dev_v2_routing/README.md)
có tám request giữ nguyên nội dung từ H2:Q005/Q009/Q019/Q023/Q033/Q037/Q047/Q051,
hai câu mỗi ngành. Gold/evidence kế thừa bản đã review trực tiếp từ nguồn;
đổi ID dev, không dùng dự đoán để tạo gold. Đã freeze trước khi sửa runtime và
ghi [exposure log](../data/hus/evaluation/diagnostic_dev_v2_routing/exposure_log.json).
Bộ này dùng để phát triển, không phải holdout độc lập. Các cờ ở thời điểm tạo
parent pack là lịch sử; hiện tám câu đã được dùng để sửa routing.

Collector gọi API thật trên TestClient, chỉ truyền request đã ghim; lưu response,
classifier và search trace trước khi chấm. Không ép dataset/field/code kỳ vọng.

| Tiêu chí trên tám ca dev | Trước | Sau phiên bản cuối |
| --- | ---: | ---: |
| Dataset + field đúng | 0/8 | **8/8** |
| Bốn câu tên có đáp án/anchor/facts đúng | 0/4 | **4/4** |
| Bốn câu preview gọi đúng search F3/content | 0/4 | **4/4** |
| Anchor preview trong top5 | 0/4 | **4/4** |
| Preview gốc trả lời đủ nguồn theo scorer | 0/4 | **0/4 — còn gate** |

[Run trước](../data/hus/evaluation/runs/dev_v2_routing_before/report.json),
[run cuối](../data/hus/evaluation/runs/dev_v2_routing_after_need_guard/report.json).
Giữ các run trung gian nguyên vẹn; khi đối chiếu hiện trạng dùng run cuối.
Chỉ router khác giữa hai snapshot runtime/artifact; môi trường và evaluator
giữ nguyên. Baseline P11/P12/P2, dev cũ, toàn bộ H2/gold/prediction/review và dữ
liệu nguồn giữ byte; 357 input được bảo vệ, không gồm file router được phép sửa.

## Kiểm chứng và giới hạn

Đã viết test trước khi sửa và xác nhận thất bại đúng nguyên nhân. Bộ mới có 62
test cho tám ca gốc, cách hỏi tự nhiên, tiên quyết thật có/không dấu phân cách,
scope/tên–mã/version/review, official và AI opt-in. **194 test routing/guard/dev
đạt**, Ruff trên router và file test đạt. Rà chéo code đã kiểm các ranh giới mệnh
đề/“cần học” và không còn phát hiện Important trong phạm vi này.

Regression mới trên phiên bản cuối: **1.541 test offline đạt/90 deselected,
5 test Node, 50 ca Chromium**; kiểm API/scope/AI opt-in/citation và UI đổi ngành,
response cũ/PDF links. 111 artifact và 138 file test giữ nguyên trong lượt kiểm;
cache dev cuối tái tính khớp. Có cảnh báo Starlette/httpx đã biết. Không chạy
PostgreSQL/HUS PostgreSQL/full-catalog hoặc nghiệm thu production. Các child
process kiểm thử dùng `PYTHONUTF8=1` để thống nhất encoding trên Windows.

Chưa chạy lại toàn bộ 56 câu H2 trên phiên bản cuối; số 80% trong báo cáo H2 là
phép đo trước sửa. Không suy Recall toàn bộ hoặc ngưỡng90% từ tám câu dev đã dùng
tuning. Bước tiếp theo là gate sau retrieval và đủ ý nhiều chunk; giữ riêng lỗi
biểu diễn tiên quyết `[]`/`[null]`. Chưa commit/push hoặc triển khai.
