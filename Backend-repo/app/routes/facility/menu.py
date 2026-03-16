"""
API Router for the Menu Management feature.
Handles CRUD operations for Counters, Categories, Items, and related entities.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_current_active_user,
    get_db_session,
    get_user_with_menu_permission,
)
from app.models.core.user import User
from app.schemas.facility.menu import (
    CategoryCreate,
    CategoryNode,
    CategoryResponse,
    CategorysuccessResponse,
    CounterCreate,
    CounterstatusResponse,
    CounterResponse,
    CounterUpdate,
    MenuItemCreate,
    MenuItemResponse,
    MenuItemUpdate,
)
from app.services.facility import menu as menu_service

# This router will handle all endpoints under the /api/v1/facility/menu prefix
router = APIRouter()


class PaginatedCounterResponse(BaseModel):
    """Schema for paginated list of counters."""

    total: int
    counters: List[CounterResponse]

    class Config:
        from_attributes = True


@router.post(
    "/counters",
    response_model=CounterstatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Kitchen Counter"
)
async def create_counter_endpoint(
    counter_data: CounterCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_with_menu_permission), # Our new dependency!
):
    """
    Creates a new kitchen counter/station within a branch.
    - **Requires `menu_crud` permission.**
    """
    new_counter = await menu_service.create_counter(
        db=db, counter_data=counter_data, creator=current_user
    )
    return {
        "success": True,
        "data": new_counter,
    }


@router.get(
    "/counters",
    response_model=PaginatedCounterResponse,
    summary="List Kitchen Counters"
)
async def list_counters_endpoint(
    branch_id: int = Query(..., description="Filter counters by branch ID."),
    floor_number: Optional[int] = Query(None, description="Optionally filter counters by floor number."),
    limit: int = Query(50, ge=1, le=200, description="Number of counters to return."),
    offset: int = Query(0, ge=0, description="Offset for pagination."),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user), # Read access for all authenticated users
):
    """
    Retrieves a paginated list of kitchen counters for a specific branch, with optional filtering by floor.
    - **Accessible by any authenticated user.**
    """
    counters, total = await menu_service.get_counters_by_branch(
        db=db, branch_id=branch_id, floor_number=floor_number, creator=current_user, limit=limit, offset=offset
    )
    return PaginatedCounterResponse(total=total, counters=counters)


@router.patch(
    "/counters/{counter_id}",
    response_model=CounterstatusResponse,
    summary="Update a Kitchen Counter"
)
async def update_counter_endpoint(
    counter_id: int,
    update_data: CounterUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_with_menu_permission),
):
    """
    Updates a kitchen counter's details, such as its name or assigned staff.
    - **Requires `menu_crud` permission.**
    """
    updated_counter = await menu_service.update_counter(
        db=db, counter_id=counter_id, update_data=update_data, updater=current_user
    )
    return {
        "success": True,
        "data": updated_counter,
    }


@router.delete(
    "/counters/{counter_id}",
    response_model=CounterResponse,
    summary="Deactivate a Kitchen Counter"
)
async def deactivate_counter_endpoint(
    counter_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_with_menu_permission),
):
    """
    Deactivates a kitchen counter (soft delete). The counter will no longer be available for new assignments but historical data is preserved.
    - **Requires `menu_crud` permission.**
    """
    deactivated_counter = await menu_service.deactivate_counter(
        db=db, counter_id=counter_id, updater=current_user
    )
    return deactivated_counter


@router.post(
    "/categories",
    response_model=CategorysuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Category or Sub-Category"
)
async def create_category_endpoint(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_with_menu_permission),
):
    """
    Creates a new menu category. To create a sub-category, provide the `parent_id` of an existing category.
    - **Requires `menu_crud` permission.**
    """
    new_category = await menu_service.create_category(
        db=db, category_data=category_data, creator=current_user
    )
    return {
        "success": True,
        "data": new_category,
    }


@router.get(
    "/categories",
    response_model=List[CategoryNode],
    summary="Get Category Tree for a Counter"
)
async def get_category_tree_endpoint(
    counter_id: int = Query(..., description="The ID of the counter to fetch the category tree for."),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves the full hierarchical tree of active categories and sub-categories for a specific counter.
    - **Accessible by any authenticated user.**
    """
    category_tree = await menu_service.get_category_tree(
        db=db, counter_id=counter_id, creator=current_user
    )
    return category_tree


#
# Menu Item Endpoints
#


@router.post(
    "/items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Menu Item",
)
async def create_menu_item_endpoint(
    item_data: MenuItemCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_with_menu_permission),
):
    """
    Creates a new menu item within a specific category.

    - **Requires `menu_crud` permission or Product/Super Admin.**
    """
    new_item = await menu_service.create_menu_item(
        db=db, item_data=item_data, creator=current_user
    )
    return new_item


@router.patch(
    "/items/{item_id}",
    response_model=MenuItemResponse,
    summary="Update a Menu Item",
)
async def update_menu_item_endpoint(
    item_id: int,
    update_data: MenuItemUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_with_menu_permission),
):
    """
    Partially updates details of an existing menu item.

    - **Requires `menu_crud` permission or Product/Super Admin.**
    """
    updated_item = await menu_service.update_menu_item(
        db=db, item_id=item_id, update_data=update_data, updater=current_user
    )
    return updated_item


@router.delete(
    "/items/{item_id}",
    response_model=MenuItemResponse,
    summary="Deactivate a Menu Item",
)
async def deactivate_menu_item_endpoint(
    item_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_with_menu_permission),
):
    """
    Deactivates (soft deletes) a menu item. It will no longer appear in active menus,
    but historical data is preserved.

    - **Requires `menu_crud` permission or Product/Super Admin.**
    """
    deactivated_item = await menu_service.deactivate_menu_item(
        db=db, item_id=item_id, updater=current_user
    )
    return deactivated_item