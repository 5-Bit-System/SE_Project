"""Test suite for VT-099: Reviewer Role RBAC and Concurrency Conflict Protection (Compare-and-Set).

Test Matrix:
- TC-01 (DB Integration): Reviewer account exists, login() succeeds and session_from_token() resolves role == 'reviewer'.
- TC-02 (DB Integration): Account with unsupported role (e.g. 'guest') fails login() with AuthFailure (401).
- TC-03 (API): Reviewer calls GET /admin/crawler/documents -> 200 OK.
- TC-04 (API): Reviewer calls GET /admin/crawler/documents/{doc_id} -> 200 OK.
- TC-05 (API): Reviewer calls POST /admin/crawler/documents/{doc_id}/approve -> 200 OK, review_status == 'approved'.
- TC-06 (API): Reviewer calls POST /admin/crawler/documents/{doc_id}/reject -> 200 OK, review_status == 'rejected'.
- TC-07 (API Negative): Reviewer calls GET (200 OK), then calls PUT /admin/crawler/documents/{doc_id}/metadata -> 403 Forbidden.
- TC-08 (API Regression): Student calls POST .../approve -> 403 Forbidden.
- TC-09 (API Regression): Anonymous calls POST .../approve -> 401 Unauthorized.
- TC-10 (Service Concurrency): Two real DB connections, 1 pending doc, 2 threads with Barrier(2), Thread 1 approves,
         Thread 2 rejects, both send expected_status="pending". Exactly one commits and one raises DocumentConflictError.
- TC-11 (API Conflict): Document already approved. Reviewer sends POST .../reject with expected_status="pending" -> 409 Conflict.
- TC-12 (API/DB Audit): Reviewer approves document -> admin_audit_logs has entry with actor_id == reviewer_id.
"""

import threading
import pytest
from sqlalchemy import text

from app.auth import repository
from app.auth.security import AuthFailure, password_hash
from app.crawler.document_review_service import (
    create_document,
    get_document,
    review_document,
)
from tests.support.admin_database import admin_test_engine, admin_test_url

try:
    from app.crawler.document_review_service import DocumentConflictError
except ImportError:
    DocumentConflictError = None  # Expected during RED phase

pytestmark = pytest.mark.hus_postgres

REVIEWER_1_ID = "55555555-5555-4555-8555-111111111111"
REVIEWER_1_EMAIL = "reviewer1_vt099@hus.vnu.edu.vn"
REVIEWER_2_ID = "55555555-5555-4555-8555-222222222222"
REVIEWER_2_EMAIL = "reviewer2_vt099@hus.vnu.edu.vn"
GUEST_ID = "55555555-5555-4555-8555-333333333333"
GUEST_EMAIL = "guest_vt099@hus.vnu.edu.vn"
TEST_PASSWORD = "StrongReviewerPassword2026!"


def ensure_account(eng, account_id: str, email: str, password: str, role: str = "reviewer"):
    uname = f"usr_{account_id.replace('-', '')[:20]}"
    with eng.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO accounts (
                    id, username, email, email_normalized, display_name,
                    password_hash, role, email_verified_at, is_active,
                    must_change_password
                )
                VALUES (
                    :id, :username, :email, :email, :name,
                    :pw_hash, :role, now(), true, false
                )
                ON CONFLICT (username) DO UPDATE SET
                    id = EXCLUDED.id,
                    role = EXCLUDED.role,
                    email = EXCLUDED.email,
                    email_normalized = EXCLUDED.email_normalized,
                    password_hash = EXCLUDED.password_hash,
                    email_verified_at = now(),
                    is_active = true,
                    must_change_password = false
            """),
            {
                "id": account_id,
                "username": uname,
                "email": email,
                "name": f"Test User {account_id[:8]}",
                "pw_hash": password_hash(password),
                "role": role,
            },
        )


def ensure_test_doc(eng, doc_id: str = "doc_vt099_test_pending") -> dict:
    with eng.begin() as conn:
        conn.execute(text("DELETE FROM crawled_documents WHERE id = :id"), {"id": doc_id})
        return create_document(
            conn,
            url=f"https://hus.vnu.edu.vn/{doc_id}",
            title="Tài liệu đào tạo kiểm thử VT-099",
            markdown_content="# Nội dung văn bản chi tiết tài liệu kiểm thử đạt tiêu chuẩn phê duyệt và kiểm tra concurrency.",
            major="toan_hoc",
            doc_type="curriculum",
            source_id="src_hus_main",
            doc_id=doc_id,
        )


@pytest.fixture(autouse=True)
def setup_engine(monkeypatch, tmp_path):
    admin_test_url()
    eng = admin_test_engine()
    with eng.begin() as conn:
        conn.execute(text("ALTER TABLE accounts DROP CONSTRAINT IF EXISTS accounts_role_check"))
        conn.execute(
            text(
                "ALTER TABLE accounts ADD CONSTRAINT accounts_role_check "
                "CHECK (role in ('student', 'teacher', 'admin', 'reviewer', 'guest'))"
            )
        )
    monkeypatch.setattr("app.api.admin.engine", lambda: eng)
    monkeypatch.setattr("app.auth.repository.engine", lambda: eng)
    monkeypatch.setattr("app.integrations.daotao.store.engine", lambda: eng)
    monkeypatch.setattr("app.api.admin.export_git_reviews_from_db", lambda *args, **kwargs: None)

    import app.crawler.document_review_service as drs
    test_reviews = tmp_path / "vt099_test_reviews.json"
    monkeypatch.setattr(drs, "DEFAULT_REVIEWS_FILE", test_reviews)


@pytest.fixture(autouse=True)
def cleanup_data():
    eng = admin_test_engine()

    def _cleanup():
        with eng.begin() as conn:
            conn.execute(
                text("""
                    DELETE FROM admin_audit_logs
                    WHERE actor_id IN (:id1, :id2, :id3)
                       OR target_id LIKE 'doc_vt099%'
                """),
                {"id1": REVIEWER_1_ID, "id2": REVIEWER_2_ID, "id3": GUEST_ID},
            )
            conn.execute(
                text("DELETE FROM auth_sessions WHERE account_id IN (:id1, :id2, :id3)"),
                {"id1": REVIEWER_1_ID, "id2": REVIEWER_2_ID, "id3": GUEST_ID},
            )
            conn.execute(text("DELETE FROM crawled_documents WHERE id LIKE 'doc_vt099%'"))
            conn.execute(
                text(
                    "DELETE FROM accounts "
                    "WHERE id IN (:id1, :id2, :id3) OR username LIKE 'usr_55555555%'"
                ),
                {"id1": REVIEWER_1_ID, "id2": REVIEWER_2_ID, "id3": GUEST_ID},
            )

    _cleanup()
    try:
        yield
    finally:
        _cleanup()


@pytest.fixture
def sample_pending_doc():
    eng = admin_test_engine()
    ensure_account(eng, REVIEWER_1_ID, REVIEWER_1_EMAIL, TEST_PASSWORD, role="reviewer")
    ensure_account(eng, REVIEWER_2_ID, REVIEWER_2_EMAIL, TEST_PASSWORD, role="reviewer")
    doc_id = "doc_vt099_test_pending"
    ensure_test_doc(eng, doc_id)
    with eng.connect() as conn:
        return get_document(conn, doc_id)


@pytest.fixture
def reviewer_client(fake_accounts):
    from fastapi.testclient import TestClient
    from app.main import app

    eng = admin_test_engine()
    ensure_account(eng, REVIEWER_1_ID, REVIEWER_1_EMAIL, TEST_PASSWORD, role="reviewer")

    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        fake_accounts.issue(client, owner="reviewer1")
        for session in fake_accounts.sessions.values():
            session["role"] = "reviewer"
            session["account_id"] = REVIEWER_1_ID
            session["email"] = REVIEWER_1_EMAIL
        yield client


@pytest.fixture
def student_client(fake_accounts):
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        fake_accounts.issue(client, owner="student1")
        for session in fake_accounts.sessions.values():
            session["role"] = "student"
            session["account_id"] = "00000000-0000-4000-8000-000000000456"
        yield client


@pytest.fixture
def anonymous_client():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        yield client


# ===========================================================================
# TC-01 & TC-02: DB Authentication & Session Integration
# ===========================================================================


def test_tc01_reviewer_db_login_and_session():
    """TC-01 (DB Integration): Reviewer account exists, login() succeeds and session_from_token() resolves role == 'reviewer'."""
    eng = admin_test_engine()
    ensure_account(eng, REVIEWER_1_ID, REVIEWER_1_EMAIL, TEST_PASSWORD, role="reviewer")

    raw_token = repository.login(REVIEWER_1_EMAIL, TEST_PASSWORD)
    assert raw_token is not None

    session = repository.session_from_token(raw_token)
    assert session is not None
    assert session["role"] == "reviewer"
    assert session["account_id"] == REVIEWER_1_ID


def test_tc02_unsupported_role_db_login_fails():
    """TC-02 (DB Integration): Account with unsupported role (e.g. 'guest') fails login() with AuthFailure (401)."""
    eng = admin_test_engine()
    ensure_account(eng, GUEST_ID, GUEST_EMAIL, TEST_PASSWORD, role="guest")

    with pytest.raises(AuthFailure) as exc_info:
        repository.login(GUEST_EMAIL, TEST_PASSWORD)
    assert exc_info.value.status == 401
    assert exc_info.value.code == "invalid_login"


# ===========================================================================
# TC-03 to TC-06: API RBAC Endpoints for Reviewer (200 OK)
# ===========================================================================


def test_tc03_reviewer_list_documents(reviewer_client, sample_pending_doc):
    """TC-03 (API): Reviewer calls GET /admin/crawler/documents -> 200 OK."""
    resp = reviewer_client.get("/admin/crawler/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert "documents" in data
    assert any(d["id"] == sample_pending_doc["id"] for d in data["documents"])


def test_tc04_reviewer_get_document_detail(reviewer_client, sample_pending_doc):
    """TC-04 (API): Reviewer calls GET /admin/crawler/documents/{doc_id} -> 200 OK."""
    doc_id = sample_pending_doc["id"]
    resp = reviewer_client.get(f"/admin/crawler/documents/{doc_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == doc_id
    assert data["review_status"] == "pending"


def test_tc05_reviewer_approve_document(reviewer_client, sample_pending_doc):
    """TC-05 (API): Reviewer calls POST /admin/crawler/documents/{doc_id}/approve -> 200 OK, review_status == 'approved'."""
    doc_id = sample_pending_doc["id"]
    resp = reviewer_client.post(
        f"/admin/crawler/documents/{doc_id}/approve",
        json={"reason": "Nội dung chuẩn chương trình đào tạo chính quy"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["review_status"] == "approved"
    assert data["reviewer_id"] == REVIEWER_1_ID


def test_tc06_reviewer_reject_document(reviewer_client, sample_pending_doc):
    """TC-06 (API): Reviewer calls POST /admin/crawler/documents/{doc_id}/reject -> 200 OK, review_status == 'rejected'."""
    doc_id = sample_pending_doc["id"]
    resp = reviewer_client.post(
        f"/admin/crawler/documents/{doc_id}/reject",
        json={"reason": "Nội dung hết hạn tuyển sinh và đào tạo"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["review_status"] == "rejected"
    assert data["reviewer_id"] == REVIEWER_1_ID


# ===========================================================================
# TC-07 to TC-09: Negative and Regression RBAC Tests
# ===========================================================================


def test_tc07_reviewer_cannot_update_metadata_negative(reviewer_client, sample_pending_doc):
    """TC-07 (API Negative): Reviewer calls GET (200 OK), then calls PUT /metadata -> 403 Forbidden (anti-vacuous)."""
    doc_id = sample_pending_doc["id"]

    # Step 1: GET documents succeeds with 200 OK (verifies active reviewer authentication)
    get_resp = reviewer_client.get(f"/admin/crawler/documents/{doc_id}")
    assert get_resp.status_code == 200

    # Step 2: PUT metadata is strictly forbidden for reviewer
    put_resp = reviewer_client.put(
        f"/admin/crawler/documents/{doc_id}/metadata",
        json={"title": "Tiêu đề bị sửa trái phép bởi reviewer", "major": "data_science"},
    )
    assert put_resp.status_code == 403

    # Step 3: Verify DB metadata was NOT changed
    eng = admin_test_engine()
    with eng.connect() as conn:
        doc = get_document(conn, doc_id)
        assert doc["title"] == sample_pending_doc["title"]
        assert doc["title"] != "Tiêu đề bị sửa trái phép bởi reviewer"


def test_tc08_student_cannot_approve_document_regression(student_client, sample_pending_doc):
    """TC-08 (API Regression): Student calls POST .../approve -> 403 Forbidden."""
    doc_id = sample_pending_doc["id"]
    resp = student_client.post(
        f"/admin/crawler/documents/{doc_id}/approve",
        json={"reason": "Sinh viên cố tình can thiệp duyệt tài liệu"},
    )
    assert resp.status_code == 403


def test_tc09_anonymous_cannot_approve_document_regression(anonymous_client, sample_pending_doc):
    """TC-09 (API Regression): Anonymous calls POST .../approve -> 401 Unauthorized."""
    doc_id = sample_pending_doc["id"]
    resp = anonymous_client.post(
        f"/admin/crawler/documents/{doc_id}/approve",
        json={"reason": "Ẩn danh cố tình duyệt tài liệu"},
    )
    assert resp.status_code == 401


# ===========================================================================
# TC-10 to TC-12: Concurrency Race Condition, API Conflict & Audit
# ===========================================================================


def test_tc10_service_concurrency_race_condition_barrier(sample_pending_doc):
    """TC-10 (Service Concurrency): Two real DB connections, 1 pending doc, 2 threads with Barrier(2),
    Thread 1 approves, Thread 2 rejects, both send expected_status='pending'.
    Assert exactly one commits and one raises DocumentConflictError."""
    eng = admin_test_engine()
    doc_id = sample_pending_doc["id"]

    barrier = threading.Barrier(2)
    results = {}
    exceptions = {}

    def worker_approve():
        with eng.connect() as conn:
            try:
                with conn.begin():
                    barrier.wait(timeout=10)
                    res = review_document(
                        conn,
                        doc_id,
                        decision="approved",
                        reason="Đồng thời phê duyệt từ luồng 1",
                        reviewer_id=REVIEWER_1_ID,
                        expected_status="pending",
                    )
                    results["approve"] = res
            except Exception as exc:
                exceptions["approve"] = exc

    def worker_reject():
        with eng.connect() as conn:
            try:
                with conn.begin():
                    barrier.wait(timeout=10)
                    res = review_document(
                        conn,
                        doc_id,
                        decision="rejected",
                        reason="Đồng thời từ chối từ luồng 2",
                        reviewer_id=REVIEWER_2_ID,
                        expected_status="pending",
                    )
                    results["reject"] = res
            except Exception as exc:
                exceptions["reject"] = exc

    t1 = threading.Thread(target=worker_approve, name="worker_approve")
    t2 = threading.Thread(target=worker_reject, name="worker_reject")

    t1.start()
    t2.start()
    t1.join(timeout=15)
    t2.join(timeout=15)

    # In RED phase, expected_status argument does not exist yet (TypeError),
    # or DocumentConflictError is not raised.
    # Assert exactly one thread commits successfully:
    assert len(results) == 1, (
        f"Expected exactly 1 successful commit, got {len(results)}. "
        f"Results: {results}, Exceptions: {exceptions}"
    )

    # Assert exactly one thread caught DocumentConflictError:
    conflict_exceptions = [
        exc for exc in exceptions.values()
        if DocumentConflictError is not None and isinstance(exc, DocumentConflictError)
    ]
    assert len(conflict_exceptions) == 1, (
        f"Expected exactly 1 DocumentConflictError, got {len(conflict_exceptions)}. "
        f"Exceptions: {exceptions}"
    )

    # Verify DB state matches the winner
    with eng.connect() as conn:
        final_doc = get_document(conn, doc_id)
        expected_status = "approved" if "approve" in results else "rejected"
        assert final_doc["review_status"] == expected_status


def test_tc11_api_conflict_returns_409(reviewer_client, sample_pending_doc):
    """TC-11 (API Conflict): Document already approved. Reviewer sends POST .../reject with expected_status='pending' -> 409 Conflict."""
    doc_id = sample_pending_doc["id"]
    eng = admin_test_engine()
    ensure_account(eng, REVIEWER_1_ID, REVIEWER_1_EMAIL, TEST_PASSWORD, role="reviewer")

    # Precondition: document is already approved
    with eng.begin() as conn:
        conn.execute(
            text("""
                UPDATE crawled_documents
                SET review_status = 'approved',
                    review_reason = 'Đã được duyệt từ trước',
                    reviewer_id = :rid,
                    reviewed_at = now()
                WHERE id = :id
            """),
            {"rid": REVIEWER_1_ID, "id": doc_id},
        )

    # Reviewer sends reject with expected_status="pending"
    resp = reviewer_client.post(
        f"/admin/crawler/documents/{doc_id}/reject",
        json={
            "reason": "Phát hiện tài liệu không đạt chuẩn sau khi thấy pending",
            "expected_status": "pending",
        },
    )
    assert resp.status_code == 409
    data = resp.json()
    assert "detail" in data
    assert "approved" in data["detail"].lower() or "pending" in data["detail"].lower()


def test_tc12_reviewer_audit_log_recorded(reviewer_client, sample_pending_doc):
    """TC-12 (API/DB Audit): Reviewer approves document -> admin_audit_logs has entry with actor_id == reviewer_id."""
    doc_id = sample_pending_doc["id"]
    resp = reviewer_client.post(
        f"/admin/crawler/documents/{doc_id}/approve",
        json={"reason": "Phê duyệt với kiểm toán đầy đủ giải trình"},
    )
    assert resp.status_code == 200

    eng = admin_test_engine()
    with eng.connect() as conn:
        log = conn.execute(
            text("""
                SELECT actor_id, action, target_type, target_id
                FROM admin_audit_logs
                WHERE target_id = :doc_id AND action = 'document.approve'
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"doc_id": doc_id},
        ).mappings().one_or_none()

        assert log is not None
        assert log["actor_id"] == REVIEWER_1_ID
        assert log["action"] == "document.approve"
        assert log["target_id"] == doc_id
