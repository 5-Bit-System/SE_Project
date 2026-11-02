"""Open a loopback RAG-only chat; no product DB/account/recommendation stack."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
from pathlib import Path
import socket
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
PROGRAMS = {
    "data_science": ("MAT3533", "QD3569-2023"),
    "mathematics": ("MAT3300", "QD3565-2023"),
    "mathematics_informatics": ("MAT3539", "QD3567-2023"),
    "computer_science": ("MAT3507", "QD3568-2023"),
}


@contextmanager
def demo_server():
    import uvicorn

    from app.hus.demo import app

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    base = f"http://127.0.0.1:{sock.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", log_level="error"))
    worker = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 20
        while not server.started:
            if not worker.is_alive() or time.monotonic() > deadline:
                raise RuntimeError("RAG demo did not start")
            threading.Event().wait(.05)
        yield base
    finally:
        server.should_exit = True
        worker.join(timeout=10)
        sock.close()


def smoke(page, base, out):
    """Exercise real mixed chat and a late-response scope switch in the dedicated UI."""
    from playwright.sync_api import expect

    records, errors, seen = [], [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: seen.append(request.url))

    def ask(question, generated=False):
        expect(page.locator("#rag-question")).to_be_enabled()
        page.locator("#rag-generated").set_checked(generated)
        page.locator("#rag-question").fill(question)
        with page.expect_response(lambda response: response.url.endswith("/hus/chat")) as event:
            page.locator("#rag-send").click()
        response = event.value
        assert response.status == 200, (question, response.status)
        value = response.json()
        expect(page.locator(".rag-message-assistant .rag-message-text").last).to_have_text(value["reply"])
        expect(page.locator("#rag-question")).to_be_enabled()
        records.append({"major": page.locator("#rag-major").input_value(), "question": question,
                        "mode": value["mode"], "status": "pass"})
        return value

    for major, (course, version) in PROGRAMS.items():
        page.locator("#rag-major").select_option(major)
        expect(page.locator("#rag-version")).to_have_text(version)
        expect(page.locator("#rag-generated")).not_to_be_checked()
        for question in ("Xin chào", "Cảm ơn bạn", "Tạm biệt", "Bạn có thể làm gì?"):
            value = ask(question)
            assert value["mode"] == "basic_chat" and value["hus_answer"] is None
            expect(page.locator(".rag-message-assistant").last.locator(".rag-citations")).to_have_count(0)
        for question in ("Kỳ tới nên học môn gì?", "Xếp thời khóa biểu cho tôi", "Thầy nào dễ tính?"):
            value = ask(question)
            assert value["mode"] == "hus_rag" and value["hus_answer"]["status"] == "no_information"
            assert not value["hus_answer"]["citations"] and not value["hus_answer"]["facts"]
        for question, generated, dataset, status in [
            ("Giới thiệu ngành", False, "f1", "answered"),
            (f"Số tín chỉ {course}?", False, "f2", "answered"),
            (f"Nội dung {course}?", False, "f3", "needs_clarification"),
            (f"Nội dung {course}?", True, "f3", "answered"),
            (f"{course} thi cuối kỳ bao nhiêu phần trăm?", False, None, "no_information"),
        ]:
            value = ask(question, generated)
            answer = value["hus_answer"]
            assert value["mode"] == "hus_rag" and answer["major"] == major and answer["status"] == status
            if status == "answered":
                assert answer["dataset"] == dataset and answer["citations"]
                if dataset == "f3":
                    assert all(c["display_label"] == "kiến thức AI" and c["open_url"] is None for c in answer["citations"])
                    expect(page.locator(".rag-message-assistant").last.locator(".rag-citation-ai")).to_have_count(len(answer["citations"]))
                if dataset == "f2":
                    link = page.locator(".rag-message-assistant").last.locator(".rag-citations a").first
                    expect(link).to_be_visible()
                    target = link.get_attribute("href")
                    citation = answer["citations"][0]
                    assert target.startswith(base + "/hus/sources/" + citation["document_sha256"])
                    binary = page.request.get(target.split("#")[0])
                    assert binary.status == 200 and binary.body().startswith(b"%PDF-")
                    assert hashlib.sha256(binary.body()).hexdigest() == citation["document_sha256"]
            else:
                assert not answer["citations"] and not answer["facts"]

    page.locator("#rag-major").select_option("mathematics")
    value = ask("Tiên quyết MAT3325?")
    locators = value["hus_answer"]["citations"]
    assert [c["pdf_page"] for c in locators] == [13, 12]
    links = page.locator(".rag-message-assistant").last.locator(".rag-citations a")
    expect(links).to_have_count(2)
    assert "page=13" in links.nth(0).get_attribute("href") and "page=12" in links.nth(1).get_attribute("href")

    # Hold a completed real answer, switch scope, then release it; no old reply may land.
    held = []
    page.route("**/hus/chat", lambda route: held.append(route))
    page.locator("#rag-generated").check()
    page.locator("#rag-question").fill("Tín chỉ MAT3300?")
    page.locator("#rag-send").click()
    deadline = time.monotonic() + 10
    while not held and time.monotonic() < deadline:
        page.wait_for_timeout(50)
    assert held
    response = held[0].fetch()
    assert response.status == 200
    page.locator("#rag-major").select_option("data_science")
    expect(page.locator("#rag-generated")).not_to_be_checked()
    expect(page.locator(".rag-message-user")).to_have_count(0)
    expect(page.locator(".rag-message-assistant")).to_have_count(1)
    held[0].fulfill(response=response)
    page.wait_for_timeout(200)
    expect(page.locator(".rag-message-assistant")).to_have_count(1)
    page.unroute("**/hus/chat")
    assert ask("Tín chỉ MAT3533?")["hus_answer"]["facts"]["value"] == 3
    assert not errors, errors
    assert not any(any(part in url for part in ("/advisor", "/recommendations", "/academic", "/eligibility")) for url in seen)
    page.screenshot(path=str(out / "rag-only-chat.png"), full_page=True)
    return {"status": "pass", "scope": "standalone RAG/basic chat only", "cases": records,
            "late_response_scope_isolation": "pass", "same_pdf_distinct_pages": "pass",
            "browser_page_errors": errors, "recommendation_requests": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--major", choices=PROGRAMS, default="data_science")
    parser.add_argument("--smoke", action="store_true", help="Run four-major browser acceptance headlessly, then exit")
    args = parser.parse_args(argv)
    from playwright.sync_api import Error, expect, sync_playwright

    with demo_server() as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=args.smoke, channel="chromium")
        try:
            page = browser.new_page(viewport={"width": 1380, "height": 1000})
            page.goto(base, wait_until="networkidle")
            expect(page.locator("#rag-major")).to_be_enabled(timeout=20000)
            page.locator("#rag-major").select_option(args.major)
            expect(page.locator("#rag-question")).to_be_enabled()
            print(f"RAG demo: {base}", flush=True)
            print("Ask in 'Cau hoi cua ban'. No login or transcript required. Ctrl+C to stop.", flush=True)
            if args.smoke:
                out = ROOT / "backups/hus_rag_demo" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                out.mkdir(parents=True)
                report = smoke(page, base, out)
                report["product_database_modified"] = report["llm_used"] = False
                (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"PASS: {len(report['cases'])} browser chat cases + scope isolation. {out / 'report.json'}", flush=True)
            else:
                page.locator("#rag-question").focus()
                while browser.is_connected() and not page.is_closed():
                    try:
                        page.wait_for_timeout(250)
                    except Error:
                        if page.is_closed() or not browser.is_connected():
                            break
                        raise
        finally:
            if browser.is_connected():
                browser.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("RAG demo stopped.")
