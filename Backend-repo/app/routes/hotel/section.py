"""API routes for managing Sections within a Hall."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, get_super_admin_or_admin, get_super_admin, get_current_active_user
from app.models.core.user import User
from app.schemas.hotel.section import SectionCreate, SectionSuccessResponse, SectionUpdate, SectionResponse, SectionListApiResponse, SectionList
from app.services.hotel import section as section_service

section_router = APIRouter()


@section_router.post(
    "/branches/{branch_id}/floors/{floor_id}/halls/{hall_id}/sections", # This path is relative to the router's prefix
    response_model=SectionSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Section in a Hall"
)
async def create_section(
    branch_id: int,
    floor_id: int,
    hall_id: int,
    section_data: SectionCreate,
    current_user: User = Depends(get_super_admin_or_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create a new section within a specific hall.

    Requires Super Admin or Admin privileges.
    """
    try:
        new_section = await section_service.create_section_service(
            db=db,
            section_data=section_data,
            branch_id=branch_id,
            floor_id=floor_id,
            hall_id=hall_id,
            current_user=current_user,
        )
        return SectionSuccessResponse(success=True, data=new_section)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the section.")


@section_router.get(
    "/branches/{branch_id}/floors/{floor_id}/halls/{hall_id}/sections", # This path is relative to the router's prefix
    response_model=SectionListApiResponse,
    summary="List Sections in a Hall with optional filters"
)
async def list_sections_with_filters(
    branch_id: int,
    floor_id: int,
    hall_id: int,
    page: int = Query(1, ge=1, description="Page number for pagination."),
    per_page: int = Query(10, ge=1, le=100, description="Number of sections per page."),
    assigned_to: Optional[int] = Query(None, description="Filter sections by user ID assigned to tables within them."),
    section_status: Optional[str] = Query(None, enum=["all", "active", "inactive"], description="Filter sections by status."),
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves a list of sections for a specific hall.
    - Supports filtering by `assigned_to` and `section_status`.
    - Supports pagination.
    - Requires Super Admin privileges.
    """
    try:
        sections, total = await section_service.list_sections_service(
            db=db,
            branch_id=branch_id,
            floor_id=floor_id,
            hall_id=hall_id,
            current_user=current_user,
            page=page, per_page=per_page, assigned_to=assigned_to, section_status=section_status
        )
        return SectionListApiResponse(data=SectionList(sections=sections, total=total, page=page, per_page=per_page))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@section_router.get(
    "/branches/{branch_id}/floors/{floor_id}/halls/{hall_id}/sections/{section_sequence_id}",
    response_model=SectionResponse,
    summary="Get a single Section"
)
async def get_section(
    branch_id: int,
    floor_id: int,
    hall_id: int,
    section_sequence_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a single section by its sequence ID.

    Allows any active user to view.
    """
    try:
        return await section_service.get_section_service(db, branch_id, floor_id, hall_id, section_sequence_id, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@section_router.put(
    "/branches/{branch_id}/floors/{floor_id}/halls/{hall_id}/sections/{section_sequence_id}",
    response_model=SectionSuccessResponse,
    summary="Update a Section"
)
async def update_section(
    branch_id: int,
    floor_id: int,
    hall_id: int,
    section_sequence_id: int,
    update_data: SectionUpdate,
    current_user: User = Depends(get_super_admin_or_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Update a section's name or type.

    Requires Super Admin or Admin privileges.
    """
    try:
        updated_section = await section_service.update_section_service(db, branch_id, floor_id, hall_id, section_sequence_id, update_data, current_user)
        return SectionSuccessResponse(success=True, data=updated_section)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@section_router.delete(
    "/branches/{branch_id}/floors/{floor_id}/halls/{hall_id}/sections/{section_sequence_id}",
    status_code=status.HTTP_200_OK,
    summary="Deactivate a Section"
)
async def delete_section(
    branch_id: int,
    floor_id: int,
    hall_id: int,
    section_sequence_id: int,
    current_user: User = Depends(get_super_admin_or_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Deactivate a section (soft delete).

    Requires Super Admin or Admin privileges.
    """
    try:
        await section_service.delete_section_service(db, branch_id, floor_id, hall_id, section_sequence_id, current_user)
        return {"success": True, "message": "Section deactivated successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")