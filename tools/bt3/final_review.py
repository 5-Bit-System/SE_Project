"""Review BT3-only changed paths, legacy AST, mutant absence and common secret patterns."""

import ast
import json
import re
import subprocess

from tools.bt3.run_evidence import EVIDENCE, ROOT, git

BASE = "7b387a394e334e217733a571ee76a573157a24f2"


def main() -> int:
    changed = set(git("diff", BASE, "--name-only").splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard").splitlines())
    production = {"app/api/routes.py", "app/schemas/catalog.py", "app/services/course_search_service.py"}
    allowed = production | {"README.md", ".gitattributes", "tests/support/search_data.py",
                            "tests/catalogs/test_course_search.py",
                            "tests/integrations/test_course_search_contract.py"}
    unexpected = sorted(path for path in changed if path not in allowed and not path.startswith(
        ("tools/bt3/", "docs/assignments/BT3_23001953_VT-101/")))
    before = ast.parse(subprocess.check_output(
        ["git", "show", f"{BASE}:app/api/routes.py"], cwd=ROOT, text=True, encoding="utf-8"))
    after = ast.parse((ROOT / "app/api/routes.py").read_text(encoding="utf-8"))

    def function(tree, name):
        return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)

    unchanged = ast.dump(function(before, "courses")) == ast.dump(function(after, "courses"))
    catch_all = any(isinstance(node, ast.ExceptHandler) and (
        node.type is None or isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"}
    ) for node in ast.walk(function(after, "course_search")))
    patterns = [r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
                r"gh[pousr]_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{40,}",
                r"AKIA[0-9A-Z]{16}", r"https?://[^\s/@:]+:[^\s/@]+@"]
    findings = []
    for name in sorted(changed):
        path = ROOT / name
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            if any(re.search(pattern, content) for pattern in patterns):
                findings.append(name)  # Never print matched credential contents.
    whitespace = subprocess.run(["git", "diff", "--check", BASE], cwd=ROOT,
                                capture_output=True, text=True, check=False)
    result = dict(baseline=BASE, head=git("rev-parse", "HEAD"), changed_paths=sorted(changed),
                  unexpected_paths=unexpected, legacy_courses_ast_unchanged=unchanged,
                  production_catch_all_present=catch_all, common_secret_pattern_findings=findings,
                  whitespace_exit_code=whitespace.returncode,
                  scanner_limit="Common patterns on BT3 changes only; not proof that every possible secret is detectable")
    result["passed"] = not (unexpected or catch_all or findings or whitespace.returncode) and unchanged
    (EVIDENCE / "scope-review-results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
