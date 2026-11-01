"""Tests for admin crawler sources configuration and jobs lifecycle API."""

from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    config = dotenv_values(ENV_PATH)
    url = config.get("DATABASE_URL")
    if url:
        eng = create_engine(url)
        monkeypatch.setattr("app.api.admin.engine", lambda: eng)


def test_admin_crawler_sources_and_jobs_api(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    # 1. Get Sources (seeds defaults)
    resp = verified_client.get("/admin/crawler/sources")
    assert resp.status_code == 200
    sources = resp.json()
    assert len(sources) >= 3
    main_src = [s for s in sources if s["id"] == "src_hus_main"][0]
    assert "Cổng thông tin đào tạo" in main_src["name"]

    # 2. Test URL allowlist policy rejection
    bad_resp = verified_client.post(
        "/admin/crawler/sources",
        json={"name": "Attacker Source", "base_url": "http://127.0.0.1:8000/internal"},
    )
    assert bad_resp.status_code == 400
    assert (
        "nội bộ" in bad_resp.json()["detail"]
        or "không nằm trong danh sách" in bad_resp.json()["detail"]
    )

    # 3. Create Valid Source
    create_resp = verified_client.post(
        "/admin/crawler/sources",
        json={
            "name": "Tuyển sinh Sau đại học HUS",
            "base_url": "https://tuyensinh.hus.vnu.edu.vn/sau-dai-hoc",
            "schedule": "0 4 * * 0",
            "depth_limit": 2,
        },
    )
    assert create_resp.status_code == 200
    new_src = create_resp.json()
    src_id = new_src["id"]
    assert new_src["name"] == "Tuyển sinh Sau đại học HUS"

    # 4. Trigger Crawl Job
    job_resp = verified_client.post("/admin/crawler/jobs", json={"source_id": src_id})
    assert job_resp.status_code == 200
    job = job_resp.json()
    job_id = job["id"]
    assert job["status"] == "running"

    # Duplicate trigger on active running job raises 400
    dup_resp = verified_client.post("/admin/crawler/jobs", json={"source_id": src_id})
    assert dup_resp.status_code == 400
    assert "đang có một tiến trình" in dup_resp.json()["detail"]

    # 5. Pause Job
    pause_resp = verified_client.post(f"/admin/crawler/jobs/{job_id}/pause")
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "paused"

    # 6. Resume Job
    resume_resp = verified_client.post(f"/admin/crawler/jobs/{job_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "running"

    # 7. Cancel Job
    cancel_resp = verified_client.post(f"/admin/crawler/jobs/{job_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    # 8. List Jobs
    list_jobs_resp = verified_client.get(f"/admin/crawler/jobs?source_id={src_id}")
    assert list_jobs_resp.status_code == 200
    jobs_data = list_jobs_resp.json()
    assert len(jobs_data) >= 1
    assert jobs_data[0]["id"] == job_id
