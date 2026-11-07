"""End-to-end Playwright verification for 179 real HUS documents review and Git dual-write."""

import json
import logging
import os
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("e2e_verification")

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")
SCREENSHOTS_DIR = Path("screenshots")
REVIEWS_FILE = Path("data/hus/document_reviews.json")


def verify_live_hus_links():
    """Verify live HTTP responses for sampled real crawled documents across all 3 HUS domains."""
    logger.info("=== BƯỚC 1: KIỂM CHỨNG LIÊN KẾT THẬT QUA HTTP TRỰC TIẾP ===")
    test_urls = [
        # Domain 1: mim.hus.vnu.edu.vn (normalized to HTTP port 80)
        ("Khoa Toán - Cơ - Tin học (MIM)", "http://mim.hus.vnu.edu.vn/vi/khmt-tt"),
        ("CTĐT CLC Máy tính & KHTT", "http://mim.hus.vnu.edu.vn/vi/mt-khtt-clc"),
        ("Ngành Toán tin (MIM)", "http://mim.hus.vnu.edu.vn/vi/toantin"),
        # Domain 2: hus.vnu.edu.vn (HTTPS port 443)
        ("Trang chủ HUS", "https://hus.vnu.edu.vn/"),
        # Domain 3: tuyensinh.hus.vnu.edu.vn (HTTPS port 443)
        ("Trang Tuyển sinh HUS", "https://tuyensinh.hus.vnu.edu.vn/dai-hoc/nganh-hoc/toan-toan-ung-dung-va-tin-hoc/toan-tin"),
    ]

    client = httpx.Client(timeout=10.0, follow_redirects=True, verify=False)
    results = []
    for label, url in test_urls:
        try:
            resp = client.get(url)
            status = resp.status_code
            logger.info("  [LINK OK] %s (%s) -> HTTP %d", label, url, status)
            assert status in (200, 301, 302), f"URL {url} returned unexpected status {status}"
            results.append({"label": label, "url": url, "status": status, "alive": True})
        except Exception as e:
            logger.error("  [LINK FAIL] %s (%s) -> Error: %s", label, url, e)
            results.append({"label": label, "url": url, "error": str(e), "alive": False})

    client.close()
    alive_count = sum(1 for r in results if r.get("alive"))
    logger.info("Kết quả kiểm chứng link: %d/%d liên kết hoạt động tốt!", alive_count, len(test_urls))
    assert alive_count == len(test_urls), "Tất cả các link mẫu phải sống và phản hồi thành công"
    return results


def run_playwright_e2e():
    """Run full browser UI workflow on Admin Document Review Workspace."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("=== BƯỚC 2: KIỂM THỬ GIAO DIỆN ADMIN VÀ DUAL-WRITE BẰNG PLAYWRIGHT ===")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Sign in as admin
        logger.info("1. Đăng nhập quyền Admin...")
        page.goto(BASE_URL)
        page.wait_for_function("document.body.dataset.authState !== 'loading'")
        page.locator("#auth-login-tab").click()
        page.locator("#auth-login-email").fill("admin")
        page.locator("#auth-login-password").fill("admin123")
        page.locator("#auth-login-form button[type=submit]").click()

        page.locator("#system-admin-open").wait_for(state="visible", timeout=10000)
        page.locator("#system-admin-open").click()
        page.locator("#system-admin").wait_for(state="visible", timeout=10000)
        logger.info("  -> Đăng nhập thành công, đã mở Admin Console")

        # 2. Switch to Document Review tab
        logger.info("2. Chuyển sang tab Kiểm duyệt tài liệu...")
        page.locator("#admin-tab-crawler").click()
        page.locator("#admin-crawler-docs-view").wait_for(state="visible", timeout=5000)

        # 3. Check document queue table & pagination
        page.wait_for_timeout(1000)
        rows = page.locator("#admin-crawler-docs-tbody tr")
        row_count = rows.count()
        logger.info("  -> Hàng đợi tài liệu hiển thị %d dòng", row_count)
        assert row_count >= 10, f"Hàng đợi phải có ít nhất 10 dòng, nhận được {row_count}"

        page_info = page.locator("#admin-docs-page-info").inner_text()
        logger.info("  -> Thông tin phân trang: %s", page_info)
        assert "18" in page_info or "tổng số" in page_info, f"Phân trang phải hiển thị tổng số tài liệu thật, có: {page_info}"

        # Capture Screenshot 1: Document Review Queue with Pagination
        ss_queue = SCREENSHOTS_DIR / "admin_document_review_queue_179.png"
        page.screenshot(path=str(ss_queue))
        logger.info("  -> Đã chụp ảnh hàng đợi kiểm duyệt: %s", ss_queue)

        # 4. Open Document Review Workspace modal for a real document
        logger.info("4. Mở modal kiểm duyệt tài liệu thật...")
        real_row = page.locator("#admin-crawler-docs-tbody tr").filter(has_text="mim.hus.vnu.edu.vn").first
        real_row.locator(".btn-review-doc").click()

        modal = page.locator("#admin-doc-review-modal")
        modal.wait_for(state="visible", timeout=5000)

        # Wait for async API call to populate modal content and set href
        page.wait_for_function(
            "() => { const a = document.getElementById('admin-doc-source-link'); return a && a.href && a.href.startsWith('http'); }",
            timeout=10000,
        )

        source_link = page.locator("#admin-doc-source-link")
        source_url = source_link.get_attribute("href")
        doc_title = page.locator("#admin-doc-modal-title").inner_text()
        logger.info("  -> Modal mở tài liệu: '%s'", doc_title)
        logger.info("  -> URL gốc của bài viết: %s", source_url)

        assert source_url.startswith("http://") or source_url.startswith("https://")
        assert "approved-doc-test" not in source_url
        assert "cntt-copy" not in source_url

        # Capture Screenshot 2: Real Document Detail Modal
        ss_modal = SCREENSHOTS_DIR / "admin_document_review_modal_real_doc.png"
        page.screenshot(path=str(ss_modal))
        logger.info("  -> Đã chụp ảnh modal tài liệu thật: %s", ss_modal)

        # 5. Perform Admin Review Approval on UI
        logger.info("5. Thực hiện thao tác Admin phê duyệt trên giao diện...")
        review_input = page.locator("#admin-doc-decision-reason")
        test_audit_reason = "Admin đối chiếu đề cương chi tiết chuẩn Trường ĐHKHTN - phê duyệt thành công"
        review_input.fill(test_audit_reason)

        approve_btn = page.locator("#admin-doc-approve-btn")
        approve_btn.click()
        page.wait_for_timeout(1000)

        # 6. Verify Dual-Write: check data/hus/document_reviews.json
        logger.info("6. Kiểm tra cơ chế Dual-Write vào file data/hus/document_reviews.json...")
        assert REVIEWS_FILE.is_file(), f"File {REVIEWS_FILE} phải tồn tại trên ổ đĩa"
        saved_reviews = json.loads(REVIEWS_FILE.read_text(encoding="utf-8"))
        logger.info("  -> Số lượng bản ghi trong document_reviews.json: %d", len(saved_reviews))

        # Check that the reason or approval is in saved reviews
        matching_reviews = [r for r in saved_reviews.values() if test_audit_reason in r.get("review_reason", "")]
        logger.info("  -> Tìm thấy %d bản ghi vừa phê duyệt trong file Git-tracked", len(matching_reviews))
        assert len(matching_reviews) >= 1, "Bản ghi phê duyệt phải được tự động ghi vào file document_reviews.json"

        # 7. Switch to Overview tab and verify Donut chart has 3 colors and live count
        logger.info("7. Chuyển sang tab Tổng quan để kiểm tra biểu đồ Donut...")
        page.locator("#admin-tab-overview").click()
        page.locator("#admin-panel-overview").wait_for(state="visible", timeout=5000)
        page.wait_for_timeout(1000)

        # Refresh overview metrics to get latest counts
        page.locator("#admin-overview-refresh").click()
        page.wait_for_timeout(1000)

        donut_chart = page.locator("#ad-catalog-chart")
        donut_chart.wait_for(state="visible", timeout=5000)
        chart_text = donut_chart.inner_text()
        logger.info("  -> Nội dung biểu đồ kiểm duyệt: %s", chart_text.replace("\n", " | "))

        assert "Đã duyệt" in chart_text
        assert "Chờ duyệt" in chart_text
        assert "Từ chối" in chart_text

        # Capture Screenshot 3: Overview Donut Chart
        ss_overview = SCREENSHOTS_DIR / "admin_overview_document_reviews_donut.png"
        donut_card = page.locator("section.ad-card").filter(has=page.locator("#ad-catalog-heading"))
        donut_card.screenshot(path=str(ss_overview))
        logger.info("  -> Đã chụp ảnh biểu đồ Donut kiểm duyệt tài liệu: %s", ss_overview)

        # Capture Screenshot 4: Full Overview Dashboard
        ss_full_overview = SCREENSHOTS_DIR / "admin_overview_full_dashboard.png"
        page.screenshot(path=str(ss_full_overview))
        logger.info("  -> Đã chụp ảnh toàn cảnh trang Tổng quan: %s", ss_full_overview)

        browser.close()
        logger.info("=== HOÀN TẤT TẤT CẢ CÁC BƯỚC KIỂM THỬ E2E THÀNH CÔNG ===")


def main():
    verify_live_hus_links()
    run_playwright_e2e()


if __name__ == "__main__":
    main()
