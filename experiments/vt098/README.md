# VT-098 — chạy test

**Dương Văn Tài — 23001925 — SE2026-T25 — AI-07.**

Baseline: `7b387a394e334e217733a571ee76a573157a24f2`.
Nhánh nộp: [vt098/23001925-idempotency](https://github.com/5-Bit-System/SE_Project/tree/vt098/23001925-idempotency).
**Không merge nếu nhóm chưa review; không merge nhánh mutant.**

## Chạy từ root repository, Python 3.11

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r experiments/vt098/requirements.txt
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s experiments/vt098 -p "test_*.py" -v
```

Kỳ vọng: **19 test methods OK**, gồm 8 pairwise subcases. Không cần Docker,
VNU, LLM, API key hoặc database production. Dependency trực tiếp là Pydantic;
SQLite/unittest thuộc Python. Ruff là style check tùy chọn, không cần để chạy test.

## Code, patch và evidence

- Test: [test_harness.py](test_harness.py); runtime: [harness.py](harness.py).
- [Patch `91b2030`](https://github.com/5-Bit-System/SE_Project/commit/91b20308dc86daa8b1067db3e558aba350635e61): 27 dòng thêm, 8 dòng bỏ trong runtime.
- [Traceability](ENGINEERING_EVIDENCE.md), [AI Usage Log](AI_USAGE.md),
  [reflection 286 từ](REFLECTION.md), [kết quả quality/load](QUALITY_REPORT.md).
- [Hướng dẫn đầy đủ](REPRODUCTION.md): tái hiện red, mutation ở worktree riêng,
  coverage, flaky review và tải 150 tác vụ. [Rà soát cuối](FINAL_REVIEW.md).

Đây là **executable harness SQLite cho bản nháp học kỳ rỗng**; schema request
được nạp từ source thật. Chưa nối API/auth/CSRF/PostgreSQL/browser production.
Kết quả timing chỉ áp dụng cho harness. Các TC production còn thiếu được đánh
dấu trong traceability, không nhận là đã pass.
