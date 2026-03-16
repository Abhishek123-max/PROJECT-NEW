"""
API Router for Staff Role Management.
Handles creation, retrieval, updating, and deletion of roles.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.schemas.core.user import UserResponse
from app.schemas.staff.role import (
    RoleAssignedUser,
    RoleOut,
    RoleWithCreatorOut,
    RoleCreate,
    RoleUpdate,
    RoleListResponse,
    RoleWithCreatorListResponse,
)
from app.services.staff.role import RoleService
from app.core.dependencies import (get_role_manager,
    get_current_active_user,
    get_db_session,
)
from app.models.core.user import User
from app.utils.exceptions import RoleHierarchyError, InsufficientPermissionsError
from app.settings.constants import DEFAULT_PAGE_PERMISSIONS



router = APIRouter()
public_role_router = APIRouter()

# Include public role routes in the main internal router so they appear in both docs
router.include_router(public_role_router)


from app.schemas.core.user import UserResponse

def _serialize_roles(roles):
    """Ensure role JSON fields are never None to avoid response validation errors."""
    serialized = []
    for role in roles:
        serialized.append(
            RoleOut(
                id=role.id,
                hotel_id=getattr(role, "hotel_id", None),
                name=role.name,
                display_name=role.display_name,
                description=role.description,
                level=role.level,
                permissions=role.permissions or {},
                can_create_roles=role.can_create_roles or [],
                default_features=role.default_features or {},
                is_default=bool(role.is_default),
                assigned_users=[
                    RoleAssignedUser(
                        id=user.id,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        employee_pic=user.employee_pic,
                        employee_id=user.employee_id
                    ) for user in role.users
                ],
            )
        )
    return serialized


# Remove PREDEFINED_PAGES; use DEFAULT_PAGE_PERMISSIONS as the source of truth

def _validate_permission_pages(permissions, template=DEFAULT_PAGE_PERMISSIONS, path=None):
    """Recursively validate permissions keys against DEFAULT_PAGE_PERMISSIONS structure."""
    if path is None:
        path = []
    for page, perms in permissions.items():
        if page not in template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid page: {'.'.join(path+[page])}. Valid pages: {', '.join(template.keys())}."
            )
        if isinstance(perms, dict) and isinstance(template.get(page), dict):
            # Recurse for sub-pages
            _validate_permission_pages(perms, template=template[page], path=path+[page])


@public_role_router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED, summary="Create Role")
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_role_manager),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Creates a new custom role with granular, nested page-based permissions using DEFAULT_PAGE_PERMISSIONS structure.
    """
    # Auto-scope to creator's hotel if not explicitly provided
    if not role_data.hotel_id:
        role_data.hotel_id = getattr(current_user, "hotel_id", None)

    if role_data.hotel_id and not current_user.can_access_hotel(role_data.hotel_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create roles for this hotel")

    if role_data.permissions:
        _validate_permission_pages(role_data.permissions)

    role_service = RoleService(db_session)
    try:
        new_role = await role_service.create_role(role_data, current_user)
        return new_role
    except (ValueError, RoleHierarchyError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@public_role_router.get("/roles", response_model=RoleListResponse, summary="Get All Roles")
async def get_all_roles(db_session: AsyncSession = Depends(get_db_session)):
    """Retrieves a list of all available roles, sorted by hierarchy level."""
    role_service = RoleService(db_session)
    roles = await role_service.get_all_roles()
    return RoleListResponse(roles=_serialize_roles(roles))

@public_role_router.get("/roles/mine", response_model=RoleListResponse, summary="Get My Created Roles")
async def get_my_roles(
    current_user: User = Depends(get_current_active_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """Retrieves roles created by the current user plus default system roles."""
    role_service = RoleService(db_session)
    user_id = int(getattr(current_user, "id", 0))
    roles = await role_service.get_roles_created_by(user_id)
    return RoleListResponse(roles=_serialize_roles(roles))

@public_role_router.get("/roles/hotel/{hotel_id}", response_model=RoleListResponse, summary="Get Roles By Hotel")
async def get_roles_by_hotel(
    hotel_id: int,
    current_user: User = Depends(get_current_active_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves distinct roles that are currently assigned to users in the given hotel.
    Access is restricted to users who can access that hotel.
    """
    if not current_user.can_access_hotel(hotel_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access roles for this hotel")

    role_service = RoleService(db_session)
    roles = await role_service.get_roles_by_hotel(hotel_id)
    try:
        return RoleListResponse(roles=_serialize_roles(roles))
    except Exception as e:
        import traceback
        print("Error serializing roles:", e)
        traceback.print_exc()
        # Debug response for dev: returns raw data and error
        return {"error": str(e), "roles": [role.__dict__ for role in roles]}

@public_role_router.get("/roles/with-creator", response_model=RoleWithCreatorListResponse, summary="Get Roles With Creator")
async def get_roles_with_creator(
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves all roles and includes the username of the user who created them.
    """
    role_service = RoleService(db_session)
    roles = await role_service.get_all_roles_with_creator()
    
    roles_with_creator_out = []
    for role in roles:
        role_data = RoleWithCreatorOut.from_orm(role)
        if role.creator:
            role_data.creator_name = role.creator.username
        elif bool(role.is_default):
            role_data.creator_name = "System"
        roles_with_creator_out.append(role_data)
        
    return RoleWithCreatorListResponse(roles=roles_with_creator_out)

@public_role_router.get("/roles/{role_id}", response_model=RoleOut, summary="Get Role By Id")
async def get_role_by_id(role_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """Retrieves a single role by its ID."""
    role_service = RoleService(db_session)
    role = await role_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role

@public_role_router.put("/roles/{role_id}", response_model=RoleOut, summary="Update Role")
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_role_manager or get_current_active_user)
):
    """Updates an existing custom role."""
    if role_data.permissions:
        _validate_permission_pages(role_data.permissions)

    role_service = RoleService(db_session)
    try:
        updated_role = await role_service.update_role(role_id, role_data, current_user)
        if not updated_role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return updated_role
    except (RoleHierarchyError, InsufficientPermissionsError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

@public_role_router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Role")
async def delete_role(
    role_id: int,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_role_manager)
):
    """Deletes a custom role, if it is not currently assigned to any users."""
    role_service = RoleService(db_session)
    try:
        success = await role_service.delete_role(role_id, current_user)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    except (RoleHierarchyError, InsufficientPermissionsError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))