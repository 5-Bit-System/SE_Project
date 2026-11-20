"""Verify and capture screenshot proof for Admin Overview improvements (Issue #129)."""
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ARTIFACT_DIR = Path(r"C:\Users\5560\.gemini\antigravity\brain\90387ac5-567a-4705-9f70-45d94f72deb5\screenshots")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto("http://127.0.0.1:8000/")
            page.wait_for_function("document.body.dataset.authState !== 'loading'")

            # Sign in as admin
            page.locator("#auth-login-tab").click()
            page.locator("#auth-login-email").fill("admin")
            page.locator("#auth-login-password").fill("admin123")
            page.locator("#auth-login-form button[type=submit]").click()

            # Wait for admin console open button
            page.locator("#system-admin-open").wait_for(state="visible")
            page.locator("#system-admin-open").click()

            # Wait for admin console shell
            expect(page.locator("#system-admin")).to_be_visible()
            page.wait_for_timeout(1000)

            # 1. Verify program table is removed
            assert page.locator("#ad-program-table").count() == 0, "ad-program-table should be removed"
            assert page.locator(".ad-program-card").count() == 0, "ad-program-card should be removed"

            # 2. Verify document review stats card
            heading = page.locator("#ad-catalog-heading")
            expect(heading).to_have_text("Kiểm duyệt tài liệu")

            donut = page.locator("#ad-catalog-chart .ad-donut-wrap")
            expect(donut).to_be_visible()
            donut_text = donut.inner_text()
            print("Donut text:", donut_text)
            assert "44" in donut_text, f"Expected 44 in donut text, got: {donut_text}"

            legend = page.locator("#ad-catalog-chart .ad-verification-legend")
            expect(legend).to_contain_text("Đã duyệt")
            expect(legend).to_contain_text("21")
            expect(legend).to_contain_text("Chờ duyệt")
            expect(legend).to_contain_text("2")
            expect(legend).to_contain_text("Từ chối")
            print("Legend text:", legend.inner_text())

            # 3. Take screenshots
            # Desktop light
            page.screenshot(path=str(ARTIFACT_DIR / "overview_desktop_light.png"), full_page=True)

            # Card close-up
            card = page.locator("#system-admin .ad-card:has(#ad-catalog-chart)")
            card.screenshot(path=str(ARTIFACT_DIR / "overview_document_review_card.png"))

            # Desktop dark
            page.locator('[data-theme-choice="dark"]').click()
            page.wait_for_timeout(400)
            page.screenshot(path=str(ARTIFACT_DIR / "overview_desktop_dark.png"), full_page=True)

            # Mobile view
            page.locator('[data-theme-choice="light"]').click()
            page.set_viewport_size({"width": 390, "height": 844})
            page.wait_for_timeout(400)
            page.screenshot(path=str(ARTIFACT_DIR / "overview_mobile_light.png"), full_page=True)

            print("All screenshot proofs captured successfully!")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
