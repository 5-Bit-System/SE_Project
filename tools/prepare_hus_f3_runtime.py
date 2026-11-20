"""Prepare/verify detailed F3 portable release or stage an explicit preview root."""

import argparse
import tempfile
from pathlib import Path

from app.hus.corpus import verify_artifacts
from app.hus.f3_runtime_release import RELEASE_ID, build_release, stage_preview


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify", "preview"))
    parser.add_argument("--release", type=Path, default=Path("data/hus/rag/releases") / RELEASE_ID)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "preview":
            stage_preview(args.release, args.out)
        elif args.command == "verify":
            verify_artifacts(args.out, build_release())
        else:
            out = args.out.resolve()
            if out.exists():
                raise ValueError("Output exists; choose a new release directory")
            protected = [
                Path("data/hus/qa"),
                Path("data/hus/review"),
                Path("data/hus/evaluation"),
                Path("data/hus/rag/releases/hus-data-20261031-v3"),
            ]
            if any(
                out.is_relative_to(p.resolve()) or p.resolve().is_relative_to(out)
                for p in protected
            ):
                raise ValueError("Output overlaps protected inputs/history")
            output = build_release()
            out.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".hus-v4-", dir=out.parent) as temporary:
                staged = Path(temporary) / "release"
                staged.mkdir()
                for name, raw in output.items():
                    target = staged / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
                staged.rename(out)
        print("F3 portable release " + args.command + ": OK")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, "F3 runtime preparation failed: " + str(error) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
