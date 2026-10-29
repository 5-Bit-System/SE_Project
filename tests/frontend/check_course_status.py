"""Three-color board regression with intercepted synthetic data; no VNU access."""

import copy
import json
import mimetypes
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload


def course(code, name, credits=3, **changes):
    return {"code": code, "name": name, "name_en": None, "credits": credits,
            "requirement_type": "required", "counted_in_total": True, "groups": [],
            "reasons": [], "suggested": False, **changes}


def main():
    group = {"id": "choice", "name": "Synthetic elective group", "earned_credits": 0,
             "required_credits": 3, "remaining_credits": 3}
    data = {
        "status": "ready", "context_revision": "synthetic-revision", "blocking_reasons": [],
        "catalog_status": "draft_unverified", "selections": {},
        "courses": {
            "completed": [course("TEST-A", "Synthetic completed")],
            "eligible": [course("TEST-B", "Synthetic required", 4, suggested=True,
                                counted_in_total=False, eligibility_basis="excluded_from_total"),
                         course("TEST-E1", "<img src=x onerror=alert(1)>",
                                requirement_type="elective", groups=[group], suggested=True,
                                eligibility_basis="requested_default"),
                         course("TEST-E2", "Synthetic alternative", requirement_type="elective",
                                groups=[group], eligibility_basis="no_prerequisites",
                                result_pending=True)],
            "blocked": [course("TEST-C", "Synthetic blocked", reasons=[{
                "kind": "missing_prerequisites", "missing_prerequisites": [
                    ["TEST-B", "TEST-OR"], ["TEST-AND"]]}]),
                        course("TEST-D", "Synthetic unknown", reasons=[{
                            "kind": "prerequisite_unknown", "missing_prerequisites": []}])],
        },
        "progress": {"total": {"earned_credits": 3, "required_credits": 120,
                               "remaining_credits": 117}},
        "plan": {"max_credits": 20, "suggested_credits": 7,
                 "course_codes": ["TEST-B", "TEST-E1"], "offering_status": "unknown"},
    }
    source = {"profile": {"program": "Synthetic program", "cohort": "79"},
              "snapshot": {"completeness": "complete", "attempts": []}}
    source.update(subject='synthetic-only', expires_in=7200)
    requests, errors, pending = [], [], []
    mode = "ready"

    def intercept(route):
        parsed = urlparse(route.request.url)
        path = parsed.path
        requests.append(path)
        if path == '/me/course-status':
            if mode == 'pending':
                pending.append(route)
                return
            if mode == 'expired':
                route.fulfill(status=401, content_type='application/json', body='{}')
                return
            result = copy.deepcopy(data)
            budget = int(parse_qs(parsed.query)['max_credits'][0])
            if budget == 6:
                result['plan'].update(course_codes=['TEST-B'], suggested_credits=4, max_credits=6)
            if mode == 'unready':
                result.update(status='needs_program_binding', courses=None, progress=None, plan=None,
                              blocking_reasons=['source_incomplete', 'program_binding_unverified'])
            if mode == 'paused':
                result.update(status='partial', can_plan=False,
                              blocking_reasons=['graduation_selection_required'])
                result['plan'].update(course_codes=[], suggested_credits=0)
            route.fulfill(content_type='application/json', body=json.dumps(result))
        elif path == '/me/semester-plans':
            route.fulfill(json={'plans': []})
        elif path == '/auth/session':
            route.fulfill(json=session_payload())
        elif path == '/me/profile':
            route.fulfill(json=source)
        elif parsed.hostname == '127.0.0.1' and (path == '/' or path.startswith('/static/')):
            static = Path(__file__).resolve().parents[2] / 'app/static'
            file = static / ('index.html' if path == '/' else path.removeprefix('/static/'))
            if file.is_file():
                route.fulfill(body=file.read_bytes(), content_type=mimetypes.guess_type(file)[0] or 'text/plain')
            else:
                route.fulfill(status=404)
        else:
            route.abort()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1050})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', intercept)
        page.goto('http://127.0.0.1:8000/#rules')
        root = page.locator('#course-status-board')
        page.wait_for_selector('[data-course-code="TEST-A"]')

        def emit_source():
            page.evaluate("value => document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: value}))", source)

        emit_source()
        page.wait_for_selector('[data-course-code="TEST-A"]')
        assert root.locator('.course-state-completed .course-status-card').count() == 1
        assert root.locator('.course-state-eligible .course-status-card').count() == 3
        assert root.locator('.course-state-blocked .course-status-card').count() == 2
        assert page.locator('#course-credit-budget').input_value() == '20'
        assert 'TEST-B hoặc TEST-OR' in root.inner_text() and 'và (TEST-AND)' in root.inner_text()
        assert root.locator('img').count() == 0
        assert '<img src=x' in root.inner_text()
        assert 'môn không tính vào tín chỉ tích lũy' in root.locator('[data-course-code="TEST-B"]').inner_text()
        assert 'mặc định đã chọn; điều kiện tiên quyết đã thỏa' in root.locator('[data-course-code="TEST-E1"]').inner_text()
        assert 'môn không có điều kiện tiên quyết' in root.locator('[data-course-code="TEST-E2"]').inner_text()
        assert 'chưa tính là đã hoàn thành' in root.locator('[data-course-code="TEST-E2"]').inner_text()
        assert '7 / 20 TC' in root.inner_text()
        page.locator('[data-plan-code="TEST-E2"]').click()
        assert not page.locator('[data-plan-code="TEST-E2"]').is_checked()
        assert 'đủ yêu cầu' in root.locator('.course-plan-error').inner_text()
        page.locator('[data-plan-code="TEST-E1"]').uncheck()
        page.locator('[data-plan-code="TEST-E2"]').check()
        assert page.locator('[data-plan-code="TEST-E2"]').is_checked()
        assert root.locator('[data-course-code="TEST-C"]').count() == 1
        assert root.locator('.course-state-completed [data-course-code="TEST-B"]').count() == 0
        page.locator('#course-credit-budget').fill('6')
        root.get_by_role('button', name='Áp dụng', exact=True).click()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('7 / 6 TC')")
        assert page.locator('[data-plan-code="TEST-E2"]').is_checked()
        assert 'vượt ngân sách mới' in root.locator('.course-plan-error').inner_text()
        page.locator('[data-plan-code="TEST-E2"]').uncheck()
        page.locator('[data-plan-code="TEST-E1"]').click()
        assert not page.locator('[data-plan-code="TEST-E1"]').is_checked()
        assert 'vượt mức tín chỉ' in root.locator('.course-plan-error').inner_text()
        root.locator('input[type=search]').fill('TEST-C')
        assert root.locator('.course-status-card').count() == 1
        root.locator('input[type=search]').fill('')
        page.locator('[data-language-choice="en"]').click()
        assert 'Your course map' in root.inner_text()
        assert '(TEST-B or TEST-OR) and (TEST-AND)' in root.inner_text()
        assert root.locator('[data-course-code="TEST-E1"] h4').inner_text().startswith('<img')
        assert 'this course has no prerequisites' in root.locator('[data-course-code="TEST-E2"]').inner_text()
        assert 'excluded from earned program credits' in root.locator('[data-course-code="TEST-B"]').inner_text()
        assert page.locator('[data-plan-code="TEST-B"]').is_checked()
        page.locator('[data-language-choice="vi"]').click()
        mode = 'paused'
        root.get_by_role('button', name='Cập nhật', exact=True).click()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('Chọn nhánh tốt nghiệp')")
        assert root.locator('.course-state-eligible .course-status-card').count() == 3
        for plan_input in root.locator('input[data-plan-code]').all():
            assert plan_input.is_disabled()
        # Existing edited drafts survive a pause, but no action can persist them.
        assert page.locator('[data-plan-code="TEST-B"]').is_checked()
        assert root.locator('#semester-plan-form button[type=submit]').is_disabled()
        mode = 'ready'
        root.get_by_role('button', name='Cập nhật', exact=True).click()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('4 / 6 TC')")
        evidence = Path('backups/local_runtime/course-status')
        evidence.mkdir(parents=True, exist_ok=True)
        for theme in ('light', 'dark'):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            for width in (1600, 390):
                page.set_viewport_size({"width": width, "height": 1050})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=str(evidence / f'{theme}-{width}.png'), full_page=True)
        page.set_viewport_size({"width": 1440, "height": 1050})
        mode = 'unready'
        root.get_by_role('button', name='Cập nhật', exact=True).click()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('Chưa xác minh chương trình')")
        assert root.locator('.course-status-card').count() == 0
        assert root.locator('.course-status-column').count() == 3
        mode = 'ready'
        root.get_by_role('button', name='Cập nhật', exact=True).click()
        page.wait_for_selector('[data-course-code="TEST-A"]')
        mode = 'pending'
        root.get_by_role('button', name='Cập nhật', exact=True).click()
        page.wait_for_timeout(100)
        assert pending
        page.evaluate("document.dispatchEvent(new Event('workspace:session-expired'))")
        assert 'Đăng nhập VNU' in root.inner_text()
        for route in pending:
            route.fulfill(content_type='application/json', body=json.dumps(data))
        page.wait_for_timeout(100)
        assert root.locator('.course-status-card').count() == 0
        assert root.locator('input[type=search]').input_value() == ''
        mode = 'expired'
        emit_source()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('Đăng nhập VNU')")
        assert root.locator('.course-status-card').count() == 0
        assert not errors, errors
        assert not set(requests) & {'/eligibility', '/recommendations', '/transcript/summary', '/programs'}
        assert page.evaluate("Object.keys(localStorage).every(key => key.startsWith('study-workspace-'))")
        browser.close()
    print('Course board: states, reasons, quotas, budget, search, VI/EN, themes/mobile and logout race passed')


if __name__ == '__main__':
    main()
