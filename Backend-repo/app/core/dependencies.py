"""
FastAPI dependency functions for HotelAgent authentication system.
Provides reusable dependencies for authentication, authorization, and database access.
"""

import redis
import secrets
from typing import Optional, Generator
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPBasic, HTTPBasicCredentials, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.auth import decode_token, TokenPayload
from ..models.core.user import User
from ..models.core.auth import Role
from ..core.rbac import UserContext
from ..settings.base import get_settings
from ..settings.constants import RoleNames
from ..utils.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    InvalidTokenError
)

# JWT Bearer security scheme
jwt_bearer = HTTPBearer()
dev_docs_security = HTTPBasic()
optional_jwt_bearer = HTTPBearer(auto_error=False)


# Database Dependencies
async def get_db_session():
    """
    Get database session dependency.
    
    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    async for db in get_db():
        yield db


# Redis Dependencies
def get_redis_client():
    """
    Get Redis client dependency.
    
    Returns:
        redis.Redis: Redis client instance
    """
    settings = get_settings()
    return redis.from_url(
        settings.REDIS_URL,
        decode_responses=settings.REDIS_DECODE_RESPONSES,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
        socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
        retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
        max_connections=settings.REDIS_MAX_CONNECTIONS
    )


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from request Authorization header.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: JWT token or None if not found
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None


async def get_current_user_from_db(user_id: int, db: AsyncSession) -> Optional[User]:
    """
    Get user from database by ID.
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        User: User object or None if not found
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User).options(selectinload(User.role)).filter(
            User.id == user_id,
            User.is_active == True
        )
    )
    return result.scalar_one_or_none()


# Authentication Dependencies
async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: JWT credentials from Bearer token
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        if not payload or payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await get_current_user_from_db(payload.user_id, db)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user.token_payload = payload.dict()
        return user

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

        


async def get_current_active_user(
    current_user: User = Depends(get_current_user_from_token)
) -> User:
    """
    Get current active user (must be active and not locked).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive or locked
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    if current_user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked"
        )
    
    return current_user

def get_role_manager(user: User = Depends(get_current_active_user)):
    if not (user.is_product_admin() or user.is_super_admin() or user.is_admin()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to manage roles.")
    return user

async def get_current_user(
    current_user: User = Depends(get_current_active_user)
) -> UserContext:
    return UserContext.from_user(current_user)

def has_permission(permission: str):
    """
    Get current user as UserContext for RBAC operations.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserContext: User context for RBAC validation
    """
    async def _has_permission(
        user_context: UserContext = Depends(get_current_user)
    ):
        if not user_context.role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have an assigned role."
            )
        
        # Check if the role has the 'all' permission
        if user_context.permissions.get("all"):
            return
        if not user_context.permissions.get(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have permission: {permission}"
            )
    return _has_permission


async def get_user_with_menu_permission(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to get the current active user and verify they have permissions
    to manage menu-related resources.

    This is the specific authorization check for the Menu Management feature.

    Raises:
        HTTPException (403): If the user does not have the required role or permission.

    Returns:
        The authenticated and authorized user object.
    """
    # Check for high-level admin roles first
    is_privileged_admin = current_user.is_product_admin() or current_user.is_super_admin()

    # Check for the specific "menu_crud" permission in the user's role
    has_menu_permission = False
    if current_user.role and current_user.role.permissions:
        has_menu_permission = current_user.role.permissions.get("menu_crud", False)

    # If the user is not a privileged admin AND does not have the specific permission, deny access.
    if not (is_privileged_admin or has_menu_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage the menu.",
        )

    return current_user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Used for endpoints that work with or without authentication.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User: Current user or None if not authenticated
    """
    token = extract_token_from_request(request)
    
    if not token:
        return None
    
    try:
        payload = decode_token(token)
        if not payload or payload.type != "access":
            return None
        
        user = await get_current_user_from_db(payload.user_id, db)
        return user if user and user.is_active else None
    except (TokenExpiredError, InvalidTokenError, AuthenticationError):
        return None


async def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer)
) -> TokenPayload:
    """
    Get decoded token payload.
    
    Args:
        credentials: JWT credentials from Bearer token
        
    Returns:
        TokenPayload: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        if not payload or payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Role-based Dependencies
async def get_product_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require Product Admin role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Product Admin user
        
    Raises:
        HTTPException: If user is not Product Admin
    """
    if not current_user.is_product_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Product Admin access required"
        )
    
    return current_user


async def get_super_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require Super Admin role or higher.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Super Admin or Product Admin user
        
    Raises:
        HTTPException: If user is not Super Admin or higher
    """
    return await require_role(RoleNames.SUPER_ADMIN)(current_user)


async def get_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require Admin role or higher.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Admin, Super Admin, or Product Admin user
        
    Raises:
        HTTPException: If user is not Admin or higher
    """
    return await require_role(RoleNames.ADMIN)(current_user)


async def get_manager(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require Manager role or higher.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Manager, Admin, Super Admin, or Product Admin user
        
    Raises:
        HTTPException: If user is not Manager or higher
    """
    return await require_role(RoleNames.MANAGER)(current_user)


async def get_admin_or_manager(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current admin or manager user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current admin or manager user
        
    Raises:
        HTTPException: 403 for insufficient permissions
    """
    return await require_any_role([RoleNames.ADMIN, RoleNames.MANAGER])(current_user)


async def get_super_admin_or_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current super admin or admin user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current super admin or admin user
        
    Raises:
        HTTPException: 403 for insufficient permissions
    """
    return await require_any_role([RoleNames.SUPER_ADMIN, RoleNames.ADMIN])(current_user)


async def get_cashier(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require Cashier role or higher management roles.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: User with Cashier role or higher
        
    Raises:
        HTTPException: If user doesn't have appropriate role
    """
    return await require_role(RoleNames.CASHIER)(current_user)


async def get_kitchen_staff(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require Kitchen Staff role or higher management roles.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: User with Kitchen Staff role or higher
        
    Raises:
        HTTPException: If user doesn't have appropriate role
    """
    return await require_role(RoleNames.KITCHEN_STAFF)(current_user)


async def get_waiters(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require Waiters role or higher management roles.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: User with Waiters role or higher
        
    Raises:
        HTTPException: If user doesn't have appropriate role
    """
    return await require_role(RoleNames.WAITERS)(current_user)


async def get_inventory_manager(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require Inventory Manager role or higher management roles.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: User with Inventory Manager role or higher
        
    Raises:
        HTTPException: If user doesn't have appropriate role
    """
    return await require_role(RoleNames.INVENTORY_MANAGER)(current_user)


async def get_housekeeping(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require Housekeeping role or higher management roles.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: User with Housekeeping role or higher
        
    Raises:
        HTTPException: If user doesn't have appropriate role
    """
    return await require_role(RoleNames.HOUSEKEEPING)(current_user)


# Utility Dependencies
async def get_user_context(
    current_user: User = Depends(get_current_active_user),
    token_payload: TokenPayload = Depends(get_token_payload)
) -> dict:
    """
    Get complete user context including user object and token payload.
    
    Args:
        current_user: Current authenticated user
        token_payload: Decoded token payload
        
    Returns:
        dict: Complete user context
    """
    return {
        "user": current_user,
        "user_context": UserContext.from_user(current_user),
        "token_payload": token_payload,
        "role": current_user.role.name if current_user.role else None,
        "hotel_id": current_user.hotel_id,
        "branch_id": current_user.branch_id,
        "zone_id": current_user.zone_id,
        "floor_id": current_user.floor_id,
        "section_id": current_user.section_id,
        
        "feature_toggles": current_user.feature_toggles,
        "access_level": current_user.get_access_level()
    }


async def get_request_context(
    request: Request,
    user_context: dict = Depends(get_user_context)
) -> dict:
    """
    Get complete request context including user and request information.
    
    Args:
        request: FastAPI request object
        user_context: User context from get_user_context
        
    Returns:
        dict: Complete request context
    """
    return {
        **user_context,
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path
    }


async def get_client_ip(request: Request) -> str:
    """
    Get the client's IP address from the request.
    """
    return request.client.host if request.client else "unknown"


# Convenience functions for role checking
def require_role(required_role: str):
    """
    Create a dependency that requires a specific role.
    
    Args:
        required_role: Required role name
        
    Returns:
        Dependency function
    """
    async def role_dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.role or current_user.role.name != required_role:
            # Check if user has higher authority role
            from ..settings.constants import get_role_level, is_higher_role
            
            if current_user.role:
                current_role = current_user.role.name
                if is_higher_role(current_role, required_role):
                    return current_user
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        
        return current_user
    
    return role_dependency


def get_dev_docs_user(credentials: HTTPBasicCredentials = Depends(dev_docs_security)):
    """
    Dependency to protect non-public, work-in-progress API documentation.
    This uses a simple, self-contained basic auth check.
    """
    # Hardcoded credentials for securing development/staging endpoints.
    correct_username = secrets.compare_digest(credentials.username, "wip-viewer")
    correct_password = secrets.compare_digest(credentials.password, "show-me-wip-apis")

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password for this resource",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def require_any_role(required_roles: list):
    """
    Create a dependency that requires any of the specified roles.
    
    Args:
        required_roles: List of acceptable role names
        
    Returns:
        Dependency function
    """
    async def role_dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.role or current_user.role.name not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_dependency