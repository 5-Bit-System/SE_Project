"""SQLite create-plan experiment, NOT the production API or its authentication.

Only empty synthetic drafts and the fixture basis are supported. `account_id`
represents an already verified principal supplied by the test, never user input.
The initial version deliberately models the existing create-on-every-call flow.
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
        validate_key(key)
        normalized = normalize(body)
        if normalized['course_codes']:
            raise HarnessError(422, 'nonempty_courses_outside_harness')
        if normalized['expected_basis'] != BASIS:
            raise HarnessError(409, 'context_changed')
        response = {**normalized, 'id': str(uuid.uuid4()), 'version': 1}
        encoded = json.dumps(response, ensure_ascii=False, sort_keys=True)
        with closing(self.connect()) as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                conn.execute('INSERT INTO plans VALUES (?, ?, ?)',
                             (response['id'], account_id, encoded))
                fault('after_plan')
                conn.execute('INSERT INTO audits VALUES (?, ?, ?)',
                             (account_id, response['id'], 'save_semester_plan'))
                fault('after_audit')
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        fault('after_commit')
        return Response(201, response)
