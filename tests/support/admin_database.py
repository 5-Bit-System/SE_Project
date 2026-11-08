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


def ensure_test_admin_account(conn):
    try:
        from sqlalchemy import text
        row = conn.execute(
            text("SELECT id FROM accounts WHERE id = '57e9a52b-7365-4fe2-b9ce-1320ef48dc02'")
        ).scalar()
        if not row:
            conn.execute(
                text("""
                    INSERT INTO accounts (id, username, password_hash, role)
                    VALUES ('57e9a52b-7365-4fe2-b9ce-1320ef48dc02', 'test_admin_57e9a52b', 'hash_test', 'admin')
                    ON CONFLICT DO NOTHING
                """)
            )
    except Exception:
        pass


@contextmanager
def db_transaction_rollback():
    eng = admin_test_engine()
    with eng.connect() as conn:
        trans = conn.begin_nested() if conn.in_transaction() else conn.begin()
        ensure_test_admin_account(conn)
        try:
            yield conn
        finally:
            if trans.is_active:
                trans.rollback()


@pytest.fixture
def isolated_db_conn():
    with db_transaction_rollback() as conn:
        yield conn


