"""Build/verify a fresh local HUS submission ZIP from an explicit public allowlist."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
RELEASES = ('hus-data-20261031-v3', 'hus-data-20261111-v4')
MANIFEST = 'SUBMISSION_MANIFEST.json'
FIXED = (
    'app/__init__.py', 'app/schemas/__init__.py', 'app/schemas/hus.py',
    'app/services/__init__.py', 'app/services/hus_service.py',
    'app/static/hus-rag-demo.html', 'app/static/hus-rag-demo.css',
    'app/static/hus-rag-demo.js', 'app/static/favicon.svg',
    'tools/run_hus_submission.py', 'tools/run_hus_rag.py', 'tools/package_hus_demo.py',
    'tools/check_hus_submission_target.py',
    'requirements-rag-demo.txt', 'requirements-rag.txt', 'requirements-lock.txt',
    'docs/HUS_RAG_SUBMISSION.md', 'docs/RAG_A7_V4_2026_11_11.md',
    'docs/RAG_LLM_COMPACT_V3_2026_11_11.md', 'data/hus/rag/CURRENT.json',
    'docs/RAG_BASELINE_A7_DIAGNOSTIC_2026_11_12.md',
    'docs/RAG_A7_POSTFIX_2026_11_12.md',
    'docs/RAG_LLM_V3_PREFLIGHT_2026_11_12.md',
    'docs/RAG_A7_AFTER_FOLLOWUP_2026_11_12.md',
    'docs/RAG_A7_THREE_CASE_REVIEW_2026_11_13.md',
    'docs/RAG_LLM_L5_V3_2026_11_13.md',
    'docs/RAG_LLM_ACCESS_DIAGNOSTIC_2026_11_13.md',
    'docs/RAG_L6_KEEP_DISABLED_2026_11_13.md',
    'data/hus/citation_assets/registry.json',
)
README = '''# HUS RAG — local submission

Python 3.11; lexical/BM25; release hus-data-20261111-v4; LLM off.
No private env file, key, account/database, vector index or Python environment is bundled.

```powershell
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements-rag-demo.txt -c requirements-lock.txt
.\\.venv\\Scripts\\python.exe -m tools.run_hus_submission --check
.\\.venv\\Scripts\\python.exe -m tools.run_hus_submission
```

Open http://127.0.0.1:8011/. Stop with Ctrl+C. No Google or 9Router is needed.
F3 requires the user's separate AI-reference consent and keeps its AI label.
The launcher forces this submission profile even if inherited environment differs.

Archive integrity: `python -m tools.package_hus_demo --verify PATH_TO_ORIGINAL_ZIP`.
Source files are bound by SUBMISSION_MANIFEST.json; it is not a digital signature.

A7 is **not fully accepted**: latest 48-case evaluation has routed Recall@5
24/24, completeness34/36 and controls11/12. Q002 refuses after retrieval,
Q003 returns a different source list, Q011 clarifies instead of no_information.
Historical23/24--33/36 and19/24--27/36 results remain unchanged.
See docs/RAG_A7_AFTER_FOLLOWUP_2026_11_12.md and the three-case review.
Compact LLM v3 live attempts all returned403: 0used/24fallback; prior budgets
are exhausted. New diagnostics/circuit/preparedr2 have only offline checks.
L6 remains keep_disabled; model content/latency/operator acceptance is pending.
Human reviews: 0. This archive is a reproducible local demo, not production sign-off.
Baseline language fixes were checked on exposed dev questions; historical Q001
still lacks evidence for the requested standard variant. If current A7 cases
are used for tuning, retire that set to dev and freeze another set after fixes.
See [submission and rollback](docs/HUS_RAG_SUBMISSION.md).
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_name(name):
    parts = PurePosixPath(name).parts
    if (not parts or PurePosixPath(name).as_posix() != name
            or '\\' in name or ':' in name or name.startswith('/')
            or any(p in {'.', '..', '.git', 'backups', '__pycache__'}
                   or p.startswith('.env') for p in parts)):
        raise ValueError('Unsafe or private package path')
    return name


def read_public(root, name):
    safe_name(name)
    root = Path(root).resolve()
    path = root / name
    if (not path.resolve().is_relative_to(root) or path.is_symlink()
            or any(p.is_symlink() for p in path.parents if p != root and p.is_relative_to(root))):
        raise ValueError('Package path escapes root or uses a symlink')
    return path.read_bytes()


def payloads(root=ROOT):
    root = Path(root).resolve()
    names = set(FIXED)
    names.update(p.relative_to(root).as_posix() for p in (root / 'app/hus').rglob('*.py')
                 if '__pycache__' not in p.parts)
    for release in RELEASES:
        prefix = 'data/hus/rag/releases/' + release + '/'
        manifest = json.loads(read_public(root, prefix + 'manifest.json'))
        names.add(prefix + 'manifest.json')
        for name, identity in manifest['files'].items():
            raw = read_public(root, prefix + safe_name(name))
            if {'bytes': len(raw), 'sha256': sha(raw)} != identity:
                raise ValueError('Release payload hash changed')
            names.add(prefix + name)
    registry = json.loads(read_public(root, 'data/hus/citation_assets/registry.json'))
    for identity in registry['assets'].values():
        name = 'data/hus/citation_assets/' + safe_name(identity['path'])
        raw = read_public(root, name)
        if len(raw) != identity['bytes'] or sha(raw) != identity['sha256']:
            raise ValueError('Citation asset hash changed')
        names.add(name)
    result = {name: read_public(root, name) for name in sorted(names)}
    result['README.md'] = README.encode('utf-8')
    current = json.loads(result['data/hus/rag/CURRENT.json'])
    if current['release_id'] != RELEASES[1]:
        raise ValueError('Submission requires CURRENT v4')
    return result


def build(out, *, root=ROOT):
    out = Path(out)
    if out.exists():
        raise ValueError('Choose a fresh ZIP path; existing packages are immutable')
    content = payloads(root)
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()
    manifest = {'schema_version': 'hus-local-submission-1.0', 'source_head_base': head,
        'source_identity': 'Actual payload hashes are authoritative, including uncommitted files.',
        'release_id': RELEASES[1], 'rollback_release_id': RELEASES[0],
        'retrieval': 'lexical', 'llm_enabled': False, 'public_deployment': False,
        'files_sha256': {name: sha(raw) for name, raw in sorted(content.items())}}
    content[MANIFEST] = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(content.items()):
            entry = zipfile.ZipInfo(name, date_time=(2026, 11, 12, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, raw)
    return verify(out)


def verify(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive names')
        for name in names:
            safe_name(name)
        manifest = json.loads(archive.read(MANIFEST))
        expected = manifest['files_sha256']
        if (manifest['schema_version'] != 'hus-local-submission-1.0'
                or manifest['llm_enabled'] is not False or manifest['retrieval'] != 'lexical'
                or set(names) != set(expected) | {MANIFEST}):
            raise ValueError('Submission inventory/profile differs')
        for name, checksum in expected.items():
            if sha(archive.read(name)) != checksum:
                raise ValueError('Submission payload hash differs')
    return {'verified': True, 'files': len(expected), 'bytes': Path(path).stat().st_size,
            'zip_sha256': sha(Path(path).read_bytes()), 'release_id': manifest['release_id'],
            'llm_enabled': False}


def build_transfer(out, wheel_zip, *, root=ROOT):
    """Build an immutable local kit; reuse verified offline wheels without downloads."""
    out, wheel_zip = Path(out), Path(wheel_zip)
    if out.exists():
        raise ValueError('Choose a fresh transfer directory; old kits are immutable')
    with zipfile.ZipFile(wheel_zip) as archive:
        inventory = json.loads(archive.read('wheelhouse/WHEELHOUSE_MANIFEST.json'))['files_sha256']
        if (len(inventory) != 25 or any(not name.endswith('.whl') or '/' in name or '\\' in name for name in inventory)
                or set(archive.namelist()) != {'wheelhouse/' + name for name in inventory}
                    | {'wheelhouse/WHEELHOUSE_MANIFEST.json'}):
            raise ValueError('Unexpected wheel inventory')
        for name, checksum in inventory.items():
            if sha(archive.read('wheelhouse/' + name)) != checksum:
                raise ValueError('Wheel SHA mismatch')
    out.mkdir(parents=True)
    package = build(out / 'hus-rag-demo.zip', root=root)
    shutil.copyfile(wheel_zip, out / 'wheelhouse-win-py311.zip')
    hashes = {'hus-rag-demo.zip': package['zip_sha256'],
              'wheelhouse-win-py311.zip': sha(wheel_zip.read_bytes())}
    template = read_public(root, 'tools/check_hus_submission_target.py').decode('utf-8')
    marker = 'ARCHIVES = {}  # Filled with verified ZIP hashes by build_transfer().'
    if template.count(marker) != 1:
        raise ValueError('Target checker template marker changed')
    checker = template.replace(marker, 'ARCHIVES = ' + repr(hashes))
    (out / 'CHECK_TARGET.py').write_text(checker, encoding='utf-8')
    guide = ('# HUS RAG: Windows 64-bit / CPython3.11\n\n'
             'Copy CHECK_TARGET.py and both ZIPs together. From this directory run:\n\n'
             '```powershell\npython -X utf8 -I -B CHECK_TARGET.py --root .\\hus-demo-target --run-demo\n```\n\n'
             'The root must be new. Installation/checks are offline; no API key is needed.\n'
             'The checker writes target-receipt even on failure; retain all logs.\n'
             'After checks, review browser, source opening, major reset and v4/v3 rollback\n'
             'on the actual target machine using demo/docs/HUS_RAG_SUBMISSION.md.\n'
             'A passed install/API receipt is not manual acceptance of A7/L6 or the UI.\n'
             'A7 remains24/24 recall,34/36 completeness,11/12 controls; AI review/human0.\n'
             'LLM stays off; no publish/deploy is authorized.\n')
    (out / 'README-MAY-NOP.md').write_text(guide, encoding='utf-8')
    manifest = {'schema_version': 'hus-target-transfer-1.0', 'actual_target_verified': False,
                'target_os': 'Windows amd64 CPython3.11',
                'files_sha256': {p.name: sha(p.read_bytes()) for p in sorted(out.iterdir())}}
    (out / 'TRANSFER_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return {'package': package, 'transfer_files': manifest['files_sha256'], 'actual_target_verified': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--out', type=Path, help='Build a fresh ZIP; never reads env files')
    action.add_argument('--verify', type=Path, help='Read-only inventory/hash verification')
    action.add_argument('--transfer', type=Path, help='Build a fresh ZIP/checker/offline wheel transfer kit')
    parser.add_argument('--wheel-zip', type=Path, help='Existing verified 25-wheel Windows/Python3.11 ZIP')
    args = parser.parse_args(argv)
    if args.transfer:
        if not args.wheel_zip:
            parser.error('--transfer requires --wheel-zip; no download is performed')
        result = build_transfer(args.transfer, args.wheel_zip)
    else:
        result = verify(args.verify) if args.verify else build(args.out)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
