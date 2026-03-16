"""Service layer for section management."""

from typing import List, Optional, Tuple, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from fastapi import HTTPException, status
from app.models.core.auth import Branch
from app.models.core.hall import Hall
from app.models.core.section import Section
from app.models.core.user import User
from app.schemas.hotel.section import SectionCreate, SectionUpdate
from app.models.core.floor import Floor # New import for Floor model
from app.models.core.table import Table

MAX_SECTIONS_PER_HALL = 4
async def create_section_service(
    db: AsyncSession,
    section_data: SectionCreate,
    branch_id: int,
    floor_id: int,
    hall_id: int,
    current_user: User,
) -> Section:
    """
    Creates a new section within a specific hall, ensuring hierarchy and concurrency safety.
    """
    try:
        table_ids: List[int] = section_data.tables or []

        # 1. Hierarchy Validation: Find the parent Hall securely.
        hall_query = (
            select(Hall)
            .join(Floor, Hall.floor_id == Floor.id)
            .join(Branch, Floor.branch_id == Branch.id)
            .where(
                Branch.id == branch_id,
                Floor.id == floor_id,
                Hall.id == hall_id,
                Branch.is_active == True,
                Floor.is_active == True,
                Hall.is_active == True,
            )
        )
        hall_result = await db.execute(hall_query)
        target_hall = hall_result.scalar_one_or_none()

        if not target_hall:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hall not found in the specified hierarchy.")


         # 2️⃣ Enforce max section count (COUNT, not MAX)
        count_query = select(func.count(Section.id)).where(
            Section.hall_id == target_hall.id
        )
        section_count = (await db.execute(count_query)).scalar_one()

        if section_count >= MAX_SECTIONS_PER_HALL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of sections (4) for this hall has been reached.",
            )

        # 2. Concurrency-Safe Sequencing: Lock the parent hall to prevent race conditions.
        await db.refresh(target_hall, with_for_update=True)

        max_seq_query = select(func.max(Section.section_sequence)).where(Section.hall_id == target_hall.id)
        max_sequence = (await db.execute(max_seq_query)).scalar_one_or_none() or 0
        next_sequence = max_sequence + 1

        stmt = select(Section.id).where(
        Section.hall_id == target_hall.id,
        Section.section_name == section_data.section_name,
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section name already exists in this hall.")
      
        # 4️⃣ Find first available sequence (gap-based)
        seq_query = (
            select(Section.section_sequence)
            .where(Section.hall_id == target_hall.id)
            .order_by(Section.section_sequence)
            .with_for_update()
        )

        existing_sequences = [
            row[0] for row in (await db.execute(seq_query)).all()
        ]

        next_sequence = 1
        for seq in existing_sequences:
            if seq == next_sequence:
                next_sequence += 1
            elif seq > next_sequence:
                break
        # 4. Creation: Instantiate the new Section model.
        section_dict = section_data.model_dump(exclude={"tables"})
        
        new_section = Section(
            **section_dict,
            hall_id=target_hall.id,
            section_sequence=next_sequence,
        )
        db.add(new_section)

        # Flush to obtain section ID without committing transaction yet
        await db.flush()

        # 5. Assign tables to this section if provided
        if table_ids:
            tables_query = select(Table.id).where(
                Table.id.in_(table_ids),
                Table.branch_id == branch_id,
                Table.floor_id == floor_id,
                Table.hall_id == hall_id,
            )
            result = await db.execute(tables_query)
            found_ids = {row[0] for row in result.all()}
            missing_ids = set(table_ids) - found_ids

            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tables not found in the specified hierarchy: {sorted(missing_ids)}",
                )

            await db.execute(
                update(Table)
                .where(Table.id.in_(table_ids))
                .values(section_id=new_section.id, updated_by=current_user.id)
            )

        await db.commit()
        
        await db.refresh(new_section)
        return new_section
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise


async def list_sections_service(
    db: AsyncSession,
    branch_id: int,
    floor_id: int,
    hall_id: int,
    current_user: User,
    page: int,
    per_page: int,
    assigned_to: Optional[int] = None,
    section_status: Optional[str] = None,
) -> Tuple[Sequence[Section], int]:
    """
    Lists all sections in a specific hall with filtering and pagination.
    - Filters by user assignment (via tables).
    - Filters by active/inactive status.
    - Paginates the results.
    """
    # Hierarchy Validation: Find the parent Hall securely.
    hall_query = (
        select(Hall.id)
        .join(Floor, Hall.floor_id == Floor.id)
        .join(Branch, Floor.branch_id == Branch.id)
        .where(
            Branch.id == branch_id,
            Floor.id == floor_id,
            Hall.id == hall_id,
            Branch.is_active == True,
            Floor.is_active == True,
            Hall.is_active == True,
        )
    )
    target_hall_id = (await db.execute(hall_query)).scalar_one_or_none()

    if not target_hall_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hall not found in the specified hierarchy.")

    # Base query for sections in the target hall
    query = select(Section).where(Section.hall_id == target_hall_id)

    # Apply filters conditionally
    if assigned_to is not None:
        # Join with Table to filter by table assignment
        from app.models.core.table import Table
        query = (
            query.join(Table, Section.id == Table.section_id)
            .where(Table.assigned_to == assigned_to)
            .distinct()  # Use distinct to avoid duplicate sections
        )

    # Default to 'active' if no status is provided, to maintain original behavior
    status_filter = section_status or "active"
    if status_filter != "all":
        is_active_flag = True if status_filter == "active" else False
        query = query.where(Section.is_active == is_active_flag)

    # Get the total count of items matching the filters
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination and ordering
    offset = (page - 1) * per_page
    paged_query = query.order_by(Section.section_sequence).offset(offset).limit(per_page)
    result = await db.execute(paged_query)
    sections = result.scalars().all()

    return sections, total


async def get_section_service(
    db: AsyncSession, branch_id: int, floor_id: int, hall_id: int, section_sequence_id: int, current_user: User
) -> Section:
    """
    Gets a single active section by its sequence IDs.
    """
    section_query = (
        select(Section)
        .join(Hall, Section.hall_id == Hall.id)
        .join(Floor, Hall.floor_id == Floor.id)
        .join(Branch, Floor.branch_id == Branch.id)
        .where(
            Branch.id == branch_id,
            Floor.id == floor_id,
            Hall.id == hall_id,
            Section.section_sequence == section_sequence_id,
            Section.is_active == True,
        )
    )
    section_result = await db.execute(section_query)
    section = section_result.scalar_one_or_none()

    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")

    return section


async def update_section_service(
    db: AsyncSession,
    branch_id: int,
    floor_id: int,
    hall_id: int,
    section_sequence_id: int,
    update_data: SectionUpdate,
    current_user: User,
) -> Section:
    """
    Updates a section's details.
    """
    section_to_update = await get_section_service(
        db, branch_id, floor_id, hall_id, section_sequence_id, current_user
    )

    # Separate scalar updates from table assignment
    table_ids: Optional[List[int]] = update_data.tables
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"tables"})
    if not update_dict:
        # Allow requests that only update table assignments (no scalar fields)
        if table_ids is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided.",
            )

    for key, value in update_dict.items():
        setattr(section_to_update, key, value)

    # If tables list is provided, (re)assign those tables to this section
    if table_ids is not None:
        # Validate tables belong to this hierarchy
        tables_query = select(Table.id).where(
            Table.id.in_(table_ids),
            Table.branch_id == branch_id,
            Table.floor_id == floor_id,
            Table.hall_id == hall_id,
        )
        result = await db.execute(tables_query)
        found_ids = {row[0] for row in result.all()}
        missing_ids = set(table_ids) - found_ids

        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tables not found in the specified hierarchy: {sorted(missing_ids)}",
            )

        # Assign the specified tables to this section (does not clear previous tables)
        await db.execute(
            update(Table)
            .where(Table.id.in_(table_ids))
            .values(section_id=section_to_update.id, updated_by=current_user.id)
        )

    await db.commit()
    await db.refresh(section_to_update)
    return section_to_update


async def delete_section_service_isactive(
    db: AsyncSession, branch_id: int, floor_id: int, hall_id: int, section_sequence_id: int, current_user: User
) -> None:
    """
    Deactivates a section (soft delete).
    """
    section_to_deactivate = await get_section_service(db, branch_id, floor_id, hall_id, section_sequence_id, current_user)

    section_to_deactivate.is_active = False  # type: ignore[assignment]
    await db.commit()

async def delete_section_service(
    db: AsyncSession, branch_id: int, floor_id: int, hall_id: int, section_sequence_id: int, current_user: User
) -> None:
    """
    Deactivates a section (soft delete).
    """
    section_to_delete = await get_section_service(db, branch_id, floor_id, hall_id, section_sequence_id, current_user)

    await db.delete(section_to_delete)
    await db.commit()