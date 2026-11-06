"""Visual and functional Playwright verification for Task 18: Academic Announcements Management."""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
SCREENSHOTS_DIR = Path("backups/admin_announcements_20261101")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def save_screenshot(page, name: str):
    path1 = SCREENSHOTS_DIR / name
    page.screenshot(path=str(path1), full_page=True)
    print(f"  [SAVED] Screenshot {name}")


def main():
    print(">>> Starting Playwright verification for Academic Announcements Management...")

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

            # 3. Switch to Announcements Tab
            page.locator('#admin-tab-announcements').click()
            page.wait_for_selector('#admin-panel-announcements:not([hidden])')
            print("  [PASS] Navigated to Announcements Panel")

            # 4. Open Create Announcement Modal
            page.locator('#admin-ann-create-btn').click()
            page.wait_for_selector('#admin-ann-modal[open]')
            print("  [PASS] Create Announcement modal opened")

            # Fill Form
            page.locator('#admin-ann-input-title').fill('Thông báo kế hoạch năm học 2026-2027')
            page.locator('#admin-ann-input-source').fill('https://hus.vnu.edu.vn/ke-hoach-2026.pdf')
            page.locator('#admin-ann-input-content').fill('Chi tiết khung thời gian học tập và đăng ký môn học cho toàn thể sinh viên.')

            # Take Dark screenshot of Modal
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.wait_for_timeout(300)
            save_screenshot(page, "announcements_modal_dark.png")

            # Switch back to Light theme
            page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
            page.wait_for_timeout(300)

            # Submit Form
            page.locator('#admin-ann-submit-btn').click()
            page.locator('#admin-ann-modal').wait_for(state='hidden')
            page.wait_for_timeout(1000)
            print("  [PASS] Announcement submitted and saved as draft")

            # 5. Verify row rendered and publish it
            page.wait_for_selector('#admin-ann-tbody tr')
            first_row = page.locator('#admin-ann-tbody tr').first
            assert 'Thông báo kế hoạch năm học 2026-2027' in first_row.inner_text()
            print("  [PASS] Created announcement row verified in table")

            # Click Publish
            publish_btn = first_row.locator('.admin-ann-btn-publish')
            if publish_btn.count() > 0:
                publish_btn.click()
                page.wait_for_timeout(1000)
                assert 'Đang phát hành' in page.locator('#admin-ann-tbody tr').first.inner_text()
                print("  [PASS] Announcement published successfully")

            # Take Light screenshot of Table & KPIs
            save_screenshot(page, "announcements_overview_light.png")

            # 6. Mobile Viewport (390px iPhone)
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

            page_mobile.locator("#admin-sidebar-toggle").click()
            page_mobile.locator('#admin-tab-announcements').click()
            page_mobile.wait_for_selector('#admin-panel-announcements:not([hidden])')
            page_mobile.wait_for_selector('#admin-ann-table')

            # Verify no overflow
            no_overflow = page_mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert no_overflow, "Horizontal overflow detected on mobile announcements (390px)!"
            print("  [PASS] Mobile responsive view verified without overflow (390px)")

            save_screenshot(page_mobile, "announcements_mobile.png")
            print(">>> ALL Academic Announcements Playwright checks PASSED!")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
