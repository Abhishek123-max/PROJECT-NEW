"""
API Router for subscription management.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core.user import User
from app.schemas.core.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse
from app.core.database import get_db
from app.core.dependencies import get_product_admin
from app.subscription_service import (
    create_subscription,
    list_subscriptions,
    get_subscription_by_id,
    update_subscription,
    deactivate_subscription,
    SubscriptionNotFoundError,
    SubscriptionAlreadyExistsError,
)

logger = logging.getLogger(__name__)


# --- API ROUTER ---

router = APIRouter()

# Pydantic models for API responses
class SubscriptionListResponse(BaseModel):
    subscriptions: List[SubscriptionResponse]
    total: int
    page: int
    per_page: int


@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subscription"
)
async def api_create_subscription(
    subscription_data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    creator: User = Depends(get_product_admin)
):
    """
    Create a new subscription for a hotel.
    Requires Product Admin privileges.
    """
    try:
        return await create_subscription(db, subscription_data, creator)
    except SubscriptionAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get(
    "",
    response_model=SubscriptionListResponse,
    summary="List all subscriptions"
)
async def api_list_subscriptions(
    hotel_id: Optional[int] = Query(None, description="Filter by Hotel ID"),
    status: Optional[str] = Query(None, description="Filter by status (e.g., 'active', 'inactive')"),
    onboarding_mode: Optional[str] = Query(None, description="Filter by onboarding mode"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    creator: User = Depends(get_product_admin)
):
    """
    Retrieve a paginated list of subscriptions with optional filters.
    Requires Product Admin privileges.
    """
    subscriptions, total = await list_subscriptions(db, hotel_id, status, onboarding_mode, page, per_page)
    return {
        "subscriptions": subscriptions,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Get a subscription by ID"
)
async def api_get_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    creator: User = Depends(get_product_admin)
):
    """
    Retrieve a single subscription by its ID.
    Requires Product Admin privileges.
    """
    try:
        return await get_subscription_by_id(db, subscription_id)
    except SubscriptionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Update a subscription"
)
async def api_update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    creator: User = Depends(get_product_admin)
):
    """
    Update an existing subscription's plan, status, or dates.
    Requires Product Admin privileges.
    """
    try:
        return await update_subscription(db, subscription_id, update_data, creator)
    except SubscriptionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate a Subscription"
)
async def api_deactivate_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    creator: User = Depends(get_product_admin)
):
    """
    Deactivate an existing subscription by setting its status to 'inactive'.
    This is a soft delete. Requires Product Admin privileges.
    """
    try:
        return await deactivate_subscription(db, subscription_id, creator)
    except SubscriptionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))