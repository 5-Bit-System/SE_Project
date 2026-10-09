"""Browser integration tests; install requirements-ui.txt and Chromium to run."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture(scope="module")
def browser():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as driver:
        if not Path(driver.chromium.executable_path).exists():
            pytest.skip("Install Chromium with python -m playwright install chromium")
        browser = driver.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def ui(browser):
    # Serve the actual FastAPI/static app through request interception. Requests
    # can be held and released in any order without sleeps or an external server.
    with TestClient(app) as client:
        page = browser.new_page()
        page.add_init_script("""
            window.completedResponses = 0;
            const originalFetch = window.fetch;
            window.fetch = async (...args) => {
                const response = await originalFetch(...args);
                const originalJson = response.json.bind(response);
                response.json = async () => {
                    const data = await originalJson();
                    setTimeout(() => { ++window.completedResponses; }, 0);
                    return data;
                };
                return response;
            };
        """)
        state = {"hold_next": None, "held": [], "error_next": None, "requests": []}

        def serve(route):
            request = route.request
            url = urlsplit(request.url)
            path = url.path + (f"?{url.query}" if url.query else "")
            program_id = parse_qs(url.query).get("program_id", [None])[0]
            key = program_id if url.path == "/courses" else url.path
            state["requests"].append((request.method, path, request.post_data))
            if state["hold_next"] == key:
                state["hold_next"] = None
                state["held"].append(route)
                return
            if state["error_next"] == key:
                state["error_next"] = None
                route.fulfill(status=503, json={"detail": "Catalog tạm không tải được"})
                return
            response = client.request(request.method, path, content=request.post_data, headers=request.headers)
            route.fulfill(status=response.status_code, body=response.content, content_type=response.headers.get("content-type"))

        page.route("http://catalog.test/**", serve)
        page.goto("http://catalog.test/")
        page.wait_for_function("document.querySelector('#courses input') !== null")
        yield page, state, client
        page.close()


def wait_for_courses(page):
    page.wait_for_function("!document.querySelector('button[type=submit]').disabled")


def release_response(page, route, status, body):
    completed = page.evaluate("window.completedResponses")
    route.fulfill(status=status, json=body)
    page.wait_for_function("count => window.completedResponses > count", arg=completed)


def test_switching_all_four_programs_clears_passed_courses_and_results(ui):
    page, _, client = ui
    programs = client.get("/programs").json()
    assert page.locator("#program option").count() == 4
    for program in programs:
        page.select_option("#program", program["program_id"])
        wait_for_courses(page)
        actual = page.locator("#courses input").evaluate_all("inputs => inputs.map(input => input.value)")
        expected = client.get("/courses", params={"program_id": program["program_id"]}).json()
        assert actual == [course["code"] for course in expected]
        assert page.locator("#courses input:checked").count() == 0
        assert page.locator("#result article").count() == 0
        assert program["name"] in page.locator("#catalog-note").inner_text()
        page.locator("#courses input").first.check()
        page.click("button[type=submit]")
        page.wait_for_function("document.querySelector('#result article') !== null")


@pytest.mark.parametrize("status", [200, 503])
def test_out_of_order_course_response_cannot_replace_current_program(ui, status):
    page, state, client = ui
    programs = client.get("/programs").json()
    old_id, new_id = programs[1]["program_id"], programs[2]["program_id"]
    state["hold_next"] = old_id
    page.select_option("#program", old_id)
    page.wait_for_function("document.querySelector('button[type=submit]').disabled")
    assert len(state["held"]) == 1
    page.select_option("#program", new_id)
    wait_for_courses(page)
    # Return to the same ID: comparing only the selected ID would miss this race.
    page.select_option("#program", old_id)
    wait_for_courses(page)
    expected = page.locator("#courses").inner_text()
    route = state["held"].pop()
    release_response(page, route, status, [{"code": "STALE", "name": "Old data", "credits": 3}] if status == 200 else {"detail": "Old error"})
    assert page.locator("#courses").inner_text() == expected
    assert page.locator("#program").input_value() == old_id
    assert page.locator("button[type=submit]").is_enabled()


@pytest.mark.parametrize("status", [200, 503])
def test_old_recommendation_response_cannot_survive_program_change(ui, status):
    page, state, client = ui
    state["hold_next"] = "/recommendations"
    page.click("button[type=submit]")
    page.wait_for_function("document.querySelector('#result').textContent.includes('Đang kiểm tra')")
    assert len(state["held"]) == 1
    new_id = client.get("/programs").json()[1]["program_id"]
    page.select_option("#program", new_id)
    wait_for_courses(page)
    route = state["held"].pop()
    release_response(page, route, status, {"warnings": [], "recommendations": [{"code": "STALE", "name": "Old result", "credits": 3, "reason": "Old reason"}]} if status == 200 else {"detail": "Old error"})
    assert page.locator("#result").inner_text() == "Chọn môn đã qua rồi xem gợi ý."
    assert page.locator("#result article").count() == 0


def test_course_failure_clears_selection_and_blocks_submission_until_retry(ui):
    page, state, client = ui
    page.locator("#courses input").first.check()
    programs = client.get("/programs").json()
    state["error_next"] = programs[1]["program_id"]
    page.select_option("#program", programs[1]["program_id"])
    page.wait_for_function("document.querySelector('#courses').textContent.includes('tạm không tải được')")
    assert page.locator("#courses input:checked").count() == 0
    assert page.locator("button[type=submit]").is_disabled()
    page.select_option("#program", programs[2]["program_id"])
    wait_for_courses(page)
    page.locator("#courses input").first.check()
    selected = page.locator("#courses input:checked").input_value()
    page.click("button[type=submit]")
    page.wait_for_function("document.querySelector('#result article') !== null")
    payload = json.loads(next(body for method, path, body in reversed(state["requests"]) if path == "/recommendations"))
    assert payload["program_id"] == programs[2]["program_id"]
    assert payload["passed_course_codes"] == [selected]


def test_validation_detail_array_is_displayed_as_readable_text(ui):
    page, _, _ = ui
    page.fill("#credits", "31")
    # Exercise the API guard even if the browser's native form validation is bypassed.
    page.evaluate("document.querySelector('#recommend-form').dispatchEvent(new Event('submit', {cancelable: true}))")
    page.wait_for_function("document.querySelector('#result').textContent.includes('body.max_credits')")
    assert "[object Object]" not in page.locator("#result").inner_text()
