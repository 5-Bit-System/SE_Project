"""Admin accounts stay in the console; student UI uses a separate login."""

from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.presentation_fixture import common_route


def main():
    state = {'role': None}
    requests, errors = [], []
    student = session_payload()
    admin = session_payload()
    admin['account'].update(account_id='synthetic-admin', session_id='synthetic-admin-session',
                            role='admin', auth_method='local', vnu_subject=None)
    sample = {'subject': 'synthetic-only', 'expires_in': 7200,
              'profile': {'name': 'Synthetic student', 'program': 'Synthetic program', 'cohort': '79'},
              'snapshot': {'attempts': [], 'source_summary': [], 'unknown_rows': []}}

    def intercept(route):
        path = urlsplit(route.request.url).path
        requests.append((state['role'], path))
        if path == '/auth/session':
            route.fulfill(json=admin if state['role'] == 'admin' else student
                          if state['role'] == 'student' else session_payload(False))
        elif path == '/auth/login':
            state['role'] = 'admin'
            route.fulfill(json={'authenticated': True})
        elif path == '/auth/vnu':
            assert state['role'] is None, 'VNU sign-in must follow explicit logout from admin'
            state['role'] = 'student'
            route.fulfill(json={'authenticated': True})
        elif path == '/auth/logout':
            state['role'] = None
            route.fulfill(json={'logged_out': True})
        elif path == '/me/password':
            assert state['role'] == 'admin'
            admin['account']['must_change_password'] = False
            admin['account']['session_id'] += '-rotated'
            route.fulfill(json={'changed': True})
        elif path.startswith('/me/'):
            assert state['role'] == 'student', 'Admin must not load student data'
            if path == '/me/profile':
                route.fulfill(json=sample)
            elif path == '/me/semester-plans':
                route.fulfill(json={'plans': []})
            else:
                route.abort()
        elif path.startswith('/admin/'):
            route.fulfill(json={})
        elif common_route(route):
            return
        else:
            route.abort()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        try:
            page = browser.new_page(viewport={'width': 1366, 'height': 768})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.route('**/*', intercept)
            page.goto('http://127.0.0.1:8000/#profile')
            page.locator('#auth-login-tab').click()
            page.locator('#auth-login-email').fill('synthetic-admin')
            page.locator('#auth-login-password').fill('synthetic-admin-password')
            page.locator('#auth-login-form button[type=submit]').click()

            def admin_only():
                expect(page.locator('#system-admin')).to_be_visible()
                expect(page.locator('#system-home')).to_be_hidden()
                assert page.locator('#admin-back').count() == 0
                expect(page.locator('.main-content')).to_be_hidden()
                expect(page.locator('#portal-login')).to_be_hidden()
                assert page.evaluate('window.systemAuth.account.role') == 'admin'

            admin_only()
            page.reload()
            admin_only()
            page.evaluate("location.hash = '#profile'")
            page.evaluate("window.workspaceNavigate('portal-dialog')")
            admin_only()
            assert not any(role == 'admin' and path.startswith('/me/') for role, path in requests)

            for language in ('en', 'vi'):
                page.locator(f'[data-language-choice="{language}"]').click()
                admin_only()
            page.set_viewport_size({'width': 390, 'height': 844})
            admin_only()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')

            def change_password():
                expect(page.locator('#auth-password-form')).to_be_visible()
                expect(page.locator('#system-home')).to_be_hidden()
                for name in ('current-password', 'new-password', 'new-confirm'):
                    page.locator('#auth-' + name).fill('synthetic-password-2099')
                page.locator('#auth-password-form button[type=submit]').click()
                admin_only()

            page.locator('#system-password').click()
            change_password()
            admin['account']['must_change_password'] = True
            page.reload()
            change_password()
            assert not any(role == 'admin' and path.startswith('/me/')
                           and path != '/me/password' for role, path in requests)

            page.locator('#system-logout').click()
            expect(page.locator('#auth-student-form')).to_be_visible()
            page.locator('#auth-vnu-username').fill('synthetic-only')
            page.locator('#auth-vnu-password').fill('synthetic-vnu-password')
            page.locator('#auth-student-form button[type=submit]').click()
            expect(page.locator('.main-content')).to_be_visible()
            # Admin URLs now deliberately restore students to their dashboard.
            # Open the profile explicitly instead of relying on the old admin hash.
            page.locator('[data-tab="portal-dialog"]').click()
            expect(page.locator('#portal-profile')).to_be_visible()
            expect(page.locator('#system-home')).to_be_visible()
            expect(page.locator('#system-admin')).to_be_hidden()
            expect(page.locator('#system-admin-open')).to_be_hidden()
            expect(page.locator('#portal-identity')).to_have_text('synthetic-only')
            assert not errors, errors
        finally:
            browser.close()
    print('Admin-only UI: login/reload/routes, no student data/navigation, password rotation, VI/EN/mobile; logout -> student login preserved')


if __name__ == '__main__':
    main()
