"""Service layer for hall management."""

from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from app.models.core.auth import Branch
from app.models.core.hall import Hall
from app.models.core.section import Section
from app.models.core.table import Table, table_assignees # Import table_assignees for many-to-many relationship
from app.services.hotel.branch import get_branch_by_sequence_and_creator
from app.models.core.user import User
from app.schemas.hotel.hall import HallCreate, HallUpdate

from app.models.core.floor import Floor # New import for Floor model

async def list_halls(
    db: AsyncSession,
    floor_id: int,
    page: int,
    per_page: int,
    assigned_to: Optional[int] = None,
    status: Optional[str] = None,
    current_user: Optional[User] = None, # Added for security context
) -> Tuple[List[Hall], int]:
    """
    Retrieves a paginated and filtered list of halls for a given floor.

    Args:
        db: The database session.
        floor_id: The ID of the floor to retrieve halls for.
        page: The page number for pagination.
        per_page: The number of items per page.
        assigned_to: Optional user ID to filter halls by table assignment.
        status: Optional status to filter halls by ('active' or 'inactive').

    Returns:
        A tuple containing the list of Hall objects and the total count.
    """
    query = select(Hall).where(Hall.floor_id == floor_id)

    # Apply filters conditionally
    if assigned_to is not None:
        # Join through Section, Table, and table_assignees to filter by table assignment
        # Tables now use a many-to-many relationship through table_assignees
        query = (
            query.join(Section, Hall.id == Section.hall_id)
            .join(Table, Section.id == Table.section_id)
            .join(table_assignees, Table.id == table_assignees.c.table_id)
            .where(table_assignees.c.user_id == assigned_to)
            .distinct()  # Use distinct to avoid duplicate halls
        )

    if status is not None:
        if status == "active":
            query = query.where(Hall.is_active == True)
        elif status == "inactive":
            query = query.where(Hall.is_active == False)

    # Get the total count of items matching the filters
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination and ordering
    offset = (page - 1) * per_page
    paged_query = (
        query.order_by(Hall.hall_sequence).offset(offset).limit(per_page)
    )
    result = await db.execute(paged_query)
    halls = result.scalars().all()

    return halls, total


async def create_hall_service(
    db: AsyncSession,
    hall_data: HallCreate,
    branch_id: int,
    floor_id: int,
    current_user: User,
) -> Hall:
    """
    Creates a new hall within a specific floor, ensuring hierarchy and concurrency safety.
    """
    # 1. Hierarchy Validation: Find the parent Floor securely.
    floor_query = (
        select(Floor)
        .join(Branch, and_(Floor.branch_id == Branch.id, Branch.id == branch_id, Branch.hotel_id == current_user.hotel_id))
        .where(
            Floor.id == floor_id,
            Branch.is_active == True,
            Floor.is_active == True,
        )
    )
    floor_result = await db.execute(floor_query)
    target_floor = floor_result.scalar_one_or_none()

    if not target_floor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor not found in the specified hierarchy.")

    # 2. Concurrency-Safe Sequencing: Lock the parent floor to prevent race conditions.
    await db.refresh(target_floor, with_for_update=True)

    max_seq_query = select(func.max(Hall.hall_sequence)).where(Hall.floor_id == target_floor.id)
    max_sequence = (await db.execute(max_seq_query)).scalar_one_or_none() or 0
    next_sequence = max_sequence + 1

    # 3. Business Rule: Enforce a maximum of 4 halls per floor.
    if next_sequence > 20:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum number of halls (4) for this floor has been reached.")

    # 4. Creation: Instantiate the new Hall model.
    new_hall = Hall(
        **hall_data.model_dump(),
        floor_id=target_floor.id,
        hall_sequence=next_sequence,
        created_by=current_user.id,
    )
    db.add(new_hall)
    await db.commit()
    await db.refresh(new_hall)
    return new_hall


async def get_hall_service(
    db: AsyncSession, branch_id: int, floor_id: int, hall_id: int, current_user: User
) -> Hall:
    """
    Gets a single active hall by its sequence IDs.
    """
    hall_query = (
        select(Hall)
        .join(Floor, and_(Hall.floor_id == Floor.id, Floor.id == floor_id))
        .join(Branch, and_(Floor.branch_id == Branch.id, Branch.id == branch_id, Branch.hotel_id == current_user.hotel_id))
        .where(
            Hall.id == hall_id,
            Hall.is_active == True,
        )
    )
    hall_result = await db.execute(hall_query)
    hall = hall_result.scalar_one_or_none()

    if not hall:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hall not found.")

    return hall


async def update_hall_service(
    db: AsyncSession,
    hall_to_update: Hall, # Changed to accept Hall object
    update_data: HallUpdate,
    current_user: User,
) -> Hall:
    """
    Updates a hall's details.
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    for key, value in update_dict.items():
        setattr(hall_to_update, key, value)

    hall_to_update.updated_by = current_user.id

    await db.commit()
    await db.refresh(hall_to_update)
    return hall_to_update


async def delete_hall_services(db: AsyncSession, hall: Hall, current_user: User) -> None:
    """Soft-deletes a hall by setting is_active to False."""
    hall.is_active = False
    hall.updated_by = current_user.id
    await db.commit()


async def delete_hall_service(
    db: AsyncSession,
    hall: Hall,
    current_user: User,
) -> None:
    """
    Deletes a hall from the database.
    """
    await db.delete(hall)
    await db.commit()


async def get_hall_service_without_active_filter(
    db: AsyncSession, branch_id: int, floor_id: int, hall_id: int, current_user: User
) -> Hall:
    """
    Gets a single hall by its sequence IDs without filtering by is_active.
    Used for status updates where we need to access inactive halls.
    """
    hall_query = (
        select(Hall)
        .join(Floor, and_(Hall.floor_id == Floor.id, Floor.id == floor_id))
        .join(Branch, and_(Floor.branch_id == Branch.id, Branch.id == branch_id, Branch.hotel_id == current_user.hotel_id))
        .where(
            Hall.id == hall_id,
        )
    )
    hall_result = await db.execute(hall_query)
    hall = hall_result.scalar_one_or_none()

    if not hall:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hall not found.")

    return hall


async def toggle_hall_status_service(
    db: AsyncSession,
    hall: Hall,
    is_active: bool,
    current_user: User,
) -> Hall:
    """
    Toggles a hall's is_active status.
    """
    hall.is_active = is_active
    hall.updated_by = current_user.id
    await db.commit()
    await db.refresh(hall)
    return hall