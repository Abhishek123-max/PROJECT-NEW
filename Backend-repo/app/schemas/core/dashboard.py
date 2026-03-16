"""
Pydantic schemas for the Product Admin Dashboard.

These models define the data structures for the dashboard summary API endpoint,
ensuring type safety and clear API contracts.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SubscriptionStat(BaseModel):
    """Schema for subscription statistics."""
    active: int
    inactive: int


class ExpiringSubscription(BaseModel):
    """Schema for an individual expiring subscription."""
    subscription_id: int
    hotel_id: int
    hotel_name: str
    subscription_end_date: datetime


class RevenueReport(BaseModel):
    """Schema for the revenue report."""
    online_payments: float
    offline_payments: float
    total_revenue: float


class NewHotelInfo(BaseModel):
    """Schema for a newly onboarded hotel."""
    hotel_id: int
    hotel_name: str
    onboarding_date: datetime


class GeographicalData(BaseModel):
    """Schema for hotel geographical location."""
    hotel_id: int
    hotel_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DashboardSummaryData(BaseModel):
    """The data payload for the dashboard summary endpoint."""
    total_hotels: int
    total_branches: int
    subscription_stats: SubscriptionStat
    expiring_subscriptions: List[ExpiringSubscription]
    revenue_report: RevenueReport
    new_hotels: List[NewHotelInfo]
    geographical_data: List[GeographicalData]


class DashboardSummaryResponse(BaseModel):
    """The main response schema for the dashboard summary endpoint."""
    success: bool = True
    message: str = "Dashboard summary retrieved successfully."
    data: DashboardSummaryData