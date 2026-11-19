"""Source-first cohort after bounded repair; no policy relaxation or predictions."""
import importlib
import json
import socket
from collections import Counter
from copy import deepcopy

import pytest

from tools import evaluate_hus_a7 as evaluator

COHORT = 'bounded-request-20261113'


def builder():
    return importlib.import_module('tools.hus_a7_bounded_cases')


def test_balanced_source_only_candidate_records_exposure_and_held_contracts(monkeypatch):
    from app.hus.answering import HUSAnswerer
    from app.hus.llm import HUSLLMClient
    from app.hus.retrieval import HUSRAGRetriever

    def forbidden(*args, **kwargs):
        pytest.fail('Source authoring must not infer, retrieve or connect')
    for cls, method in ((HUSAnswerer, 'answer'), (HUSRAGRetriever, 'search'),
                        (HUSLLMClient, '__init__'), (socket.socket, 'connect')):
        monkeypatch.setattr(cls, method, forbidden)
    module = builder()
    known, inputs, targets, literal_inputs = module.prior_exposure()
    # A real candidate created after this test's first run is valid prior
    # exposure. Isolate the shape/source test; repeat-freeze rejection below
    # exercises production overlap handling without hiding that candidate.
    monkeypatch.setattr(module, 'prior_exposure', lambda: (set(), inputs, targets, literal_inputs))
    pack = module.build_pack()
    assert evaluator.validate_structure(pack)['questions'] == 48
    evaluator.check_sources(pack)
    assert Counter(q['request']['major'] for q in pack['questions']) == dict.fromkeys(evaluator.MAJORS, 12)
    assert len(pack['evidence']) == 36 and pack['holdout_eligible'] is False
    assert pack['exposure']['actual_human_reviews'] == 0
    assert pack['exposure']['regression_literal_inputs_sha256']
    assert not any(c['normalized_exact_overlap_in_checked_inputs'] for c in pack['exposure']['cases'])
    assert not any(c['prediction_seen_before_freeze'] for c in pack['exposure']['cases'])
    assert pack['held_contracts'] == {
        'A7R-Q025': 'unresolved_source_branch; no new runtime behavior',
        'A7R-Q037': 'history_plus_orientation_not_proven; no dropped_requirement',
        'DEV-Q002': 'enumeration_vs_comparison_unresolved; old assertion preserved'}
    assert all(g['review_contract'] for g in pack['gold'])
    assert pack['exposure']['eligible_for_independent_acceptance'] is False


def test_new_freeze_pins_builder_test_timestamp_and_prediction_free_inputs(monkeypatch, tmp_path):
    module = builder()
    known, inputs, targets, literal_inputs = module.prior_exposure()
    monkeypatch.setattr(module, 'prior_exposure', lambda: (set(), inputs, targets, literal_inputs))
    monkeypatch.setattr(evaluator, 'require_submission_settings', lambda: None)
    monkeypatch.setattr(evaluator, 'fresh_output', lambda folder, run: tmp_path)
    evaluator.freeze(tmp_path, cohort=COHORT)
    from tools.hus_llm_measurement import read_sealed
    pack = read_sealed(tmp_path)['pack.json']
    assert pack['pins'] == evaluator.pins() and pack['frozen_at_utc']
    assert pack['submission']['llm_enabled'] is False and pack['submission']['retrieval'] == 'lexical'
    for name in ('tools/hus_a7_bounded_cases.py', 'tests/hus/test_a7_bounded_candidate.py'):
        assert name in pack['pins']['evaluators']


def test_same_candidate_wording_cannot_be_frozen_again(monkeypatch, tmp_path):
    module = builder()
    known, inputs, targets, literals = module.prior_exposure()
    wording = module.F1['computer_science'][0][1]
    monkeypatch.setattr(module, 'prior_exposure', lambda: (
        known | {module.normalized(wording)}, inputs, targets, literals))
    monkeypatch.setattr(evaluator, 'require_submission_settings', lambda: None)
    with pytest.raises(ValueError, match='Repeated wording'):
        evaluator.freeze(tmp_path, cohort=COHORT)
    assert not list(tmp_path.iterdir())


def test_prior_exposure_includes_same_cohort_and_regression_literals(tmp_path):
    module = builder()
    prior = tmp_path / 'evaluation/candidates/r1/pack.json'
    prior.parent.mkdir(parents=True)
    prior.write_text(json.dumps({'kind': evaluator.KIND,
        'questions': [{'request': {'question': 'Earlier frozen request'}}],
        'evidence': [{'source_ref': {'identity': 'same-cohort-target'}}]}), encoding='utf-8')
    tests = tmp_path / 'tests'
    tests.mkdir()
    regression = tests / 'test_regression.py'
    regression.write_text('WORDING = "Exposed regression request"\n', encoding='utf-8')
    known, inputs, targets, literals = module.prior_exposure(prior.parents[2], tests)
    assert module.normalized('Earlier frozen request') in known
    assert module.normalized('Exposed regression request') in known
    assert 'same-cohort-target' in targets
    assert str(regression) in inputs and str(regression) in literals


@pytest.mark.parametrize('damage', ['scope', 'quote', 'fact_type', 'course_request'])
def test_candidate_cannot_change_source_scope_quote_facts_or_course(damage):
    pack = deepcopy(builder().build_pack())
    if damage == 'scope':
        pack['evidence'][0]['source_scope']['program_variant'] = 'standard'
    elif damage == 'quote':
        pack['evidence'][0]['value'] = 'Invented target'
    elif damage == 'fact_type':
        pack['gold'][3]['v2_expected_facts']['value'] = str(pack['gold'][3]['v2_expected_facts']['value'])
    else:
        pack['questions'][3]['request']['question'] = 'Credits of MAT9999?'
    with pytest.raises((AssertionError, ValueError)):
        evaluator.check_sources(pack)
