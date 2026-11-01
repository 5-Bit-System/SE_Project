"""Unit tests for crawler service, URL policy enforcement, and job transitions."""

from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine

from app.crawler.repository import create_source, toggle_source
from app.crawler.service import (
    cancel_crawl_job,
    pause_crawl_job,
    resume_crawl_job,
    trigger_crawl_job,
    validate_crawler_url,
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


def test_url_policy_validation():
    # Disallowed / Malformed
    assert not validate_crawler_url("")[0]
    assert not validate_crawler_url("ftp://hus.vnu.edu.vn")[0]
    assert not validate_crawler_url("http://localhost:8000/steal")[0]
    assert not validate_crawler_url("http://127.0.0.1:5432")[0]
    assert not validate_crawler_url("https://malicious-domain.com/phishing")[0]
    assert not validate_crawler_url("https://google.com")[0]

    # Allowed educational domains
    ok1, _ = validate_crawler_url("https://hus.vnu.edu.vn/dao-tao/dai-hoc")
    assert ok1 is True
    ok2, _ = validate_crawler_url("https://tuyensinh.hus.vnu.edu.vn/dai-hoc/nganh-hoc")
    assert ok2 is True
    ok3, _ = validate_crawler_url("https://mim.hus.vnu.edu.vn/vi/cacctrdaotao")
    assert ok3 is True


def test_crawler_job_orchestration(db_engine):
    with db_engine.begin() as conn:
        src = create_source(
            conn,
            name="Policy Test Source",
            base_url="https://hus.vnu.edu.vn/policy-test",
        )

        # 1. Trigger job
        job = trigger_crawl_job(conn, source_id=src["id"])
        assert job["status"] == "running"

        # 2. Prevent duplicate concurrent running job
        with pytest.raises(ValueError, match="đang có một tiến trình"):
            trigger_crawl_job(conn, source_id=src["id"])

        # 3. Pause job
        p_job = pause_crawl_job(conn, job["id"])
        assert p_job["status"] == "paused"

        # Pausing already paused job raises error
        with pytest.raises(ValueError, match="Không thể tạm dừng"):
            pause_crawl_job(conn, job["id"])

        # 4. Resume job
        r_job = resume_crawl_job(conn, job["id"])
        assert r_job["status"] == "running"

        # 5. Cancel job
        c_job = cancel_crawl_job(conn, job["id"])
        assert c_job["status"] == "cancelled"

        # 6. Triggering on inactive source fails
        toggle_source(conn, src["id"], is_active=False)
        with pytest.raises(ValueError, match="đang bị tạm dừng"):
            trigger_crawl_job(conn, source_id=src["id"])
