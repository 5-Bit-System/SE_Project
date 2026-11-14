# SE2026 BT3 — 23001956 — VT-102

Sinh viên: **Vũ Khắc Huy Vinh**, SE2026-T25, thành viên, AI-07.
Nhánh nộp: `feat/vt102-async-task-progress`.
Baseline: `7aa9d939ddca47461dbc7a55972fdfbec7c434fe`.

## Checkout và cài đặt

```powershell
git fetch origin
git switch --track origin/feat/vt102-async-task-progress
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-vt102.txt -c requirements-lock.txt
# Browser E2E cần thêm requirements-portal.txt và Google Chrome.
.venv/Scripts/python.exe -m pip install -r requirements-portal.txt -c requirements-lock.txt
$env:PYTHONUTF8 = '1'
New-Item -ItemType Directory -Force backups/vt102_reproduce | Out-Null
```

Nếu nhánh đã tồn tại local, dùng `git switch feat/vt102-async-task-progress`.
Tests offline không cần `.env`, PostgreSQL, tài khoản VNU hoặc API key.
Không dùng credential hay bảng điểm thật làm fixture.

## Chạy lại

```powershell
# Feature + queue, 29 instances:
.venv/Scripts/python.exe -m pytest tests/integrations/test_vt102_async_progress.py tests/integrations/test_vt102_queue.py -q -p no:cacheprovider --basetemp backups/vt102_reproduce/feature
# Toàn nhóm offline và PDF acceptance, loại 80 test PostgreSQL:
.venv/Scripts/python.exe -m pytest tests -q -m "not postgres and not hus_postgres" --full-catalog-root docs/acceptance/hus_2022 -p no:cacheprovider --basetemp backups/vt102_reproduce/full
# Line + branch coverage, phạm vi ba module liên quan:
.venv/Scripts/python.exe -m coverage run --branch --data-file=backups/vt102_reproduce/data --source=app.services.portal_sync_jobs,app.api.portal,app.integrations.daotao.runtime -m pytest tests -q -m "not postgres and not hus_postgres" --full-catalog-root docs/acceptance/hus_2022 -p no:cacheprovider --basetemp backups/vt102_reproduce/coverage
.venv/Scripts/python.exe -m coverage report --data-file=backups/vt102_reproduce/data
# Harness 40 actor / 160 requests; ghi file mới để giữ evidence lần gốc:
.venv/Scripts/python.exe -m tools.vt102_load --output backups/vt102_reproduce/load.json
# Chrome; toàn bộ route được intercept, không cần server đang chạy:
.venv/Scripts/python.exe -m tests.frontend.check_vt102_async_progress
.venv/Scripts/python.exe -m ruff check .
```

Mỗi lần chạy chọn `--basetemp` mới, không xóa artifacts dùng trong báo cáo.
Harness dùng ASGI thật và fake subprocess VNU/store/auth repository; nearest-rank
p95 được đo riêng POST, retry và poll. Đạt ngưỡng 1.5s ở đây không chứng minh
hiệu năng mạng, DB hoặc cổng VNU thật. PostgreSQL tests có hướng dẫn riêng trong
`tests/database/README.md`; bài này không chạy chúng trên dữ liệu thật.

## RED → GREEN, mutation và artifacts

- Spec: [STEP1_SPEC_PLAN.md](docs/vt102/STEP1_SPEC_PLAN.md).
- Strategy/23 case IDs và Equivalence Partitioning:
  [STEP2_TEST_STRATEGY.md](docs/vt102/STEP2_TEST_STRATEGY.md).
- Log RED gốc: `docs/vt102/evidence/red/pytest.txt` — 12 FAIL / 13 PASS, exit1;
  người dùng đã xác nhận RED trước product patch. Commit `1fe363e` giữ đúng hash
  test gốc; dùng worktree tách biệt checkout commit đó để tái hiện RED.
- Implementation GREEN: `7a06e62`; log đầy đủ ở `evidence/green/pytest.txt`.
- Mutation `8a4fc64` trên nhánh thí nghiệm cục bộ riêng map progress về 0:
  6 FAIL / 23 PASS; revert `3093c3b`: 29 PASS, tree khớp GREEN. Receipt/log ở
  `docs/vt102/evidence/mutation/`. Hai commit thí nghiệm không là ancestor của
  nhánh nộp và không được push lên nhánh nộp.
- Tái hiện mutation sau khi checkout feature: tạo worktree/branch tạm, đổi duy
  nhất `progress_percent` trong `app/services/portal_sync_jobs.py` thành 0,
  chạy suite feature, phải thấy TC08 fail 0 != 100; revert rồi chạy lại. Không
  thực hiện trên worktree có thay đổi chưa lưu. Không cần truy cập nhánh tạm cũ.
- Báo cáo: `docs/vt102/BT3_23001956_VT-102.tex`, một file standalone cho Overleaf;
  bản PDF cùng tên khi biên dịch thành công. Upload `.tex`, chọn **XeLaTeX**,
  rồi Recompile. File cũng có nhánh pdfLaTeX để tránh lỗi compiler/fontspec.
- Reflection được đếm theo token cách nhau bằng whitespace, 315 từ:
  `docs/vt102/REFLECTION.md`. Sửa theo trải nghiệm cá nhân trước khi nộp.

Idempotency chỉ áp dụng request sync có key hợp lệ, cùng app session/process.
Không có cam kết survive restart/multi-worker. Password-only reauth không tự
retry. Progress là mốc giai đoạn 0/25/75/100, không phải % số dòng đã crawl.
