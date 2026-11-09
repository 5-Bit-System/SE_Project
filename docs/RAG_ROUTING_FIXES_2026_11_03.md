# Sửa routing, chọn field và gate RAG — 03/11/2026

Đã sửa local trên `crawldata`, base Git `1287e2a`; chưa commit/push. Phạm vi vẫn là
app HUS độc lập F1/F2/F3/basic chat. Không nối ranking, tài khoản, VNU, DB hoặc LLM.

## Thay đổi

- Tách quy tắc nhận diện vào `app/hus/question_routing.py`: cách hỏi tự nhiên về
  chương trình/nghề nghiệp/học tiếp, tên môn, học trước, nội dung và năng lực.
  Quy tắc theo cụm từ, không đọc bộ dev/gold trong runtime.
- Chỉ bỏ đúng phần meta bị phủ định đã nhận diện, giữ phần yêu cầu phía sau để
  kiểm tra nguồn/phạm vi. “Không yêu cầu đề cương chính thức” không tự chặn câu
  tham khảo, nhưng “không cần … vui lòng xác nhận tỷ lệ thi” vẫn bị từ chối.
- Không hiểu “khối lượng tín chỉ” thành yêu cầu lương sau khi bỏ dấu.
- Chặn yêu cầu xếp hạng/chọn môn/thao tác bên ngoài trước mọi override dataset/field.
- F2 giữ lookup cấu trúc. Tên đầy đủ chỉ được resolve trong đúng ngành/version;
  tên đa nghĩa hoặc mâu thuẫn tên/mã cần làm rõ. Quyết định ghi trong câu hỏi
  không được mâu thuẫn với version request. Không fuzzy-match tên hoặc tự đổi version.
- Gate sau retrieval trong `app/hus/answer_support.py` bỏ từ hội thoại, còn topic
  cụ thể phải xuất hiện trong quote. Hệ tài năng/hệ chuẩn, cấp bằng và thời lượng
  cần quote hoặc metadata variant tương ứng; không dùng intent label để chứng minh.
- Không đổi BM25, schema citation, binary resolver, review/AI opt-in, CURRENT hoặc
  dữ liệu/release. Mỗi request vẫn dùng snapshot đã chọn; thiếu nguồn phải từ chối.

## Phép đo trước–sau trên dev

Gói `diagnostic_dev_v1` giữ nguyên hash. Có96 request/88 chuỗi,24 request/ngành;
gold nháp kế thừa nguồn đã exposed. Các con số dưới đây **chỉ đo development**,
không so sánh trực tiếp với baseline P1-2 gồm48 câu và không chứng nhận holdout mới.

| Chỉ số | Trước sửa | Sau sửa |
| --- | ---: | ---: |
| Routed Recall@5, toàn bộ F1/F3 đủ điều kiện |6/40 (15%) |39/40 (97,5%) |
| F2 đúng facts, anchor và kiểm nguồn |0/24 |24/24 |
| Câu dương trả lời có anchor nguồn dự kiến |0/64 |61/64 |
| Câu dương bị từ chối |64/64 |0/64 |
| Đúng trạng thái trong gold nháp |20/96 |96/96 |
| Guard đúng trạng thái và không lộ facts/citation |20/32 |32/32 |
| Yêu cầu AI opt-in đúng |0/8 |8/8 |
| Lỗi HTTP / ngành / mã môn / phiên bản phát hiện |0 /0 /0 /0 |0 /0 /0 /0 |

Sau sửa:64/64 đáp án dương qua oracle quote/row/page/hash/review/AI và GET binary.
Đây là **integrity**, không chứng nhận đúng ý nghĩa mọi claim. Có80 citation,
61 citation khớp anchor,19 nguồn thay thế chưa được người review chấm; lower-bound
precision theo anchor là61/80=76,25%. Có3 câu chưa cite anchor dự kiến,1 ca không
có anchor trong top5. Semantic precision/source support giữ null chờ reviewer.

Ba ca cần review:

- `DEV-Q006`: anchor học tiếp đã ở top5 nhưng hai excerpt trả ra mô tả khả năng
  tiếp tục học nói chung; chưa đủ để tự coi đã hỗ trợ thạc sĩ/tiến sĩ và điều kiện.
- `DEV-Q049/050`: nguồn chương trình DOCX2023 có nội dung gần tương đương gold,
  nhưng khác web anchor/edition. Cần reviewer xác nhận nguồn thay thế/phạm vi áp dụng.
  `DEV-Q050` là ca duy nhất chưa có web anchor trong top5.

Không đổi gold, chọn lại anchor hoặc nâng điểm để loại các trường hợp này khỏi báo cáo.

Runner `tools.evaluate_hus_diagnostic` chỉ đưa request vào app. Lưu tất cả96
prediction/trace trước khi chấm gold. Code/hash/scope/nguồn/test identity và trạng
thái dirty được ghi riêng; không gọi Git HEAD là commit đã nghiệm thu.
Name-only F2 được oracle gắn mã từ record nguồn **sau** khi thu prediction, không
bơm mã/field/gold vào router. Trước sửa runner chưa có binding này; vì không có
đáp án dương nào nên cache trước vẫn tái tính đúng. Verify báo khác hash công cụ
và runtime trước–sau một cách tường minh.

Artifact:

- [Trước sửa](../data/hus/evaluation/runs/dev_before_routing_v1/report.json).
- [Sau sửa](../data/hus/evaluation/runs/dev_after_routing_v1/report.json).
- Mỗi run có predictions, retrieval trace, citation audits, scored cases và manifest.
  Không ghi đè lần cũ; cả P1-1/P1-2/P2 gốc giữ nguyên byte và ý nghĩa lịch sử.

## Kiểm tra và tái lập

Trên runtime cuối cùng:

- **1.444 Python tests đạt**,90 deselected: bộ offline bỏ các marker PostgreSQL
  và full-catalog acceptance. JUnit ở `backups/hus_diagnostic_20261103/routing-offline.xml`.
- **212 test tập trung đạt**, gồm96 request dev,31 guard, regression answering/chat
  và8 test công cụ đo; các số này là tập con của suite, không cộng thêm vào1.444.
- **50 ca Chromium và scope isolation đạt**, gồm bốn ngành, reset AI opt-in,
  đổi ngành khi chờ, binary hash và hai trang13/12 cùng PDF. Report:
  `backups/hus_rag_demo/20261103-013648-568729/report.json`.
- **5 Node citation tests đạt**; `ruff check app tools tests` và `git diff --check` đạt.
  `ruff check .` còn2 lỗi từ trước trong artifact
  `data/hus/review/p13_followup_v1/generation_script.py` (import order và semicolon);
  không sửa artifact nguồn/receipt P1-3 để làm sạch lint ngoài phạm vi.
- Verify cache sau sửa tái tính96 ca,0 inference mới, hash runtime/evaluator khớp.
  Validator dev xác nhận15 file P1-1/P1-2/P2 gốc giữ nguyên byte; release loader
  vẫn kiểm toàn bộ payload pinned/CURRENT. Không đổi source/review.

Receipt tổng hợp: [hus_routing_fixes_report.json](acceptance/hus_routing_fixes_report.json).
Không chạy test DB hoặc remote CI trong lượt này; có một cảnh báo deprecation
Starlette/httpx đã tồn tại. Chưa commit/push hoặc kích hoạt production.

Môi trường đủ dependency đã có:
`backups/hus_integration/pr6-resolution-20261102/backups/pr6/ci-venv/Scripts/python.exe`.
Python global thiếu `argon2`, nên lần thử một số regression product bằng Python
global không chạy được; không sửa dependency hoặc product để bỏ qua lỗi môi trường.

```powershell
# Chỉ tái tính cache, không inference mới:
python -X utf8 -m tools.evaluate_hus_diagnostic --verify-run data/hus/evaluation/runs/dev_after_routing_v1
python -X utf8 -m tools.validate_hus_diagnostic

# Nếu có lý do đo dev lần khác, chọn thư mục mới:
python -X utf8 -m tools.evaluate_hus_diagnostic --out backups/hus_eval/dev_new_run

python -m pytest tests/hus/test_routing_diagnostic.py tests/hus/test_routing_guards.py tests/hus/test_answering.py tests/hus/test_chat_scope.py tests/hus/test_diagnostic_evaluation.py -q
node --test tests/frontend/chat.test.cjs
python -X utf8 -m tools.run_hus_rag_demo --smoke
```

Routing/gate hiện vẫn lexical. Cần holdout mới ít nhất40 câu có reviewer độc lập,
đối chiếu ngữ nghĩa nguồn thay thế và các ca chưa có anchor; không tự nâng review,
hiệu lực học vụ hoặc bật official F3 từ kết quả dev. Vector/reranker/LLM vẫn hoãn
cho tới khi phép đo mới chứng minh nhu cầu. Chưa triển khai hoặc kích hoạt production.
