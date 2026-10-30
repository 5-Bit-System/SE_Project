"""SQLite create-plan experiment, NOT the production API or its authentication.

Only empty synthetic drafts and the fixture basis are supported. `account_id`
represents an already verified principal supplied by the test, never user input.
The receipt and all business writes commit together in this isolated experiment.
"""

import hashlib
import json
import re
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from experiments.vt098.schema import SemesterPlanInput

BASIS = 'a' * 64  # Synthetic, not an assertion about any student's real catalog.
OPERATION = 'POST /me/semester-plans'


class HarnessError(Exception):
    def __init__(self, status: int, code: str):
        super().__init__(code)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class Response:
    status: int
    body: dict


def validate_key(key: str) -> str:
    if (not isinstance(key, str) or not key or len(key) > 64
            or re.fullmatch(r'[A-Za-z0-9_-]+', key) is None):
        raise HarnessError(400, 'invalid_idempotency_key')
    return hashlib.sha256(key.encode('ascii')).hexdigest()


def normalize(body: dict) -> dict:
    try:
        encoded = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        if len(encoded) > 16384:
            raise HarnessError(413, 'invalid_semester_plan')
        value = SemesterPlanInput.model_validate_json(encoded)
    except (ValidationError, TypeError, ValueError):
        raise HarnessError(422, 'invalid_semester_plan') from None
    if value.expected_version is not None:
        raise HarnessError(422, 'invalid_semester_plan')
    return value.model_dump(mode='json')


def fingerprint(normalized: dict) -> str:
    payload = json.dumps(normalized, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def no_fault(stage: str) -> None:
    pass


class PlanHarness:
    def __init__(self, path: Path):
        self.path = path
        with closing(self.connect()) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY, account_id TEXT NOT NULL, response_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audits (
                    account_id TEXT NOT NULL, plan_id TEXT NOT NULL, event TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS receipts (
                    account_id TEXT NOT NULL, operation TEXT NOT NULL, key_digest TEXT NOT NULL,
                    fingerprint TEXT NOT NULL, plan_id TEXT NOT NULL,
                    status INTEGER NOT NULL, response_json TEXT NOT NULL,
                    PRIMARY KEY (account_id, operation, key_digest));
            ''')

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10, isolation_level=None)

    def create(self, account_id: str, key: str, body: dict,
               fault: Callable[[str], None] = no_fault) -> Response:
        if not account_id:
            raise HarnessError(401, 'account_required')
        key_digest = validate_key(key)
        normalized = normalize(body)
        request_fingerprint = fingerprint(normalized)
        with closing(self.connect()) as conn:
            # SQLite serializes writers; PostgreSQL account-row locking is untested.
            conn.execute('BEGIN IMMEDIATE')
            try:
                receipt = conn.execute('''SELECT fingerprint, status, response_json FROM receipts
                    WHERE account_id=? AND operation=? AND key_digest=?''',
                    (account_id, OPERATION, key_digest)).fetchone()
                if receipt is not None:
                    if receipt[0] != request_fingerprint:
                        raise HarnessError(409, 'idempotency_conflict')
                    conn.commit()
                    return Response(receipt[1], json.loads(receipt[2]))
                # A replay describes the original commit, not current academic facts.
                if normalized['course_codes']:
                    raise HarnessError(422, 'nonempty_courses_outside_harness')
                if normalized['expected_basis'] != BASIS:
                    raise HarnessError(409, 'context_changed')
                count = conn.execute('SELECT count(*) FROM plans WHERE account_id=?',
                                     (account_id,)).fetchone()[0]
                if count >= 100:
                    raise HarnessError(409, 'semester_plan_limit')
                response = {**normalized, 'id': str(uuid.uuid4()), 'version': 1}
                encoded = json.dumps(response, ensure_ascii=False, sort_keys=True)
                conn.execute('INSERT INTO plans VALUES (?, ?, ?)',
                             (response['id'], account_id, encoded))
                fault('after_plan')
                conn.execute('INSERT INTO audits VALUES (?, ?, ?)',
                             (account_id, response['id'], 'save_semester_plan'))
                fault('after_audit')
                conn.execute('INSERT INTO receipts VALUES (?, ?, ?, ?, ?, ?, ?)',
                             (account_id, OPERATION, key_digest, request_fingerprint,
                              response['id'], 201, encoded))
                fault('after_receipt')
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        fault('after_commit')
        return Response(201, response)
