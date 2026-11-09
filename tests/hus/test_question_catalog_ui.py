"""Real-browser acceptance of the question menu and its scope/consent boundaries."""

import json
import unicodedata

import pytest
from playwright.sync_api import expect, sync_playwright

from tools.run_hus_rag_demo import demo_server


@pytest.fixture(scope='module')
def browser_app():
    with demo_server() as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, channel='chromium')
        yield browser, base
        browser.close()


@pytest.fixture
def page(browser_app):
    browser, base = browser_app
    page = browser.new_page(viewport={'width': 1380, 'height': 1000}, base_url=base)
    page.goto(base, wait_until='networkidle')
    expect(page.locator('#rag-catalog-status')).to_contain_text('câu hỏi')
    yield page
    page.close()


def click_and_answer(page, button):
    with page.expect_response(lambda r: r.url.endswith('/hus/chat')) as event:
        button.click()
    result = event.value.json()
    expect(page.locator('.rag-message-assistant .rag-message-text').last).to_have_text(result['reply'])
    return json.loads(event.value.request.post_data), result


def test_click_questions_keeps_sources_and_ai_consent(page):
    expect(page.locator('[data-family]')).to_have_count(4)
    page.locator('#rag-catalog-search').fill('MAT3533')
    f2 = page.locator('[data-family="f2"]')
    payload, result = click_and_answer(page, f2.get_by_role('button', name='MAT3533 có bao nhiêu tín chỉ?', exact=True))
    assert payload['major'] == 'data_science' and payload['version'] == 'QD3569-2023'
    assert payload['allow_generated_reference'] is False
    assert result['hus_answer']['facts']['value'] == 3
    expect(page.locator('.rag-message-assistant').last.locator('.rag-citations a')).not_to_have_count(0)

    f3 = page.locator('[data-family="f3"]')
    button = f3.get_by_role('button', name='Nội dung MAT3533?', exact=True)
    expect(button).to_be_disabled()
    expect(page.locator('#rag-generated')).not_to_be_checked()
    page.locator('#rag-generated').check()
    payload, result = click_and_answer(page, button)
    assert payload['allow_generated_reference'] is True
    assert result['hus_answer']['status'] == 'answered'
    assert all(c['display_label'] == 'kiến thức AI' and c['open_url'] is None
               for c in result['hus_answer']['citations'])
    page.locator('#rag-generated').uncheck()
    expect(button).to_be_disabled()


def test_f1_editions_help_and_accent_insensitive_filter(page):
    f1 = page.locator('[data-family="f1"]')
    f1.locator('.rag-catalog-section summary').first.click()
    payload, result = click_and_answer(page, f1.get_by_role('button', name='Giới thiệu ngành', exact=True))
    assert payload['version'] == 'unknown' and payload['program_variant'] == 'unknown'
    assert result['hus_answer']['dataset'] == 'f1' and result['hus_answer']['citations']
    help_group = page.locator('[data-family="help"]')
    help_group.locator('summary').first.click()
    _, result = click_and_answer(page, help_group.get_by_role('button', name='Cách đọc nguồn?', exact=True))
    assert result['mode'] == 'basic_chat' and result['hus_answer'] is None

    response = page.request.get('/hus/questions?major=data_science&version=QD3569-2023').json()
    course = next(q for g in response['groups'] if g['id'] == 'f2'
                  for q in g['questions'] if q['request'].get('course_code') == 'MAT3533')
    title = course['course_label'].split(' — ')[1]
    plain = ''.join(c for c in unicodedata.normalize('NFD', title) if not unicodedata.combining(c)).replace('đ', 'd')
    page.locator('#rag-catalog-search').fill(plain)
    expect(page.locator('[data-family="f2"]')).to_be_visible()
    expect(page.locator('[data-family="f2"] .rag-catalog-section:not([hidden])')).not_to_have_count(0)
    page.locator('#rag-catalog-search').fill('zzzz_no_matching_course')
    expect(page.locator('#rag-catalog-status')).to_contain_text('Không có câu hỏi')
    expect(page.locator('[data-family]:not([hidden])')).to_have_count(0)


def test_late_catalog_and_answer_cannot_cross_major(page):
    # Simulate a transport that delivers a completed response despite abort.
    # This proves the generation guard as well as the normal AbortController.
    page.evaluate("""() => {
        window.completedCatalogReads = [];
        window.fetch = ((original) => async (url, options) => {
            const response = await original(url, {...options, signal: undefined});
            const json = response.json.bind(response);
            response.json = async () => {
                const value = await json();
                // Next task runs after the application's await-json continuation.
                setTimeout(() => window.completedCatalogReads.push(String(url)), 0);
                return value;
            };
            return response;
        })(window.fetch.bind(window));
    }""")
    held = []
    def hold_math(route):
        if 'major=mathematics&' in route.request.url:
            held.append(route)
        else:
            route.continue_()

    page.route('**/hus/questions?*', hold_math)
    page.locator('#rag-major').select_option('mathematics')
    expect(page.locator('#rag-catalog-groups')).to_be_empty()
    page.wait_for_function("document.querySelector('#rag-catalog-status').textContent.includes('Đang tải')")
    page.wait_for_timeout(100)
    assert held
    old = held[0].fetch()
    page.locator('#rag-major').select_option('computer_science')
    expect(page.locator('#rag-catalog-status')).to_contain_text('câu hỏi')
    held[0].fulfill(response=old)
    page.wait_for_function("window.completedCatalogReads.some(url => url.includes('major=mathematics&'))")
    page.unroute('**/hus/questions?*')
    expect(page.locator('#rag-catalog')).to_have_attribute('data-major', 'computer_science')

    held_chat = []
    page.route('**/hus/chat', lambda route: held_chat.append(route))
    page.locator('#rag-generated').check()
    group = page.locator('[data-family="help"]')
    group.locator('summary').first.click()
    group.get_by_role('button', name='Bạn có thể làm gì?', exact=True).click()
    expect(page.locator('#rag-form')).to_have_attribute('aria-busy', 'true')
    expect(group.get_by_role('button', name='Cách đọc nguồn?', exact=True)).to_be_disabled()
    page.wait_for_timeout(100)
    old_chat = held_chat[0].fetch()
    page.locator('#rag-major').select_option('data_science')
    held_chat[0].fulfill(response=old_chat)
    page.wait_for_function("window.completedCatalogReads.includes('/hus/chat')")
    expect(page.locator('#rag-generated')).not_to_be_checked()
    expect(page.locator('.rag-message-user')).to_have_count(0)
    expect(page.locator('.rag-message-assistant')).to_have_count(1)
    expect(page.locator('#rag-catalog')).to_have_attribute('data-major', 'data_science')


def test_catalog_failure_can_retry_without_breaking_chat(page):
    page.route('**/hus/questions?*', lambda route: route.fulfill(status=503, json={'detail': 'unavailable'}))
    page.locator('#rag-major').select_option('mathematics')
    expect(page.locator('#rag-catalog-status')).to_contain_text('Không tải được')
    expect(page.locator('#rag-question')).to_be_enabled()
    page.unroute('**/hus/questions?*')
    page.get_by_role('button', name='Tải lại danh mục', exact=True).click()
    expect(page.locator('#rag-catalog-status')).to_contain_text('câu hỏi')
    expect(page.locator('#rag-catalog')).to_have_attribute('data-major', 'mathematics')


def test_mobile_catalog_keyboard_selection_and_no_horizontal_overflow(page):
    page.set_viewport_size({'width': 390, 'height': 844})
    group = page.locator('[data-family="help"]')
    group.locator('summary').first.click()
    button = group.get_by_role('button', name='Bạn có thể làm gì?', exact=True)
    button.focus()
    with page.expect_response(lambda r: r.url.endswith('/hus/chat')) as event:
        page.keyboard.press('Enter')
    assert event.value.json()['mode'] == 'basic_chat'
    expect(page.locator('#rag-form')).to_have_attribute('aria-busy', 'false')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
