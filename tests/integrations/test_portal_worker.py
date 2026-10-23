import asyncio
import json

import pytest

from app.integrations.daotao import runtime
from app.integrations.daotao.snapshot import PortalFailure


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
