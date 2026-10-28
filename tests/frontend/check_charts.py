"""Saved source statistics and chart privacy checks, using intercepted synthetic data only."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload


def main():
    evidence = Path("backups/dashboard_charts_20261023")
    evidence.mkdir(parents=True, exist_ok=True)
    auth = {"valid": True}
    requests = []
    attempts = [
        {"term": "HỌC KỲ 1 - 2099-2100", "code": "TEST001E", "name": "Môn giả lập",
         "credits": "3", "grade10": "8,5", "letter": "A+", "grade4": "3,5"},
        {"term": "HỌC KỲ 1 - 2099-2100", "code": "TEST001E", "name": "Môn giả lập",
         "credits": "1", "grade10": "0", "letter": "F", "grade4": "0"},
        {"term": "HỌC KỲ 2 - 2099-2100", "code": "TEST002", "name": "Môn giả lập",
         "credits": "4", "grade10": "7", "letter": "B", "grade4": "3"},
        {"term": "HỌC KỲ 1 - 2100-2101", "code": "TEST003", "name": "Môn giả lập",
         "credits": "2", "grade10": "", "letter": "I", "grade4": ""},
        {"term": "HỌC KỲ 2 - 2100-2101", "code": "TEST004", "name": "Môn giả lập",
         "credits": "3", "grade10": "9", "letter": "A+", "grade4": "4"},
        {"term": None, "code": "TEST005", "name": "Môn giả lập",
         "credits": "", "grade10": "Miễn", "letter": "", "grade4": ""},
        {"term": None, "code": "TEST006", "name": "Môn giả lập",
         "credits": "0", "grade10": "8", "letter": "B", "grade4": "3"},
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
        if '/auth/session' in url:
            route.fulfill(json=session_payload(auth['valid']))
            return
        elif '/profiles' in url:
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
        context = browser.new_context(viewport={'width': 1600, 'height': 1080}, locale='vi-VN',
                                      timezone_id='Asia/Bangkok')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', intercept)
        page.goto('http://127.0.0.1:8000/#dashboard')
        page.wait_for_function("document.querySelectorAll('#analytics-trend .chart-point').length===3")
        page.wait_for_function("document.querySelectorAll('#analytics-trend4 .chart-point').length===3")
        assert page.locator('#profile-select').count() == 0
        assert len(requests) == 1
        assert page.locator('#analytics-trend polyline').count() == 1  # Gap is not bridged.
        assert '6,38' in page.locator('#analytics-trend').inner_text()
        assert '2,63' in page.locator('#analytics-trend4').inner_text()
        assert page.locator('#analytics-trend4 polyline').count() == 1
        assert '7,32' in page.locator('#analytics-weighted-summary').inner_text()
        assert '3,14' in page.locator('#analytics-weighted-summary').inner_text()
        assert 'Tất cả lượt học' in page.locator('#analytics-weighted-summary').inner_text()
        assert 'TB hệ 4' in page.locator('#analytics-table thead').text_content()
        assert '2,63' in page.locator('#analytics-table tbody').text_content()
        assert page.locator('#analytics-table tbody tr').first.locator('td').nth(3).text_content() == '4'
        assert page.locator('#analytics-table tbody tr').first.locator('td').nth(4).text_content() == '6,38'
        assert page.locator('#analytics-table tbody tr').first.locator('td').nth(6).text_content() == '4'
        assert page.locator('#analytics-table tbody tr').first.locator('td').nth(7).text_content() == '2,63'
        assert page.locator('#analytics-credits .credit-chart-row').count() == 5
        assert '4' in page.locator('#analytics-credits .credit-chart-row').first.inner_text()
        assert '7 lượt học' in page.locator('#analytics-count').inner_text()
        page.locator('#analytics-year').select_option('2099–2100')
        assert page.locator('#analytics-trend .chart-point').count() == 2
        assert page.locator('#analytics-trend4 .chart-point').count() == 2
        assert '6,69' in page.locator('#analytics-weighted-summary').inner_text()
        assert '2,81' in page.locator('#analytics-weighted-summary').inner_text()
        assert page.locator('#analytics-credits .credit-chart-row').count() == 2
        assert '3 lượt học' in page.locator('#analytics-count').inner_text()
        page.locator('#analytics-year').select_option('')
        page.evaluate("document.getElementById('portal-search').value = 'TEST004'")
        first_point = page.locator('#analytics-trend circle.chart-point').first
        assert first_point.get_attribute('role') == 'button'
        first_point.click()
        assert page.locator('#portal-profile').is_visible()
        assert page.locator('#portal-term').input_value() == 'HỌC KỲ 1 - 2099-2100'
        assert page.locator('#portal-search').input_value() == ''
        assert page.locator('#portal-table tbody tr:not(.portal-term)').count() == 2
        assert page.locator('#portal-table .portal-term').first.inner_text() == 'HỌC KỲ 1 - 2099-2100'
        page.evaluate("window.workspaceNavigate('tab-dashboard')")
        page.locator('#analytics-trend circle.chart-point').nth(1).press('Enter')
        assert page.locator('#portal-term').input_value() == 'HỌC KỲ 2 - 2099-2100'
        assert page.locator('#portal-table tbody tr:not(.portal-term)').count() == 1
        assert page.locator('#portal-table .portal-term').first.inner_text() == 'HỌC KỲ 2 - 2099-2100'
        page.evaluate("window.workspaceNavigate('tab-dashboard')")
        page.locator('#analytics-trend circle.chart-point').nth(2).press('Space')
        assert page.locator('#portal-term').input_value() == 'HỌC KỲ 2 - 2100-2101'
        assert page.locator('#portal-table tbody tr:not(.portal-term)').count() == 1
        page.evaluate("window.workspaceNavigate('tab-dashboard')")
        page.locator('#analytics-trend4 circle.chart-point').first.click()
        assert page.locator('#portal-term').input_value() == 'HỌC KỲ 1 - 2099-2100'
        page.evaluate("window.workspaceNavigate('tab-dashboard')")
        page.locator('#analytics-year').select_option('2099–2100')
        grade_button = page.locator('#analytics-distribution .distribution-legend button').filter(has_text='A+')
        assert grade_button.count() == 1
        grade_button.click()
        assert page.locator('#portal-term').input_value() == ''
        assert page.locator('#portal-table tbody tr:not(.portal-term)').count() == 1
        assert page.locator('#portal-table tbody tr:not(.portal-term) td:first-child').inner_text() == 'TEST001E'
        page.evaluate("window.workspaceNavigate('tab-dashboard')")
        page.locator('#analytics-year').select_option('')
        grade_button = page.locator('#analytics-distribution .distribution-legend button').filter(has_text='A+')
        grade_button.click()
        assert page.locator('#portal-profile').is_visible()
        assert page.locator('#portal-term').input_value() == ''
        assert page.locator('#portal-table tbody tr:not(.portal-term)').count() == 2
        assert page.locator('#portal-table .portal-term').all_inner_texts() == [
            'HỌC KỲ 2 - 2100-2101', 'HỌC KỲ 1 - 2099-2100']
        assert page.locator('#portal-table tbody tr:not(.portal-term) td:nth-child(5)').all_inner_texts() == ['A+', 'A+']
        page.evaluate("window.workspaceNavigate('tab-dashboard')")
        grade_button = page.locator('#analytics-distribution .distribution-legend button').filter(has_text='A+')
        assert grade_button.count() == 1
        grade_button.click()
        assert page.locator('#portal-table tbody tr:not(.portal-term) td:nth-child(5)').all_inner_texts() == ['A+', 'A+']
        page.evaluate("window.workspaceNavigate('tab-dashboard')")
        grade_segment = page.locator('#analytics-distribution .chart-grade-segment[data-grade-letter="A+"]')
        assert grade_segment.get_attribute('role') == 'button'
        grade_segment.click(position={'x': 90, 'y': 3})
        assert page.locator('#portal-table tbody tr:not(.portal-term) td:nth-child(5)').all_inner_texts() == ['A+', 'A+']
        page.evaluate("window.workspaceNavigate('tab-dashboard')")
        for theme in ('light', 'dark'):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            page.screenshot(path=str(evidence / f'charts-{theme}.png'), full_page=True)
        page.locator('#analytics-trend circle.chart-point').first.focus()
        assert page.locator('#analytics-trend circle.chart-point').first.get_attribute('aria-label')
        page.locator('[data-language-choice="en"]').click()
        assert 'Grades across semesters' in page.locator('.analytics-trend').first.inner_text()
        assert '4-point scale' in page.locator('.analytics-trend-four').inner_text()
        assert 'Credit-weighted mean' in page.locator('.analytics-trend').first.inner_text()
        assert 'Credit-weighted mean' in page.locator('.analytics-trend-four').inner_text()
        assert '6.38' in page.locator('#analytics-trend').inner_text()
        assert '2.63' in page.locator('#analytics-trend4').inner_text()
        assert 'All attempts' in page.locator('#analytics-weighted-summary').inner_text()
        page.locator('.analytics-data-table summary').click()
        assert 'sum (grade × credits) / valid credits' in page.locator('#analytics-method').inner_text()
        assert 'Zero-credit attempts excluded from weighting: 1' in page.locator('#analytics-method').inner_text()
        page.locator('.analytics-data-table summary').click()
        assert 'Updated: 23/10/2026, 07:00:00' in page.locator('#analytics-status').inner_text()
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
        assert page.locator('#analytics-trend4 .chart-point').count() == 1
        assert '9' in page.locator('#analytics-weighted-summary').inner_text()
        assert '4' in page.locator('#analytics-weighted-summary').inner_text()
        assert '4' in page.locator('#analytics-trend4').inner_text()
        assert '—' in page.locator('#analytics-table').text_content()  # Missing grade stays missing.
        page.locator('#tab-btn-profile').click()
        page.locator('#system-logout').click()
        page.evaluate("window.workspaceNavigate('tab-dashboard')")
        assert page.locator('#analytics-trend svg').count() == 0
        assert page.locator('#analytics-trend4 svg').count() == 0
        assert page.locator('#analytics-distribution svg').count() == 0
        assert page.locator('#analytics-credits .credit-chart-row').count() == 0
        assert page.locator('#analytics-source-totals').inner_text() == ''
        assert page.locator('#analytics-table tbody tr').count() == 0
        assert not errors, errors
        browser.close()
    print('Charts: source grade 10/4 means, retakes/gaps, credits/letters, filters, VI/EN, themes, mobile, logout passed')


if __name__ == '__main__':
    main()
