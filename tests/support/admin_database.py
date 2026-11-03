"""Explicit disposable targets and rollback-only admin test connections."""
import os
from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine

from tests.support.postgres_targets import validate_hus_test_target

_active = None


def admin_test_url():
    raw = os.environ.get('HUS_TEST_DATABASE_URL')
    if not raw:
        pytest.skip('Admin DB tests require explicit HUS_TEST_DATABASE_URL')
    validate_hus_test_target(raw)
    return raw


def admin_test_engine():
    return _active if _active is not None else create_engine(admin_test_url())


class TransactionEngine:
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def begin(self):
        with self.connection.begin_nested():
            yield self.connection

    @contextmanager
    def connect(self):
        yield self.connection

    def dispose(self):
        pass
