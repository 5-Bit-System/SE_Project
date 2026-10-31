"""Synchronize the shared F2 copy and its receipts from the pinned canonical input."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.hus.data_release import digest, encoded, read_json


def synchronize(rag: Path, check: bool = False) -> None:
    inputs = read_json(rag / 'inputs/input_manifest.json')
    current_raw = (rag / 'inputs/canonical_f2.json').read_bytes()
    if digest(current_raw) != inputs['canonical_f2_sha256']:
        raise ValueError('Canonical input changed')
    current = json.loads(current_raw)
    old = read_json(rag.parents[0] / 'qa/20261028/f3_reference/inputs/hus_source.json')
    comparison = {'schema_version': '2.0', 'canonical_commit': inputs['canonical_commit'],
                  'canonical_git_blob': inputs['canonical_f2_git_blob'],
                  'canonical_sha256': digest(current_raw),
                  'previous_comparison': 'data/hus/qa/20261028/main_f2_comparison.json',
                  'tables_equal_to_previous_snapshot': current['tables'] == old['tables'],
                  'programs': len(current['tables']['curricula']),
                  'memberships': len(current['tables']['curriculum_courses']),
                  'source_rows': len(current['tables']['official_curriculum_entries']),
                  'catalog_reviews': current.get('catalog_reviews', []),
                  'runtime_publication': False,
                  'scope': 'source_transcription_preserving_unsigned_catalogs_and_unresolved_prerequisites'}
    expected = {'inputs/canonical_f2_comparison.json': encoded(comparison),
                'f2/hus_source.json': current_raw, 'f2/source_comparison.json': encoded(comparison)}
    manifest = read_json(rag / 'manifest.json')
    for item in manifest['files']:
        if item['path'] == 'f2/hus_source.json':
            item.update(origin='data/hus/rag/inputs/canonical_f2.json', bytes=len(current_raw), sha256=digest(current_raw))
        elif item['path'] == 'f2/source_comparison.json':
            item.update(origin='data/hus/rag/inputs/canonical_f2_comparison.json',
                        bytes=len(encoded(comparison)), sha256=digest(encoded(comparison)))
    manifest['datasets']['f2'].update(kind='structured_curriculum_source_mixed_review_status',
        canonical_commit=inputs['canonical_commit'], verified_programs=[r['program_id'] for r in current.get('catalog_reviews', [])])
    manifest['source_date'] = '2026-10-31'
    expected['manifest.json'] = encoded(manifest)
    for name, raw in expected.items():
        path = rag / name
        if check:
            if not path.is_file() or path.read_bytes() != raw:
                raise ValueError('Shared handoff is stale: ' + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    repo = rag.parents[2]
    for item in manifest['files']:
        raw = (rag / item['path']).read_bytes()
        if digest(raw) != item['sha256'] or len(raw) != item['bytes'] or raw != (repo / item['origin']).read_bytes():
            raise ValueError('Shared payload differs: ' + item['path'])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        synchronize(Path('data/hus/rag'), args.check)
        print('Shared F2/current-main receipt and all 19 payloads match.')
        return 0
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'HUS handoff synchronization failed: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
