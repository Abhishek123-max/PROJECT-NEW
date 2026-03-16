"""
Service layer for handling notification logic.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.websocket_manager import notification_manager
from app.models.core.notification import Notification
from app.schemas.core.notification import NotificationCreate, NotificationOut


async def create_and_broadcast_notification(
    notification_data: NotificationCreate,
) -> Notification:
    """
    Creates a notification in a new DB session, saves it, and broadcasts it.
    This runs in its own transaction to decouple it from the calling service.
    """
    async with get_db_session() as db:
        db_notification = Notification(**notification_data.model_dump())
        db.add(db_notification)
        await db.commit()
        await db.refresh(db_notification)

        broadcast_payload = NotificationOut.from_attributes(db_notification).model_dump()
        if isinstance(broadcast_payload.get("created_at"), datetime):
            broadcast_payload["created_at"] = broadcast_payload["created_at"].isoformat()

        await notification_manager.broadcast(broadcast_payload)

        return db_notification


async def list_notifications(
    db: AsyncSession,
    type: Optional[str] = None,
    hotel_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Notification], int]:
    """
    Fetches a paginated and filtered list of historical notifications.
    """
    query = select(Notification)

    if type:
        query = query.where(Notification.type == type)
    if hotel_id:
        query = query.where(Notification.hotel_id == hotel_id)
    if start_date:
        query = query.where(Notification.created_at >= start_date)
    if end_date:
        query = query.where(Notification.created_at <= end_date)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * per_page
    paged_query = query.order_by(Notification.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(paged_query)
    notifications = result.scalars().all()

    return notifications, total