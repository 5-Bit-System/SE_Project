"""Unit tests for truthful admin overview metrics service."""

import pytest
from unittest.mock import patch

from app.services.admin_overview import get_admin_overview, AdminOverviewResponse


@pytest.mark.anyio
async def test_admin_overview_success():
    overview = await get_admin_overview()
    assert isinstance(overview, AdminOverviewResponse)

    # 1. Accounts metric
    assert overview.accounts_total.source == "postgres:accounts"
    if overview.accounts_total.status == "available":
        assert isinstance(overview.accounts_total.value, int)
        assert overview.accounts_total.value >= 0

    # 2. Programs and courses
    assert overview.programs_count.source == "catalog:active"
    if overview.programs_count.status == "available":
        assert isinstance(overview.programs_count.value, int)
        assert overview.programs_count.value >= 0
        assert isinstance(overview.courses_count.value, int)
        assert overview.courses_count.value >= 0
        assert overview.catalog_status.value in {"draft_unverified", "verified"}

    # 3. System readiness
    assert overview.system_readiness.source == "system:readiness_checks"
    assert overview.system_readiness.value in {"operational", "degraded"}


@pytest.mark.anyio
async def test_admin_overview_accounts_unavailable_does_not_report_zero():
    """When the account repository fails, the metric must be unavailable with None, not 0."""
    with patch("app.auth.repository.count_accounts", side_effect=RuntimeError("connection refused")):
        overview = await get_admin_overview()

        assert overview.accounts_total.status == "unavailable"
        assert overview.accounts_total.value is None
        assert "connection refused" in overview.accounts_total.details.get("error", "")


@pytest.mark.anyio
async def test_admin_overview_catalog_unavailable_does_not_report_zero():
    """When catalog loading fails, catalog metrics must be unavailable with None, not 0."""
    with patch("app.catalog.list_catalogs", side_effect=RuntimeError("catalog missing")):
        overview = await get_admin_overview()

        assert overview.programs_count.status == "unavailable"
        assert overview.programs_count.value is None
        assert overview.courses_count.status == "unavailable"
        assert overview.courses_count.value is None
        assert overview.catalog_status.status == "unavailable"
        assert overview.catalog_status.value is None


@pytest.mark.anyio
async def test_admin_overview_readiness_degraded_when_check_fails():
    """When a readiness check fails, system_readiness reports degraded, not a crash."""
    with patch("app.main.check_storage_ready", side_effect=Exception("storage corrupted")):
        overview = await get_admin_overview()

        assert overview.system_readiness.status == "available"
        assert overview.system_readiness.value == "degraded"
        assert "storage corrupted" in overview.system_readiness.details.get("error", "")
