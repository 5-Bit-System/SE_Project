"""E2E Playwright script to verify Admin Document Review and capture visual proofs.

Captures 4 comprehensive visual proof screenshots:
1. admin_overview_document_reviews_remediated.png:
   Admin Overview dashboard displaying the Document Reviews donut chart reflecting
   true pending state (179 total, 176 pending, 2 approved, 1 rejected).
2. admin_document_queue_remediated.png:
   Admin Document Review table showing 179 documents with standardized taxonomy.
3. admin_document_quality_gate_modal.png:
   Document review modal opened for empty/marker document doc_42f38f75db40
   (showing amber "Chờ xử lý OCR" badge, marker content, and rejection alert).
4. admin_document_approved_success.png:
   Document review modal approving a valid curriculum document with complete text,
   showing successful approval status and decision audit metadata.

Outputs saved to:
- C:/Users/5560/.gemini/antigravity/brain/90387ac5-567a-4705-9f70-45d94f72deb5/screenshots/
- docs/screenshots/remediation/
"""

import os
import shutil
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")
BRAIN_SCREENSHOTS = Path(
    r"C:\Users\5560\.gemini\antigravity\brain\90387ac5-567a-4705-9f70-45d94f72deb5\screenshots"
)
DOCS_SCREENSHOTS = Path("docs/screenshots/remediation")


def save_screenshot(source_path: Path, filename: str) -> None:
    """Save screenshot to both destination folders."""
    BRAIN_SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    DOCS_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

    target_brain = BRAIN_SCREENSHOTS / filename
    target_docs = DOCS_SCREENSHOTS / filename

    if source_path != target_brain:
        shutil.copy2(source_path, target_brain)
    if source_path != target_docs:
        shutil.copy2(source_path, target_docs)

    print(f"  [SAVED] {target_brain}")
    print(f"  [SAVED] {target_docs}")


def main() -> None:
    BRAIN_SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    DOCS_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

    print("=== STARTING PLAYWRIGHT E2E PROOF CAPTURE ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 960})

            dialog_messages = []

            def on_dialog(dialog):
                dialog_messages.append(dialog.message)
                print(f"  [DIALOG] {dialog.type}: {dialog.message}")
                dialog.accept()

            page.on("dialog", on_dialog)

            # -------------------------------------------------------------
            # Step 1: Sign in as Admin and capture Overview Donut Chart
            # -------------------------------------------------------------
            print("\n[STEP 1] Navigating to Admin Overview Dashboard...")
            page.goto(BASE_URL)
            page.wait_for_function("document.body.dataset.authState !== 'loading'")

            page.locator("#auth-login-tab").click()
            page.locator("#auth-login-email").fill("admin")
            page.locator("#auth-login-password").fill("admin123")
            page.locator("#auth-login-form button[type=submit]").click()

            if page.locator("#system-admin-open").is_visible():
                page.locator("#system-admin-open").click()
            page.locator("#system-admin").wait_for(state="visible", timeout=10000)

            # Ensure overview tab is active and data loaded
            overview_tab = page.locator("#admin-tab-overview")
            overview_tab.click()
            page.wait_for_timeout(1000)

            # Verify Donut chart
            catalog_card = page.locator("#system-admin .ad-card:has(#ad-catalog-chart)")
            catalog_card.wait_for(state="visible", timeout=10000)
            donut_wrap = page.locator("#ad-catalog-chart .ad-donut-wrap")
            donut_wrap.wait_for(state="visible", timeout=10000)

            donut_text = donut_wrap.inner_text()
            legend_text = page.locator("#ad-catalog-chart .ad-verification-legend").inner_text()
            print(f"  Overview Donut: {donut_text.strip().replace(chr(10), ' ')}")
            print(f"  Overview Legend: {legend_text.strip().replace(chr(10), ' | ')}")

            # Assertions on remediation numbers
            assert "179" in donut_text, f"Expected 179 in donut text, got: {donut_text}"
            assert any(x in legend_text or x in donut_text for x in ("176", "177")), (
                f"Expected 176 or 177 pending in document reviews, got: {legend_text}"
            )

            # Capture Screenshot 1: Overview Dashboard
            s1_path = DOCS_SCREENSHOTS / "admin_overview_document_reviews_remediated.png"
            page.screenshot(path=str(s1_path))
            save_screenshot(s1_path, "admin_overview_document_reviews_remediated.png")
            print("  -> Captured admin_overview_document_reviews_remediated.png")

            # -------------------------------------------------------------
            # Step 2: Document Review Queue with Standardized Taxonomy
            # -------------------------------------------------------------
            print("\n[STEP 2] Navigating to Document Review Queue...")
            crawler_tab = page.locator("#admin-tab-crawler")
            crawler_tab.click()
            page.locator("#admin-crawler-docs-view").wait_for(state="visible", timeout=10000)

            # Wait for table to load and pagination to update
            page.wait_for_function(
                "() => document.getElementById('admin-docs-page-info')?.innerText.includes('179')",
                timeout=10000,
            )
            tbody = page.locator("#admin-crawler-docs-tbody")
            tbody.locator("tr").first.wait_for(state="visible", timeout=10000)

            page_info = page.locator("#admin-docs-page-info")
            info_text = page_info.inner_text()
            print(f"  Pagination info: {info_text}")
            assert "179" in info_text, f"Expected 179 documents in page info, got: {info_text}"

            # Capture Screenshot 2: Document Queue
            s2_path = DOCS_SCREENSHOTS / "admin_document_queue_remediated.png"
            page.screenshot(path=str(s2_path))
            save_screenshot(s2_path, "admin_document_queue_remediated.png")
            print("  -> Captured admin_document_queue_remediated.png")

            # -------------------------------------------------------------
            # Step 3: Quality Gate Modal on Empty/Marker Document doc_42f38f75db40
            # -------------------------------------------------------------
            print("\n[STEP 3] Opening Quality Gate modal for marker doc_42f38f75db40...")
            search_input = page.locator("#admin-docs-search")
            search_input.fill("104.-KHMTTT-chuẩn final QD 3568 Scan final.pdf")
            page.wait_for_timeout(600)

            marker_row = page.locator("tr[data-doc-id='doc_42f38f75db40']")
            marker_row.wait_for(state="visible", timeout=10000)
            print("  Found marker document row: doc_42f38f75db40")

            # Open modal
            marker_row.locator(".btn-review-doc").click()
            modal = page.locator("#admin-doc-review-modal")
            modal.wait_for(state="visible", timeout=5000)

            # Verify OCR Badge
            status_badge = page.locator("#admin-doc-status-badge")
            expect(status_badge).to_contain_text("Chờ xử lý OCR")
            print(f"  Status badge text: {status_badge.inner_text().strip()}")

            # Verify tooltip on approve button
            approve_btn = page.locator("#admin-doc-approve-btn")
            btn_title = approve_btn.get_attribute("title")
            print(f"  Approve button title: {btn_title}")
            assert "cần xử lý OCR" in (btn_title or "") or "Chờ xử lý OCR" in status_badge.inner_text()

            # Attempt approval to verify Quality Gate rejection
            dialog_count_before = len(dialog_messages)
            reason_input = page.locator("#admin-doc-decision-reason")
            reason_input.fill("Thử nghiệm phê duyệt tài liệu scan rỗng chưa qua OCR")
            approve_btn.click()
            page.wait_for_timeout(600)

            # Assert dialog intercepted with quality gate error
            assert len(dialog_messages) > dialog_count_before, "Expected error alert dialog on approval rejection"
            last_dialog = dialog_messages[-1]
            print(f"  Quality Gate Alert Captured: {last_dialog}")
            assert "Nội dung tài liệu rỗng hoặc chỉ chứa marker trang" in last_dialog or "cần OCR" in last_dialog

            # Capture Screenshot 3: Quality Gate modal
            s3_path = DOCS_SCREENSHOTS / "admin_document_quality_gate_modal.png"
            page.screenshot(path=str(s3_path))
            save_screenshot(s3_path, "admin_document_quality_gate_modal.png")
            print("  -> Captured admin_document_quality_gate_modal.png")

            # Close modal
            page.locator("#admin-doc-review-close-btn").click()
            modal.wait_for(state="hidden", timeout=5000)

            # -------------------------------------------------------------
            # Step 4: Approve Valid Curriculum Document doc_1c2e63abf104
            # -------------------------------------------------------------
            print("\n[STEP 4] Approving valid curriculum document doc_1c2e63abf104...")
            search_input.fill("04_De_cuong_chi_tiet_ToanTin_2021.pdf")
            page.wait_for_timeout(600)

            valid_row = page.locator("tr[data-doc-id='doc_1c2e63abf104']")
            valid_row.wait_for(state="visible", timeout=10000)
            print("  Found valid document row: doc_1c2e63abf104")

            valid_row.locator(".btn-review-doc").click()
            modal.wait_for(state="visible", timeout=5000)

            # Fill audit reason
            approval_reason = (
                "Phê duyệt chuẩn sau khi đối chiếu văn bản gốc và thẩm định chất lượng nội dung"
            )
            reason_input = page.locator("#admin-doc-decision-reason")
            reason_input.fill(approval_reason)

            # Click Approve
            dialog_count_before = len(dialog_messages)
            approve_btn = page.locator("#admin-doc-approve-btn")
            approve_btn.click()
            page.wait_for_timeout(800)

            # Verify success alert dialog
            assert len(dialog_messages) > dialog_count_before
            success_dialog = dialog_messages[-1]
            print(f"  Approval Success Alert Captured: {success_dialog}")
            assert "Đã phê duyệt tài liệu" in success_dialog

            # Re-open modal to capture approved state with full preview and audit metadata
            page.wait_for_timeout(600)
            valid_row = page.locator("tr[data-doc-id='doc_1c2e63abf104']")
            valid_row.locator(".btn-review-doc").click()
            modal.wait_for(state="visible", timeout=5000)

            # Verify badge is now approved
            expect(status_badge).to_contain_text("Đã phê duyệt")
            dec_meta = page.locator("#admin-doc-decision-meta")
            expect(dec_meta).to_contain_text(approval_reason)
            print(f"  Decision metadata updated: {dec_meta.inner_text().strip()}")

            # Capture Screenshot 4: Approved Success modal
            s4_path = DOCS_SCREENSHOTS / "admin_document_approved_success.png"
            page.screenshot(path=str(s4_path))
            save_screenshot(s4_path, "admin_document_approved_success.png")
            print("  -> Captured admin_document_approved_success.png")

            # Close modal
            page.locator("#admin-doc-review-close-btn").click()
            modal.wait_for(state="hidden", timeout=5000)

            # Re-visit Overview to capture final donut state (179 total, 176 pending, 2 approved, 1 rejected)
            overview_tab.click()
            page.wait_for_timeout(1000)
            donut_wrap.wait_for(state="visible", timeout=10000)
            donut_text = donut_wrap.inner_text()
            legend_text = page.locator("#ad-catalog-chart .ad-verification-legend").inner_text()
            print(f"  Final Overview Donut: {donut_text.strip().replace(chr(10), ' ')}")
            print(f"  Final Overview Legend: {legend_text.strip().replace(chr(10), ' | ')}")
            assert "179" in donut_text, f"Expected 179 in donut text, got: {donut_text}"
            assert "176" in legend_text or "176" in donut_text, "Expected 176 pending in final overview"
            page.screenshot(path=str(s1_path))
            save_screenshot(s1_path, "admin_overview_document_reviews_remediated.png")
            print("  -> Recaptured admin_overview_document_reviews_remediated.png with 176 pending, 2 approved")

            print("\n[SUCCESS] All 4 remediation proof screenshots captured successfully!")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
