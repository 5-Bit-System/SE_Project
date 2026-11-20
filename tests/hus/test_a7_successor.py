"""Source-first A7 after role repair; never certify independent acceptance."""
from collections import Counter
from copy import deepcopy

import pytest

from tools import evaluate_hus_a7 as evaluator

COHORT = 'request-role-20261113'


def test_successor_freezes_source_gold_without_prediction(monkeypatch, tmp_path):
    from app.hus.answering import HUSAnswerer
    from app.hus.llm import HUSLLMClient
    from app.hus.retrieval import HUSRAGRetriever
    from tools import hus_a7_successor_cases as builder

    def forbidden(*args, **kwargs):
        pytest.fail('Source authoring must not consult predictions or provider')

    monkeypatch.setattr(HUSAnswerer, 'answer', forbidden)
    monkeypatch.setattr(HUSRAGRetriever, 'search', forbidden)
    monkeypatch.setattr(HUSLLMClient, '__init__', forbidden)
    monkeypatch.setattr(evaluator, 'require_submission_settings', lambda: None)
    monkeypatch.setattr(evaluator, 'fresh_output', lambda folder, run: tmp_path)
    # Synthetic prior exposure isolates this fresh-freeze test from real sealed
    # packs added later; production authoring always scans all prior packs.
    monkeypatch.setattr(builder, 'prior_inputs', lambda: (
        set(), {}, {builder.F1['computer_science'][0][0]}))
    evaluator.freeze(tmp_path, cohort=COHORT)
    from tools.hus_llm_measurement import read_sealed
    pack = read_sealed(tmp_path)['pack.json']
    assert evaluator.validate_structure(pack)['questions'] == 48
    assert Counter(q['request']['major'] for q in pack['questions']) == dict.fromkeys(evaluator.MAJORS, 12)
    assert pack['frozen_at_utc'] and pack['pins'] == evaluator.pins()
    assert pack['exposure']['actual_human_reviews'] == 0 and pack['holdout_eligible'] is False
    assert any(c['prior_a7_target_identity_overlap'] for c in pack['exposure']['cases'])
    assert not any(c['normalized_exact_overlap_in_checked_inputs'] for c in pack['exposure']['cases'])
    assert all(c['prediction_seen_before_freeze'] is False for c in pack['exposure']['cases'])
    for path in ('tools/hus_a7_successor_cases.py', 'tests/hus/test_a7_successor.py'):
        assert path in pack['pins']['evaluators']
    evaluator.check_sources(pack)


def test_same_cohort_prior_inputs_remain_visible(tmp_path):
    import json

    from tools import hus_a7_successor_cases as builder

    prior = tmp_path / 'candidates/r1/pack.json'
    prior.parent.mkdir(parents=True)
    wording = builder.F1['computer_science'][0][1]
    identity = builder.F1['computer_science'][0][0]
    prior.write_text(json.dumps({
        'kind': evaluator.KIND, 'exposure': {'cohort_id': builder.COHORT},
        'questions': [{'request': {'question': wording}}],
        'evidence': [{'source_ref': {'identity': identity}}]}), encoding='utf8')
    known, hashes, targets = builder.prior_inputs(tmp_path)
    assert builder.normalized(wording) in known and identity in targets
    assert str(prior) in hashes


def test_successor_rejects_repeated_wording(monkeypatch, tmp_path):
    from tools import hus_a7_successor_cases as builder
    known, hashes, targets = builder.prior_inputs()
    monkeypatch.setattr(builder, 'prior_inputs', lambda: (
        known | {builder.normalized(builder.F1['computer_science'][0][1])}, hashes, targets))
    monkeypatch.setattr(evaluator, 'require_submission_settings', lambda: None)
    with pytest.raises(ValueError, match='Repeated wording'):
        evaluator.freeze(tmp_path, cohort=COHORT)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('damage', ['scope', 'quote', 'facts'])
def test_successor_rejects_changed_source_binding(damage):
    from tools import hus_a7_successor_cases as builder
    pack = deepcopy(builder.build_pack())
    if damage == 'scope':
        pack['evidence'][0]['source_scope']['program_variant'] = 'standard'
    elif damage == 'quote':
        pack['evidence'][0]['value'] = 'Invented source'
    else:
        pack['gold'][3]['v2_expected_facts']['value'] = 999
    with pytest.raises((AssertionError, ValueError)):
        evaluator.check_sources(pack)
