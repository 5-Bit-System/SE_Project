"""Transcript-only chart modals against intercepted VNU attempts; no live account."""

import mimetypes
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload


def main():
    evidence = Path('backups/dashboard_popup_20261031')
    evidence.mkdir(parents=True, exist_ok=True)
    attempts = [
        {"term": "HỌC KỲ 1 - 2023-2024", "code": "MAT100", "name": "Đại số <nguồn>",
         "credits": "3", "grade10": "8,5", "letter": "A+", "grade4": "4"},
        {"term": "HỌC KỲ 1 - 2023-2024", "code": "MAT101", "name": "Giải tích",
         "credits": "2", "grade10": "", "letter": "", "grade4": ""},
        {"term": "HỌC KỲ 2 - 2023-2024", "code": "MAT200", "name": "Xác suất",
         "credits": "4", "grade10": "7", "letter": "B", "grade4": "3"},
        {"term": "HỌC KỲ 1 - 2024-2025", "code": "MAT300", "name": "Thống kê",
         "credits": "3", "grade10": "9", "letter": "A+", "grade4": "4"},
    ]
    source = {"snapshot": {"schema_version": 1, "digest": "synthetic-analytics",
                           "completeness": "complete", "attempts": attempts,
                           "source_summary": [], "unknown_rows": []},
              "profile": {"program": "Toán học", "cohort": "68"}, "fetched_at": None}
    static = Path(__file__).resolve().parents[2] / "app/static"
    errors = []

    def intercept(route):
        path = urlparse(route.request.url).path
        if path == "/auth/session":
            route.fulfill(json=session_payload())
        elif path == "/me/profile":
            route.fulfill(json={"subject": "synthetic-only", "profile": source["profile"],
                                "snapshot": source["snapshot"], "fetched_at": None,
                                "last_synced_at": None, "expires_in": 7200})
        elif path == "/" or path.startswith("/static/"):
            file = static / ("index.html" if path == "/" else path.removeprefix("/static/"))
            if file.is_file():
                route.fulfill(body=file.read_bytes(),
                              content_type=mimetypes.guess_type(file)[0] or "text/plain")
            else:
                route.fulfill(status=404)
        else:
            route.abort()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/")
        page.evaluate('document.fonts.ready')
        page.wait_for_selector("#analytics-trend")
        page.evaluate("value => document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: value}))", source)
        page.wait_for_selector("#analytics-trend .chart-point")

        dialog = page.locator('#analytics-detail')
        point = page.locator('#analytics-trend .chart-point').first
        point.scroll_into_view_if_needed()
        page.evaluate("Promise.allSettled(document.querySelector('.analytics-trend').getAnimations().map(animation => animation.finished))")
        page.evaluate('window.scrollTo(0, 240)')
        chart_bounds = page.locator('.analytics-trend').first.bounding_box()
        scroll_before = page.evaluate('window.scrollY')
        assert scroll_before > 0
        page.locator("#analytics-trend .chart-point").first.click()
        assert page.locator("#dashboard-analytics").is_visible()
        assert page.locator("#portal-dialog").is_hidden()
        assert page.locator("#analytics-detail").is_visible()
        assert dialog.evaluate('node => node instanceof HTMLDialogElement && node.matches(":modal")')
        assert dialog.locator('svg, .chart-region, .analytics-trend').count() == 0
        assert page.locator('.analytics-trend').first.bounding_box() == chart_bounds
        assert page.evaluate('window.scrollY') == scroll_before
        assert page.evaluate('document.activeElement.id') == 'analytics-detail-title'
        for theme in ('light', 'dark'):
            page.evaluate("theme => document.querySelector(`[data-theme-choice=\"${theme}\"]`).click()", theme)
            page.screenshot(path=str(evidence / f'popup-semester-{theme}.png'))
        for key in ('Tab', 'Tab', 'Tab', 'Shift+Tab', 'Shift+Tab', 'Shift+Tab'):
            page.keyboard.press(key)
            assert dialog.evaluate('node => node.contains(document.activeElement)')
        assert "2023–2024" in page.locator("#analytics-detail-title").inner_text()
        assert "Hệ 10" in page.locator("#analytics-detail-meta").inner_text()
        assert page.locator("#analytics-detail-table tr[data-source-code]").evaluate_all(
            "rows => rows.map(row => row.dataset.sourceCode)") == ["MAT100", "MAT101"]
        assert page.evaluate("""() => {
            const table = document.querySelector('#analytics-detail-table');
            return getComputedStyle(table.tHead.rows[0].cells[0]).fontSize ===
                getComputedStyle(table.querySelector('tr[data-source-code] td')).fontSize;
        }""")
        assert page.locator("#analytics-detail-table img").count() == 0
        page.keyboard.press('Escape')
        assert dialog.is_hidden()
        assert page.locator('#analytics-detail-table tr').count() == 0
        assert point.evaluate('node => node === document.activeElement')
        assert page.evaluate('window.scrollY') == scroll_before

        page.locator("#analytics-trend4 .chart-point").nth(1).click()
        assert dialog.evaluate('node => node.matches(":modal")')
        assert "Hệ 4" in page.locator("#analytics-detail-meta").inner_text()
        assert page.locator("#analytics-detail-table tr[data-source-code]").evaluate_all(
            "rows => rows.map(row => row.dataset.sourceCode)") == ["MAT200"]
        page.locator('#analytics-detail-close').click()

        page.locator("#analytics-distribution .distribution-grade-button[data-grade-letter='A+']").click()
        assert page.locator("#dashboard-analytics").is_visible()
        assert page.locator("#portal-dialog").is_hidden()
        assert dialog.evaluate('node => node.matches(":modal")')
        assert page.locator("#analytics-detail-table tr[data-source-code]").evaluate_all(
            "rows => rows.map(row => row.dataset.sourceCode)") == ["MAT300", "MAT100"]
        assert page.locator("#analytics-detail-table .analytics-detail-term").count() == 2
        page.locator('#analytics-detail-title').click()
        assert dialog.is_visible()  # Clicking the popup itself must not dismiss it.
        page.mouse.click(5, 5)
        assert dialog.is_hidden()
        assert page.locator('#analytics-distribution .distribution-grade-button[data-grade-letter="A+"]').evaluate(
            'node => node === document.activeElement')
        page.locator("#analytics-year").select_option("2024–2025")
        page.locator("#analytics-distribution .distribution-grade-button[data-grade-letter='A+']").click()
        assert page.locator("#analytics-detail-table tr[data-source-code]").evaluate_all(
            "rows => rows.map(row => row.dataset.sourceCode)") == ["MAT300"]

        page.keyboard.press('Escape')
        page.locator("#analytics-year").select_option("")
        page.locator("#analytics-distribution .distribution-grade-button[data-grade-letter='']").click()
        assert page.locator("#analytics-detail-table tr[data-source-code]").evaluate_all(
            "rows => rows.map(row => row.dataset.sourceCode)") == ["MAT101"]
        page.evaluate("document.querySelector('[data-language-choice=en]').click()")
        assert "Transcript" in page.locator("#analytics-detail-title").inner_text()
        assert page.locator("#analytics-detail-table tr[data-source-code]").count() == 1
        page.evaluate("document.querySelector('[data-language-choice=vi]').click()")

        page.locator("#analytics-detail-close").click()
        assert page.locator("#analytics-detail").is_hidden()
        page.locator("#analytics-distribution .chart-grade-segment[data-grade-letter='A+']").focus()
        page.keyboard.press("Enter")
        assert page.locator("#analytics-detail").is_visible()
        assert page.locator("#analytics-detail-table tr[data-source-code]").count() == 2
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert page.locator("#analytics-detail-hint").is_visible()
        assert "Vuốt ngang" in page.locator("#analytics-detail-hint").inner_text()
        bounds = dialog.bounding_box()
        assert bounds['x'] >= 0 and bounds['x'] + bounds['width'] <= 390
        assert bounds['y'] >= 0 and bounds['y'] + bounds['height'] <= 844
        page.screenshot(path=str(evidence / 'popup-mobile.png'))
        page.locator('.analytics-detail-scroll').evaluate('node => node.scrollLeft = node.scrollWidth')
        assert page.locator('.analytics-detail-scroll').evaluate('node => node.scrollLeft > 0')
        page.evaluate("document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: null}))")
        assert page.locator("#analytics-detail").is_hidden()
        assert page.locator("#analytics-detail-table tr").count() == 0
        assert page.locator("#analytics-detail-title").text_content() == ""
        assert page.locator("#analytics-detail-meta").text_content() == ""
        assert page.evaluate('getComputedStyle(document.documentElement).overflow') != 'hidden'

        # A long semester scrolls inside the popup, including on a short viewport.
        long_source = {**source, 'snapshot': {**source['snapshot'], 'digest': 'synthetic-long',
                       'attempts': [{**attempts[0], 'code': f'TEST{i:03}'} for i in range(40)]}}
        page.set_viewport_size({'width': 390, 'height': 400})
        page.evaluate("value => document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: value}))", long_source)
        page.locator('#analytics-trend .chart-point').first.click()
        bounds = dialog.bounding_box()
        assert bounds['y'] >= 0 and bounds['y'] + bounds['height'] <= 400
        scroller = page.locator('.analytics-detail-scroll')
        assert scroller.evaluate('node => node.scrollHeight > node.clientHeight')
        scroller.evaluate('node => node.scrollTop = node.scrollHeight')
        assert scroller.evaluate('node => node.scrollTop > 0')
        page.evaluate("window.workspaceNavigate('portal-dialog')")
        assert dialog.is_hidden()
        assert page.locator('#analytics-detail-table tr').count() == 0
        page.evaluate("window.workspaceNavigate('tab-dashboard')")
        page.locator('#analytics-trend .chart-point').first.click()
        page.evaluate("document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: null}))")
        assert dialog.is_hidden()
        assert page.locator('#analytics-detail-table tr').count() == 0
        assert not errors, errors
        browser.close()
    print("Analytics modals: transcript-only, 10/4 terms, grade/year filters, focus, Escape/backdrop/close, scroll, language, mobile and source reset passed")


if __name__ == "__main__":
    main()
