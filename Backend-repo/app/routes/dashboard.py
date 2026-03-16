"""
API Router for the Product Admin Dashboard.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_product_admin
from app.models.core.user import User
from app.schemas.core.dashboard import DashboardSummaryResponse
from app.services import dashboard_service

router = APIRouter()


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get Product Admin Dashboard Summary",
    description="Provides a comprehensive dashboard for Product Admins with system-wide insights."
)
async def get_dashboard_summary(
    start_date: Optional[datetime] = Query(None, description="Filter data from this date (e.g., for revenue or onboarding)."),
    end_date: Optional[datetime] = Query(None, description="Filter data up to this date."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_product_admin)
):
    """
    Retrieve aggregated data for the Product Admin dashboard.

    - **total_hotels**: Count of all hotels (tenants).
    - **total_branches**: Count of all branches across all hotels.
    - **subscription_stats**: Breakdown of active vs. inactive/expired subscriptions.
    - **expiring_subscriptions**: List of subscriptions expiring within the next 30 days.
    - **revenue_report**: Total revenue from online and offline payments.
    - **new_hotels**: List of hotels onboarded in the last 30 days (or date range).
    - **geographical_data**: Location data for all hotels with coordinates.
    """
    summary_data = await dashboard_service.get_dashboard_summary(
        db=db, start_date=start_date, end_date=end_date
    )
    return DashboardSummaryResponse(
        data=summary_data
    )