"""Service layer for the Menu Management feature."""

import logging
import time
from typing import Optional, List, Dict, Any, Tuple

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.core.user import User
from app.schemas.facility.menu import (
    CategoryCreate,
    CategoryNode,
    CategoryResponse,
    CounterCreate,
    CounterUpdate,
    MenuItemCreate,
    MenuItemUpdate,
)
from app.models.core.auth import Branch
from app.models.facility.menu import Category, Counter, MenuItem, TaxProfile
from app.services.core.storage_service import storage_service
from app.services.hotel.branch import get_branch_by_id
from app.utils.exceptions import (
    DataSegregationError,
    InsufficientPermissionsError,
    ItemNotFoundError,
)

logger = logging.getLogger(__name__)


async def create_counter(
    db: AsyncSession, counter_data: CounterCreate, creator: User
) -> Counter:
    """
    Creates a new kitchen counter/station.

    Args:
        db: The database session.
        counter_data: The data for the new counter.
        creator: The user performing the action.

    Returns:
        The newly created Counter object.
    """
    # 1. Authorization Check
    # A user can create a counter if they are a Super Admin, Product Admin,
    # or have the 'menu_crud' permission in their role.
    is_super_or_product_admin = creator.is_super_admin() or creator.is_product_admin()
    has_menu_permission = (
        creator.role.permissions.get("menu_crud")
        if creator.role and creator.role.permissions
        else False
    )

    if not (is_super_or_product_admin or has_menu_permission):
        raise InsufficientPermissionsError("You do not have permission to create a counter.")

    # 2. Hierarchy Validation
    branch = await get_branch_by_id(db, counter_data.branch_id)
    if not branch:
        raise ItemNotFoundError(f"Branch with ID {counter_data.branch_id} not found.")

    if not creator.is_product_admin() and branch.hotel_id != creator.hotel_id:
        raise DataSegregationError("You can only create counters for branches within your own hotel.")

    # 3. Staff Assignment Validation
    if counter_data.staff_assign_id:
        staff_result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.id == counter_data.staff_assign_id)
        )
        staff_to_assign = staff_result.scalar_one_or_none()
        if not staff_to_assign:
            raise ItemNotFoundError(f"User with ID {counter_data.staff_assign_id} not found for staff assignment.")
        if not staff_to_assign.role or staff_to_assign.role.name != "kitchen_staff":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned staff must have the 'kitchen_staff' role.",
            )

    # 4. Sequence Generation (Transaction-safe)
    max_sequence_result = await db.execute(
        select(func.max(Counter.counter_sequence)).where(
            Counter.branch_id == counter_data.branch_id,
            Counter.floor_number == counter_data.floor_number,
        )
    )
    max_sequence = max_sequence_result.scalar_one_or_none() or 0
    next_sequence = max_sequence + 1

    # 5. Object Creation
    new_counter = Counter(
        name=counter_data.name,
        branch_id=counter_data.branch_id,
        floor_number=counter_data.floor_number,
        staff_assign_id=counter_data.staff_assign_id,
        counter_sequence=next_sequence,
        created_by=creator.id,
        updated_by=creator.id,
    )

    # 6. Database Commit
    db.add(new_counter)
    await db.commit()
    await db.refresh(new_counter)

    logger.info(f"User '{creator.username}' (ID: {creator.id}) created new counter '{new_counter.name}' (ID: {new_counter.id}).")

    return new_counter


async def get_counters_by_branch(
    db: AsyncSession,
    branch_id: int,
    creator: User,
    floor_number: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Counter], int]:
    """Fetches and filters counters for a given branch."""
    # Data segregation check
    branch = await get_branch_by_id(db, branch_id)
    if not branch:
        raise ItemNotFoundError(f"Branch with ID {branch_id} not found.")

    if not creator.is_product_admin() and branch.hotel_id != creator.hotel_id:
        raise DataSegregationError("You can only view counters for branches within your own hotel.")

    query = select(Counter).where(Counter.branch_id == branch_id)

    if floor_number is not None:
        query = query.where(Counter.floor_number == floor_number)

    # Get total count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination and ordering
    paged_query = query.order_by(Counter.floor_number, Counter.counter_sequence).offset(offset).limit(limit)
    result = await db.execute(paged_query)
    counters = result.scalars().all()

    return counters, total


async def get_counter_by_id(db: AsyncSession, counter_id: int, creator: User) -> Counter:
    """Helper function to fetch a single counter and validate ownership/permissions."""
    result = await db.execute(
        select(Counter).options(selectinload(Counter.branch)).where(Counter.id == counter_id)
    )
    counter = result.scalar_one_or_none()

    if not counter:
        raise ItemNotFoundError(f"Counter with ID {counter_id} not found.")

    # Data segregation check
    if not creator.is_product_admin() and counter.branch.hotel_id != creator.hotel_id:
        raise DataSegregationError("You do not have permission to access this counter.")

    return counter


async def update_counter(
    db: AsyncSession, counter_id: int, update_data: CounterUpdate, updater: User
) -> Counter:
    """Partially updates a counter's details."""
    counter_to_update = await get_counter_by_id(db, counter_id, updater)

    update_dict = update_data.dict(exclude_unset=True)

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided."
        )

    # If staff is being changed, validate the new staff member
    if "staff_assign_id" in update_dict and update_dict["staff_assign_id"] is not None:
        staff_result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.id == update_dict["staff_assign_id"])
        )
        staff_to_assign = staff_result.scalar_one_or_none()
        if not staff_to_assign:
            raise ItemNotFoundError(f"User with ID {update_dict['staff_assign_id']} not found for staff assignment.")
        if not staff_to_assign.role or staff_to_assign.role.name != "kitchen_staff":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned staff must have the 'kitchen_staff' role.",
            )

    for key, value in update_dict.items():
        setattr(counter_to_update, key, value)

    counter_to_update.updated_by = updater.id

    await db.commit()
    await db.refresh(counter_to_update)

    logger.info(f"User '{updater.username}' (ID: {updater.id}) updated counter ID {counter_id}.")

    return counter_to_update


async def deactivate_counter(db: AsyncSession, counter_id: int, updater: User) -> Counter:
    """Hard-deletes a counter by removing it from the database."""
    counter_to_deactivate = await get_counter_by_id(db, counter_id, updater)

    await db.delete(counter_to_deactivate)
    await db.commit()

async def create_category(
    db: AsyncSession, category_data: CategoryCreate, creator: User
) -> Category:
    """Creates a new category or sub-category, including sequence generation."""
    # 1. Hierarchy Validation: Ensure the counter exists and belongs to the user's hotel.
    # The get_counter_by_id helper already performs the necessary data segregation checks.
    counter = await get_counter_by_id(db, category_data.counter_id, creator)

    # If creating a sub-category, validate the parent.
    if category_data.parent_id:
        parent_result = await db.execute(
            select(Category).where(Category.id == category_data.parent_id)
        )
        parent_category = parent_result.scalar_one_or_none()
        if not parent_category:
            raise ItemNotFoundError(f"Parent category with ID {category_data.parent_id} not found.")
        if not parent_category.active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add sub-category to an inactive parent category.")
        # Crucial check to prevent cross-counter nesting.
        if parent_category.counter_id != counter.id:
            raise DataSegregationError("Parent category must belong to the same counter.")

    # 2. Sequence Generation (Transaction-safe)
    # The where clause correctly handles both top-level (parent_id is None) and sub-categories.
    max_sequence_result = await db.execute(
        select(func.max(Category.category_sequence)).where(
            Category.counter_id == category_data.counter_id,
            Category.parent_id == category_data.parent_id,
        )
    )
    max_sequence = max_sequence_result.scalar_one_or_none() or 0
    next_sequence = max_sequence + 1

    # 3. Object Creation
    new_category = Category(
        name=category_data.name,
        counter_id=category_data.counter_id,
        parent_id=category_data.parent_id,
        category_sequence=next_sequence,
        created_by=creator.id,
        updated_by=creator.id,
    )

    # 4. Database Commit
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)

    logger.info(f"User '{creator.username}' (ID: {creator.id}) created new category '{new_category.name}' (ID: {new_category.id}).")

    return new_category


async def get_category_tree(
    db: AsyncSession, counter_id: int, creator: User,
) -> List[CategoryNode]:
    """
    Fetches all categories for a counter and builds a recursive tree structure.
    """
    # 1. Hierarchy Validation: Ensure the counter exists and the user has access.
    await get_counter_by_id(db, counter_id, creator)

    # 2. Initial Fetch: Perform a single, efficient query to get all active categories.
    query = (
        select(Category)
        .where(Category.counter_id == counter_id, Category.active == True)
        .order_by(Category.parent_id, Category.category_sequence) # Order for predictable structure
    )
    result = await db.execute(query)
    all_categories = result.scalars().all()

    # 3. In-Memory Processing & Tree Building
    nodes: Dict[int, CategoryNode] = {}
    root_nodes: List[CategoryNode] = []

    # First pass: Create a node for each category and map it by its ID.
    for category in all_categories:
        nodes[category.id] = CategoryNode.from_orm(category)

    # Second pass: Link children to their parents.
    for category in all_categories:
        node = nodes[category.id]
        if category.parent_id and category.parent_id in nodes:
            nodes[category.parent_id].children.append(node)
        else:
            # 4. Identify and collect root nodes.
            root_nodes.append(node)

    return root_nodes
#
# Menu Item Services
#


async def _get_category_with_hierarchy(
    db: AsyncSession, category_id: int
) -> Category:
    """
    Helper to load a category along with its counter and branch hierarchy.
    """
    result = await db.execute(
        select(Category)
        .options(
            selectinload(Category.counter).selectinload(Counter.branch),
        )
        .where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise ItemNotFoundError(f"Category with ID {category_id} not found.")

    if not category.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot attach items to an inactive category.",
        )

    return category


async def _validate_item_access_for_user(menu_item: MenuItem, user: User) -> None:
    """
    Ensure that the given user is allowed to access/modify this item.
    """
    # Product or super admin can access everything
    if user.is_product_admin() or user.is_super_admin():
        return

    # For regular users, enforce hotel-level data segregation.
    # We rely on the category -> counter -> branch hierarchy.
    category = menu_item.category
    if not category or not category.counter or not category.counter.branch:
        # Ensure relationships are loaded; if not, raise a generic error.
        raise DataSegregationError("Unable to resolve hierarchy for this menu item.")

    if category.counter.branch.hotel_id != user.hotel_id:
        raise DataSegregationError(
            "You do not have permission to access this menu item."
        )


async def get_menu_item_by_id(
    db: AsyncSession, item_id: int, requester: User
) -> MenuItem:
    """
    Fetch a single menu item and validate that the requester has access to it.
    """
    result = await db.execute(
        select(MenuItem)
        .options(
            selectinload(MenuItem.category)
            .selectinload(Category.counter)
            .selectinload(Counter.branch)
        )
        .where(MenuItem.id == item_id)
    )
    menu_item = result.scalar_one_or_none()

    if not menu_item:
        raise ItemNotFoundError(f"Menu item with ID {item_id} not found.")

    await _validate_item_access_for_user(menu_item, requester)
    return menu_item


async def create_menu_item(
    db: AsyncSession, item_data: MenuItemCreate, creator: User
) -> MenuItem:
    """
    Creates a new menu item under a specific category.
    """
    # 1. Load and validate category hierarchy
    category = await _get_category_with_hierarchy(db, item_data.category_id)

    # 2. Data segregation check (non-product admins restricted to their hotel)
    if not creator.is_product_admin() and not creator.is_super_admin():
        if category.counter.branch.hotel_id != creator.hotel_id:
            raise DataSegregationError(
                "You can only create items for branches within your own hotel."
            )

    # 3. Validate tax profile, if provided
    if item_data.tax_profile_id is not None:
        tax_result = await db.execute(
            select(TaxProfile).where(TaxProfile.id == item_data.tax_profile_id)
        )
        tax_profile = tax_result.scalar_one_or_none()
        if not tax_profile:
            raise ItemNotFoundError(
                f"Tax profile with ID {item_data.tax_profile_id} not found."
            )

        # Ensure the tax profile belongs to the same branch for non-product admins
        if not creator.is_product_admin() and not creator.is_super_admin():
            if tax_profile.branch_id != category.counter.branch_id:
                raise DataSegregationError(
                    "Tax profile must belong to the same branch as the item's category."
                )

    # 4. Sequence generation within the category
    max_sequence_result = await db.execute(
        select(func.max(MenuItem.item_sequence)).where(
            MenuItem.category_id == category.id
        )
    )
    max_sequence = max_sequence_result.scalar_one_or_none() or 0
    next_sequence = max_sequence + 1

    # 5. Create the menu item
    new_item = MenuItem(
        name=item_data.name,
        description=item_data.description,
        base_price=item_data.base_price,
        item_sequence=next_sequence,
        tags=item_data.tags,
        cooking_instructions=item_data.cooking_instructions,
        image_url=item_data.image_url,
        item_type=item_data.item_type,
        active=item_data.active if item_data.active is not None else True,
        category_id=category.id,
        counter_id=category.counter_id,
        tax_profile_id=item_data.tax_profile_id,
        created_by=creator.id,
        updated_by=creator.id,
    )

    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    logger.info(
        "User '%s' (ID: %s) created new menu item '%s' (ID: %s) in category %s.",
        creator.username,
        creator.id,
        new_item.name,
        new_item.id,
        category.id,
    )

    return new_item


async def update_menu_item(
    db: AsyncSession, item_id: int, update_data: MenuItemUpdate, updater: User
) -> MenuItem:
    """
    Partially updates a menu item's details.
    """
    menu_item = await get_menu_item_by_id(db, item_id, updater)

    update_dict = update_data.model_dump(exclude_unset=True)

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided.",
        )

    # Handle category change (move item to another category)
    if "category_id" in update_dict and update_dict["category_id"] is not None:
        new_category_id = update_dict.pop("category_id")
        new_category = await _get_category_with_hierarchy(db, new_category_id)

        # Data segregation check for the new category
        if not updater.is_product_admin() and not updater.is_super_admin():
            if new_category.counter.branch.hotel_id != updater.hotel_id:
                raise DataSegregationError(
                    "You can only move items within branches of your own hotel."
                )

        # Recompute sequence within the new category
        max_sequence_result = await db.execute(
            select(func.max(MenuItem.item_sequence)).where(
                MenuItem.category_id == new_category.id
            )
        )
        max_sequence = max_sequence_result.scalar_one_or_none() or 0
        menu_item.item_sequence = max_sequence + 1
        menu_item.category_id = new_category.id
        menu_item.counter_id = new_category.counter_id

    # Handle tax profile change
    if "tax_profile_id" in update_dict and update_dict["tax_profile_id"] is not None:
        new_tax_profile_id = update_dict["tax_profile_id"]
        tax_result = await db.execute(
            select(TaxProfile).where(TaxProfile.id == new_tax_profile_id)
        )
        tax_profile = tax_result.scalar_one_or_none()
        if not tax_profile:
            raise ItemNotFoundError(
                f"Tax profile with ID {new_tax_profile_id} not found."
            )

        if not updater.is_product_admin() and not updater.is_super_admin():
            # Use the current (possibly updated) category hierarchy
            category = menu_item.category or await _get_category_with_hierarchy(
                db, menu_item.category_id
            )
            if tax_profile.branch_id != category.counter.branch_id:
                raise DataSegregationError(
                    "Tax profile must belong to the same branch as the item's category."
                )

    # Apply remaining simple field updates
    for key, value in update_dict.items():
        setattr(menu_item, key, value)

    menu_item.updated_by = updater.id

    await db.commit()
    await db.refresh(menu_item)

    logger.info(
        "User '%s' (ID: %s) updated menu item ID %s.",
        updater.username,
        updater.id,
        item_id,
    )

    return menu_item


async def deactivate_menu_item(
    db: AsyncSession, item_id: int, updater: User
) -> MenuItem:
    """
    Soft-deletes a menu item by marking it inactive.
    """
    menu_item = await get_menu_item_by_id(db, item_id, updater)

    if not menu_item.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Menu item is already inactive.",
        )

    menu_item.active = False
    menu_item.updated_by = updater.id

    await db.commit()
    await db.refresh(menu_item)

    logger.warning(
        "User '%s' (ID: %s) deactivated menu item ID %s.",
        updater.username,
        updater.id,
        item_id,
    )

    return menu_item
