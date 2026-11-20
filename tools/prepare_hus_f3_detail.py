"""Build/verify an isolated detailed AI reference candidate, with no provider calls."""

import argparse
import tempfile
from pathlib import Path

from app.hus.corpus import verify_artifacts
from app.hus.f3_detail import SOURCE_ROOT, build_candidate

DEFAULT_INPUTS = Path('data/hus/qa/20261110/f3_reference_v2/inputs')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    parser.add_argument('--inputs', type=Path, default=DEFAULT_INPUTS)
    parser.add_argument('--source-root', type=Path, default=SOURCE_ROOT)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        out = args.out.resolve()
        protected = [args.inputs, args.source_root, Path('data/hus/rag'), Path('data/hus/review'),
            Path('data/hus/evaluation'), Path('data/hus/qa/20261028'), Path('data/hus/corpus'),
            Path('data/hus/raw'), Path('data/hus/processed'), Path('database')]
        if any(out == p.resolve() or out.is_relative_to(p.resolve()) or p.resolve().is_relative_to(out)
               for p in protected):
            raise ValueError('Output overlaps protected input/data')
        if args.command == 'build' and out.exists():
            raise ValueError('Output already exists; choose a new candidate directory')
        output = build_candidate(args.inputs, args.source_root)
        if args.command == 'verify':
            verify_artifacts(out, output)
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.f3-detail-', dir=out.parent) as temp:
                staged = Path(temp) / 'candidate'
                staged.mkdir()
                for name, raw in output.items():
                    (staged / name).write_bytes(raw)
                staged.rename(out)
        print('Verified byte-identical candidate' if args.command == 'verify' else 'Built detailed F3 candidate')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'F3 candidate preparation failed: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
