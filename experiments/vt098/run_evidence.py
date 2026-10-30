"""Capture actual unittest output, command, source hashes and environment."""

import hashlib
import json
import platform
import sqlite3
import subprocess
import sys
from pathlib import Path

import pydantic

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    label = sys.argv[1]
    if label not in {'draft-red', 'reviewed-red', 'green'}:
        raise SystemExit('Use draft-red, reviewed-red or green')
    command = [sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover',
               '-s', 'experiments/vt098', '-p', 'test_*.py', '-v']
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    head = subprocess.run(['git', '-c', f'safe.directory={ROOT.as_posix()}', 'rev-parse', 'HEAD'],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    artifact = {
        'label': label, 'head_before_capture': head,
        'baseline': '7b387a394e334e217733a571ee76a573157a24f2',
        'command': command, 'exit_code': result.returncode,
        'python': platform.python_version(), 'platform': platform.platform(),
        'sqlite': sqlite3.sqlite_version, 'pydantic': pydantic.__version__,
        'sha256': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                   for name in ('harness.py', 'schema.py', 'test_harness.py')},
        'stdout': result.stdout, 'stderr': result.stderr,
        'scope': 'SQLite harness; not production HTTP, authentication or PostgreSQL',
    }
    target = HERE / 'evidence' / f'{label}.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(result.stdout + result.stderr)
    print(f'Captured {label}: exit_code={result.returncode}; {target.relative_to(ROOT)}')
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
