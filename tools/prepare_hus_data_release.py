"""Build, validate or reproduce the portable HUS data handoff, without network/DB."""
from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

from app.hus.data_release import build_release
from app.hus.release_validation import validate_release


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'validate', 'reproduce'))
    parser.add_argument('--repo-root', type=Path, default=Path('.'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    repo, out = args.repo_root.resolve(), args.out.resolve()
    protected = [repo / p for p in ('data/hus/processed', 'data/hus/raw', 'data/hus/corpus',
                                    'data/hus/qa', 'data/hus/rag/inputs', 'docs/pdf')]
    try:
        if any(out == p or out.is_relative_to(p) or p.is_relative_to(out) for p in protected):
            raise ValueError('Output overlaps source inputs')
        if args.command == 'validate':
            print(validate_release(out))
            return 0
        artifacts = build_release(repo)
        if args.command == 'reproduce':
            present = {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob('*') if p.is_file()}
            if present != artifacts:
                changed = sorted(k for k in present.keys() | artifacts.keys() if present.get(k) != artifacts.get(k))
                raise ValueError(f'Reproduction differs: {changed}')
        else:
            if out.exists():
                raise ValueError('Output exists; choose a new immutable release directory')
            out.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.hus-data-', dir=out.parent) as temporary:
                stage = Path(temporary) / 'release'
                stage.mkdir()
                for name, data in artifacts.items():
                    path = stage / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                validate_release(stage)
                stage.rename(out)
        print(validate_release(out))
        return 0
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.exit(1, f'HUS data release failed: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
