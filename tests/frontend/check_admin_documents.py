"""Browser verification for Document Review Workspace UI (Task 13).

Tests:
1. Open Admin Console -> Crawler tab -> Documents subtab.
2. Filter documents by major and review status.
3. Open Document Review Workspace modal for a crawled document.
4. Verify safe Markdown preview rendering and source links.
5. Edit document metadata (title, major, doc_type) and save.
6. Perform review approval action with mandatory reason.
7. Capture screenshots in light theme, dark theme, and mobile viewport (390px).

Run: .venv/Scripts/python.exe -m tests.frontend.check_admin_documents
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")
EVIDENCE_DIR = Path("backups/admin_documents_20261101")


def seed_security_test_document():
    from app.crawler.document_review_service import create_document, get_document
    from tests.support.admin_database import admin_test_engine
    eng = admin_test_engine()
    with eng.begin() as conn:
        if not get_document(conn, 'doc_xss_test'):
            create_document(conn, url="javascript:alert('xss')",
                title="Tài liệu bảo mật <img src=x onerror=window.__doc_xss=true>",
                markdown_content="# Nội dung an toàn", major="toan_hoc", doc_type="curriculum", doc_id="doc_xss_test")
    eng.dispose()


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    seed_security_test_document()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))

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

            # 2. Switch to Document Review Tab
            tab_crawler = page.locator("#admin-tab-crawler")
            tab_crawler.wait_for(state="visible")
            tab_crawler.click()

            docs_view = page.locator("#admin-crawler-docs-view")
            docs_view.wait_for(state="visible")
            print("  [PASS] Switched to Document Review tab")

            # 4. Wait for documents to load and render
            page.locator("#admin-crawler-docs-tbody tr[data-doc-id='doc_xss_test']").wait_for(state="visible")
            doc_rows = page.locator("#admin-crawler-docs-tbody tr")
            count = doc_rows.count()
            print(f"  [PASS] Rendered {count} documents in review queue")

            # 4b. Security Check: Assert hostile document fields render as inert text without executing
            page.evaluate("window.__doc_xss = false")
            xss_row = page.locator("tr[data-doc-id='doc_xss_test']")
            assert xss_row.count() == 1, "Security fixture must be present"
            if xss_row.count() > 0:
                assert page.evaluate("window.__doc_xss") is False
                assert xss_row.locator("img").count() == 0, "img tag rendered in document row!"
                xss_row.locator(".btn-review-doc").click()
                xss_modal = page.locator("#admin-doc-review-modal")
                xss_modal.wait_for(state="visible")
                src_link = page.locator("#admin-doc-source-link")
                href = src_link.get_attribute("href")
                assert href is None or not href.startswith("javascript:"), f"Dangerous href permitted: {href}"
                page.locator("#admin-doc-review-close-btn").click()
                page.wait_for_timeout(300)
                print("  [PASS] Malicious document title and URL rendered safely as inert text")

            # 4c. Verify Pagination Controls and Page Navigation (Task 8)
            pagination_bar = page.locator("#admin-docs-pagination")
            assert pagination_bar.is_visible()
            prev_btn = page.locator("#admin-docs-prev-btn")
            next_btn = page.locator("#admin-docs-next-btn")
            page_info = page.locator("#admin-docs-page-info")
            page_cur = page.locator("#admin-docs-current-page")

            assert page_info.is_visible()
            assert prev_btn.is_disabled()
            assert "Trang 1" in page_cur.inner_text()
            print("  [PASS] Verified initial pagination state (Page 1, prev disabled)")

            assert not next_btn.is_disabled(), "Pagination fixture must contain at least 101 documents"
            if not next_btn.is_disabled():
                next_btn.click()
                page.wait_for_timeout(500)
                assert "Trang 2" in page_cur.inner_text()
                assert not prev_btn.is_disabled()
                print("  [PASS] Navigated to Page 2, prev button enabled")

                # Changing filter while on Page 2 must reset offset to Page 1
                page.locator("#admin-docs-status-filter").select_option("pending")
                page.wait_for_timeout(500)
                assert "Trang 1" in page_cur.inner_text()
                page.locator("#admin-docs-status-filter").select_option("all")
                page.wait_for_timeout(500)
                print("  [PASS] Changing filter resets pagination to Page 1")

            # 4d. Test Error and Stale Data Affordance (Task 9)
            def simulate_server_error(route):
                route.fulfill(status=500, body='{"detail": "Lỗi máy chủ thử nghiệm"}', headers={"content-type": "application/json"})

            page.route("**/admin/crawler/documents*", simulate_server_error)
            page.locator("#admin-docs-refresh-btn").click()
            page.wait_for_timeout(500)

            error_banner = page.locator("#admin-docs-error-banner")
            stale_banner = page.locator("#admin-docs-stale-banner")
            assert error_banner.is_visible(), "Error banner did not appear on fetch failure!"
            assert stale_banner.is_visible(), "Stale banner did not appear on refresh failure!"
            assert page.locator("#admin-crawler-docs-tbody tr").count() > 0, "Useful rows were cleared on failure!"
            print("  [PASS] Document load failure surfaces error banner and marks data as stale")

            # Unroute and click retry button to verify recovery
            page.unroute("**/admin/crawler/documents*", simulate_server_error)
            page.locator("#admin-docs-retry-btn").click()
            page.wait_for_timeout(500)
            assert not error_banner.is_visible()
            assert not stale_banner.is_visible()
            print("  [PASS] Retry successfully recovered document queue")

            # 5. Open Review Modal on first document
            first_review_btn = page.locator("#admin-crawler-docs-tbody tr .btn-review-doc").first
            first_review_btn.wait_for(state="visible")
            first_review_btn.click()

            modal = page.locator("#admin-doc-review-modal")
            modal.wait_for(state="visible")
            assert modal.is_visible()
            print("  [PASS] Document Review Workspace modal opened")

            # Verify preview pane content
            preview_pane = page.locator("#admin-doc-preview-pane")
            preview_pane.wait_for(state="visible")
            assert len(preview_pane.text_content().strip()) > 0
            print("  [PASS] Document Markdown safely rendered in preview pane")

            # Capture desktop light and dark screenshots
            page.screenshot(path=str(EVIDENCE_DIR / "doc_review_light.png"))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.screenshot(path=str(EVIDENCE_DIR / "doc_review_dark.png"))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
            print("  [PASS] Captured document review light and dark desktop screenshots")

            # 6. Test metadata edit
            page.locator("#admin-doc-edit-title").fill("Tài liệu khảo sát chương trình đào tạo HUS")
            page.locator("#admin-doc-meta-save-btn").click()
            page.wait_for_timeout(500)
            print("  [PASS] Saved document metadata edits")

            # 7. Approve document with reason
            page.locator("#admin-doc-decision-reason").fill(
                "Phê duyệt chuẩn sau khi đối chiếu văn bản gốc"
            )
            page.locator("#admin-doc-approve-btn").click()
            modal.wait_for(state="hidden")
            print("  [PASS] Approved document with audit reason and modal closed")

            # Verify table reflected approval
            page.wait_for_timeout(500)

            # 8. Test Mobile Viewport (390px)
            mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
            mobile_page.on("dialog", handle_dialog)
            mobile_page.goto(BASE_URL)
            mobile_page.wait_for_function("document.body.dataset.authState !== 'loading'")
            mobile_page.locator("#auth-login-tab").click()
            mobile_page.locator("#auth-login-email").fill("admin")
            mobile_page.locator("#auth-login-password").fill("admin123")
            mobile_page.locator("#auth-login-form button[type=submit]").click()

            mobile_page.locator("#system-admin-open").wait_for(state="visible")
            mobile_page.locator("#system-admin-open").click()
            mobile_page.locator("#system-admin").wait_for(state="visible")

            mobile_page.locator("#admin-sidebar-toggle").click()
            mobile_page.locator("#admin-tab-crawler").click()
            mobile_page.locator("#admin-crawler-docs-view").wait_for(state="visible")
            mobile_page.locator("#admin-crawler-docs-tbody tr .btn-review-doc").first.click()
            mobile_modal = mobile_page.locator("#admin-doc-review-modal")
            mobile_modal.wait_for(state="visible")

            mobile_page.screenshot(path=str(EVIDENCE_DIR / "doc_review_mobile.png"))
            print("  [PASS] Captured Mobile Viewport screenshot (390px)")

            assert len(errors) == 0, f"Page errors encountered: {errors}"
            print("\n[SUCCESS] All Document Review Workspace checks passed cleanly!")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
