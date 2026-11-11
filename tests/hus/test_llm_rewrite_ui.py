"""L4 UI -> actual RAG/adapter/client; only provider transport is synthetic."""

import json
import re
from threading import Event

import httpx
import pytest
from playwright.sync_api import expect

from app.hus.llm.capacity import llm_call_slot
from tests.hus.llm.test_pipeline import completion, transport
from tests.hus.test_question_catalog_ui import browser_app  # noqa: F401


@pytest.fixture
def llm_ui(monkeypatch, browser_app):  # noqa: F811 - imported pytest fixture
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-ui-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_LLM_BASE_URL',
                       'https://generativelanguage.googleapis.com/v1beta/openai')
    mode = {'failure': None}

    def respond(request):
        if mode.get('block'):
            mode['entered'].set()
            assert mode['release'].wait(10), 'Provider test was not released'
        if mode['failure'] == 'timeout':
            raise httpx.ReadTimeout('private-timeout', request=request)
        if mode['failure'] == 'quota':
            return httpx.Response(429, text='private-quota synthetic-ui-key')
        bundle = json.loads(json.loads(request.content)['messages'][1]['content'])
        sources = bundle['sources']
        if bundle['scope']['dataset'] == 'f2':
            output = {'kind': 'facts', 'style': 'explain_source',
                      'fact_keys': list(bundle['facts']),
                      'citation_ids': [source['citation_id'] for source in sources]}
        else:
            output = {'kind': 'rewrite_v3', 'items': [
                {'id': part['id'], 'text': part['text']}
                for source in sources for part in source['segments']]}
        return httpx.Response(200, json=completion(output))

    calls = transport(monkeypatch, respond)
    browser, base = browser_app
    page = browser.new_page(viewport={'width': 1380, 'height': 1000}, base_url=base)
    page.goto(base, wait_until='networkidle')
    expect(page.locator('#rag-catalog-status')).to_contain_text('câu hỏi')
    yield page, calls, mode
    page.close()


def ask(page, question='MAT3533 có bao nhiêu tín chỉ?'):
    page.locator('#rag-question').fill(question)
    with page.expect_response(lambda r: r.url.endswith('/hus/chat')) as event:
        page.locator('#rag-send').click()
    result = event.value.json()
    expect(page.locator('#rag-form')).to_have_attribute('aria-busy', 'false')
    expect(page.locator('.rag-message-assistant .rag-message-text').last).to_have_text(result['reply'])
    return json.loads(event.value.request.post_data), result


def test_default_off_disclosed_and_independent_from_f3(llm_ui):
    page, calls, _ = llm_ui
    expect(page.get_by_label('AI diễn đạt từ nguồn', exact=True)).not_to_be_checked()
    expect(page.locator('#rag-rewrite-disclosure')).to_contain_text('Google')
    expect(page.locator('#rag-rewrite-disclosure')).to_contain_text('câu hỏi và bằng chứng')
    payload, result = ask(page)
    assert 'allow_llm_rewrite' not in payload and 'generation' not in result
    assert calls == []
    page.locator('#rag-generated').check()
    payload, _ = ask(page)
    assert payload['allow_generated_reference'] is True
    assert 'allow_llm_rewrite' not in payload and calls == []
    page.locator('#rag-generated').uncheck()
    page.locator('#rag-rewrite').check()
    payload, result = ask(page)
    assert payload['allow_generated_reference'] is False
    assert payload['allow_llm_rewrite'] is True and result['generation']['used'] is True
    assert len(calls) == 1
    assert result['reply'].endswith(result['hus_answer']['reply'])
    assert result['hus_answer']['facts']['value'] == 3
    expect(page.locator('.rag-generation-label').last).to_have_text('AI diễn đạt từ nguồn')


def test_f3_still_labels_ai_knowledge_and_keeps_sources(llm_ui):
    page, calls, _ = llm_ui
    page.locator('#rag-rewrite').check()
    page.locator('#rag-generated').check()
    _, result = ask(page, 'Nội dung MAT3533?')
    assert result['generation']['used'] is True and len(calls) == 1
    expect(page.locator('.rag-generation-label').last).to_have_text('AI diễn đạt từ nguồn')
    expect(page.locator('.rag-message-assistant').last.locator('.rag-citation-ai')).not_to_have_count(0)
    expect(page.locator('.rag-message-assistant').last).to_contain_text('kiến thức AI')
    expect(page.locator('.rag-message-assistant').last.locator('.rag-citations a')).to_have_count(0)


def test_f1_shows_actual_use_and_original_citation_links(llm_ui):
    page, calls, _ = llm_ui
    page.locator('#rag-rewrite').check()
    _, result = ask(page, 'Giới thiệu ngành')
    assert result['generation']['used'] is True and len(calls) == 1
    assert result['hus_answer']['dataset'] == 'f1'
    expect(page.locator('.rag-generation-label').last).to_have_text('AI diễn đạt từ nguồn')
    expect(page.locator('.rag-message-assistant').last.locator('.rag-citations a')).not_to_have_count(0)


def test_catalog_hint_cannot_grant_external_data_consent(llm_ui):
    page, calls, _ = llm_ui

    def poisoned_hint(route):
        response = route.fetch()
        value = response.json()
        for group in value['groups']:
            for item in group['questions']:
                item['request']['allow_llm_rewrite'] = True
                item['request']['allow_generated_reference'] = True
        route.fulfill(response=response, json=value)

    page.route('**/hus/questions?*', poisoned_hint)
    page.reload(wait_until='networkidle')
    page.locator('#rag-catalog-search').fill('MAT3533')
    button = page.get_by_role('button', name='MAT3533 có bao nhiêu tín chỉ?', exact=True)
    with page.expect_response(lambda r: r.url.endswith('/hus/chat')) as event:
        button.click()
    payload = json.loads(event.value.request.post_data)
    assert 'allow_llm_rewrite' not in payload
    assert payload['allow_generated_reference'] is False and calls == []


def test_server_disabled_after_opt_in_shows_canonical_fallback(llm_ui, monkeypatch):
    page, calls, _ = llm_ui
    page.locator('#rag-rewrite').check()
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    payload, result = ask(page)
    assert payload['allow_llm_rewrite'] is True
    assert 'generation' not in result and calls == []
    expect(page.locator('.rag-generation-label').last).to_have_text('Bản trích nguồn')


@pytest.mark.parametrize('failure,note', [('quota', 'hạn mức'), ('timeout', 'thời gian'), ('busy', 'bận')])
def test_actual_pipeline_failure_has_canonical_label(llm_ui, failure, note):
    page, calls, mode = llm_ui
    mode['failure'] = failure
    page.locator('#rag-rewrite').check()
    if failure == 'busy':
        with llm_call_slot():
            _, result = ask(page)
    else:
        _, result = ask(page)
    assert result['generation']['used'] is False
    assert result['reply'] == result['hus_answer']['reply']
    assert len(calls) == (0 if failure == 'busy' else 1)
    expect(page.locator('.rag-generation-label').last).to_have_text('Bản trích nguồn')
    expect(page.locator('.rag-generation-note').last).to_contain_text(note)
    expect(page.locator('#rag-messages')).not_to_contain_text('synthetic-ui-key')
    expect(page.locator('#rag-messages')).not_to_contain_text('private-')


def test_server_off_only_disables_rewrite(llm_ui, monkeypatch):
    page, calls, _ = llm_ui
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    page.reload(wait_until='networkidle')
    expect(page.locator('#rag-rewrite')).to_be_disabled()
    expect(page.locator('#rag-rewrite')).not_to_be_checked()
    expect(page.locator('#rag-rewrite-unavailable')).to_be_visible()
    expect(page.locator('#rag-generated')).to_be_enabled()
    payload, result = ask(page)
    assert 'allow_llm_rewrite' not in payload and 'generation' not in result and calls == []


def test_accessible_description_matches_current_availability(llm_ui, monkeypatch):
    page, _, _ = llm_ui
    checkbox = page.locator('#rag-rewrite')
    expect(checkbox).to_be_enabled()
    expect(checkbox).to_have_accessible_description(re.compile('Google'))
    expect(checkbox).not_to_have_accessible_description(re.compile('chưa được bật'))
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    page.reload(wait_until='networkidle')
    expect(checkbox).to_be_disabled()
    expect(checkbox).to_have_accessible_description(re.compile('chưa được bật'))


@pytest.mark.parametrize('question', ['Xin chào', 'Môn này có bao nhiêu tín chỉ?', 'zzzz_no_course_xyz'])
def test_non_answers_have_no_ai_or_fallback_badge(llm_ui, question):
    page, calls, _ = llm_ui
    page.locator('#rag-rewrite').check()
    _, result = ask(page, question)
    assert result['generation']['used'] is False
    assert calls == []
    expect(page.locator('.rag-generation-label')).to_have_count(0)


def test_major_switch_drops_both_consents_and_late_ai_response(llm_ui):
    page, calls, _ = llm_ui
    page.evaluate("""() => {
        window.lateRead = false;
        window.fetch = ((original) => async (url, options) => {
            const response = await original(url, {...options, signal: undefined});
            if (url === '/hus/chat') {
                const json = response.json.bind(response);
                response.json = async () => {
                    const value = await json();
                    setTimeout(() => { window.lateRead = true; }, 0);
                    return value;
                };
            }
            return response;
        })(window.fetch.bind(window));
    }""")
    held = []
    page.route('**/hus/chat', lambda route: held.append(route))
    page.locator('#rag-rewrite').check()
    page.locator('#rag-generated').check()
    page.locator('#rag-question').fill('MAT3533 có bao nhiêu tín chỉ?')
    with page.expect_request('**/hus/chat'):
        page.locator('#rag-send').click()
    expect(page.locator('#rag-form')).to_have_attribute('aria-busy', 'true')
    expect(page.locator('#rag-rewrite')).to_be_disabled()
    old = held[0].fetch()
    assert old.json()['generation']['used'] is True and len(calls) == 1
    page.locator('#rag-major').select_option('mathematics')
    expect(page.locator('#rag-catalog')).to_have_attribute('data-major', 'mathematics')
    status = page.locator('#rag-status').inner_text()
    held[0].fulfill(response=old)
    page.wait_for_function('window.lateRead === true')
    expect(page.locator('#rag-rewrite')).not_to_be_checked()
    expect(page.locator('#rag-generated')).not_to_be_checked()
    expect(page.locator('.rag-generation-label')).to_have_count(0)
    expect(page.locator('.rag-message-user')).to_have_count(0)
    expect(page.locator('.rag-message-assistant')).to_have_count(1)
    expect(page.locator('#rag-status')).to_have_text(status)
    expect(page.locator('#rag-form')).to_have_attribute('aria-busy', 'false')


def test_mobile_checkbox_keyboard_and_no_horizontal_overflow(llm_ui):
    page, _, _ = llm_ui
    page.set_viewport_size({'width': 390, 'height': 844})
    page.locator('#rag-rewrite').focus()
    page.keyboard.press('Space')
    expect(page.locator('#rag-rewrite')).to_be_checked()
    expect(page.locator('#rag-generated')).not_to_be_checked()
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')


def test_major_switch_does_not_free_a_provider_call_still_running(llm_ui):
    page, calls, mode = llm_ui
    mode.update(block=True, entered=Event(), release=Event())
    page.locator('#rag-rewrite').check()
    page.locator('#rag-question').fill('MAT3533 có bao nhiêu tín chỉ?')
    page.locator('#rag-send').click()
    try:
        assert mode['entered'].wait(5)
        page.locator('#rag-major').select_option('mathematics')
        expect(page.locator('#rag-catalog')).to_have_attribute('data-major', 'mathematics')
        expect(page.locator('#rag-rewrite')).not_to_be_checked()
        page.locator('#rag-rewrite').check()
        _, result = ask(page, 'MAT3300 có bao nhiêu tín chỉ?')
        assert result['generation']['fallback_reason'] == 'busy'
        assert len(calls) == 1
        expect(page.locator('.rag-generation-label').last).to_have_text('Bản trích nguồn')
    finally:
        mode['release'].set()
