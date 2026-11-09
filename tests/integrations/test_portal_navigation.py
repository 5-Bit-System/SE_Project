"""A portal iframe can navigate without being detached; never keep partial reads."""

import sys
from types import SimpleNamespace

import pytest

from app.integrations.daotao.client import DaotaoClient


@pytest.fixture
def browser_errors(monkeypatch):
    class BrowserError(Exception):
        pass

    class BrowserTimeout(BrowserError):
        pass

    monkeypatch.setitem(sys.modules, 'playwright.sync_api', SimpleNamespace(
        Error=BrowserError, TimeoutError=BrowserTimeout))
    monkeypatch.setattr('app.integrations.daotao.client.sleep', lambda _: None)
    return BrowserError, BrowserTimeout


@pytest.mark.parametrize('message', [
    'Execution context was destroyed, most likely because of a navigation',
    'Frame was detached',
    'Cannot find context with specified id',
])
def test_profile_restarts_whole_read_when_frame_navigates(browser_errors, message):
    error, _ = browser_errors
    calls = []

    class Frame:
        def __init__(self, index):
            self.index = index

        def is_detached(self):
            return False

        def locator(self, selector):
            assert selector == 'body'
            return self

        def evaluate(self, script, labels, **kwargs):
            calls.append(self.index)
            if calls == [0, 1]:
                raise error(message)
            return ['Họ và tên\tOld document' if calls == [0]
                    else 'Họ và tên\tCurrent document']

    page = SimpleNamespace(frames=[Frame(0), Frame(1)], is_closed=lambda: False)
    client = object.__new__(DaotaoClient)
    client.context = SimpleNamespace(pages=[page])
    texts = client._profile_cell_texts()
    assert calls == [0, 1, 0, 1]
    assert texts == ['Họ và tên\tCurrent document'] * 2
    assert 'Họ và tên\tOld document' not in texts


def test_profile_does_not_hide_other_browser_errors(browser_errors):
    error, _ = browser_errors

    def fail(*args, **kwargs):
        raise error('net::ERR_CONNECTION_REFUSED')

    frame = SimpleNamespace(locator=lambda _: SimpleNamespace(evaluate=fail),
                            is_detached=lambda: False)
    client = object.__new__(DaotaoClient)
    client.context = SimpleNamespace(pages=[SimpleNamespace(
        frames=[frame], is_closed=lambda: False)])
    with pytest.raises(error, match='ERR_CONNECTION_REFUSED'):
        client._profile_cell_texts()


def test_continuous_navigation_has_a_bounded_timeout(browser_errors, monkeypatch):
    error, timeout = browser_errors
    ticks = iter([0, 0, 1])
    monkeypatch.setattr('app.integrations.daotao.client.monotonic', lambda: next(ticks))

    def fail(*args, **kwargs):
        raise error('Execution context was destroyed: private-provider-content')

    client = object.__new__(DaotaoClient)
    client.context = SimpleNamespace(pages=[SimpleNamespace(frames=[SimpleNamespace(
        locator=lambda _: SimpleNamespace(evaluate=fail))])])
    with pytest.raises(timeout, match='did not finish navigating') as captured:
        client._profile_cell_texts(timeout_ms=500)
    assert 'private-provider-content' not in str(captured.value)
