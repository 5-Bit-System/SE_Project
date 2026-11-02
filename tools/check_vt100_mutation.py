"""Run the VT-100 Boolean-negation mutation, always restoring exact source bytes."""

import hashlib
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / "app/importing/batch.py"
    original = source.read_bytes()
    rule = b"BatchStatus.PARTIAL if imported and rejected"
    mutation = b"BatchStatus.PARTIAL if not (imported and rejected)"
    if original.count(rule) != 1:
        raise RuntimeError("Expected exactly one original rule; refusing mutation")
    command = [
        sys.executable, "-m", "pytest", "-q",
        "tests/importing/test_batch.py::test_all_valid_rows_reach_handler_once_and_complete",
        "tests/importing/test_batch.py::test_all_record_errors_produce_failed_batch_summary",
        "tests/importing/test_batch.py::test_middle_row_failure_does_not_lose_valid_rows_before_or_after",
    ]
    try:
        source.write_bytes(original.replace(rule, mutation))
        result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    finally:
        source.write_bytes(original)
    restored = source.read_bytes() == original
    killed = result.returncode == 1 and "3 failed" in result.stdout and restored
    log = (
        "Mutation: bool(imported and rejected) -> not (imported and rejected)\n"
        f"Command: {' '.join(command)}\n"
        f"Original SHA256: {hashlib.sha256(original).hexdigest()}\n"
        f"Restored exact source bytes: {restored}\n"
        f"Observed pytest exit: {result.returncode}; mutation killed: {killed}\n\n"
        + result.stdout + result.stderr
    )
    (root / "deliverables/evidence/mutation-boolean-negation.txt").write_text(log)
    print(log)
    return 0 if killed else 1


if __name__ == "__main__":
    raise SystemExit(main())
