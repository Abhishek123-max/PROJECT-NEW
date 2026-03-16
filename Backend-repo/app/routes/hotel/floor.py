from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.core.dependencies import get_db_session, get_super_admin_or_admin, get_super_admin
from app.models.core.user import User
from app.schemas.hotel.floor import (
    FloorCreate, FloorUpdate, FloorApiResponse, FloorListApiResponse, FloorList
)
from app.services.hotel import floor as floor_service
from app.schemas.hotel.floor import FloorResponse
from app.services.hotel.branch import get_branch_by_id, get_branch_by_sequence_and_creator
from app.utils.exceptions import InsufficientPermissionsError

router = APIRouter()


@router.post(
    "/branches/{branch_sequence}/floors",
    response_model=FloorApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new floor"
)
async def create_floor(
    branch_sequence: int,
    floor_data: FloorCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_super_admin_or_admin)
):
    try:
        new_floor = await floor_service.create_floor(db, branch_sequence, floor_data, current_user)
        response_data = FloorResponse.model_validate(new_floor)
        # Ensures the response includes the assigned manager user IDs
        response_data.floor_manager_ids = [fm.user_id for fm in getattr(new_floor, "floor_managers", [])]
        return FloorApiResponse(data=response_data)
    except (ValueError, InsufficientPermissionsError) as e:
        # Business/permission validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError:
        # DB-level unique constraint issues
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A floor with this number already exists in this branch.",
        )
    except HTTPException:
        # Let service-raised HTTPExceptions (like duplicate name) pass through unchanged
        raise
    except Exception as e:
        import logging
        logging.error(f"create_floor error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get(
    "/branches/{branch_id}/floors",
    response_model=FloorListApiResponse, # This response model already supports pagination
    summary="List floors in a branch with optional filters"
)
async def list_floors(
    branch_id: int,
    # New optional query parameters for filtering and pagination
    page: int = Query(1, ge=1, description="Page number for pagination."),
    per_page: int = Query(10, ge=1, le=100, description="Number of floors per page."),
    assigned_to: Optional[int] = Query(None, description="Filter floors by the ID of the assigned manager."),
    floor_status: Optional[str] = Query("active", enum=["active", "inactive"], description="Filter floors by status."),
    db: AsyncSession = Depends(get_db_session), 
    current_user: User = Depends(get_super_admin_or_admin) # Super Admin can list floors
):
    """
    Retrieves a list of floors for a specific branch.
    - Supports filtering by `assigned_to` (manager ID) and `status`.
    - Supports pagination with `page` and `per_page`.
    - Requires Super Admin privileges.
    """
    try:
        # First, get the branch to ensure it exists and we have its ID
        branch = await get_branch_by_id(db, branch_id)
        import logging
        logging.warning(f"DEBUG branch type: {type(branch)}, branch: {branch}")
        if branch:
            logging.warning(f"DEBUG branch.id type: {type(branch.id)}, branch.id: {branch.id}")
        if not branch:
            raise ValueError("Branch not found or you do not have permission to access it.")

        floors, total = await floor_service.list_floors(db, branch.id, page, per_page, assigned_to, floor_status)
        # Convert SQLAlchemy Floor objects to Pydantic FloorResponse models
        floors_response = [FloorResponse.model_validate(floor) for floor in floors]
        return FloorListApiResponse(data=FloorList(floors=floors_response, total=total, page=page, per_page=per_page))
    except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get(
    "/branches/{branch_id}/floors/{floor_id}",
    response_model=FloorApiResponse,
    summary="Get a specific floor"
)
async def get_floor(
    branch_id: int,
    floor_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_super_admin_or_admin)
):
    try:
        floor = await floor_service.get_floor_by_id(db, branch_id, floor_id, current_user)
        if not floor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor not found.")
        return FloorApiResponse(data=floor)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.put(
    "/branches/{branch_id}/floors/{floor_id}",
    response_model=FloorApiResponse,
    summary="Update a floor"
)
async def update_floor(
    branch_id: int,
    floor_id: int,
    update_data: FloorUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_super_admin_or_admin)
):
    try:
        # First, get the floor to ensure it exists and belongs to the user's hierarchy
        floor_to_update = await floor_service.get_floor_by_id(db, branch_id, floor_id, current_user)
        if not floor_to_update:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor not found.")

        updated_floor = await floor_service.update_floor(db, floor_to_update, update_data, current_user)
        # Ensures the response includes the assigned manager user IDs
        response_data = FloorResponse.model_validate(updated_floor)
        response_data.floor_manager_ids = [fm.user_id for fm in getattr(updated_floor, "floor_managers", [])]
        return FloorApiResponse(data=response_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A floor with this number already exists in this branch.")
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"update_floor error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@router.delete(
    "/branches/{branch_id}/floors/{floor_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a floor"
)
async def delete_floor(
    branch_id: int,
    floor_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_super_admin_or_admin)
):
    try:
        # First, get the floor to ensure it exists and belongs to the user's hierarchy
        floor_to_delete = await floor_service.get_floor_by_id(db, branch_id, floor_id, current_user)
        if not floor_to_delete:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor not found.")

        await floor_service.delete_floors(db, floor_to_delete, current_user)
        return {"success": True, "message": "Floor deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")