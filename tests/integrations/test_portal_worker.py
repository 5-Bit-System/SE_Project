import asyncio
import json
import sys
from types import SimpleNamespace

import pytest

from app.integrations.daotao import runtime, worker
from app.integrations.daotao.snapshot import PortalFailure


@pytest.mark.parametrize('failure,accepted', [
    ('timeout', True), ('structure_changed', True), ('identity_unverified', False),
    ('interaction_required', False), ('login', False),
])
def test_signin_requires_fresh_auth_but_source_failure_can_be_retried(monkeypatch, failure, accepted):
    class BrowserError(Exception):
        pass

    class BrowserTimeout(BrowserError):
        pass

    class Client:
        def __init__(self, context):
            pass

        def login(self, username, password):
            if failure == 'login':
                raise PortalFailure('identity_unverified')
            return 'synthetic'

        def read_profile_texts(self):
            if failure == 'timeout':
                raise BrowserTimeout('private-source-details')
            if failure == 'identity_unverified':
                return ['MSSV: another-student']
            raise PortalFailure(failure)

    class Browser:
        def new_context(self, **kwargs):
            return SimpleNamespace(route=lambda *args: None, set_default_timeout=lambda *args: None,
                                   cookies=lambda: [])

        def close(self):
            pass

    class Playwright:
        def __enter__(self):
            return SimpleNamespace(chromium=self)

        def launch(self, **kwargs):
            return Browser()

        def __exit__(self, *args):
            pass

    monkeypatch.setitem(sys.modules, 'playwright.sync_api', SimpleNamespace(
        Error=BrowserError, TimeoutError=BrowserTimeout, sync_playwright=Playwright))
    monkeypatch.setattr(worker, 'DaotaoClient', Client)
    result = worker.collect({'mode': 'signin', 'username': 'synthetic', 'password': 'never-log'})
    if accepted:
        assert result == {'authenticated': True, 'subject': 'synthetic', 'snapshot': None,
                          'profile': None, 'cookies': [], 'warning': 'source_unavailable'}
    else:
        assert result['error'] in {'identity_unverified', 'interaction_required'}
        assert not result.get('authenticated')
    assert 'private-source-details' not in str(result) and 'never-log' not in str(result)


def test_worker_receives_credentials_only_via_stdin(monkeypatch):
    class Process:
        returncode = 0

        async def communicate(self, body):
            assert b'private-password' in body
            return b'{"error":"identity_unverified"}', b''

    async def spawn(*args, **kwargs):
        assert "private-password" not in str(args)
        assert kwargs["stderr"] == asyncio.subprocess.DEVNULL
        return Process()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    with pytest.raises(PortalFailure, match="identity_unverified"):
        asyncio.run(runtime.collect({"username": "synthetic", "password": "private-password"}))


def test_real_child_utf8_roundtrip_even_with_cp1252_stdio(monkeypatch):
    spawn_process = asyncio.create_subprocess_exec
    expected = {"subject": "synthetic", "snapshot": {
        "name": "Đại số tuyến tính", "term": "HỌC KỲ 1", "grade10": "8,5"}}
    script = (
        "import json,sys; from app.integrations.daotao.worker import write_result; "
        "credentials=json.load(sys.stdin); "
        "assert credentials['password']=='m\\u1eadt-kh\\u1ea9u-th\\u1eed'; "
        "assert sys.stdout.encoding.lower()=='cp1252'; "
        "write_result(" + repr(expected).encode("ascii", "backslashreplace").decode() + ")"
    )

    async def spawn(*args, **kwargs):
        # Force the exact Windows pipe locale that crashed before the binary writer fix.
        kwargs["env"]["PYTHONIOENCODING"] = "cp1252"
        return await spawn_process(args[0], "-c", script, **kwargs)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    result = asyncio.run(runtime.collect({"username": "synthetic", "password": "mật-khẩu-thử"}))
    assert result == expected


@pytest.mark.parametrize("output,exit_code,code", [
    (b"", 1, "worker_failed"), (b"", 0, "worker_output_invalid"),
    (b"not-json", 0, "worker_output_invalid"), (b"[]", 0, "worker_output_invalid"),
    (json.dumps({"snapshot": {}}).encode(), 0, "worker_output_invalid"),
])
def test_invalid_worker_output_is_safe_and_diagnosable(monkeypatch, caplog,
                                                      output, exit_code, code):
    class Process:
        returncode = exit_code

        async def communicate(self, body):
            return output, b''

    async def spawn(*args, **kwargs):
        return Process()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    with pytest.raises(PortalFailure, match=code):
        asyncio.run(runtime.collect({"username": "synthetic", "password": "never-log-this"}))
    assert "stage=" in caplog.text
    assert "never-log-this" not in caplog.text


@pytest.mark.parametrize("cancelled", [False, True])
def test_timeout_and_cancellation_terminate_process_tree(monkeypatch, cancelled):
    commands = []

    class Process:
        returncode = None
        pid = 123456

        async def communicate(self, body):
            if cancelled:
                raise asyncio.CancelledError
            raise TimeoutError

        async def wait(self):
            self.returncode = 1

        def kill(self):
            self.returncode = 1

    process = Process()

    async def spawn(*args, **kwargs):
        commands.append(args)
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    with pytest.raises(asyncio.CancelledError if cancelled else PortalFailure):
        asyncio.run(runtime.collect({"username": "synthetic", "password": "x"}))
    assert process.returncode == 1
    if runtime.os.name == "nt":
        assert commands[-1] == ("taskkill", "/PID", "123456", "/T", "/F")


@pytest.mark.parametrize("stage,expected_code,network_error", [
    ("browser_start", "browser_unavailable", False), ("login", "portal_unavailable", False),
    ("profile", "portal_unavailable", False), ("transcript", "portal_unavailable", False),
    ("login", "network_access_denied", True), ("profile", "network_access_denied", True),
    ("browser_start", "browser_unavailable", True),
])
def test_worker_diagnoses_failed_stage_without_provider_details(monkeypatch, stage, expected_code,
                                                              network_error):
    class BrowserError(Exception):
        pass

    class BrowserTimeout(BrowserError):
        pass

    private = "synthetic-private-password-cookie-and-grade"

    def fail():
        raise BrowserError(("Page.goto: net::ERR_NETWORK_ACCESS_DENIED " if network_error else "")
                           + private)

    class Client:
        def __init__(self, context):
            pass

        def login(self, *args):
            if stage == "login":
                fail()
            return "synthetic"

        def read_profile_texts(self):
            if stage == "profile":
                fail()
            return []

        def open_transcript(self):
            fail()

    class Browser:
        closed = False

        def new_context(self, **kwargs):
            return SimpleNamespace(route=lambda *args: None, set_default_timeout=lambda *args: None)

        def close(self):
            self.closed = True

    browser = Browser()

    class Playwright:
        def __enter__(self):
            return SimpleNamespace(chromium=self)

        def launch(self, **kwargs):
            assert kwargs == {"headless": True, "channel": "chrome"}
            if stage == "browser_start":
                fail()
            return browser

        def __exit__(self, *args):
            pass

    # Portal is optional; the ordinary offline/CI suite must not need Playwright.
    monkeypatch.setitem(sys.modules, "playwright.sync_api", SimpleNamespace(
        Error=BrowserError, TimeoutError=BrowserTimeout, sync_playwright=Playwright))
    monkeypatch.setattr(worker, "DaotaoClient", Client)
    result = worker.collect({"username": "synthetic", "password": private})
    assert result == {"error": expected_code, "stage": stage, "kind": "browser_error"}
    assert private not in json.dumps(result)
    assert browser.closed == (stage != "browser_start")


@pytest.mark.parametrize("hostile", [False, True])
@pytest.mark.parametrize("code", ["portal_unavailable", "network_access_denied"])
def test_runtime_logs_only_allowlisted_worker_diagnostics(monkeypatch, caplog, hostile, code):
    private = "synthetic-private-provider-response"
    result = {"error": code, "stage": "profile", "kind": "browser_error",
              "raw": private}
    if hostile:
        result.update(error=private, stage=[private], kind={"secret": private})

    class Process:
        returncode = 0

        async def communicate(self, body):
            return json.dumps(result).encode(), b''

    async def spawn(*args, **kwargs):
        return Process()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    expected = "portal_unavailable" if hostile else code
    with pytest.raises(PortalFailure, match=f"^{expected}$"):
        asyncio.run(runtime.collect({"username": "synthetic", "password": private}))
    assert f"stage={'unknown' if hostile else 'profile'}" in caplog.text
    assert private not in caplog.text
