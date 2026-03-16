"""API routes for managing Halls."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, get_super_admin, get_current_active_user
from app.models.core.user import User
from app.schemas.hotel.hall import HallCreate, HallResponse, HallSuccessResponse, HallUpdate, HallStatusUpdate, HallListApiResponse, HallList
from app.services.hotel.hall import (
    create_hall_service,
    list_halls as list_halls_service,
    get_hall_service,
    get_hall_service_without_active_filter,
    update_hall_service,
    toggle_hall_status_service,
    delete_hall_service,
)
from app.services.hotel.floor import get_floor_by_id # Use a secure way to get floor

hall_router = APIRouter()


@hall_router.post(
    "/branches/{branch_id}/floors/{floor_id}/halls",
    response_model=HallSuccessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_hall(
    branch_id: int,
    floor_id: int,
    hall_data: HallCreate,
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create a new hall on a specific floor within a branch.

    Requires Super Admin privileges.
    """
    try:
        new_hall = await create_hall_service(
            db=db,
            hall_data=hall_data,
            branch_id=branch_id,
            floor_id=floor_id,
            current_user=current_user,
        )
        return {
            "success": True,
            "data": new_hall
        }
    except HTTPException as http_exc:
        # Re-raise HTTPException to let FastAPI handle it
        raise http_exc
    except Exception as e:
        # In a real app, you would log the exception `e` here
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the hall.")


@hall_router.get(
    "/branches/{branch_id}/floors/{floor_id}/halls", # This path is relative to the router's prefix
    response_model=HallListApiResponse,
    summary="List halls on a floor with optional filters"
)
async def list_halls_with_filters(
    branch_id: int,
    floor_id: int,
    page: int = Query(1, ge=1, description="Page number for pagination."),
    per_page: int = Query(10, ge=1, le=100, description="Number of halls per page."),
    assigned_to: Optional[int] = Query(None, description="Filter halls by user ID assigned to tables within them."),
    status: Optional[str] = Query(None, enum=["active", "inactive"], description="Filter halls by status."),
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves a list of halls for a specific floor.
    - Supports filtering by `assigned_to` (a user assigned to a table within the hall).
    - Supports filtering by `status`.
    - Supports pagination.
    - Requires Super Admin privileges.
    """
    try:
        # Securely get the floor to find its actual ID
        floor = await get_floor_by_id(db, branch_id, floor_id, current_user)
        if not floor:
            raise ValueError("Floor not found or you do not have permission to access it.")

        halls, total = await list_halls_service(
            db=db,
            floor_id=floor.id,
            page=page,
            per_page=per_page,
            assigned_to=assigned_to,
            status=status,
            current_user=current_user,
        )
        # Convert SQLAlchemy models to Pydantic schemas
        hall_responses = [HallResponse.model_validate(hall) for hall in halls]
        return HallListApiResponse(data=HallList(halls=hall_responses, total=total, page=page, per_page=per_page))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@hall_router.get(
    "/branches/{branch_id}/floors/{floor_id}/halls/{hall_id}",
    response_model=HallResponse,
)
async def get_hall(
    branch_id: int,
    floor_id: int,
    hall_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a single hall by its sequence ID.

    Allows any active user to view.
    """
    return await get_hall_service(db, branch_id, floor_id, hall_id, current_user)


@hall_router.put(
    "/branches/{branch_id}/floors/{floor_id}/halls/{hall_id}",
    response_model=HallResponse,
)
async def update_hall(
    branch_id: int,
    floor_id: int,
    hall_id: int,
    update_data: HallUpdate,
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Update a hall's name or type.

    Requires Super Admin privileges.
    """
    # First, get the hall to ensure it exists and belongs to the user's hierarchy
    hall_to_update = await get_hall_service(db, branch_id, floor_id, hall_id, current_user)

    return await update_hall_service(db, hall_to_update, update_data, current_user)


@hall_router.patch(
    "/branches/{branch_id}/floors/{floor_id}/halls/{hall_id}/status",
    response_model=HallSuccessResponse,
)
async def toggle_hall_status(
    branch_id: int,
    floor_id: int,
    hall_id: int,
    status_data: HallStatusUpdate,
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Toggle a hall's active status (activate or deactivate).

    Requires Super Admin privileges.
    """
    # Get the hall without active filter to allow reactivating inactive halls
    hall = await get_hall_service_without_active_filter(db, branch_id, floor_id, hall_id, current_user)
    
    # Toggle the status
    updated_hall = await toggle_hall_status_service(
        db=db,
        hall=hall,
        is_active=status_data.is_active,
        current_user=current_user,
    )
    return {"success": True,
            "data": updated_hall}


@hall_router.delete(
    "/branches/{branch_id}/floors/{floor_id}/halls/{hall_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_hall(
    branch_id: int,
    floor_id: int,
    hall_id: int,
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Deactivate a hall (soft delete).

    Requires Super Admin privileges.
    """
    # First, get the hall to ensure it exists and belongs to the user's hierarchy
    hall_to_delete = await get_hall_service_without_active_filter(db, branch_id, floor_id, hall_id, current_user)
    
    # Then, call the service to soft-delete it
    await delete_hall_service(db, hall_to_delete, current_user)
    return {"success": True, "message": "Hall Deleted successfully."}