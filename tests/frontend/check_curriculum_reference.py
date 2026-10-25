"""Browser regression using real public curriculum facts; all personal/network I/O blocked."""

import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from app.curriculum_reference import ReferenceError, list_references, plan_reference, reference

    index = list_references()
    talent = "toan_hoc_tai_nang_7460101_2022"
    requests, errors, pending = [], [], []
    delay_plan = False
    live_http = "--live" in sys.argv

    def intercept(route):
        parsed = urlparse(route.request.url)
        path = parsed.path
        requests.append(path)
        if live_http and path.startswith("/curricula/reference"):
            response = route.fetch()
            if delay_plan and path.endswith("/plan") and response.ok:
                pending.append((route, response.json()))
                return
            route.fulfill(response=response)
            return
        if path == "/curricula/reference":
            route.fulfill(content_type="application/json", body=json.dumps(index))
        elif path.startswith("/curricula/reference/"):
            program = path.split("/")[3]
            try:
                if path.endswith("/plan"):
                    payload = route.request.post_data_json
                    result = plan_reference(program, **payload)
                    if delay_plan:
                        pending.append((route, result))
                        return
                else:
                    result = reference(program, int(parse_qs(parsed.query).get("cohort", [67])[0]))
                route.fulfill(content_type="application/json", body=json.dumps(result))
            except ReferenceError as exc:
                route.fulfill(status=422, content_type="application/json",
                              body=json.dumps({"detail": str(exc)}))
        elif path.startswith(("/me/", "/auth/")):
            route.fulfill(status=401, content_type="application/json",
                          body=json.dumps({"detail": "session_expired"}))
        elif parsed.hostname == "127.0.0.1" and (path == "/" or path.startswith("/static/")):
            route.continue_()
        else:
            route.abort()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1050})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/#rules")
        root = page.locator("#curriculum-reference")
        page.wait_for_function("document.querySelectorAll('.reference-program-card').length === 5")
        assert root.is_visible() and page.locator("#course-status-board").is_hidden()
        assert page.locator("#workspace-program").inner_text() == "Chưa đăng nhập"
        assert page.locator("#reference-cohort").input_value() == "67"
        for program in index["programs"]:
            page.locator("#reference-program").select_option(program["program_id"])
            page.wait_for_function("count => document.querySelectorAll('.reference-table tbody tr').length === count",
                                   arg=program["course_count"])
            assert page.locator("#reference-credit-budget").input_value() == "20"
            assert program["name"] in root.inner_text()
        page.locator("#reference-program").select_option(talent)
        page.wait_for_function("document.querySelectorAll('.reference-table tbody tr').length === 96")
        page.locator("#reference-cohort").select_option("68")
        page.wait_for_function("document.querySelectorAll('.reference-table tbody tr').length === 96")
        assert "168 TC" in root.inner_text() and "97 dòng nguồn" in root.inner_text()
        page.locator("#reference-search").fill("giai tich")
        assert page.locator(".reference-table tbody tr").count() > 5
        page.locator("#reference-search").fill("MAT2303")
        assert page.locator(".reference-table tbody tr").count() == 1
        page.locator('[data-reference-plan="MAT2303"]').check()
        page.wait_for_function("document.querySelector('.reference-budget-form strong').textContent === '5 / 20 TC'")
        assert "Cần đối chiếu môn tiên quyết" in root.inner_text()
        page.locator("#reference-search").fill("MAT2302")
        page.locator('[data-reference-plan="MAT2302"]').check()
        page.wait_for_function("document.querySelector('.reference-budget-form strong').textContent === '10 / 20 TC'")
        assert "Cần đối chiếu môn tiên quyết" in root.inner_text()
        page.locator("#reference-credit-budget").fill("9")
        root.get_by_role("button", name="Áp dụng", exact=True).click()
        page.wait_for_selector(".reference-error")
        assert "vượt ngân sách" in root.locator(".reference-error").inner_text()
        assert page.locator("#reference-credit-budget").input_value() == "20"
        page.locator("#reference-credit-budget").fill("12")
        root.get_by_role("button", name="Áp dụng", exact=True).click()
        page.wait_for_function("document.querySelector('.reference-budget-form strong').textContent === '10 / 12 TC'")
        page.locator("#reference-search").fill("MAT2320")
        page.locator('[data-reference-plan="MAT2320"]').click()
        page.wait_for_selector(".reference-error")
        assert page.locator(".reference-selected button").count() == 2
        root.get_by_role("button", name="Bỏ chọn tất cả", exact=True).click()
        page.wait_for_function("document.querySelectorAll('.reference-selected button').length === 0")
        root.get_by_role("button", name="Gợi ý môn không ghi tiên quyết", exact=True).click()
        page.wait_for_function("document.querySelectorAll('.reference-selected button').length > 0")
        assert int(root.locator(".reference-budget-form strong").inner_text().split(" / ")[0]) <= 12
        with page.expect_download() as download:
            root.get_by_role("button", name="Tải kế hoạch CSV", exact=True).click()
        exported = download.value
        assert exported.suggested_filename == f"ke-hoach-{talent}-K68.csv"
        assert "Hypothetical plan; eligibility not evaluated" in Path(exported.path()).read_text(encoding="utf-8-sig")
        page.locator("#reference-search").fill("")
        page.locator("#reference-group").select_option("theory")
        assert page.locator(".reference-table tbody tr").count() == 8
        page.locator("#reference-group").select_option("")
        page.locator("#reference-type").select_option("graduation")
        assert page.locator(".reference-table tbody tr").count() == 1
        assert "MAT4074" in page.locator(".reference-table").inner_text()
        page.locator("#reference-type").select_option("")
        page.locator("#reference-search").fill("MAT3359")
        root.get_by_role("button", name="MAT3359", exact=True).click()
        assert page.locator("dialog").is_visible()
        assert "MAT1202" in page.locator("dialog").inner_text()
        assert page.locator('dialog a[href$="#page=12"]').count() == 1
        page.locator("dialog").get_by_role("button", name="Đóng", exact=True).click()
        page.locator("#reference-search").fill("")
        # A delayed plan from the previous program cannot restore its selection.
        delay_plan = True
        root.locator('.reference-selected button').first.click()
        page.wait_for_timeout(80)
        assert pending
        other = "khdl_7460108_2022"
        page.locator("#reference-program").select_option(other)
        page.wait_for_function("document.querySelectorAll('.reference-table tbody tr').length === 65")
        for route, result in pending:
            route.fulfill(content_type="application/json", body=json.dumps(result))
        page.wait_for_timeout(80)
        assert page.locator(".reference-selected button").count() == 0
        assert page.locator("#reference-program").input_value() == other
        delay_plan = False
        page.locator("[data-language-choice=en]").click()
        assert "Explore course requirements" in root.inner_text()
        assert "Khoa học dữ liệu" in root.inner_text()
        assert page.locator("#reference-cohort").input_value() == "68"
        page.locator("[data-language-choice=vi]").click()
        evidence = Path("backups/curriculum_lookup_20261024/ui")
        evidence.mkdir(parents=True, exist_ok=True)
        for theme in ("light", "dark"):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            for width in (1600, 390):
                page.set_viewport_size({"width": width, "height": 1050})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(evidence / f"reference-{theme}-{width}.png"), full_page=True)
        page.locator("#course-mode-personal").click()
        assert root.is_hidden()
        assert "Đăng nhập VNU" in page.locator("#course-status-board").inner_text()
        page.locator("#course-mode-reference").click()
        assert root.is_visible()
        assert page.locator("#workspace-program").inner_text() == "Chưa đăng nhập"
        assert not errors, errors
        assert not set(requests) & {"/programs", "/eligibility", "/recommendations", "/transcript/summary"}
        assert page.evaluate("Object.keys(localStorage).every(key => key.startsWith('study-workspace-'))")
        browser.close()
    print("Curriculum lookup: all five sources, cohorts, prerequisites, PDF links, 20-credit planning, filters, CSV, stale-response isolation, VI/EN and mobile passed")


if __name__ == "__main__":
    main()
