"""Delay the app-session response to ensure reload never flashes the login form."""

import mimetypes
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import EMPTY_PROFILE, session_payload


def main():
    static = Path(__file__).resolve().parents[2] / 'app/static'
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel='chrome')
        try:
            for scenario in ('valid', 'expired', 'unavailable'):
                context = browser.new_context()
                page = context.new_page()
                pending, errors, hold = [], [], [True]
                page.on('pageerror', lambda error: errors.append(str(error)))

                def intercept(route):
                    path = urlsplit(route.request.url).path
                    if path == '/auth/session':
                        if hold[0]:
                            hold[0] = False
                            pending.append(route)
                        else:
                            route.fulfill(json=session_payload(scenario == 'valid'))
                    elif path == '/me/profile':
                        route.fulfill(json=EMPTY_PROFILE)
                    elif path == '/' or path.startswith('/static/'):
                        file = static / ('index.html' if path == '/' else path.removeprefix('/static/'))
                        if file.is_file():
                            route.fulfill(body=file.read_bytes(), content_type=mimetypes.guess_type(file)[0] or 'text/plain')
                        else:
                            route.fulfill(status=404)
                    else:
                        route.fulfill(status=401, json={'detail': 'session_expired'})

                page.route('**/*', intercept)
                page.goto('http://127.0.0.1:8000/')
                for reload in range(2 if scenario == 'valid' else 1):
                    if reload:
                        hold[0] = True
                        page.reload()
                    page.wait_for_function("document.body.dataset.authState === 'loading'")
                    assert page.locator('#system-session-loading').is_visible()
                    assert not page.locator('#system-auth').is_visible()
                    assert not page.locator('.main-content').is_visible()
                    page.wait_for_timeout(200)
                    assert page.locator('body').get_attribute('data-auth-state') == 'loading'
                    assert not page.locator('#auth-student-form').is_visible()
                    page.locator('[data-language-choice=en]').click()
                    assert 'Restoring your session' in page.locator('#system-session-loading').inner_text()
                    route = pending.pop()
                    if scenario == 'unavailable':
                        route.fulfill(status=503, json={'detail': 'storage_unavailable'})
                    else:
                        route.fulfill(json=session_payload(scenario == 'valid'))
                    if scenario == 'valid':
                        page.wait_for_function("document.body.dataset.authState === 'workspace'")
                        assert not page.locator('#system-auth').is_visible()
                    else:
                        page.wait_for_function("document.body.dataset.authState === 'auth'")
                        assert page.locator('#auth-student-form').is_visible()
                    assert not page.locator('#system-session-loading').is_visible()
                assert not errors, errors
                context.close()
        finally:
            browser.close()
    print('PASS: delayed valid/reloaded session shows loader without login flash; expired/error shows login')


if __name__ == '__main__':
    main()
