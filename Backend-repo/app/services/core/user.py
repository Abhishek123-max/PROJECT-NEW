from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from sqlalchemy import Date, select, func
from app.models.core.user import User
from app.schemas.core.user import UserCreate, UnifiedUserCreate
from app.utils.exceptions import InsufficientPermissionsError, UserAlreadyExistsError, DataSegregationError
from app.services.core.username_service import generate_unique_username
from app.utils.helpers import generate_onetime_password
from app.services.hotel.hotel import get_hotel_by_id
from app.services.hotel.branch import get_branch_by_id, get_branch_by_sequence_and_creator, get_branch_by_id_and_creator
from app.services.staff.role import RoleService
from app.models.core.subscription import Subscription
from app.core.auth import get_password_hash
from app.core.auth import TokenPayload
from app.models.core.auth import Hotel, Branch
from app.models.core.floor import Floor
from app.models.core.hall import Hall
from app.models.core.section import Section
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from app.settings.constants import get_role_level


async def create_unified_user(
    creator: User,
    role_name: str,
    first_name: str,
    db: AsyncSession,
    creator_token_payload: TokenPayload,
    last_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    phone: Optional[str] = None,
    employee_id: Optional[str] = None,
    hotel_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    floor_id: Optional[int] = None,
    section_id: Optional[int] = None,
    hotel_name: Optional[str] = None,
    owner_name: Optional[str] = None,
    report_manager: Optional[str] = None,
    hotel_data: Optional[Dict[str, Any]] = None,
    employee_pic: Optional[str] = None,
    date_of_birth: Optional[Date] = None,
    annual_salary: Optional[float] = None,
    joining_date: Optional[Date] = None,
    department: Optional[str] = None,
    street_address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    pin_code: Optional[str] = None,
    country: Optional[str] = None,
    emergency_contact_name: Optional[str] = None,
    emergency_contact_phone: Optional[str] = None,
    emergency_contact_relationship: Optional[str] = None,
):
    """
    Unified function to create users with different roles, handling access control,
    hotel/branch creation, and permission checks.
    """
    # Ensure the creator's role is loaded to prevent sync I/O on lazy load
    # when calling methods like creator.is_product_admin(). This is a common
    # cause for the 'greenlet_spawn' error with SQLAlchemy's async support.
    refreshed_creator_result = await db.execute(
        select(User).options(
            selectinload(User.role), selectinload(User.branch)
        ).filter(User.id == creator.id)
    )
    creator = refreshed_creator_result.scalar_one_or_none()
    if not creator:
        raise InsufficientPermissionsError("Creator user not found or is invalid.")

    # Determine the role
    role_service = RoleService(db_session=db)
    role = await role_service.get_role_by_name(role_name, creator.hotel_id)
    if not role:
        raise ValueError(f"Role '{role_name}' not found. Please create the role first using the role management endpoint before assigning it to a user.")

    # This will be populated if a new hotel is created for a super_admin
    new_hotel = None

    # Generate and hash the default password
    onetime_password = f"{first_name.capitalize()}welcome"
    hashed_password = await get_password_hash(onetime_password)

    # Initialize user data
    user_data = {
        "role_id": role.id,
        "password_hash": hashed_password,
        "first_name": first_name,
        "last_name": last_name,
        "contact_email": contact_email,
        "is_one_time_password": True,
        "phone": phone,
        "report_manager": report_manager,
        "employee_pic": employee_pic,
        "employee_id": employee_id,
        # Profile fields
        "date_of_birth": date_of_birth,
        "annual_salary": annual_salary,
        "joining_date": joining_date,
        "department": department,
        "street_address": street_address,
        "city": city,
        "state": state,
        "pin_code": pin_code,
        "country": country,
        "emergency_contact_name": emergency_contact_name,
        "emergency_contact_phone": emergency_contact_phone,
        "emergency_contact_relationship": emergency_contact_relationship,
    }

    # --- Subscription Feature Toggle Integration ---
    # Determine the final feature toggles based on role and active subscription.
    from app.settings.constants import DEFAULT_ROLE_FEATURES  # Local import to avoid circular deps
    from copy import deepcopy

    def merge_features(role_feats, subscription_feats):
        """
        Deeply merge role and subscription features.
        - Booleans are ANDed when a subscription toggle exists; otherwise role value is used.
        - Nested dicts are merged recursively.
        """
        if not subscription_feats:
            return deepcopy(role_feats)

        merged = {}
        for key, role_val in (role_feats or {}).items():
            sub_val = subscription_feats.get(key)
            if isinstance(role_val, dict):
                merged[key] = merge_features(role_val, sub_val if isinstance(sub_val, dict) else {})
            else:
                merged[key] = bool(role_val and bool(sub_val))
        return merged

    # Fall back to the static defaults when the role doesn't yet have defaults persisted.
    role_features = role.default_features or DEFAULT_ROLE_FEATURES.get(role_name, {})
    subscription_features = {}

    # This logic applies to all roles being created, including super_admin.
    # For a new super_admin, hotel_id is determined in the block below.
    # For other roles, hotel_id must be provided or inherited.
    temp_hotel_id = hotel_id or creator_token_payload.hotel_id

    if temp_hotel_id:
        active_sub_stmt = select(Subscription).where(
            Subscription.hotel_id == temp_hotel_id,
            Subscription.status == 'active'
        ).limit(1)
        active_sub = (await db.execute(active_sub_stmt)).scalar_one_or_none()
        if active_sub:
            subscription_features = active_sub.feature_toggles or {}
    
    # Merge role and subscription toggles without flattening nested structures.
    user_data["feature_toggles"] = merge_features(role_features, subscription_features)

    # Access control and data segregation based on creator's role
    if creator.is_product_admin():
        # Product admin can create any user, including new hotels and branches
        if role_name == "super_admin":
            if not hotel_id:
                # Create a new hotel if hotel_id is not provided for super_admin
                if hotel_data:
                    hotel_data_dict = hotel_data.copy()
                    # Handle legacy 'location' key and current 'address' key from router, mapping to 'address_line_1'
                    if "location" in hotel_data_dict:
                        hotel_data_dict["address_line_1"] = hotel_data_dict.pop("location")
                    elif "address" in hotel_data_dict:
                        hotel_data_dict["address_line_1"] = hotel_data_dict.pop("address")
                    if 'name' not in hotel_data_dict and hotel_name:
                        hotel_data_dict['name'] = hotel_name
                    if 'owner_name' not in hotel_data_dict and owner_name:
                        hotel_data_dict['owner_name'] = owner_name
                    if "gst_number" in hotel_data_dict:
                        del hotel_data_dict["gst_number"]
                    valid_hotel_fields = ["name", "owner_name", "address_line_1", "city", "country", "pincode"]
                    filtered_hotel_data = {k: v for k, v in hotel_data_dict.items() if k in valid_hotel_fields}
                    new_hotel = Hotel(**filtered_hotel_data)
                else:
                    new_hotel = Hotel(
                        name=hotel_name if hotel_name else f"{first_name}'s Hotel",
                        owner_name=owner_name
                    )
                db.add(new_hotel)
                await db.flush()  # To get the new_hotel.id
                user_data["hotel_id"] = new_hotel.id
                user_data["branch_id"] = None  # Super admin is not assigned to a branch on creation
            else:
                # If hotel_id is provided, ensure it exists
                hotel = await get_hotel_by_id(hotel_id, db)
                if not hotel:
                    raise ValueError(f"Hotel with ID {hotel_id} not found.")
                user_data["hotel_id"] = hotel_id
                if not branch_id:
                    # Create a default branch for the existing hotel
                    # Find the next available sequence for the new branch, specific to the hotel.
                    max_sequence_result = await db.execute( # type: ignore
                        select(func.max(Branch.branch_sequence)).filter(Branch.hotel_id == hotel_id)
                    )
                    max_sequence = max_sequence_result.scalar_one_or_none()
                    next_branch_sequence = (max_sequence + 1) if max_sequence is not None else 1
                    new_branch = Branch(hotel_id=hotel_id, name=f"Branch {next_branch_sequence}", branch_sequence=next_branch_sequence)
                    db.add(new_branch)
                    await db.flush()
                    user_data["branch_id"] = new_branch.id
                else:
                    branch = await get_branch_by_id_and_creator(db, branch_id, creator)
                    if not branch:
                        raise ValueError(f"Branch with sequence ID {branch_id} not found for hotel {hotel_id}.")
                    user_data["branch_id"] = branch.id
            
            # Generate username after hotel/branch is confirmed
            generated_username = await generate_unique_username(
                db=db,
                first_name=first_name,
                role_name=role_name,
                hotel_id=user_data["hotel_id"],
                branch_sequence_id=branch_id
            )
            user_data["username"] = generated_username

        else:  # This block now handles admin, manager, and all other staff/custom roles
            if not hotel_id or not branch_id:
                raise ValueError(f"Hotel ID and Branch ID are required to create a '{role_name}' user.")
            
            hotel = await get_hotel_by_id(hotel_id, db)
            if not hotel:
                raise ValueError(f"Hotel with ID {hotel_id} not found.")
            
            branch = await get_branch_by_id_and_creator(db, branch_id, creator)
            if not branch:
                raise ValueError(f"Branch ID {branch_id} not found for hotel {hotel_id}.")

            # Ensure only one admin per branch and set admin name on the branch record
            if role_name == "admin":
                existing_admin = (await db.execute(
                    select(User).filter(User.is_active == True, User.branch_id == branch.id, User.role_id == role.id)
                )).scalar_one_or_none()

                if existing_admin:
                    raise ValueError(f"Branch {branch.branch_sequence} already has an admin assigned")
                full_admin_name = " ".join(filter(None, [first_name, last_name])) or first_name
                branch.admin_name = full_admin_name

            # TODO: Add validation for floor_id, section_id existence if they are provided.
            user_data["hotel_id"] = hotel_id
            user_data["branch_id"] = branch.id
            user_data["floor_id"] = floor_id
            user_data["section_id"] = section_id

            generated_username = await generate_unique_username(
                db=db,
                first_name=first_name,
                role_name=role_name,
                hotel_id=hotel_id,
                branch_sequence_id=branch_id
            )
            user_data["username"] = generated_username

    elif creator.is_super_admin():
        # Super admin can create admin, manager, staff within their hotel
        if creator_token_payload.hotel_id is None:
            raise InsufficientPermissionsError("Super admin token missing hotel_id.")

        user_data["hotel_id"] = creator_token_payload.hotel_id

        # A Super Admin can only create roles with a lower level.
        if get_role_level(creator.role.name) <= get_role_level(role_name):
            raise InsufficientPermissionsError(f"A Super Admin cannot create a user with the role '{role_name}'.")

        if role_name == "admin":
            if not branch_id:
                raise ValueError(
                    "A branch_id is required to create an Admin user. Please create a branch first."
                )
            branch = await get_branch_by_id_and_creator(db, branch_id, creator)
            if not branch:
                raise ValueError(f"Branch ID {branch_id} not found for your hotel.")

            # Ensure only one admin per branch and set admin name on the branch record
            existing_admin = (await db.execute(
                select(User).filter(User.branch_id == branch.id, User.role_id == role.id,User.is_active == True)
            )).scalar_one_or_none()
            if existing_admin:
                raise ValueError(f"Branch {branch.branch_sequence} already has an admin assigned")
            full_admin_name = " ".join(filter(None, [first_name, last_name])) or first_name
            branch.admin_name = full_admin_name
            user_data["branch_id"] = branch.id

            # Generate username
            generated_username = await generate_unique_username(
                db=db,
                first_name=first_name,
                role_name=role_name,
                hotel_id=user_data["hotel_id"],
                branch_sequence_id=branch_id
            )
            user_data["username"] = generated_username
        elif role_name == "manager":
            if not branch_id:
                raise ValueError("Branch ID is required for manager creation by super admin.")
            branch = await get_branch_by_id_and_creator(db, branch_id, creator)
            if not branch:
                raise ValueError(f"Branch ID {branch_id} not found for your hotel.")
            user_data["branch_id"] = branch.id
            user_data["floor_id"] = floor_id
            user_data["section_id"] = section_id

            # Generate username
            generated_username = await generate_unique_username(
                db=db,
                first_name=first_name,
                role_name=role_name,
                hotel_id=user_data["hotel_id"],
                branch_sequence_id=branch_id
            )
            user_data["username"] = generated_username
        else: # This now handles 'gatekeeper' and all other custom/staff roles
            # A super admin must specify the branch for the staff member.
            if not branch_id:
                raise ValueError("A branch_id is required when a Super Admin creates staff.")

            branch = await get_branch_by_id_and_creator(db, branch_id, creator)
            if not branch:
                raise ValueError(f"Branch ID {branch_id} not found for your hotel.")

            # Validate floor_id if provided, otherwise set to None (can be assigned later)
            if section_id and not floor_id:
                raise ValueError("section_id requires floor_id to be provided.")
            
            if floor_id:
                target_floor = await db.scalar(select(Floor).filter(Floor.id == floor_id, Floor.branch_id == branch.id))
                if not target_floor:
                    raise ValueError(f"Floor with ID {floor_id} not found in branch {branch_id}.")
                user_data["floor_id"] = floor_id
                
                # Validate section_id if provided
                if section_id:
                    target_section = await db.scalar(
                        select(Section)
                        .join(Hall, Section.hall_id == Hall.id)
                        .filter(Section.id == section_id, Hall.floor_id == target_floor.id)
                    )
                    if not target_section:
                        raise ValueError(f"Section with ID {section_id} not found in floor {floor_id}.")
                    user_data["section_id"] = section_id
                else:
                    user_data["section_id"] = None
            else:
                # No floor_id provided - create employee without floor/section (can be assigned later)
                user_data["floor_id"] = None
                user_data["section_id"] = None

            user_data["branch_id"] = branch.id

            # Generate username
            generated_username = await generate_unique_username(
                db=db,
                first_name=first_name,
                role_name=role_name,
                hotel_id=user_data["hotel_id"],
                branch_sequence_id=branch_id
            )
            user_data["username"] = generated_username

    elif creator.is_admin():
        # Admin can create manager, staff within their branch
        if creator_token_payload.hotel_id is None or creator_token_payload.branch_id is None:
            raise InsufficientPermissionsError("Admin token missing hotel_id or branch_id.")

        user_data["hotel_id"] = creator_token_payload.hotel_id
        user_data["branch_id"] = creator_token_payload.branch_id

        # An Admin can only create roles with a lower level.
        if get_role_level(creator.role.name) <= get_role_level(role_name):
            raise InsufficientPermissionsError(f"Admins cannot create users with a role of equal or higher level ('{role_name}').")

        if role_name == "manager":
            user_data["floor_id"] = None
            user_data["section_id"] = section_id

            branch_for_username = await get_branch_by_id(db, user_data["branch_id"])
            if not branch_for_username:
                raise ValueError("Could not resolve branch for username generation.")
            generated_username = await generate_unique_username(
                db=db,
                first_name=first_name,
                role_name=role_name,
                hotel_id=user_data["hotel_id"],
                branch_sequence_id=branch_for_username.branch_sequence
            )
            user_data["username"] = generated_username
        else:
            # Handle staff and other roles below admin level
            # Validate floor_id if provided, otherwise set to None (can be assigned later)
            if section_id and not floor_id:
                raise ValueError("section_id requires floor_id to be provided.")
            
            if floor_id:
                target_floor = await db.scalar(select(Floor).filter(Floor.id == floor_id, Floor.branch_id == creator_token_payload.branch_id))
                if not target_floor:
                    raise ValueError(f"Floor with ID {floor_id} not found in your branch.")
                user_data["floor_id"] = floor_id
                
                # Validate section_id if provided
                if section_id:
                    target_section = await db.scalar(
                        select(Section)
                        .join(Hall, Section.hall_id == Hall.id)
                        .filter(Section.id == section_id, Hall.floor_id == target_floor.id)
                    )
                    if not target_section:
                        raise ValueError(f"Section with ID {section_id} not found in floor {floor_id}.")
                    user_data["section_id"] = section_id
                else:
                    user_data["section_id"] = None
            else:
                # No floor_id provided - create employee without floor/section (can be assigned later)
                user_data["floor_id"] = None
                user_data["section_id"] = None

            branch_for_username = await get_branch_by_id(db, user_data["branch_id"])
            if not branch_for_username:
                raise ValueError("Could not resolve branch for username generation.")
            generated_username = await generate_unique_username(
                db=db,
                first_name=first_name,
                role_name=role_name,
                hotel_id=user_data["hotel_id"],
                branch_sequence_id=branch_for_username.branch_sequence
            )
            user_data["username"] = generated_username

    elif creator.is_manager():
        # Manager can create staff within their zone/floor/section
        if creator_token_payload.hotel_id is None or creator_token_payload.branch_id is None or creator_token_payload.floor_id is None:
            raise InsufficientPermissionsError("Manager token missing hotel_id, branch_id, or floor_id.")

        user_data["hotel_id"] = creator_token_payload.hotel_id
        user_data["branch_id"] = creator_token_payload.branch_id

        # Check if the manager has permission to create this role.
        if role_name in creator.role.can_create_roles:
            # Prioritize IDs from the request body, fall back to the creator's token, then to None.
            assigned_floor_id = floor_id if floor_id is not None else creator_token_payload.floor_id
            assigned_section_id = section_id if section_id is not None else creator_token_payload.section_id

            # Validate that the provided floor/section (if any) belong to the manager's branch/floor.
            if assigned_floor_id:
                floor_query = select(Floor).filter(
                    Floor.id == assigned_floor_id,
                    Floor.branch_id == creator_token_payload.branch_id
                )
                if not (await db.execute(floor_query)).scalar_one_or_none():
                    raise ValueError(f"Floor with ID {assigned_floor_id} not found in your assigned branch.")

            if assigned_section_id:
                if not assigned_floor_id:
                    raise ValueError("A floor_id must be provided when specifying a section_id.")
                target_section = await db.scalar(
                    select(Section)
                    .join(Hall, Section.hall_id == Hall.id)
                    .filter(Section.id == assigned_section_id, Hall.floor_id == assigned_floor_id)
                )
                if not target_section:
                    raise ValueError(f"Section with ID {assigned_section_id} not found on the specified floor.")

            user_data["floor_id"] = assigned_floor_id
            user_data["section_id"] = assigned_section_id

            # A creator might be a manager without a branch themselves, so we can't rely on creator.branch
            # We use the branch_id that was validated for the user being created.
            branch_for_username = await get_branch_by_id(db, user_data["branch_id"])
            if not branch_for_username:
                 raise ValueError("Could not resolve branch for username generation.")
            # Generate username
            generated_username = await generate_unique_username(
                db=db,
                first_name=first_name,
                role_name=role_name,
                hotel_id=user_data["hotel_id"],
                branch_sequence_id=branch_for_username.branch_sequence
            )
            user_data["username"] = generated_username
        else:
            raise InsufficientPermissionsError(f"Manager cannot create user with role '{role_name}'.")

    else:
        raise InsufficientPermissionsError("You do not have permission to create users.")

    new_user = User(**user_data)
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        # Check if it's a username collision
        if 'username' in user_data:
            raise UserAlreadyExistsError(f"A user with a similar name and role might already exist. The generated username '{user_data['username']}' is taken.")
        raise ValueError("Error creating user. Check provided IDs and unique constraints.")

    if new_hotel:
        # The transaction was successful, and a new hotel was part of it.
        # Now, trigger the notification.
        from app.services.core.notification_service import create_and_broadcast_notification
        from app.schemas.core.notification import NotificationCreate

        await create_and_broadcast_notification(
            notification_data=NotificationCreate(
                type="new_hotel_request",
                hotel_id=new_hotel.id,
                details={
                    "hotel_id": str(new_hotel.id),
                    "hotel_name": new_hotel.name,
                    "request_date": datetime.utcnow().isoformat(),
                },
            )
        )

    if new_hotel:
        # Instead of just refresh, we re-fetch with the relationship loaded to avoid lazy loading issues.
        hotel_result = await db.execute(
            select(Hotel).options(selectinload(Hotel.branches)).filter(Hotel.id == new_hotel.id)
        )
        new_hotel = hotel_result.scalar_one_or_none()

    # Eagerly load the role relationship to prevent lazy loading errors in the response model.
    # The 'greenlet_spawn' error occurs when a sync I/O (lazy load) is attempted in an async context.
    # By loading the role here, we ensure the user object is complete before being used for the response.
    result = await db.execute(
        select(User).options(selectinload(User.role), selectinload(User.branch)).filter(User.id == new_user.id)
    )
    loaded_user = result.scalar_one()

    # Attach the plain-text password for the response
    return loaded_user, new_hotel, onetime_password


async def get_user_by_id(user_id: int, current_user: User, db: AsyncSession) -> Optional[User]:
    """Get user by ID with access control."""
    stmt = select(User).options(selectinload(User.role), selectinload(User.branch)).filter(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None

    # Implement data segregation based on roles
    if current_user.is_product_admin():
        return user
    elif current_user.is_super_admin():
        if user.hotel_id == current_user.hotel_id:
            return user
    elif current_user.is_admin():
        if user.hotel_id == current_user.hotel_id and user.branch_id == current_user.branch_id:
            return user
    elif current_user.is_manager():
        if user.hotel_id == current_user.hotel_id and user.branch_id == current_user.branch_id and user.floor_id == current_user.floor_id:
            return user
    else:
        # Regular staff can only view their own profile
        if user.id == current_user.id:
            return user

    raise InsufficientPermissionsError("You do not have permission to view this user.")


async def update_user(user_id: int, current_user: User, update_data: Dict[str, Any], db: AsyncSession) -> User:
    """Update user with access control."""
    user_to_update = await get_user_by_id(user_id, current_user, db)

    if not user_to_update:
        raise ValueError("User not found or you do not have permission to update this user.")

    # Prevent product admin from being deactivated or having their role changed by anyone else
    if user_to_update.is_product_admin() and not current_user.is_product_admin():
        raise InsufficientPermissionsError("Only product admins can modify other product admins.")

    # If a role_name is provided, resolve it to a role_id with proper permission checks
    if "role_name" in update_data:
        new_role_name = update_data.pop("role_name")
        if new_role_name:
            role_service = RoleService(db_session=db)
            new_role = await role_service.get_role_by_name(new_role_name, current_user.hotel_id)
            if not new_role:
                raise ValueError(
                    f"Role '{new_role_name}' not found. Please create the role first before assigning it to a user."
                )

            # Only Product Admins or Super Admins can change another user's role
            if not (current_user.is_product_admin() or current_user.is_super_admin()):
                raise InsufficientPermissionsError("Only Product Admins or Super Admins can change user roles.")

            # Enforce role hierarchy: cannot assign a role of equal or higher level than yourself
            if current_user.role and get_role_level(current_user.role.name) <= get_role_level(new_role_name):
                raise InsufficientPermissionsError(
                    f"You cannot assign a role of equal or higher level ('{new_role_name}')."
                )

            # Sync role_id and feature_toggles with the target role's defaults
            update_data["role_id"] = new_role.id
            update_data["feature_toggles"] = new_role.default_features or {}

    # Prevent users from changing their own role or deactivating themselves
    if user_to_update.id == current_user.id:
        if "role_id" in update_data and update_data["role_id"] != user_to_update.role_id:
            raise InsufficientPermissionsError("You cannot change your own role.")
        if "is_active" in update_data and not update_data["is_active"]:
            raise InsufficientPermissionsError("You cannot deactivate yourself.")

    # Update fields
    for key, value in update_data.items():
        # Prevent changing immutable fields
        # if key in ["hotel_id", "branch_id", "role_id"]:
        #     raise InsufficientPermissionsError(f"Cannot change {key}.")
        if key == "password":
            user_to_update.password_hash = await get_password_hash(value)
        elif key in ["floor_id", "section_id"]:
            # Allow Super Admin and Admin to modify hierarchical IDs
            if current_user.is_super_admin() or current_user.is_admin():
                setattr(user_to_update, key, value)
            else:
                raise InsufficientPermissionsError(f"Only Super Admins or Admins can change {key}.")
        elif hasattr(user_to_update, key):
            setattr(user_to_update, key, value)

    try:
        await db.commit()
        # Re-fetch the user with relationships loaded to avoid lazy-loading issues.
        result = await db.execute(
            select(User).options(selectinload(User.role), selectinload(User.branch)).filter(User.id == user_to_update.id)
        )
        user_to_update = result.scalar_one()
    except IntegrityError as e:
        await db.rollback()
        # Preserve the underlying DB error so the API can respond usefully
        # (e.g. duplicate contact_email).
        detail = str(getattr(e, "orig", e))
        raise ValueError(f"Error updating user: {detail}")

    return user_to_update


async def deactivate_user(user_id: int, current_user: User, db: AsyncSession) -> bool:
    """Deactivate user."""
    user_to_deactivate = await get_user_by_id(user_id, current_user, db)

    if not user_to_deactivate:
        raise ValueError("User not found or you do not have permission to deactivate this user.")

    if user_to_deactivate.id == current_user.id:
        raise InsufficientPermissionsError("You cannot deactivate yourself.")

    if user_to_deactivate.is_product_admin():
        raise InsufficientPermissionsError("Cannot deactivate a product admin.")

    user_to_deactivate.is_active = False
    try:
        await db.commit()
        await db.refresh(user_to_deactivate)
    except IntegrityError:
        await db.rollback()
        raise ValueError("Error deactivating user.")

    return True


async def assign_user_to_branch(
    user_id_to_update: int,
    target_branch_sequence_id: int,
    creator: User,
    db: AsyncSession
) -> User:
    """
    Assigns a user to a specific branch. Only for super admins.

    Args:
        user_id_to_update: The ID of the user to assign.
        target_branch_sequence_id: The sequence ID of the branch to assign to.
        creator: The super admin performing the action.
        db: The database session.

    Returns:
        The updated User object.

    Raises:
        InsufficientPermissionsError: If the creator is not a super admin.
        DataSegregationError: If the creator or user is not in the same hotel.
        ValueError: If the user or branch is not found.
    """
    # 1. Permission Check
    if not creator.is_super_admin():
        raise InsufficientPermissionsError("Only Super Admins can assign users to a branch.")

    # 2. Data Segregation & Validation
    if not creator.hotel_id:
        raise DataSegregationError("Super Admin must belong to a hotel to perform this action.")

    # Fetch the user to be updated, ensuring they are in the creator's hotel
    user_to_update = await get_user_by_id(user_id_to_update, creator, db)
    if not user_to_update or user_to_update.hotel_id != creator.hotel_id:
        raise ValueError("User not found or you do not have permission to modify this user.")

    # Fetch the target branch from the creator's hotel
    target_branch = await get_branch_by_sequence_and_creator(db, target_branch_sequence_id, creator)
    if not target_branch:
        raise ValueError(f"Branch with sequence ID {target_branch_sequence_id} not found for your hotel.")

    # 3. Update user's branch
    user_to_update.branch_id = target_branch.id
    await db.commit()
    await db.refresh(user_to_update, ["role", "branch"])

    return user_to_update



async def deactivate_user_status(user_id: int, current_user: User, db: AsyncSession) -> bool:
    """Deactivate user."""
    user_to_deactivate = await get_user_by_id(user_id, current_user, db)

    if not user_to_deactivate:
        raise ValueError("User not found or you do not have permission to deactivate this user.")

    if user_to_deactivate.id == current_user.id:
        raise InsufficientPermissionsError("You cannot deactivate yourself.")

    if user_to_deactivate.is_product_admin():
        raise InsufficientPermissionsError("Cannot deactivate a product admin.")

    user_to_deactivate.is_locked = True
    try:
        await db.commit()
        await db.refresh(user_to_deactivate)
    except IntegrityError:
        await db.rollback()
        raise ValueError("Error deactivating user.")

    return True


async def set_user_lock_status(
    user_id: int, current_user: User, is_locked: bool, db: AsyncSession
) -> bool:
    """
    Set user's is_locked to the given boolean (True or False).
    Enforces: cannot change own lock status; cannot lock a product admin.
    """
    user_to_update = await get_user_by_id(user_id, current_user, db)
    if not user_to_update:
        raise ValueError("User not found or you do not have permission to update this user.")

    if user_to_update.id == current_user.id:
        raise InsufficientPermissionsError("You cannot change your own inactive status.")

    if is_locked and user_to_update.is_product_admin():
        raise InsufficientPermissionsError("Cannot inactivate a product admin.")

    user_to_update.is_locked = is_locked
    try:
        await db.commit()
        await db.refresh(user_to_update)
    except IntegrityError:
        await db.rollback()
        raise ValueError("Error updating user inactive status.")

    return True