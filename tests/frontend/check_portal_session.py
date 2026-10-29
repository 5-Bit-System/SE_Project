"""System session privacy/expiry and VNU failure retry with intercepted requests."""
import mimetypes
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import EMPTY_PROFILE, session_payload


def main():
    root = Path(__file__).resolve().parents[2] / 'app' / 'static'
    state = {'authenticated':False, 'connected':False, 'fail_login':True,
             'hold_session':False, 'hold_profile':False}
    requests, pending, errors = [], [], []
    sample = {'subject':'synthetic-only', 'expires_in':7200,
              'profile':{'name':'Synthetic student','program':'Synthetic program'},
              'snapshot':{'attempts':[],'source_summary':[],'unknown_rows':[]}}

    def intercept(route):
        path = urlsplit(route.request.url).path
        requests.append(path)
        if path == '/auth/session':
            if state['hold_session']:
                pending.append(route)
            else:
                route.fulfill(json=session_payload(state['authenticated']))
        elif path == '/auth/vnu':
            if state['fail_login']:
                route.fulfill(status=502,json={'detail':'portal_unavailable'})
            else:
                state['authenticated'] = True
                state['connected'] = True
                route.fulfill(json={'authenticated':True})
        elif path == '/me/portal-connection':
            if state['fail_login']:
                route.fulfill(status=502,json={'detail':'portal_unavailable'})
            else:
                state['connected'] = True
                route.fulfill(json={'connected':True})
        elif path == '/me/profile':
            assert state['authenticated'], 'No private-data fetch while signed out'
            if state['hold_profile']:
                pending.append(route)
            else:
                route.fulfill(json=sample if state['connected'] else EMPTY_PROFILE)
        elif path == '/auth/logout':
            state['authenticated'] = False
            route.fulfill(json={'logged_out':True})
        elif path == '/me/semester-plans' and route.request.method == 'GET':
            assert state['authenticated'], 'No plan fetch while signed out'
            route.fulfill(json={'plans': []})
        elif path.startswith(('/auth/','/me/')):
            raise AssertionError('Unexpected private API')
        else:
            file = root / ('index.html' if path == '/' else path.removeprefix('/static/'))
            if file.is_file():
                route.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'text/plain')
            else:
                route.fulfill(status=404,body='')

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True,channel='chrome')
        try:
            page = browser.new_page()
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.route('**/*',intercept)
            page.goto('http://127.0.0.1:8000/#profile')
            page.evaluate('window.systemAuth.ready')
            assert requests.count('/auth/session') == 1
            assert '/me/profile' not in requests
            assert page.locator('.main-content').is_hidden()

            def system_login(wait=True):
                page.locator('#auth-vnu-username').fill('synthetic-only')
                page.locator('#auth-vnu-password').fill('Synthetic password phrase!')
                page.locator('#auth-student-form button[type=submit]').click()
                if wait:
                    page.wait_for_function("document.body.dataset.authState === 'workspace'")
                    page.locator('#portal-profile').wait_for(state='visible')

            system_login(False)
            page.wait_for_function("document.getElementById('auth-notice').classList.contains('is-error')")
            assert '/me/profile' not in requests
            assert page.locator('#auth-vnu-password').input_value() == ''
            assert page.locator('.main-content').is_hidden()
            state['fail_login'] = False
            system_login()
            for _ in range(3):
                page.locator('#tab-btn-dashboard').click()
                page.locator('#tab-btn-profile').click()

            assert requests.count('/me/portal-connection') == 0
            assert '/auth/portal' not in requests
            assert page.locator('.main-content').is_visible()
            page.locator('[data-language-choice="en"]').click()
            page.locator('#portal-profile').wait_for(state='visible')

            before = requests.count('/me/profile')
            state['authenticated'] = False
            page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
            page.locator('#auth-student-form').wait_for(state='visible')
            assert requests.count('/me/profile') == before
            assert page.locator('#portal-identity').inner_text() == ''
            assert 'expired' in page.locator('#auth-notice').inner_text()

            for hold_key in ['hold_session','hold_profile']:
                system_login()
                page.locator('#portal-profile').wait_for(state='visible')
                state[hold_key] = True
                page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
                page.wait_for_timeout(100)
                assert pending
                before = requests.count('/me/profile')
                page.locator('#system-logout').click()
                page.locator('#auth-student-form').wait_for(state='visible')
                while pending:
                    route = pending.pop()
                    if hold_key == 'hold_session':
                        route.fulfill(json=session_payload())
                    else:
                        route.fulfill(status=401,json={'detail':'session_expired'})
                state[hold_key] = False
                page.wait_for_timeout(100)
                assert page.locator('#portal-profile').is_hidden()
                assert page.locator('#portal-identity').inner_text() == ''
                assert requests.count('/me/profile') == before
                assert page.locator('#auth-notice').inner_text() == ''
            assert not errors, errors
        finally:
            browser.close()
    print('VNU sign-in: anonymous gate, failed login/retry, no second connection, expiry, late positive/401 logout races passed')


if __name__ == '__main__':
    main()
