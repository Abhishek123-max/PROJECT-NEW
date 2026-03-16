"""
Feature management schemas for HotelAgent API.
"""

from typing import Dict, Any, List
from pydantic import BaseModel


class UserFeaturesResponse(BaseModel):
    """User features response schema."""
    success: bool
    message: str
    data: Dict[str, bool]


class UpdateRoleFeaturesRequest(BaseModel):
    """Update role features request schema."""
    features: Dict[str, bool]


class UpdateRoleFeaturesResponse(BaseModel):
    """Update role features response schema."""
    success: bool
    message: str
    data: Dict[str, bool]
    role: str


class RoleFeaturesResponse(BaseModel):
    """Role features response schema."""
    success: bool
    message: str
    data: Dict[str, bool]
    role: str


class AllRoleFeaturesResponse(BaseModel):
    """All role features response schema."""
    success: bool
    message: str
    data: Dict[str, Dict[str, bool]]


class UpdateUserFeaturesRequest(BaseModel):
    """Update user features request schema."""
    features: Dict[str, bool]


class UpdateUserFeaturesResponse(BaseModel):
    """Update user features response schema."""
    success: bool
    message: str
    data: Dict[str, bool]
    user_id: int


class FeatureValidationRequest(BaseModel):
    """Feature validation request schema."""
    feature: str


class FeatureValidationResponse(BaseModel):
    """Feature validation response schema."""
    success: bool
    message: str
    data: Dict[str, Any]


class SubscriptionFeaturesResponse(BaseModel):
    """Subscription features response schema."""
    success: bool
    message: str
    data: Dict[str, bool]
    subscription_plan: str


class AllSubscriptionFeaturesResponse(BaseModel):
    """All subscription features response schema."""
    success: bool
    message: str
    data: Dict[str, Dict[str, bool]]


class FeatureListResponse(BaseModel):
    """Feature list response schema."""
    success: bool
    message: str
    data: List[Dict[str, str]]