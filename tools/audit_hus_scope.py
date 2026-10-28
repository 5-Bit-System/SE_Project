"""Build/verify a scoped HUS data audit through the existing corpus review gate."""

import argparse
from pathlib import Path
import tempfile

from app.hus.corpus import verify_artifacts
from app.hus.scope_audit import audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--source-root", type=Path, default=Path("data/hus"))
    parser.add_argument("--config", type=Path, default=Path("data/hus/qa/20261028/contract/build_config.json"))
    parser.add_argument("--catalogs", type=Path, default=Path("data/curricula"))
    parser.add_argument("--experimental", type=Path,
                        default=Path("data/hus/qa/20261028/experimental/f3_inferred.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        out = args.out.resolve()
        for protected in (args.source_root / "processed", args.source_root / "raw", args.catalogs,
                          args.config.parent):
            protected = protected.resolve()
            if out == protected or out.is_relative_to(protected) or protected.is_relative_to(out):
                raise ValueError("Output overlaps protected source/contract inputs")
        outputs = audit(args.source_root, args.config, args.catalogs, args.experimental)
        if args.command == "verify":
            verify_artifacts(out, outputs)
            print(f"Verified byte-identical scope audit: {len(outputs)} files")
        else:
            if out.exists():
                raise ValueError("Output exists; choose a new directory")
            out.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".hus-audit-", dir=out.parent) as temp:
                staged = Path(temp) / "audit"
                staged.mkdir()
                for name, data in outputs.items():
                    destination = staged / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(data)
                staged.rename(out)
            print(f"Created scope audit: {out}")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Scope audit failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
