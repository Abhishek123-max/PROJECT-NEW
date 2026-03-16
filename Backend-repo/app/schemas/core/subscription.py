"""Pydantic schemas for Subscription management."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SubscriptionBase(BaseModel):
    """Base schema for subscription."""
    hotel_id: int
    plan_type: str
    onboarding_mode: str
    payment_amount: float
    payment_method: str
    payment_date: datetime
    payment_status: str
    subscription_start_date: datetime
    subscription_end_date: datetime


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription."""
    pass


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""
    plan_type: Optional[str] = None
    payment_amount: Optional[float] = None
    payment_method: Optional[str] = None
    payment_date: Optional[datetime] = None
    payment_status: Optional[str] = None
    subscription_end_date: Optional[datetime] = None
    status: Optional[str] = None


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response."""
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubscriptionList(BaseModel):
    """Schema for a list of subscriptions."""
    subscriptions: List[SubscriptionResponse]
    total: int
    page: int
    per_page: int


class SubscriptionListResponse(BaseModel):
    """Response schema for a list of subscriptions."""
    success: bool
    message: str
    data: SubscriptionList