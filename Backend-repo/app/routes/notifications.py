"""
API Router for the Product Admin Communication System.
Handles WebSocket connections for real-time alerts and provides a REST endpoint
for historical notification data.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_product_admin, get_current_active_user
from app.core.auth import decode_token
from app.core.websocket_manager import notification_manager
from app.models.core.user import User
from app.schemas.core.notification import NotificationListResponse, NotificationList, NotificationOut
from app.services.core.notification_service import list_notifications
from app.utils.exceptions import DataSegregationError

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_product_admin_from_ws_token(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to authenticate a user from a WebSocket token and verify
    they are a product admin.
    """
    try:
        payload = decode_token(token)
        user_id: int = payload.get("user_id")
        role: str = payload.get("role_name")
        if user_id is None or role != "product_admin":
            raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="Not enough permissions")
    except Exception:
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")

    user = await db.get(User, user_id)
    if user is None or not user.is_active or not user.is_product_admin():
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="User not found or not authorized")
    
    return user


@router.websocket("/ws/notifications")
async def websocket_notification_endpoint(
    websocket: WebSocket,
    user: User = Depends(get_product_admin_from_ws_token),
):
    """
    Establishes a WebSocket connection for real-time notifications to Product Admins.
    Authenticates via a JWT token passed as a query parameter.
    """
    await notification_manager.connect(websocket, user.id)
    logger.info(f"Product Admin (ID: {user.id}) connected to notifications WebSocket.")
    try:
        while True:
            # Keep the connection alive. The server sends messages.
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_manager.disconnect(user.id)
        logger.info(f"Product Admin (ID: {user.id}) disconnected from notifications WebSocket.")


async def get_hotel_scoped_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to allow hotel-scoped users (super_admin, admin, manager, staff).
    Ensures user has a hotel_id for data segregation.
    """
    # Product admins can access all notifications via the other endpoint
    if current_user.is_product_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Product admins should use the /notifications endpoint"
        )
    
    # Check if user has a hotel_id (required for hotel-scoped access)
    if current_user.hotel_id is None:
        raise DataSegregationError("User must be associated with a hotel to access notifications.")
    
    return current_user


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Get historical notifications (Product Admin)"
)
async def api_list_notifications(
    type: Optional[str] = Query(None, description='Filter by notification type (e.g., "new_hotel_request", "subscription_update")'),
    hotel_id: Optional[int] = Query(None, description="Filter by specific hotel ID"),
    start_date: Optional[datetime] = Query(None, description="Filter notifications from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter notifications up to this date"),
    page: int = Query(1, ge=1, description="Pagination page number"),
    per_page: int = Query(20, ge=1, le=100, description="Number of results per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_product_admin),
):
    """
    Retrieve a historical list of notifications for auditing or review.
    Only accessible by Product Admins.
    """
    notifications, total = await list_notifications(
        db=db, type=type, hotel_id=hotel_id, start_date=start_date,
        end_date=end_date, page=page, per_page=per_page
    )
    return NotificationListResponse(
        data=NotificationList(
            notifications=[NotificationOut.model_validate(n) for n in notifications],
            total=total,
            page=page,
            per_page=per_page
        )
    )


@router.get(
    "/hotel",
    response_model=NotificationListResponse,
    summary="Get hotel notifications (Super Admin, Admin, Manager, Staff)"
)
async def api_list_hotel_notifications(
    type: Optional[str] = Query(None, description='Filter by notification type (e.g., "branch_created")'),
    start_date: Optional[datetime] = Query(None, description="Filter notifications from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter notifications up to this date"),
    page: int = Query(1, ge=1, description="Pagination page number"),
    per_page: int = Query(20, ge=1, le=100, description="Number of results per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_hotel_scoped_user),
):
    """
    Retrieve notifications for the current user's hotel.
    Automatically filters by the user's hotel_id for data segregation.
    Accessible by Super Admin, Admin, Manager, and Staff roles.
    """
    # Automatically filter by user's hotel_id (data segregation)
    hotel_id = current_user.hotel_id
    
    notifications, total = await list_notifications(
        db=db, type=type, hotel_id=hotel_id, start_date=start_date,
        end_date=end_date, page=page, per_page=per_page
    )
    return NotificationListResponse(
        data=NotificationList(
            notifications=[NotificationOut.model_validate(n) for n in notifications],
            total=total,
            page=page,
            per_page=per_page
        )
    )