"""Verification of the protected HUS Admin Console Shell & Navigation.

Tests:
1. Admin authentication and visibility of the admin entry point.
2. Tablist rendering (Overview, Curriculum, Users) with semantic ARIA attributes.
3. Tab switching via mouse clicks and keyboard navigation (Arrow keys, Home, End).
4. Responsive mobile layout (no horizontal overflow on 390px viewport).
5. Dark/light theme rendering and screenshot capture.
6. Server-side authorization check (unauthorized/forbidden direct API access).

Run: .venv/Scripts/python.exe -m tests.frontend.check_admin_shell
"""
import os
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
EVIDENCE_DIR = Path('backups/admin_shell_20261101')


def verify_api_authorization():
    """Verify that direct API access without admin credentials is rejected."""
    # 1. Unauthenticated request to /admin/users must return 401
    try:
        urllib.request.urlopen(f'{BASE_URL}/admin/users')
        raise AssertionError('Expected 401 for unauthenticated /admin/users')
    except urllib.error.HTTPError as err:
        assert err.code == 401, f'Expected 401, got {err.code}'
    print('  [PASS] Unauthenticated access to /admin/users returns 401')


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    verify_api_authorization()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        try:
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            errors = []
            page.on('pageerror', lambda err: errors.append(str(err)))

            # 1. Open page
            page.goto(BASE_URL)
            page.wait_for_function("document.body.dataset.authState !== 'loading'")

            # 2. Sign in as admin
            page.locator('#auth-login-tab').click()
            page.locator('#auth-login-email').fill('admin')
            page.locator('#auth-login-password').fill('admin123')
            page.locator('#auth-login-form button[type=submit]').click()

            # 3. Wait for admin console open button
            page.locator('#system-admin-open').wait_for(state='visible')
            print('  [PASS] Admin signed in, #system-admin-open is visible')

            # 4. Open Admin Console
            page.locator('#system-admin-open').click()
            page.locator('#system-admin').wait_for(state='visible')
            assert not page.locator('#system-admin').is_hidden()
            print('  [PASS] Admin console shell is displayed (#system-admin visible)')

            # 5. Check Navigation Tabs and ARIA attributes
            tab_overview = page.locator('#admin-tab-overview')
            tab_curriculum = page.locator('#admin-tab-curriculum')
            tab_users = page.locator('#admin-tab-users')

            assert tab_overview.get_attribute('aria-selected') == 'true'
            assert tab_overview.get_attribute('role') == 'tab'
            assert tab_curriculum.get_attribute('aria-selected') == 'false'
            assert tab_users.get_attribute('aria-selected') == 'false'

            panel_overview = page.locator('#admin-panel-overview')
            panel_curriculum = page.locator('#admin-panel-curriculum')
            panel_users = page.locator('#admin-panel-users')

            assert panel_overview.is_visible()
            assert panel_curriculum.is_hidden()
            assert panel_users.is_hidden()
            print('  [PASS] Default tab is Overview with matching active panel')

            # 6. Test tab switching via click: Curriculum
            tab_curriculum.click()
            assert tab_curriculum.get_attribute('aria-selected') == 'true'
            assert tab_overview.get_attribute('aria-selected') == 'false'
            assert panel_curriculum.is_visible()
            assert panel_overview.is_hidden()
            print('  [PASS] Switched to Curriculum tab successfully')

            # 7. Test tab switching via click: Users
            tab_users.click()
            assert tab_users.get_attribute('aria-selected') == 'true'
            assert panel_users.is_visible()
            page.locator('#admin-users tbody tr').first.wait_for(state='visible')
            assert page.locator('#admin-users tbody tr').count() >= 1
            print('  [PASS] Switched to Users tab, user rows rendered')

            # 8. Test Keyboard Navigation
            tab_overview.click()
            tab_overview.focus()
            page.keyboard.press('ArrowRight')
            assert tab_curriculum.get_attribute('aria-selected') == 'true'
            assert panel_curriculum.is_visible()

            for name in ('crawler', 'users', 'audit', 'announcements'):
                page.keyboard.press('ArrowRight')
                assert page.locator(f'#admin-tab-{name}').get_attribute('aria-selected') == 'true'
                assert page.locator(f'#admin-panel-{name}').is_visible()

            page.keyboard.press('Home')
            assert tab_overview.get_attribute('aria-selected') == 'true'
            assert panel_overview.is_visible()

            page.keyboard.press('End')
            assert page.locator('#admin-tab-announcements').get_attribute('aria-selected') == 'true'
            assert page.locator('#admin-panel-announcements').is_visible()
            print('  [PASS] Keyboard navigation (ArrowRight, Home, End) verified')

            # 9. Test Back to Workspace
            page.locator('#admin-back').click()
            assert page.locator('#system-admin').is_hidden()
            print('  [PASS] Back button returns to student workspace (#system-admin hidden)')

            # Re-enter admin console for visual & responsive checks
            page.locator('#system-admin-open').click()
            page.locator('#system-admin').wait_for(state='visible')

            # 10. Desktop Light screenshot
            page.screenshot(path=str(EVIDENCE_DIR / 'admin_desktop_light.png'), full_page=True)

            # 11. Dark theme check & screenshot
            page.locator('[data-theme-choice="dark"]').click()
            page.wait_for_timeout(200)
            page.screenshot(path=str(EVIDENCE_DIR / 'admin_desktop_dark.png'), full_page=True)
            print('  [PASS] Dark mode captured')

            # 12. Mobile layout check (390 x 844)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(200)
            page.screenshot(path=str(EVIDENCE_DIR / 'admin_mobile_dark.png'), full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')

            page.locator('[data-theme-choice="light"]').click()
            page.wait_for_timeout(200)
            page.screenshot(path=str(EVIDENCE_DIR / 'admin_mobile_light.png'), full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            print('  [PASS] Mobile responsive view verified without overflow (390px)')

            # 13. Verify no uncaught browser page errors
            assert not errors, f'Uncaught browser errors: {errors}'
            print('  [PASS] Zero browser page errors detected')

        finally:
            browser.close()

    print('\n>>> Task 1 verification SUCCESSFUL! Screenshots stored in:', EVIDENCE_DIR)


if __name__ == '__main__':
    main()
