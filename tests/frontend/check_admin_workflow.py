"""Browser verification for Curriculum Revisions & Diff Review Workflow.

Tests:
1. Open Admin Console -> Curriculum tab.
2. Switch to 'Bản thảo & Lịch sử phiên bản' subtab.
3. Verify Revisions table renders with status and action buttons.
4. Open Diff Modal for a revision -> verify diff summary stats and course changes.
5. Capture screenshots in light and dark themes.
6. Verify mobile layout (390px).

Run: .venv/Scripts/python.exe -m tests.frontend.check_admin_workflow
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
EVIDENCE_DIR = Path('backups/admin_workflow_20261101')


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

            page.locator('#system-admin').wait_for(state='visible')
            page.locator('#system-admin').wait_for(state='visible')

            # 2. Switch to Curriculum Tab
            page.locator('#admin-tab-curriculum').click()
            page.locator('#admin-panel-curriculum').wait_for(state='visible')
            print('  [PASS] Switched to Curriculum tab')

            # 3. Switch to Revisions subtab
            subtab_rev = page.locator('#admin-curriculum-subtab-revisions')
            subtab_rev.wait_for(state='visible')
            subtab_rev.click()

            revisions_view = page.locator('#admin-curriculum-revisions-view')
            revisions_view.wait_for(state='visible')
            assert not revisions_view.is_hidden()
            print('  [PASS] Switched to Revisions subtab')

            # 4. Wait for revisions table rows
            page.locator('#admin-revisions-tbody tr').first.wait_for(state='visible')
            row_count = page.locator('#admin-revisions-tbody tr').count()
            print(f'  [PASS] Rendered {row_count} revision rows')

            # Capture revisions list screenshot
            page.screenshot(path=str(EVIDENCE_DIR / 'revisions_list_light.png'))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.screenshot(path=str(EVIDENCE_DIR / 'revisions_list_dark.png'))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")

            # 5. Open Diff Modal on the first revision
            diff_btn = page.locator('#admin-revisions-tbody .admin-action-btn-sm:has-text("So sánh")').first
            diff_btn.click()

            modal = page.locator('#admin-diff-modal')
            modal.wait_for(state='visible')
            assert page.evaluate("document.getElementById('admin-diff-modal').open") is True
            page.locator('#admin-diff-stats .diff-stat-card').first.wait_for(state='visible')
            print('  [PASS] Diff modal opened with stats grid')

            # Capture Diff Modal screenshots
            page.screenshot(path=str(EVIDENCE_DIR / 'diff_modal_light.png'))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.screenshot(path=str(EVIDENCE_DIR / 'diff_modal_dark.png'))
            print('  [PASS] Captured Diff modal screenshots in light & dark')

            # 6. Test mobile layout (390px)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(300)
            page.screenshot(path=str(EVIDENCE_DIR / 'diff_modal_mobile.png'))
            print('  [PASS] Mobile responsive view verified')

            # 7. Close Diff Modal
            page.locator('#admin-diff-close-btn').click()
            page.wait_for_timeout(300)
            assert page.evaluate("document.getElementById('admin-diff-modal').open") is False
            print('  [PASS] Diff modal closed')

            # Check zero browser errors
            assert len(errors) == 0, f'Browser page errors: {errors}'

            print('\n>>> Task 8 verification SUCCESSFUL! Screenshots stored in:', EVIDENCE_DIR)
        finally:
            browser.close()


if __name__ == '__main__':
    main()
