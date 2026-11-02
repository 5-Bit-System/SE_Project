"""Stdlib trace line coverage for the focused slice; excludes timed load tests."""

import tempfile
import trace
from pathlib import Path

import pytest


def main():
    root = Path(__file__).resolve().parents[1]
    tracer = trace.Trace(count=True, trace=False)
    exit_code = tracer.runfunc(pytest.main, [
        "-q", "tests/importing/test_batch.py", "tests/importing/test_transcript_import.py",
    ])
    results = tracer.results()
    targets = {str(root / "app/importing" / name) for name in ("batch.py", "transcript.py")}
    results.counts = {key: value for key, value in results.counts.items() if key[0] in targets}
    directory = tempfile.mkdtemp(prefix="vt100-line-coverage-")
    results.write_results(show_missing=True, summary=True, coverdir=directory)
    print("Branch coverage: not measured by stdlib trace. Load timing excluded.")
    print(f"Annotated files: {directory}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
