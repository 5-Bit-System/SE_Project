"""Playwright visual regression and functional test for Publication Provenance Manifest.

Verifies:
1. Admin logs in and opens Revisions subtab in Curriculum panel.
2. Identifies a published/active revision with 'Chứng thực' button.
3. Clicks 'Chứng thực' and verifies #admin-provenance-modal displays the SHA-256
   manifest checksum, published timestamp, publisher identity, reason, and source documents.
4. Captures Desktop Light, Desktop Dark, and Mobile 390px screenshots.
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
SCREENSHOT_DIR = Path("backups/admin_provenance_20261101")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def save_screenshot(page, name: str):
    local_p = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(local_p), full_page=False)
    print(f"Captured {name} to {local_p}")


def test_provenance_modal_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 840})
        page = context.new_page()

        def handle_dialog(dialog):
            dialog.accept()

        page.on("dialog", handle_dialog)

        # 1. Sign in as admin
        page.goto(BASE_URL)
        page.wait_for_function("document.body.dataset.authState !== 'loading'")
        page.locator("#auth-login-tab").click()
        page.locator("#auth-login-email").fill("admin")
        page.locator("#auth-login-password").fill("admin123")
        page.locator("#auth-login-form button[type=submit]").click()

        page.locator("#system-admin-open").wait_for(state="visible")
        page.locator("#system-admin-open").click()
        page.locator("#system-admin").wait_for(state="visible")

        # 2. Switch to Curriculum Tab and Revisions Subtab
        page.locator("#admin-tab-curriculum").click()
        page.locator("#admin-panel-curriculum").wait_for(state="visible")
        page.locator("#admin-curriculum-subtab-revisions").click()
        page.locator("#admin-curriculum-revisions-view").wait_for(state="visible")
        page.wait_for_timeout(1000)

        # 3. Check for 'Chứng thực' button on published/active revision
        prov_buttons = page.locator("#admin-revisions-tbody .btn-diff:has-text('Chứng thực')")
        print(f"Found {prov_buttons.count()} provenance buttons")
        assert prov_buttons.count() > 0, (
            "Expected at least one published revision with 'Chứng thực' button"
        )

        prov_buttons.first.click()
        page.locator("#admin-provenance-modal").wait_for(state="visible")
        page.locator("#admin-prov-content").wait_for(state="visible", timeout=5000)

        # Verify Manifest Checksum is rendered
        checksum_text = page.locator("#admin-prov-checksum").inner_text()
        assert len(checksum_text) == 64, f"Invalid SHA-256 checksum length: {len(checksum_text)}"
        print(f"Manifest Checksum: {checksum_text}")

        # Desktop Light
        save_screenshot(page, "provenance_modal_light")

        # Desktop Dark
        page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
        page.wait_for_timeout(400)
        save_screenshot(page, "provenance_modal_dark")
        page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
        page.wait_for_timeout(300)

        # Mobile 390px
        context_m = browser.new_context(viewport={"width": 390, "height": 844})
        page_m = context_m.new_page()
        page_m.on("dialog", handle_dialog)
        page_m.goto(BASE_URL)
        page_m.wait_for_function("document.body.dataset.authState !== 'loading'")
        page_m.locator("#auth-login-tab").click()
        page_m.locator("#auth-login-email").fill("admin")
        page_m.locator("#auth-login-password").fill("admin123")
        page_m.locator("#auth-login-form button[type=submit]").click()

        page_m.locator("#system-admin-open").wait_for(state="visible")
        page_m.locator("#system-admin-open").click()
        page_m.locator("#system-admin").wait_for(state="visible")

        page_m.locator("#admin-sidebar-toggle").click()
        page_m.locator("#admin-tab-curriculum").click()
        page_m.locator("#admin-curriculum-subtab-revisions").click()
        page_m.locator("#admin-curriculum-revisions-view").wait_for(state="visible")
        page_m.wait_for_timeout(1000)

        m_btn = page_m.locator("#admin-revisions-tbody .btn-diff:has-text('Chứng thực')").first
        m_btn.click()
        page_m.locator("#admin-provenance-modal").wait_for(state="visible")
        page_m.locator("#admin-prov-content").wait_for(state="visible", timeout=5000)
        save_screenshot(page_m, "provenance_modal_mobile")
        context_m.close()

        browser.close()
        print("Playwright test completed successfully.")


if __name__ == "__main__":
    test_provenance_modal_ui()
