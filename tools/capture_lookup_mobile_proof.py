"""Capture high-resolution screenshot proof of HUS Lookup tab on mobile viewport."""

from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect, sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.presentation_fixture import common_route


def _launch_browser(p):
    try:
        return p.chromium.launch(headless=True)
    except PlaywrightError:
        return p.chromium.launch(channel="chrome", headless=True)


def main():
    sample = {
        "subject": "synthetic-mobile",
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
            route.fulfill(json={"account_id": "synthetic-mobile", "major": "data_science", "messages": []})
        elif path == "/hus/chat":
            route.fulfill(
                json={
                    "mode": "hus_rag",
                    "reply": (
                        "### Thông tin học phần\n"
                        "- **Mã học phần:** MAT2400 [1]\n"
                        "- **Tên học phần:** Giải tích 1\n"
                        "- **Số tín chỉ:** 3\n"
                        "- **Điều kiện tiên quyết:** Không\n\n"
                        "Môn học trang bị các kiến thức cơ bản về phép tính vi tích phân hàm một biến số, "
                        "làm nền tảng cho các học phần tiếp theo."
                    ),
                    "generation_mode": "grounded_llm",
                    "hus_answer": {
                        "status": "answered",
                        "citations": [
                            {
                                "citation_id": 1,
                                "label": "QĐ 3569",
                                "evidence_kind": "pdf",
                                "availability": "available",
                                "open_url": "/hus/sources/sample.pdf#page=10",
                                "document_sha256": "sample_sha256",
                                "pdf_page": 10,
                            }
                        ],
                    },
                }
            )
        else:
            assert common_route(route), url

    with sync_playwright() as p:
        browser = _launch_browser(p)
        page = browser.new_page(viewport={"width": 375, "height": 667})
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/#lookup", wait_until="networkidle")

        expect(page.locator("#lookup-question")).to_be_visible()
        page.locator("#lookup-question").fill("thông tin môn giải tích 1")
        with page.expect_response(lambda r: "/hus/chat" in r.url):
            page.locator("#lookup-send").click()

        expect(page.locator(".rag-course-card")).to_be_visible()
        page.wait_for_timeout(500)

        out_path = Path("screenshots/hus_lookup_mobile_verified.png")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out_path))
        print(f"Screenshot saved to {out_path.resolve()}")

        browser.close()


if __name__ == "__main__":
    main()
