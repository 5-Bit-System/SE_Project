"""A rejected update stays visible when returning from the source browser."""

import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


def main():
    state = {"authenticated": True, "job": "running", "review": None}
    errors, updates = [], []
    report = {"connector_version": "vnu-full-table-20261025", "completeness": "unknown",
        "save_status": "retained", "unparsed_rows": 0, "evidence": {
            "source_host_valid": True, "source_path_valid": True, "transcript_container_valid": True,
            "filters_absent": False, "pagination_absent": True, "hidden_records_absent": True,
            "virtualization_absent": True, "loading_absent": True, "network_idle": True,
            "stable_reads": 3, "data_table_count": 1}}
    source = {"subject": "synthetic-only", "profile": {"program": "Khoa học dữ liệu", "cohort": "67"},
        "snapshot": {"completeness": "unknown", "connector_version": "b790d6af+identity1",
            "attempts": [], "unknown_rows": [], "source_summary": []}}

    def intercept(route):
        parsed = urlparse(route.request.url)
        path = parsed.path
        if path == "/me/profile":
            value = {**source, "latest_collection": state["review"]} if state["authenticated"] else {"detail": "session_expired"}
            route.fulfill(status=200 if state["authenticated"] else 401,
                          content_type="application/json", body=json.dumps(value))
        elif path == "/me/portal-sync":
            updates.append(route.request.post_data_json)
            route.fulfill(content_type="application/json", body='{"id":"synthetic-job"}')
        elif path == "/me/portal-sync/synthetic-job":
            value = {"state": state["job"]}
            if state["job"] == "failed":
                state["review"] = report
                value["error"] = "incomplete_snapshot"
            route.fulfill(content_type="application/json", body=json.dumps(value))
        elif path == "/me/course-status":
            value = {"status": "needs_source_review", "blocking_reasons": ["source_incomplete"],
                "courses": None, "collection_status": {"completeness": "unknown"},
                "latest_collection": state["review"]}
            route.fulfill(content_type="application/json", body=json.dumps(value))
        elif path == "/auth/logout":
            state["authenticated"] = False
            route.fulfill(content_type="application/json", body='{}')
        elif path.startswith(("/auth/", "/me/")):
            route.fulfill(status=401, content_type="application/json", body='{"detail":"session_expired"}')
        elif parsed.hostname == "127.0.0.1" and (path == "/" or path.startswith("/static/")):
            route.continue_()
        else:
            route.abort()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/?course-mode=personal#rules")
        root = page.locator("#course-status-board")
        root.get_by_role("button", name="Cập nhật bảng điểm VNU", exact=True).click()
        page.locator("#portal-password").fill("invented-password")
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        page.wait_for_timeout(120)
        assert page.locator("#portal-login").is_visible()
        assert page.locator("#portal-password").input_value() == "invented-password"
        assert page.locator("#portal-submit").inner_text() == "Cập nhật hồ sơ và bảng điểm"
        page.locator("#portal-submit").click()
        page.wait_for_function("document.querySelector('#portal-status').textContent.includes('Đang kết nối')")
        # The source Chrome window returns focus and causes a passive profile load.
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        page.wait_for_timeout(120)
        assert "Đang kết nối" in page.locator("#portal-status").inner_text()
        state["job"] = "failed"
        page.wait_for_function("document.querySelector('#portal-status').textContent.includes('Giữ nguyên')")
        assert "điều khiển lọc" in page.locator("#portal-collection-review").inner_text()
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        page.wait_for_timeout(120)
        assert "Giữ nguyên" in page.locator("#portal-status").inner_text()
        assert page.locator("#portal-password").input_value() == ""
        page.locator("#tab-btn-rules").click()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('điều khiển lọc')")
        assert root.locator(".course-status-empty").count() == 3
        assert "lần lấy bảng điểm chưa được xác minh đầy đủ" in root.inner_text()
        page.locator('[data-language-choice="en"]').click()
        assert "Detected filter controls" in root.inner_text()
        page.locator("#tab-btn-profile").click()
        assert "previous transcript" in page.locator("#portal-collection-review").inner_text()
        assert "retained" in page.locator("#portal-status").inner_text()
        evidence = Path("backups/personal_academic_20261025/sync-feedback")
        evidence.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(evidence / "rejected-update.png"), full_page=True)
        page.reload()
        page.wait_for_function("document.querySelector('#portal-status').textContent.includes('retained')")
        assert "Detected filter controls" in page.locator("#portal-collection-review").inner_text()
        page.locator("#portal-logout").click()
        assert page.locator("#portal-collection-review").is_hidden()
        assert page.locator("#portal-collection-review").inner_text() == ""
        assert len(updates) == 1
        assert not errors, errors
        browser.close()
    print("Portal sync: progress/error survive source return, precise proof, reload, VI/EN and logout passed")


if __name__ == "__main__":
    main()
