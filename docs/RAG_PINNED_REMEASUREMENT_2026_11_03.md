# Đo lại RAG trên snapshot ghim — 03/11/2026

Đã chạy lại96 request của `diagnostic_dev_v1` trên app RAG độc lập. Đây là **phép
đo development**, không phải nghiệm thu holdout mới. Kiểm tra review trước khi đo:
H2 vẫn0/56 quyết định accepted, nên không gửi câu H2 vào app/retriever.
**Recall@5≥90% trên holdout độc lập vẫn chưa được chứng minh.**

Không sửa runtime, retriever, nguồn/gold, review hay AI opt-in trong lượt này.
Chỉ bổ sung quan sát classifier và scorer tách lớp ở công cụ đo; không đưa gold
dataset/field/code vào request. Thu đủ96 prediction/trace trước bước chấm điểm.

## Snapshot và artifact của lần chạy mới

- Base Git `1287e2a`; tree còn dirty, `tested_commit=null`. Ghim SHA-256 thực,
  không gọi base commit là commit đã nghiệm thu.
- Release `hus-data-20261031-v3`, release SHA-256
  `27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4`.
- 111 file code/UI/dependency constraints/release/CURRENT/registry/binary được ghim
  và đối chiếu trước–sau; Python3.11.9 và54 distribution/version thực tế được ghi.
- [Report mới](../data/hus/evaluation/runs/dev_pinned_remeasurement_v1/report.json),
  [metric tách lớp](../data/hus/evaluation/runs/dev_pinned_remeasurement_v1/layered_metrics.json),
  [prediction/trace](../data/hus/evaluation/runs/dev_pinned_remeasurement_v1/predictions.jsonl)
  và [manifest](../data/hus/evaluation/runs/dev_pinned_remeasurement_v1/manifest.json).

Tạo thư mục run mới, không ghi đè baseline P1-2 hoặc hai run dev trước–sau sửa.
96/96 response body khớp lần dev sau sửa trước đó; không tuning hoặc chọn run có
điểm tốt nhất. Verify cache tái tính cả metric cũ và tách lớp,0 inference mới;
runtime/evaluator/artifact/environment đều khớp snapshot.

## Kết quả tách lớp

| Lớp | Kết quả | Mẫu số/phạm vi |
| --- | ---: | --- |
| Routing: đúng dataset |64/64 |Chỉ64 câu dương có đáp án; không suy từ response status |
| Routing: đúng field chuẩn hóa |64/64 |Quan sát classifier trước gate scope/evidence; map `course_name→name`, `prerequisites.raw_variants→prerequisites` chỉ ở scorer |
| Retrieval: thực sự gọi search |40/40 |24 F1+16 F3 bật AI; F2 là lookup |
| Routed Recall@5 có kiểm scope/field/code |39/40=97,5% |Mọi câu đủ điều kiện; không gọi search vẫn tính miss |
| Recall@5 trong những ca đã search |39/40=97,5% |Mẫu số conditional riêng; trùng mẫu số chính trong run này vì không có no-call |
| Search sai dataset/field hoặc filter loại anchor |Đều0 ca |Từ tham số của lần gọi thực; không chạy search ép theo gold |
| F2 đúng facts/scope/anchor/kiểm nguồn |24/24 |Không cộng F2 vào Recall@5 |
| Citation integrity trên đáp án có citation |64/64 |Oracle quote/row/page/hash/review/AI và GET binary thật |
| Đáp án có anchor nguồn dự kiến |61/64 |Chấm bảo thủ;3 ca cần người review nguồn/ý nghĩa |
| Precision theo anchor, lower bound |61/80=76,25% |80 citation phát ra;19 citation thay thế chưa được review ngữ nghĩa |
| Từ chối đúng thiếu nguồn/ngoài scope |24/24 |16 thiếu nguồn+8 ngoài phạm vi, không facts/citation |
| Yêu cầu AI opt-in đúng |8/8 |Không lộ generated content trước quyền cho phép |
| Từ chối sai trên câu dương |0/64 |HTTP failure không tính là abstention |
| Lỗi HTTP / sai ngành / mã môn / version |0/0/0/0 |Trong96 request dev, không suy thành bảo đảm mọi trường hợp |

32 ca control được báo riêng:8 ngoài scope và8 hỏi thông tin lớp hiện tại có
classifier `None/None`,8 hỏi assessment chính thức nhận `f3/official_assessment`,
8 chưa opt-in nhận `f3/content`. Các gate vẫn từ chối/yêu cầu quyền đúng; không
ép các ca không có dữ kiện hỗ trợ thành positive routing để nâng số đo.

Semantic citation precision và semantic source support giữ **null**. Quote/link
đúng không tự chứng minh đủ ý. Ba ca còn chờ:

- `DEV-Q006`: anchor trong top5 nhưng excerpt phát ra nói học tiếp nói chung;
  cần review mức hỗ trợ đầy đủ điều kiện/bậc học trong gold nháp.
- `DEV-Q049/050`: trích nguồn chương trình2023 khác web anchor/edition; cần
  xác nhận nội dung thay thế và applicability. `DEV-Q050` là Recall miss duy nhất.

Không sửa gold, phê duyệt nguồn thay thế hoặc đổi anchor để loại các ca khỏi báo cáo.

## Regression mới trên cùng runtime/data

- **1.479 Python tests đạt**,90 deselected,0 failure/error/skip; không chạy các
  marker PostgreSQL/full-catalog. Có một cảnh báo Starlette/httpx đã tồn tại.
- 147 test API/PDF/scope là tập con của1.479:answering54,citation oracle27,
  citations14,chat scope18,routing guards31,main/demo boundary3. Bao gồm wrong
  major/version/code,PDF GET/HEAD/range/hash failure,DOCX attachment,AI nhãn/link
  và auth/Origin boundary. Không cộng lại các tập con vào tổng.
- **50 ca Chromium mới**,4 ngành,F1/F2/F3/basic chat,reset/default AI opt-in,
  response chậm không xuất hiện sau đổi ngành,không gọi recommendation.
- **5 Node citation tests đạt**. Ruff `app tools tests` và diff whitespace đạt.
- 108 file runtime/UI/dependency/data của regression và136 file test giữ nguyên
  hash; số inventory khác111 file của runner đo vì phạm vi pin khác nhau.

Artifact regression:
[summary.json](../backups/hus_remeasurement_20261103/summary.json),
[JUnit](../backups/hus_remeasurement_20261103/offline.xml),
[browser report](../backups/hus_rag_demo/20261103-022830-535512/report.json).

### PDF viewer thực, tách khỏi kiểm binary/link

Đã click hai citation thật của câu dev `Tiên quyết MAT3325?` từ UI RAG hiện tại.
Chrome145 PDF plugin hoàn tất load,physical page13 và12 đúng,pending scrolls0,
scroll inner frame khớp viewport. Mỗi URL trả HTTP200/application/pdf,21.509.533
byte,hash `e6e33a8a489f7ab77f3db0c727cc4c837ba86f8f17a7eae17c9da08d3c066bd0`.

- [Viewer report](../backups/hus_remeasurement_20261103/pdf_viewer/20261102T193417894167Z/report.json).
- [Ảnh trang13](../backups/hus_remeasurement_20261103/pdf_viewer/20261102T193417894167Z/pdf-physical-page-13.png).
- [Ảnh trang12](../backups/hus_remeasurement_20261103/pdf_viewer/20261102T193417894167Z/pdf-physical-page-12.png).

Browser/server do test tạo đã đóng.108 pin giữ nguyên. Một lần thử viewer đầu
lỗi chờ trạng thái nút gửi khi input rỗng trong script kiểm thử; log/screenshot
giữ ở thư mục `20261102T193344265659Z`. Đã sửa đồng bộ của test runner và chạy
lượt mới đạt, không sửa app/data. Đây không phải chạy lại toàn bộ ma trận viewer
lịch sử47 ca; chỉ hai trang thật được yêu cầu kiểm trong lượt này.

Receipt tổng hợp ghim artifact/test/snapshot:
[hus_pinned_remeasurement_report.json](acceptance/hus_pinned_remeasurement_report.json).

## Cách tái tính và lệnh regression

```powershell
$ragPython = '.\backups\hus_integration\pr6-resolution-20261102\backups\pr6\ci-venv\Scripts\python.exe'
& $ragPython -X utf8 -m tools.evaluate_hus_diagnostic --verify-run data/hus/evaluation/runs/dev_pinned_remeasurement_v1

# Chỉ tạo inference dev mới khi có lý do, dùng thư mục mới:
& $ragPython -X utf8 -m tools.evaluate_hus_diagnostic --out backups/hus_eval/new_dev_run

& $ragPython -m pytest tests -q -m 'not postgres and not hus_postgres and not full_catalog_acceptance'
node --test tests/frontend/chat.test.cjs
& $ragPython -X utf8 -m tools.run_hus_rag_demo --smoke
```

Các test API từ chối wrong version kiểm riêng với UI: giao diện chọn ngành và
hiện decision version tương ứng, không có arbitrary-edition selector. Không mô tả
đổi ngành trên UI thành một phép thử nhập edition tùy ý.

Để chạy nghiệm thu holdout: trước hết cần người thật duyệt/chốt>=40 câu cùng
nguồn/gold/semantic overlap/nguồn thay thế, rồi ghim subset và snapshot mới.
Không dùng kết quả dev hoặc số regression pass để thay điều kiện đó. Giữ quy trình
[review→release](RAG_REVIEW_RELEASE_GATES_2026_11_03.md). Chưa commit/push/triển khai.
