import asyncio

from tests.support.vt102_harness import workload


def test_tc19_40_distinct_jobs_queue_behind_two_collectors_without_duplicate_retry(monkeypatch):
    report = asyncio.run(workload(monkeypatch))
    assert report["logical_jobs"] == report["collector_calls"] == report["save_calls"] == 40
    assert report["maximum_collector_concurrency"] == 2
    assert report["error_rate"] == 0
