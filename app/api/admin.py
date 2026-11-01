"""Admin console API endpoints with strict role-based authorization."""

from fastapi import APIRouter, HTTPException, Request

from app.auth.dependencies import require_account
from app.services.admin_overview import AdminOverviewResponse, get_admin_overview

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverviewResponse)
async def overview(request: Request) -> AdminOverviewResponse:
    """Return truthful overview metrics for administrators only."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")
    return await get_admin_overview()
