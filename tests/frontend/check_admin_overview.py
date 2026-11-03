"""Playwright browser verification of the HUS Admin Overview Dashboard UI.

Checks:
1. Live KPI cards rendering (Accounts, Programs, Courses, Catalog Status, System Readiness).
2. Proper amber warning badge and note for draft_unverified catalog status.
3. Refresh button functionality.
4. Truthful rendering of unavailable metrics: never displays '0'.
5. Error state recovery with retry action.
6. Desktop light/dark mode and mobile responsive screenshots.

Run: .venv/Scripts/python.exe -m tests.frontend.check_admin_overview
"""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
EVIDENCE_DIR = Path('backups/admin_overview_20261101')


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

            # 2. Open Admin Console
            page.locator('#system-admin-open').wait_for(state='visible')
            page.locator('#system-admin-open').click()
            page.locator('#system-admin').wait_for(state='visible')

            # 3. Wait for Overview metrics to load
            page.locator('.admin-kpi-card').first.wait_for(state='visible')
            page.wait_for_selector('[data-metric="accounts"]')
            print('  [PASS] Live overview metrics rendered')

            # 4. Verify rendered numbers & states
            acc_text = page.locator('[data-metric="accounts"]').inner_text()
            prog_text = page.locator('[data-metric="programs"]').inner_text()
            crs_text = page.locator('[data-metric="courses"]').inner_text()
            assert acc_text == '2', f'Expected 2 accounts, got {acc_text}'
            assert prog_text == '4', f'Expected 4 programs, got {prog_text}'
            assert crs_text == '174', f'Expected 174 courses, got {crs_text}'
            print(f'  [PASS] Verified numeric metrics: {acc_text} accounts, {prog_text} programs, {crs_text} courses')

            # 5. Verify catalog status: draft_unverified badge exists
            cat_badge = page.locator('[data-catalog-status="draft_unverified"]')
            assert cat_badge.is_visible()
            assert 'Bản thảo chưa kiểm định' in cat_badge.inner_text()
            print('  [PASS] Draft unverified badge rendered truthfully')

            # 6. Verify readiness badge: operational
            rdy_badge = page.locator('[data-readiness="operational"]')
            assert rdy_badge.is_visible()
            print('  [PASS] Operational readiness badge rendered')

            # 7. Test Refresh button
            refresh_btn = page.locator('#admin-overview-refresh')
            assert refresh_btn.is_visible()
            refresh_btn.click()
            page.wait_for_selector('[data-metric="accounts"]')
            print('  [PASS] Refresh action completed cleanly')

            # 8. Screenshots: Desktop Light & Dark
            page.screenshot(path=str(EVIDENCE_DIR / 'overview_desktop_light.png'), full_page=True)

            page.locator('[data-theme-choice="dark"]').click()
            page.wait_for_timeout(200)
            page.screenshot(path=str(EVIDENCE_DIR / 'overview_desktop_dark.png'), full_page=True)
            print('  [PASS] Desktop light and dark screenshots captured')

            # 9. Screenshots: Mobile (390px)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(200)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(EVIDENCE_DIR / 'overview_mobile_dark.png'), full_page=True)

            page.locator('[data-theme-choice="light"]').click()
            page.wait_for_timeout(200)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(EVIDENCE_DIR / 'overview_mobile_light.png'), full_page=True)
            print('  [PASS] Mobile responsive view verified without overflow (390px)')

            # 10. Test Unavailable Metric Behavior (Must NOT display '0')
            page.set_viewport_size({'width': 1440, 'height': 900})
            unavailable_payload = {
                "accounts_total": {"value": None, "status": "unavailable", "source": "postgres:accounts"},
                "programs_count": {"value": None, "status": "unavailable", "source": "catalog:active"},
                "courses_count": {"value": None, "status": "unavailable", "source": "catalog:active"},
                "catalog_status": {"value": None, "status": "unavailable", "source": "catalog:verification_state"},
                "system_readiness": {"value": None, "status": "unavailable", "source": "system:readiness_checks"}
            }
            page.evaluate(f"window.adminOverview.render({json.dumps(unavailable_payload)})")
            # Assert no '0' is shown in any metric value
            metric_values = page.locator('#admin-overview-grid .admin-kpi-value-row').all_inner_texts()
            for val in metric_values:
                assert '0' not in val, f"Misleading '0' detected in unavailable metric: {val}"
            unavailable_badges = page.locator('[data-unavailable="true"]')
            assert unavailable_badges.count() == 5
            print('  [PASS] Unavailable metrics rendered as Unavailable, never as 0')
            page.screenshot(path=str(EVIDENCE_DIR / 'overview_unavailable_state.png'), full_page=True)

            # 11. Test Error State & Retry
            page.evaluate("window.adminOverview.renderError('Connection timeout to PostgreSQL')")
            error_banner = page.locator('.admin-error-banner')
            assert error_banner.is_visible()
            assert 'Connection timeout' in error_banner.inner_text()
            print('  [PASS] Error banner rendered with actionable details')

            # Click retry to restore
            page.locator('#admin-overview-retry').click()
            page.wait_for_selector('[data-metric="accounts"]')
            assert page.locator('[data-metric="accounts"]').inner_text() == '2'
            print('  [PASS] Retry successfully restored live overview state')

            assert not errors, f'Uncaught browser errors: {errors}'

        finally:
            browser.close()

    print('\n>>> Task 3 verification SUCCESSFUL! Screenshots stored in:', EVIDENCE_DIR)


if __name__ == '__main__':
    main()
