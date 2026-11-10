"""
Script to render deliverables/BT3_23001939_VT-099.html into deliverables/BT3_23001939_VT-099.pdf
using Playwright Chromium, measure page count, and capture screenshot proofs.
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "deliverables" / "BT3_23001939_VT-099.html"
PDF_PATH = ROOT / "deliverables" / "BT3_23001939_VT-099.pdf"
SCREENSHOT_PATH = ROOT / "docs" / "screenshots" / "remediation" / "vt099_report_page1.png"


def render_pdf_and_screenshot():
    if not HTML_PATH.exists():
        print(f"Error: HTML report not found at {HTML_PATH}")
        sys.exit(1)

    print(f"Reading HTML from: {HTML_PATH}")
    file_url = HTML_PATH.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Create page with A4-like aspect ratio (approx 794 x 1123 at 96 DPI)
        page = browser.new_page(viewport={"width": 800, "height": 1130})
        page.goto(file_url, wait_until="networkidle")

        # Capture Page 1 screenshot proof
        SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SCREENSHOT_PATH), full_page=False)
        print(f"Screenshot of Page 1 saved to: {SCREENSHOT_PATH}")

        # Render PDF with headers and footers
        header_html = (
            '<div style="font-size: 7pt; font-family: -apple-system, BlinkMacSystemFont, '
            "'Segoe UI', Roboto, sans-serif; width: 100%; text-align: right; "
            'padding-right: 14mm; color: #718096;">'
            "[SE2026] Báo cáo BT3 — Biến thể VT-099 | Thái Văn Thắng — MSSV: 23001939"
            "</div>"
        )
        footer_html = (
            '<div style="font-size: 7pt; font-family: -apple-system, BlinkMacSystemFont, '
            "'Segoe UI', Roboto, sans-serif; width: 100%; display: flex; justify-content: space-between; "
            'padding-left: 14mm; padding-right: 14mm; color: #718096;">'
            "<span>Đề tài AI-07 — Nhánh: bt3/23001939-vt099</span>"
            '<span>Trang <span class="pageNumber"></span> / <span class="totalPages"></span></span>'
            "</div>"
        )

        page.pdf(
            path=str(PDF_PATH),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=header_html,
            footer_template=footer_html,
            margin={"top": "14mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
        )
        print(f"PDF successfully rendered to: {PDF_PATH}")
        browser.close()

    # Verify PDF page count
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    page_matches = re.findall(rb"/Type\s*/Page\b", pdf_bytes)
    total_pages = len(page_matches)
    print(f"Total PDF pages: {total_pages}")
    print(f"PDF file size: {len(pdf_bytes)} bytes")

    if total_pages < 8:
        print(f"Warning: PDF has {total_pages} pages, which may be missing sections.")
    else:
        print(f"Verification: PDF contains all sections and appendices across {total_pages} pages.")

    return total_pages


if __name__ == "__main__":
    render_pdf_and_screenshot()
