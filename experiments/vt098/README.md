# VT-098 — test-first idempotent creation harness

**Dương Văn Tài — 23001925 — SE2026-T25 — thành viên — AI-07.**

Baseline: `7b387a394e334e217733a571ee76a573157a24f2`.
Nhánh: [`vt098/23001925-idempotency`](https://github.com/5-Bit-System/SE_Project/tree/vt098/23001925-idempotency).
Không merge nếu nhóm chưa review.

## Chạy test (từ root repository)

Python 3.11; không cần Docker, VNU, LLM, API key hoặc database production.
Nên dùng virtual environment riêng; cài dependency duy nhất của harness:

```powershell
python -m pip install -r experiments/vt098/requirements.txt
python -X utf8 -m unittest discover -s experiments/vt098 -p "test_*.py" -v
```

Yêu cầu 3 ghi nhận **18 test methods passed**. Yêu cầu 4 bổ sung test body đúng
16 KiB / vượt 1 byte sau khi xem coverage: hiện có **19 methods passed**, gồm
8 pairwise subcases (24/24 cặp), biên, rollback, conflict và reopen connection.
Đây là test harness, không phải test API/E2E production. Kết quả mutation,
line/branch coverage, flaky review và tải nằm trong [QUALITY_REPORT.md](QUALITY_REPORT.md).

## Slice và giới hạn

Tạo **bản nháp học kỳ rỗng** với nguồn/basis giả lập; gửi lại cùng account/key/body
trả response gốc, không tăng số plan/audit/receipt. Khác body với key đã dùng trả
409; cùng body nhưng key khác tạo phương án khác. Receipt không bị xóa khi plan
bị xóa và không có TTL. Account được test cung cấp như principal đã xác minh.

- `schema.py` nạp **đúng class `SemesterPlanInput`** từ `app/api/academic.py` bằng
  AST, không sao chép model và không import stack auth/runtime. Chỉ class này
  được compile; loader phải lỗi nếu class đổi và có dependency ngoài namespace.
- `harness.py` dùng SQLite trên file tạm, `BEGIN IMMEDIATE`, unique key
  `(account_id, operation, key_digest)` và một transaction cho ba loại ghi.
- Không nối harness vào production, không chạy migration HUS. Không kiểm chứng
  session/CSRF, eligibility môn thật, browser, PostgreSQL locking hoặc nhiều process.
  Nonempty course list bị từ chối rõ ràng để không giả lập quyết định học vụ.
- Lỗi trước commit được inject sau từng loại ghi; lỗi sau commit mô phỏng mất
  phản hồi ở boundary hàm. Đây **không phải lỗi mạng TCP hoặc process-kill thật**.
- Reopen test tạo lại object/connection trên cùng DB. Không gọi nó là restart OS
  hay kiểm chứng crash recovery của production.

## Chuỗi test-first và hai test AI được sửa

1. [`9b18b7d`](https://github.com/5-Bit-System/SE_Project/commit/9b18b7d729976fb7704976845cab70f3dd1d21d1):
   scaffold tạo mới mỗi lần, hai test AI yếu vẫn xanh nhưng test so sánh kết quả
   sau reopen đỏ vì ID khác. `evidence/draft-red.json`: 3 tests, 1 failure, exit 1.
2. [`a20c996`](https://github.com/5-Bit-System/SE_Project/commit/a20c996f65b017b4dc1a2e3d9b692a25fec42f94):
   sửa D1 status-only thành `test_retry_response_and_counts`; thay D2 happy path
   trùng thành `test_failure_before_commit_rolls_back_then_retry`; thêm pairwise
   và các oracle khác **trước patch**. `evidence/reviewed-red.json`: 18 methods,
   21 assertion failures và 1 business error (subtest failures được đếm riêng), exit 1.
3. Commit patch tiếp theo chỉ đổi logic `harness.py` (27 dòng thêm, 8 dòng bỏ).
   `evidence/patch.diff` lưu diff thực tế và `PATCH_REVIEW.md` ghi review trước
   commit. **Không đổi file test sau red.** `evidence/green.json`: 18 methods, OK,
   exit 0. SHA-256 file test trong hai artifact reviewed-red/green phải giống nhau.

Tái hiện red trong checkout riêng để không sửa nhánh nộp:

```powershell
git worktree add --detach ../vt098-red a20c996f65b017b4dc1a2e3d9b692a25fec42f94
cd ../vt098-red
python -X utf8 -m unittest discover -s experiments/vt098 -p "test_*.py" -v
```

Lệnh ở commit red được kỳ vọng trả exit 1; quay về checkout nhánh nộp để chạy
lại lệnh test và nhận exit 0. Không ghi đè log lịch sử để giả lập lần chạy trước.
`run_evidence.py` là công cụ thu stdout/stderr thật cho lần thực nghiệm; trường
`head_before_capture` là parent HEAD khi working tree chưa commit, **không phải**
commit khẳng định đã chứa patch. Source hashes xác định đúng bytes đã chạy.

## Oracle, risk và file

| Hành vi | Test method (trong `test_harness.py`) | Liên hệ kế hoạch |
|---|---|---|
| Replay giữ JSON/version, đếm DB từ connection độc lập | `test_retry_response_and_counts` | TC01 / AC2 / RK1 |
| 8 tổ hợp, account/key/body/dispatch | `test_pairwise_create_replay_conflict_and_scope` | TC01–08 ở mức harness |
| Conflict giữ dữ liệu gốc; ý định tạo mới | `test_conflict_keeps_original_unchanged`, `test_new_key_same_body_creates_separate_intent` | AC3–4 |
| Key 1/63/64 và key sai | `test_valid_key_boundaries`, `test_invalid_keys_do_not_write` | TC09–10 ở mức harness |
| Schema thực/default/JSON order | `test_canonicalization_uses_real_schema_defaults`, `test_real_schema_forbids_extra_and_non_strict_input` | TC11 / validation |
| Rollback sau từng loại ghi, retry một lần | `test_failure_before_commit_rolls_back_then_retry` | TC14 ở mức harness |
| Commit rồi mất kết quả trả về | `test_lost_response_after_commit_replays_receipt` | TC15 ở mức harness |
| Mở connection/object mới; plan bị xóa; quota 100 | Các method reopen/deleted/limit | TC16–18 ở mức harness |

TC12–13 (auth/CSRF), browser TC19–20 và mọi test API/PostgreSQL trong bảng thiết
kế vẫn chưa chạy. SQLite serialization không chứng minh PostgreSQL row locking.
Chỉ dùng tài khoản/basis và dữ liệu tự tạo, không dùng test data của thành viên khác.

Chi tiết plan và assumptions: [PLAN_REVIEW.md](PLAN_REVIEW.md).
Khai báo AI và trách nhiệm review: [AI_USAGE.md](AI_USAGE.md).

## Chạy lại yêu cầu 4

Dùng môi trường riêng (coverage 7.17.0); các lệnh quality ghi đè artifact cùng
tên nên nên chạy trong checkout riêng khi muốn giữ nguyên log lịch sử đã commit.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r experiments/vt098/requirements-quality.txt
.\.venv\Scripts\python.exe -X utf8 -m experiments.vt098.quality coverage
.\.venv\Scripts\python.exe -X utf8 -m experiments.vt098.quality flaky
.\.venv\Scripts\python.exe -X utf8 -m experiments.vt098.quality load --workers 150 --rounds 3
```

Mutation được giữ **chỉ ở nhánh tạm**
[`vt098/23001925-boundary-mutation-reviewed`](https://github.com/5-Bit-System/SE_Project/tree/vt098/23001925-boundary-mutation-reviewed),
commit `0a057964cb2819cda5af0abbadd4b748536f8600`. Không merge nhánh này.
Tạo worktree mới từ commit đó, rồi dùng runner ở nhánh nộp để so sánh:

```powershell
git worktree add --detach ../vt098-mutation 0a057964cb2819cda5af0abbadd4b748536f8600
.\.venv\Scripts\python.exe -X utf8 -m experiments.vt098.quality mutation --mutant-root ../vt098-mutation
```

Runner yêu cầu toàn file test giống nhau giữa control/mutant và runtime harness
chỉ khác đúng `len(key) > 64` thành `len(key) >= 64`. Mutation không nằm trên
nhánh nộp; evidence riêng có control exit 0 / mutant exit 1.

Kết quả tải: 9 burst, mỗi burst phát 150 tác vụ qua barrier, tổng 1.350 mẫu; peak
lời gọi thực tế 149–150, p95 cao nhất 3,0686 giây, không lỗi và số ghi đúng.
Đo SQLite `create()` trên máy cục bộ, chưa chứng nhận p95 HTTP/production.
