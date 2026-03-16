"""
Main router configuration for HotelAgent API.
"""

from fastapi import APIRouter

from .routes.auth.auth import password_router, router as auth_router
from .routes.auth.users import router as users_router, public_users_router
from .routes.staff.role import public_role_router, router as role_router
from .routes.subscriptions import router as subscription_router
from .routes.dashboard import router as dashboard_router
from .routes.notifications import router as notification_router
from .routes.hotel.branch import public_onboarding_router, branch_management_router
from .routes.hotel.floor import router as floor_router
from .routes.hotel.section import section_router
from .routes.hotel.table import table_router
 
# Master router for public-facing APIs
public_api_router = APIRouter()
public_api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
public_api_router.include_router(
    public_users_router, prefix="/auth/users", tags=["User Registration"]
)
public_api_router.include_router(
    users_router, prefix="/auth/users", tags=["User Management"]
)
public_api_router.include_router(
    public_role_router, prefix="/staff", tags=["Staff Roles"]
)
public_api_router.include_router(
    password_router, prefix="/auth", tags=["Password Management"]
)
public_api_router.include_router(
    subscription_router, prefix="/subscriptions", tags=["Subscription Management"]
)
 
# Master router for internal/admin APIs
internal_api_router = APIRouter()
internal_api_router.include_router(
    role_router, prefix="/staff", tags=["Staff Roles"]
)
internal_api_router.include_router(
    subscription_router, prefix="/subscriptions", tags=["Subscription Management"]
)
internal_api_router.include_router(
    dashboard_router, prefix="/dashboard", tags=["Dashboard"]
)
internal_api_router.include_router(
    notification_router, prefix="/notifications", tags=["Notifications"]
)
internal_api_router.include_router(
    branch_management_router, prefix="/hotels", tags=["Branch Management"]
)
internal_api_router.include_router(
    floor_router, prefix="/hotels", tags=["Floor Management"]
)
internal_api_router.include_router(
    table_router, prefix="/hotels", tags=["Table Management"]
)
public_api_router.include_router(
    public_onboarding_router, prefix="/hotels", tags=["Hotel Onboarding"]
)