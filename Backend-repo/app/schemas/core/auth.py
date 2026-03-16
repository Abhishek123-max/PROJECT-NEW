"""
Authentication schemas for HotelAgent API.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUser(BaseModel):
    """Current user schema."""
    id: int
    username: str
    role: Optional[str] = None
    hotel_id: Optional[int] = None
    branch_id: Optional[int] = None
    floor_id: Optional[int] = None
    section_id: Optional[int] = None
    is_active: bool
    feature_toggles: Dict[str, Any] = {}
    permissions: Dict[str, Any] = {}
    last_login: Optional[datetime] = None
    created_at: datetime


class LoginResponse(BaseModel):
    """Login response schema."""
    success: bool
    message: str
    data: TokenResponse
    user: CurrentUser
    reset_required: bool
    onboarding_completed: bool


class TokenRefresh(BaseModel):
    """Token refresh request schema."""
    refresh_token: str


class LogoutResponse(BaseModel):
    """Logout response schema."""
    success: bool
    message: str


class UserInfoResponse(BaseModel):
    """User info response schema."""
    success: bool
    message: str
    data: CurrentUser


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema."""
    username: str


class ForgotPasswordResponse(BaseModel):
    """Response for the forgot password request, including token for testing."""
    message: str
    username: Optional[str] = None
    reset_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    """Reset password request schema."""
    username: str
    onetime_password: str
    new_password: str
    reset_token: str


class ResetPasswordForgotRequest(BaseModel):
    """Reset password via forgot password flow schema."""
    username: str
    token: str
    new_password: str

class ResetPasswordAccessTokenRequest(BaseModel):
    username:str
    new_password:str


class VerifyTokenResponse(BaseModel):
    """Response for token verification."""
    is_valid: bool
    message: str