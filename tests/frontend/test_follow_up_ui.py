"""End-to-end Playwright tests verifying follow-up pronoun resolution in HUS lookup tab."""

import json
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect, sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.presentation_fixture import common_route


def _launch_browser(p):
    try:
        return p.chromium.launch(headless=True)
    except PlaywrightError:
        return p.chromium.launch(channel="chrome", headless=True)


def test_follow_up_pronoun_resolution_in_ui():
    chat_requests = []
    server_history = {}

    sample = {
        "subject": "synthetic-only",
        "fetched_at": "2026-10-23T00:00:00+00:00",
        "profile": {"program": "Khoa học dữ liệu", "cohort": "68"},
        "snapshot": {"source_summary": [["Tổng tín chỉ: 6"]], "unknown_rows": [], "attempts": []},
    }

    def intercept(route):
        url = route.request.url
        path = urlsplit(url).path
        if path == "/auth/session":
            route.fulfill(json=session_payload())
        elif path.startswith("/me/"):
            route.fulfill(json=sample)
        elif path == "/hus/chat/history":
            qs = parse_qs(urlsplit(url).query)
            major = qs.get("major", ["data_science"])[0]
            if route.request.method == "DELETE":
                server_history[major] = []
                route.fulfill(json={"status": "cleared"})
            elif route.request.method == "POST":
                data = json.loads(route.request.post_data)
                server_history.setdefault(major, []).append(data)
                route.fulfill(json={"status": "saved", "count": len(server_history[major])})
            else:
                route.fulfill(
                    json={
                        "account_id": "synthetic-student",
                        "major": major,
                        "messages": server_history.get(major, []),
                    }
                )
        elif path == "/hus/chat":
            req_data = json.loads(route.request.post_data)
            chat_requests.append(req_data)
            code = req_data.get("course_code")
            if code == "CME1000":
                route.fulfill(
                    json={
                        "mode": "hus_rag",
                        "reply": "### Thông tin học phần\n- **Mã học phần:** CME1000\n- **Điều kiện tiên quyết:** Không",
                        "generation_mode": "grounded_llm",
                        "hus_answer": {
                            "status": "answered",
                            "facts": {"course_code": "CME1000", "field": "prerequisites"},
                            "citations": [],
                        },
                    }
                )
            else:
                route.fulfill(
                    json={
                        "mode": "hus_rag",
                        "reply": "### Thông tin học phần\n- **Mã học phần:** CME1000\n- **Số tín chỉ:** 3",
                        "generation_mode": "grounded_llm",
                        "hus_answer": {
                            "status": "answered",
                            "facts": {"course_code": "CME1000", "credits": 3},
                            "citations": [],
                        },
                    }
                )
        else:
            assert common_route(route, llm_rewrite_available=True), url

    with sync_playwright() as p:
        browser = _launch_browser(p)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.route("**/*", intercept)
        page.goto("http://localhost:8000/")

        # Open lookup tab
        lookup_tab_btn = page.locator("#tab-btn-lookup")
        expect(lookup_tab_btn).to_be_visible()
        lookup_tab_btn.click()

        # Step 1: First query explicitly naming course
        question_input = page.locator("#lookup-question")
        send_btn = page.locator("#lookup-send")
        rewrite = page.get_by_role("checkbox", name="Cho phép gửi câu hỏi tới Gemini để diễn đạt")
        expect(question_input).to_be_visible()
        expect(rewrite).to_be_enabled()
        expect(rewrite).not_to_be_checked()

        question_input.fill("môn CME1000 có mấy tín chỉ")
        with page.expect_response(lambda r: "/hus/chat" in r.url):
            send_btn.click()

        # Wait for reply
        expect(page.locator(".rag-message-assistant").last).to_contain_text("CME1000")
        assert len(chat_requests) == 1
        assert chat_requests[0]["allow_llm_rewrite"] is False
        assert "course_code" not in chat_requests[0] or chat_requests[0]["course_code"] is None

        # Step 2: Follow-up query using pronoun "môn đó"
        rewrite.check()
        question_input.fill("môn đó có điều kiện tiên quyết không?")
        with page.expect_response(lambda r: "/hus/chat" in r.url):
            send_btn.click()

        # Wait for second reply
        expect(page.locator(".rag-message-assistant").last).to_contain_text("Điều kiện tiên quyết")
        assert len(chat_requests) == 2
        assert chat_requests[1]["allow_llm_rewrite"] is True
        # Assert client resolved pronoun and injected course_code="CME1000"
        assert chat_requests[1].get("course_code") == "CME1000"

        question_input.fill("môn này có khó k")
        with page.expect_response(lambda r: urlsplit(r.url).path == "/hus/chat"):
            send_btn.click()
        assert chat_requests[2]["question"] == "môn này có khó k"
        assert chat_requests[2]["course_code"] == "CME1000"
        assert chat_requests[2]["allow_llm_rewrite"] is True

        # Step 3: Click "+ Đoạn chat mới" to clear session context
        new_chat_btn = page.locator("#lookup-new-chat")
        new_chat_btn.click()
        expect(page.locator(".rag-message")).to_have_count(1)
        expect(rewrite).not_to_be_checked()

        # Step 4: After clearing, asking "môn đó học như thế nào?" does not carry stale course code
        question_input.fill("môn đó học như thế nào?")
        with page.expect_response(lambda r: "/hus/chat" in r.url):
            send_btn.click()

        expect(page.locator(".rag-message-assistant").last).to_be_visible()
        assert len(chat_requests) == 4
        assert chat_requests[3]["allow_llm_rewrite"] is False
        assert "course_code" not in chat_requests[3] or chat_requests[3]["course_code"] is None

        browser.close()
