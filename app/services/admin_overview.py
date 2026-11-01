"""Truthful overview metrics for the HUS Admin Console.

Metrics are strictly sourced and never fabricated. If a data source is
unavailable, its status is marked 'unavailable' and its value is set to None
rather than a misleading zero.
"""
from datetime import datetime, timezone
from typing import Any, Literal
from anyio import to_thread
from pydantic import BaseModel, Field

from app.config import get_settings


class SourcedMetric(BaseModel):
    value: Any = None
    status: Literal["available", "unavailable"] = "available"
    source: str
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: dict[str, Any] | None = None


class AdminOverviewResponse(BaseModel):
    accounts_total: SourcedMetric
    programs_count: SourcedMetric
    courses_count: SourcedMetric
    catalog_status: SourcedMetric
    system_readiness: SourcedMetric


def _collect_accounts_metric() -> SourcedMetric:
    try:
        from app.auth import repository as auth_repo
        count = auth_repo.count_accounts()
        return SourcedMetric(
            value=count,
            status="available",
            source="postgres:accounts",
        )
    except Exception as err:
        return SourcedMetric(
            value=None,
            status="unavailable",
            source="postgres:accounts",
            details={"error": str(err)},
        )


def _collect_catalog_metrics() -> tuple[SourcedMetric, SourcedMetric, SourcedMetric]:
    try:
        from app.catalog import list_catalogs
        catalogs = list_catalogs()
        programs_count = len(catalogs)

        course_codes = set()
        for cat in catalogs:
            for course in cat.courses:
                course_codes.add(course.code)
        courses_count = len(course_codes)

        statuses = [cat.program.catalog_status for cat in catalogs]
        if all(s == "verified" for s in statuses) and statuses:
            verification_status = "verified"
        else:
            verification_status = "draft_unverified"

        programs_metric = SourcedMetric(
            value=programs_count,
            status="available",
            source="catalog:active",
        )
        courses_metric = SourcedMetric(
            value=courses_count,
            status="available",
            source="catalog:active",
        )
        catalog_status_metric = SourcedMetric(
            value=verification_status,
            status="available",
            source="catalog:verification_state",
            details={
                "statuses": {cat.program.program_id: cat.program.catalog_status for cat in catalogs}
            },
        )
        return programs_metric, courses_metric, catalog_status_metric
    except Exception as err:
        programs_metric = SourcedMetric(
            value=None,
            status="unavailable",
            source="catalog:active",
            details={"error": str(err)},
        )
        courses_metric = SourcedMetric(
            value=None,
            status="unavailable",
            source="catalog:active",
            details={"error": str(err)},
        )
        catalog_status_metric = SourcedMetric(
            value=None,
            status="unavailable",
            source="catalog:verification_state",
            details={"error": str(err)},
        )
        return programs_metric, courses_metric, catalog_status_metric


def _collect_readiness_metric() -> SourcedMetric:
    try:
        from app.main import check_auth_ready, check_storage_ready
        check_storage_ready()
        check_auth_ready()
        return SourcedMetric(
            value="operational",
            status="available",
            source="system:readiness_checks",
            details={"storage_backend": get_settings().storage_backend},
        )
    except Exception as err:
        return SourcedMetric(
            value="degraded",
            status="available",
            source="system:readiness_checks",
            details={"error": str(err), "storage_backend": get_settings().storage_backend},
        )


async def get_admin_overview() -> AdminOverviewResponse:
    """Collect truthful overview metrics without blocking the async event loop."""
    accounts_metric = await to_thread.run_sync(_collect_accounts_metric)
    programs_metric, courses_metric, catalog_status_metric = await to_thread.run_sync(
        _collect_catalog_metrics
    )
    readiness_metric = await to_thread.run_sync(_collect_readiness_metric)

    return AdminOverviewResponse(
        accounts_total=accounts_metric,
        programs_count=programs_metric,
        courses_count=courses_metric,
        catalog_status=catalog_status_metric,
        system_readiness=readiness_metric,
    )
