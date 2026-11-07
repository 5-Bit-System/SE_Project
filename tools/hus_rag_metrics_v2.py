"""Offline A2 metrics. Raw legacy scores and AI judgments stay separate."""

from __future__ import annotations

import hashlib
import json
import math
import re

from tools.hus_rag_layer_metrics import canonical_field, layer_metrics
from tools.hus_rag_metrics import ratio, summarize

SCHEMA = 'hus-chatbot-evaluation-2.0'


def digest_json(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def latency_stats(values):
    if any(type(v) not in {int, float} or not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('Latency samples must be finite nonnegative milliseconds')
    values = sorted(values)
    return {'count': len(values), 'p50_ms': values[math.ceil(len(values) * .5) - 1] if values else None,
            'p95_ms': values[math.ceil(len(values) * .95) - 1] if values else None,
            'min_ms': values[0] if values else None, 'max_ms': values[-1] if values else None}


def validate_review(questions, gold, observations, audits, review):
    if review is None:
        return {}
    if [r.get('question_id') for r in review] != [q['question_id'] for q in questions]:
        raise ValueError('Review must cover every question exactly once in recorded order')
    for q, g, o, a, r in zip(questions, gold, observations, audits, review, strict=True):
        bindings = {'request': q['request'], 'response': o.get('response', {}), 'gold': g, 'audit': a}
        if any(r.get(key + '_sha256') != digest_json(value) for key, value in bindings.items()):
            raise ValueError('Semantic review binding differs: ' + q['question_id'])
        if r.get('reviewer_kind') != 'ai' or not r.get('reviewer') or not r.get('notes'):
            raise ValueError('This AI-only review workflow cannot certify a human reviewer')
        if any(r.get(key) not in {'pass', 'fail', 'not_applicable'} for key in ['entailment', 'completeness']):
            raise ValueError('Invalid review decision')
        positive = g['category'] in {'f1', 'f2', 'f3'}
        answer = o.get('response', {}).get('hus_answer') or {}
        answered = o.get('http_status') == 200 and answer.get('status') == 'answered'
        if positive and r['completeness'] == 'not_applicable':
            raise ValueError('Every positive needs a completeness judgment')
        if not positive and (r['entailment'] != 'not_applicable' or r['completeness'] != 'not_applicable'):
            raise ValueError('Control questions have no positive-answer semantic score')
        if positive and not answered and (r['completeness'] != 'fail' or r['entailment'] != 'not_applicable'):
            raise ValueError('A missing positive answer is incomplete, not entailed')
        if positive and answered and r['entailment'] == 'not_applicable':
            raise ValueError('An answered positive needs an entailment judgment')
    return {r['question_id']: r for r in review}


def _scope(citation):
    meta = citation.get('metadata') or {}
    record = meta.get('provenance', {}).get('portable_record') or {}
    scope = record.get('scope') or meta.get('scope') or {}
    return {'major': record.get('major', scope.get('major', meta.get('major'))),
            'version': scope.get('curriculum_version', meta.get('curriculum_version', meta.get('program_version'))),
            'course_code': record.get('course_code', meta.get('course_code')),
            'program_variant': scope.get('program_variant', meta.get('program_variant')),
            'review_status': citation.get('review_status'),
            'content_origin': citation.get('content_origin', meta.get('content_origin')),
            'dataset': citation.get('dataset')}


def filter_errors(request, answer, calls):
    errors = dict.fromkeys(['major', 'version', 'course_code', 'program_variant', 'review', 'ai_opt_in'], False)
    contexts = []
    if answer:
        contexts.append({'major': answer.get('major'), 'version': answer.get('version'),
                         'course_code': answer.get('facts', {}).get('course_code')})
    contexts += [_scope(c) for c in answer.get('citations', [])]
    contexts += [hit for call in calls for hit in call.get('hits', [])]
    codes = set(re.findall(r'\b[A-Z]{3}\d{4}[A-Z]?\b', request['question'].upper()))
    if request.get('course_code'):
        codes.add(request['course_code'])
    for call in calls:
        parameters = call.get('parameters') or {}
        if not parameters:
            continue
        errors['major'] |= parameters.get('major') != request['major']
        if request.get('version') is not None:
            errors['version'] |= parameters.get('version') != request['version']
        if len(codes) == 1 and parameters.get('course_code'):
            errors['course_code'] |= parameters['course_code'] not in codes
        if request.get('program_variant') is not None:
            errors['program_variant'] |= parameters.get('program_variant') != request['program_variant']
        if parameters.get('allow_generated') is True:
            errors['ai_opt_in'] |= request.get('allow_generated_reference') is not True
    for context in contexts:
        if context.get('major') is not None:
            errors['major'] |= context['major'] != request['major']
        if request.get('version') is not None and context.get('version') is not None:
            errors['version'] |= context['version'] != request['version']
        if len(codes) == 1 and context.get('course_code'):
            errors['course_code'] |= context['course_code'] not in codes
        if request.get('program_variant') is not None and context.get('program_variant') is not None:
            errors['program_variant'] |= context['program_variant'] != request['program_variant']
        review = context.get('review_status')
        allowed = {'f1': {'include', 'include_markdown'}, 'f2': {'verified', 'draft_unverified'}, 'f3': {'needs_review'}}
        if review is not None and context.get('dataset') in allowed:
            errors['review'] |= review not in allowed[context['dataset']]
        if context.get('content_origin') == 'generated' or context.get('dataset') == 'f3':
            errors['ai_opt_in'] |= request.get('allow_generated_reference') is not True
    return errors


def _quote_key(text):
    # This is just an explicitly named coverage proxy, not an entailment judge.
    return re.sub(r'[\W_]', '', re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)).casefold()


def _summarize(cases, *, legacy_applicable):
    positive = [c for c in cases if c['positive']]
    ranked = [c for c in cases if c['retrieval_eligible']]
    called = [c for c in ranked if c['retrieval_called']]
    f2 = [c for c in cases if c['category'] == 'f2']
    answered = [c for c in positive if c['actual_status'] == 'answered' and not c['http_error']]
    semantic = [c for c in positive if c['ai_completeness'] is not None]
    entailed = [c for c in answered if c['ai_entailment'] is not None]
    controls = [c for c in cases if not c['positive']]
    refusals = [c for c in controls if c['category'] in {'missing_evidence', 'out_of_scope'}]
    consent = [c for c in controls if c['category'] == 'opt_in_required']
    clarifications = [c for c in controls if c['category'] == 'clarification_required']
    return {
        'cases': len(cases), 'raw_legacy': summarize(cases) if legacy_applicable else None,
        'routing': {'positive_dataset_and_field': ratio(sum(c['positive_dataset_and_field_correct'] for c in positive), len(positive)),
                    'missing_observation_cases': sum(not c['classifier_observation_present'] for c in cases),
                    'stage': 'classifier_before_scope_and_evidence_guards'},
        'filters': {'errors': {key: sum(c['filter_errors'][key] for c in cases)
                               for key in ['major', 'version', 'course_code', 'program_variant', 'review', 'ai_opt_in']},
                    'observed_search_cases': sum(c['retrieval_filter_observed'] for c in ranked),
                    'anchor_excluded_by_observed_filter': sum(c['anchor_excluded_by_observed_filter'] for c in ranked)},
        'retrieval': {'routed_recall_at_5': ratio(sum(c['scope_checked_recall_at_5'] for c in ranked), len(ranked)),
                      'conditional_recall_at_5': ratio(sum(c['scope_checked_recall_at_5'] for c in called), len(called)),
                      'search_call_coverage': ratio(len(called), len(ranked)),
                      'no_call_misses': sum(not c['retrieval_called'] for c in ranked),
                      'post_retrieval_false_abstention': sum(c['false_abstention'] for c in called),
                      'definition': 'Macro recall over all F1/F3 positives, first actual search top5 and anchor scope; no-call is zero.'},
        'f2': {'source_contract_success': ratio(sum(c['f2_contract_correct'] for c in f2), len(f2)),
               'by_field': {field: ratio(sum(c['f2_contract_correct'] for c in f2 if c['expected_field_v2'] == field),
                                         sum(c['expected_field_v2'] == field for c in f2))
                            for field in sorted({c['expected_field_v2'] for c in f2})},
               'definition': 'Exact source facts/status and intent, independent audit and scope; raw values never normalized into empty lists.'},
        'citation_source_support': {
            'integrity_among_answered_positive': ratio(sum(c['source_integrity'] for c in answered), len(answered)),
            'gold_quote_coverage_proxy': ratio(sum(c['gold_quote_covered'] for c in ranked), len(ranked)),
            'ai_review_coverage': ratio(len(semantic), len(positive)),
            'ai_entailment': ratio(sum(c['ai_entailment'] for c in entailed), len(entailed)) if entailed else None,
            'ai_completeness': ratio(sum(c['ai_completeness'] for c in semantic), len(semantic)) if semantic else None,
            'ai_end_to_end_supported_complete': ratio(sum(c['ai_entailment'] is True and c['ai_completeness'] is True
                and c['source_integrity'] and not any(c['filter_errors'].values()) and not c['http_error']
                and c['actual_status'] == 'answered' and (c['category'] != 'f2' or c['f2_contract_correct'])
                for c in semantic), len(semantic)) if semantic else None,
            'reviewer_kind': 'ai' if semantic else None, 'actual_human_reviews': 0,
            'definition': 'Quote/anchor coverage is not entailment. Semantic judgments require a separate exact-response-bound AI review.'},
        'abstention': {'correct_missing_or_out_of_scope': ratio(sum(c['guardrail_success'] for c in refusals), len(refusals)),
                       'correct_opt_in_clarification': ratio(sum(c['guardrail_success'] for c in consent), len(consent)),
                       'correct_contract_clarification': ratio(sum(c['guardrail_success'] for c in clarifications), len(clarifications)),
                       'false_abstention': ratio(sum(c['false_abstention'] for c in positive), len(positive)),
                       'http_errors': sum(c['http_error'] for c in cases),
                       'control_failures': sum(not c['guardrail_success'] for c in controls)},
        'latency': {'http_ms': latency_stats([c['latency_ms'] for c in cases]),
                    'definition': 'Nearest-rank p50/p95 of recorded local warmed TestClient HTTP wall time; excludes source auditing/review.'},
    }


def evaluate(questions, gold, evidence, observations, audits, *, review=None, legacy_applicable=True):
    ids = [q['question_id'] for q in questions]
    if ids != [a['question_id'] for a in audits] or len(ids) != len(set(ids)):
        raise ValueError('All source audit IDs must join exactly')
    combined = [{**o, 'citation_integrity': a} for o, a in zip(observations, audits, strict=True)]
    # The unchanged layer scorer enforces strict question/gold/observation joins.
    layers = layer_metrics(questions, gold, evidence, combined)
    judgments = validate_review(questions, gold, observations, audits, review)
    by_evidence = {e['evidence_id']: e for e in evidence}
    cases = []
    for q, g, o, a, base in zip(questions, gold, observations, audits, layers['cases'], strict=True):
        answer = o.get('response', {}).get('hus_answer') or {}
        facts = answer.get('facts') or {}
        expected_field = canonical_field(g['expected_field'])
        source = a.get('source_f2_contract')
        expected = g.get('v2_expected_facts', {})
        errors = filter_errors(q['request'], answer, o.get('retrieval_calls') or [])
        f2_ok = (g['category'] == 'f2' and o.get('http_status') == 200 and answer.get('status') == 'answered'
                 and answer.get('dataset') == 'f2' and facts.get('field') == expected_field
                 and a.get('passed') is True and bool(source) and not any(errors.values())
                 and all(facts.get(k) == v for k, v in source.items())
                 and all(facts.get(k) == v for k, v in expected.items()))
        quotes = [_quote_key(c.get('quote', '')) for c in answer.get('citations', [])]
        refs = [by_evidence[eid] for eid in g['evidence_ids']]
        wanted = [e.get('value', e.get('quote')) for e in refs]
        covered = bool(wanted) and all(isinstance(value, str) and bool(_quote_key(value))
            and any(_quote_key(value) in quote for quote in quotes) for value in wanted)
        judgment = judgments.get(q['question_id'], {})
        cases.append({**base, 'expected_field_v2': expected_field, 'filter_errors': errors,
                      'f2_contract_correct': bool(f2_ok), 'source_integrity': a.get('passed') is True,
                      'gold_quote_covered': bool(covered), 'latency_ms': o['latency_ms'],
                      'ai_entailment': None if judgment.get('entailment') in {None, 'not_applicable'} else judgment['entailment'] == 'pass',
                      'ai_completeness': None if judgment.get('completeness') in {None, 'not_applicable'} else judgment['completeness'] == 'pass'})
    return {'schema_version': SCHEMA, 'independent_holdout_accepted': False,
            'metrics': _summarize(cases, legacy_applicable=legacy_applicable), 'cases': cases,
            'by_major': {major: _summarize([c for c in cases if c['major'] == major], legacy_applicable=legacy_applicable)
                         for major in sorted({c['major'] for c in cases})},
            'by_category': {category: _summarize([c for c in cases if c['category'] == category], legacy_applicable=legacy_applicable)
                            for category in sorted({c['category'] for c in cases})}}
