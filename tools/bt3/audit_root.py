"""Hash only pre-existing dirty paths, without reading credential/config contents into logs."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def snapshot(root: Path) -> dict:
    # Per-command trust for the explicitly selected local root, never global configuration.
    command = ["git", "-c", f"safe.directory={root.as_posix()}"]
    status = subprocess.check_output([*command, "status", "--porcelain=v1", "-z"], cwd=root)
    files = {}
    for entry in status.decode("utf-8").split("\0"):
        if not entry:
            continue
        path = root / entry[3:]
        candidates = path.rglob("*") if path.is_dir() else [path]
        for candidate in candidates:
            if candidate.is_file():
                files[candidate.relative_to(root).as_posix()] = hashlib.sha256(
                    candidate.read_bytes()).hexdigest()
    return {
        "head": subprocess.check_output([*command, "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "branch": subprocess.check_output([*command, "branch", "--show-current"], cwd=root, text=True).strip(),
        "status": status.decode("utf-8").replace("\0", "\n"),
        "dirty_file_sha256": files,
        "staged_names": subprocess.check_output(
            [*command, "diff", "--cached", "--name-only"], cwd=root, text=True).strip(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    result = snapshot(args.root.resolve())
    if args.compare:
        result["matches_before"] = result == json.loads(args.compare.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print({"files_hashed": len(result["dirty_file_sha256"]),
           "matches_before": result.get("matches_before"), "head": result["head"]})
    if args.compare and not result["matches_before"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
