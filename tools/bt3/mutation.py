"""Apply one valid swallowed-exception mutant ONLY in a clean detached BT3 worktree."""

import argparse
import difflib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from tools.bt3.run_evidence import EVIDENCE


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("worktree", type=Path)
    args = parser.parse_args()
    target = args.worktree.resolve()
    git = ["git", "-c", f"safe.directory={target.as_posix()}"]

    def query(*parts):
        return subprocess.check_output([*git, *parts], cwd=target, text=True).strip()

    if query("branch", "--show-current") or query("status", "--porcelain=v1"):
        parser.error("Mutation requires a clean detached worktree; never the submission branch")
    path = target / "app/api/routes.py"
    original = path.read_text(encoding="utf-8")
    head, rest = original.split("def course_search(", 1)
    region, tail = rest.split('@router.get("/profiles"', 1)
    marker = "    except ValueError as exc:\n        _raise_domain_error(exc)\n"
    if region.count(marker) != 1:
        parser.error("Production boundary changed; review mutant placement manually")
    changed = head + "def course_search(" + region.replace(marker, marker +
        "    except Exception:\n"
        "        return CourseSearchPage(program_id=program_id, items=[], total=0,\n"
        "                                page=page, page_size=page_size)\n") + '@router.get("/profiles"' + tail
    path.write_text(changed, encoding="utf-8")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "mutation.patch").write_text("".join(difflib.unified_diff(
        original.splitlines(keepends=True), changed.splitlines(keepends=True),
        fromfile="a/app/api/routes.py", tofile="b/app/api/routes.py")), encoding="utf-8")
    compile(changed, str(path), "exec")  # Valid Python; not an import/syntax-error mutant.
    command = [sys.executable, "-m", "pytest", "-q",
               "tests/integrations/test_course_search_contract.py", "--tb=short", "-p", "no:cacheprovider"]
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(command, cwd=target, env=env, capture_output=True,
                            text=True, encoding="utf-8", check=False)
    (EVIDENCE / "mutation.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    record = {"started_utc": datetime.now(timezone.utc).isoformat(),
              "base_commit": query("rev-parse", "HEAD"), "branch": "detached",
              "command": command, "exit_code": result.returncode,
              "working_tree": query("status", "--porcelain=v1"),
              "compile_valid": True,
              "expected_detection": "503/500 became 200 only in the added /courses/search boundary",
              "mutation_killed": result.returncode == 1 and "3 failed, 39 passed" in result.stdout}
    (EVIDENCE / "mutation.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(result.stdout)
    print(json.dumps(record, indent=2))
    return 0 if record["mutation_killed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
