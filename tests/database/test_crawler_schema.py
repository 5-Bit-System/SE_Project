"""Database tests for crawler sources and jobs lifecycle tables."""

from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine

from app.crawler.repository import (
    cancel_job,
    complete_job,
    create_job,
    create_source,
    fail_job,
    pause_job,
    resume_job,
    seed_default_sources_if_empty,
    toggle_source,
    update_source,
)

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@pytest.fixture(scope="module")
def db_engine():
    config = dotenv_values(ENV_PATH)
    url = config.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not configured")
    eng = create_engine(url)
    return eng


def test_crawler_sources_crud(db_engine):
    with db_engine.begin() as conn:
        # Seed defaults
        defaults = seed_default_sources_if_empty(conn)
        assert len(defaults) >= 3

        # Create new source
        src = create_source(
            conn,
            name="Test Source KHTN",
            base_url="https://hus.vnu.edu.vn/dao-tao",
            schedule="0 1 * * *",
            depth_limit=4,
        )
        assert src["name"] == "Test Source KHTN"
        assert src["depth_limit"] == 4
        assert src["is_active"] is True

        # Update source
        upd = update_source(conn, src["id"], name="Updated Source KHTN", depth_limit=5)
        assert upd["name"] == "Updated Source KHTN"
        assert upd["depth_limit"] == 5

        # Toggle source
        toggled = toggle_source(conn, src["id"], is_active=False)
        assert toggled["is_active"] is False


def test_crawler_jobs_lifecycle(db_engine):
    with db_engine.begin() as conn:
        src = create_source(
            conn,
            name="Job Test Source",
            base_url="https://hus.vnu.edu.vn/test-job",
        )

        # 1. Create job (status = running)
        job = create_job(conn, source_id=src["id"])
        assert job["status"] == "running"
        assert job["pages_crawled"] == 0

        # 2. Pause job
        p_job = pause_job(conn, job["id"])
        assert p_job["status"] == "paused"

        # 3. Resume job
        r_job = resume_job(conn, job["id"])
        assert r_job["status"] == "running"

        # 4. Complete job
        c_job = complete_job(
            conn, job["id"], pages_discovered=25, pages_crawled=20, documents_found=5
        )
        assert c_job["status"] == "completed"
        assert c_job["pages_discovered"] == 25
        assert c_job["pages_crawled"] == 20
        assert c_job["documents_found"] == 5
        assert c_job["completed_at"] is not None

        # 5. Create another job and fail it
        job2 = create_job(conn, source_id=src["id"])
        f_job = fail_job(conn, job2["id"], error_message="Connection timeout to host")
        assert f_job["status"] == "failed"
        assert "timeout" in f_job["error_message"]

        # 6. Create another job and cancel it
        job3 = create_job(conn, source_id=src["id"])
        x_job = cancel_job(conn, job3["id"])
        assert x_job["status"] == "cancelled"
