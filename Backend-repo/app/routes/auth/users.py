"""
User management API endpoints for HotelAgent.
Handles role-specific user creation, updates, and management operations.
"""

import logging

logger = logging.getLogger(__name__)
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, UploadFile, File
from sqlalchemy import desc, select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import (
    get_db_session,
    get_current_active_user,
    get_product_admin,
    get_super_admin,
    get_admin,
    get_manager,
    get_admin_or_manager,
    get_super_admin_or_admin
)
from ...schemas.core.user import (
    SuperAdminCreate,
    SuperAdminCreateResponse,
    AdminCreate,
    ManagerCreate,
    StaffCreate,
    UserCreate,
    UserCreateResponse,
    UserUpdateResponse,
    UserListResponse,
    UserDeleteResponse,
    UserCreateData,
    UserResponse,
    UserList,
    UnifiedUserCreate,
    UserUpdate,
    UserLockStatusUpdate,
)
from ...schemas.core.user_assignment import UserAssignBranch
from ...core.auth import TokenPayload
import os
import uuid
import asyncio
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from ...settings.base import get_settings
from ...services.core.storage_service import storage_service
from ...services.core.user import ( # Removed recursive helpers
    create_unified_user as create_unified_user_service,
    set_user_lock_status,
    get_user_by_id,
    assign_user_to_branch,
    update_user,
    deactivate_user,
)
from ...models.core.auth import Role
from ...models.core.user import User
from ...settings.constants import RoleNames, is_higher_role
from ...core.audit import audit_service
from ...services.core import password_service, email_service
from ...utils.exceptions import (
    InsufficientPermissionsError,
    DataSegregationError,
    UserAlreadyExistsError,
    AuthenticationError
)

router = APIRouter(tags=["User Management"])
public_users_router = APIRouter(tags=["User Management"])


@router.get("/{user_id}", response_model=UserCreateResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get user by ID with proper access control.
    
    Args:
        user_id: User ID to retrieve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserCreateResponse: User data
        
    Raises:
        HTTPException: 404 for not found, 403 for access denied
    """
    try:
        user = await get_user_by_id(user_id, current_user, db)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Eagerly load relationships to prevent async lazy-loading errors
        await db.refresh(user, ["branch", "role"])
        
        # Create response
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            role=user.role.name if user.role else None,
            hotel_id=user.hotel_id,            branch_id=user.branch.id if user.branch else None,
            is_active=user.is_active,
            floor_id=user.floor_id,
            section_id=user.section_id,
            employee_id=user.employee_id,
            employee_pic=user.employee_pic,
            feature_toggles=user.feature_toggles,
            created_by=user.created_by,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        
        return UserCreateResponse(
            success=True,
            message="User retrieved successfully",
            data=user_response
        )
        
    except DataSegregationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=UserUpdateResponse, status_code=status.HTTP_200_OK)
async def update_user_info(
    user_id: int,
    request: Request,
    update_data: UserUpdate = Depends(UserUpdate.as_form),
    employee_pic: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update user information with proper access control.
    
    Args:
        user_id: User ID to update
        update_data: Update data
        request: FastAPI request object for IP extraction
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserUpdateResponse: Updated user data
        
    Raises:
        HTTPException: 404 for not found, 403 for access denied
    """
    try:
        # Extract client IP for audit logging
        client_ip = request.client.host if request.client else "unknown"
        
        # Handle file upload if provided (use StorageService to upload and save URL/path to DB)
        if employee_pic:
            settings = get_settings()

            suffix = os.path.splitext(employee_pic.filename)[1] or ""
            unique_name = f"employee_pictures/{uuid.uuid4().hex}{suffix}"

            # Use storage service to upload to S3
            saved_url = await storage_service.upload_file(
                employee_pic,
                bucket_name=(settings.S3_BUCKET_NAME or ""),
                destination_path=unique_name,
            )
            # Set on the Pydantic model so it flows into the update dict
            update_data.employee_pic = saved_url

        # Convert Pydantic model to dict, excluding None values
        update_dict = update_data.dict(exclude_unset=True, exclude_none=True)
        
        # Update user
        user = await update_user(user_id, current_user, update_dict, db)
        
        # Eagerly load relationships to prevent async lazy-loading errors
        await db.refresh(user, ["branch", "role"])

        # Log user update
        await audit_service.log_user_update(
            updater_user_id=current_user.id,
            updated_user_id=user.id,
            old_values={},  # Would need to track old values in real implementation
            new_values=update_dict,
            hotel_id=user.hotel_id,
            branch_id=user.branch_id,
            ip_address=client_ip
        )
        
        # Create response
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            employee_pic=user.employee_pic,
            role=user.role.name if user.role else None,
            hotel_id=user.hotel_id,            
            branch_id=user.branch.id if user.branch else None,
            is_active=user.is_active,
            floor_id=user.floor_id,
            section_id=user.section_id,
            feature_toggles=user.feature_toggles,
            created_by=user.created_by,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            date_of_birth=user.date_of_birth,
            annual_salary=user.annual_salary,
            joining_date=user.joining_date,
            department=user.department,
            street_address=user.street_address,
            city=user.city,
            state=user.state,
            pin_code=user.pin_code,
            country=user.country,
            emergency_contact_name=user.emergency_contact_name,
            emergency_contact_phone=user.emergency_contact_phone,
            emergency_contact_relationship=user.emergency_contact_relationship,
        )
        
        return UserUpdateResponse(
            success=True,
            message="User updated successfully",
            data=user_response
        )
        
    except (DataSegregationError, InsufficientPermissionsError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
        
    except AuthenticationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    except ValueError as e:
        # Covers DB constraint failures and other validation errors raised from service layer
        # (e.g. duplicate contact_email).
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@public_users_router.post("/create", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_unified_user(
    request: Request,
    user_data: UnifiedUserCreate = Depends(UnifiedUserCreate.as_form),
    employee_pic: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Unified endpoint to create users with different roles.
    Permissions are determined by the creator's role.
    """
    try:
        client_ip = request.client.host if request.client else "unknown"

        # Handle file upload if provided (use StorageService to upload and save URL/path to DB)
        if employee_pic:
            settings = get_settings()

            suffix = os.path.splitext(employee_pic.filename)[1] or ""
            unique_name = f"employee_pictures/{uuid.uuid4().hex}{suffix}"

            # Use storage service to upload to S3
            saved_url = await storage_service.upload_file(employee_pic, bucket_name=(settings.S3_BUCKET_NAME or ""), destination_path=unique_name)
            user_data.employee_pic = saved_url
        # 1. Create the user in the database
        user, hotel, onetime_password = await create_unified_user_service(
            creator=current_user,
            role_name=user_data.role_name,
            db=db,
            creator_token_payload=TokenPayload(**current_user.token_payload),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            contact_email=user_data.contact_email,
            phone=user_data.phone,
            employee_pic=user_data.employee_pic,
            employee_id=user_data.employee_id,
            branch_id=user_data.branch_id,
            floor_id=user_data.floor_id,
            section_id=user_data.section_id,
            hotel_name=user_data.hotel_name,
            owner_name=user_data.owner_name,
            report_manager=user_data.report_manager,
            date_of_birth=user_data.date_of_birth,
            annual_salary=user_data.annual_salary,
            joining_date=user_data.joining_date,
            department=user_data.department,
            street_address=user_data.street_address,
            city=user_data.city,
            state=user_data.state,
            pin_code=user_data.pin_code,
            country=user_data.country,
            emergency_contact_name=user_data.emergency_contact_name,
            emergency_contact_phone=user_data.emergency_contact_phone,
            emergency_contact_relationship=user_data.emergency_contact_relationship,
            hotel_data={"address": user_data.hotel_location} if user_data.hotel_location else None
        )

        # Eagerly load relationships to prevent async lazy-loading errors
        await db.refresh(user, ["branch", "role"])

        # 2. Generate a password reset token
        reset_token = await password_service.generate_password_reset_token(user, db)

        # 3. Send the welcome email
        # The welcome email is intentionally not sent in this flow to facilitate testing
        # without a configured email service. The reset_token is returned in the response body.
        # await email_service.send_welcome_email(
        #     to_email=user.contact_email,
        #     first_name=user.first_name,
        #     username=user.username,
        #     default_password=onetime_password,
        #     reset_token=reset_token,
        # )

        # 4. Handle audit logging
        await audit_service.log_user_creation(
            creator_user_id=current_user.id,
            created_user_id=user.id,
            created_user_username=user.username,
            created_user_role=user_data.role_name.lower(),
            ip_address=client_ip,
            hotel_id=user.hotel_id,
            branch_id=user.branch_id,
        )

        # 5. Create response
        user_response_data = UserCreateData.model_validate({
            "id": user.id,
            "employee_pic": user.employee_pic,
            "employee_id": user.employee_id,
            "username": user.username,
            "onetime_password": onetime_password,
            "reset_token": reset_token,
            "contact_email": user.contact_email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role": user.role.name if user.role else None,
            "hotel_id": user.hotel_id,            
            "branch_id": user.branch.id if user.branch else None,
            "is_active": user.is_active,
            "floor_id": user.floor_id,
            "section_id": user.section_id,
            "report_manager": user.report_manager,
            "feature_toggles": user.feature_toggles or {},
            "date_of_birth": user.date_of_birth,
            "annual_salary": user.annual_salary,
            "joining_date": user.joining_date,
            "department": user.department,
            "street_address": user.street_address,
            "city": user.city,
            "state": user.state,
            "pin_code": user.pin_code,
            "country": user.country,
            "emergency_contact_name": user.emergency_contact_name,
            "emergency_contact_phone": user.emergency_contact_phone,
            "emergency_contact_relationship": user.emergency_contact_relationship,
            "created_by": user.created_by,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login": user.last_login,
        })

        return UserCreateResponse(
            success=True,
            message=f"{user_data.role_name.title()} user created successfully.",
            data=user_response_data
        )

    except (InsufficientPermissionsError, UserAlreadyExistsError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except (DataSegregationError, AuthenticationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.put("/{user_id}/assign-branch", response_model=UserUpdateResponse, status_code=status.HTTP_200_OK)
async def assign_user_to_branch_endpoint(
    user_id: int,
    assignment_data: UserAssignBranch,
    request: Request,
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Assign a user to a specific branch.

    Only a Super Admin can perform this action. The user being assigned (who can be the super admin
    themselves or another user) must belong to the same hotel as the super admin.
    """
    try:
        client_ip = request.client.host if request.client else "unknown"

        updated_user = await assign_user_to_branch(
            user_id_to_update=user_id,
            target_branch_sequence_id=assignment_data.branch_id,
            creator=current_user,
            db=db
        )

        # Eagerly load relationships to prevent async lazy-loading errors
        await db.refresh(updated_user, ["branch", "role"])

        # Log the assignment
        await audit_service.log_user_update(
            updater_user_id=current_user.id,
            updated_user_id=updated_user.id,
            old_values={"branch_id": "previously unassigned or different"},
            new_values={"branch_id": updated_user.branch_id},
            hotel_id=updated_user.hotel_id,
            branch_id=updated_user.branch_id,
            ip_address=client_ip,
            details=f"Assigned user to branch sequence ID {assignment_data.branch_id}"
        )

        # Create response
        user_response = UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            phone=updated_user.phone,
            role=updated_user.role.name if updated_user.role else None,
            hotel_id=updated_user.hotel_id,
            branch_id=updated_user.branch.id if updated_user.branch else None,
            is_active=updated_user.is_active,
            floor_id=updated_user.floor_id,
            section_id=updated_user.section_id,
            feature_toggles=updated_user.feature_toggles,
            created_by=updated_user.created_by,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            last_login=updated_user.last_login
        )

        return UserUpdateResponse(
            success=True,
            message=f"User successfully assigned to branch {assignment_data.branch_id}.",
            data=user_response
        )

    except (InsufficientPermissionsError, DataSegregationError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        # This will catch not found errors from the service layer
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        # Log the exception e
        logger.error(f"Error during branch assignment: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during branch assignment.")


@router.put("/update/{user_id}", response_model=UserUpdateResponse, status_code=status.HTTP_200_OK)
async def update_unified_user(
    user_id: int,
    request: Request,
    update_data: UserUpdate = Depends(UserUpdate.as_form),
    employee_pic: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update user information with proper access control.
    Handles updating users of any role type based on the current user's permissions.
    
    Args:
        user_id: User ID to update
        update_data: Update data
        request: FastAPI request object for IP extraction
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserUpdateResponse: Updated user data
        
    Raises:
        HTTPException: 404 for not found, 403 for access denied, 422 for validation errors
    """
    try:
        # Extract client IP for audit logging
        client_ip = request.client.host if request.client else "unknown"
        
        # Handle file upload if provided (use StorageService to upload and save URL/path to DB)
        if employee_pic:
            settings = get_settings()

            suffix = os.path.splitext(employee_pic.filename)[1] or ""
            unique_name = f"employee_pictures/{uuid.uuid4().hex}{suffix}"

            # Use storage service to upload to S3
            saved_url = await storage_service.upload_file(
                employee_pic,
                bucket_name=(settings.S3_BUCKET_NAME or ""),
                destination_path=unique_name,
            )
            # Set on the Pydantic model so it flows into the update dict
            update_data.employee_pic = saved_url

        # Get the user to update first to check permissions
        user_to_update = await get_user_by_id(user_id, current_user, db)
        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or you don't have permission to update this user"
            )
            
        # Check role-based permissions
        # Only allow updating users with lower role levels
        if user_to_update.role and current_user.role:
            if not is_higher_role(current_user.role.name, user_to_update.role.name):
                raise InsufficientPermissionsError(
                    "You can only update users with roles lower than your own"
                )
        
        # Convert Pydantic model to dict, excluding None values
        update_dict = update_data.dict(exclude_unset=True, exclude_none=True)
        
        # Update user
        user = await update_user(user_id, current_user, update_dict, db)
        
        # Eagerly load relationships to prevent async lazy-loading errors
        await db.refresh(user, ["branch", "role"])

        # Log user update
        await audit_service.log_user_update(
            updater_user_id=current_user.id,
            updated_user_id=user.id,
            old_values={},  # Would need to track old values in real implementation
            new_values=update_dict,
            hotel_id=user.hotel_id,
            branch_id=user.branch_id,
            ip_address=client_ip
        )
        
        # Create response
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            role=user.role.name if user.role else None,
            hotel_id=user.hotel_id,            branch_id=user.branch.id if user.branch else None,
            is_active=user.is_active,
            floor_id=user.floor_id,
            employee_pic=user.employee_pic,
            section_id=user.section_id,
            feature_toggles=user.feature_toggles,
            created_by=user.created_by,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        
        return UserUpdateResponse(
            success=True,
            message="User updated successfully",
            data=user_response
        )
        
    except (DataSegregationError, InsufficientPermissionsError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
        
    except AuthenticationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.delete("/{user_id}", response_model=UserDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_user_info(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a user with proper access control.
    Handles deleting users of any role type based on the current user's permissions.
    
    Args:
        user_id: User ID to delete
        request: FastAPI request object for IP extraction
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserDeleteResponse: Success message
        
    Raises:
        HTTPException: 404 for not found, 403 for access denied, 422 for validation errors
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        
        # Get the user to delete first to check permissions
        user_to_delete = await get_user_by_id(user_id, current_user, db)
        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or you don't have permission to delete this user"
            )
            
        # Check role-based permissions
        # Only allow deleting users with lower role levels
        if user_to_delete.role and current_user.role:
            if not is_higher_role(current_user.role.name, user_to_delete.role.name):
                raise InsufficientPermissionsError(
                    "You can only delete users with roles lower than your own"
                )
        
        await deactivate_user(user_id, current_user, db)
        
        await audit_service.log_user_deletion(
            deleter_user_id=current_user.id,
            deleted_user_id=user_id,
            ip_address=client_ip
        )
        
        return UserDeleteResponse(
            success=True,
            message="User deleted successfully"
        )
        
    except (DataSegregationError, InsufficientPermissionsError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except AuthenticationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.patch("/{user_id}", response_model=UserDeleteResponse, status_code=status.HTTP_200_OK)
async def set_user_lock_status_info(
    user_id: int,
    body: UserLockStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Set user's is_locked to true or false (from request body).
    Access control: cannot change own lock status; cannot lock a product admin.
    
    Args:
        user_id: User ID to update
        body: Request body with is_locked (true/false)
        request: FastAPI request object for IP extraction
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserDeleteResponse: Success message
        
    Raises:
        HTTPException: 404 for not found, 403 for access denied, 422 for validation errors
    """
    try:
        # Get the user first to check permissions
        user_to_update = await get_user_by_id(user_id, current_user, db)
        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or you don't have permission to update this user"
            )
        # Only allow updating lock status for users with lower role levels
        if user_to_update.role and current_user.role:
            if not is_higher_role(current_user.role.name, user_to_update.role.name):
                raise InsufficientPermissionsError(
                    "You can only change inactive status for users with roles lower than your own"
                )

        await set_user_lock_status(user_id, current_user, body.is_locked, db)

        status_msg = "inactive" if body.is_locked else "active"
        return UserDeleteResponse(
            success=True,
            message=f"User {status_msg} successfully"
        )

    except (DataSegregationError, InsufficientPermissionsError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthenticationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def list_users(
    hotel_id: Optional[int] = Query(None, description="Filter by hotel ID"),
    branch_id: Optional[int] = Query(None, description="Filter by branch ID"),
    role: Optional[str] = Query(None, description="Filter by role name"),
    joining_date_from: Optional[date] = Query(None, description="Filter by joining date from"),
    joining_date_to: Optional[date] = Query(None, description="Filter by joining date to"),
    max_annual_salary: Optional[float] = Query(None, description="Filter by maximum annual salary"),
    min_annual_salary: Optional[float] = Query(None, description="Filter by minimum annual salary"),
    report_manager: Optional[str] = Query(None, description="Filter by report manager"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List users with filtering and pagination.
    Access is controlled based on user's role and data segregation rules.
    
    Args:
        hotel_id: Filter by hotel ID
        branch_id: Filter by branch ID
        role: Filter by role name
        joining_date_from: Filter by joining date (from)
        joining_date_to: Filter by joining date (to)
        min_annual_salary: Filter by minimum annual salary
        max_annual_salary: Filter by maximum annual salary
        report_manager: Filter by report manager
        is_active: Filter by active status
        page: Page number
        per_page: Items per page
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserListResponse: Paginated list of users
    """
    try:
        # Build query based on user's access level
        query = (select(User).options(selectinload(User.role), selectinload(User.branch)).order_by(desc(User.id)))
        
        # Apply data segregation filters
        if current_user.is_product_admin():
            # Product Admin can see all users
            pass
        elif current_user.is_super_admin():
            # Super Admin can see users in their hotel
            query = query.where(User.hotel_id == current_user.hotel_id)
        elif current_user.is_admin():
            # Admin can see users in their branch
            query = query.where(
                User.hotel_id == current_user.hotel_id,
                User.branch_id == current_user.branch_id
            )
        else:
            # Staff can only see themselves
            query = query.where(User.id == current_user.id)
        
        # Apply additional filters
        if hotel_id is not None:
            # Validate access to requested hotel
            if not current_user.can_access_hotel(hotel_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot access users from this hotel"
                )
            query = query.where(User.hotel_id == hotel_id)
        
        if branch_id is not None:
            # Validate access to requested branch
            if not current_user.can_access_branch(branch_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot access users from this branch"
                )
            query = query.where(User.branch_id == branch_id)
        
        if role is not None:
            query = query.join(User.role).where(Role.name == role)
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        if joining_date_from is not None:
            query = query.where(User.joining_date >= joining_date_from)
        
        if joining_date_to is not None:
            query = query.where(User.joining_date <= joining_date_to)
        
        if min_annual_salary is not None:
            query = query.where(User.annual_salary >= min_annual_salary)
        
        if max_annual_salary is not None:
            query = query.where(User.annual_salary <= max_annual_salary)
        
        if report_manager is not None:
            query = query.where(User.report_manager == report_manager)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        offset = (page - 1) * per_page
        paged_query = query.offset(offset).limit(per_page)
        result = await db.execute(paged_query)
        users = result.scalars().all()
        
        # Create user responses
        user_responses = []
        for user in users:
            user_response = UserResponse(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                contact_email=user.contact_email,
                phone=user.phone,
                role_id=user.role_id,
                role=user.role.display_name if user.role else None,
                hotel_id=user.hotel_id,                branch_id=user.branch.id if user.branch else None,
                is_active=user.is_active,
                floor_id=user.floor_id,
                employee_id=user.employee_id,
                employee_pic=user.employee_pic,
                section_id=user.section_id,
                report_manager=user.report_manager,
                is_locked=user.is_locked,
                feature_toggles=user.feature_toggles,
                date_of_birth=user.date_of_birth,
                annual_salary=user.annual_salary,
                joining_date=user.joining_date,
                department=user.department,
                street_address=user.street_address,
                city=user.city,
                state=user.state,
                pin_code=user.pin_code,
                country=user.country,
                emergency_contact_name=user.emergency_contact_name,
                emergency_contact_phone=user.emergency_contact_phone,
                emergency_contact_relationship=user.emergency_contact_relationship,
                created_by=user.created_by,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login
            )
            user_responses.append(user_response)
        
        # Create list response
        user_list = UserList(
            users=user_responses,
            total=total,
            page=page,
            per_page=per_page
        )
        
        return UserListResponse(
            success=True,
            message="Users retrieved successfully",
            data=user_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )