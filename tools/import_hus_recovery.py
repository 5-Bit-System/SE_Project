"""Archive already captured public sources and compare selected F1 prose offline."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import tempfile

from app.hus.data_release import digest, encoded, jsonl, read_json, read_rows
from app.hus.release_text import display_text, fold


def comparison_text(value: str) -> str:
    return re.sub(r'[^a-z0-9]', '', fold(display_text(value)[0]))


def import_captures(acquisitions: list[Path], repo: Path, out: Path) -> dict:
    if out.exists():
        raise ValueError('Recovery output exists')
    units = read_rows(repo / 'data/hus/rag/f1/f1_units.jsonl')
    wanted = {u['document_id'] for u in units if u['review_status'] == 'include_markdown'}
    captures, pages, comparisons, payloads = [], [], [], {}
    seen = set()
    for acquisition in acquisitions:
        report = read_json(acquisition / 'report.json')
        for row in report['results']:
            if row['status'] != 'captured_unreviewed':
                continue
            raw = row['raw_source']
            path = acquisition / raw['raw_path']
            data = path.read_bytes()
            if digest(data) != raw['raw_sha256']:
                raise ValueError('Captured bytes differ from provenance')
            key = row['document_id']
            if (key, raw['raw_sha256']) in seen:
                continue
            seen.add((key, raw['raw_sha256']))
            ext = raw['file_type']
            relative = 'files/' + raw['raw_sha256'] + '.' + ext
            payloads[relative] = data
            capture = {'document_id': key, 'requested_url': row['url'], 'final_url': row['final_url'],
                       'fetched_at': raw['fetched_at'], 'sha256': raw['raw_sha256'], 'bytes': len(data),
                       'path': relative, 'file_type': ext, 'major': row['major'],
                       'historical_byte_equality': 'unknown', 'academic_verified': False}
            captures.append(capture)
            source_pages = []
            if ext == 'pdf':
                import fitz
                with fitz.open(path) as document:
                    source_pages = [p.get_text('text') for p in document]
                capture['extractor'] = 'PyMuPDF/' + fitz.VersionBind
            elif ext == 'docx':
                import docx
                document = docx.Document(path)
                # F1 narrative paragraphs only; tables remain in the archived source.
                source_pages = ['\n'.join(p.text for p in document.paragraphs)]
                capture['extractor'] = 'python-docx/' + docx.__version__
            elif ext == 'html':
                from bs4 import BeautifulSoup
                source_pages = [BeautifulSoup(data, 'html.parser').get_text('\n', strip=True)]
                capture['extractor'] = 'beautifulsoup4-visible-text'
            capture['page_count'] = len(source_pages)
            for number, text in enumerate(source_pages, 1):
                pages.append({'document_id': key, 'page': number, 'text': text,
                              'text_sha256': digest(text.encode('utf-8')), 'raw_sha256': capture['sha256'],
                              'extraction_not_visual_review': True})
            if key in wanted:
                whole = comparison_text('\n'.join(source_pages))
                for unit in [u for u in units if u['document_id'] == key]:
                    quote = comparison_text(unit['source_quote'])
                    matches = [i + 1 for i, text in enumerate(source_pages) if quote in comparison_text(text)]
                    comparisons.append({'unit_id': unit['unit_id'], 'document_id': key,
                        'raw_sha256': capture['sha256'], 'source_quote_sha256': digest(unit['source_quote'].encode()),
                        'source_markdown_locator': unit['locator'],
                        'comparison': 'normalized_prose_match' if quote and quote in whole else 'alignment_not_established',
                        'matching_single_pages': matches, 'normalization': 'display_repairs_fold_alnum_only',
                        'reviewer': 'Codex', 'review_scope': 'selected_F1_prose_trace_only',
                        'academic_verified': False, 'historical_original_version_verified': False})
    report = {'schema_version': '1.0', 'captures': len(captures),
              'f1_originals_captured': len({c['document_id'] for c in captures} & wanted),
              'f1_originals_expected': len(wanted), 'extracted_pages': len(pages),
              'f1_comparisons': dict(Counter(c['comparison'] for c in comparisons)),
              'academic_review_completed': False,
              'policy': 'Capture and selected-prose comparison do not certify historical versions or academic applicability'}
    payloads.update({'captures.jsonl': jsonl(captures), 'source_texts.jsonl': jsonl(pages),
                     'f1_comparisons.jsonl': jsonl(comparisons), 'report.json': encoded(report)})
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.recovery-', dir=out.parent) as temporary:
        stage = Path(temporary) / 'recovered'
        stage.mkdir()
        for name, data in payloads.items():
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        shutil.move(str(stage), str(out))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquisition', type=Path, action='append', required=True)
    parser.add_argument('--repo-root', type=Path, default=Path('.'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(import_captures(args.acquisition, args.repo_root, args.out), ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f'Recovery import failed: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
