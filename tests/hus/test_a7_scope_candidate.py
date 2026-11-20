"""Successor candidate freeze is source-only and declares reused/exposed evidence."""
from collections import Counter
from copy import deepcopy

import pytest

from tools import evaluate_hus_a7 as evaluator
from tools import hus_a7_scope_cases as builder
from tools.hus_llm_measurement import read_sealed


@pytest.fixture(scope='module')
def candidate():
    return builder.build_pack()


def test_candidate_is_balanced_and_exposure_is_not_independent(candidate):
    assert evaluator.validate_structure(candidate)['questions'] == 48
    assert Counter(q['request']['major'] for q in candidate['questions']) == dict.fromkeys(evaluator.MAJORS, 12)
    assert not any(c['normalized_exact_overlap_in_checked_inputs'] for c in candidate['exposure']['cases'])
    assert any(c['prior_a7_target_identity_overlap'] for c in candidate['exposure']['cases'])
    assert candidate['holdout_eligible'] is False and candidate['exposure']['actual_human_reviews'] == 0
    assert all(c['prediction_seen_before_freeze'] is False for c in candidate['exposure']['cases'])
    assert candidate['source_edition_policy']['mode'] == 'source-scoped F1; no alternative equivalence assumed'


def test_source_gold_and_freeze_never_call_answerer_retriever_or_provider(monkeypatch, tmp_path):
    from app.hus.answering import HUSAnswerer
    from app.hus.llm import HUSLLMClient
    from app.hus.retrieval import HUSRAGRetriever

    def forbidden(*a, **k):
        pytest.fail('Candidate authoring/freeze must not use prediction')

    monkeypatch.setattr(HUSAnswerer, 'answer', forbidden)
    monkeypatch.setattr(HUSRAGRetriever, 'search', forbidden)
    monkeypatch.setattr(HUSLLMClient, '__init__', forbidden)
    monkeypatch.setattr(evaluator, 'require_submission_settings', lambda: None)
    monkeypatch.setattr(evaluator, 'fresh_output', lambda folder, run: tmp_path)
    evaluator.freeze(tmp_path, cohort='scope-assessment-20261113')
    frozen = read_sealed(tmp_path)['pack.json']
    assert frozen['frozen_at_utc'] and frozen['pins'] == evaluator.pins()
    evaluator.check_sources(frozen)


@pytest.mark.parametrize('damage', ['quote', 'scope', 'facts'])
def test_candidate_cannot_relabel_source_or_canonical_fact(candidate, damage):
    changed = deepcopy(candidate)
    if damage == 'quote':
        changed['evidence'][0]['value'] = 'Invented list'
    elif damage == 'scope':
        changed['evidence'][0]['source_scope']['program_variant'] = 'standard'
    else:
        changed['gold'][3]['v2_expected_facts']['value'] = 999
    with pytest.raises((AssertionError, ValueError)):
        evaluator.check_sources(changed)
