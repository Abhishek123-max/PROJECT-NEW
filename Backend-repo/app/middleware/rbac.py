"""
Role-Based Access Control (RBAC) middleware for HotelAgent.
Provides permission checking, data segregation validation, and decorators.
"""

import functools
from typing import Optional, List, Callable, Any
from fastapi import HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse
from sqlalchemy.orm import Session
import json

from ..core.rbac import UserContext
from ..services.core.features import validate_feature_access

from ..core.dependencies import get_current_user, get_db_session
from ..utils.exceptions import (
    AuthorizationError, InsufficientPermissionsError, 
    DataSegregationError, FeatureAccessError
)
from ..settings.constants import ERROR_CODES


security = HTTPBearer()


def check_permission(user_context: UserContext, permission: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user_context: User context with role and permissions
        permission: Permission name to check
        
    Returns:
        bool: True if user has permission
        
    Raises:
        InsufficientPermissionsError: If user lacks permission
    """
    if not user_context.permissions.get(permission, False):
        raise InsufficientPermissionsError(
            f"Permission '{permission}' required for this operation"
        )
    return True


def check_feature_access(user_context: UserContext, feature: str) -> bool:
    """
    Check if user has access to a specific feature.
    
    Args:
        user_context: User context with feature toggles
        feature: Feature name to check
        
    Returns:
        bool: True if user has feature access
        
    Raises:
        FeatureAccessError: If feature access is denied
    """
    return validate_feature_access(user_context, feature)


def check_data_segregation(
    user_context: UserContext,
    hotel_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    zone_id: Optional[int] = None,
    db: Session = None
) -> bool:
    """
    Check data segregation constraints for user access.
    
    Args:
        user_context: User context
        hotel_id: Hotel ID to validate (optional)
        branch_id: Branch ID to validate (optional)
        zone_id: Zone ID to validate (optional)
        db: Database session
        
    Returns:
        bool: True if access is allowed
        
    Raises:
        DataSegregationError: If data segregation is violated
    """
    if hotel_id is not None:
        if not user_context.user.can_access_hotel(hotel_id):
            raise DataSegregationError("User does not have access to this hotel.")
    
    if branch_id is not None:
        if not user_context.user.can_access_branch(branch_id):
            raise DataSegregationError("User does not have access to this branch.")
    
    if zone_id is not None:
        if not user_context.user.can_access_zone(zone_id):
            raise DataSegregationError("User does not have access to this zone.")
    
    return True


def validate_multi_tenant_access(
    user_context: UserContext,
    request: Request,
    db: Session
) -> bool:
    """
    Middleware function to validate multi-tenant access based on request parameters.
    
    Args:
        user_context: User context
        request: FastAPI request object
        db: Database session
        
    Returns:
        bool: True if access is allowed
        
    Raises:
        DataSegregationError: If multi-tenant validation fails
    """
    # Extract tenant identifiers from request path parameters or query parameters
    path_params = request.path_params
    query_params = request.query_params
    
    # Also check request body for JSON payloads (for POST/PUT requests)
    request_body_params = {}
    if hasattr(request, '_json') and request._json:
        request_body_params = request._json
    
    # Check for hotel_id in path, query, or body parameters
    hotel_id = (path_params.get("hotel_id") or 
                query_params.get("hotel_id") or 
                request_body_params.get("hotel_id"))
    if hotel_id:
        try:
            hotel_id = int(hotel_id)
            if not user_context.user.can_access_hotel(hotel_id):
                raise DataSegregationError("User does not have access to this hotel.")
        except ValueError:
            raise DataSegregationError("Invalid hotel_id format")
    
    # Check for branch_id in path, query, or body parameters
    branch_id = (path_params.get("branch_id") or 
                 query_params.get("branch_id") or 
                 request_body_params.get("branch_id"))
    if branch_id:
        try:
            branch_id = int(branch_id)
            if not user_context.user.can_access_branch(branch_id):
                raise DataSegregationError("User does not have access to this branch.")
        except ValueError:
            raise DataSegregationError("Invalid branch_id format")
    
    # Check for zone_id in path, query, or body parameters
    zone_id = (path_params.get("zone_id") or 
               query_params.get("zone_id") or 
               request_body_params.get("zone_id"))
    if zone_id:
        try:
            zone_id = int(zone_id)
            if not user_context.user.can_access_zone(zone_id):
                raise DataSegregationError("User does not have access to this zone.")
        except ValueError:
            raise DataSegregationError("Invalid zone_id format")
    
    return True


# Decorators for role-based access control

def require_role(*allowed_roles: str):
    """
    Decorator to require specific roles for endpoint access.
    
    Args:
        *allowed_roles: Role names that are allowed to access the endpoint
        
    Returns:
        Decorator function
        
    Usage:
        @require_role("admin", "manager")
        async def some_endpoint():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_context from function arguments or dependencies
            user_context = None
            
            # Look for user_context in kwargs (from dependency injection)
            if "current_user" in kwargs:
                user_context = kwargs["current_user"]
            elif "user_context" in kwargs:
                user_context = kwargs["user_context"]
            
            # If not found in kwargs, look in args
            if user_context is None:
                for arg in args:
                    if isinstance(arg, UserContext):
                        user_context = arg
                        break
            
            if user_context is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            if user_context.role_name not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Role '{user_context.role_name}' not authorized. "
                           f"Required roles: {', '.join(allowed_roles)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(*required_permissions: str):
    """
    Decorator to require specific permissions for endpoint access.
    
    Args:
        *required_permissions: Permission names that are required
        
    Returns:
        Decorator function
        
    Usage:
        @require_permission("manage_users", "view_users")
        async def some_endpoint():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_context from function arguments or dependencies
            user_context = None
            
            # Look for user_context in kwargs (from dependency injection)
            if "current_user" in kwargs:
                user_context = kwargs["current_user"]
            elif "user_context" in kwargs:
                user_context = kwargs["user_context"]
            
            # If not found in kwargs, look in args
            if user_context is None:
                for arg in args:
                    if isinstance(arg, UserContext):
                        user_context = arg
                        break
            
            if user_context is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # Check all required permissions
            missing_permissions = []
            for permission in required_permissions:
                if not has_permission(user_context, permission):
                    missing_permissions.append(permission)
            
            if missing_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing required permissions: {', '.join(missing_permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_feature(*required_features: str):
    """
    Decorator to require specific features for endpoint access.
    
    Args:
        *required_features: Feature names that are required
        
    Returns:
        Decorator function
        
    Usage:
        @require_feature("advanced_analytics", "custom_reports")
        async def some_endpoint():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_context from function arguments or dependencies
            user_context = None
            
            # Look for user_context in kwargs (from dependency injection)
            if "current_user" in kwargs:
                user_context = kwargs["current_user"]
            elif "user_context" in kwargs:
                user_context = kwargs["user_context"]
            
            # If not found in kwargs, look in args
            if user_context is None:
                for arg in args:
                    if isinstance(arg, UserContext):
                        user_context = arg
                        break
            
            if user_context is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # Check all required features
            missing_features = []
            for feature in required_features:
                try:
                    validate_feature_access(user_context, feature)
                except FeatureAccessError:
                    missing_features.append(feature)
            
            if missing_features:
                raise HTTPException(
                    status_code=403,
                    detail=f"Features not available in your subscription: {', '.join(missing_features)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_hotel_access():
    """
    Decorator to require hotel-level access validation.
    Validates hotel_id from request parameters against user's hotel access.
    
    Usage:
        @require_hotel_access()
        async def some_endpoint(hotel_id: int, current_user: UserContext = Depends(get_current_user)):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies
            user_context = None
            db_session = None
            hotel_id = None
            
            # Look for dependencies in kwargs
            if "current_user" in kwargs:
                user_context = kwargs["current_user"]
            if "db" in kwargs:
                db_session = kwargs["db"]
            if "hotel_id" in kwargs:
                hotel_id = kwargs["hotel_id"]
            
            # Look for hotel_id in args if not in kwargs
            if hotel_id is None:
                for arg in args:
                    if isinstance(arg, int):
                        hotel_id = arg
                        break
            
            if user_context is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            if db_session is None:
                raise HTTPException(
                    status_code=500,
                    detail="Database session required"
                )
            
            if hotel_id is not None:
                try:
                    validate_hotel_access(user_context, hotel_id, db_session)
                except DataSegregationError as e:
                    raise HTTPException(
                        status_code=403,
                        detail=str(e)
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_branch_access():
    """
    Decorator to require branch-level access validation.
    Validates branch_id from request parameters against user's branch access.
    
    Usage:
        @require_branch_access()
        async def some_endpoint(branch_id: int, current_user: UserContext = Depends(get_current_user)):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies
            user_context = None
            db_session = None
            branch_id = None
            
            # Look for dependencies in kwargs
            if "current_user" in kwargs:
                user_context = kwargs["current_user"]
            if "db" in kwargs:
                db_session = kwargs["db"]
            if "branch_id" in kwargs:
                branch_id = kwargs["branch_id"]
            
            # Look for branch_id in args if not in kwargs
            if branch_id is None:
                for arg in args:
                    if isinstance(arg, int):
                        branch_id = arg
                        break
            
            if user_context is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            if db_session is None:
                raise HTTPException(
                    status_code=500,
                    detail="Database session required"
                )
            
            if branch_id is not None:
                try:
                    validate_branch_access(user_context, branch_id, db_session)
                except DataSegregationError as e:
                    raise HTTPException(
                        status_code=403,
                        detail=str(e)
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_zone_access():
    """
    Decorator to require zone-level access validation.
    Validates zone_id from request parameters against user's zone access.
    
    Usage:
        @require_zone_access()
        async def some_endpoint(zone_id: int, current_user: UserContext = Depends(get_current_user)):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies
            user_context = None
            db_session = None
            zone_id = None
            
            # Look for dependencies in kwargs
            if "current_user" in kwargs:
                user_context = kwargs["current_user"]
            if "db" in kwargs:
                db_session = kwargs["db"]
            if "zone_id" in kwargs:
                zone_id = kwargs["zone_id"]
            
            # Look for zone_id in args if not in kwargs
            if zone_id is None:
                for arg in args:
                    if isinstance(arg, int):
                        zone_id = arg
                        break
            
            if user_context is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            if db_session is None:
                raise HTTPException(
                    status_code=500,
                    detail="Database session required"
                )
            
            if zone_id is not None:
                try:
                    validate_zone_access(user_context, zone_id, db_session)
                except DataSegregationError as e:
                    raise HTTPException(
                        status_code=403,
                        detail=str(e)
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# FastAPI dependency functions for RBAC

def get_permission_checker(permission: str):
    """
    Create a FastAPI dependency that checks for a specific permission.
    
    Args:
        permission: Permission name to check
        
    Returns:
        FastAPI dependency function
        
    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(
            _: bool = Depends(get_permission_checker("manage_users")),
            current_user: UserContext = Depends(get_current_user)
        ):
            pass
    """
    def permission_dependency(
        current_user: UserContext = Depends(get_current_user)
    ) -> bool:
        return check_permission(current_user, permission)
    
    return permission_dependency


def get_feature_checker(feature: str):
    """
    Create a FastAPI dependency that checks for a specific feature.
    
    Args:
        feature: Feature name to check
        
    Returns:
        FastAPI dependency function
        
    Usage:
        @app.get("/premium-feature")
        async def premium_endpoint(
            _: bool = Depends(get_feature_checker("advanced_analytics")),
            current_user: UserContext = Depends(get_current_user)
        ):
            pass
    """
    def feature_dependency(
        current_user: UserContext = Depends(get_current_user)
    ) -> bool:
        return check_feature_access(current_user, feature)
    
    return feature_dependency


def get_role_checker(*allowed_roles: str):
    """
    Create a FastAPI dependency that checks for specific roles.
    
    Args:
        *allowed_roles: Role names that are allowed
        
    Returns:
        FastAPI dependency function
        
    Usage:
        @app.get("/admin-or-manager")
        async def restricted_endpoint(
            _: bool = Depends(get_role_checker("admin", "manager")),
            current_user: UserContext = Depends(get_current_user)
        ):
            pass
    """
    def role_dependency(
        current_user: UserContext = Depends(get_current_user)
    ) -> bool:
        if current_user.role_name not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{current_user.role_name}' not authorized. "
                       f"Required roles: {', '.join(allowed_roles)}"
            )
        return True
    
    return role_dependency


def get_data_segregation_validator():
    """
    Create a FastAPI dependency that validates data segregation.
    
    Returns:
        FastAPI dependency function
        
    Usage:
        @app.get("/hotels/{hotel_id}/data")
        async def hotel_data_endpoint(
            hotel_id: int,
            _: bool = Depends(get_data_segregation_validator()),
            current_user: UserContext = Depends(get_current_user),
            db: Session = Depends(get_db_session)
        ):
            pass
    """
    def data_segregation_dependency(
        request: Request,
        current_user: UserContext = Depends(get_current_user),
        db: Session = Depends(get_db_session)
    ) -> bool:
        return validate_multi_tenant_access(current_user, request, db)
    
    return data_segregation_dependency


class DataSegregationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic data segregation validation.
    
    This middleware automatically validates multi-tenant access for all API requests
    that contain hotel_id, branch_id, or zone_id parameters.
    """
    
    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        """
        Initialize the data segregation middleware.
        
        Args:
            app: FastAPI application instance
            excluded_paths: List of paths to exclude from validation (e.g., auth endpoints)
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/auth/login",
            "/auth/refresh", 
            "/auth/logout",
            "/health",
            "/docs",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: StarletteRequest, call_next) -> StarletteResponse:
        """
        Process request and validate data segregation if needed.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from the next handler
        """
        # Immediately pass through OPTIONS requests for CORS preflight and skip excluded paths
        if request.method == "OPTIONS" or any(request.url.path.startswith(path) for path in self.excluded_paths):
          return await call_next(request)
        
        # Skip validation for non-authenticated endpoints
        if not hasattr(request.state, "user") or not request.state.user:
            return await call_next(request)
        
        try:
            # Get user context and database session from request state
            user_context = getattr(request.state, "user", None)
            db_session = getattr(request.state, "db", None)
            
            if user_context and db_session:
                # Validate multi-tenant access
                validate_multi_tenant_access(user_context, request, db_session)
            
            # Continue to next handler
            response = await call_next(request)
            return response
            
        except DataSegregationError as e:
            # Return 403 Forbidden for data segregation violations
            return StarletteResponse(
                content=json.dumps({
                    "error": "Data segregation violation",
                    "message": str(e),
                    "status_code": 403
                }),
                status_code=403,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            # Log unexpected errors and continue
            # In production, you might want to log this error
            return await call_next(request)


def create_tenant_isolation_validator(
    resource_type: str,
    resource_id_param: str = None
):
    """
    Create a FastAPI dependency for tenant isolation validation.
    
    Args:
        resource_type: Type of resource to validate (hotel, branch, zone)
        resource_id_param: Parameter name containing the resource ID
        
    Returns:
        FastAPI dependency function
        
    Usage:
        # Validate hotel access from path parameter
        hotel_validator = create_tenant_isolation_validator("hotel", "hotel_id")
        
        @app.get("/hotels/{hotel_id}/data")
        async def get_hotel_data(
            hotel_id: int,
            _: bool = Depends(hotel_validator),
            current_user: UserContext = Depends(get_current_user)
        ):
            pass
    """
    def tenant_isolation_dependency(
        request: Request,
        current_user: UserContext = Depends(get_current_user),
        db: Session = Depends(get_db_session)
    ) -> bool:
        # Extract resource ID from request
        resource_id = None
        
        if resource_id_param:
            # Get from path parameters first
            resource_id = request.path_params.get(resource_id_param)
            
            # Fall back to query parameters
            if resource_id is None:
                resource_id = request.query_params.get(resource_id_param)
        
        if resource_id is not None:
            try:
                resource_id = int(resource_id)
                
                # Validate access based on resource type
                if resource_type == "hotel":
                    validate_hotel_access(current_user, resource_id, db)
                elif resource_type == "branch":
                    validate_branch_access(current_user, resource_id, db)
                elif resource_type == "zone":
                    validate_zone_access(current_user, resource_id, db)
                else:
                    raise ValueError(f"Invalid resource type: {resource_type}")
                    
            except ValueError as e:
                if "invalid literal" in str(e).lower():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid {resource_id_param} format"
                    )
                raise HTTPException(status_code=400, detail=str(e))
            except DataSegregationError as e:
                raise HTTPException(status_code=403, detail=str(e))
        
        return True
    
    return tenant_isolation_dependency