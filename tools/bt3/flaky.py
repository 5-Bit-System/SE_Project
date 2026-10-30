"""Repeat contracts in fresh processes with different hash seeds and fixture reset."""

import json
import os
import subprocess
import sys

from tools.bt3.run_evidence import EVIDENCE, ROOT


def main() -> int:
    results, logs = [], []
    for seed in (1, 17, 231953):
        for repeat in (1, 2):
            command = [sys.executable, "-m", "pytest", "-q",
                       "tests/integrations/test_course_search_contract.py",
                       "tests/catalogs/test_course_search.py", "--tb=short", "-p", "no:cacheprovider"]
            env = {**os.environ, "PYTHONHASHSEED": str(seed), "PYTHONUTF8": "1",
                   "PYTHONIOENCODING": "utf-8"}
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                    text=True, encoding="utf-8", check=False)
            results.append({"seed": seed, "repeat": repeat, "exit_code": result.returncode,
                            "command": command})
            logs.append(f"seed={seed}, repeat={repeat}, exit={result.returncode}\n" +
                        result.stdout + result.stderr)
            print(f"seed={seed}, repeat={repeat}, exit={result.returncode}", flush=True)
    (EVIDENCE / "flaky-runs.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE / "flaky-runs.log").write_text("\n".join(logs), encoding="utf-8")
    return int(any(row["exit_code"] for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
