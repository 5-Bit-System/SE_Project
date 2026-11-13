"""Measure line-by-line statement coverage for VT-099 git diff dynamically.

Executes real git diff against baseline commit 1205fa94eadfaa6a52721e85cdab8a7dea9cfa11
and inspects coverage.py execution data to verify that 100% of statements introduced
by VT-099 in target files were executed during test suite runs.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE = "1205fa94eadfaa6a52721e85cdab8a7dea9cfa11"
TARGET_FILES = [
    "app/api/admin.py",
    "app/auth/repository.py",
    "app/crawler/document_review_service.py",
]


def get_git_diff_added_lines(baseline: str, target_files: list[str]) -> dict[str, list[int]]:
    """Parse git diff -U0 to find exact line numbers added or modified in HEAD."""
    cmd = ["git", "diff", "-U0", f"{baseline}..HEAD", "--"] + target_files
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    diff_lines: dict[str, list[int]] = {f: [] for f in target_files}
    current_file = None

    for line in res.stdout.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("@@ ") and current_file in diff_lines:
            m = re.search(r"\+([0-9]+)(?:,([0-9]+))?", line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) is not None else 1
                diff_lines[current_file].extend(range(start, start + count))

    return diff_lines


def load_coverage_data(target_files: list[str]) -> dict[str, dict]:
    """Generate and load coverage.json from the active .coverage database."""
    temp_json = REPO_ROOT / ".tmp_cov_report.json"
    cmd = [sys.executable, "-m", "coverage", "json", "-o", str(temp_json)]
    subprocess.run(cmd, cwd=REPO_ROOT, check=True, capture_output=True)

    try:
        data = json.loads(temp_json.read_text(encoding="utf-8"))
    finally:
        if temp_json.exists():
            temp_json.unlink()

    cov_files = {}
    for path, fdata in data.get("files", {}).items():
        norm_path = path.replace("\\\\", "/").replace("\\", "/")
        for target in target_files:
            if norm_path.endswith(target):
                cov_files[target] = fdata

    return cov_files


def main():
    print("=" * 80)
    print("VT-099: DYNAMIC DIFF STATEMENT COVERAGE VERIFICATION")
    print(f"Baseline Commit: {BASELINE} | Target: HEAD")
    print("=" * 80)

    try:
        diff_lines = get_git_diff_added_lines(BASELINE, TARGET_FILES)
    except Exception as exc:
        print(f"Error executing git diff: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        cov_data = load_coverage_data(TARGET_FILES)
    except Exception as exc:
        print(f"Error loading coverage data: {exc}", file=sys.stderr)
        sys.exit(1)

    total_diff_stmts = 0
    total_executed = 0
    total_missed = 0

    for target in TARGET_FILES:
        target_path = REPO_ROOT / target
        if not target_path.exists():
            print(f"Warning: File {target} not found on disk.")
            continue

        file_lines = target_path.read_text(encoding="utf-8").splitlines()
        cdata = cov_data.get(target, {})
        exec_lines = set(cdata.get("executed_lines", []))
        miss_lines = set(cdata.get("missing_lines", []))
        all_stmts = exec_lines | miss_lines

        added_lines = diff_lines.get(target, [])
        tracked_stmts = [l for l in added_lines if l in all_stmts]

        file_exec = [l for l in tracked_stmts if l in exec_lines]
        file_miss = [l for l in tracked_stmts if l in miss_lines]

        pct = (len(file_exec) / len(tracked_stmts) * 100) if tracked_stmts else 0.0

        print(f"\nTarget File: {target}")
        print(f"Added lines in git diff: {len(added_lines)} | Tracked statements: {len(tracked_stmts)}")
        print("-" * 80)

        for l in tracked_stmts:
            code = file_lines[l - 1].strip() if l <= len(file_lines) else ""
            status = "EXECUTED (1)" if l in exec_lines else "MISSED   (0)"
            print(f"  Line {l:<4} | {status} | {code[:60]}")

        print(f"-> Statement Coverage for {target}: {len(file_exec)}/{len(tracked_stmts)} ({pct:.1f}%)")

        total_diff_stmts += len(tracked_stmts)
        total_executed += len(file_exec)
        total_missed += len(file_miss)

    print("\n" + "=" * 80)
    total_pct = (total_executed / total_diff_stmts * 100) if total_diff_stmts else 0.0
    print(f"TOTAL DIFF STATEMENT COVERAGE: {total_executed}/{total_diff_stmts} statements ({total_pct:.1f}%)")
    print(f"Total Missed Statements: {total_missed}")

    if total_diff_stmts > 0 and total_missed == 0:
        print("Verdict: PASSED (100.0% of VT-099 diff statements executed by test suite)")
        print("=" * 80)
        sys.exit(0)
    else:
        print("Verdict: FAILED (Uncovered diff statements detected)")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
