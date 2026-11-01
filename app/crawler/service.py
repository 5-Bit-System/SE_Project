"""Service for crawler policy enforcement, job orchestration, and execution."""

from urllib.parse import urlparse

from app.crawler.repository import (
    cancel_job,
    create_job,
    get_job,
    get_source,
    list_jobs,
    pause_job,
    resume_job,
)

# Allowed domains policy for academic crawler
ALLOWED_DOMAINS = (
    "hus.vnu.edu.vn",
    "tuyensinh.hus.vnu.edu.vn",
    "mim.hus.vnu.edu.vn",
    "vnu.edu.vn",
    "uet.vnu.edu.vn",
)


def validate_crawler_url(url: str) -> tuple[bool, str]:
    """Validate that target URL belongs to official educational allowlisted domains."""
    if not url or not isinstance(url, str):
        return False, "URL không được để trống."

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "URL không hợp lệ."

    if parsed.scheme not in ("http", "https"):
        return False, "Chỉ chấp nhận giao thức HTTP hoặc HTTPS."

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "URL thiếu tên miền (hostname)."

    # Reject localhost or internal loopbacks
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        return False, "Không được phép thu thập trên máy chủ nội bộ (localhost)."

    # Domain allowlist check
    is_allowed = any(
        hostname == domain or hostname.endswith("." + domain) for domain in ALLOWED_DOMAINS
    )
    if not is_allowed:
        return (
            False,
            f"Tên miền '{hostname}' không nằm trong danh sách được phép thu thập ({', '.join(ALLOWED_DOMAINS)}).",
        )

    return True, ""


def trigger_crawl_job(
    conn,
    source_id: str,
    created_by: str | None = None,
) -> dict:
    """Validate source and launch a new crawl job safely."""
    source = get_source(conn, source_id)
    if not source:
        raise ValueError(f"Nguồn thu thập '{source_id}' không tồn tại.")

    if not source["is_active"]:
        raise ValueError(f"Nguồn thu thập '{source['name']}' đang bị tạm dừng hoạt động.")

    # Check for active running jobs on this source to prevent duplicate starts
    running_jobs = list_jobs(conn, source_id=source_id, status="running")
    if running_jobs:
        raise ValueError(
            f"Nguồn '{source['name']}' đang có một tiến trình thu thập đang chạy (Mã: {running_jobs[0]['id']})."
        )

    job = create_job(conn, source_id=source_id, created_by=created_by)
    return job


def pause_crawl_job(conn, job_id: str) -> dict:
    job = get_job(conn, job_id)
    if not job:
        raise ValueError(f"Tiến trình '{job_id}' không tồn tại.")
    if job["status"] != "running":
        raise ValueError(
            f"Không thể tạm dừng tiến trình ở trạng thái '{job['status']}'. Chỉ áp dụng cho 'running'."
        )
    return pause_job(conn, job_id)


def resume_crawl_job(conn, job_id: str) -> dict:
    job = get_job(conn, job_id)
    if not job:
        raise ValueError(f"Tiến trình '{job_id}' không tồn tại.")
    if job["status"] != "paused":
        raise ValueError(
            f"Không thể tiếp tục tiến trình ở trạng thái '{job['status']}'. Chỉ áp dụng cho 'paused'."
        )
    return resume_job(conn, job_id)


def cancel_crawl_job(conn, job_id: str) -> dict:
    job = get_job(conn, job_id)
    if not job:
        raise ValueError(f"Tiến trình '{job_id}' không tồn tại.")
    if job["status"] in ("completed", "failed", "cancelled"):
        raise ValueError(f"Tiến trình đã kết thúc với trạng thái '{job['status']}'.")
    return cancel_job(conn, job_id)
