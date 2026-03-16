"""
Pydantic schemas for Notifications.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class NotificationBase(BaseModel):
    type: str
    hotel_id: Optional[int] = None
    details: Dict[str, Any]


class NotificationCreate(NotificationBase):
    pass


class NotificationOut(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationList(BaseModel):
    """Schema for a list of notifications."""
    notifications: List[NotificationOut]
    total: int
    page: int
    per_page: int


class NotificationListResponse(BaseModel):
    """Response schema for a list of notifications."""
    success: bool = True
    message: str = "Notifications retrieved successfully."
    data: NotificationList