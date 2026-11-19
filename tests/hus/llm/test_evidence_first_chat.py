"""Evidence reaches the provider before extractive F1/F3 presentation is built."""
import json

import httpx
import pytest

from app.hus.answering import HUSAnswerer
from app.hus.chat import chat
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion
from tests.hus.llm.test_pipeline import completion, transport


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.fixture(autouse=True)
def config(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'offline-evidence-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'lexical')


REQUESTS = [
    {'major': 'computer_science', 'question': 'Ra trường KHMTTT có những hướng công việc nào?'},
    {'major': 'data_science', 'version': 'QD3569-2023', 'question': 'Số tín chỉ MAT2403?'},
    {'major': 'computer_science', 'version': 'QD3568-2023',
     'question': 'Mục tiêu MAT1204?', 'allow_generated_reference': True},
    {'major': 'computer_science', 'version': 'QD3568-2023',
     'question': 'Nội dung MAT1204: Tài liệu và cấu trúc bằng chứng?', 'allow_generated_reference': True},
]


@pytest.mark.parametrize('values', REQUESTS)
def test_prepared_evidence_generates_before_render_and_preserves_public_canonical(answerer, monkeypatch, values):
    request = HUSQuestion(**values, allow_llm_rewrite=True)
    baseline = answerer.answer(request)
    assert baseline.status == 'answered', baseline.reply
    plan = answerer.prepare_evidence(request)
    assert plan.evidence.citations and plan.evidence.facts == baseline.facts
    assert plan.materialize() == baseline
    if baseline.dataset != 'f2':
        assert plan.evidence.reply == ''
    from app.hus.answering import HUSPreparedAnswer

    materialized = []
    original = HUSPreparedAnswer.materialize

    def materialize(self):
        materialized.append(self)
        return original(self)

    monkeypatch.setattr(HUSPreparedAnswer, 'materialize', materialize)

    def provider(wire):
        assert not materialized, 'Canonical presentation was built before provider work'
        bundle = json.loads(json.loads(wire.content)['messages'][1]['content'])
        assert 'reply' not in bundle and 'offline-evidence-key' not in wire.content.decode()
        if baseline.dataset == 'f2':
            output = {'kind': 'facts', 'style': 'explain_source',
                      'fact_keys': list(bundle['facts']),
                      'citation_ids': [s['citation_id'] for s in bundle['sources']]}
        else:
            output = {'kind': 'rewrite_v3', 'items': [
                {'id': leaf['id'], 'text': leaf['text']}
                for source in bundle['sources'] for leaf in source['segments']]}
        return httpx.Response(200, json=completion(output))

    calls = transport(monkeypatch, provider)
    result = chat(request, answerer)
    assert len(calls) == len(materialized) == 1
    assert result.generation.used is True
    assert result.hus_answer == baseline
    assert '[1]' in result.reply
    if baseline.dataset == 'f2':
        assert result.reply.endswith(baseline.reply)
    if baseline.dataset == 'f3':
        assert all(c.display_label == 'kiến thức AI' for c in result.hus_answer.citations)
        assert all(w in result.reply for w in baseline.warnings)


@pytest.mark.parametrize('status', [503, 429])
def test_provider_error_materializes_exact_original_fallback(answerer, monkeypatch, status):
    request = HUSQuestion(**REQUESTS[0], allow_llm_rewrite=True)
    baseline = answerer.answer(request)
    calls = transport(monkeypatch, lambda wire: httpx.Response(status, json={}))
    result = chat(request, answerer)
    assert len(calls) == 1 and result.generation.used is False
    assert result.generation.http_status == status
    assert result.hus_answer == baseline and result.reply == baseline.reply


@pytest.mark.parametrize('values', [
    {'major': 'data_science', 'question': 'Số tín chỉ MAT9999?', 'version': 'QD3569-2023'},
    {'major': 'computer_science', 'question': 'Mục tiêu MAT1204?', 'version': 'QD3568-2023'},
    {'major': 'data_science', 'question': 'Môn đó có bao nhiêu tín chỉ?'},
    {'major': 'data_science', 'question': 'Xin chào'},
])
def test_missing_ambiguous_or_f3_opt_out_never_call_provider(answerer, monkeypatch, values):
    calls = transport(monkeypatch, lambda wire: pytest.fail('No eligible evidence'))
    result = chat(HUSQuestion(**values, allow_llm_rewrite=True), answerer)
    assert not calls and result.generation.used is False


def test_flag_off_retains_exact_legacy_response_without_provider(answerer, monkeypatch):
    calls = transport(monkeypatch, lambda wire: pytest.fail('Server flag off'))
    request = HUSQuestion(**REQUESTS[0])
    baseline = chat(request, answerer).model_dump(mode='json')
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    enabled_request = request.model_copy(update={'allow_llm_rewrite': True})
    assert chat(enabled_request, answerer).model_dump(mode='json') == baseline
    assert not calls
