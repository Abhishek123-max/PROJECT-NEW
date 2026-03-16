"""Service layer for floor management."""

from typing import Optional, List, Tuple
from fastapi import status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.core.auth import Branch
from app.models.core.floor import Floor
from app.schemas.hotel.floor import FloorCreate, FloorUpdate
from app.models.core.user import User
from app.models.core import Base
from app.utils.exceptions import ValidationError, InsufficientPermissionsError


async def list_floors(
    db: AsyncSession,
    branch_id: int,
    page: int,
    per_page: int,
    assigned_to: Optional[int] = None,
    status: Optional[str] = None,
) -> Tuple[List[Floor], int]:
    """
    Retrieves a paginated and filtered list of floors for a given branch.

    Args:
        db: The database session.
        branch_id: The ID of the branch to retrieve floors for.
        page: The page number for pagination.
        per_page: The number of items per page.
        assigned_to: Optional user ID to filter floors by floor_manager_id.
        status: Optional status to filter floors by ('active' or 'inactive').

    Returns:
        A tuple containing the list of Floor objects and the total count.
    """
    query = select(Floor).where(Floor.branch_id == branch_id)

    # Apply filters conditionally
    if assigned_to is not None:
        query = query.where(Floor.floor_manager_id == assigned_to)

    if status is not None:
        if status == "active":
            query = query.where(Floor.is_active == True)
        elif status == "inactive":
            query = query.where(Floor.is_active == False)

    # Get the total count of items matching the filters
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination and ordering, with eager loading of floor_managers
    offset = (page - 1) * per_page
    paged_query = (
        query.options(selectinload(Floor.floor_managers))
        .order_by(Floor.floor_sequence)
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(paged_query)
    floors = result.scalars().all()

    return floors, total

async def create_floor(
    db: AsyncSession,
    branch_sequence: int,
    floor_data: FloorCreate,
    current_user: User,
) -> Floor:
    """
    Creates a new floor within a specific branch, ensuring hierarchy,
    concurrency safety, and multi-tenant manager assignment.
    """
    from app.services.hotel.branch import get_branch_by_sequence_and_creator
    from app.models.core.floor_manager import FloorManager
    from app.models.core.user import User as UserModel

    # 1. Hierarchy validation (tenant-safe)
    branch = await get_branch_by_sequence_and_creator(db, branch_sequence, current_user)
    if not branch:
        raise ValueError("Branch not found or access denied.")

    # 2. Concurrency-safe lock
    await db.refresh(branch, with_for_update=True)

    # 3. Calculate next floor sequence
    max_sequence_result = await db.execute(
        select(func.max(Floor.floor_sequence)).where(
            Floor.branch_id == branch.id,
            Floor.hotel_id == current_user.hotel_id,
        )
    )
    max_sequence = max_sequence_result.scalar_one_or_none() or 0

    # 3a. Check for duplicate floor name in this branch (and hotel)
    name_exists_stmt = select(Floor.id).where(
        Floor.branch_id == branch.id,
        Floor.hotel_id == current_user.hotel_id,
        func.lower(Floor.floor_name) == func.lower(floor_data.floor_name),
    )
    if (await db.execute(name_exists_stmt)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Floor name already exists in this branch.",
        )

    # 4. Create Floor (exclude manager IDs)
    new_floor = Floor(
        floor_number=floor_data.floor_number,
        floor_name=floor_data.floor_name,
        is_active=floor_data.is_active,
        hotel_id=current_user.hotel_id,
        branch_id=branch.id,
        floor_sequence=max_sequence + 1,
        created_by=current_user.id,
    )

    db.add(new_floor)
    await db.flush()  # IMPORTANT: get new_floor.id without committing

    # 5. Validate & assign managers (tenant-safe)
    if floor_data.floor_manager_ids:
        # Validate users belong to same hotel
        result = await db.execute(
            select(UserModel.id).where(
                UserModel.id.in_(floor_data.floor_manager_ids),
                UserModel.hotel_id == current_user.hotel_id,
                UserModel.is_active.is_(True),
            )
        )
        valid_user_ids = set(result.scalars().all())

        invalid_ids = set(floor_data.floor_manager_ids) - valid_user_ids
        if invalid_ids:
            raise ValueError(f"Invalid or cross-hotel user IDs: {invalid_ids}")

        # Insert into mapping table
        for user_id in valid_user_ids:
            db.add(FloorManager(
                hotel_id=current_user.hotel_id,
                floor_id=new_floor.id,
                user_id=user_id
            ))

    # 6. Commit transaction
    await db.commit()
    await db.refresh(new_floor)
    # Eagerly load the floor_managers relationship to avoid MissingGreenlet when serializing with Pydantic
    await db.refresh(new_floor, attribute_names=["floor_managers"])

    return new_floor


async def get_floor_by_id(
    db: AsyncSession, branch_id: int, floor_id: int, current_user: User
) -> Optional[Floor]:
    """
    Retrieves a single floor by its ID, ensuring it belongs to the correct branch
    and the current user's hotel.
    """
    from app.services.hotel.branch import get_branch_by_id
    
    # Securely get the branch first
    branch = await get_branch_by_id(db, branch_id)
    if not branch:
        # This should ideally be handled by the caller with an HTTPException
        # but for internal service calls, returning None is acceptable.
        return None

    floor_query = (
        select(Floor)
        .options(selectinload(Floor.floor_managers))
        .where(
            Floor.id == floor_id,
            Floor.branch_id == branch.id,
            Floor.is_active == True # Only retrieve active floors by default
        )
    )
    result = await db.execute(floor_query)
    floor = result.scalar_one_or_none()
    
    # Eagerly load the floor_managers relationship to avoid MissingGreenlet when serializing with Pydantic
    if floor:
        await db.refresh(floor, attribute_names=["floor_managers"])
    
    return floor


async def update_floor(db: AsyncSession, floor: Floor, update_data: FloorUpdate, current_user: User) -> Floor:
    """Updates an existing floor and managers (mirroring create flow)."""
    from app.models.core.floor_manager import FloorManager
    from app.models.core.user import User as UserModel

    update_dict = update_data.dict(exclude_unset=True)

    # Update basic fields
    for key in ['floor_name', 'floor_number', 'is_active']:
        if key in update_dict:
            setattr(floor, key, update_dict[key])

    # Update floor managers if present
    if 'floor_manager_ids' in update_dict:
        # Remove all existing managers for this floor
        await db.execute(
            FloorManager.__table__.delete().where(FloorManager.floor_id == floor.id)
        )
        user_ids = update_dict['floor_manager_ids']
        if user_ids:
            # Validate user IDs
            result = await db.execute(
                select(UserModel.id).where(
                    UserModel.id.in_(user_ids),
                    UserModel.hotel_id == current_user.hotel_id,
                    UserModel.is_active.is_(True),
                )
            )
            valid_user_ids = set(result.scalars().all())
            invalid_ids = set(user_ids) - valid_user_ids
            if invalid_ids:
                raise ValueError(f"Invalid or cross-hotel user IDs: {invalid_ids}")
            for user_id in valid_user_ids:
                db.add(FloorManager(hotel_id=current_user.hotel_id, floor_id=floor.id, user_id=user_id))
    await db.commit()
    await db.refresh(floor)
    await db.refresh(floor, attribute_names=["floor_managers"])
    return floor


async def delete_floor(db: AsyncSession, floor: Floor, current_user: User) -> None:
    """Soft-deletes a floor by setting is_active to False."""
    floor.is_active = False
    floor.updated_by = current_user.id # Set updated_by for soft delete
    await db.commit()
    return

async def delete_floors(db: AsyncSession, floor: Floor, current_user: User) -> None:
    """deletes a floor by setting is_active to False."""
    await db.delete(floor)
    await db.commit()
    return