"""The startup check must catch local network restrictions without authenticating."""

import sys
from types import SimpleNamespace

import pytest

from tools import run_local


@pytest.mark.parametrize("failure,expected", [
    ("blocked", "network_access_denied"), ("timeout", "timeout"),
    ("http", "portal_unavailable"), ("layout", "structure_changed"), (None, None),
])
def test_public_form_probe_never_submits_credentials(monkeypatch, failure, expected):
    class BrowserError(Exception):
        pass

    class BrowserTimeout(BrowserError):
        pass

    closed = []

    class Page:
        def goto(self, url, **kwargs):
            assert url == run_local.LOGIN_URL
            if failure == "blocked":
                raise BrowserError("net::ERR_NETWORK_ACCESS_DENIED private-provider-text")
            if failure == "timeout":
                raise BrowserTimeout("private-provider-text")
            return SimpleNamespace(status=503 if failure == "http" else 200)

        def locator(self, selector):
            assert selector in {"#frmLogin", "#txtLoginId", "#txtPassword"}
            return SimpleNamespace(count=lambda: 0 if failure == "layout" else 1)

    class Browser:
        def new_context(self, **kwargs):
            return SimpleNamespace(route=lambda *args: None, set_default_timeout=lambda *args: None,
                                   new_page=lambda: Page())

        def close(self):
            closed.append(True)

    class Playwright:
        def __enter__(self):
            return SimpleNamespace(chromium=SimpleNamespace(launch=lambda **kwargs: Browser()))

        def __exit__(self, *args):
            pass

    monkeypatch.setitem(sys.modules, "playwright.sync_api", SimpleNamespace(
        Error=BrowserError, TimeoutError=BrowserTimeout, sync_playwright=Playwright))
    assert run_local.check_portal() == expected
    assert closed == [True]


def test_failed_preflight_does_not_start_server(monkeypatch, capsys):
    monkeypatch.setattr(run_local, "check_portal", lambda: "network_access_denied")
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(
        run=lambda *args, **kwargs: pytest.fail("Do not serve from a restricted session")))
    assert run_local.main([]) == 1
    assert "restricted session" in capsys.readouterr().err


def test_check_only_does_not_start_server(monkeypatch):
    monkeypatch.setattr(run_local, "check_portal", lambda: None)
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(
        run=lambda *args, **kwargs: pytest.fail("The probe must not start another server")))
    assert run_local.main(["--check-only"]) == 0
