"""API routes for managing Tables."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, get_super_admin_or_admin, get_super_admin, get_current_active_user
from app.models.core.user import User
from app.schemas.hotel.table import TableCreate,TableCreateResponse, TableUpdate, TableShift, TableResponse, TableListApiResponse, TableList, TableStatus
from app.services.hotel import table as table_service

table_router = APIRouter()


@table_router.post(
    "/branches/{branch_id}/tables", # This path is relative to the router's prefix
    response_model=TableCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Table"
)
async def create_table(
    branch_id: int,
    table_data: TableCreate,
    current_user: User = Depends(get_super_admin_or_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create a new table within a specific branch.

    The table can be assigned to a floor, a hall, or a section within the branch.
    Requires Super Admin or Admin privileges.
    """
    try:
        new_table = await table_service.create_table_service(
            db=db,
            table_data=table_data,
            branch_id=branch_id,
            current_user=current_user,
        )
        return TableCreateResponse(success=True, data=new_table)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


@table_router.get(
    "/branches/{branch_id}/tables", # This path is relative to the router's prefix
    response_model=TableListApiResponse,
    summary="List Tables in a Branch with optional filters"
)
async def list_tables_with_filters(
    branch_id: int,
    page: int = Query(1, ge=1, description="Page number for pagination."),
    per_page: int = Query(10, ge=1, le=100, description="Number of tables per page."),
    assigned_to: Optional[int] = Query(None, description="Filter tables by the ID of the assigned user."),
    table_status: Optional[TableStatus] = Query(None, description="Filter tables by their status."),
    current_user: User = Depends(get_super_admin), # Enforcing Super Admin as per requirements
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves a list of tables for a specific branch.
    - Supports filtering by `assigned_to` and `table_status`.
    - Supports pagination.
    - Requires Super Admin privileges.
    """
    try:
        tables, total = await table_service.list_tables_service(
            db, branch_id, current_user, page, per_page, assigned_to, table_status
        )
        return TableListApiResponse(data=TableList(tables=tables, total=total, page=page, per_page=per_page))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@table_router.get(
    "/branches/{branch_id}/tables/{table_id}",
    response_model=TableResponse,
    summary="Get a single Table"
)
async def get_table(
    branch_id: int,
    table_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a single table by its primary key ID, ensuring it belongs to the specified branch.

    Allows any active user to view.
    """
    try:
        return await table_service.get_table_service(db, branch_id, table_id, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@table_router.put(
    "/branches/{branch_id}/tables/{table_id}",
    response_model=TableResponse,
    summary="Update a Table"
)
async def update_table(
    branch_id: int,
    table_id: int,
    update_data: TableUpdate,
    current_user: User = Depends(get_super_admin_or_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Update a table's details (e.g., number, seats, status).
    This endpoint does not handle moving the table to a new parent.

    Requires Super Admin or Admin privileges.
    """
    try:
        return await table_service.update_table_service(db, branch_id, table_id, update_data, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@table_router.put(
    "/branches/{branch_id}/tables/{table_id}/shift",
    response_model=TableResponse,
    summary="Shift a Table to a new Parent"
)
async def shift_table(
    branch_id: int,
    table_id: int,
    shift_data: TableShift,
    current_user: User = Depends(get_super_admin_or_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Moves a table to a new parent (Floor, Hall, or Section) and re-sequences it accordingly.
    This is a transaction-safe operation.

    Requires Super Admin or Admin privileges.
    """
    try:
        return await table_service.shift_table_service(db, branch_id, table_id, shift_data, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@table_router.delete(
    "/branches/{branch_id}/tables/{table_id}",
    status_code=status.HTTP_200_OK,
    summary="Deactivate a Table"
)
async def delete_table(
    branch_id: int,
    table_id: int,
    current_user: User = Depends(get_super_admin_or_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Deactivate a table (soft delete). The table will no longer be listed but its data is preserved.

    Requires Super Admin or Admin privileges.
    """
    try:
        await table_service.delete_table_service(db, branch_id, table_id, current_user)
        return {"success": True, "message": "Table deactivated successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")