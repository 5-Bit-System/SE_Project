"""Dashboard chart drilldown against intercepted VNU attempts; no live account."""

import mimetypes
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload


def main():
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
        page.wait_for_selector("#analytics-trend")
        page.evaluate("value => document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: value}))", source)
        page.wait_for_selector("#analytics-trend .chart-point")

        page.locator("#analytics-trend .chart-point").first.click()
        assert page.locator("#dashboard-analytics").is_visible()
        assert page.locator("#portal-dialog").is_hidden()
        assert page.locator("#analytics-detail").is_visible()
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

        page.locator("#analytics-trend4 .chart-point").nth(1).click()
        assert page.locator(".analytics-trend-four #analytics-detail").count() == 1
        assert "Hệ 4" in page.locator("#analytics-detail-meta").inner_text()
        assert page.locator("#analytics-detail-table tr[data-source-code]").evaluate_all(
            "rows => rows.map(row => row.dataset.sourceCode)") == ["MAT200"]

        page.locator("#analytics-distribution .distribution-grade-button[data-grade-letter='A+']").click()
        assert page.locator("#dashboard-analytics").is_visible()
        assert page.locator("#portal-dialog").is_hidden()
        assert page.locator(".analytics-distribution #analytics-detail").count() == 1
        assert page.locator("#analytics-detail-table tr[data-source-code]").evaluate_all(
            "rows => rows.map(row => row.dataset.sourceCode)") == ["MAT300", "MAT100"]
        assert page.locator("#analytics-detail-table .analytics-detail-term").count() == 2
        page.locator("#analytics-year").select_option("2024–2025")
        assert page.locator("#analytics-detail-table tr[data-source-code]").evaluate_all(
            "rows => rows.map(row => row.dataset.sourceCode)") == ["MAT300"]

        page.locator("#analytics-year").select_option("")
        page.locator("#analytics-distribution .distribution-grade-button[data-grade-letter='']").click()
        assert page.locator("#analytics-detail-table tr[data-source-code]").evaluate_all(
            "rows => rows.map(row => row.dataset.sourceCode)") == ["MAT101"]
        page.locator("[data-language-choice='en']").click()
        assert "Transcript" in page.locator("#analytics-detail-title").inner_text()
        assert page.locator("#analytics-detail-table tr[data-source-code]").count() == 1
        page.locator("[data-language-choice='vi']").click()

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
        page.evaluate("document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: null}))")
        assert page.locator("#analytics-detail").is_hidden()
        assert not errors, errors
        browser.close()
    print("Analytics drilldown: 10/4 terms, A+ year filter, keyboard, language, mobile and source reset passed")


if __name__ == "__main__":
    main()
