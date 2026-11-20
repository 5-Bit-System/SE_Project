"""L5 sealed artifacts and cached paired metrics; no network or RAG execution."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tools.evaluate_hus_rag import digest, write_json
from tools.hus_rag_metrics_v2 import digest_json, latency_stats

SCHEMA = 'hus-llm-paired-1.0'


def reserve(folder):
    folder = Path(folder).resolve()
    if folder.exists() or any((p / 'manifest.json').exists() for p in folder.parents):
        raise ValueError('Choose a fresh non-nested artifact directory')
    folder.mkdir(parents=True)
    return folder


def seal(folder):
    folder = Path(folder)
    write_json(folder / 'manifest.json', {'schema_version': SCHEMA, 'files_sha256': {
        p.name: digest(p) for p in sorted(folder.iterdir()) if p.is_file() and p.name != 'manifest.json'}})


def read_sealed(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder / 'manifest.json').read_bytes())
    expected = manifest['files_sha256']
    if (manifest.get('schema_version') != SCHEMA
            or set(expected) != {p.name for p in folder.iterdir() if p.name != 'manifest.json'}):
        raise ValueError('Artifact inventory mismatch')
    result = {}
    for name, checksum in expected.items():
        path = (folder / name).resolve()
        if path.parent != folder or path.is_symlink() or digest(path) != checksum:
            raise ValueError('Artifact hash mismatch')
        result[name] = json.loads(path.read_bytes())
    return result


def eligible(record):
    answer = record['baseline'].get('hus_answer') or {}
    return (answer.get('status') == 'answered' and answer.get('dataset') in {'f1', 'f2', 'f3'}
            and bool(answer.get('citations'))
            and (answer['dataset'] != 'f3' or record['effective_request'].get('allow_generated_reference') is True))


def metrics(records, observations):
    ids = [r['question_id'] for r in records]
    if len(ids) != len(set(ids)) or ids != [o.get('question_id') for o in observations]:
        raise ValueError('Paired IDs must join exactly in order')
    for record, o in zip(records, observations, strict=True):
        a, b = o['a'], o['b']
        generation = b.get('generation') or {}
        if (o['prepared_case_sha256'] != digest_json(record) or a != record['baseline']
                or a.get('hus_answer') != b.get('hus_answer') or a['mode'] != b['mode']):
            raise ValueError('Paired canonical binding changed')
        if type(generation.get('used')) is not bool:
            raise ValueError('Missing strict generation outcome')
        if generation['used']:
            if (not eligible(record) or generation.get('model') != o['trace'].get('actual_model')
                    or not o['trace']['attempted'] or generation.get('fallback_reason') is not None
                    or generation.get('prompt_sha256') != record['prompt'].get('sha256')):
                raise ValueError('Used output differs from provider/prompt binding')
            if (a['hus_answer']['dataset'] == 'f2' and not b['reply'].endswith(a['reply'])):
                raise ValueError('F2 canonical text changed')
        elif b['reply'] != a['reply'] or generation.get('model') is not None:
            raise ValueError('Fallback changed original text/model')
        if o['trace']['attempted'] and (not eligible(record)
                or o['trace']['prompt_sha256'] != record['prompt'].get('sha256')):
            raise ValueError('Provider request escaped guard/prompt binding')
    return summarize(records, observations)


def summarize(records, observations):
    pairs = list(zip(records, observations, strict=True))
    positive = [(r, o) for r, o in pairs if eligible(r)]
    used = [(r, o) for r, o in positive if o['b']['generation']['used']]
    fallback = [(r, o) for r, o in positive if not o['b']['generation']['used']]
    attempted = [o for _, o in pairs if o['trace']['attempted']]
    usage = [o['trace'].get('usage') or {} for o in attempted]
    counters = ('prompt_tokens', 'completion_tokens', 'total_tokens')
    unknown = {key: sum(key not in u for u in usage) for key in counters}
    known = {key: sum(u.get(key, 0) for u in usage) for key in counters}
    targets = [r for r, _ in pairs if r['gold']['category'] in {'f1', 'f2', 'f3'}]
    result = {'cases': len(pairs), 'eligible': len(positive), 'used': len(used), 'fallback': len(fallback),
        'guard_skipped': len(pairs) - len(positive), 'provider_requests': len(attempted),
        'eligible_not_attempted': sum(not o['trace']['attempted'] for _, o in positive),
        'used_rate_among_eligible': len(used) / len(positive) if positive else None,
        'actual_models': dict(Counter(o['trace']['actual_model'] for o in attempted if o['trace'].get('actual_model'))),
        'fallback_reasons': dict(Counter(o['b']['generation']['fallback_reason'] for _, o in fallback)),
        'http_status': dict(Counter(str(o['trace']['http_status']) for o in attempted if o['trace'].get('http_status'))),
        'errors': dict(Counter(o['trace']['error'] for _, o in pairs if o['trace'].get('error'))),
        'token_usage': {key: known[key] if not unknown[key] else None for key in counters},
        'token_usage_known_subtotal': known, 'token_counter_unknown_requests': unknown,
        'source_audit_failures': sum(not r['source_audit'].get('passed', False) for r, _ in pairs),
        'baseline_false_refusals': sum((r['baseline'].get('hus_answer') or {}).get('status') != 'answered' for r in targets),
        'control_status_mismatches': sum(
            (r['baseline']['mode'] if r['baseline']['mode'] == 'basic_chat'
             else (r['baseline'].get('hus_answer') or {}).get('status')) != r['gold'].get('expected_status')
            for r, _ in pairs if r not in targets and 'expected_status' in r['gold']),
        'usage_known_requests': sum(bool(u) for u in usage),
        'usage_unknown_requests': sum(not u for u in usage),
        'latency': {'baseline': latency_stats([r['baseline_latency_ms'] for r, _ in pairs]),
                    'rewrite_used': latency_stats([o['rewrite_ms'] for _, o in used]),
                    'rewrite_fallback': latency_stats([o['rewrite_ms'] for _, o in fallback]),
                    'provider': latency_stats([o['trace']['provider_ms'] for o in attempted])}}
    for dimension, get in [('major', lambda r: r['request']['major']),
                           ('family', lambda r: r['gold']['category'])]:
        result['by_' + dimension] = {}
        for value in sorted({get(r) for r, _ in pairs}):
            rows = [(r, o) for r, o in pairs if get(r) == value]
            result['by_' + dimension][value] = {
                'cases': len(rows), 'eligible': sum(eligible(r) for r, _ in rows),
                'used': sum(o['b']['generation']['used'] for _, o in rows),
                'provider_requests': sum(o['trace']['attempted'] for _, o in rows)}
    return result


def review_template(run_id, records, observations):
    return {'schema_version': SCHEMA, 'measurement_id': run_id,
        'pairs_sha256': digest_json(observations), 'actual_human_reviews': 0,
        'cases': [{'question_id': r['question_id'], 'pair_sha256': digest_json(o),
                   'target_sha256': digest_json({'gold': r['gold'], 'evidence': r['gold_evidence']}),
                   'reviewer_kind': 'ai', 'reviewer': '', 'notes': '',
                   'a_entailment': 'pending', 'a_completeness': 'pending',
                   'b_entailment': 'pending', 'b_completeness': 'pending', 'readability': 'pending'}
                  for r, o in zip(records, observations, strict=True)]}


def semantic_scores(records, observations, template, review):
    if ({k: v for k, v in review.items() if k != 'cases'}
            != {k: v for k, v in template.items() if k != 'cases'}):
        raise ValueError('Semantic review metadata binding changed')
    if len(review['cases']) != len(template['cases']):
        raise ValueError('Semantic review coverage missing')
    judgments = []
    for record, o, expected, row in zip(records, observations, template['cases'], review['cases'], strict=True):
        keys = {'question_id', 'pair_sha256', 'target_sha256'}
        if set(row) != set(expected) or any(row.get(k) != expected[k] for k in keys):
            raise ValueError('Semantic review pair/target binding changed')
        if (row['reviewer_kind'] != 'ai' or not isinstance(row['reviewer'], str) or not row['reviewer'].strip()
                or not isinstance(row['notes'], str) or not row['notes'].strip()):
            raise ValueError('Explicit AI reviewer and content notes required')
        positive = record['gold']['category'] in {'f1', 'f2', 'f3'}
        for arm in ('a', 'b'):
            answer = o[arm].get('hus_answer') or {}
            answered = answer.get('status') == 'answered'
            entailment, complete = row[arm + '_entailment'], row[arm + '_completeness']
            if entailment not in {'pass', 'fail', 'not_applicable'} or complete not in {'pass', 'fail', 'not_applicable'}:
                raise ValueError('Pending or invalid semantic judgment')
            if positive:
                if complete == 'not_applicable' or (answered and entailment == 'not_applicable'):
                    raise ValueError('Positive semantic review cannot be skipped')
                if not answered and (entailment != 'not_applicable' or complete != 'fail'):
                    raise ValueError('Missing positive answer is incomplete')
            elif (entailment, complete) != ('not_applicable', 'not_applicable'):
                raise ValueError('Controls have no positive semantic score')
        if row['readability'] not in ({'better', 'same', 'worse'} if positive and eligible(record) else {'not_applicable'}):
            raise ValueError('Invalid readability judgment')
        if o['a']['reply'] == o['b']['reply']:
            if (row['a_entailment'], row['a_completeness']) != (row['b_entailment'], row['b_completeness']):
                raise ValueError('Semantic judgments differ for identical answers')
            if positive and eligible(record) and row['readability'] != 'same':
                raise ValueError('Readability cannot improve or worsen for identical answers')
        judgments.append((record, o, row))

    def group(items):
        return {'count': len(items), **{key + '_pass': sum(row[key] == 'pass' for _, _, row in items)
                    for key in ('a_entailment', 'a_completeness', 'b_entailment', 'b_completeness')},
                'readability': dict(Counter(row['readability'] for _, _, row in items))}

    positives = [item for item in judgments if item[0]['gold']['category'] in {'f1', 'f2', 'f3'}]
    return {'all_positive': group(positives),
            'used_only': group([item for item in positives if item[1]['b']['generation']['used']]),
            'fallback_only': group([item for item in positives if eligible(item[0]) and not item[1]['b']['generation']['used']]),
            'reviewer_kind': 'ai', 'actual_human_reviews': 0,
            'independent_holdout_accepted': False}
