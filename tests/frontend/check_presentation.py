"""Presentation audit with invented records; real auth and personal I/O are blocked."""

import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

NAVIGATION = ["tab-btn-dashboard", "tab-btn-profile", "tab-btn-rules", "tab-btn-recommend"]
VIETNAMESE = "Đường đến học phần tiếp theo: điều kiện, tín chỉ và kết quả đã ghi nhận."


def contrast(page, selector, property_name="color", pseudo=None):
    """WCAG text contrast including ancestor surface fills, rather than token guesses."""
    return page.locator(selector).first.evaluate(r"""(node, {property, pseudo}) => {
      const rgba = value => (value.match(/[\d.]+/g) || []).map(Number);
      const ancestors = []; for (let n = node; n; n = n.parentElement) ancestors.unshift(n);
      let background = [255, 255, 255];
      for (const n of ancestors) {
        const channels = rgba(getComputedStyle(n).backgroundColor), alpha = channels[3] ?? 1;
        background = background.map((value, i) => (channels[i] || 0) * alpha + value * (1-alpha));
      }
      const foreground = rgba(getComputedStyle(node, pseudo)[property]);
      const luminance = rgb => rgb.slice(0, 3).map(value => {
        value /= 255; return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
      }).reduce((sum, value, i) => sum + value * [.2126, .7152, .0722][i], 0);
      const a = luminance(foreground), b = luminance(background);
      return Math.round(((Math.max(a,b)+.05)/(Math.min(a,b)+.05))*100)/100;
    }""", {"property": property_name, "pseudo": pseudo})


def main():
    evidence = Path("backups/frontend_polish_20261028/after")
    evidence.mkdir(parents=True, exist_ok=True)
    sample = {
        "subject": "synthetic-only", "expires_in": 1800, "fetched_at": "2026-10-28T00:00:00Z",
        "profile": {"name": "Sinh viên kiểm thử", "program": "Chương trình minh họa",
                    "cohort": "79"},
        "snapshot": {
            "completeness": "complete", "unknown_rows": [],
            "source_summary": [["Tổng tín chỉ: 10"], ["Tổng tín chỉ tích lũy: 6"]],
            "attempts": [
                {"term": "HỌC KỲ 1 - 2099-2100", "code": "TEST001", "credits": "3",
                 "name": "Giải tích minh họa", "grade10": "8,5", "letter": "B+", "grade4": "3,5"},
                {"term": "HỌC KỲ 2 - 2099-2100", "code": "TEST002", "credits": "3",
                 "name": "Cấu trúc dữ liệu minh họa", "grade10": "7", "letter": "B", "grade4": "3"},
                {"term": "HỌC KỲ 1 - 2100-2101", "code": "TEST003", "credits": "4",
                 "name": "Phân tích và thiết kế hệ thống thông tin — môn kiểm thử",
                 "grade10": "", "letter": "I", "grade4": ""},
            ],
        },
    }

    def course(code, name, **changes):
        return {"code": code, "name": name, "name_en": None, "credits": 3,
                "requirement_type": "required", "counted_in_total": True,
                "groups": [], "reasons": [], "suggested": False, **changes}

    board = {
        "status": "ready", "context_revision": "synthetic-presentation", "blocking_reasons": [],
        "catalog_status": "draft_unverified", "selections": {},
        "courses": {
            "completed": [course("TEST001", "Giải tích minh họa"),
                          course("TEST002", "Cấu trúc dữ liệu minh họa")],
            "eligible": [course("TEST004", "Phân tích và thiết kế hệ thống thông tin minh họa",
                                eligibility_basis="no_prerequisites", suggested=True),
                         course("TEST005", "Kỹ năng bổ trợ minh họa", counted_in_total=False,
                                eligibility_basis="excluded_from_total", suggested=True)],
            "blocked": [course("TEST006", "Học phần cần điều kiện minh họa", reasons=[{
                "kind": "missing_prerequisites", "missing_prerequisites": [["TEST004"]]}])],
        },
        "progress": {"total": {"earned_credits": 6, "required_credits": 120,
                               "remaining_credits": 114}},
        "plan": {"max_credits": 20, "suggested_credits": 6,
                 "course_codes": ["TEST004", "TEST005"], "offering_status": "unknown"},
    }
    state = {"signed_in": True, "board": "ready"}
    pending_login, errors, outside, reports = [], [], [], []

    def intercept(route):
        parsed = urlparse(route.request.url)
        if parsed.hostname != "127.0.0.1":
            outside.append(parsed.hostname)
            route.abort()
            return
        path = parsed.path
        if path == "/me/profile":
            route.fulfill(status=200 if state["signed_in"] else 401,
                          content_type="application/json", body=json.dumps(
                              sample if state["signed_in"] else {"detail": "session_expired"}))
        elif path == "/me/course-status":
            route.fulfill(status=503 if state["board"] == "error" else 200,
                          content_type="application/json", body=json.dumps(
                              {"detail": "storage_unavailable"} if state["board"] == "error" else board))
        elif path == "/auth/logout":
            state["signed_in"] = False
            route.fulfill(content_type="application/json", body="{}")
        elif path == "/auth/portal":
            pending_login.append(route)
        elif path == "/" or path.startswith(("/static/", "/curricula/reference")):
            route.continue_()
        else:
            route.abort()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, color_scheme="light")
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/#dashboard")
        page.wait_for_function("document.querySelectorAll('#analytics-trend .chart-point').length === 2")
        assert page.locator(".nav-tabs .tab-btn").evaluate_all("nodes => nodes.map(n=>n.id)") == NAVIGATION
        assert page.locator(".workspace-body > .tab-panel").evaluate_all(
            "nodes => nodes.map(n=>n.id)") == ["tab-dashboard", "portal-dialog", "tab-rules", "tab-recommend"]
        for weight in (400, 500, 600, 700, 800):
            assert page.evaluate("""async ({weight, text}) => {
              await document.fonts.load(`${weight} 16px "Be Vietnam Pro"`, text);
              return document.fonts.check(`${weight} 16px "Be Vietnam Pro"`, text);
            }""", {"weight": weight, "text": VIETNAMESE})

        for theme in ("light", "dark"):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            for width in (1440, 1024, 390):
                page.set_viewport_size({"width": width, "height": 1000})
                expected_orientation = "horizontal" if width <= 800 else "vertical"
                page.wait_for_function("expected => document.querySelector('.nav-tabs').getAttribute('aria-orientation') === expected",
                                       arg=expected_orientation)
                for name, navigation in zip(("dashboard", "profile", "courses", "recommend"), NAVIGATION):
                    page.locator(f"#{navigation}").click()
                    if name == "courses":
                        page.locator("#course-mode-personal").click()
                        page.wait_for_selector('[data-course-code="TEST004"]')
                        assert contrast(page, "#course-status-board input[type=search]", pseudo="::placeholder") >= 4.5
                        for state_name in ("completed", "eligible", "blocked"):
                            assert contrast(page, f".course-status-column.course-state-{state_name} h3") >= 4.5
                    if name == "profile":
                        assert page.locator("#portal-table thead th").count() == 6
                        assert "8,5" in page.locator("#portal-table").inner_text()
                        assert page.locator("#portal-table").evaluate(
                            "n => getComputedStyle(n).fontVariantNumeric.includes('tabular-nums')")
                        assert contrast(page, ".profile-table-tools input", "borderTopColor") >= 3
                    if name == "dashboard":
                        assert page.locator("#analytics-trend svg").evaluate(
                            "n => n.getBoundingClientRect().width >= n.viewBox.baseVal.width")
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (theme, width, name)
                    assert page.locator(".tab-panel.active").count() == 1
                    assert page.locator(".source-notice").is_visible()
                    heading_size = page.locator(".tab-panel.active h2").first.evaluate(
                        "n => parseFloat(getComputedStyle(n).fontSize)")
                    assert 24 <= heading_size <= 36
                    for selector in (".source-notice p", ".tab-btn.active", ".sidebar-profile strong"):
                        value = contrast(page, selector)
                        assert value >= 4.5, (theme, selector, value)
                        reports.append({"theme": theme, "width": width, "screen": name,
                                        "selector": selector, "contrast": value})
                    if width == 390:
                        nav = page.locator(".nav-tabs")
                        assert nav.evaluate("n => n.scrollWidth <= n.clientWidth")
                    page.evaluate("scrollTo(0,0)")
                    page.mouse.move(0, 0)
                    page.screenshot(path=str(evidence / f"{name}-{theme}-{width}.png"), full_page=True,
                                    animations="disabled")
                page.locator('[data-language-choice="en"]').click()
                assert page.locator("html").get_attribute("lang") == "en"
                for navigation in NAVIGATION:
                    page.locator(f"#{navigation}").click()
                    assert page.locator("#workspace-program").inner_text() == "Chương trình minh họa"
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.locator('[data-language-choice="vi"]').click()

        # Existing tab keyboard flow and its visible focus remain available.
        page.locator("#tab-btn-dashboard").focus()
        page.keyboard.press("ArrowRight")
        assert page.locator("#tab-btn-profile").evaluate("n => n === document.activeElement")
        assert page.locator("#tab-btn-profile").evaluate(
            "n => n.matches(':focus-visible') && getComputedStyle(n).outlineStyle !== 'none'")
        page.locator("#tab-btn-rules").click()
        page.locator("#course-mode-reference").click()
        page.locator("#reference-program").select_option("khmtt_7480113qtd_2022")
        page.wait_for_selector(".reference-table tbody tr")
        region = page.locator(".reference-table-scroll")
        assert region.get_attribute("role") == "region"
        region.focus()
        page.keyboard.press("ArrowRight")
        page.wait_for_function("document.querySelector('.reference-table-scroll').scrollLeft > 0")
        page.locator(".reference-table tbody tr button").first.click()
        dialog = page.get_by_role("dialog")
        assert dialog.is_visible() and dialog.get_attribute("aria-label")
        assert dialog.evaluate("n => n.contains(document.activeElement)")
        page.keyboard.press("Escape")
        page.wait_for_selector(".reference-detail", state="detached")
        assert page.get_by_role("dialog").count() == 0
        assert page.locator(".reference-table tbody tr button").first.evaluate(
            "n => n === document.activeElement")

        page.locator("#tab-btn-profile").click()
        page.locator("#portal-search").fill("NO-MATCH-SYNTHETIC")
        assert "Không có học phần phù hợp" in page.locator("#portal-table").inner_text()
        page.locator("#portal-search").fill("")
        assert "8,5" in page.locator("#portal-table").inner_text()
        page.locator("#tab-btn-rules").click()
        page.locator("#course-mode-personal").click()
        search = page.locator("#course-status-board input[type=search]")
        search.fill("NO-MATCH-SYNTHETIC")
        assert page.locator(".course-status-empty", has_text="Không có môn phù hợp").count() == 3
        search.fill("")
        state["board"] = "error"
        page.locator("#course-status-board").get_by_role("button", name="Cập nhật", exact=True).click()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('Chưa tải được')")
        assert page.locator("#course-status-board").get_by_role("button", name="Cập nhật", exact=True).is_enabled()
        page.screenshot(path=str(evidence / "courses-error-390.png"), full_page=True, animations="disabled")
        page.locator("#tab-btn-profile").click()
        page.locator("#portal-logout").click()
        page.wait_for_function("document.getElementById('portal-profile').hidden")
        for theme in ("light", "dark"):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            page.screenshot(path=str(evidence / f"login-{theme}-390.png"), full_page=True, animations="disabled")
            assert contrast(page, "#portal-submit") >= 4.5
            assert contrast(page, "#portal-username", "borderTopColor") >= 3
        page.locator("#portal-username").fill("synthetic-only")
        page.locator("#portal-password").fill("synthetic-password")
        page.locator("#portal-submit").click()
        page.wait_for_function("document.getElementById('portal-submit').disabled")
        assert "Đang kết nối" in page.locator("#portal-status").inner_text()
        assert pending_login
        pending_login.pop().fulfill(status=409, content_type="application/json",
                                    body=json.dumps({"detail": "interaction_required"}))
        page.wait_for_function("!document.getElementById('portal-submit').disabled")
        assert "CAPTCHA" in page.locator("#portal-status").inner_text()
        assert page.locator("#portal-password").input_value() == ""
        page.emulate_media(reduced_motion="reduce")
        assert page.locator("#portal-submit").evaluate("n => getComputedStyle(n).transitionDuration") == "0s"
        assert not errors, errors
        assert not outside, outside
        browser.close()
    (evidence / "verification.json").write_text(json.dumps({
        "viewports": [1440, 1024, 390], "themes": ["light", "dark"],
        "local_font_weights": [400, 500, 600, 700, 800], "checks": reports,
        "personal_data": "invented fixtures only", "outbound_requests": 0,
    }, indent=2), encoding="utf-8")
    print("Presentation: existing structure, 1440/1024/390, both themes, VI/EN, local Vietnamese fonts, "
          "contrast, keyboard/focus, table scrolling, dialog and loading/error states passed")


if __name__ == "__main__":
    main()
