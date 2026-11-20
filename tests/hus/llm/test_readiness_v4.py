"""V4 readiness must bind its own pack, not legacy evidence or current prompts."""

from copy import deepcopy
from pathlib import Path

import pytest

from tools import check_hus_llm_readiness as checker

RUN = Path('data/hus/evaluation/runs/llm_l5_v4_ai_review_20261111_r1')


def test_historical_v4_is_assessed_without_provider_retrieval_or_current_prompt_validation(monkeypatch):
    from app.hus.llm import HUSLLMClient
    from app.hus.rag_loader import HUSRAGData
    from tools import evaluate_hus_llm_v4 as v4

    def forbidden(*args, **kwargs):
        pytest.fail('Readiness must use only sealed responses and source files')

    monkeypatch.setattr(HUSLLMClient, '__init__', forbidden)
    monkeypatch.setattr(HUSRAGData, 'load_current', forbidden)
    monkeypatch.setattr(v4, 'validate_prepared', forbidden)
    monkeypatch.setattr(checker, 'current_pins', forbidden)
    result = checker.assess(RUN)
    assert result['evidence_version'] == 'v4'
    assert result['source_pack'] == 'data/hus/evaluation/llm_v4_dev_20261111_r1'
    assert result['source_release']['release_id'] == 'hus-data-20261111-v4'
    assert result['used'] == 16 and result['fallback'] == 8
    assert result['supported_complete_readability_gains'] == 2
    assert {'pins_changed', 'readability_regressed'} <= set(result['reasons'])
    assert result['recommended_action'] == 'keep_disabled'
    assert result['new_provider_calls'] == result['new_retrieval_calls'] == 0
    assert result['activation_performed'] is False


@pytest.mark.parametrize('change', ['manifest', 'release', 'case', 'effective_request',
                                    'missing_provenance', 'unknown_kind'])
def test_v4_pack_binding_tampering_is_rejected_before_decision(monkeypatch, change):
    saved = deepcopy(checker.read_sealed(RUN))
    doc = saved['prepared.json']
    if change == 'manifest':
        doc['provenance']['source_pack_manifest_sha256'] = '0' * 64
    elif change == 'release':
        doc['provenance']['release']['release_id'] = 'other'
    elif change == 'case':
        doc['records'][0]['request']['question'] = 'different frozen question'
    elif change == 'effective_request':
        doc['records'][0]['effective_request']['question'] = 'different effective intent'
    elif change == 'missing_provenance':
        doc['provenance'].pop('source_pack')
    else:
        doc['provenance']['kind'] = 'unrecognized'
    monkeypatch.setattr(checker, 'read_sealed', lambda path: saved)
    monkeypatch.setattr(checker, 'replay', lambda path: {'reproduced': True})
    with pytest.raises(ValueError, match='[Vv]4|pack|cohort'):
        checker.assess(RUN)


def test_matching_v4_pins_still_cannot_hide_readability_regression(monkeypatch):
    from tools import evaluate_hus_llm_v4 as v4

    saved = checker.read_sealed(RUN)
    seen = []

    def pins(pack):
        seen.append(pack.relative_to(checker.ROOT).as_posix())
        return saved['prepared.json']['pins']

    monkeypatch.setattr(v4, 'current_pins', pins)
    result = checker.assess(RUN)
    assert seen == ['data/hus/evaluation/llm_v4_dev_20261111_r1']
    assert 'pins_changed' not in result['reasons']
    assert 'readability_regressed' in result['reasons']
    assert result['recommended_action'] == 'keep_disabled'


def test_changed_observed_model_blocks_even_if_requested_model_matches(monkeypatch):
    saved = deepcopy(checker.read_sealed(RUN))
    saved['report.json']['metrics']['actual_models'] = {'other-resolved-model': 24}
    monkeypatch.setattr(checker, 'read_sealed', lambda path: saved)
    monkeypatch.setattr(checker, 'replay', lambda path: {'reproduced': True})
    assert 'observed_model_changed' in checker.assess(RUN)['reasons']
