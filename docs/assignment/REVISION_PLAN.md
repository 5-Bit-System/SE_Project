# Review-driven VT-100 revision — plan before code

Baseline for this second iteration: e54f4bc095c056cd24c6af3f4ec38928ceb63390.
Original baseline and RED log remain intact; do not rewrite them.

## Exact revision prompt recorded before code

“Đối chiếu bản chấm thử BT3 với repository. Thêm adapter CSV nhỏ dùng
TranscriptRecord và StudentTranscript hiện có; định nghĩa schema synthetic rõ
ràng, bảo toàn input và valid rows; không thêm API/DB hay quy tắc trường mới.
Viết test trước, chạy một stub trả zero imports để có RED ở assertion, rồi
triển khai GREEN. Bổ sung blank-header/row-width tests. Mutation phải phủ định
trực tiếp Boolean, chạy test và khôi phục source trong finally. Sửa benchmark:
200 workers chờ chung barrier, đo submitted-to-completed, ghi peak active,
nearest-rank p95 bằng ceil(.95*n)-1. Cập nhật spec/test/docs/PDF, reflection
250–350 whitespace words; giữ dàn trang liên tục. Không giả prompt cũ hoặc
claim production/database performance. Không merge.”

This is a new agent work instruction, recorded verbatim now, not a reconstruction
of the original prompt. The original user assignment is preserved separately.

## Reviewed assumptions and decisions

1. No domain CSV importer exists, but real TranscriptRecord/StudentTranscript do
   exist in app/transcript.py. Reuse their normalization, grade 0..10, term 1..12,
   passing threshold and duplicate policy; the earlier domain-isolation argument
   was too restrictive. Add a narrow adapter instead of another domain model.
2. CSV columns are an explicit harness contract: course_code,grade,term (this
   order); numeric grade is required, blank term means None. This is not the
   university export schema. Reject duplicate existing/within-batch courses,
   foreign catalog codes and mismatched programs. Do not overwrite old grades.
3. No DB transaction or API behavior is demonstrated by an in-memory adapter.
   Test its output through the existing eligibility rule engine using synthetic
   reviewed fixtures. Do not change the product passing or source-review rules.
4. 200 submitted jobs do not establish overlap. Add bounded barrier rendezvous,
   counters under Lock, submission timestamps and nearest-rank percentile.
   GIL means overlap is not simultaneous CPU execution or HTTP-user capacity.

## Files and sequence

- This plan and exact prompt, then test/stub and captured assertion RED.
- app/importing/transcript.py and opt-in expected-columns validation in batch.py.
- tests/importing/test_transcript_import.py: partial grades, no overwrite,
  duplicate, bounds/term/blank, major/schema, existing eligibility consumer.
- tests/importing/test_batch.py: blank field header, narrow/wide rows, Unicode.
- tests/importing/test_batch_performance.py: overlap/end-to-end p95 and tests.
- Reproducible temporary negation mutation script, evidence logs, full regression,
  Ruff, coverage if available; then docs and continuous-layout PDF.

Student-confirmed challenge remains: “Repo có sẵn CSV importer — tôi bác bỏ:
tìm kiếm không thấy API/domain importer”. Additional technical challenges above
are agent review findings, not invented student statements.
