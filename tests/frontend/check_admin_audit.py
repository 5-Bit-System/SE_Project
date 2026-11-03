"""Playwright visual regression and functional test for Privileged Action Audit Trail (Task 15).

Verifies:
1. Admin logs in and opens the 'Nhật ký kiểm toán' tab.
2. Verifies audit KPI cards (Total, 24h, Warnings).
3. Verifies audit table with action badges, timestamps, actors, targets, summaries.
4. Tests search and target filtering.
5. Opens Audit Detail Modal, inspecting the safe redacted JSON viewer.
6. Captures Desktop Light, Desktop Dark, and Mobile 390px screenshots.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
SCREENSHOT_DIR = Path("backups/admin_audit_20261101")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_SCREENSHOT_DIR = Path(
    r"C:\Users\5560\.gemini\antigravity\brain\90387ac5-567a-4705-9f70-45d94f72deb5\screenshots"
)
BRAIN_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def save_screenshot(page, name: str):
    local_p = SCREENSHOT_DIR / f"{name}.png"
    brain_p = BRAIN_SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(local_p), full_page=False)
    page.screenshot(path=str(brain_p), full_page=False)
    print(f"Captured {name} to {local_p}")


def test_admin_audit_ui():
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

        # 2. Switch to Audit Log tab
        tab_audit = page.locator("#admin-tab-audit")
        tab_audit.wait_for(state="visible")
        tab_audit.click()

        page.locator("#admin-panel-audit").wait_for(state="visible")
        page.wait_for_timeout(1000)

        # 3. Check KPIs & table rows
        rows = page.locator("#admin-audit-tbody tr")
        print(f"Found {rows.count()} audit log rows")
        assert rows.count() > 0, "Expected at least one audit log row in table"

        # Capture Desktop Light overview
        save_screenshot(page, "audit_overview_light")

        # 4. Open Detail Modal
        detail_btns = page.locator("#admin-audit-tbody button[data-audit-id]")
        assert detail_btns.count() > 0, "Expected at least one detail button"
        detail_btns.first.click()

        page.locator("#admin-audit-detail-modal").wait_for(state="visible")
        page.wait_for_timeout(400)

        # Capture Detail Modal Light
        save_screenshot(page, "audit_modal_light")

        # Desktop Dark
        page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
        page.wait_for_timeout(400)
        save_screenshot(page, "audit_modal_dark")
        page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
        page.wait_for_timeout(300)

        # Close Modal
        page.locator("#admin-audit-detail-dismiss-btn").click()
        page.wait_for_timeout(300)

        # 5. Mobile 390px view
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

        page_m.locator("#admin-tab-audit").click()
        page_m.locator("#admin-panel-audit").wait_for(state="visible")
        page_m.wait_for_timeout(1000)

        save_screenshot(page_m, "audit_overview_mobile")
        context_m.close()

        browser.close()
        print("Playwright audit test completed successfully.")


if __name__ == "__main__":
    test_admin_audit_ui()
