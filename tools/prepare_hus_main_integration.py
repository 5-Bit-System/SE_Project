"""Export/replay the P0-4 overlay against pinned main without replacing crawldata.

Export: python -m tools.prepare_hus_main_integration --export backups/hus_integration/p04-main
Replay: python -m tools.prepare_hus_main_integration --target backups/hus_integration/p04-replay
Creates a new detached worktree; never modifies an existing checkout or creates a commit.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "integration/hus-rag-p04"
BASE = "5239b7333a8f8cdf0f919e6b0505af0def99fe23"
RUNTIME = [f"app/hus/{name}.py" for name in (
    "answering", "citations", "citation_assets", "rag_loader", "retrieval", "portable_adapter",
    "source_response", "data_release", "release_reader", "release_validation", "release_text")]
RUNTIME += ["app/schemas/hus.py", "app/services/hus_service.py"]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-c", f"safe.directory={repo.as_posix()}", *args], cwd=repo)


def within(root: Path, name: str) -> Path:
    if (not name or "\\" in name or ":" in name or Path(name).is_absolute()
            or ".." in Path(name).parts or ".git" in Path(name).parts):
        raise ValueError("Unsafe integration path")
    result = (root / name).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError("Integration path escapes workspace")
    return result


def normalized(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def input_sha(name: str, raw: bytes) -> str:
    return sha(normalized(raw) if name.startswith("app/") else raw)


def export(worktree: Path, bundle: Path = BUNDLE) -> dict:
    worktree = worktree.resolve()
    if not worktree.is_relative_to(ROOT) or git(worktree, "rev-parse", "HEAD").decode().strip() != BASE:
        raise ValueError("Export requires the isolated worktree at pinned main")
    copies = list(RUNTIME) + ["data/hus/rag/CURRENT.json", "data/hus/rag/PORTABLE_IMPORT.json"]
    for folder in ("data/hus/rag/releases/hus-data-20261031-v3", "data/hus/citation_assets"):
        copies += [p.relative_to(ROOT).as_posix() for p in (ROOT / folder).rglob("*") if p.is_file()]
    source_hashes = {name: input_sha(name, within(ROOT, name).read_bytes()) for name in sorted(copies)}
    changed = git(worktree, "diff", "--name-only", "-z", BASE).decode().split("\0")
    added = git(worktree, "ls-files", "--others", "--exclude-standard", "-z").decode().split("\0")
    paths = sorted(set(changed + added + copies) - {""})
    patch, outputs = [], {}
    for name in paths:
        file = within(worktree, name)
        if not file.is_file():
            raise ValueError("P0-4 overlay does not remove existing main files")
        after = file.read_bytes()
        if name in copies:
            before = within(ROOT, name).read_bytes()
            if name.startswith("data/"):
                if after != before:
                    raise ValueError(f"Pinned data changed: {name}")
                continue
        else:
            exists = subprocess.run(["git", "cat-file", "-e", f"{BASE}:{name}"], cwd=worktree,
                                    capture_output=True).returncode == 0
            before = git(worktree, "show", f"{BASE}:{name}") if exists else None
        outputs[name] = sha(normalized(after))
        if before is not None and normalized(before) == normalized(after):
            continue
        old = normalized(before).decode("utf-8").splitlines(keepends=True) if before is not None else []
        new = normalized(after).decode("utf-8").splitlines(keepends=True)
        patch.append(f"diff --git a/{name} b/{name}\n")
        if before is None:
            patch.append("new file mode 100644\n")
        patch.extend(difflib.unified_diff(old, new, fromfile=f"a/{name}" if before is not None else "/dev/null",
                                          tofile=f"b/{name}"))
    raw_patch = "".join(patch).encode("utf-8")
    manifest = {"schema_version": "1.0", "main_base": BASE, "source_head": git(ROOT, "rev-parse", "HEAD").decode().strip(),
                "selected_release": json.loads((ROOT / "data/hus/rag/CURRENT.json").read_bytes()),
                "patch": "main.patch", "patch_sha256": sha(raw_patch), "copy_from_crawldata": source_hashes,
                "source_hash_encoding": "app: utf8-lf; data: exact bytes",
                "normalized_output_sha256": outputs, "academic_review_added": False,
                "requires_feature_branch_and_pr_for_main": True}
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "main.patch").write_bytes(raw_patch)
    (bundle / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return {"copied_inputs": len(copies), "source_outputs": len(outputs), "patch_bytes": len(raw_patch)}


def replay(target: Path, bundle: Path = BUNDLE) -> dict:
    target = target.resolve()
    if not target.is_relative_to(ROOT) or target.exists():
        raise ValueError("Choose a new worktree directory inside this repository")
    manifest = json.loads((bundle / "manifest.json").read_bytes())
    base = manifest["main_base"]
    if base != BASE or not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ValueError("Unexpected main base")
    patch = within(bundle, manifest["patch"])
    if sha(patch.read_bytes()) != manifest["patch_sha256"]:
        raise ValueError("Integration patch checksum differs")
    # Complete all input checks before creating/writing the new worktree.
    for name, digest in manifest["copy_from_crawldata"].items():
        if input_sha(name, within(ROOT, name).read_bytes()) != digest:
            raise ValueError(f"Crawldata input differs from accepted snapshot: {name}")
    if git(ROOT, "rev-parse", "--verify", base).decode().strip() != base:
        raise ValueError("Fetch the pinned main commit before replay")
    git(ROOT, "worktree", "add", "--quiet", "--detach", str(target), base)
    for name in manifest["copy_from_crawldata"]:
        raw = within(ROOT, name).read_bytes()
        dest = within(target, name)
        if dest.exists() and dest.read_bytes() != raw:
            raise ValueError(f"Pinned main has a different file: {name}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(normalized(raw) if name.startswith("app/") else raw)
    git(target, "apply", "--check", str(patch))
    git(target, "apply", str(patch))
    for name, digest in manifest["normalized_output_sha256"].items():
        if sha(normalized(within(target, name).read_bytes())) != digest:
            raise ValueError(f"Replayed source differs: {name}")
    for name, digest in manifest["copy_from_crawldata"].items():
        if name.startswith("data/") and sha(within(target, name).read_bytes()) != digest:
            raise ValueError(f"Replayed data differs: {name}")
    return {"main_base": base, "target": str(target), "status": "verified", "committed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--export", type=Path)
    action.add_argument("--target", type=Path)
    parser.add_argument("--bundle", type=Path, default=BUNDLE, help="Review bundle inside this repository")
    args = parser.parse_args(argv)
    bundle = args.bundle.resolve()
    if not bundle.is_relative_to(ROOT) or ".git" in bundle.parts:
        parser.error("Bundle must be inside this repository")
    print(json.dumps(export(args.export, bundle) if args.export else replay(args.target, bundle), ensure_ascii=False))


if __name__ == "__main__":
    main()
