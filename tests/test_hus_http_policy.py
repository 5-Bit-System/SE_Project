"""HTTP pacing and identification tests with a deterministic clock and mocked network."""

import io

from docx import Document
import httpx
import pytest

from app.hus.allowlist import Allowlist
from app.hus.pipeline import HUSPipeline
from app.hus.state import CrawlStateManager
from app.hus.storage import ProcessedStorage, RawStorage

HOST = "mim.hus.vnu.edu.vn"
BASE = f"https://{HOST}"
AGENT = "SEProjectCrawler/7.0"


class Clock:
    def __init__(self):
        self.value = 0.0
        self.sleeps = []

    def now(self):
        return self.value

    def sleep(self, seconds):
        assert seconds >= 0
        self.sleeps.append(seconds)
        self.value += seconds


def pipeline(root, *, delay=2.0, extra_sources=()):
    rules = Allowlist(
        [{"host": HOST, "path_prefixes": ["/vi/", "/files/"],
          "seeds": [BASE + "/vi/seed"]}, *extra_sources],
        delay_seconds=delay, retry_attempts=3, user_agent=AGENT,
    )
    return HUSPipeline(rules, RawStorage(root), ProcessedStorage(root),
                       CrawlStateManager(root / "state/crawl_state.json"))


def word_bytes():
    document = Document()
    document.add_paragraph("Official attachment content.")
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


@pytest.mark.parametrize("delay", [2.0, 0.5, 0.0])
def test_pages_robots_and_attachments_share_request_spacing(tmp_path, monkeypatch, delay):
    clock = Clock()
    monkeypatch.setattr("app.hus.crawler.time.monotonic", clock.now)
    events = []
    payload = word_bytes()

    def handler(request):
        events.append((request.url.path, clock.now(), request.headers["user-agent"]))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path == "/vi/seed":
            return httpx.Response(200, text='<main><h1>Seed</h1><p>Details.</p>'
                                  '<a href="/files/a.docx">A</a>'
                                  '<a href="/files/b.docx">B</a></main>',
                                  headers={"content-type": "text/html"})
        return httpx.Response(200, content=payload)

    # A caller-provided client must retain its settings after the run.
    with httpx.Client(transport=httpx.MockTransport(handler),
                      headers={"User-Agent": "CallerAgent/1"}) as client:
        result = pipeline(tmp_path).run(client=client, sleep=clock.sleep, delay_seconds=delay)
        assert client.headers["User-Agent"] == "CallerAgent/1"

    assert result.attachment_count == 2
    assert result.error_count == 0
    assert [path for path, _, _ in events] == [
        "/robots.txt", "/vi/seed", "/files/a.docx", "/files/b.docx",
    ]
    assert [at for _, at, _ in events] == pytest.approx([0, delay, 2 * delay, 3 * delay])
    assert all(agent == AGENT for _, _, agent in events)
    assert clock.now() == pytest.approx(3 * delay)  # No extra sleep after the final request.


@pytest.mark.parametrize("request_duration,expected_wait", [(0.75, 1.25), (3.0, 0.0)])
def test_request_duration_counts_towards_minimum_gap(
    tmp_path, monkeypatch, request_duration, expected_wait,
):
    clock = Clock()
    monkeypatch.setattr("app.hus.crawler.time.monotonic", clock.now)
    events = []

    def handler(request):
        events.append(clock.now())
        clock.value += request_duration
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, text="<main><h1>Seed</h1><p>Details.</p></main>",
                              headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = pipeline(tmp_path).run(client=client, sleep=clock.sleep)
    assert result.new_count == 1
    assert events == pytest.approx([0, max(2.0, request_duration)])
    assert sum(clock.sleeps) == pytest.approx(expected_wait)


@pytest.mark.parametrize("failure", ["503", "connect_error"])
def test_retry_fallback_and_redirects_are_paced(tmp_path, monkeypatch, failure):
    clock = Clock()
    monkeypatch.setattr("app.hus.crawler.time.monotonic", clock.now)
    events = []
    attempts = 0

    def handler(request):
        nonlocal attempts
        events.append((str(request.url), clock.now(), request.headers["user-agent"]))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path == "/vi/seed":
            attempts += 1
            if attempts == 1:
                if failure == "503":
                    return httpx.Response(503)
                raise httpx.ConnectError("simulated HTTPS failure", request=request)
            return httpx.Response(302, headers={"location": "/vi/final"})
        return httpx.Response(200, text="<main><h1>Final</h1><p>Details.</p></main>",
                              headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = pipeline(tmp_path).run(client=client, sleep=clock.sleep)
    assert result.new_count == 1
    assert result.error_count == 0
    assert [at for _, at, _ in events] == pytest.approx([0, 2, 4, 6])
    assert all(agent == AGENT for _, _, agent in events)
    if failure == "connect_error":
        assert events[2][0].startswith("http://")


def test_robots_http_fallback_and_different_hosts_use_shared_policy(tmp_path, monkeypatch):
    clock = Clock()
    monkeypatch.setattr("app.hus.crawler.time.monotonic", clock.now)
    second_host = "hus.vnu.edu.vn"
    events = []

    def handler(request):
        events.append((str(request.url), clock.now(), request.headers["user-agent"]))
        if request.url.path == "/robots.txt":
            if request.url.host == HOST and request.url.scheme == "https":
                raise httpx.ConnectTimeout("simulated HTTPS robots timeout", request=request)
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.host == HOST:
            return httpx.Response(302, headers={"location": f"https://{second_host}/vi/final"})
        return httpx.Response(200, text="<main><h1>Final</h1><p>Details.</p></main>",
                              headers={"content-type": "text/html"})

    current = pipeline(tmp_path, extra_sources=[
        {"host": second_host, "path_prefixes": ["/vi/"], "seeds": []},
    ])
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = current.run(client=client, sleep=clock.sleep)
    assert result.new_count == 1
    assert result.error_count == 0
    assert [at for _, at, _ in events] == pytest.approx([0, 2, 4, 4, 6])
    assert all(agent == AGENT for _, _, agent in events)


def test_default_client_sends_configured_user_agent(tmp_path, monkeypatch):
    events = []

    def handler(request):
        events.append(request.headers["user-agent"])
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: SEProjectCrawler\nAllow: /\n"
                                  "User-agent: *\nDisallow: /\n")
        return httpx.Response(200, text="<main><h1>Seed</h1><p>Details.</p></main>",
                              headers={"content-type": "text/html"})

    original_init = httpx.Client.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", patched_init)
    result = pipeline(tmp_path, delay=0).run()
    assert result.new_count == 1
    assert events == [AGENT, AGENT]


def test_longer_retry_backoff_is_not_followed_by_another_full_delay(tmp_path, monkeypatch):
    clock = Clock()
    monkeypatch.setattr("app.hus.crawler.time.monotonic", clock.now)
    events = []
    attempts = 0

    def handler(request):
        nonlocal attempts
        events.append(clock.now())
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        attempts += 1
        if attempts < 3:
            return httpx.Response(503)
        return httpx.Response(200, text="<main><h1>Seed</h1><p>Details.</p></main>",
                              headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = pipeline(tmp_path).run(client=client, sleep=clock.sleep)
    assert result.new_count == 1
    assert result.error_count == 0
    assert events == pytest.approx([0, 2, 4, 8])
    assert sum(clock.sleeps) == pytest.approx(8)


def test_legacy_crawler_uses_the_same_pacing_and_user_agent(monkeypatch):
    from app.hus.crawler import crawl

    clock = Clock()
    monkeypatch.setattr("app.hus.crawler.time.monotonic", clock.now)
    events = []
    rules = Allowlist([{"host": HOST, "path_prefixes": ["/vi/"],
                        "seeds": [BASE + "/vi/seed"]}],
                      delay_seconds=2, user_agent=AGENT)

    def handler(request):
        events.append((clock.now(), request.headers["user-agent"]))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, text="<main><h1>Seed</h1><p>Details.</p></main>",
                              headers={"content-type": "text/html"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        documents, failures = crawl(rules, client, sleep=clock.sleep)
    assert len(documents) == 1
    assert not failures
    assert events == [(0, AGENT), (2, AGENT)]
    assert clock.now() == 2
