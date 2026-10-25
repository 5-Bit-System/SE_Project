"""Active UI has one source and never calls legacy personal-input endpoints."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import EMPTY_PROFILE, session_payload


def main():
    logged_in = False
    requests, errors = [], []
    sample = {"subject": "synthetic-only", "profile": {"name": "Sinh viên giả lập",
              "program": "Ngành nguồn thử liên ngành", "cohort": "79"},
              "snapshot": {"attempts": [], "source_summary": [], "unknown_rows": []}}

    def intercept(route):
        nonlocal logged_in
        path = route.request.url.split('8000')[-1]
        requests.append(path)
        if path == '/auth/session':
            result, code = session_payload(), 200
        elif path == '/programs':
            result, code = [{"program_id": "synthetic", "name": "Chương trình thử"}], 200
        elif path.startswith('/me/academic-context?'):
            result, code = {"status": "needs_program_binding", "blocking_reasons": [
                "source_incomplete", "program_binding_unverified"]}, 200
        elif path == '/me/portal-connection':
            logged_in = True
            result, code = {}, 200
        elif path == '/auth/logout':
            logged_in = False
            result, code = {}, 200
        elif path == '/me/profile':
            result, code = (sample, 200) if logged_in else (EMPTY_PROFILE, 200)
        elif path.startswith('/static/') or path == '/' or path.startswith('/?'):
            route.continue_()
            return
        else:
            route.abort()
            return
        route.fulfill(status=code, content_type='application/json', body=json.dumps(result))

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', intercept)
        page.goto('http://127.0.0.1:8000/#transcript')
        page.wait_for_function("location.hash === '#profile'")
        assert page.locator('#tab-btn-transcript, #tab-transcript, #dashboard-manual-plan').count() == 0
        assert page.locator('input[type=file], #recommend-form, #advisor-chat-form').count() == 0
        assert page.locator('#program-select').count() == 0
        assert page.locator('#course-language-select').count() == 0
        assert page.locator('[data-language-choice="vi"]').get_attribute('aria-pressed') == 'true'
        assert page.locator('#workspace-program').inner_text() == 'Chưa kết nối VNU'
        page.locator('#tab-btn-rules').click()
        assert 'Đăng nhập VNU' in page.locator('#tab-rules').inner_text()
        page.locator('#tab-btn-profile').click()
        page.wait_for_function("!document.getElementById('portal-submit').disabled")
        page.locator('#portal-username').fill('synthetic-only')
        page.locator('#portal-password').fill('synthetic-password')
        page.locator('#portal-submit').click()
        page.wait_for_function("!document.getElementById('portal-profile').hidden")
        assert page.locator('#workspace-program').inner_text() == sample['profile']['program']
        assert page.locator('#workspace-cohort').inner_text() == '79'
        assert page.locator('#catalog-name-text').inner_text() == sample['profile']['program']
        page.locator('#tab-btn-rules').click()
        page.wait_for_function("document.getElementById('tab-rules').textContent.includes('Chưa xác minh chương trình')")
        assert 'Chưa xác minh bảng điểm' in page.locator('#tab-rules').inner_text()
        page.locator('#tab-btn-recommend').click()
        page.wait_for_function("document.getElementById('tab-recommend').textContent.includes('Chưa xác minh chương trình')")
        page.locator('[data-language-choice="en"]').focus()
        page.locator('[data-language-choice="en"]').press('Enter')
        assert page.locator('[data-language-choice="en"]').get_attribute('aria-pressed') == 'true'
        assert page.locator('[data-language-choice="vi"]').get_attribute('aria-pressed') == 'false'
        assert 'applicable program' in page.locator('#tab-recommend').inner_text()
        assert page.locator('#workspace-program').inner_text() == sample['profile']['program']
        assert page.locator('#workspace-cohort').inner_text() == '79'
        page.reload()
        page.wait_for_function("document.getElementById('workspace-cohort').textContent === '79'")
        assert page.locator('[data-language-choice="en"]').get_attribute('aria-pressed') == 'true'
        assert page.locator('html').get_attribute('lang') == 'en'
        page.locator('[data-language-choice="vi"]').click()
        # Missing source fields clear old labels instead of choosing a catalog.
        saved_program = sample['profile'].pop('program')
        sample['profile'].pop('cohort')
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        page.wait_for_function("document.getElementById('workspace-program').textContent === 'Chưa có thông tin'")
        assert page.locator('#workspace-cohort').inner_text() == 'Chưa có thông tin'
        sample['profile'].update(program=saved_program, cohort='79')
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        page.wait_for_function("document.getElementById('workspace-cohort').textContent === '79'")
        pending = []
        page.route('**/me/profile', lambda route: pending.append(route))
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        page.wait_for_timeout(100)
        assert pending
        page.locator('#tab-btn-profile').click()
        page.locator('#system-logout').click()
        page.wait_for_function("document.getElementById('portal-profile').hidden")
        for route in pending:
            route.fulfill(content_type='application/json', body=json.dumps(sample))
        page.wait_for_timeout(100)
        assert 'Đăng nhập VNU' in page.locator('#tab-rules').text_content()
        assert page.locator('#workspace-program').inner_text() == 'Chưa kết nối VNU'
        assert page.locator('#workspace-cohort').inner_text() == 'Chưa kết nối VNU'
        assert page.locator('#catalog-name-text').inner_text() == 'Hồ sơ học tập VNU'
        evidence = Path('backups/vnu_only_ui_20261023')
        evidence.mkdir(parents=True, exist_ok=True)
        for theme in ('light', 'dark'):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            for width in (1440, 390):
                page.set_viewport_size({"width": width, "height": 1000})
                page.evaluate("window.workspaceNavigate('tab-recommend')")
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=str(evidence / f'{theme}-{width}.png'), full_page=True)
        assert not errors, errors
        assert not any(path.split('?')[0] in {'/transcript/summary', '/eligibility', '/recommendations',
                                               '/recommendations/what-if', '/advisor/chat'} for path in requests)
        assert '/static/app.js' not in requests and '/static/dashboard.js' not in requests
        assert not any(path == '/programs' or path.startswith('/me/academic-context') for path in requests)
        browser.close()
    print('VNU-only UI: manual entry removed; old URL, readiness, logout race, VI/EN and mobile passed')


if __name__ == '__main__':
    main()
