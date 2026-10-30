"""AI draft: two deliberately weak tests plus one meaningful red test."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from experiments.vt098.harness import BASIS, PlanHarness

ACCOUNT = '00000000-0000-4000-8000-000000000001'


def body():
    return {'title': 'VT098-Draft', 'academic_year_start': 2026, 'semester': 1,
            'course_codes': [], 'expected_basis': BASIS}


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='vt098-')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'plans.sqlite'
        self.store = PlanHarness(self.path)

    def counts(self):
        with closing(sqlite3.connect(self.path)) as conn:
            return tuple(conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                         for table in ('plans', 'audits', 'receipts'))

    def test_ai_draft_retry_status_only(self):
        first = self.store.create(ACCOUNT, 'vt098-k0', body())
        second = self.store.create(ACCOUNT, 'vt098-k0', body())
        self.assertEqual((first.status, second.status), (201, 201))

    def test_ai_draft_duplicate_happy_path(self):
        self.store.create(ACCOUNT, 'vt098-k0', body())
        self.assertEqual(self.store.create(ACCOUNT, 'vt098-k0', body()).status, 201)

    def test_retry_after_reopen_preserves_result(self):
        first = self.store.create(ACCOUNT, 'vt098-k0', body())
        reopened = PlanHarness(self.path)
        replay = reopened.create(ACCOUNT, 'vt098-k0', body())
        self.assertEqual(first.body, replay.body)
        self.assertEqual(self.counts(), (1, 1, 1))


if __name__ == '__main__':
    unittest.main()
