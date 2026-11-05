"""Truthful operational metrics and service health recorder.

Tracks bounded execution telemetry: request counts, latencies, error rates by route group,
consultation failures, and user quality signals.
Never collects or retains student transcripts, grade details, passwords, or tokens.
Truthfully returns status 'unavailable' and value None when data is not recorded.
"""

import inspect
import math
import re
import threading
import time
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any


@dataclass(slots=True)
class RequestMetric:
    route_group: str
    path: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: datetime


@dataclass(slots=True)
class ConsultationEvent:
    event_type: str
    success: bool
    duration_ms: float
    failure_reason: str | None
    timestamp: datetime


@dataclass(slots=True)
class FeedbackSignal:
    rating: int
    category: str
    is_helpful: bool
    timestamp: datetime


@dataclass(slots=True)
class RecommendationSignal:
    course_codes: tuple[str, ...]
    scores: tuple[float, ...]
    reason_categories: tuple[str, ...]
    timestamp: datetime


def _fit_category(reason: str) -> str:
    if reason.startswith('Tên hoặc metadata môn có chứa chủ đề'):
        return 'topic'
    if reason.startswith('Metadata môn khớp định hướng nghề nghiệp'):
        return 'career'
    if reason.startswith('Metadata môn khớp '):
        return 'metadata'
    if reason.startswith('Môn có loại '):
        return 'course_type'
    if reason.startswith('Môn có một phần từ khóa'):
        return 'keyword'
    if reason.startswith('Catalog hiện chưa có metadata đủ'):
        return 'insufficient_metadata'
    return 'other'


ROUTE_GROUP_PREFIXES = [
    ("academic", ("/academic", "/programs")),
    ("portal", ("/portal",)),
    ("auth", ("/auth", "/me/profile", "/me/account")),
    ("consultation", ("/recommendations", "/eligibility", "/advisor", "/me/semester-plans", "/transcript/summary")),
    ("admin", ("/admin", "/catalog-revisions")),
]


def classify_route_group(path: str) -> str:
    """Classify request path into a bounded logical group."""
    clean_path = path.split("?")[0].rstrip("/")
    if not clean_path:
        return "other"
    for group, prefixes in ROUTE_GROUP_PREFIXES:
        for prefix in prefixes:
            if clean_path == prefix or clean_path.startswith(prefix + "/"):
                return group
    return "other"


def _percentile(values: list[float], pct: float) -> float:
    """Calculate percentile from a sorted list of numbers."""
    if not values:
        return 0.0
    k = (len(values) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    d0 = values[int(f)] * (c - k)
    d1 = values[int(c)] * (k - f)
    return d0 + d1


class OperationalMetricsRecorder:
    """Thread-safe, memory-bounded operational metrics telemetry recorder."""

    def __init__(self, max_requests: int = 20000, max_consultations: int = 5000, max_feedbacks: int = 2000):
        self._lock = threading.Lock()
        self._requests: deque[RequestMetric] = deque(maxlen=max_requests)
        self._consultations: deque[ConsultationEvent] = deque(maxlen=max_consultations)
        self._feedbacks: deque[FeedbackSignal] = deque(maxlen=max_feedbacks)
        self._recommendations: deque[RecommendationSignal] = deque(maxlen=max_consultations)
        self.started_at = datetime.now(timezone.utc)

    def clear(self) -> None:
        """Clear all in-memory buffers (primarily for tests)."""
        with self._lock:
            self._requests.clear()
            self._consultations.clear()
            self._feedbacks.clear()
            self._recommendations.clear()

    @staticmethod
    def sanitize_path(raw_path: str) -> str:
        """Strip query parameters, fragments, and mask dynamic ID segments to protect privacy."""
        clean = raw_path.split("?")[0].split("#")[0]
        # Mask UUIDs or long hex strings
        clean = re.sub(r"/[a-f0-9-]{16,40}", "/{id}", clean)
        # Mask numeric IDs
        clean = re.sub(r"/\d+", "/{id}", clean)
        return clean

    def record_request(
        self,
        route_group: str,
        path: str,
        method: str,
        status_code: int,
        duration_ms: float,
        timestamp: datetime | None = None,
    ) -> None:
        """Record an HTTP request metric safely without sensitive parameters."""
        ts = timestamp or datetime.now(timezone.utc)
        safe_path = self.sanitize_path(path)
        metric = RequestMetric(
            route_group=route_group,
            path=safe_path,
            method=method.upper(),
            status_code=status_code,
            duration_ms=max(0.0, float(duration_ms)),
            timestamp=ts,
        )
        with self._lock:
            self._requests.append(metric)

    def record_consultation(
        self,
        event_type: str,
        success: bool,
        duration_ms: float,
        failure_reason: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Record a consultation/recommendation engine execution event."""
        ts = timestamp or datetime.now(timezone.utc)
        event = ConsultationEvent(
            event_type=event_type,
            success=success,
            duration_ms=max(0.0, float(duration_ms)),
            failure_reason=failure_reason[:100] if failure_reason else None,
            timestamp=ts,
        )
        with self._lock:
            self._consultations.append(event)

    def record_feedback(
        self,
        rating: int,
        category: str,
        is_helpful: bool,
        timestamp: datetime | None = None,
    ) -> None:
        """Record an authenticated user quality feedback signal."""
        ts = timestamp or datetime.now(timezone.utc)
        signal = FeedbackSignal(
            rating=max(1, min(5, int(rating))),
            category=category[:50],
            is_helpful=bool(is_helpful),
            timestamp=ts,
        )
        with self._lock:
            self._feedbacks.append(signal)

    def record_recommendation(
        self, courses: list[tuple[str, float]], fit_reasons: list[str] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Keep bounded course codes and scores, never identity or preference text."""
        valid = [(index, code, float(score)) for index, (code, score) in enumerate(courses[:20])
                 if re.fullmatch(r'[A-Za-z0-9_-]{2,30}', code) and math.isfinite(float(score))
                 and 0 <= float(score) <= 1]
        reasons = fit_reasons or []
        event = RecommendationSignal(tuple(code for _, code, _ in valid),
                                     tuple(score for _, _, score in valid),
                                     tuple(_fit_category(reasons[index]) if index < len(reasons) else 'other'
                                           for index, _, _ in valid),
                                     timestamp or datetime.now(timezone.utc))
        with self._lock:
            self._recommendations.append(event)

    def get_health(self, window: str = "24h") -> dict[str, Any]:
        """Aggregate truthful metrics for the specified sliding window."""
        now = datetime.now(timezone.utc)
        if window == "1h":
            cutoff = now - timedelta(hours=1)
        elif window == "7d":
            cutoff = now - timedelta(days=7)
        elif window == "all":
            cutoff = datetime.min.replace(tzinfo=timezone.utc)
        else:
            window = "24h"
            cutoff = now - timedelta(hours=24)

        with self._lock:
            requests = [r for r in self._requests if r.timestamp >= cutoff]
            consultations = [c for c in self._consultations if c.timestamp >= cutoff]
            feedbacks = [f for f in self._feedbacks if f.timestamp >= cutoff]
            recommendations = [r for r in self._recommendations if r.timestamp >= cutoff]

        # 1. Overall & Route Groups
        total_requests = len(requests)
        groups = ["academic", "portal", "auth", "consultation", "admin", "other"]
        grouped_requests: dict[str, list[RequestMetric]] = {g: [] for g in groups}
        for r in requests:
            grp = r.route_group if r.route_group in grouped_requests else "other"
            grouped_requests[grp].append(r)

        route_groups_data: dict[str, Any] = {}
        for grp in groups:
            items = grouped_requests[grp]
            if not items:
                route_groups_data[grp] = {
                    "status": "unavailable",
                    "total_requests": None,
                    "success_rate_pct": None,
                    "error_rate_pct": None,
                    "server_error_rate_pct": None,
                    "p50_latency_ms": None,
                    "p95_latency_ms": None,
                }
            else:
                n = len(items)
                success_count = sum(1 for x in items if 200 <= x.status_code < 300)
                client_error_count = sum(1 for x in items if 400 <= x.status_code < 500)
                server_error_count = sum(1 for x in items if x.status_code >= 500)
                error_count = client_error_count + server_error_count
                durations = sorted(x.duration_ms for x in items)

                route_groups_data[grp] = {
                    "status": "available",
                    "total_requests": n,
                    "success_rate_pct": round((success_count / n) * 100, 1),
                    "error_rate_pct": round((error_count / n) * 100, 1),
                    "server_error_rate_pct": round((server_error_count / n) * 100, 1),
                    "p50_latency_ms": round(_percentile(durations, 50), 1),
                    "p95_latency_ms": round(_percentile(durations, 95), 1),
                }

        # Overall summary
        if total_requests == 0:
            overall_health = {
                "status": "unavailable",
                "total_requests": None,
                "success_rate_pct": None,
                "error_rate_pct": None,
                "server_error_rate_pct": None,
                "p50_latency_ms": None,
                "p95_latency_ms": None,
            }
        else:
            success_count = sum(1 for x in requests if 200 <= x.status_code < 300)
            server_error_count = sum(1 for x in requests if x.status_code >= 500)
            error_count = sum(1 for x in requests if x.status_code >= 400)
            all_durations = sorted(x.duration_ms for x in requests)
            overall_health = {
                "status": "available",
                "total_requests": total_requests,
                "success_rate_pct": round((success_count / total_requests) * 100, 1),
                "error_rate_pct": round((error_count / total_requests) * 100, 1),
                "server_error_rate_pct": round((server_error_count / total_requests) * 100, 1),
                "p50_latency_ms": round(_percentile(all_durations, 50), 1),
                "p95_latency_ms": round(_percentile(all_durations, 95), 1),
            }

        # 2. Consultation Health
        if not consultations:
            consultation_health = {
                "status": "unavailable",
                "total_consultations": None,
                "successful_consultations": None,
                "failed_consultations": None,
                "failure_rate_pct": None,
                "top_failure_reasons": [],
                "avg_duration_ms": None,
                "recommendation_total": None,
                "recommendation_success_rate_pct": None,
            }
        else:
            cons_n = len(consultations)
            cons_success = sum(1 for c in consultations if c.success)
            cons_failed = cons_n - cons_success
            reasons = Counter(c.failure_reason for c in consultations if c.failure_reason)
            top_reasons = [{"reason": r, "count": count} for r, count in reasons.most_common(5)]
            avg_dur = sum(c.duration_ms for c in consultations) / cons_n
            recommendation_events = [c for c in consultations if c.event_type == 'recommendation']

            consultation_health = {
                "status": "available",
                "total_consultations": cons_n,
                "successful_consultations": cons_success,
                "failed_consultations": cons_failed,
                "failure_rate_pct": round((cons_failed / cons_n) * 100, 1),
                "top_failure_reasons": top_reasons,
                "avg_duration_ms": round(avg_dur, 1),
                "recommendation_total": len(recommendation_events),
                "recommendation_success_rate_pct": (
                    round(sum(c.success for c in recommendation_events) / len(recommendation_events) * 100, 1)
                    if recommendation_events else None
                ),
            }

        # 3. User Feedback Signals
        if not feedbacks:
            feedback_signals = {
                "status": "unavailable",
                "total_feedbacks": None,
                "positive_feedbacks": None,
                "positive_rate_pct": None,
                "average_rating": None,
                "negative_count": None,
                "by_category": [],
            }
        else:
            fb_n = len(feedbacks)
            fb_pos = sum(1 for f in feedbacks if f.is_helpful)
            feedback_signals = {
                "status": "available",
                "total_feedbacks": fb_n,
                "positive_feedbacks": fb_pos,
                "positive_rate_pct": round((fb_pos / fb_n) * 100, 1),
                "average_rating": round(sum(f.rating for f in feedbacks) / fb_n, 1),
                "negative_count": sum(f.rating <= 2 for f in feedbacks),
                "by_category": [{"category": category, "count": count}
                                for category, count in sorted(Counter(f.category for f in feedbacks).items())],
            }

        codes = Counter(code for event in recommendations for code in event.course_codes)
        scores = [score for event in recommendations for score in event.scores]
        reason_counts = Counter(category for event in recommendations
                                for category in event.reason_categories)
        recommendation_insights = {
            "status": "available" if recommendations else "unavailable",
            "total_runs": len(recommendations) if recommendations else None,
            "average_fit_pct": round(sum(scores) / len(scores) * 100, 1) if scores else None,
            "top_courses": [{"code": code, "count": count} for code, count in codes.most_common(8)],
            "reason_categories": [{"category": category, "count": count}
                                  for category, count in reason_counts.most_common()],
        }

        return {
            "window": window,
            "window_start": cutoff.isoformat(),
            "window_end": now.isoformat(),
            "sample_count": total_requests + len(consultations) + len(feedbacks),
            "source": "runtime:operational_metrics",
            "scope": "current_process",
            "started_at": self.started_at.isoformat(),
            "note": "Số liệu giới hạn trong phiên chạy hiện tại, được đặt lại khi khởi động ứng dụng.",
            "overall_health": overall_health,
            "route_groups": route_groups_data,
            "consultation_health": consultation_health,
            "feedback_signals": feedback_signals,
            "recommendation_insights": recommendation_insights,
        }


metrics_recorder = OperationalMetricsRecorder()


def get_operational_health(window: str = "24h") -> dict[str, Any]:
    """Helper entry point for retrieving operational health metrics."""
    return metrics_recorder.get_health(window=window)


def measured_consultation(kind):
    def decorate(function):
        @wraps(function)
        async def measured(*args, **kwargs):
            started = time.perf_counter()
            try:
                result = await function(*args, **kwargs)
            except Exception as exc:
                metrics_recorder.record_consultation(kind, False, (time.perf_counter()-started)*1000,
                    failure_reason=f'HTTP_{exc.status_code}' if hasattr(exc, 'status_code') else type(exc).__name__)
                raise
            metrics_recorder.record_consultation(kind, True, (time.perf_counter()-started)*1000)
            return result
        measured.__signature__ = inspect.signature(function, eval_str=True)
        return measured
    return decorate
