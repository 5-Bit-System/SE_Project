"""Fresh source-authored A7 cohort; no inference while choosing gold or tests."""

import importlib
import importlib.util
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from tools import evaluate_hus_a7 as evaluator


def builder():
    assert importlib.util.find_spec('tools.hus_a7_postfix_cases') is not None, 'Fresh A7 builder missing'
    return importlib.import_module('tools.hus_a7_postfix_cases')


@pytest.fixture(scope='module')
def fresh():
    return builder().build_pack()


def test_fresh_cohort_has_balance_new_wording_and_honest_exposure(fresh):
    assert evaluator.validate_structure(fresh)['questions'] == 48
    assert Counter(q['request']['major'] for q in fresh['questions']) == dict.fromkeys(evaluator.MAJORS, 12)
    assert len({q['question_id'] for q in fresh['questions']}) == 48
    assert fresh['exposure']['cohort_id'] == 'a7-postfix-20261112'
    assert fresh['holdout_eligible'] is False
    assert fresh['exposure']['actual_human_reviews'] == 0
    assert fresh['exposure']['runtime_and_sources_seen'] is True
    assert not any(c['normalized_exact_overlap_in_checked_inputs'] for c in fresh['exposure']['cases'])
    assert not any(c['prior_a7_target_identity_overlap'] for c in fresh['exposure']['cases'])


def test_new_course_topics_are_not_old_a7_tuning_targets(fresh):
    old = json.loads(Path('data/hus/evaluation/a7_v4_candidate_20261111_r2/pack.json').read_bytes())
    old_ids = {e['source_ref']['identity'] for e in old['evidence']}
    assert not old_ids & {e['source_ref']['identity'] for e in fresh['evidence']}
    expected = Counter(g['category'] for g in fresh['gold'])
    assert all(expected[f] == 12 for f in ('f1', 'f2', 'f3'))


def test_gold_is_bound_to_source_without_model_or_rag_execution(monkeypatch):
    from app.hus.answering import HUSAnswerer
    from app.hus.llm import HUSLLMClient
    from app.hus.retrieval import HUSRAGRetriever

    def forbidden(*a, **k):
        pytest.fail('Gold creation cannot call RAG/provider')

    monkeypatch.setattr(HUSAnswerer, 'answer', forbidden)
    monkeypatch.setattr(HUSRAGRetriever, 'search', forbidden)
    monkeypatch.setattr(HUSLLMClient, '__init__', forbidden)
    evaluator.check_sources(builder().build_pack())


@pytest.mark.parametrize('damage', ['scope', 'source_scope', 'value', 'facts_type', 'field', 'request_code'])
def test_fresh_gold_cannot_be_rebound_to_wrong_source(fresh, damage):
    pack = deepcopy(fresh)
    if damage == 'scope':
        pack['evidence'][0]['major'] = 'mathematics'
    elif damage == 'source_scope':
        pack['evidence'][0]['source_scope']['program_variant'] = 'standard'
    elif damage == 'value':
        pack['evidence'][0]['value'] = 'Invented quote'
    elif damage == 'field':
        pack['gold'][0]['expected_field'] = 'careers'
    elif damage == 'request_code':
        pack['questions'][3]['request']['question'] = 'Số tín chỉ MAT9999?'
    else:
        pack['gold'][3]['v2_expected_facts']['value'] = float(pack['gold'][3]['v2_expected_facts']['value'])
    with pytest.raises((ValueError, AssertionError)):
        evaluator.check_sources(pack)


def test_freeze_selects_new_cohort_before_sealing(tmp_path, monkeypatch, fresh):
    monkeypatch.setattr(evaluator, 'require_submission_settings', lambda: None)
    monkeypatch.setattr(evaluator, 'pins', lambda: {'fixed': 'code-data-config'})
    monkeypatch.setattr(evaluator, 'fresh_output', lambda folder, run: tmp_path)
    result = evaluator.freeze(tmp_path, cohort='postfix-20261112')
    from tools.hus_llm_measurement import read_sealed

    sealed = read_sealed(tmp_path)['pack.json']
    assert result['questions'] == 48 and sealed['questions'] == fresh['questions']
    assert sealed['pins'] == {'fixed': 'code-data-config'}
    assert sealed['exposure']['cohort_id'] == 'a7-postfix-20261112'


def test_unknown_cohort_cannot_silently_use_old_set(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluator, 'require_submission_settings', lambda: None)
    with pytest.raises(ValueError, match='cohort'):
        evaluator.freeze(tmp_path, cohort='unknown')


def test_freeze_refuses_known_wording_or_reused_a7_target(tmp_path, monkeypatch, fresh):
    module = builder()
    monkeypatch.setattr(evaluator, 'require_submission_settings', lambda: None)
    for field in ('normalized_exact_overlap_in_checked_inputs', 'prior_a7_target_identity_overlap'):
        bad = deepcopy(fresh)
        bad['exposure']['cases'][0][field] = True
        monkeypatch.setattr(module, 'build_pack', lambda: bad)
        with pytest.raises(ValueError, match='[Oo]verlap|[Rr]euse'):
            evaluator.freeze(tmp_path, cohort='postfix-20261112')
    assert not list(tmp_path.iterdir())


def test_pins_include_fresh_builder_and_its_contract_tests():
    pins = evaluator.pins()
    assert 'tools/hus_a7_postfix_cases.py' in pins['evaluators']
    assert 'tests/hus/test_a7_postfix.py' in pins['evaluators']
    assert pins['configuration']['index'] is None
    assert pins['configuration']['model_inference'] == 'not_run'
