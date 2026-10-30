"""Check the public VNU form before starting the local app; never submit credentials."""

import argparse
import sys

from app.integrations.daotao.client import LOGIN_URL, DaotaoClient
from app.integrations.daotao.worker import browser_error_code, portal_context


def check_portal() -> str | None:
    stage = "browser_start"
    try:
        from playwright.sync_api import Error, TimeoutError, sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, channel="chrome")
            try:
                stage = "browser_context"
                context = portal_context(browser)
                client = DaotaoClient(context)
                stage = "login"
                response = client.page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=15000)
                if response is None or response.status != 200:
                    return "portal_unavailable"
                for selector in ("#frmLogin", "#txtLoginId", "#txtPassword"):
                    if client.page.locator(selector).count() != 1:
                        return "structure_changed"
            finally:
                browser.close()
    except ImportError:
        return "browser_unavailable"
    except TimeoutError:
        return "timeout"
    except Error as exc:
        return browser_error_code(stage, exc)
    except Exception:
        return "portal_unavailable"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Check VNU without starting HTTP")
    args = parser.parse_args(argv)
    code = check_portal()
    if code:
        print(f"VNU connection check failed: {code}.", file=sys.stderr)
        if code == "network_access_denied":
            print("Start from a terminal with network access. For an agent, request an approved "
                  "execution outside its restricted session; child workers inherit restrictions.",
                  file=sys.stderr)
        elif code == "browser_unavailable":
            print("Install requirements-portal.txt in the project venv and install Google Chrome.",
                  file=sys.stderr)
        else:
            print("Check VNU connectivity and the public login form before retrying.", file=sys.stderr)
        return 1
    print("VNU public login form reachable (no credentials submitted).", flush=True)
    if not args.check_only:
        import uvicorn

        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
