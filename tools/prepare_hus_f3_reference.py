"""Build or verify an isolated generated F3 reference corpus; no HTTP, LLM or database."""

import argparse
from pathlib import Path
import tempfile

from app.hus.corpus import verify_artifacts
from app.hus.f3_reference import build_reference

DEFAULT_ROOT = Path("data/hus/qa/20261028/f3_reference")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--inputs", type=Path, default=DEFAULT_ROOT / "inputs")
    parser.add_argument("--candidate-audit", type=Path, default=Path("data/hus/qa/20261028/audit"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        out = args.out.resolve()
        protected = (args.inputs, args.candidate_audit, Path("data/hus/corpus"),
                     Path("data/hus/processed"), Path("data/hus/raw"), Path("data/curricula"))
        if any(out == p.resolve() or out.is_relative_to(p.resolve()) or p.resolve().is_relative_to(out)
               for p in protected):
            raise ValueError("Output overlaps protected inputs or official/source data")
        output = build_reference(args.inputs, args.candidate_audit)
        if args.command == "verify":
            verify_artifacts(out, output)
            print(f"Verified byte-identical F3 reference: {len(output)} files")
        else:
            if out.exists():
                raise ValueError("Output exists; choose a new release directory")
            out.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".f3-reference-", dir=out.parent) as temp:
                staged = Path(temp) / "release"
                staged.mkdir()
                for name, raw in output.items():
                    (staged / name).write_bytes(raw)
                staged.rename(out)
            print(f"Created generated F3 reference: {out}")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"F3 reference preparation failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
