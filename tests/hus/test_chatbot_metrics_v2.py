"""Evaluator changes must not hide routing misses, bad facts or unreviewed semantics."""

import importlib
import importlib.util
from copy import deepcopy

import pytest

from tests.hus.test_rag_evaluation import sample


def metrics():
    assert importlib.util.find_spec('tools.hus_rag_metrics_v2') is not None, 'V2 scorer is not implemented'
    return importlib.import_module('tools.hus_rag_metrics_v2')


def fixture():
    q, g, e, o = sample()
    o['latency_ms'] = 12.5
    o['routing_observation'] = {'dataset': 'f3', 'field': 'content', 'stage': 'classifier_before_scope_and_evidence_guards'}
    o['retrieval_calls'][0]['parameters'] = {'dataset': 'f3', 'field': 'content', 'major': 'data_science',
                                              'version': 'v1', 'course_code': 'MAT9998', 'top_k': 5}
    o['response']['hus_answer']['reply'] = 'Một đoạn nguồn.'
    o['response']['hus_answer']['citations'][0]['quote'] = 'Một đoạn nguồn.'
    e['value'] = 'Một đoạn nguồn.'
    audit = {'question_id': q['question_id'], 'passed': True}
    return [q], [g], [e], [o], [audit]


def score(data, review=None):
    return metrics().evaluate(*data, review=review)


def review_for(data):
    m = metrics()
    qs, gold, _, observations, audits = data
    return [{'question_id': q['question_id'], 'reviewer_kind': 'ai', 'reviewer': 'AI test reviewer',
             'request_sha256': m.digest_json(q['request']), 'response_sha256': m.digest_json(o['response']),
             'gold_sha256': m.digest_json(g), 'audit_sha256': m.digest_json(a),
             'entailment': 'pass', 'completeness': 'pass', 'notes': 'Read the question, answer and pinned source.'}
            for q, g, o, a in zip(qs, gold, observations, audits, strict=True)]


def test_no_search_is_a_miss_not_a_smaller_denominator():
    data = fixture()
    data[3][0]['retrieval_calls'] = []
    data[3][0]['response']['hus_answer'].update(status='no_information', citations=[])
    report = score(data)['metrics']
    assert report['retrieval']['routed_recall_at_5']['value'] == 0
    assert report['retrieval']['routed_recall_at_5']['denominator'] == 1
    assert report['retrieval']['conditional_recall_at_5']['value'] is None
    assert report['abstention']['false_abstention']['numerator'] == 1


def test_http_error_stays_a_failure_but_is_not_false_refusal():
    data = fixture()
    data[3][0].update(http_status=503, response={}, retrieval_calls=[])
    result = score(data)['metrics']
    assert result['retrieval']['routed_recall_at_5']['denominator'] == 1
    assert result['abstention']['http_errors'] == 1
    assert result['abstention']['false_abstention']['numerator'] == 0


def test_real_top_five_and_scope_are_both_required():
    data = fixture()
    hit = data[3][0]['retrieval_calls'][0]['hits'][0]
    hit['version'] = 'foreign'
    assert score(data)['metrics']['retrieval']['routed_recall_at_5']['value'] == 0
    assert score(data)['metrics']['filters']['errors']['version'] == 1
    hit['version'] = 'v1'
    data[3][0]['retrieval_calls'][0]['hits'] = [dict(hit, chunk_id=f'x{i}') for i in range(5)] + [hit]
    assert score(data)['metrics']['retrieval']['routed_recall_at_5']['value'] == 0


def test_quote_coverage_is_not_semantic_entailment():
    result = score(fixture())['metrics']['citation_source_support']
    assert result['gold_quote_coverage_proxy']['value'] == 1
    assert result['ai_entailment'] is None and result['ai_completeness'] is None


@pytest.mark.parametrize('tamper', ['response', 'gold', 'request', 'audit', 'reviewer', 'duplicate', 'omit'])
def test_semantic_review_is_strictly_bound_and_cannot_claim_human(tamper):
    data = fixture()
    review = review_for(data)
    if tamper == 'response':
        data[3][0]['response']['hus_answer']['reply'] = 'Different answer'
    elif tamper == 'gold':
        data[1][0]['expected_answer'] = 'Different expected meaning'
    elif tamper == 'request':
        data[0][0]['request']['question'] = 'Other question'
    elif tamper == 'audit':
        data[4][0]['passed'] = False
    elif tamper == 'reviewer':
        review[0]['reviewer_kind'] = 'human'
    elif tamper == 'duplicate':
        review += deepcopy(review)
    else:
        review = []
    with pytest.raises(ValueError):
        score(data, review)


def test_ai_review_can_mark_incomplete_despite_exact_gold_quote():
    data = fixture()
    review = review_for(data)
    review[0]['completeness'] = 'fail'
    result = score(data, review)['metrics']['citation_source_support']
    assert result['ai_entailment']['value'] == 1
    assert result['ai_completeness']['value'] == 0
    assert result['reviewer_kind'] == 'ai' and result['actual_human_reviews'] == 0


def test_unknown_f2_preserves_raw_null_and_legacy_mismatch():
    data = fixture()
    q, g, e, o, audit = [item[0] for item in data]
    g.update(category='f2', expected_dataset='f2', expected_field='prerequisites',
             expected_facts={'prerequisites.raw_variants': []})
    e['source_ref'] = {'identity_field': 'record_id', 'identity': 'program:MAT9998'}
    o['response']['hus_answer'].update(dataset='f2', facts={'field': 'prerequisites', 'course_code': 'MAT9998',
                                     'value': [None], 'prerequisite_status': 'unknown'})
    o['response']['hus_answer']['citations'][0].update(dataset='f2', evidence_kind='pdf', metadata={
        'provenance': {'portable_record': {'record_id': 'program:MAT9998', 'major': 'data_science',
                                          'scope': {'curriculum_version': 'v1'}}}})
    audit['source_f2_contract'] = {'field': 'prerequisites', 'course_code': 'MAT9998',
                                   'value': [None], 'prerequisite_status': 'unknown'}
    report = score(data)['metrics']
    assert report['raw_legacy']['f2_lookup_success']['value'] == 0
    assert report['f2']['source_contract_success']['value'] == 1
    o['response']['hus_answer']['facts']['value'] = []
    assert score(data)['metrics']['f2']['source_contract_success']['value'] == 0


def test_f2_source_contract_checks_all_requested_fields():
    data = fixture()
    data[1][0].update(category='f2', expected_dataset='f2', expected_field='group_rules', expected_facts={})
    data[4][0]['source_f2_contract'] = {'field': 'group_rules', 'value': {'min_credits_if_selected': 5, 'offered_credits': 13}}
    data[3][0]['response']['hus_answer'].update(dataset='f2', facts={'field': 'group_rules', 'value': {'min_credits_if_selected': 5}})
    assert score(data)['metrics']['f2']['source_contract_success']['value'] == 0


def test_filter_parameters_are_observed_even_when_search_returns_no_hits():
    m = metrics()
    request = {'question': 'MAT9998 content', 'major': 'data_science', 'version': 'v1', 'program_variant': 'standard'}
    calls = [{'parameters': {'dataset': 'f3', 'major': 'foreign', 'version': 'v999', 'course_code': 'MAT1111',
                             'program_variant': 'talent', 'allow_generated': True}, 'hits': []}]
    errors = m.filter_errors(request, {}, calls)
    assert errors['major'] and errors['version'] and errors['course_code']
    assert errors['program_variant'] and errors['ai_opt_in']


def test_latency_nearest_rank_is_explicit_and_bad_samples_are_rejected():
    m = metrics()
    assert m.latency_stats([1, 2, 3, 4, 100]) == {'count': 5, 'p50_ms': 3, 'p95_ms': 100, 'min_ms': 1, 'max_ms': 100}
    assert m.latency_stats([])['p50_ms'] is None
    for value in [-1, float('nan'), float('inf')]:
        with pytest.raises(ValueError):
            m.latency_stats([value])
