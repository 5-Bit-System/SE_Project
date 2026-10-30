"""Reproducible VT-098 mutation, coverage, flakiness and synthetic-load evidence.

Run from repository root. No production endpoint or external service is called.
"""

import argparse
import hashlib
import io
import json
import math
import os
import platform
import random
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pydantic

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / 'evidence'
FOCUSED = 'experiments.vt098.test_harness.HarnessTests.test_valid_key_boundaries'
DISCOVER = ['-m', 'unittest', 'discover', '-s', 'experiments/vt098', '-p', 'test_*.py', '-v']


def git_head(root):
    return subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}',
                           'rev-parse', 'HEAD'], cwd=root, capture_output=True,
                          text=True, check=True).stdout.strip()


def metadata():
    return {'head_before_capture': git_head(ROOT), 'python': platform.python_version(),
            'sqlite': sqlite3.sqlite_version, 'pydantic': pydantic.__version__,
            'platform': platform.platform(), 'cpu_count': os.cpu_count(),
            'scope': 'SQLite harness; not production HTTP/auth/PostgreSQL',
            'sha256': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                       for name in ('harness.py', 'schema.py', 'test_harness.py', 'quality.py')}}


def capture(arguments, root=ROOT, env=None):
    command = [sys.executable, '-X', 'utf8', *arguments]
    result = subprocess.run(command, cwd=root, env=env, capture_output=True,
                            text=True, encoding='utf-8', timeout=180)
    return {'command': command, 'cwd': str(root), 'exit_code': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def write_evidence(name, data):
    EVIDENCE.mkdir(exist_ok=True)
    data = {**metadata(), **data}
    (EVIDENCE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                                encoding='utf-8')
    print(f'Evidence: experiments/vt098/evidence/{name}')


def mutation(mutant_root):
    control = capture(['-m', 'unittest', FOCUSED, '-v'])
    mutant = capture(['-m', 'unittest', FOCUSED, '-v'], root=mutant_root)
    correct = (HERE / 'harness.py').read_text(encoding='utf-8')
    mutated = (mutant_root / 'experiments/vt098/harness.py').read_text(encoding='utf-8')
    same_tests = (HERE / 'test_harness.py').read_bytes() == (
        mutant_root / 'experiments/vt098/test_harness.py').read_bytes()
    one_change = mutated == correct.replace('len(key) > 64', 'len(key) >= 64', 1)
    killed = (control['exit_code'] == 0 and mutant['exit_code'] != 0
              and 'length=64' in mutant['stderr'] and 'invalid_idempotency_key' in mutant['stderr']
              and same_tests and one_change)
    write_evidence('mutation.json', {'control': control, 'mutant': mutant,
                   'mutant_commit': git_head(mutant_root), 'same_test_bytes': same_tests,
                   'exactly_one_operator_change': one_change, 'killed': killed})
    print('Control:', control['exit_code'], 'mutant:', mutant['exit_code'], 'killed:', killed)
    return 0 if killed else 1


def coverage_run():
    import coverage
    with tempfile.TemporaryDirectory(prefix='vt098-coverage-') as directory:
        env = {**os.environ, 'COVERAGE_FILE': str(Path(directory) / 'coverage-data')}
        run = capture(['-m', 'coverage', 'run', '--branch',
                       '--source=experiments.vt098.harness,experiments.vt098.schema',
                       *DISCOVER], env=env)
        target = EVIDENCE / 'coverage-full.json'
        report = capture(['-m', 'coverage', 'json', '-o', str(target)], env=env)
        if report['exit_code']:
            raise RuntimeError(report)
        raw = json.loads(target.read_text(encoding='utf-8'))
        scoped = {}
        for path, data in raw['files'].items():
            if Path(path).name not in ('harness.py', 'schema.py'):
                continue
            summary = data['summary']
            scoped[path] = {**summary, 'missing_lines': data['missing_lines'],
                            'missing_branches': data['missing_branches'],
                            'line_percent': round(100 * summary['covered_lines'] /
                                                  summary['num_statements'], 4),
                            'branch_percent': round(100 * summary['covered_branches'] /
                                                    summary['num_branches'], 4)}
    write_evidence('coverage.json', {'coverage_version': coverage.__version__, 'run': run,
                   'report': report, 'scoped_files': scoped,
                   'raw_report': 'coverage-full.json',
                   'scope_note': 'Dynamic AST class also traces academic.py; that partial file '
                                 'is not production route coverage. No whole-project percentage.'})
    for path, summary in scoped.items():
        print(path, 'line', summary['line_percent'], 'branch', summary['branch_percent'],
              'missing lines', summary['missing_lines'])
    return run['exit_code']


def flaky_worker(order, seed, wallclock):
    from experiments.vt098.test_harness import HarnessTests
    names = unittest.defaultTestLoader.getTestCaseNames(HarnessTests)
    if order == 'reverse':
        names.reverse()
    elif order == 'shuffle':
        random.Random(seed).shuffle(names)
    attempts = []

    def deny(name):
        def blocked(*args, **kwargs):
            attempts.append(name)
            raise AssertionError(f'Forbidden dependency in functional test: {name}')
        return blocked

    stream = io.StringIO()
    with (patch.object(time, 'time', return_value=wallclock),
          patch.object(time, 'sleep', side_effect=deny('sleep')),
          patch.object(socket.socket, 'connect', side_effect=deny('socket.connect')),
          patch.object(socket, 'getaddrinfo', side_effect=deny('DNS'))):
        suite = unittest.TestSuite(HarnessTests(name) for name in names)
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    data = {'order': names, 'seed': seed, 'wallclock': wallclock,
            'tests_run': result.testsRun, 'successful': result.wasSuccessful(),
            'dependency_attempts': attempts, 'log': stream.getvalue()}
    print(json.dumps(data, ensure_ascii=False))
    return 0 if result.wasSuccessful() and not attempts else 1


def flaky_run():
    scenarios = [('normal', 1, 0), ('reverse', 2, 0), ('shuffle', 7, 0),
                 ('normal', 1, 4102444800), ('reverse', 2, 4102444800),
                 ('shuffle', 29, 4102444800)]
    runs = []
    for order, seed, wallclock in scenarios:
        env = {**os.environ, 'PYTHONHASHSEED': str(seed)}
        run = capture(['-m', 'experiments.vt098.quality', 'flaky-worker', '--order', order,
                       '--seed', str(seed), '--wallclock', str(wallclock)], env=env)
        run['parsed'] = json.loads(run['stdout'])
        runs.append(run)
        print(order, seed, wallclock, 'exit', run['exit_code'])
    write_evidence('flaky.json', {'runs': runs,
                   'total_method_executions': sum(run['parsed']['tests_run'] for run in runs),
                   'all_passed': all(run['exit_code'] == 0 for run in runs),
                   'limits': 'Six finite schedules, not all orders/interleavings; SQLite C-level '
                             'busy waits remain real. Wall clock only is patched, not perf_counter.'})
    return 0 if all(run['exit_code'] == 0 for run in runs) else 1


def percentile(samples, fraction):
    ordered = sorted(samples)
    return ordered[math.ceil(fraction * len(ordered)) - 1]


def load_batch(kind, workers, round_number):
    from experiments.vt098.harness import BASIS, HarnessError, PlanHarness
    payload = {'title': 'VT098-Load', 'academic_year_start': 2026, 'semester': 1,
               'course_codes': [], 'expected_basis': BASIS}
    with tempfile.TemporaryDirectory(prefix='vt098-load-') as directory:
        path = Path(directory) / 'load.sqlite'
        store = PlanHarness(path)
        jobs = []
        for index in range(workers):
            if kind == 'hot-key':
                jobs.append(('load-shared', 'hot-key', 'contended-create-or-replay'))
            elif kind == 'mixed' and index < workers // 2:
                account, key = f'load-seed-{index}', f'seed-{index}'
                store.create(account, key, payload)  # Preparation is outside measurement.
                jobs.append((account, key, 'replay'))
            else:
                jobs.append((f'load-new-{index}', f'new-{index}', 'create'))
        released = []
        barrier = threading.Barrier(workers + 1, action=lambda: released.append(time.perf_counter()))
        lock = threading.Lock()
        active, peak = 0, 0

        def request(index):
            nonlocal active, peak
            account, key, group = jobs[index]
            barrier.wait(timeout=30)
            entered = time.perf_counter()
            with lock:
                active += 1
                peak = max(peak, active)
            try:
                response = store.create(account, key, payload)
                status, identity, error = response.status, response.body['id'], None
            except HarnessError as exc:
                status, identity, error = exc.status, None, exc.code
            except Exception as exc:
                status, identity, error = None, None, f'{type(exc).__name__}: {exc}'
            finally:
                ended = time.perf_counter()
                with lock:
                    active -= 1
            return {'index': index, 'group': group, 'status': status, 'id': identity, 'error': error,
                    'start_offset_seconds': entered - released[0],
                    'latency_seconds': ended - released[0]}

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(request, index) for index in range(workers)]
            barrier.wait(timeout=30)
            results = [future.result(timeout=120) for future in futures]
        with closing(sqlite3.connect(path)) as conn:
            counts = tuple(conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                           for table in ('plans', 'audits', 'receipts'))
            pragmas = {key: conn.execute(f'PRAGMA {key}').fetchone()[0]
                       for key in ('journal_mode', 'synchronous', 'busy_timeout')}
        expected = 1 if kind == 'hot-key' else workers
        errors = [item for item in results if item['status'] != 201 or item['error'] is not None]
        unique_ids = len({item['id'] for item in results if item['id'] is not None})
        valid = not errors and counts == (expected,) * 3 and unique_ids == expected
        latencies = [item['latency_seconds'] for item in results]
        p95 = percentile(latencies, .95)
        groups = {group: {'count': len(values), 'p95_seconds': percentile(values, .95)}
                  for group in sorted({item['group'] for item in results})
                  if (values := [item['latency_seconds'] for item in results if item['group'] == group])}
        return {'workload': kind, 'round': round_number, 'offered_workers': workers,
                'ready_at_release': workers, 'peak_calls_inflight': peak, 'samples': results,
                'preseed_count': workers // 2 if kind == 'mixed' else 0,
                'counts': counts, 'expected_counts': [expected] * 3, 'unique_response_ids': unique_ids,
                'oracle_passed': valid, 'error_count': len(errors), 'p50_seconds': percentile(latencies, .5),
                'p95_seconds': p95, 'max_seconds': max(latencies), 'groups': groups,
                'target_seconds': 4.0, 'target_met': valid and p95 <= 4.0,
                'pragmas_on_observer_connection': pragmas,
                'writer_connection_timeout_seconds': 10,
                'payload_bytes': len(json.dumps(payload, ensure_ascii=False).encode('utf-8'))}


def load_run(workers, rounds):
    if workers != 150 or rounds < 1:
        raise ValueError('VT-098 evidence requires exactly 150 workers and positive rounds')
    batches = []
    for round_number in range(1, rounds + 1):
        for kind in ('new', 'hot-key', 'mixed'):
            batch = load_batch(kind, workers, round_number)
            batches.append(batch)
            print(kind, round_number, 'p95', round(batch['p95_seconds'], 4),
                  'errors', batch['error_count'], 'oracle', batch['oracle_passed'],
                  'target', batch['target_met'], flush=True)
    write_evidence('load.json', {'workers': workers, 'rounds': rounds, 'batches': batches,
                   'all_targets_met': all(batch['target_met'] for batch in batches),
                   'clock': 'time.perf_counter, real monotonic',
                   'percentile': 'nearest rank: sorted samples[ceil(0.95*n)-1]',
                   'measurement': 'common barrier release to create() return/error; includes OS '
                                  'dispatch and SQLite lock waiting, excludes setup and network',
                   'limits': '150 ready threads offered together, not 150 production HTTP users; '
                             'peak actual calls reported; nine finite bursts, not sustained load.'})
    return 0 if all(batch['oracle_passed'] for batch in batches) else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('mutation', 'coverage', 'flaky', 'flaky-worker', 'load'))
    parser.add_argument('--mutant-root', type=Path)
    parser.add_argument('--order', choices=('normal', 'reverse', 'shuffle'), default='normal')
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--wallclock', type=int, default=0)
    parser.add_argument('--workers', type=int, default=150)
    parser.add_argument('--rounds', type=int, default=3)
    args = parser.parse_args()
    if args.mode == 'mutation':
        if args.mutant_root is None:
            parser.error('mutation requires --mutant-root')
        return mutation(args.mutant_root.resolve())
    if args.mode == 'coverage':
        return coverage_run()
    if args.mode == 'flaky':
        return flaky_run()
    if args.mode == 'flaky-worker':
        return flaky_worker(args.order, args.seed, args.wallclock)
    return load_run(args.workers, args.rounds)


if __name__ == '__main__':
    raise SystemExit(main())
