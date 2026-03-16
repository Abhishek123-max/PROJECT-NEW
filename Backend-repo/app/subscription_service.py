"""Service layer for subscription management."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from .models.core.audit import AuditLog
from .models.core.subscription import Subscription
from .models.core.user import User
from .schemas.core.subscription import SubscriptionCreate, SubscriptionUpdate
from .schemas.core.notification import NotificationCreate
from .settings.constants import PLAN_FEATURES
from .services.core.notification_service import create_and_broadcast_notification
from .core.database import get_db_session


class SubscriptionNotFoundError(Exception):
    """Custom exception for subscription not found errors."""
    pass


class SubscriptionAlreadyExistsError(Exception):
    """Custom exception for when an active subscription already exists for a hotel."""
    def __init__(self, existing_subscription: Subscription):
        self.subscription = existing_subscription
        plan_type = self.subscription.plan_type
        # Format dates for readability in the error message
        start_date = self.subscription.subscription_start_date.strftime('%Y-%m-%d')
        end_date = self.subscription.subscription_end_date.strftime('%Y-%m-%d')
        message = (
            f"There is a {plan_type} subscription going on for this hotel id. "
            f"The subscription starts on {start_date} and ends on {end_date}. "
            "If you want to update the subscription plan, you can use the update subscription endpoint."
        )
        super().__init__(message)


async def create_subscription(
    db: AsyncSession,
    subscription_data: SubscriptionCreate,
    creator: User
) -> Subscription:
    """
    Creates a new subscription for a hotel.

    Args:
        db: The database session.
        subscription_data: The data for the new subscription.
        creator: The Product Admin creating the subscription.

    Returns:
        The created Subscription object.
    """
    # Check for an existing active subscription for the same hotel
    existing_sub_query = select(Subscription).where(
        Subscription.hotel_id == subscription_data.hotel_id,
        Subscription.status == 'active'
    )
    result = await db.execute(existing_sub_query)
    # Use .first() to be robust against cases where old logic might have created multiple active subs
    existing_subscription = result.scalars().first()

    if existing_subscription:
        raise SubscriptionAlreadyExistsError(existing_subscription)

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

    audit_entry = AuditLog(
        event_type="subscription_created",
        action="create_subscription",
        success="success",
        user_id=creator.id,
        hotel_id=new_subscription.hotel_id,
        resource="subscription",
        resource_id=new_subscription.id,
        details={
            "plan_type": new_subscription.plan_type,
        }
    )
    db.add(audit_entry)

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
    paged_query = query.offset(offset).limit(per_page)
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

    # Create a JSON-serializable version of the changes for notifications and auditing.
    serializable_changes = {
        k: v.isoformat() if isinstance(v, datetime) else v
        for k, v in update_dict.items()
    }

    # Send notification for subscription update
    await create_and_broadcast_notification(
        notification_data=NotificationCreate(
            type="subscription_update",
            hotel_id=subscription.hotel_id,
            details={
                "subscription_id": subscription.id,
                "status": subscription.status,
                "update_date": datetime.utcnow().isoformat(),
                "changes": serializable_changes,
            },
        )
    )

    audit_entry = AuditLog(
        event_type="subscription_updated",
        action="update_subscription",
        success="success",
        user_id=creator.id,
        hotel_id=subscription.hotel_id,
        resource="subscription",
        resource_id=subscription.id,
        details={
            "changes": serializable_changes,
        }
    )
    db.add(audit_entry)

    return subscription


async def deactivate_subscription(
    db: AsyncSession,
    subscription_id: int,
    creator: User
) -> Subscription:
    """
    Deactivates a subscription by setting its status to 'inactive'.
    """
    subscription = await get_subscription_by_id(db, subscription_id)
    subscription.status = "inactive"
    
    await db.commit()
    await db.refresh(subscription)

    # Send notification for subscription deactivation
    await create_and_broadcast_notification(
        notification_data=NotificationCreate(
            type="subscription_update",
            hotel_id=subscription.hotel_id,
            details={
                "subscription_id": subscription.id,
                "status": "inactive",
                "update_date": datetime.utcnow().isoformat(),
            },
        )
    )

    audit_entry = AuditLog(
        event_type="subscription_deactivated",
        action="deactivate_subscription",
        success="success",
        user_id=creator.id,
        hotel_id=subscription.hotel_id,
        resource="subscription",
        resource_id=subscription.id,
        details={
            "deactivated_by": creator.id
        }
    )
    db.add(audit_entry)

    return subscription


async def check_and_expire_subscriptions():
    """
    A background job to find active subscriptions that have passed their end date
    and update their status to 'expired'.
    """
    logger = logging.getLogger(__name__)
    logger.info("Background job: Running check for expired subscriptions...")
    async with get_db_session() as db:
        try:
            utc_now = datetime.utcnow()
            expired_subs_query = select(Subscription).where(
                Subscription.status == 'active',
                Subscription.subscription_end_date < utc_now
            )
            result = await db.execute(expired_subs_query)
            subscriptions_to_expire = result.scalars().all()

            if not subscriptions_to_expire:
                logger.info("Background job: No subscriptions to expire.")
                return

            for sub in subscriptions_to_expire:
                sub.status = 'expired'
                await create_and_broadcast_notification(notification_data=NotificationCreate(type="subscription_update", hotel_id=sub.hotel_id, details={"subscription_id": sub.id, "status": "expired", "update_date": utc_now.isoformat()}))
                audit_entry = AuditLog(
                    event_type="subscription_expired_system",
                    action="expire_subscription",
                    success="success",
                    user_id=None,  # System action
                    hotel_id=sub.hotel_id,
                    resource="subscription",
                    resource_id=sub.id,
                    details={
                        "expired_on": sub.subscription_end_date.isoformat()
                    }
                )
                db.add(audit_entry)
            
            await db.commit()
            logger.info(f"Background job: Successfully expired {len(subscriptions_to_expire)} subscription(s).")
        except Exception as e:
            logger.error(f"Background job: Error during subscription expiration check: {e}", exc_info=True)