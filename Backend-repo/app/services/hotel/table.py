"""Service layer for table management."""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.core.auth import Branch
from app.models.core.hall import Hall
from app.models.core.section import Section
from app.models.core.table import Table
from app.models.core.user import User 
from app.schemas.hotel.table import TableCreate, TableUpdate, TableShift, TableStatus
from app.services.hotel.branch import get_branch_by_id
from app.models.core.floor import Floor # New import for Floor model


async def _get_and_lock_parent(db: AsyncSession, floor_id: int, hall_id: Optional[int], section_id: Optional[int]) -> Tuple[object, str, int]:
    """
    Identifies, fetches, and locks the direct parent entity (Floor, Hall, or Section).
    Returns the parent object, the parent type as a string, and the parent ID.
    """
    if section_id:
        parent = await db.get(Section, section_id)
        parent_type = "section_id"
    elif hall_id:
        parent = await db.get(Hall, hall_id)
        parent_type = "hall_id"
    else:
        parent = await db.get(Floor, floor_id)
        parent_type = "floor_id"

    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent floor, hall, or section not found.")

    # This is the critical step for concurrency safety.
    await db.refresh(parent, with_for_update=True)
    return parent, parent_type, parent.id


async def create_table_service(
    db: AsyncSession,
    table_data: TableCreate,
    branch_id: int,
    current_user: User,
) -> Table:
    """
    Creates a new table, ensuring hierarchy, data segregation, and concurrency safety.
    """
    # 1. Hierarchy & Ownership Validation
    branch = await get_branch_by_id(db, branch_id)
    if not branch or branch.hotel_id != current_user.hotel_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branch with ID {branch_id} not found in your hotel.")

    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branch with ID {branch_id} not found in your hotel.")

    # Validate floor belongs to the branch
    floor = await db.get(Floor, table_data.floor_id)
    if not floor or floor.branch_id != branch.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Floor ID {table_data.floor_id} does not belong to branch {branch.name}.")

    # Validate hall (if provided) belongs to the floor
    if table_data.hall_id:
        hall = await db.get(Hall, table_data.hall_id)
        if not hall or hall.floor_id != floor.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Hall ID {table_data.hall_id} does not belong to floor {floor.floor_name}.")

    # Validate section (if provided) belongs to the hall
    if table_data.section_id:
        if not table_data.hall_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A hall_id must be provided when specifying a section_id.")
        section = await db.get(Section, table_data.section_id)
        if not section or section.hall_id != table_data.hall_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Section ID {table_data.section_id} does not belong to hall ID {table_data.hall_id}.")

    # 2. Parent Identification and Concurrency-Safe Sequencing
    parent, parent_type, parent_id = await _get_and_lock_parent(db, table_data.floor_id, table_data.hall_id, table_data.section_id)

    # 3. Sequence Calculation
    max_seq_query = select(func.max(Table.table_sequence)).where(getattr(Table, parent_type) == parent_id)
    max_sequence = (await db.execute(max_seq_query)).scalar_one_or_none() or 0
    next_sequence = max_sequence + 1

    # 4. Business Rule for the tables apis
    if next_sequence > 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum number of tables (4) for this parent has been reached.")

    # 5. Creation (assignees assigned BEFORE add/commit)
    new_table = Table(
        **table_data.model_dump(exclude={"status", "assigned_to"}),
        status=table_data.status.value,
        branch_id=branch.id,
        table_sequence=next_sequence,
        created_by=current_user.id
    )
    # Assign users before add/commit!
    if table_data.assigned_to:
        users = (await db.execute(
            select(User).where(
                User.id.in_(table_data.assigned_to),
                User.hotel_id == current_user.hotel_id
            )
        )).scalars().all()
        if len(users) != len(table_data.assigned_to):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more assigned users not found or do not belong to your hotel."
            )
        new_table.assignees = users
    db.add(new_table)
    await db.commit()
    # Re-fetch with assignees loaded so response shows assigned_to correctly.
    table_query = (
        select(Table)
        .options(selectinload(Table.assignees))
        .where(Table.id == new_table.id)
    )
    return (await db.execute(table_query)).scalar_one()


async def get_table_service(db: AsyncSession, branch_id: int, table_id: int, current_user: User) -> Table:
    """
    Gets a single active table by its primary key ID, ensuring it belongs to the correct branch.
    """
    branch = await get_branch_by_id(db, branch_id)
    if not branch or branch.hotel_id != current_user.hotel_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branch with ID {branch_id} not found in your hotel.")
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branch with ID {branch_id} not found in your hotel.")

    table_query = select(Table).options(selectinload(Table.assignees)).where(
        Table.id == table_id,
        Table.branch_id == branch.id,
        Table.is_active == True
    )
    table = (await db.execute(table_query)).scalar_one_or_none()

    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found.")

    return table


async def list_tables_service(
    db: AsyncSession,
    branch_id: int,
    current_user: User,
    page: int,
    per_page: int,
    assigned_to: Optional[int] = None,
    table_status: Optional[TableStatus] = None,
) -> Tuple[List[Table], int]:
    """
    Lists tables in a specific branch with filtering and pagination.
    """
    branch = await get_branch_by_id(db, branch_id)
    if not branch or branch.hotel_id != current_user.hotel_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branch with ID {branch_id} not found in your hotel.")
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branch with ID {branch_id} not found in your hotel.")

    query = select(Table).options(selectinload(Table.assignees)).where(Table.branch_id == branch.id)

    # Apply filters conditionally
    if assigned_to is not None:
        # Filter through the many-to-many relationship
        query = query.join(Table.assignees).where(User.id == assigned_to).distinct()

    if table_status is not None and table_status.value != "all":
        query = query.where(Table.status == table_status.value)

    # Get the total count of items matching the filters
    # Use distinct count when filtering by assigned_to
    if assigned_to is not None:
        count_query = select(func.count()).select_from(query.distinct().subquery())
    else:
        count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination and ordering
    offset = (page - 1) * per_page
    paged_query = query.order_by(Table.floor_id, Table.hall_id, Table.section_id, Table.table_sequence).offset(offset).limit(per_page)
    result = await db.execute(paged_query)
    tables = result.scalars().unique().all()

    return tables, total


async def update_table_service(
    db: AsyncSession,
    branch_id: int,
    table_id: int,
    update_data: TableUpdate,
    current_user: User,
) -> Table:
    """
    Updates a table's details. Does not handle shifting parents.
    Handles assignees relationship updates separately.
    """
    table_to_update = await get_table_service(db, branch_id, table_id, current_user)

    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    # Handle assignees separately (many-to-many relationship)
    assigned_to_ids = update_dict.pop("assigned_to", None)
    
    if assigned_to_ids is not None:
        # Validate that all users exist and belong to the same hotel/branch
        users = (await db.execute(
            select(User).where(
                User.id.in_(assigned_to_ids),
                User.hotel_id == current_user.hotel_id
            )
        )).scalars().all()
        if len(users) != len(assigned_to_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more assigned users not found or do not belong to your hotel."
            )
        table_to_update.assignees = users
        table_to_update.assigned_to = assigned_to_ids

    if "status" in update_dict:
        update_dict["status"] = update_dict["status"].value

    # Update other fields
    for key, value in update_dict.items():
        setattr(table_to_update, key, value)

    table_to_update.updated_by = current_user.id

    await db.commit()
    return table_to_update


async def delete_table_service(
    db: AsyncSession, branch_id: int, table_id: int, current_user: User
) -> None:
    """
    Permanently deletes a table from the database.
    """
    table_to_delete = await get_table_service(db, branch_id, table_id, current_user)

    # Hard delete the table row
    await db.delete(table_to_delete)
    await db.commit()


async def shift_table_service(
    db: AsyncSession,
    branch_id: int,
    table_id: int,
    shift_data: TableShift,
    current_user: User,
) -> Table:
    """
    Shifts a table to a new parent (Floor, Hall, or Section) and re-sequences it.
    This is a transaction-safe operation with row-level locking.
    """
    # 1. Find and Lock the table to be moved
    branch = await get_branch_by_id(db, branch_id)
    if not branch or branch.hotel_id != current_user.hotel_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branch with ID {branch_id} not found in your hotel.")
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branch with ID {branch_id} not found in your hotel.")

    table_to_shift_query = select(Table).options(selectinload(Table.assignees)).where(Table.id == table_id).with_for_update()
    table_to_shift = (await db.execute(table_to_shift_query)).scalar_one_or_none()
    if not table_to_shift or table_to_shift.branch_id != branch.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found in this branch.")

    # 2. Validate and Lock the new parent hierarchy
    new_floor = await db.get(Floor, shift_data.floor_id)
    if not new_floor or new_floor.branch_id != branch.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New floor not found in this branch.")

    if shift_data.hall_id:
        new_hall = await db.get(Hall, shift_data.hall_id)
        if not new_hall or new_hall.floor_id != new_floor.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New hall not found on the specified floor.")

    if shift_data.section_id:
        if not shift_data.hall_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A hall_id must be provided when specifying a section_id.")
        new_section = await db.get(Section, shift_data.section_id)
        if not new_section or new_section.hall_id != shift_data.hall_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New section not found in the specified hall.")

    # 3. Get and lock the new direct parent
    _, new_parent_type, new_parent_id = await _get_and_lock_parent(db, shift_data.floor_id, shift_data.hall_id, shift_data.section_id)

    # 4. Calculate New Sequence under the new parent
    max_seq_query = select(func.max(Table.table_sequence)).where(getattr(Table, new_parent_type) == new_parent_id)
    max_sequence = (await db.execute(max_seq_query)).scalar_one_or_none() or 0
    next_sequence = max_sequence + 1

    if next_sequence > 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum number of tables (4) for the new parent has been reached.")

    # 5. Update the table's foreign keys and sequence
    table_to_shift.floor_id = shift_data.floor_id
    table_to_shift.hall_id = shift_data.hall_id
    table_to_shift.section_id = shift_data.section_id
    table_to_shift.table_sequence = next_sequence
    table_to_shift.updated_by = current_user.id

    # The transaction will be committed by the get_db_session context manager
    await db.commit()
    return table_to_shift
