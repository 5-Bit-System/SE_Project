"""Unit tests for operational metrics and health monitoring service."""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.operational_metrics import (
    classify_route_group,
    get_operational_health,
    metrics_recorder,
)


@pytest.fixture(autouse=True)
def reset_recorder():
    metrics_recorder.clear()
    yield
    metrics_recorder.clear()


def test_classify_route_group():
    assert classify_route_group("/academic/documents") == "academic"
    assert classify_route_group("/programs/mat-clc") == "academic"
    assert classify_route_group("/portal/session") == "portal"
    assert classify_route_group("/auth/login") == "auth"
    assert classify_route_group("/me/profile") == "auth"
    assert classify_route_group("/recommendations") == "consultation"
    assert classify_route_group("/recommendations/what-if") == "consultation"
    assert classify_route_group("/eligibility") == "consultation"
    assert classify_route_group("/advisor/chat") == "consultation"
    assert classify_route_group("/me/semester-plans") == "consultation"
    assert classify_route_group("/admin/overview") == "admin"
    assert classify_route_group("/catalog-revisions/rev123") == "admin"
    assert classify_route_group("/unknown/path") == "other"


def test_data_minimization_path_sanitization():
    # Verify that query params, student IDs, tokens in paths are stripped
    sanitized = metrics_recorder.sanitize_path("/portal/grades?student_id=23001939&token=secret123")
    assert "23001939" not in sanitized
    assert "secret123" not in sanitized
    assert sanitized == "/portal/grades"


def test_empty_periods_and_missing_instrumentation():
    # When no metrics exist, health response must truthfully indicate unavailable
    health = get_operational_health(window="24h")
    assert health["window"] == "24h"
    assert health["sample_count"] == 0
    assert health["overall_health"]["status"] == "unavailable"
    assert health["overall_health"]["total_requests"] is None

    # Route groups should be unavailable
    for group_name, group_data in health["route_groups"].items():
        assert group_data["status"] == "unavailable"
        assert group_data["total_requests"] is None

    # Consultation health should be unavailable
    assert health["consultation_health"]["status"] == "unavailable"
    assert health["consultation_health"]["total_consultations"] is None

    # Feedback should be unavailable
    assert health["feedback_signals"]["status"] == "unavailable"
    assert health["feedback_signals"]["total_feedbacks"] is None


def test_recorded_metrics_and_percentiles():
    now = datetime.now(timezone.utc)

    # Record 10 requests with varying latencies
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    for lat in latencies:
        metrics_recorder.record_request(
            route_group="academic",
            path="/academic/documents",
            method="GET",
            status_code=200,
            duration_ms=lat,
            timestamp=now,
        )

    # Record 1 error in portal
    metrics_recorder.record_request(
        route_group="portal",
        path="/portal/session",
        method="POST",
        status_code=500,
        duration_ms=120.0,
        timestamp=now,
    )

    health = get_operational_health(window="1h")
    assert health["sample_count"] == 11
    assert health["overall_health"]["status"] == "available"
    assert health["overall_health"]["total_requests"] == 11
    assert health["overall_health"]["error_rate_pct"] == pytest.approx(1 / 11 * 100, rel=1e-2)

    academic = health["route_groups"]["academic"]
    assert academic["status"] == "available"
    assert academic["total_requests"] == 10
    assert academic["success_rate_pct"] == 100.0
    assert academic["error_rate_pct"] == 0.0
    # p50 of 10..100: median is 55.0
    assert academic["p50_latency_ms"] == pytest.approx(55.0, abs=1.0)
    # p95
    assert academic["p95_latency_ms"] >= 90.0


def test_time_window_filtering():
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(hours=2)

    # 1 recent request (within 1h)
    metrics_recorder.record_request(
        route_group="admin",
        path="/admin/overview",
        method="GET",
        status_code=200,
        duration_ms=15.0,
        timestamp=now,
    )

    # 1 older request (2h ago)
    metrics_recorder.record_request(
        route_group="admin",
        path="/admin/overview",
        method="GET",
        status_code=200,
        duration_ms=25.0,
        timestamp=old_time,
    )

    # Window 1h should only see the recent one
    health_1h = get_operational_health(window="1h")
    assert health_1h["sample_count"] == 1

    # Window 24h should see both
    health_24h = get_operational_health(window="24h")
    assert health_24h["sample_count"] == 2


def test_consultation_events_and_reasons():
    now = datetime.now(timezone.utc)

    metrics_recorder.record_consultation(
        event_type="recommendation",
        success=True,
        duration_ms=45.0,
        timestamp=now,
    )
    metrics_recorder.record_consultation(
        event_type="recommendation",
        success=False,
        duration_ms=12.0,
        failure_reason="catalog_unverified",
        timestamp=now,
    )
    metrics_recorder.record_consultation(
        event_type="eligibility",
        success=False,
        duration_ms=10.0,
        failure_reason="catalog_unverified",
        timestamp=now,
    )

    health = get_operational_health(window="24h")
    cons = health["consultation_health"]
    assert cons["status"] == "available"
    assert cons["total_consultations"] == 3
    assert cons["successful_consultations"] == 1
    assert cons["failed_consultations"] == 2
    assert cons["failure_rate_pct"] == pytest.approx(66.67, rel=1e-2)
    assert len(cons["top_failure_reasons"]) == 1
    assert cons["top_failure_reasons"][0]["reason"] == "catalog_unverified"
    assert cons["top_failure_reasons"][0]["count"] == 2


def test_feedback_signals():
    now = datetime.now(timezone.utc)
    metrics_recorder.record_feedback(
        rating=5,
        category="recommendation",
        is_helpful=True,
        timestamp=now,
    )
    metrics_recorder.record_feedback(
        rating=1,
        category="advisor",
        is_helpful=False,
        timestamp=now,
    )

    health = get_operational_health(window="24h")
    fb = health["feedback_signals"]
    assert fb["status"] == "available"
    assert fb["total_feedbacks"] == 2
    assert fb["positive_feedbacks"] == 1
    assert fb["positive_rate_pct"] == 50.0
