# Handoff cho session làm PDF — chưa tạo PDF ở lượt này

Nguyễn Công Việt · MSSV23001953 · BT cá nhân3 · VT-101 · SE2026-T25 · Nhóm trưởng.
Dự án AI-07 – Explainable Course Recommender, https://github.com/5-Bit-System/SE_Project.
Lecture06 AI-assisted Software Development & Vibe Coding; Lecture07 Software
Testing & Quality Engineering theo mô tả user. Chưa có slide/rubric gốc; cần
sinh viên đối chiếu nếu giảng viên có biểu mẫu riêng.

## Version và kết quả phải giữ nguyên

- Baseline `7b387a394e334e217733a571ee76a573157a24f2`.
- Branch `bt3/23001953-VT-101-search-contract`;
  [link branch](https://github.com/5-Bit-System/SE_Project/tree/bt3/23001953-VT-101-search-contract).
  Trạng thái push/PR chính xác: PUBLICATION.md, không suy từ link dự kiến.
- RED `a5aab95c9d8453093621453b25f5807e584e15a3`, intentional37failed5passed.
- Implementation `cb3b35d944364e74fec65af4b299a79fcb90df36`, initial78passed,
  offline619passed79deselected0skipped, focused46passed.
- Harness/evidence `2e864fc565e525da3b967f6c607e1ba5860f67f5` đã push,
  GitHub Actions3/3passed. Receipt tiếp theo theo PUBLICATION.md; PR chưa tạo.
- Mutant valid syntax swallow Exception/default:3failed39passed, killed;
  submission không có mutant. Coverage service12/12line4/4branch, toàn3module
  chỉ83/163lines và6/8branches. Flaky6×46passed. Browser realHTTP passed.
- **Performance chưa đạt ổn định**:100workers,6000request/config, default p95
  3534,735/1698,054/2590,135ms;8thread3293,964/2501,387/2742,991ms.
  12000/12000correct,0errors, peak100, một run vượt3s mỗi config.
- Không production/realVNU/PDF/academic acceptance; không human approval ngầm.

## Map rubric → tài liệu/evidence

| Hạng mục theo yêu cầu đã nhận | Tài liệu/đầu vào PDF |
|---|---|
| Cá nhân/team/variant |README, SPEC, file này |
| Problem/3–5AC/NFC/invariants |SPEC.md |
| AI plan +≥2review adjustments |PLAN.md điểm1..3, file/symbol evidence |
| Risk-based levels +≥10cases |TEST_STRATEGY.md,18case groups |
| Contract old/new, risk schema/client |SPEC, C::test_legacy_consumer_array_fields_types_order_and_extras, new envelope/error tests |
| Test-first meaningful RED |evidence/red.json/log; commit a5aab95 |
| AI-assisted patch/review/GREEN |PATCH_REVIEW.md; cb3b35d; green/offline-green/final-* logs |
| Deliberate swallow/default bug |evidence/mutation.patch/json/log; REPORT mutation |
| Coverage/ACrisk map/flaky |coverage.json/report.log; TRACEABILITY; flaky-runs.log/json |
|100concurrency/p95≤3s |REPORT performance; performance[-tuned]-results.json/requests.csv; profile.log; giữ failed SLO |
| AI disclosure +≥2untrusted outputs |AI_USAGE_LOG.md, lỗi runner/harness thực tế và cách kiểm chứng |
| Reflection250–350từ |REFLECTION_DRAFT.md:318whitespace-separated words, AI draft sinh viên cần sửa/xác nhận |
| Reproduction/source/Git/evidence |README commands; PUBLICATION; final-review/root-integrity evidence |

Đọc JSON/log/CSV làm nguồn số liệu, không chỉ dựa tóm tắt. Không biến exit1 của
mutant thành suite production fail; không biến failed benchmark thành passed.
Initial harness setup failure logs là khác với feature RED và loadSLO failures.
Không cần đưa toàn bộ6000CSVrows vào8trang; bảng summary đủ, file gốc ở phụ lục/link.

## Gợi ý bố cục ≤8 trang nội dung chính

1. Thông tin cá nhân, biến thể, problem/scope/baseline.
2. Contract cũ/mới, invariants,5AC và NFC.
3. Revised plan, các đề xuất AI đã sửa/bác bỏ bằng code evidence.
4. Risk strategy và test-case table chọn lọc (bảng đầy đủ ở phụ lục).
5. RED→patch→GREEN, diff chính, contract compatibility.
6. Mutation +coverage+risk coverage/flaky, giải thích confidence/limits.
7.100concurrency: workload,percentile, số trước/sau và **SLO chưa đạt ổn định**.
8. Review, residual risks, reflection, nguồn/link tái lập.

Phụ lục riêng: AI Usage Log, bảng case đầy đủ, command/log excerpts, screenshot
nếu sinh viên bổ sung và raw CSV link. Không thêm ảnh giả hoặc screenshot chưa chụp.

## Sinh viên cần tự làm trước khi nộp

- Đọc route/service/schema và consumer contract tests; chạy lại RED/GREEN/mutant.
- Xác nhận thiết kế additive API phù hợp bài; xem yêu cầu có bắt buộc UI hoặc
  SLO phải đạt hay cho phép phân tích fail. Hiện tại không đạt ổn định, không giấu.
- Đọc số đo/giới hạnPG/offset, kiểm link remote và CI trong PUBLICATION.
- Tự sửa reflection cho đúng trải nghiệm, kiểm rubric gốc/độ dài8trang.
- Tự xác nhận trách nhiệm, không coi tài liệu AI là việc đã review/approve.

Câu cam kết **chỉ đưa vào PDF sau khi sinh viên tự xác nhận**:

> “Tôi chịu trách nhiệm về toàn bộ code, test và nội dung bài làm; tôi đã khai báo việc sử dụng AI.”
