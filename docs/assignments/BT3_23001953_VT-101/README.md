# BT cá nhân 3 — Nguyễn Công Việt — 23001953 — VT-101

SE2026-T25 · Nhóm trưởng · AI-07 – Explainable Course Recommender.
Quy trình: **Spec → Test → AI-assisted Change → Verify → Review**.
Chưa tạo PDF. Đây là tài liệu kỹ thuật và evidence để sinh viên tự review.

**Kết quả:** search API và contract/regression tests passed; mutant bị phát hiện.
**Mục tiêu p95≤3s chưa đạt ổn định:** một trong ba lượt vượt ngưỡng ở cả cấu hình
mặc định và thử 8 thread. Không diễn giải các lượt nhanh thành đạt toàn bộ NFC-01.

## Phạm vi, baseline và version

- Repository: https://github.com/5-Bit-System/SE_Project.
- Baseline main đã đối chiếu GitHub: `7b387a394e334e217733a571ee76a573157a24f2`.
- Branch: `bt3/23001953-VT-101-search-contract`.
- Worktree làm bài: `D:/SE_Project/backups/bt3_23001953`; không mang thay đổi cũ
  của root main sang bài. Root integrity được kiểm riêng bằng hash/status/HEAD.
- Test-first checkpoint: `a5aab95c9d8453093621453b25f5807e584e15a3`
  (**cố ý đỏ**, chưa có endpoint). Implementation đúng:
  `cb3b35d944364e74fec65af4b299a79fcb90df36`.
- Commit harness/docs tiếp theo được tra bằng `git log --oneline` và
  [PUBLICATION.md](PUBLICATION.md). Bản đo app là cb3b35d, working-tree context
  khi đo có trong JSON. Harness được công bố sau đó, không sửa số liệu.
- [Branch GitHub](https://github.com/5-Bit-System/SE_Project/tree/bt3/23001953-VT-101-search-contract)
  chỉ được coi đã phát hành khi PUBLICATION.md ghi verified push; không có merge.

Thêm GET `/courses/search` với q/block/requirement_type/sort/page/page_size.
Giữ nguyên GET `/courses` trả array và error semantics. Ba file production:
routes.py, schemas/catalog.py, services/course_search_service.py. Không thay
Course model, DB schema, nguồn học vụ, auth, VNU, RAG hoặc active UI.

## Đọc theo thứ tự

1. [SPEC.md](SPEC.md): contract hiện tại/mới, 5 AC, invariants và giới hạn.
2. [PLAN.md](PLAN.md): revised plan trước code, 3 quyết định sửa/bác bỏ có evidence.
3. [TEST_STRATEGY.md](TEST_STRATEGY.md): risk-based strategy, 18 test case groups.
4. [PATCH_REVIEW.md](PATCH_REVIEW.md), [REPORT.md](REPORT.md): RED/GREEN, mutation,
   coverage, flaky, performance và kết luận đúng phạm vi.
5. [TRACEABILITY.md](TRACEABILITY.md): AC/risk → tests → commit → evidence.
6. [AI_USAGE_LOG.md](AI_USAGE_LOG.md), [REFLECTION_DRAFT.md](REFLECTION_DRAFT.md).
7. [HANDOFF_FOR_PDF.md](HANDOFF_FOR_PDF.md): rubric map, bố cục ≤8 trang, việc còn thiếu.

## Môi trường và tái lập an toàn

Đã chạy Windows build26300 AMD64, AMD Family25 Model116, 12 logical CPU;
Python3.11.9, pytest9.1.1, FastAPI0.143.0, Pydantic2.14.1, HTTPX0.28.1,
Uvicorn0.54.0, Ruff0.17.0, coverage.py7.17.0. Chrome version thực tế trong
`evidence/browser-results.json`; Playwright1.64.1. Không có dependency runtime mới.
Coverage là dev-only tùy chọn tại `tools/bt3/requirements.txt`.

Làm trong clean worktree không có cấu hình cá nhân. Không copy config, khóa,
cookie hoặc DB dump từ root. Không chạy migration/publisher/load trên DB nhóm.
Harness từ chối bootstrap nếu có local config; tự sinh 4 catalog giả trong temp,
240 môn program được đo +3 môn ở 3 catalog khác. Unit/API có 8 môn/foreign1.
Không cần tự chuẩn bị dữ liệu hoặc VNU account. Không mở app đang dùng port8000.

PowerShell, đứng ở root **worktree BT3**. Khi dùng venv sẵn trong workspace gốc:

```powershell
$py = 'D:/SE_Project/.venv/Scripts/python.exe'
& $py -m pytest -q tests/integrations/test_course_search_contract.py tests/catalogs/test_course_search.py
& $py -m pytest -q tests -m "not postgres and not hus_postgres" --full-catalog-root docs/acceptance/hus_2022
& $py -m ruff check . --no-cache
& $py -X utf8 tools/build_catalogs.py --check --root tests/support/fixtures/catalogs
& $py -X utf8 tools/build_catalogs.py --check
node tests/frontend/check_analytics.mjs
```

Fresh clone/worktree khác: tạo `.venv`, cài `requirements-dev.txt` với
`-c requirements-lock.txt`, rồi đổi `$py` sang Python của venv đó. Browser smoke
tùy chọn cần `requirements-portal.txt`/Chrome theo docs/LOCAL_SETUP.md; unit/API,
load HTTP không cần Playwright. Lệnh dùng `-m tools.bt3.run_evidence <label> -- ...`
lưu stdout/stderr, exit code, timestamp, commit và trạng thái Git. Các lệnh tái
lập cùng label ghi đè evidence; nên chạy ở worktree tái lập khác hoặc label mới.

### Test-first RED và mutation

```powershell
git worktree add --detach D:/SE_Project/backups/bt3-red-repeat a5aab95c9d8453093621453b25f5807e584e15a3
# Trong worktree RED, chạy pytest test_course_search_contract.py: expected exit1, 37failed/5passed.
git worktree add --detach D:/SE_Project/backups/bt3-mutant-repeat cb3b35d944364e74fec65af4b299a79fcb90df36
# Trở về worktree BT3 hiện tại:
& $py -m tools.bt3.mutation D:/SE_Project/backups/bt3-mutant-repeat
```

Mutation runner chỉ chấp nhận clean detached worktree. Pytest mutant expected
exit1 (3failed39passed); runner expected exit0 khi đúng ba failure được phát hiện.
Patch bằng chứng `evidence/mutation.patch` không được app import/tự thực thi.
Đừng apply nó vào branch nộp. Branch đúng expected46passed.

### Coverage và flaky

```powershell
& $py -m pip install --target D:/SE_Project/backups/bt3_devtools -r tools/bt3/requirements.txt
$env:PYTHONPATH = 'D:/SE_Project/backups/bt3_devtools'
& $py -m coverage run --branch --source=app.services.course_search_service,app.api.routes,app.schemas.catalog -m pytest -q tests/integrations/test_course_search_contract.py tests/catalogs/test_course_search.py
& $py -m coverage report -m
& $py -m coverage json -o docs/assignments/BT3_23001953_VT-101/evidence/coverage-repeat.json
& $py -m tools.bt3.flaky
```

Expected: service12/12 lines,4/4branches; model14/14lines;6 process runs×46tests.
Không coi coverage của service là coverage toàn app.

### HTTP performance và browser

```powershell
& $py -m tools.bt3.run_evidence performance-repeat -- $py -m tools.bt3.http_experiment --label performance-repeat
& $py -m tools.bt3.run_evidence tuned-repeat -- $py -m tools.bt3.http_experiment --thread-tokens 8 --label tuned-repeat
& $py -m tools.bt3.run_evidence profile-repeat -- $py -m tools.bt3.profile_search
& $py -m tools.bt3.run_evidence browser-repeat -- $py -m tools.bt3.browser_smoke
& $py -m tools.bt3.final_review
```

Benchmark khoảng1–2 phút/cấu hình; 3 server mới, mỗi server50warmup+2000measured,
100 worker đợi Event barrier, tối đa100 connection, peak100in-flight. 10 query
cases có literal/closed-form oracles, gồm legacy array request. Mỗi response phải
đúng contract; latency gồm body decode/check. Percentile nearest rank. Default
test run có thể exit1 khi SLO không đạt — đó là kết quả thật, không lỗi test setup.
CSV và JSON không chứa hồ sơ cá nhân. Wrapper giữ nguyên router/service/repository
và response/error handling, thay riêng lifecycle VNU startup bằng JSON readiness,
thêm marker/shutdown **chỉ ở test server** để không để lại process. Không dùng
PostgreSQL thật, không thay cấu hình runtime nhóm và không chứng minh production SLO.
