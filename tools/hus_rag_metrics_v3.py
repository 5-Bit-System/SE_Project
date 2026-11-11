"""V5 replay metrics: parent final5 is distinct from either leg's candidate pool."""
from __future__ import annotations

import json
import math
import re
from dataclasses import asdict

from app.hus.hybrid_retrieval import POLICY
from app.hus.vector_contract import encoded
from tools.hus_rag_layer_metrics import canonical_field
from tools.hus_rag_metrics import ratio
from tools.hus_rag_metrics_v2 import evaluate as evaluate_v2
from tools.hus_rag_metrics_v2 import filter_errors, latency_stats

SCHEMA = 'hus-hybrid-evaluation-3.0'


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _validate_call(call):
    trace = call['v5_trace']
    _require(trace['policy_sha256'] == POLICY.sha256
             and encoded(json.loads(trace['policy_json'])) == encoded(asdict(POLICY)), 'V5 policy differs')
    scope = {k: v for k, v in call['parameters'].items() if k != 'top_k'}
    _require(json.loads(trace['filter_json']) == scope and call['parameters']['top_k'] == 5,
             'Trace scope/final budget differs')
    ranks, scores = {}, {}
    for leg in ('lexical', 'vector'):
        values = trace[leg]
        ids = [r['parent_id'] for r in values]
        _require(len(ids) <= 20 and len(ids) == len(set(ids)), 'Invalid candidate leg IDs')
        _require([r['rank'] for r in values] == list(range(1, len(ids) + 1)), 'Invalid compact parent rank')
        _require(all(type(r['rank']) is int and type(r['raw_score']) in {int, float}
                     and math.isfinite(r['raw_score']) for r in values), 'Invalid rank/score type')
        leg_hits = call['leg_hits'][leg]
        _require([h['chunk_id'] for h in leg_hits] == ids, 'Leg hits differ from ranked candidates')
        _require(all(h['score'] == r['raw_score'] for h, r in zip(leg_hits, values, strict=True)), 'Leg raw score differs')
        for hit in leg_hits:
            _require(hit['dataset'] == scope['dataset'] and hit['major'] == scope['major'], 'Candidate scope differs')
            for key in ('version', 'course_code', 'field', 'program_variant'):
                _require(scope.get(key) is None or hit.get(key) == scope[key], 'Candidate filter differs')
            _require(hit['review_status'] in ({'include', 'include_markdown'} if hit['dataset'] == 'f1'
                                             else {'needs_review'}), 'Candidate review differs')
            if hit['dataset'] == 'f3':
                _require(scope.get('allow_generated') is True and hit['content_origin'] == 'generated',
                         'Generated candidate without permission')
        ranks[leg] = {r['parent_id']: r['rank'] for r in values}
        scores[leg] = {r['parent_id']: r['raw_score'] for r in values}
    union = sorted(ranks['lexical'].keys() | ranks['vector'].keys())
    _require(list(trace['candidate_union']) == union, 'Candidate union differs')
    requested, actual = trace['requested_mode'], trace['actual_mode']
    _require(requested in {'lexical', 'vector', 'hybrid'} and actual in {requested, 'lexical'}, 'Invalid mode transition')
    reason = trace.get('fallback_reason')
    _require(actual == requested or bool(reason), 'Unlabelled lexical fallback')
    if reason:
        _require(actual == 'lexical' and not trace['vector'] and not trace['fused'], 'Fallback counted as vector/RRF')
    vt = trace.get('vector_trace')
    if requested == 'lexical':
        _require(not trace['vector'] and vt is None and not reason, 'Lexical comparator contains vector state')
    if vt:
        if vt.get('mode_used') != 'vector' or vt.get('fallback_reason'):
            _require(bool(reason) and actual == 'lexical' and not trace['vector'], 'Nested vector fallback counted twice')
        else:
            _require(not reason and actual == requested, 'Successful vector trace contradicts fallback')
    if trace['vector']:
        _require(vt and vt.get('index_id') and vt.get('mode_used') == 'vector'
                 and not vt.get('fallback_reason'), 'Unverified vector candidate leg')
    if actual == 'hybrid':
        fused = []
        for pid in union:
            a, b = ranks['lexical'].get(pid), ranks['vector'].get(pid)
            fused.append({'parent_id': pid, 'lexical_rank': a, 'vector_rank': b,
                          'rrf_score': (1 / (60 + a) if a else 0) + (1 / (60 + b) if b else 0)})
        fused.sort(key=lambda r: (-r['rrf_score'], r['parent_id']))
        _require(encoded(trace['fused']) == encoded(fused), 'RRF contributions/ranking differ')
        wanted = [r['parent_id'] for r in fused[:5]]
        expected_scores = {r['parent_id']: r['rrf_score'] for r in fused}
    else:
        _require(not trace['fused'], 'Non-hybrid result claims RRF')
        wanted = [r['parent_id'] for r in trace[actual]][:5]
        expected_scores = scores[actual]
    final = call['hits']
    _require([h['chunk_id'] for h in final] == wanted == list(trace['final_top5']), 'Final top5 differs from trace')
    _require(all(h['score'] == expected_scores[h['chunk_id']] for h in final), 'Final score differs')
    _require(len(final) <= 5 and len(wanted) == len(set(wanted)), 'Invalid final5')
    return trace, final, call['leg_hits']['lexical'] + call['leg_hits']['vector']


def validate_call(call):
    try:
        return _validate_call(call)
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        raise ValueError('Malformed V5 retrieval trace') from exc


def _matches(hit, anchor, target, request):
    code = request.get('course_code')
    codes = set(re.findall(r'\b[A-Z]{3}\d{4}[A-Z]?\b', request['question'].upper()))
    if code:
        codes.add(code)
    return (hit.get('chunk_id') == anchor['source_ref']['identity']
        and (hit.get('dataset'), hit.get('major'), hit.get('version'), hit.get('field')) ==
            (target['expected_dataset'], anchor['major'], anchor['version'], canonical_field(target['expected_field']))
        and (len(codes) != 1 or hit.get('course_code') in codes)
        and (request.get('program_variant') is None or hit.get('program_variant') == request['program_variant'])
        and (anchor.get('program_variant') is None or hit.get('program_variant') == anchor['program_variant']))


def retrieval_case(question, target, evidence, observation):
    eligible = target['category'] in {'f1', 'f3'}
    by_id = {e['evidence_id']: e for e in evidence}
    anchors = {by_id[eid]['source_ref']['identity']: by_id[eid] for eid in target['evidence_ids']
               if by_id[eid]['source_ref']['identity_field'] == 'chunk_id'}
    _require(not eligible or bool(anchors), 'Positive retrieval case has no canonical gold parent')
    calls = observation.get('retrieval_calls') or []
    _require(len(calls) <= 1, 'V5 expects one final retrieval call per question')
    trace, final, pool = (None, [], []) if not calls else validate_call(calls[0])
    request = question['request']
    recalled = sum(any(_matches(h, e, target, request) for h in final) for e in anchors.values())
    candidates = sum(any(_matches(h, e, target, request) for h in pool) for e in anchors.values())
    first = next((i for i, h in enumerate(final, 1)
                  if any(_matches(h, e, target, request) for e in anchors.values())), None)
    vt = trace.get('vector_trace') if trace else None
    return {'question_id': question['question_id'], 'major': request['major'], 'category': target['category'],
            'tags': question.get('v5_tags', ['historical_exposed']), 'retrieval_eligible': eligible,
            'retrieval_called': bool(calls), 'recall_at_5': recalled / len(anchors) if eligible else None,
            'mrr_at_5': (1 / first if first else 0.0) if eligible else None,
            'candidate_recall': candidates / len(anchors) if eligible else None,
            'actual_mode': trace['actual_mode'] if trace else None,
            'fallback_reason': trace.get('fallback_reason') if trace else None,
            'vector_attempted': vt is not None,
            'vector_live': bool(vt and vt.get('index_id') and vt['mode_used'] == 'vector'
                                and not vt.get('fallback_reason'))}


def summarize_cases(cases):
    ranked = [c for c in cases if c['retrieval_eligible']]
    attempted = [c for c in cases if c['vector_attempted']]
    return {'cases': len(cases), 'retrieval_cases': len(ranked),
        'recall_at_5': ratio(sum(c['recall_at_5'] for c in ranked), len(ranked)),
        'mrr_at_5': ratio(sum(c['mrr_at_5'] for c in ranked), len(ranked)),
        'candidate_recall': ratio(sum(c['candidate_recall'] for c in ranked), len(ranked)),
        'no_call_misses': sum(not c['retrieval_called'] for c in ranked),
        'vector_attempts': len(attempted), 'vector_live': sum(c['vector_live'] for c in attempted),
        'fallbacks': {reason: sum(c['fallback_reason'] == reason for c in cases)
                      for reason in sorted({c['fallback_reason'] for c in cases if c['fallback_reason']})},
        'fallback_rate': ratio(sum(bool(c['fallback_reason']) for c in attempted), len(attempted)),
        'false_refusals': sum(c.get('false_refusal', False) for c in cases),
        'scope_error_cases': sum(c.get('scope_error', False) for c in cases),
        'http_errors': sum(c.get('http_error', False) for c in cases),
        'source_audit_failures': sum(not c.get('source_audit_passed', True) for c in cases),
        'warm_latency': latency_stats([c['latency_ms'] for c in cases if 'latency_ms' in c])}


def evaluate(bundle, observations, audits, review=None):
    _require([q['question_id'] for q in bundle['questions']] == [o['question_id'] for o in observations],
             'Prediction IDs do not join questions')
    baseline = evaluate_v2(bundle['questions'], bundle['gold'], bundle['evidence'], observations, audits,
                           legacy_applicable=bundle['legacy_applicable'], review=review)
    cases = []
    for q, g, o, a, old in zip(bundle['questions'], bundle['gold'], observations, audits, baseline['cases'], strict=True):
        row = retrieval_case(q, g, bundle['evidence'], o)
        expanded = []
        for call in o.get('retrieval_calls', []):
            expanded.append(call)
            expanded += [dict(parameters=call['parameters'], hits=call['leg_hits'][leg]) for leg in ('lexical', 'vector')]
        answer = o.get('response', {}).get('hus_answer') or {}
        errors = filter_errors(q['request'], answer, expanded)
        cases.append(row | {'false_refusal': old['positive'] and answer.get('status') != 'answered',
            'scope_error': any(errors.values()), 'http_error': o.get('http_status') != 200,
            'source_audit_passed': a['passed'], 'latency_ms': o['latency_ms']})
    return {'schema_version': SCHEMA, 'metrics': summarize_cases(cases), 'cases': cases,
        'by_major': {m: summarize_cases([c for c in cases if c['major'] == m]) for m in sorted({c['major'] for c in cases})},
        'by_tag': {tag: summarize_cases([c for c in cases if tag in c['tags']]) for tag in sorted({t for c in cases for t in c['tags']})},
        'source_and_answer_metrics_v2': baseline,
        'semantic_review': 'exact_response_bound_ai' if review else 'pending',
        'independent_holdout_accepted': False, 'actual_human_reviews': 0}
