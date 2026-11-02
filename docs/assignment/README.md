# Chạy và review VT-100

Branch: `bt3/23001946-vt100`. Original baseline: `5239b7333a8f8cdf0f919e6b0505af0def99fe23`.
Revision: assertion RED `a1afd93`, GREEN `68b99df`. Không merge trước team review.

Từ repo root:

```bash
conda activate SE_Project
python -m pytest -q tests/importing -s
python -m tools.check_vt100_mutation
python -m pytest -q tests/importing
python -m tools.measure_vt100_lines
python -m pytest -q tests -m "not postgres and not hus_postgres and not full_catalog_acceptance"
python -m ruff check .
```

Mutation tạm phủ định Boolean, tự khôi phục source trong finally, trả exit0 khi
3 test phát hiện lỗi; sau đó chạy GREEN lại. Công cụ line trace dùng stdlib,
không đo branch và không chạy benchmark dưới tracing.

Adapter nhận `course_code,grade,term` theo đúng thứ tự; numeric grade bắt buộc,
term rỗng được phép. Dùng TranscriptRecord/StudentTranscript hiện có, trả bản
sao transcript, không ghi DB/API. Dữ liệu và catalog test hoàn toàn synthetic.
200 task chờ barrier, peak200 tính cả thời gian chờ; E2E p95 tính từ submit,
nearest-rank index189. Không suy ra hiệu năng 200 HTTP users hoặc production DB.

Xem [spec/plan](../BT3_SPEC_AND_PLAN.md), [revision plan/exact prompt](REVISION_PLAN.md),
[original user prompt](ORIGINAL_USER_PROMPT.txt), [strategy](TEST_STRATEGY.md),
[evidence](TEST_FIRST_EVIDENCE.md), [PDF](../../deliverables/BT3_23001946_VT-100.pdf).
Historical logs giữ nguyên; kết quả hiện tại dùng `revised-*` và
`mutation-boolean-negation.txt`. PDF source là file HTML cùng thư mục, dàn trang
liên tục; xuất bằng Chrome headless với `--no-pdf-header-footer`.
