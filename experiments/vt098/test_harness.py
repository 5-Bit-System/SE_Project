"""Reviewed individual tests: durable results and side effects, not status alone.

All accounts, bases, keys and drafts are synthetic. No production API is called.
"""

import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from itertools import combinations, product
from pathlib import Path

from experiments.vt098.harness import (
    BASIS,
    HarnessError,
    PlanHarness,
    fingerprint,
    normalize,
    validate_key,
)

ACCOUNT = '00000000-0000-4000-8000-000000000001'
OTHER = '00000000-0000-4000-8000-000000000002'
PAIRWISE = (
    (0, 0, 0, 0), (0, 0, 1, 1), (0, 1, 0, 1), (0, 1, 1, 0),
    (1, 0, 0, 1), (1, 0, 1, 0), (1, 1, 0, 0), (1, 1, 1, 1),
)


def body():
    return {'title': 'VT098-Draft', 'academic_year_start': 2026, 'semester': 1,
            'course_codes': [], 'expected_basis': BASIS}


class InjectedFailure(Exception):
    pass


def fail_at(expected):
    def fault(stage):
        if stage == expected:
            raise InjectedFailure(stage)
    return fault


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='vt098-')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'plans.sqlite'
        self.store = PlanHarness(self.path)

    def counts(self, path=None, account=None):
        # Independent connection/oracle, not an implementation counting helper.
        with closing(sqlite3.connect(path or self.path)) as conn:
            where = ' WHERE account_id=?' if account else ''
            params = (account,) if account else ()
            return tuple(conn.execute(f'SELECT count(*) FROM {table}' + where, params).fetchone()[0]
                         for table in ('plans', 'audits', 'receipts'))

    def test_retry_response_and_counts(self):
        # Replaces AI draft D1, which incorrectly accepted two different IDs.
        first = self.store.create(ACCOUNT, 'vt098-k0', body())
        second = self.store.create(ACCOUNT, 'vt098-k0', body())
        self.assertEqual((first.status, second.status), (201, 201))
        self.assertEqual(first.body, second.body)
        self.assertEqual(first.body['version'], 1)
        self.assertEqual(self.counts(), (1, 1, 1))

    def test_failure_before_commit_rolls_back_then_retry(self):
        # Replaces duplicated AI happy path D2 with a controlled failure path.
        for stage in ('after_plan', 'after_audit', 'after_receipt'):
            with self.subTest(stage=stage):
                path = Path(self.temp.name) / f'{stage}.sqlite'
                store = PlanHarness(path)
                with self.assertRaises(InjectedFailure):
                    store.create(ACCOUNT, 'vt098-k0', body(), fault=fail_at(stage))
                self.assertEqual(self.counts(path), (0, 0, 0))
                self.assertEqual(store.create(ACCOUNT, 'vt098-k0', body()).status, 201)
                self.assertEqual(self.counts(path), (1, 1, 1))

    def test_retry_after_reopen_preserves_result(self):
        first = self.store.create(ACCOUNT, 'vt098-k0', body())
        reopened = PlanHarness(self.path)
        replay = reopened.create(ACCOUNT, 'vt098-k0', body())
        self.assertEqual(first.body, replay.body)
        self.assertEqual(self.counts(), (1, 1, 1))

    def test_pairwise_has_all_24_pairs(self):
        required = {(i, j, a, b) for i, j in combinations(range(4), 2)
                    for a, b in product(range(2), repeat=2)}
        covered = {(i, j, row[i], row[j]) for row in PAIRWISE
                   for i, j in combinations(range(4), 2)}
        self.assertEqual(len(set(PAIRWISE)), 8)
        self.assertEqual(covered, required)

    def test_pairwise_create_replay_conflict_and_scope(self):
        for index, (new_key, changed, other, parallel) in enumerate(PAIRWISE, start=1):
            with self.subTest(case=f'TC{index:02d}'):
                path = Path(self.temp.name) / f'pairwise-{index}.sqlite'
                store = PlanHarness(path)
                seed = store.create(ACCOUNT, 'vt098-k0', body())
                account = OTHER if other else ACCOUNT
                key = 'vt098-k1' if new_key else 'vt098-k0'
                payload = {**body(), 'title': 'VT098-Alternative'} if changed else body()
                gate = threading.Barrier(2) if parallel else None

                def request():
                    if gate is not None:
                        gate.wait(timeout=10)
                    try:
                        result = store.create(account, key, payload)
                        return result.status, result.body
                    except HarnessError as exc:
                        return exc.status, {'detail': exc.code}

                if parallel:
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        futures = [executor.submit(request) for _ in range(2)]
                        results = [future.result(timeout=15) for future in futures]
                else:
                    results = [request(), request()]
                conflict = not new_key and changed and not other
                self.assertEqual([status for status, _ in results], [409 if conflict else 201] * 2)
                self.assertEqual(results[0][1], results[1][1])
                created = bool(new_key or other)
                self.assertEqual(self.counts(path), (1 + int(created),) * 3)
                if conflict:
                    self.assertEqual(results[0][1], {'detail': 'idempotency_conflict'})
                elif created:
                    self.assertNotEqual(seed.body['id'], results[0][1]['id'])
                    self.assertEqual(results[0][1]['version'], 1)
                else:
                    self.assertEqual(results[0][1], seed.body)
                if other:
                    self.assertEqual(self.counts(path, ACCOUNT), (1, 1, 1))
                    self.assertEqual(self.counts(path, OTHER), (1, 1, 1))

    def test_valid_key_boundaries(self):
        for length in (1, 63, 64):
            with self.subTest(length=length):
                self.assertEqual(self.store.create(ACCOUNT, 'k' * length, body()).status, 201)
        self.assertEqual(self.counts(), (3, 3, 3))

    def test_invalid_keys_do_not_write(self):
        for key in (None, '', 'k' * 65, 'bad key', 'bad.key', 'khóa'):
            with self.subTest(key=key):
                with self.assertRaises(HarnessError) as error:
                    self.store.create(ACCOUNT, key, body())
                self.assertEqual((error.exception.status, error.exception.code),
                                 (400, 'invalid_idempotency_key'))
                self.assertEqual(self.counts(), (0, 0, 0))

    def test_canonicalization_uses_real_schema_defaults(self):
        original = fingerprint(normalize(body()))
        reordered = dict(reversed(list(body().items())))
        explicit = {**reordered, 'max_credits': 20}
        self.assertEqual(original, fingerprint(normalize(explicit)))
        for change in ({'title': 'Changed'}, {'expected_basis': 'b' * 64}):
            self.assertNotEqual(original, fingerprint(normalize({**body(), **change})))
        first = normalize({**body(), 'course_codes': ['TEST-A', 'TEST-B']})
        reverse = normalize({**body(), 'course_codes': ['TEST-B', 'TEST-A']})
        self.assertNotEqual(fingerprint(first), fingerprint(reverse))

    def test_conflict_keeps_original_unchanged(self):
        first = self.store.create(ACCOUNT, 'vt098-k0', body())
        with self.assertRaises(HarnessError) as error:
            self.store.create(ACCOUNT, 'vt098-k0', {**body(), 'title': 'Changed'})
        self.assertEqual((error.exception.status, error.exception.code), (409, 'idempotency_conflict'))
        self.assertEqual(self.store.create(ACCOUNT, 'vt098-k0', body()).body, first.body)
        self.assertEqual(self.counts(), (1, 1, 1))

    def test_lost_response_after_commit_replays_receipt(self):
        with self.assertRaises(InjectedFailure):
            self.store.create(ACCOUNT, 'vt098-k0', body(), fault=fail_at('after_commit'))
        self.assertEqual(self.counts(), (1, 1, 1))
        with closing(sqlite3.connect(self.path)) as conn:
            expected = json.loads(conn.execute('SELECT response_json FROM receipts').fetchone()[0])
        replay = PlanHarness(self.path).create(ACCOUNT, 'vt098-k0', body())
        self.assertEqual((replay.status, replay.body), (201, expected))
        self.assertEqual(self.counts(), (1, 1, 1))

    def test_new_key_same_body_creates_separate_intent(self):
        first = self.store.create(ACCOUNT, 'vt098-k0', body())
        second = self.store.create(ACCOUNT, 'vt098-k1', body())
        self.assertNotEqual(first.body['id'], second.body['id'])
        self.assertEqual(self.counts(), (2, 2, 2))

    def test_account_scope_and_required_principal(self):
        first = self.store.create(ACCOUNT, 'vt098-k0', body())
        other = self.store.create(OTHER, 'vt098-k0', body())
        self.assertNotEqual(first.body['id'], other.body['id'])
        self.assertEqual(self.counts(account=ACCOUNT), (1, 1, 1))
        self.assertEqual(self.counts(account=OTHER), (1, 1, 1))
        with self.assertRaises(HarnessError) as error:
            self.store.create('', 'vt098-k0', body())
        self.assertEqual(error.exception.status, 401)
        self.assertEqual(self.counts(), (2, 2, 2))

    def test_real_schema_forbids_extra_and_non_strict_input(self):
        for change in ({'account_id': OTHER}, {'academic_year_start': '2026'},
                       {'title': '  '}, {'expected_version': 1}):
            with self.subTest(change=change), self.assertRaises(HarnessError) as error:
                self.store.create(ACCOUNT, 'vt098-k0', {**body(), **change})
            self.assertEqual(error.exception.status, 422)
        self.assertEqual(self.counts(), (0, 0, 0))

    def test_basis_and_nonempty_courses_are_not_faked(self):
        for change, code in (({'expected_basis': 'b' * 64}, 'context_changed'),
                             ({'course_codes': ['TEST-A']}, 'nonempty_courses_outside_harness')):
            with self.subTest(change=change), self.assertRaises(HarnessError) as error:
                self.store.create(ACCOUNT, 'vt098-k0', {**body(), **change})
            self.assertEqual(error.exception.code, code)
        self.assertEqual(self.counts(), (0, 0, 0))

    def test_replay_at_limit_does_not_create_again(self):
        first = self.store.create(ACCOUNT, 'vt098-k0', body())
        for index in range(1, 100):
            self.store.create(ACCOUNT, f'new-{index}', body())
        self.assertEqual(self.store.create(ACCOUNT, 'vt098-k0', body()).body, first.body)
        with self.assertRaises(HarnessError) as error:
            self.store.create(ACCOUNT, 'over-limit', body())
        self.assertEqual(error.exception.code, 'semester_plan_limit')
        self.assertEqual(self.counts(), (100, 100, 100))

    def test_receipt_does_not_resurrect_deleted_plan(self):
        first = self.store.create(ACCOUNT, 'vt098-k0', body())
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute('DELETE FROM plans WHERE id=?', (first.body['id'],))
            conn.commit()
        replay = self.store.create(ACCOUNT, 'vt098-k0', body())
        self.assertEqual(replay.body, first.body)
        self.assertEqual(self.counts(), (0, 1, 1))

    def test_receipt_is_read_before_current_basis_validation(self):
        from unittest.mock import patch
        first = self.store.create(ACCOUNT, 'vt098-k0', body())
        with patch('experiments.vt098.harness.BASIS', 'b' * 64):
            self.assertEqual(self.store.create(ACCOUNT, 'vt098-k0', body()).body, first.body)
            with self.assertRaises(HarnessError) as error:
                self.store.create(ACCOUNT, 'vt098-new', body())
        self.assertEqual(error.exception.code, 'context_changed')
        self.assertEqual(self.counts(), (1, 1, 1))

    def test_key_digest_does_not_persist_raw_key(self):
        self.store.create(ACCOUNT, 'vt098-private-intent', body())
        with closing(sqlite3.connect(self.path)) as conn:
            row = conn.execute('SELECT key_digest FROM receipts').fetchone()
        self.assertIsNotNone(row, 'A committed create must have a receipt')
        stored = row[0]
        self.assertEqual(stored, validate_key('vt098-private-intent'))
        self.assertNotEqual(stored, 'vt098-private-intent')


if __name__ == '__main__':
    unittest.main()
