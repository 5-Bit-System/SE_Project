from concurrent.futures import ThreadPoolExecutor
from time import perf_counter

from app.importing.batch import BatchStatus, import_csv


def test_200_concurrent_synthetic_import_tasks_report_p95(capsys):
    payload = "id,value\n" + "".join(f"{row},synthetic\n" for row in range(100))

    def run_task(_task_id):
        start = perf_counter()
        result = import_csv(payload, lambda _row: None)
        return perf_counter() - start, result

    with ThreadPoolExecutor(max_workers=200) as pool:
        measurements = list(pool.map(run_task, range(200)))

    durations = sorted(duration for duration, _ in measurements)
    p95 = durations[188] * 1000
    assert all(result.status is BatchStatus.COMPLETED for _, result in measurements)
    assert all(result.imported_count == 100 for _, result in measurements)
    print(f"synthetic_tasks=200 rows_per_task=100 p95_ms={p95:.3f} target_ms=5000")
    # This asserts task completion only. The recorded p95 is compared with the
    # assignment target in the report and does not model production/API latency.
    assert p95 < 5000
