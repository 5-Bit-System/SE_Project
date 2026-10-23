"""Saved source statistics and chart privacy checks, using intercepted synthetic data only."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    evidence = Path("backups/dashboard_charts_20261023")
    evidence.mkdir(parents=True, exist_ok=True)
    auth = {"valid": True}
    requests = []
    attempts = [
        {"term": "HỌC KỲ 1 - 2099-2100", "code": "TEST001E", "name": "Môn giả lập",
         "credits": "3", "grade10": "8,5", "letter": "B+", "grade4": "3,5"},
        {"term": "HỌC KỲ 1 - 2099-2100", "code": "TEST001E", "name": "Môn giả lập",
         "credits": "3", "grade10": "0", "letter": "F", "grade4": "0"},
        {"term": "HỌC KỲ 2 - 2099-2100", "code": "TEST002", "name": "Môn giả lập",
         "credits": "4", "grade10": "7", "letter": "B", "grade4": "3"},
        {"term": "HỌC KỲ 1 - 2100-2101", "code": "TEST003", "name": "Môn giả lập",
         "credits": "2", "grade10": "", "letter": "I", "grade4": ""},
        {"term": "HỌC KỲ 2 - 2100-2101", "code": "TEST004", "name": "Môn giả lập",
         "credits": "3", "grade10": "9", "letter": "A", "grade4": "4"},
        {"term": None, "code": "TEST005", "name": "Môn giả lập",
         "credits": "", "grade10": "Miễn", "letter": "", "grade4": ""},
    ]
    sample = {"subject": "synthetic-only", "expires_in": 1800,
              "fetched_at": "2026-10-23T00:00:00+00:00",
              "snapshot": {"attempts": attempts, "source_summary": [
                  ["Tổng tín chỉ: 6"], ["Tổng tín chỉ tích lũy: 5"],
                  ["Điểm trung bình tích lũy hệ 4: 3,25"],
                  ["Tổng kết nguồn giả lập"], ["Điểm trung bình học kỳ hệ 10", "7,50"]],
                           "unknown_rows": [], "completeness": "unknown"}}

    def intercept(route):
        url = route.request.url
        if '/profiles' in url:
            raise AssertionError('Demo profiles must not be requested')
        if '/me/profile' in url:
            requests.append(url)
            route.fulfill(status=200 if auth['valid'] else 401, content_type='application/json',
                          body=json.dumps(sample if auth['valid'] else {'detail': 'session_expired'}))
        elif '/auth/logout' in url:
            auth['valid'] = False
            route.fulfill(content_type='application/json', body='{}')
        elif '/me/academic-context?' in url:
            route.fulfill(content_type='application/json', body=json.dumps({
                'status': 'needs_program_binding',
                'blocking_reasons': ['source_incomplete', 'program_binding_unverified']}))
        elif not url.startswith('http://127.0.0.1:8000/'):
            route.abort()
        else:
            route.continue_()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1600, 'height': 1080})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', intercept)
        page.goto('http://127.0.0.1:8000/#dashboard')
        page.wait_for_function("document.querySelectorAll('#analytics-trend .chart-point').length===3")
        assert page.locator('#profile-select').count() == 0
        assert len(requests) == 1
        assert page.locator('#analytics-trend polyline').count() == 1  # Gap is not bridged.
        assert '4,25' in page.locator('#analytics-trend').inner_text()
        assert page.locator('#analytics-credits .credit-chart-row').count() == 5
        assert '6' in page.locator('#analytics-credits .credit-chart-row').first.inner_text()
        assert '6 lượt học' in page.locator('#analytics-count').inner_text()
        page.locator('#analytics-year').select_option('2099–2100')
        assert page.locator('#analytics-trend .chart-point').count() == 2
        assert page.locator('#analytics-credits .credit-chart-row').count() == 2
        assert '3 lượt học' in page.locator('#analytics-count').inner_text()
        page.locator('#analytics-year').select_option('')
        for theme in ('light', 'dark'):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            page.screenshot(path=str(evidence / f'charts-{theme}.png'), full_page=True)
        page.locator('#analytics-trend circle.chart-point').first.focus()
        assert page.locator('#analytics-trend circle.chart-point').first.get_attribute('aria-label')
        page.locator('[data-language-choice="en"]').click()
        assert 'Grades across semesters' in page.locator('.analytics-trend').inner_text()
        assert '4.25' in page.locator('#analytics-trend').inner_text()
        assert 'Tổng kết nguồn giả lập' in page.locator('#analytics-source-totals').inner_text()
        totals = page.locator('#analytics-source-totals').inner_text()
        assert 'Total credits: 6' in totals
        assert 'Accumulated credits: 5' in totals
        assert 'Cumulative GPA (4-point scale): 3,25' in totals
        assert 'Semester average (10-point scale) | 7,50' in totals
        assert 'Tổng tín chỉ' not in totals
        page.locator('[data-language-choice="vi"]').click()
        totals = page.locator('#analytics-source-totals').inner_text()
        assert 'Tổng tín chỉ tích lũy: 5' in totals
        assert 'Điểm trung bình tích lũy hệ 4: 3,25' in totals
        page.locator('[data-language-choice="en"]').click()
        assert page.locator('#tab-transcript, #dashboard-manual-plan').count() == 0
        page.set_viewport_size({'width': 390, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(evidence / 'charts-mobile.png'), full_page=True)
        page.locator('#analytics-year').select_option('2100–2101')
        assert page.locator('#analytics-trend .chart-point').count() == 1
        assert '—' in page.locator('#analytics-table').text_content()  # Missing grade stays missing.
        page.locator('#tab-btn-profile').click()
        page.locator('#portal-logout').click()
        page.locator('#tab-btn-dashboard').click()
        assert page.locator('#analytics-trend svg').count() == 0
        assert page.locator('#analytics-distribution svg').count() == 0
        assert page.locator('#analytics-credits .credit-chart-row').count() == 0
        assert page.locator('#analytics-source-totals').inner_text() == ''
        assert page.locator('#analytics-table tbody tr').count() == 0
        assert not errors, errors
        browser.close()
    print('Charts: source snapshot, mean/retakes/gaps, credits/letters, filters, VI/EN, themes, mobile, logout passed')


if __name__ == '__main__':
    main()
