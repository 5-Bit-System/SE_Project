"""Visual and functional Playwright verification for Task 17: Synthetic Recommendation Preview."""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
SCREENSHOTS_DIR = Path("backups/admin_preview_20261101")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def save_screenshot(page, name: str):
    path1 = SCREENSHOTS_DIR / name
    page.screenshot(path=str(path1), full_page=True)
    print(f"  [SAVED] Screenshot {name}")


def main():
    print(">>> Starting Playwright verification for Synthetic Recommendation Preview...")

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

            # 3. Switch to Curriculum Tab
            page.locator('#admin-tab-curriculum').click()
            page.wait_for_selector('#admin-curriculum-subtab-preview')
            print("  [PASS] Navigated to Curriculum Panel")

            # 4. Open Synthetic Preview Subtab
            page.locator('#admin-curriculum-subtab-preview').click()
            page.wait_for_selector('#admin-curriculum-preview-view:not([hidden])')
            print("  [PASS] Synthetic Preview workspace opened")

            # 5. Wait for programs and courses picker to load
            page.wait_for_selector('.admin-preview-chk', timeout=10000)
            print("  [PASS] Course picker loaded with checkboxes")

            # 6. Click Preset "Đã học 1 năm"
            page.locator('.admin-preset-btn[data-preset="year1"]').click()
            page.wait_for_timeout(300)
            selected_count = page.locator('#admin-preview-selected-num').inner_text()
            assert int(selected_count) > 0, "Preset did not select courses"
            print(f"  [PASS] Preset selected {selected_count} courses")

            # 7. Run Simulation
            page.locator('#admin-preview-run-btn').click()
            page.wait_for_selector('#admin-preview-results-area:not([hidden])', timeout=15000)
            print("  [PASS] Simulation completed and results rendered")

            # Verify banner and table rows
            banner_text = page.locator('#admin-preview-banner').inner_text()
            assert "MÔ PHỎNG GIẢ ĐỊNH" in banner_text
            rec_rows = page.locator('#admin-tbody-rec tr')
            assert rec_rows.count() > 0
            print(f"  [PASS] Recommended courses rendered: {rec_rows.count()} rows")

            # Save desktop light screenshot
            save_screenshot(page, "preview_recommended_light.png")

            # 8. Switch to Blocked tab & Dark theme
            page.locator('#admin-res-tab-blocked').click()
            page.wait_for_selector('#admin-res-panel-blocked:not([hidden])')
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.wait_for_timeout(300)
            save_screenshot(page, "preview_blocked_dark.png")
            print("  [PASS] Switched to Blocked tab & Dark theme screenshot saved")

            # 9. Mobile Viewport (390px iPhone)
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

            page_mobile.locator('#admin-tab-curriculum').click()
            page_mobile.locator('#admin-curriculum-subtab-preview').click()
            page_mobile.wait_for_selector('#admin-curriculum-preview-view:not([hidden])')
            page_mobile.wait_for_selector('.admin-preview-chk')

            page_mobile.locator('.admin-preset-btn[data-preset="year1"]').click()
            page_mobile.locator('#admin-preview-run-btn').click()
            page_mobile.wait_for_selector('#admin-preview-results-area:not([hidden])')

            # Verify mobile responsiveness
            no_overflow = page_mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert no_overflow, "Horizontal overflow detected on mobile preview (390px)!"
            print("  [PASS] Mobile responsive view verified without overflow (390px)")

            save_screenshot(page_mobile, "preview_mobile.png")
            print(">>> ALL Synthetic Recommendation Preview Playwright checks PASSED!")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
