"""L6 readiness is a read-only evidence check, never a flag-changing action."""

from copy import deepcopy
from pathlib import Path

import pytest


def checker():
    from tools import check_hus_llm_readiness
    return check_hus_llm_readiness


@pytest.fixture
def candidate(monkeypatch):
    c = checker()
    rows = [{'question_id': f'case-{family}', 'b_entailment': 'pass', 'b_completeness': 'pass',
             'readability': 'better' if family == 'f1' else 'same'} for family in ('f1', 'f2', 'f3')]
    saved = {'prepared.json': {'pins': {'synthetic': 'fixed'}},
        'review.json': {'cases': rows},
        'observations.json': [{'question_id': row['question_id'], 'b': {'generation': {'used': True}}} for row in rows],
        'report.json': {'kind': 'review_score', 'semantic_review': 'exact_response_bound_ai',
            'base_url': c.BASE_URL,
            'transport': 'live_google', 'collection_complete': True, 'requested_model': c.MODEL,
            'actual_human_reviews': 0, 'semantic': {'reviewer_kind': 'ai',
                'all_positive': {'count': 3, 'b_entailment_pass': 3, 'b_completeness_pass': 3},
                'used_only': {'count': 3, 'b_entailment_pass': 3, 'b_completeness_pass': 3}},
            'metrics': {'eligible': 3, 'used': 3, 'fallback': 0, 'provider_requests': 3,
                'eligible_not_attempted': 0, 'source_audit_failures': 0, 'control_status_mismatches': 0,
                'baseline_false_refusals': 0, 'actual_models': {c.MODEL: 3}, 'token_usage': {'total_tokens': 90},
                'by_family': {f: {'used': 1, 'eligible': 1} for f in ('f1', 'f2', 'f3')},
                'latency': {'rewrite_used': {'count': 3, 'p50_ms': 1000, 'p95_ms': 3000}}}}}
    # This is a unit stub of the already-verified L5 loader. The integration test
    # below uses the actual sealed report and replay without changing its bytes.
    monkeypatch.setattr(c, 'replay', lambda folder: {'reproduced': True})
    monkeypatch.setattr(c, 'read_sealed', lambda folder: deepcopy(saved))
    monkeypatch.setattr(c, 'current_pins', lambda: {'synthetic': 'fixed'})
    monkeypatch.setattr(c, 'digest', lambda path: '0' * 64)
    return c, saved


def test_current_sealed_l5_blocks_default_activation_without_network(monkeypatch):
    from app.hus.llm import HUSLLMClient
    from app.hus.rag_loader import HUSRAGData

    c = checker()
    monkeypatch.setattr(HUSLLMClient, '__init__', lambda *a, **k: pytest.fail('Readiness called provider'))
    monkeypatch.setattr(HUSRAGData, 'load_current', lambda *a, **k: pytest.fail('Readiness ran retrieval'))
    result = c.assess(Path('data/hus/evaluation/runs/llm_l5_ai_review_20261110_r1'))
    assert result['eligible_for_manual_acceptance'] is False
    assert result['recommended_action'] == 'keep_disabled'
    assert result['blocked_cases'] == [{'question_id': 'DEV-Q025', 'reason': 'incomplete_generated_answer'}]
    assert result['used'] == 19 and result['fallback'] == 5
    assert result['activation_performed'] is False
    assert result['new_provider_calls'] == result['new_retrieval_calls'] == 0


def test_passing_evidence_only_qualifies_for_manual_acceptance(candidate, monkeypatch):
    import os

    c, _ = candidate
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'private-key-must-not-be-read-or-returned')
    result = c.assess(Path('synthetic'))
    assert result['eligible_for_manual_acceptance'] is True
    assert result['recommended_action'] == 'operator_review_required'
    assert result['activation_performed'] is False
    assert os.environ['HUS_LLM_ENABLED'] == 'false'
    assert 'private-key' not in str(result)


@pytest.mark.parametrize('case,reason', [
    ('synthetic', 'no_live_measurement'), ('pending', 'content_review_missing'),
    ('incomplete_collection', 'collection_incomplete'), ('all_fallback', 'no_generated_output'),
    ('missing_f3', 'no_used_output_f3'), ('no_gain', 'no_supported_readability_gain'),
    ('source_error', 'source_audit_failed'), ('control_error', 'control_contract_failed'),
    ('false_refusal', 'positive_answer_missing'), ('wrong_model', 'requested_model_changed'),
    ('bad_latency', 'latency_unavailable'), ('used_entailment', 'generated_entailment_failed'),
])
def test_failed_evidence_never_qualifies(candidate, case, reason):
    c, saved = candidate
    report, metrics = saved['report.json'], saved['report.json']['metrics']
    if case == 'synthetic':
        report['transport'] = 'synthetic_transport'
    elif case == 'pending':
        report['kind'], report['semantic_review'] = 'measurement', 'pending'
    elif case == 'incomplete_collection':
        report['collection_complete'] = False
    elif case == 'all_fallback':
        metrics['used'], metrics['fallback'] = 0, 3
        report['semantic']['used_only']['count'] = 0
        for o in saved['observations.json']:
            o['b']['generation']['used'] = False
    elif case == 'missing_f3':
        metrics['by_family']['f3']['used'] = 0
    elif case == 'no_gain':
        for row in saved['review.json']['cases']:
            row['readability'] = 'same'
    elif case == 'source_error':
        metrics['source_audit_failures'] = 1
    elif case == 'control_error':
        metrics['control_status_mismatches'] = 1
    elif case == 'false_refusal':
        metrics['baseline_false_refusals'] = 1
    elif case == 'wrong_model':
        report['requested_model'] = 'another-model'
    elif case == 'bad_latency':
        metrics['latency']['rewrite_used']['p95_ms'] = None
    else:
        report['semantic']['used_only']['b_entailment_pass'] = 2
        saved['review.json']['cases'][0]['b_entailment'] = 'fail'
    result = c.assess(Path('synthetic'))
    assert result['eligible_for_manual_acceptance'] is False
    assert reason in result['reasons']


def test_changed_code_or_source_pins_block_reuse(candidate, monkeypatch):
    c, _ = candidate
    monkeypatch.setattr(c, 'current_pins', lambda: {'synthetic': 'changed'})
    result = c.assess(Path('synthetic'))
    assert result['eligible_for_manual_acceptance'] is False
    assert 'pins_changed' in result['reasons']


def test_corrupt_saved_evidence_is_rejected_before_a_decision(candidate, monkeypatch):
    c, _ = candidate

    def fail(folder):
        raise ValueError('Saved evidence hash mismatch')

    monkeypatch.setattr(c, 'replay', fail)
    with pytest.raises(ValueError, match='hash'):
        c.assess(Path('synthetic'))


@pytest.mark.parametrize('dimension,reason', [('entailment', 'unsupported_fallback_answer'),
                                            ('completeness', 'incomplete_fallback_answer')])
def test_failed_fallback_review_cannot_qualify_even_when_every_generated_answer_passes(candidate, dimension, reason):
    c, saved = candidate
    saved['report.json']['metrics'].update(eligible=4, fallback=1, provider_requests=4)
    final = saved['report.json']['semantic']['all_positive']
    final.update(count=4, b_entailment_pass=4, b_completeness_pass=4)
    final['b_' + dimension + '_pass'] = 3
    saved['review.json']['cases'].append({'question_id': 'bad-fallback',
        'b_entailment': 'fail' if dimension == 'entailment' else 'pass',
        'b_completeness': 'fail' if dimension == 'completeness' else 'pass', 'readability': 'same'})
    saved['observations.json'].append({'question_id': 'bad-fallback',
                                     'b': {'generation': {'used': False}}})
    result = c.assess(Path('synthetic'))
    assert result['eligible_for_manual_acceptance'] is False
    assert {'question_id': 'bad-fallback', 'reason': reason} in result['blocked_cases']
    assert result['used'] == 3 and result['fallback'] == 1
