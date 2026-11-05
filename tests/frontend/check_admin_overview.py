"""Browser checks for the admin overview after removing the five legacy cards."""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
EVIDENCE_DIR = Path('backups/admin_overview_20261101')


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        try:
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(BASE_URL)
            page.wait_for_function("document.body.dataset.authState !== 'loading'")
            page.locator('#auth-login-tab').click()
            page.locator('#auth-login-email').fill('admin')
            page.locator('#auth-login-password').fill('admin123')
            page.locator('#auth-login-form button[type=submit]').click()
            page.locator('#system-admin-open').wait_for(state='visible')
            page.locator('#system-admin-open').click()
            page.locator('#admin-panel-overview').wait_for(state='visible')
            page.locator('#admin-health-kpi-grid .admin-health-kpi-card').first.wait_for()

            assert page.locator('#admin-overview-grid').count() == 0
            assert page.locator('#admin-dashboard-system').is_visible()
            assert page.locator('.admin-system-highlights .admin-dashboard-stat').count() == 4
            assert page.locator('#admin-dashboard-students').is_visible()
            assert page.locator('#admin-dashboard-courses').is_visible()
            assert page.locator('#admin-dashboard-recommendations').is_visible()
            assert page.locator('#admin-dashboard-feedback').is_visible()
            assert page.locator('#admin-dashboard-monitoring').is_visible()
            assert page.locator('#admin-overview-refresh').is_visible()

            with page.expect_response(lambda response: '/admin/insights' in response.url):
                page.locator('#admin-overview-refresh').click()
            assert page.locator('#admin-overview-grid').count() == 0
            page.screenshot(path=str(EVIDENCE_DIR / 'overview_desktop_light.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(EVIDENCE_DIR / 'overview_mobile_light.png'), full_page=True)
            assert not errors, f'Uncaught browser errors: {errors}'
        finally:
            browser.close()


if __name__ == '__main__':
    main()
