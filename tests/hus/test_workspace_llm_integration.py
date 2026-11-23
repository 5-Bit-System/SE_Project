"""Workspace API uses the new Gemini pipeline only after user opt-in."""

from contextlib import closing

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.services.hus_service import get_hus_answerer
from tests.hus.llm.test_pipeline import transport
from tests.hus.llm.test_rollback import reply_from_bundle


def test_workspace_opt_in_runs_grounded_pipeline_and_preserves_sources(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-workspace-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_LLM_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai')
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'lexical')
    monkeypatch.setenv('HUS_ANSWER_POLICY', 'legacy')
    monkeypatch.delenv('HUS_RAG_ROOT', raising=False)

    def reject_legacy_provider(*args, **kwargs):
        raise AssertionError('Explicit Workspace choices must bypass the legacy provider')

    monkeypatch.setattr('app.hus.chat.generate_grounded_answer', reject_legacy_provider)
    calls = transport(monkeypatch, reply_from_bundle)
    payload = {
        'question': 'MAT3533 có bao nhiêu tín chỉ?',
        'major': 'data_science',
        'version': 'QD3569-2023',
    }
    get_hus_answerer.cache_clear()
    try:
        with closing(TestClient(app)) as client:
            config = client.get('/hus/config')
            assert config.status_code == 200
            assert config.json()['llm_rewrite_available'] is True
            assert config.json()['release_id'] == 'hus-data-20261111-v4'
            assert 'synthetic-workspace-key' not in config.text

            original = client.post('/hus/chat', json={**payload, 'allow_llm_rewrite': False}).json()
            assert original['hus_answer']['status'] == 'answered'
            assert original['hus_answer']['citations']
            assert 'generation' not in original and calls == []

            identity = client.post('/hus/chat', json={
                **payload, 'question': 'bạn là gemini à', 'allow_llm_rewrite': True,
            }).json()
            assert identity['mode'] == 'basic_chat' and 'Trợ lý HUS' in identity['reply']
            assert 'generation' not in identity and calls == []

            rewritten = client.post('/hus/chat', json={**payload, 'allow_llm_rewrite': True}).json()
            assert rewritten['generation']['used'] is True
            assert rewritten['hus_answer'] == original['hus_answer']
            assert len(calls) == 1
            assert calls[0].url.host == 'generativelanguage.googleapis.com'

            failures = transport(monkeypatch, lambda request: httpx.Response(429, text='private-provider-error'))
            response = client.post('/hus/chat', json={**payload, 'allow_llm_rewrite': True})
            assert response.status_code == 200
            fallback = response.json()
            assert fallback['generation']['used'] is False and len(failures) == 1
            assert fallback['reply'] == original['reply']
            assert fallback['hus_answer'] == original['hus_answer']
            assert 'private-provider-error' not in response.text

            monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
            assert client.get('/hus/config').json()['llm_rewrite_available'] is False
            assert client.post('/hus/chat', json={**payload, 'allow_llm_rewrite': True}).json() == original
            assert len(failures) == 1
    finally:
        get_hus_answerer.cache_clear()


def test_course_guidance_uses_scoped_evidence_or_asks_for_course(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'lexical')
    monkeypatch.setenv('HUS_ANSWER_POLICY', 'legacy')
    monkeypatch.delenv('HUS_RAG_ROOT', raising=False)
    followup = {
        'question': 'môn này có khó k', 'major': 'data_science', 'version': 'QD3569-2023',
        'allow_generated_reference': True, 'allow_llm_rewrite': False,
    }
    get_hus_answerer.cache_clear()
    try:
        with closing(TestClient(app)) as client:
            missing = client.post('/hus/chat', json=followup).json()['hus_answer']
            assert missing['status'] == 'needs_clarification' and 'mã học phần' in missing['reply']

            payload = {**followup, 'course_code': 'MAT3533'}
            result = client.post('/hus/chat', json=payload).json()
            answer = result['hus_answer']
            assert answer['status'] == 'answered' and answer['dataset'] == 'f3'
            assert {c['metadata']['course_code'] for c in answer['citations']} == {'MAT3533'}
            assert 'Độ khó tùy vào nền tảng' in result['reply']

            study_question = 'tôi có thể học môn này như thế nào'
            study = client.post('/hus/chat', json={**payload, 'question': study_question}).json()
            assert study['hus_answer']['status'] == 'answered'
            assert {c['metadata']['course_code'] for c in study['hus_answer']['citations']} == {'MAT3533'}
            assert 'thử làm lại ví dụ' in study['reply']

            study_without_subject = client.post('/hus/chat', json={
                **followup, 'question': study_question,
            }).json()
            assert study_without_subject['hus_answer']['status'] == 'needs_clarification'

            named = client.post('/hus/chat', json={
                **followup, 'question': 'Giải tích 1 có khó không?',
            }).json()['hus_answer']
            assert named['status'] == 'answered'
            assert {c['metadata']['course_code'] for c in named['citations']} == {'MAT2501'}

            catalog = client.post('/hus/chat', json={
                **payload, 'allow_generated_reference': False,
            }).json()
            assert catalog['hus_answer']['facts']['course_code'] == 'MAT3533'
            assert catalog['hus_answer']['dataset'] == 'f2' and catalog['hus_answer']['citations']
            assert 'chưa thể kết luận môn dễ hay khó' in catalog['reply']
    finally:
        get_hus_answerer.cache_clear()
