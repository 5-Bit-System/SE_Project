"""One nonqueued Q&A adapter invocation per process, including injected adapters."""

from contextlib import contextmanager
from threading import Lock

from .client import HUSLLMError

_SLOT = Lock()


@contextmanager
def llm_call_slot():
    if not _SLOT.acquire(blocking=False):
        raise HUSLLMError('busy')
    try:
        yield
    finally:
        _SLOT.release()
