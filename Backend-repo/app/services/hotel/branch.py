"""Service layer for hotel and branch management."""

import time
import logging
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.models.core.auth import Hotel, Branch, Role
from app.models.core.floor import Floor
from app.models.core.user import User
from app.models.core.audit import AuditLog
# Import for new branch APIs and the legacy onboarding function
from app.schemas.hotel.branch import BranchCreate, BranchUpdate, BranchResponse
from app.schemas.core.branch import HotelOnboardingUpdate, HotelOnboardingResponse, HotelOnboardingData
from app.schemas.core.notification import NotificationCreate
from app.services.core.notification_service import create_and_broadcast_notification
from app.utils.exceptions import InsufficientPermissionsError, DataSegregationError
from app.services.core.storage_service import storage_service
from app.settings.base import get_settings
from app.settings.constants import (
    RoleNames,
    DEFAULT_CAN_CREATE_ROLES,
    DEFAULT_ROLE_FEATURES,
    get_role_level,
    page_permissions_for_role,
)
from fastapi import UploadFile, HTTPException, status

logger = logging.getLogger(__name__)


class OnboardingIncompleteError(Exception):
    """Custom exception for when hotel onboarding is not complete."""
    pass


async def _ensure_default_roles_for_hotel(
    db: AsyncSession,
    hotel: Hotel,
    current_user: User,
) -> None:
    """
    Ensure that a default set of roles exists for the given hotel.

    Roles are created per-hotel (scoped by hotel_id) using the defaults
    defined in settings.constants, but marked as non-system (is_default=False)
    so they can be customized later if needed.
    """
    # We don't create a product_admin per hotel; that is a global/system role.
    per_hotel_roles = [
        RoleNames.ADMIN,
        RoleNames.MANAGER,
        RoleNames.CASHIER,
        RoleNames.KITCHEN_STAFF,
        RoleNames.WAITERS,
        RoleNames.INVENTORY_MANAGER,
        RoleNames.HOUSEKEEPING,
    ]

    for role_name in per_hotel_roles:
        # Check if a role with this name already exists for the hotel
        result = await db.execute(
            select(Role).where(
                Role.name == role_name,
                Role.hotel_id == hotel.id,
            )
        )
        existing_role = result.scalar_one_or_none()
        if existing_role:
            continue

        level = get_role_level(role_name)
        permissions = page_permissions_for_role(role_name=role_name)
        can_create = DEFAULT_CAN_CREATE_ROLES.get(role_name, [])
        default_features = DEFAULT_ROLE_FEATURES.get(role_name, {})

        new_role = Role(
            name=role_name,
            display_name=role_name.replace("_", " ").title(),
            description=f"Default {role_name.replace('_', ' ').title()} role for hotel {hotel.name}.",
            hotel_id=hotel.id,
            level=level,
            permissions=permissions,
            can_create_roles=can_create,
            default_features=default_features,
            is_default=True,
            created_by=current_user.id,
        )
        db.add(new_role)

    # Flush so that any created roles are persisted before commit in the caller.
    await db.flush()


async def get_branch_by_id(db: AsyncSession, branch_id: int) -> Optional[Branch]:
    """
    Fetches a branch by its primary key ID.

    Args:
        db: The database session.
        branch_id: The ID of the branch to fetch.

    Returns:
        The Branch object or None if not found.
    """
    return await db.get(Branch, branch_id)

async def get_branch_by_id_and_creator(db: AsyncSession, branch_id: int, creator: User) -> Optional[Branch]:
    """
    Fetches a branch by its primary key ID.

    Args:
        db: The database session.
        branch_id: The ID of the branch to fetch.

    Returns:
        The Branch object or None if not found.
    """
    if creator.hotel_id is None:
        raise DataSegregationError("User must be associated with a hotel to access branches.")

    hotel_id = creator.hotel_id
    result = await db.execute(
        select(Branch).filter_by(hotel_id=hotel_id, id=branch_id)
    )
    return result.scalar_one_or_none()

async def get_branch_by_sequence_and_creator(db: AsyncSession, branch_sequence: int, creator: User) -> Optional[Branch]:
    """
    Fetches a branch by its sequence ID, ensuring it belongs to the creator's hotel.

    Args:
        db: The database session.
        branch_sequence: The sequence number of the branch within the hotel.
        creator: The user making the request (for data segregation).

    Returns:
        The Branch object or None if not found.
    """
    if creator.hotel_id is None:
        raise DataSegregationError("User must be associated with a hotel to access branches.")

    hotel_id = creator.hotel_id

    result = await db.execute(
        select(Branch).filter_by(hotel_id=hotel_id, branch_sequence=branch_sequence)
    )
    return result.scalar_one_or_none()


async def get_hotel_for_onboarding(db: AsyncSession, hotel_id: int, current_user: User) -> Hotel:
    """
    Fetches a hotel for onboarding, ensuring the user has the correct permissions.

    Args:
        db: The database session.
        hotel_id: The ID of the hotel to fetch.
        current_user: The user making the request.

    Returns:
        The fetched Hotel object.
    """
    if not current_user.is_super_admin():
        raise InsufficientPermissionsError("Only Super Admins can access onboarding information.")
    if current_user.hotel_id is None or current_user.hotel_id != hotel_id:
        raise DataSegregationError("You can only access onboarding information for your own hotel.")

    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found.")

    return hotel


async def update_hotel_onboarding(
    db: AsyncSession,
    hotel_id: int,
    onboarding_data: Dict[str, Any],
    logo: Optional[UploadFile],
    current_user: User, client_ip: str,
) -> HotelOnboardingResponse:
    """
    Updates hotel details from the onboarding form and marks onboarding as complete.

    Args:
        db: The database session.
        hotel_id: The ID of the hotel to update.
        onboarding_data: A dictionary of the new data from the onboarding form.
        logo: The optional logo file to upload.
        current_user: The user making the request.
        client_ip: The IP address of the user.

    Returns:
        A response object containing the success status and the updated hotel data.
    """
    hotel = await get_hotel_for_onboarding(db, hotel_id, current_user)

    settings = get_settings()
    storage_is_configured = settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.S3_BUCKET_NAME

    # Handle logo upload first
    if logo:
        if storage_is_configured:
            # Validate file type and size
            if logo.content_type not in ["image/jpeg", "image/png", "image/gif"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only JPG, PNG, and GIF are allowed.")
            
            # --- Robustness Improvement: Add a file size limit (e.g., 2MB) ---
            MAX_FILE_SIZE = 5 * 1024 * 1024  # 2 MB
            size = await logo.read()
            if len(size) > MAX_FILE_SIZE:
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Logo file size cannot exceed 2MB.")
            await logo.seek(0) # Reset file pointer after reading

            # Define a unique path for the logo in Supabase Storage
            destination_path = f"hotel_{hotel.id}/logo_{int(time.time())}.{logo.filename.split('.')[-1]}"
            
            # Upload the file and get the public URL
            logo_url = await storage_service.upload_file(
                file=logo,
                bucket_name=settings.S3_BUCKET_NAME, # Ensure this bucket exists in your Supabase project
                destination_path=destination_path
            )
            hotel.logo_url = logo_url
        else:
            logger.warning("Logo was provided, but storage service is not configured. Skipping logo upload.")
    
    # Map schema field 'hotel_name' to model field 'name'
    if 'hotel_name' in onboarding_data and onboarding_data['hotel_name'] is not None:
        hotel.name = onboarding_data.pop('hotel_name')

    for key, value in onboarding_data.items():
        if hasattr(hotel, key):
            setattr(hotel, key, value)

    if getattr(hotel, 'created_by', None) is None and current_user.id is not None:
        hotel.created_by = current_user.id

    hotel.onboarding_status = 'completed'

    # Ensure this hotel has a full set of default roles once onboarding completes.
    await _ensure_default_roles_for_hotel(db, hotel, current_user)

    # Create an audit log entry for the update
    audit_entry = AuditLog(
        event_type="hotel_onboarding_completed",
        action="update_onboarding_details",
        success="success",
        user_id=current_user.id,
        hotel_id=hotel.id,
        resource="hotel",
        resource_id=hotel.id,
        details={"updated_fields": list(onboarding_data.keys())},
        ip_address=client_ip
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(hotel)
    return HotelOnboardingResponse(success=True, data=HotelOnboardingData.from_orm(hotel))


async def create_branch(db: AsyncSession, branch_data: BranchCreate, creator: User, client_ip: str, logo: Optional[UploadFile] = None) -> Branch:
    """
    Creates a new branch for a hotel, with updated logic for location and onboarding status.
    """
    if not creator.is_super_admin():
        raise InsufficientPermissionsError("Only Super Admins can create branches.")
    if creator.hotel_id is None:
        raise DataSegregationError("Super Admin must be associated with a hotel.")

    hotel = await db.get(Hotel, creator.hotel_id)
    if not hotel:
        raise ValueError("Associated hotel not found for the current user.")
        
    if getattr(hotel, 'onboarding_status', None) != 'completed':
        raise OnboardingIncompleteError("Hotel onboarding must be completed before creating a branch.")

    max_sequence_result = await db.execute(
        select(func.max(Branch.branch_sequence)).where(Branch.hotel_id == creator.hotel_id)
    )
    max_sequence = max_sequence_result.scalar_one_or_none()
    next_branch_sequence = (max_sequence + 1) if max_sequence is not None else 1

    # Initialize the branch with all non-address data from the payload first.
    # Only set code if it exists in branch_data
    branch_kwargs = dict(
        hotel_id=creator.hotel_id,
        name=branch_data.name,
        branch_sequence=next_branch_sequence,
        created_by=creator.id,
        phone=branch_data.phone,
        email=branch_data.email,
        owner_name=branch_data.owner_name,
        gst_number=branch_data.gst_number,
        subscription_plan=branch_data.subscription_plan,
        business_type=branch_data.business_type,
        description=branch_data.description,
        fssai_number=branch_data.fssai_number,
        tin_number=branch_data.tin_number,
        professional_tax_reg_number=branch_data.professional_tax_reg_number,
        trade_license_number=branch_data.trade_license_number,
        bank_details=branch_data.bank_details,
        defaultbranch=branch_data.defaultBranch,
        social_media_links=branch_data.social_media_links,
        admin_name=branch_data.admin_name,
        seating_capacity=branch_data.seating_capacity,
        operating_hours=branch_data.operating_hours
    )
    if hasattr(branch_data, 'code'):
        branch_kwargs['code'] = branch_data.code
    # Handle logo upload if present
    settings = get_settings()
    if logo:
        # File uploads must be images (JPG, PNG, GIF)
        if logo.content_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type for logo. Only JPG, PNG, and GIF are allowed.")
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 2 MB
        file_content = await logo.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Logo file size cannot exceed 2MB.")
        await logo.seek(0)
        destination_path = f"branch_{creator.hotel_id}/logo_{int(time.time())}.{logo.filename.split('.')[-1]}"
        logo_url = await storage_service.upload_file(
            file=logo,
            bucket_name=settings.S3_BUCKET_NAME,
            destination_path=destination_path
        )
        branch_kwargs["logo_url"] = logo_url

    new_branch = Branch(**branch_kwargs)

    if branch_data.use_hotel_location:
        # If using hotel location, use hotel's address as a fallback for any fields not provided in the request.
        new_branch.address_line_1 = branch_data.address_line_1 if branch_data.address_line_1 is not None else hotel.address_line_1
        new_branch.address_line_2 = branch_data.address_line_2 if branch_data.address_line_2 is not None else hotel.address_line_2
        new_branch.area = branch_data.area if branch_data.area is not None else hotel.area
        new_branch.city = branch_data.city if branch_data.city is not None else hotel.city
        new_branch.state = branch_data.state if branch_data.state is not None else hotel.state
        new_branch.country = branch_data.country if branch_data.country is not None else hotel.country
        new_branch.pincode = branch_data.pincode if branch_data.pincode is not None else hotel.pincode
        new_branch.latitude = branch_data.latitude if branch_data.latitude is not None else hotel.latitude
        new_branch.longitude = branch_data.longitude if branch_data.longitude is not None else hotel.longitude
    else:
        # If not using hotel location, use the provided address details directly.
        new_branch.address_line_1 = branch_data.address_line_1
        new_branch.address_line_2 = branch_data.address_line_2
        new_branch.area = branch_data.area
        new_branch.city = branch_data.city
        new_branch.state = branch_data.state
        new_branch.country = branch_data.country
        new_branch.pincode = branch_data.pincode
        new_branch.latitude = branch_data.latitude
        new_branch.longitude = branch_data.longitude

    db.add(new_branch)
    await db.flush()

    # Create an audit log entry for branch creation
    audit_entry = AuditLog(
        event_type="branch_created",
        action="create_branch",
        success="success",
        user_id=creator.id,
        hotel_id=creator.hotel_id,
        branch_id=new_branch.id,
        resource="branch",
        resource_id=new_branch.id,
        details={
            "branch_name": new_branch.name,
            "branch_sequence": new_branch.branch_sequence,
        },
        ip_address=client_ip,
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(new_branch)

    # Fire-and-forget style notification for all users of this hotel.
    # It is intentionally decoupled from the DB transaction via its own session.
    notification = NotificationCreate(
        type="branch_created",
        hotel_id=creator.hotel_id,
        details={
            "message": f"New branch '{new_branch.name}' created.",
            "branch_id": new_branch.id,
            "branch_sequence": new_branch.branch_sequence,
            "created_by_user_id": creator.id,
        },
    )
    # We don't await errors here into the main flow; let them bubble up only in logs.
    try:
        await create_and_broadcast_notification(notification)
    except Exception:
        logger.exception("Failed to create/broadcast notification for new branch creation.")

    return new_branch


async def get_branches_by_hotel(
    db: AsyncSession, creator: User, page: int, per_page: int
) -> Tuple[List[Branch], int]:
    """
    Retrieves a paginated list of active branches for the creator's hotel.
    """
    if not creator.is_super_admin():
        raise InsufficientPermissionsError("Only Super Admins can list branches.")
    if creator.hotel_id is None:
        raise DataSegregationError("Super Admin must be associated with a hotel.")

    query = select(Branch).filter(
        Branch.hotel_id == creator.hotel_id,
        Branch.is_active == True
    ).order_by(Branch.branch_sequence)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * per_page
    paged_query = query.offset(offset).limit(per_page)
    result = await db.execute(paged_query)
    branches = result.scalars().all()

    return branches, total


async def update_branch(
    db: AsyncSession, branch_id: int, update_data: BranchUpdate, creator: User, client_ip: str, logo: Optional[UploadFile] = None
) -> Branch:
    """
    Updates an existing branch's details.
    This optimized version uses a direct UPDATE statement for better performance.
    """
    total_start_time = time.perf_counter()
    
    update_dict = update_data.dict(exclude_unset=True)
    if not update_dict:
        raise ValueError("No update data provided.")

    # Map schema field 'address' to model field 'address_line_1' for consistency
    if 'address' in update_dict:
        update_dict['address_line_1'] = update_dict.pop('address')

    # Align camelCase payload with snake_case column
    if 'defaultBranch' in update_dict:
        update_dict['defaultbranch'] = update_dict.pop('defaultBranch')

    # Handle logo upload if present and overwrite
    settings = get_settings()
    if logo:
        if logo.content_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type for logo. Only JPG, PNG, and GIF are allowed.")
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 2 MB
        file_content = await logo.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Logo file size cannot exceed 2MB.")
        await logo.seek(0)
        destination_path = f"branch_{creator.hotel_id}/logo_{int(time.time())}.{logo.filename.split('.')[-1]}"
        logo_url = await storage_service.upload_file(
            file=logo,
            bucket_name=settings.S3_BUCKET_NAME,
            destination_path=destination_path
        )
        update_dict["logo_url"] = logo_url

    # Add the updated_by field
    update_dict['updated_by'] = creator.id

    # Construct the direct UPDATE statement
    stmt = (
        update(Branch)
        .where(Branch.hotel_id == creator.hotel_id, Branch.id == branch_id)
        .values(**update_dict)
        .returning(Branch.id) # To get the ID for the audit log
    )

    db_query_start_time = time.perf_counter()
    result = await db.execute(stmt)
    updated_branch_id = result.scalar_one_or_none()
    db_commit_start_time = time.perf_counter()
    
    if updated_branch_id is None:
        raise ValueError(f"Branch with sequence ID {branch_id} not found in your hotel or you do not have permission to update it.")

    # Create an audit log entry for the update
    audit_entry = AuditLog(
        event_type="branch_updated", action="update_branch", success="success", user_id=creator.id,
        hotel_id=creator.hotel_id, branch_id=updated_branch_id, resource="branch", resource_id=updated_branch_id,
        details={"updated_fields": list(update_dict.keys())}, ip_address=client_ip
    )
    db.add(audit_entry)

    await db.commit()
    db_commit_end_time = time.perf_counter()

    # Fetch the updated object to return it
    updated_branch = await db.get(Branch, updated_branch_id)
    total_end_time = time.perf_counter()

    # --- Profiling Logs ---
    logger.info(f"[PERF] update_branch({branch_id}): Total time: {total_end_time - total_start_time:.4f}s")
    logger.info(f"[PERF] update_branch({branch_id}): DB Update Query: {db_commit_start_time - db_query_start_time:.4f}s")
    logger.info(f"[PERF] update_branch({branch_id}): DB Commit (Update+Audit): {db_commit_end_time - db_commit_start_time:.4f}s")

    if not updated_branch:
         raise ValueError("Failed to retrieve updated branch details after update.")

    return updated_branch


async def delete_branch(
    db: AsyncSession, branch_sequence_id: int, creator: User, client_ip: str
) -> bool:
    """
    Deletes a branch from the database.

    Flow (same pattern as role delete):
    - If there are **active** users on this branch, do **not** delete; instead
      raise an error that includes the active user count.
    - If **all** users on this branch are inactive, delete those users first
      and then hard-delete the branch record.
    """
    branch_to_delete = await get_branch_by_sequence_and_creator(db, branch_sequence_id, creator)

    if not branch_to_delete:
        raise ValueError(f"Branch with sequence ID {branch_sequence_id} not found in your hotel.")
    if bool(branch_to_delete.defaultbranch):
        raise ValueError("Cannot delete the default branch.")
    # Count only active users assigned to this branch
    active_user_count_query = select(func.count(User.id)).where(
        User.branch_id == branch_to_delete.id,
        User.is_active == True
    )
    active_user_count = (await db.execute(active_user_count_query)).scalar_one()

    if active_user_count > 0:
        raise ValueError(
            f"Cannot delete branch '{branch_to_delete.name}' as it is currently assigned to "
            f"{active_user_count} active user(s)."
        )

    # Fetch all inactive users for this branch
    inactive_users_query = select(User).where(
        User.branch_id == branch_to_delete.id,
        User.is_active == False
    )
    inactive_users_result = await db.execute(inactive_users_query)
    inactive_users = inactive_users_result.scalars().all()

    if inactive_users:
        # Delete all inactive users tied to this branch
        for user in inactive_users:
            await db.delete(user)
        await db.flush()  # Flush before deleting the branch

    # Before hard-deleting the branch, ensure there are no floors attached.
    # Otherwise the FK constraint on floors.branch_id will fail and cause a 500.
    floor_count_query = select(func.count(Floor.id)).where(
        Floor.branch_id == branch_to_delete.id
    )
    floor_count = (await db.execute(floor_count_query)).scalar_one()

    if floor_count > 0:
        raise ValueError(
            f"Cannot delete branch '{branch_to_delete.name}' because it has {floor_count} floor(s) attached. "
            f"Please delete or reassign those floors first."
        )

    # Now hard-delete the branch itself
    branch_id = branch_to_delete.id
    branch_name = branch_to_delete.name
    await db.delete(branch_to_delete)

    # Audit log for hard delete.
    # Important: do NOT set branch_id here, otherwise the FK constraint on audit_logs.branch_id
    # will block deletion of the branch row. We instead store the branch id in `resource_id`
    # and in the structured `details` payload for traceability.
    audit_entry = AuditLog(
        event_type="branch_deleted",
        action="delete_branch",
        success="success",
        user_id=creator.id,
        hotel_id=creator.hotel_id,
        resource="branch",
        resource_id=branch_id,
        details={
            "branch_id": branch_id,
            "branch_name": branch_name,
            "inactive_users_deleted": len(inactive_users),
        },
        ip_address=client_ip,
    )
    db.add(audit_entry)

    await db.commit()
    return True