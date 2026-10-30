"""Run a command and retain its actual exit status, output and Git context."""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/assignments/BT3_23001953_VT-101/evidence"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command or Path(args.label).name != args.label:
        parser.error("Supply a simple label and -- command ...")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    record = {
        "label": args.label, "command": command,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "head": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "working_tree_before": git("status", "--porcelain=v1"),
    }
    start = perf_counter()
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", check=False)
    record.update(exit_code=result.returncode, duration_seconds=round(perf_counter() - start, 4),
                  finished_utc=datetime.now(timezone.utc).isoformat(),
                  working_tree_after=git("status", "--porcelain=v1"))
    (EVIDENCE / f"{args.label}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    (EVIDENCE / f"{args.label}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    print(f"Evidence: {args.label}; exit={result.returncode}; seconds={record['duration_seconds']}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
