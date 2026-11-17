"""Synthetic browser regression for corrected transcript display names."""

import json
from copy import deepcopy
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.presentation_fixture import common_route

DISPLAY_NAMES = [
    "Khai phá dữ liệu",
    "Chủ nghĩa xã hội khoa học",
    "Thị giác máy tính",
    "Nguyên lý các ngôn ngữ lập trình",
    "Thiết kế và đánh giá thuật toán",
    "Ngôn ngữ lập trình thế hệ hai",
    "Phương pháp nghiên cứu khoa học",
]


def main():
    person_name = "Nguyễn Lễ"
    attempts = []
    display_names = {}
    for index, name in enumerate(DISPLAY_NAMES, start=1):
        key = f"synthetic-row-{index}"
        attempts.append({
            "row_key": key,
            "term": "HỌC KỲ 1 - 2099-2100",
            "code": f"SYN{index:03d}",
            "name": name.encode("utf-8").decode("latin1"),
            "credits": "3",
            "grade10": "8,5",
            "letter": "B+",
            "grade4": "3,5",
        })
        display_names[key] = name

    # Missing mapping/key retains the raw source string. An untrusted projected
    # value must be rendered as text, never interpreted as markup.
    attempts.extend([
        {"row_key": "synthetic-fallback", "term": "HỌC KỲ 1 - 2099-2100",
         "code": "SYN008", "name": "Raw fallback name", "credits": "2",
         "grade10": "7", "letter": "B", "grade4": "3"},
        {"row_key": "synthetic-hostile", "term": "HỌC KỲ 1 - 2099-2100",
         "code": "SYN009", "name": "Raw hostile name", "credits": "1",
         "grade10": "9", "letter": "A", "grade4": "4"},
    ])
    display_names["synthetic-hostile"] = '<img src=x onerror="window.syntheticXss=true">'
    snapshot = {"source_summary": [], "unknown_rows": [], "attempts": attempts}
    original_snapshot = deepcopy(snapshot)
    profile = {
        "subject": "synthetic-only",
        "fetched_at": "2026-11-13T00:00:00+00:00",
        "last_synced_at": "2026-11-13T00:00:00+00:00",
        "profile": {"name": person_name.encode("utf-8").decode("latin1"), "program": "Synthetic program", "cohort": "2099"},
        "display_profile": {"name": person_name},
        "snapshot": snapshot,
        "display_names": display_names,
    }

    scenario = {"omit_display_names": False}

    def intercept(route):
        path = urlsplit(route.request.url).path
        if path == "/auth/session":
            route.fulfill(json=session_payload())
        elif path == "/me/semester-plans":
            route.fulfill(json={"plans": []})
        elif path == "/me/course-status":
            route.fulfill(json={
                "status": "needs_program_binding", "can_plan": False,
                "blocking_reasons": ["source_incomplete", "program_binding_unverified"],
                "courses": None, "progress": None, "plan": None,
            })
        elif path == "/me/academic-program":
            route.fulfill(status=404, json={"detail": "not_found"})
        elif path == "/me/profile":
            result = deepcopy(profile)
            if scenario["omit_display_names"]:
                result.pop("display_names")
                result.pop("display_profile")
            route.fulfill(content_type="application/json", body=json.dumps(result, ensure_ascii=False))
        elif path.startswith(("/auth/", "/me/")):
            route.fulfill(content_type="application/json", body="{}")
        elif not route.request.url.startswith("http://127.0.0.1:8000/"):
            route.abort()
        else:
            assert common_route(route), route.request.url

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(error.stack or str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/")
        page.locator("#tab-btn-profile").click()
        page.wait_for_function("!document.getElementById('portal-profile').hidden")
        assert page.locator('#portal-name').inner_text() == person_name

        table = page.locator("#portal-table")
        for index, name in enumerate(DISPLAY_NAMES, start=1):
            row = table.locator("tbody tr:not(.portal-term)").filter(has_text=f"SYN{index:03d}")
            assert row.count() == 1
            assert name in row.inner_text()
            assert "8,5" in row.inner_text() and "B+" in row.inner_text() and "3,5" in row.inner_text()
        assert "Raw fallback name" in table.inner_text()
        assert table.locator("img, script").count() == 0
        assert '<img src=x onerror="window.syntheticXss=true">' in table.inner_text()
        assert page.evaluate("window.syntheticXss !== true")

        page.locator("#portal-search").fill("Thị giác máy tính")
        assert table.locator("tbody tr:not(.portal-term)").count() == 1
        assert "SYN003" in table.inner_text()
        page.locator("#portal-search").fill("SYN005")
        assert table.locator("tbody tr:not(.portal-term)").count() == 1
        assert "Thiết kế và đánh giá thuật toán" in table.inner_text()

        page.locator('[data-language-choice="en"]').click()
        assert page.locator('#portal-name').inner_text() == person_name
        assert DISPLAY_NAMES[4] in table.inner_text()
        page.set_viewport_size({"width": 390, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.reload()
        page.locator("#tab-btn-profile").click()
        page.wait_for_function("!document.getElementById('portal-profile').hidden")
        assert page.locator('#portal-name').inner_text() == person_name
        for name in DISPLAY_NAMES:
            assert name in page.locator("#portal-table").inner_text()
        scenario["omit_display_names"] = True
        page.reload()
        page.locator("#tab-btn-profile").click()
        page.wait_for_function("!document.getElementById('portal-profile').hidden")
        raw_fallback = DISPLAY_NAMES[0].encode("utf-8").decode("latin1")
        assert page.locator('#portal-name').inner_text() == profile['profile']['name']
        assert raw_fallback in page.locator("#portal-table").inner_text()
        page.locator('[data-language-choice="vi"]').click()
        assert DISPLAY_NAMES[6].encode("utf-8").decode("latin1") in page.locator("#portal-table").inner_text()
        scenario['omit_display_names'] = False
        profile['display_profile']['name'] = '<img src=x onerror="window.syntheticXss=true">'
        page.reload()
        page.locator('#tab-btn-profile').click()
        page.wait_for_function("!document.getElementById('portal-profile').hidden")
        assert page.locator('#portal-name img, #portal-name script').count() == 0
        assert page.locator('#portal-name').inner_text() == profile['display_profile']['name']
        assert page.evaluate('window.syntheticXss !== true')
        assert snapshot == original_snapshot
        assert not errors, errors
        browser.close()
    print("Portal encoding: corrected display projection, search, fallback, grades, VI/EN, mobile, reload and XSS text passed")


if __name__ == "__main__":
    main()
