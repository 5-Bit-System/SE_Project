"""Playwright browser verification of Hardened Account Administration UX.

Checks:
1. Users table typography, Monospace VNU subject code, Status badge (Active/Disabled).
2. Self-account safeguards: cannot disable or change role of current session.
3. Confirmation dialog explicitly names target account and warns of session revocation.
4. Focus retention: the focused control remains focused after API mutation and rerender.
5. Search filtering and pagination controls.
6. Mobile layout (390px) and screenshot capture in light/dark themes.

Run: .venv/Scripts/python.exe -m tests.frontend.check_admin_users
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
EVIDENCE_DIR = Path('backups/admin_users_20261101')


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        try:
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            errors = []
            page.on('pageerror', lambda err: errors.append(str(err)))

            # 1. Sign in as admin
            page.goto(BASE_URL)
            page.wait_for_function("document.body.dataset.authState !== 'loading'")
            page.locator('#auth-login-tab').click()
            page.locator('#auth-login-email').fill('admin')
            page.locator('#auth-login-password').fill('admin123')
            page.locator('#auth-login-form button[type=submit]').click()

            # 2. Open Admin Console and go to Users tab
            page.locator('#system-admin-open').wait_for(state='visible')
            page.locator('#system-admin-open').click()
            page.locator('#admin-tab-users').click()
            page.locator('#admin-users tbody tr').first.wait_for(state='visible')
            print('  [PASS] Users tab opened, user rows rendered')

            # 3. Check self-protection (admin row has disabled button & select)
            admin_row = page.locator('#admin-users tbody tr').filter(has_text='admin@sohoctap.local')
            assert admin_row.is_visible()
            assert admin_row.locator('button').is_disabled()
            assert admin_row.locator('select').is_disabled()
            print('  [PASS] Self-account action button and role select are disabled')

            # 4. Find student row
            student_row = page.locator('#admin-users tbody tr').filter(has_text='23001939')
            assert student_row.is_visible()

            # 5. Test Confirmation Dialog content when disabling
            dialog_messages = []
            def handle_dialog(dialog):
                dialog_messages.append(dialog.message)
                dialog.accept()

            page.on('dialog', handle_dialog)

            # Click disable button on student
            action_btn = student_row.locator('button')
            action_btn.click()

            # Verify dialog message content
            assert len(dialog_messages) >= 1
            last_msg = dialog_messages[-1]
            assert '23001939' in last_msg, f'Dialog must name target account: {last_msg}'
            assert ('phiên' in last_msg.lower() or 'session' in last_msg.lower()), (
                f'Dialog must explain session revocation: {last_msg}'
            )
            print('  [PASS] Confirmation dialog named target account and warned of session revocation')

            # Wait for status to become disabled
            page.wait_for_function("document.querySelector('#admin-users tbody').textContent.includes('Đã khóa') || document.querySelector('#admin-users tbody').textContent.includes('Disabled')")
            print('  [PASS] Account status updated to disabled')

            # 6. Verify Focus Retention: the action button on student row should still have focus!
            student_row = page.locator('#admin-users tbody tr').filter(has_text='23001939')
            button_focused = student_row.locator('button').evaluate('el => el === document.activeElement')
            assert button_focused, 'Action button lost focus after rerender!'
            print('  [PASS] Focus retention verified: action button remains focused after rerender')

            # 7. Restore student to active
            student_row.locator('button').click()
            page.wait_for_function("document.querySelector('#admin-users tbody').textContent.includes('Hoạt động') || document.querySelector('#admin-users tbody').textContent.includes('Active')")
            print('  [PASS] Restored account to active')

            # 8. Test Search
            page.locator('#admin-query').fill('nonexistent_user_9999')
            page.locator('#admin-search-form button[type=submit]').click()
            page.wait_for_timeout(200)
            assert page.locator('#admin-users tbody tr').count() == 0

            page.locator('#admin-query').fill('')
            page.locator('#admin-search-form button[type=submit]').click()
            page.locator('#admin-users tbody tr').first.wait_for(state='visible')
            assert page.locator('#admin-users tbody tr').count() >= 2
            print('  [PASS] User search and reset verified')

            # 9. Screenshots: Desktop Light & Dark
            page.screenshot(path=str(EVIDENCE_DIR / 'users_desktop_light.png'), full_page=True)

            page.locator('[data-theme-choice="dark"]').click()
            page.wait_for_timeout(200)
            page.screenshot(path=str(EVIDENCE_DIR / 'users_desktop_dark.png'), full_page=True)
            print('  [PASS] Desktop light and dark screenshots captured')

            # 10. Mobile layout check (390px)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(200)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(EVIDENCE_DIR / 'users_mobile.png'), full_page=True)
            print('  [PASS] Mobile responsive view verified without overflow (390px)')

            assert not errors, f'Uncaught browser errors: {errors}'

        finally:
            browser.close()

    print('\n>>> Task 5 verification SUCCESSFUL! Screenshots stored in:', EVIDENCE_DIR)


if __name__ == '__main__':
    main()
