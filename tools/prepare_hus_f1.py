"""Build/verify program F1 evidence from whole-document reviewed crawl sources, offline."""

import argparse
from pathlib import Path
import tempfile

from app.hus.corpus import verify_artifacts
from app.hus.f1_corpus import build_f1

ROOT = Path("data/hus/qa/20261028/f1_expanded")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--source-root", type=Path, default=Path("data/hus"))
    parser.add_argument("--config", type=Path, default=ROOT / "contract/build_config.json")
    parser.add_argument("--selections", type=Path, default=ROOT / "contract/selections.json")
    parser.add_argument("--markdown-reviews", type=Path,
                        help="Explicit user-authorized F1-only Markdown decisions; never marks raw originals verified")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        out = args.out.resolve()
        protected = (args.source_root / "raw", args.source_root / "processed", args.config.parent,
                     args.selections.parent, Path("data/hus/corpus"), Path("data/curricula"))
        if args.markdown_reviews:
            protected += (args.markdown_reviews.parent,)
        if any(out == p.resolve() or out.is_relative_to(p.resolve()) or p.resolve().is_relative_to(out)
               for p in protected):
            raise ValueError("Output overlaps protected source/contract inputs")
        if args.markdown_reviews:
            from app.hus.f1_markdown_review import build_f1_with_markdown

            output = build_f1_with_markdown(args.source_root, args.config, args.selections, args.markdown_reviews)
        else:
            output = build_f1(args.source_root, args.config, args.selections)
        if args.command == "verify":
            verify_artifacts(out, output)
            print(f"Verified byte-identical F1 release: {len(output)} files")
        else:
            if out.exists():
                raise ValueError("Output exists; choose a new directory")
            out.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".f1-corpus-", dir=out.parent) as temp:
                staged = Path(temp) / "release"
                staged.mkdir()
                for name, data in output.items():
                    (staged / name).write_bytes(data)
                staged.rename(out)
            print(f"Created source-grounded F1 release: {out}")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"F1 preparation failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
