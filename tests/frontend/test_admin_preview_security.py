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


RESULT_FIELDS = [
    ('recommendations', field) for field in ('rank', 'code', 'name', 'credits', 'reason', 'fit_reason')
] + [
    ('eligible_courses', field) for field in ('code', 'name', 'credits', 'block', 'term')
] + [
    ('blocked_courses', field) for field in ('code', 'name', 'credits', 'block', 'message', 'prerequisite')
] + [('banner', 'simulation_disclaimer'), ('banner', 'warning')]


@pytest.mark.parametrize('section,field', RESULT_FIELDS)
def test_result_metadata_does_not_create_markup(preview, section, field):
    page, state = preview
    result = state['result']
    if section == 'banner':
        if field == 'warning':
            result['catalog'] = {'is_unverified': True, 'warning': PAYLOAD}
        else:
            result[field] = PAYLOAD
        target = '#admin-preview-banner'
    else:
        row = {'rank': 1, 'code': 'TEST101', 'name': 'Giải tích', 'credits': 3,
               'score': 0.8, 'block': 'Cơ sở', 'term': 1}
        if field in ('message', 'prerequisite'):
            row['reasons'] = [{'message': PAYLOAD if field == 'message' else 'Thiếu môn',
                               'missing_prerequisites': [[PAYLOAD if field == 'prerequisite' else 'TEST001']]}]
        else:
            row[field] = PAYLOAD
        result[section] = [row]
        target = {'recommendations': '#admin-tbody-rec', 'eligible_courses': '#admin-tbody-eli',
                  'blocked_courses': '#admin-tbody-blk'}[section]
    open_preview(page)
    page.locator('#admin-preview-run-btn').click()
    expect(page.locator('#admin-preview-results-area')).to_be_visible()
    if section == 'eligible_courses':
        page.locator('#admin-res-tab-eligible').click()
    elif section == 'blocked_courses':
        page.locator('#admin-res-tab-blocked').click()
    expect(page.locator(target)).to_contain_text(PAYLOAD)
    assert_inert(page)
