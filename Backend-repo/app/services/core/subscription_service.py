"""Service layer for subscription management."""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core.subscription import Subscription
from app.models.core.user import User
from app.schemas.core.subscription import SubscriptionCreate, SubscriptionUpdate
from app.schemas.core.notification import NotificationCreate
from app.settings.constants import PLAN_FEATURES
from app.core.audit import audit_service
from app.services.core.notification_service import create_and_broadcast_notification


class SubscriptionNotFoundError(Exception):
    """Custom exception for subscription not found errors."""
    pass


async def create_subscription(
    db: AsyncSession,
    subscription_data: SubscriptionCreate,
    creator: User
) -> Subscription:
    """
    Creates a new subscription for a hotel.
    """
    feature_toggles = PLAN_FEATURES.get(subscription_data.plan_type, {})

    new_subscription = Subscription(
        **subscription_data.dict(),
        feature_toggles=feature_toggles,
        status="active"
    )
    db.add(new_subscription)
    await db.commit()
    await db.refresh(new_subscription)

    # Send notification for new active subscription
    await create_and_broadcast_notification(
        notification_data=NotificationCreate(
            type="subscription_update",
            hotel_id=new_subscription.hotel_id,
            details={
                "subscription_id": new_subscription.id,
                "status": new_subscription.status,
                "update_date": datetime.utcnow().isoformat(),
            },
        )
    )

    await audit_service.log_system_event(
        event_type="subscription_created",
        action="create_subscription",
        user_id=creator.id,
        success=True,
        details={
            "subscription_id": new_subscription.id,
            "hotel_id": new_subscription.hotel_id,
            "plan_type": new_subscription.plan_type,
        }
    )

    return new_subscription


async def get_subscription_by_id(
    db: AsyncSession,
    subscription_id: int,
) -> Subscription:
    """
    Fetches a single subscription by its ID.
    """
    subscription = await db.get(Subscription, subscription_id)
    if not subscription:
        raise SubscriptionNotFoundError(f"Subscription with ID {subscription_id} not found.")
    return subscription


async def list_subscriptions(
    db: AsyncSession,
    hotel_id: Optional[int],
    status: Optional[str],
    onboarding_mode: Optional[str],
    page: int,
    per_page: int
) -> Tuple[List[Subscription], int]:
    """
    Fetches a paginated and filtered list of subscriptions.
    """
    query = select(Subscription)
    if hotel_id:
        query = query.where(Subscription.hotel_id == hotel_id)
    if status:
        query = query.where(Subscription.status == status)
    if onboarding_mode:
        query = query.where(Subscription.onboarding_mode == onboarding_mode)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * per_page
    paged_query = query.order_by(Subscription.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(paged_query)
    subscriptions = result.scalars().all()

    return subscriptions, total


async def update_subscription(
    db: AsyncSession,
    subscription_id: int,
    update_data: SubscriptionUpdate,
    creator: User
) -> Subscription:
    """
    Updates an existing subscription.
    """
    subscription = await get_subscription_by_id(db, subscription_id)
    update_dict = update_data.dict(exclude_unset=True)

    if "plan_type" in update_dict:
        subscription.feature_toggles = PLAN_FEATURES.get(update_dict["plan_type"], {})

    for key, value in update_dict.items():
        setattr(subscription, key, value)

    await db.commit()
    await db.refresh(subscription)

    # Send notification for subscription update
    await create_and_broadcast_notification(
        notification_data=NotificationCreate(
            type="subscription_update",
            hotel_id=subscription.hotel_id,
            details={
                "subscription_id": subscription.id,
                "status": subscription.status,
                "update_date": datetime.utcnow().isoformat(),
                "changes": update_dict,
            },
        )
    )

    await audit_service.log_system_event(
        event_type="subscription_updated",
        action="update_subscription",
        user_id=creator.id,
        success=True,
        details={
            "subscription_id": subscription.id,
            "changes": update_dict,
        }
    )

    return subscription