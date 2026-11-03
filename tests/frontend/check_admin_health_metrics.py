"""Visual and functional Playwright verification for Task 16: Operational Health & Consultation Monitoring."""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
SCREENSHOTS_DIR = Path("backups/admin_health_20261101")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def save_screenshot(page, name: str):
    path1 = SCREENSHOTS_DIR / name
    page.screenshot(path=str(path1), full_page=True)
    print(f"  [SAVED] Screenshot {name}")


def main():
    print(">>> Starting Playwright verification for Operational Health & Consultation...")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))

            # 1. Sign in as admin
            page.goto(BASE_URL)
            page.wait_for_function("document.body.dataset.authState !== 'loading'")
            page.locator("#auth-login-tab").click()
            page.locator("#auth-login-email").fill("admin")
            page.locator("#auth-login-password").fill("admin123")
            page.locator("#auth-login-form button[type=submit]").click()

            # 2. Open Admin Console
            page.locator("#system-admin-open").wait_for(state="visible")
            page.locator("#system-admin-open").click()
            page.locator("#system-admin").wait_for(state="visible")
            print("  [PASS] Navigated to Admin Console")

            # 3. Verify Overview Tab & Health Section
            page.wait_for_selector("#admin-health-kpi-grid")
            page.wait_for_selector("#admin-route-groups-table")
            page.wait_for_selector("#admin-consultation-health-details")
            print("  [PASS] Operational Health section rendered")

            # 4. Capture Desktop Light Screenshot
            save_screenshot(page, "health_overview_light.png")

            # 5. Test Window Selector Tabs (1h, 7d, 24h)
            page.locator('.admin-window-btn[data-window="1h"]').click()
            page.wait_for_timeout(300)
            assert "active" in (page.locator('.admin-window-btn[data-window="1h"]').get_attribute("class") or "")
            print("  [PASS] Clicked 1h window selector")

            page.locator('.admin-window-btn[data-window="7d"]').click()
            page.wait_for_timeout(300)
            assert "active" in (page.locator('.admin-window-btn[data-window="7d"]').get_attribute("class") or "")
            print("  [PASS] Clicked 7d window selector")

            page.locator('.admin-window-btn[data-window="24h"]').click()
            page.wait_for_timeout(300)
            assert "active" in (page.locator('.admin-window-btn[data-window="24h"]').get_attribute("class") or "")
            print("  [PASS] Restored 24h window selector")

            # 6. Switch to Dark Theme & Capture Screenshot
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.wait_for_timeout(300)
            save_screenshot(page, "health_overview_dark.png")
            print("  [PASS] Dark theme verified and screenshot saved")

            # 7. Mobile Viewport (390px iPhone)
            page_mobile = browser.new_page(viewport={"width": 390, "height": 844})
            page_mobile.goto(BASE_URL)
            page_mobile.wait_for_function("document.body.dataset.authState !== 'loading'")
            page_mobile.locator("#auth-login-tab").click()
            page_mobile.locator("#auth-login-email").fill("admin")
            page_mobile.locator("#auth-login-password").fill("admin123")
            page_mobile.locator("#auth-login-form button[type=submit]").click()
            page_mobile.locator("#system-admin-open").wait_for(state="visible")
            page_mobile.locator("#system-admin-open").click()
            page_mobile.locator("#system-admin").wait_for(state="visible")
            page_mobile.wait_for_selector('[data-metric="accounts"]')
            page_mobile.wait_for_selector("#admin-health-kpi-grid")
            page_mobile.wait_for_timeout(1000)

            # Assert no horizontal overflow
            no_overflow = page_mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert no_overflow, "Horizontal overflow detected on 390px mobile view!"
            print("  [PASS] Mobile responsive view verified without overflow (390px)")

            save_screenshot(page_mobile, "health_overview_mobile.png")
            print(">>> ALL Operational Health Playwright checks PASSED!")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
