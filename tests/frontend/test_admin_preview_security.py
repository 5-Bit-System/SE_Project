"""Real admin UI with synthetic API fixtures; every browser request is intercepted."""

from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect, sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.presentation_fixture import common_route

PAYLOAD = '<img src=x onerror="window.previewInjection=true">'
QUOTED = '\" autofocus onfocus="window.previewInjection=true" data-injected="yes'


@pytest.fixture
def preview():
    state = {
        'programs': [{'program_id': 'synthetic', 'name': 'Chương trình thử nghiệm'}],
        'courses': [{'code': 'TEST101', 'name': 'Giải tích & ứng dụng', 'credits': 3}],
        'result': {'simulation_disclaimer': 'Dữ liệu mô phỏng', 'recommendations': [],
                   'eligible_courses': [], 'blocked_courses': []},
        'requests': [],
    }
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except PlaywrightError:
            browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))

        def intercept(route):
            path = urlsplit(route.request.url).path
            if path == '/auth/session':
                account = session_payload()
                account['account'].update(role='admin', display_name='Synthetic admin')
                route.fulfill(json=account)
            elif path == '/admin/programs':
                route.fulfill(json=state['programs'])
            elif path == '/admin/courses':
                route.fulfill(json=state['courses'])
            elif path == '/admin/recommendations/preview':
                state['requests'].append(route.request.post_data_json)
                route.fulfill(json=state['result'])
            elif path.startswith('/admin/'):
                route.fulfill(json={})
            elif not common_route(route):
                route.abort()

        page.route('**/*', intercept)
        page.goto('http://127.0.0.1:8000/')
        page.locator('#admin-tab-curriculum').click()
        yield page, state
        browser.close()
        assert not errors


def open_preview(page):
    page.locator('#admin-curriculum-subtab-preview').click()
    expect(page.locator('#admin-curriculum-preview-view')).to_be_visible()
    expect(page.locator('#admin-preview-prog-select option')).to_have_count(1)


def assert_inert(page):
    view = page.locator('#admin-curriculum-preview-view')
    expect(view.locator('img, script, [onerror], [onfocus], [data-injected]')).to_have_count(0)
    assert page.evaluate('window.previewInjection === undefined')


@pytest.mark.parametrize('field', ['code', 'name'])
@pytest.mark.parametrize('payload', [PAYLOAD, QUOTED])
def test_picker_metadata_is_text_and_values_survive(preview, field, payload):
    page, state = preview
    state['courses'][0][field] = payload
    open_preview(page)
    checkbox = page.locator('.admin-preview-chk')
    expect(checkbox).to_have_count(1)
    expect(page.locator('#admin-preview-courses-picker')).to_contain_text(payload)
    assert_inert(page)
    checkbox.check()
    expect(page.locator('#admin-preview-selected-num')).to_have_text('1')
    page.locator('#admin-preview-run-btn').click()
    expect(page.locator('#admin-preview-results-area')).to_be_visible()
    assert state['requests'][0]['passed_course_codes'] == [state['courses'][0]['code']]


@pytest.mark.parametrize('field', ['program_id', 'name'])
def test_program_option_preserves_special_characters(preview, field):
    page, state = preview
    state['programs'][0][field] = 'Tên <b>môn</b> & "trích dẫn"'
    open_preview(page)
    option = page.locator('#admin-preview-prog-select option')
    expect(option).to_have_text(
        f"{state['programs'][0]['name']} ({state['programs'][0]['program_id']})")
    expect(option).to_have_attribute('value', state['programs'][0]['program_id'])
    assert_inert(page)
