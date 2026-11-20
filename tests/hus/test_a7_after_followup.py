"""A different frozen source-authored cohort; never query RAG to choose its gold."""

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from tools import evaluate_hus_a7 as evaluator
from tools import hus_a7_after_followup_cases as builder
from tools.hus_llm_measurement import read_sealed


@pytest.fixture(scope='module')
def fresh():
    return builder.build_pack()


def test_family_major_balance_and_honest_exposure(fresh):
    assert evaluator.validate_structure(fresh)['questions'] == 48
    assert Counter(q['request']['major'] for q in fresh['questions']) == dict.fromkeys(evaluator.MAJORS, 12)
    assert Counter(g['category'] for g in fresh['gold'])['f1'] == 12
    assert Counter(g['category'] for g in fresh['gold'])['f2'] == 12
    assert Counter(g['category'] for g in fresh['gold'])['f3'] == 12
    assert fresh['exposure']['planned_reviewer'] == {'kind': 'ai', 'identity': 'root', 'blind': False, 'independent': False}
    assert fresh['holdout_eligible'] is fresh['exposure']['eligible_for_independent_acceptance'] is False
    assert fresh['exposure']['actual_human_reviews'] == 0
    assert not any(c['prediction_seen_before_freeze'] for c in fresh['exposure']['cases'])


def test_wording_and_target_ids_differ_from_all_checked_prior_a7(fresh):
    _, inputs, prior = builder.prior_inputs()
    assert inputs and any('a7_postfix_' in name for name in inputs)
    assert all(not c['normalized_exact_overlap_in_checked_inputs'] for c in fresh['exposure']['cases'])
    assert all(not c['prior_a7_target_identity_overlap'] for c in fresh['exposure']['cases'])
    assert not prior & {e['source_ref']['identity'] for e in fresh['evidence']}
    assert 'semantic novelty' in fresh['exposure']['limits']


def test_source_gold_builder_cannot_call_answerer_retrieval_or_provider(monkeypatch):
    from app.hus.answering import HUSAnswerer
    from app.hus.llm import HUSLLMClient
    from app.hus.retrieval import HUSRAGRetriever

    def forbidden(*args, **kwargs):
        pytest.fail('Gold/freeze must not execute RAG or provider')

    monkeypatch.setattr(HUSAnswerer, 'answer', forbidden)
    monkeypatch.setattr(HUSRAGRetriever, 'search', forbidden)
    monkeypatch.setattr(HUSLLMClient, '__init__', forbidden)
    evaluator.check_sources(builder.build_pack())


@pytest.mark.parametrize('damage', ['scope', 'variant', 'field', 'quote', 'facts_type', 'code'])
def test_source_evidence_or_canonical_binding_cannot_be_relabelled(fresh, damage):
    pack = deepcopy(fresh)
    if damage == 'scope':
        pack['evidence'][0]['major'] = 'mathematics'
    elif damage == 'variant':
        pack['evidence'][0]['source_scope']['program_variant'] = 'standard'
    elif damage == 'field':
        pack['gold'][0]['expected_field'] = 'careers'
    elif damage == 'quote':
        pack['evidence'][0]['value'] = 'Invented content'
    elif damage == 'facts_type':
        pack['gold'][3]['v2_expected_facts']['value'] = float(pack['gold'][3]['v2_expected_facts']['value'])
    else:
        pack['questions'][3]['request']['question'] = 'Số tín chỉ MAT9999?'
    with pytest.raises((ValueError, AssertionError)):
        evaluator.check_sources(pack)


def test_freeze_pins_source_gold_time_and_reviewer_before_any_inference(tmp_path, monkeypatch, fresh):
    monkeypatch.setattr(evaluator, 'require_submission_settings', lambda: None)
    monkeypatch.setattr(evaluator, 'pins', lambda: {'frozen': 'runtime-data-config'})
    monkeypatch.setattr(evaluator, 'fresh_output', lambda folder, run: tmp_path)
    start = datetime.now(timezone.utc).isoformat()
    result = evaluator.freeze(tmp_path, cohort='after-followup-20261112')
    end = datetime.now(timezone.utc).isoformat()
    saved = read_sealed(tmp_path)['pack.json']
    assert result['questions'] == 48 and saved['questions'] == fresh['questions']
    assert saved['gold'] == fresh['gold'] and saved['pins'] == {'frozen': 'runtime-data-config'}
    assert start <= saved['frozen_at_utc'] <= end
    assert saved['exposure']['cohort_id'] == builder.COHORT


@pytest.mark.parametrize('field', ['normalized_exact_overlap_in_checked_inputs', 'prior_a7_target_identity_overlap'])
def test_freeze_refuses_known_wording_or_old_target_without_writing(tmp_path, monkeypatch, fresh, field):
    bad = deepcopy(fresh)
    bad['exposure']['cases'][0][field] = True
    monkeypatch.setattr(builder, 'build_pack', lambda: bad)
    monkeypatch.setattr(evaluator, 'require_submission_settings', lambda: None)
    monkeypatch.setattr(evaluator, 'pins', lambda: {})
    with pytest.raises(ValueError, match='[Oo]verlap|[Rr]euse'):
        evaluator.freeze(tmp_path, cohort='after-followup-20261112')
    assert not list(tmp_path.iterdir())


def test_measurement_pins_include_new_builder_and_contract_tests():
    pins = evaluator.pins()
    assert 'tools/hus_a7_after_followup_cases.py' in pins['evaluators']
    assert 'tests/hus/test_a7_after_followup.py' in pins['evaluators']
    assert pins['configuration']['index'] is None and pins['configuration']['actual_model'] is None
    assert pins['configuration']['llm_enabled'] is False
