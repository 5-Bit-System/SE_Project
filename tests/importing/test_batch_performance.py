"""Synthetic overlap includes barrier waiting; this does not measure HTTP users."""

from concurrent.futures import ThreadPoolExecutor
from math import ceil
from threading import Barrier, Lock
from time import perf_counter

import pytest

from app.importing.batch import BatchStatus, import_csv


def nearest_rank_ms(seconds: list[float], percentile: float = 0.95) -> float:
    return sorted(seconds)[ceil(percentile * len(seconds)) - 1] * 1000


def test_nearest_rank_p95_uses_190th_of_200_samples():
    assert nearest_rank_ms([number / 1000 for number in range(1, 201)]) == pytest.approx(190)


def test_200_concurrent_synthetic_import_tasks_report_p95():
    workers = 200
    payload = "id,value\n" + "".join(f"{row},synthetic\n" for row in range(100))
    gate = Barrier(workers + 1, timeout=20)
    lock = Lock()
    active = peak_inflight = 0

    def run_task(submitted):
        nonlocal active, peak_inflight
        with lock:
            active += 1
            peak_inflight = max(peak_inflight, active)
        try:
            gate.wait()
            started = perf_counter()
            result = import_csv(payload, lambda _row: None)
            finished = perf_counter()
            return finished - submitted, finished - started, result
        finally:
            with lock:
                active -= 1

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_task, perf_counter()) for _ in range(workers)]
        gate.wait()
        measurements = [future.result() for future in futures]

    e2e_p95 = nearest_rank_ms([e2e for e2e, _, _ in measurements])
    service_p95 = nearest_rank_ms([service for _, service, _ in measurements])
    assert peak_inflight == 200
    assert active == 0
    assert all(result.status is BatchStatus.COMPLETED for _, _, result in measurements)
    assert all(result.imported_count == 100 for _, _, result in measurements)
    print(
        f"synthetic_tasks=200 rows_per_task=100 peak_inflight={peak_inflight} "
        f"e2e_p95_ms={e2e_p95:.3f} service_p95_ms={service_p95:.3f} target_ms=5000"
    )
    # E2E includes submit/queue/startup/barrier; peak includes barrier waiters.
    # The GIL does not promise 200 simultaneous parser executions.
    assert e2e_p95 < 5000
