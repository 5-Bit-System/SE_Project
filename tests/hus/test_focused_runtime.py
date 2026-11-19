"""Explicit launcher/service mode and source selection in the real browser/API."""
import os
from unittest.mock import patch

import pytest
from playwright.sync_api import expect

from tests.hus.test_question_catalog_ui import browser_app  # noqa: F401


def test_service_reads_explicit_policy_without_provider(monkeypatch):
    from app.services.hus_service import get_hus_answerer

    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'lexical')
    monkeypatch.setenv('HUS_ANSWER_POLICY', 'focused')
    get_hus_answerer.cache_clear()
    try:
        assert get_hus_answerer().answer_policy == 'focused'
    finally:
        get_hus_answerer.cache_clear()


def test_launcher_policy_is_explicit_and_does_not_read_a_real_key(tmp_path):
    from tools.run_hus_llm import configure

    with patch.dict(os.environ, {'HUS_LLM_API_KEY':'synthetic-focused-key'}, clear=True):
        configure(tmp_path / 'absent.env', root=tmp_path, answer_policy='focused')
        assert os.environ['HUS_ANSWER_POLICY'] == 'focused'
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            configure(tmp_path / 'absent.env', root=tmp_path, answer_policy='invalid')


def test_browser_source_choice_reuses_question_and_preserves_consent(browser_app, monkeypatch):  # noqa: F811
    from app.hus import demo
    from app.hus.answering import HUSAnswerer
    from app.hus.rag_loader import HUSRAGData

    answerer = HUSAnswerer(HUSRAGData.load_current(), answer_policy='focused')
    monkeypatch.setattr(demo, 'current_answerer', lambda: answerer)
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    monkeypatch.setenv('HUS_LLM_AUTO', 'false')
    browser, base = browser_app
    page = browser.new_page(viewport={'width': 460, 'height': 950}, base_url=base)
    try:
        page.goto(base, wait_until='networkidle')
        page.locator('#rag-major').select_option('computer_science')
        question = 'Ngành KHMTTT có thể học tiếp sau đại học như thế nào?'
        page.locator('#rag-question').fill(question)
        with page.expect_response(lambda r: r.url.endswith('/hus/chat')) as response:
            page.locator('#rag-send').click()
        choices = response.value.json()['hus_answer']['source_choices']
        source = next(c for c in choices if c['version'] == '2023' and c['program_variant'] == 'standard')
        button = page.locator('.rag-source-choice').filter(has_text=source['label'])
        expect(button).to_be_visible()
        button.focus()
        with page.expect_response(lambda r: r.url.endswith('/hus/chat')) as response:
            page.keyboard.press('Enter')
        payload = response.value.request.post_data_json
        assert payload['question'] == question and payload['source_id'] == source['source_id']
        assert payload['version'] == '2023' and payload['program_variant'] == 'standard'
        assert payload['allow_generated_reference'] is False
        answer = response.value.json()['hus_answer']
        assert answer['status'] == 'answered'
        assert all(c['metadata']['citation']['source_id'] == source['source_id'] for c in answer['citations'])
        assert 'focus_plan' not in answer
        page.locator('#rag-major').select_option('data_science')
        expect(page.locator('.rag-source-choice')).to_have_count(0)
    finally:
        page.close()
