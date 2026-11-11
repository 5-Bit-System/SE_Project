"""Compare replay-verified V5 runs without inference or changing runtime defaults."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.hus.vector_contract import digest
from tools.evaluate_hus_hybrid import replay, reserve_output
from tools.evaluate_hus_rag import write_json


def recommend(lexical, hybrid):
    a, b = lexical['result']['metrics'], hybrid['result']['metrics']
    reasons = []
    ra, rb = a['recall_at_5']['value'], b['recall_at_5']['value']
    ma, mb = a['mrr_at_5']['value'], b['mrr_at_5']['value']
    improved = ra is not None and rb is not None and (rb > ra + 1e-12 or
        (abs(rb - ra) <= 1e-12 and ma is not None and mb is not None and mb > ma + 1e-12))
    if not improved:
        reasons.append('no_final5_retrieval_improvement')
    if not b['vector_live']:
        reasons.append('no_live_vector_queries')
    for key in ('false_refusals', 'scope_error_cases', 'http_errors', 'source_audit_failures'):
        if b[key] > a[key] or (key in {'scope_error_cases', 'http_errors'} and b[key]):
            reasons.append('regression_' + key)
    for major, old in lexical['result']['by_major'].items():
        new = hybrid['result']['by_major'][major]
        if any(new[key] > old[key] for key in ('false_refusals', 'scope_error_cases', 'http_errors', 'source_audit_failures')):
            reasons.append('major_guard_regression_' + major)
    old = lexical['result']['source_and_answer_metrics_v2']['metrics']
    new = hybrid['result']['source_and_answer_metrics_v2']['metrics']
    pairs = [('f2_source_contract', old['f2']['source_contract_success'], new['f2']['source_contract_success'])]
    pairs += [(key, value, new['abstention'][key]) for key, value in old['abstention'].items()
              if key.startswith('correct_')]
    for key, left, right in pairs:
        if left['value'] is not None and (right['value'] is None or right['value'] < left['value']):
            reasons.append('regression_' + key)
    if any(r['result'].get('semantic_review') != 'exact_response_bound_ai' for r in (lexical, hybrid)):
        reasons.append('semantic_review_pending')
    else:
        supports = [r['result']['source_and_answer_metrics_v2']['metrics'].get('citation_source_support', {})
                    for r in (lexical, hybrid)]
        for support in supports:
            coverage = support.get('ai_review_coverage') or {}
            if coverage.get('value') != 1.0 or coverage.get('denominator', 0) <= 0:
                reasons.append('semantic_review_incomplete')
        for key in ('ai_entailment', 'ai_completeness', 'ai_end_to_end_supported_complete',
                    'integrity_among_answered_positive'):
            left, right = [(support.get(key) or {}).get('value') for support in supports]
            if left is None or right is None:
                reasons.append('semantic_review_incomplete')
            elif right < left:
                reasons.append('regression_' + key)
    return {'recommended_mode': 'lexical' if reasons else 'hybrid',
            'retrieval_improved': improved, 'reasons': sorted(set(reasons)), 'changes_runtime_default': False}


def compare(folders, out):
    reports, references = {}, {}
    for folder in map(Path, folders):
        replay(folder)
        report = json.loads((folder / 'report.json').read_bytes())
        if report['mode'] in reports:
            raise ValueError('Duplicate comparison mode')
        reports[report['mode']] = report
        references[report['mode']] = {'run': str(folder), 'manifest_sha256': digest(folder / 'manifest.json')}
    if set(reports) != {'lexical', 'vector', 'hybrid'}:
        raise ValueError('Comparison requires all three modes')
    if len({r['pins_sha256'] for r in reports.values()}) != 1:
        raise ValueError('Modes use different code/data/model/policy/environment pins')
    if len({r['process_id'] for r in reports.values()}) != 3:
        raise ValueError('RAM comparison requires separate mode processes')
    result = {'schema_version': 'hus-hybrid-comparison-3.0', 'runs': references,
        'pins_sha256': reports['lexical']['pins_sha256'],
        'modes': {mode: {'metrics': r['result']['metrics'], 'by_major': r['result']['by_major'],
                       'by_tag': r['result']['by_tag'], 'peak_rss_bytes': r['peak_rss_bytes'],
                       'initialization_ms': r['initialization_ms'],
                       'cold_ms': r['cold_warmup']['latency_ms'],
                       'source_and_answer_metrics': r['result']['source_and_answer_metrics_v2']['metrics']}
                  for mode, r in reports.items()},
        'recommendation': recommend(reports['lexical'], reports['hybrid']),
        'holdout_eligible': False, 'actual_human_reviews': 0}
    out = reserve_output(out)
    write_json(out / 'comparison.json', result)
    write_json(out / 'manifest.json', {'files_sha256': {'comparison.json': digest(out / 'comparison.json')}})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='append', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(compare(args.run, args.out)['recommendation']))


if __name__ == '__main__':
    main()
