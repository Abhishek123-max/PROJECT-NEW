"""
Feature toggle middleware for HotelAgent.
Provides middleware and decorators for feature access validation.
"""

import functools
from typing import Callable, Any, Optional, List, Union
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.dependencies import get_current_user, get_db
from ..services.core.features import validate_feature_access
from ..models.core.user import User
from ..utils.exceptions import FeatureAccessError, ValidationError
from ..settings.constants import FeatureNames


security = HTTPBearer()


class FeatureValidationMiddleware:
    """Middleware for validating feature access on requests."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """
        ASGI middleware for feature validation.
        This middleware can be used to automatically validate features for specific routes.
        """
        # For now, we'll pass through all requests
        # Feature validation will be handled by decorators and dependencies
        await self.app(scope, receive, send)


def require_feature(feature: Union[str, FeatureNames]) -> Callable:
    """
    Decorator to require a specific feature for endpoint access.
    
    Args:
        feature: Feature name or FeatureNames enum value
        
    Returns:
        Decorator function
        
    Usage:
        @require_feature(FeatureNames.ADVANCED_ANALYTICS)
        async def get_analytics():
            pass
    """
    feature_name = feature.value if isinstance(feature, FeatureNames) else feature
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (should be injected by get_current_user dependency)
            current_user = None
            db = None
            
            # Look for user and db in kwargs
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                elif hasattr(value, 'query'):  # Database session
                    db = value
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required for feature access validation"
                )
            
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            try:
                await validate_feature_access(current_user.id, feature_name, db)
            except FeatureAccessError as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_features(features: List[Union[str, FeatureNames]]) -> Callable:
    """
    Decorator to require multiple features for endpoint access.
    All features must be available for access to be granted.
    
    Args:
        features: List of feature names or FeatureNames enum values
        
    Returns:
        Decorator function
        
    Usage:
        @require_features([FeatureNames.ADVANCED_ANALYTICS, FeatureNames.CUSTOM_REPORTS])
        async def get_custom_analytics():
            pass
    """
    feature_names = [
        f.value if isinstance(f, FeatureNames) else f 
        for f in features
    ]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            current_user = None
            db = None
            
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                elif hasattr(value, 'query'):
                    db = value
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required for feature access validation"
                )
            
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # Validate all required features
            missing_features = []
            for feature_name in feature_names:
                try:
                    await validate_feature_access(current_user.id, feature_name, db)
                except FeatureAccessError:
                    missing_features.append(feature_name)
                except ValidationError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=str(e)
                    )
            
            if missing_features:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required features: {', '.join(missing_features)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_feature(features: List[Union[str, FeatureNames]]) -> Callable:
    """
    Decorator to require at least one of the specified features for endpoint access.
    
    Args:
        features: List of feature names or FeatureNames enum values
        
    Returns:
        Decorator function
        
    Usage:
        @require_any_feature([FeatureNames.BASIC_INVENTORY, FeatureNames.ADVANCED_INVENTORY])
        async def get_inventory():
            pass
    """
    feature_names = [
        f.value if isinstance(f, FeatureNames) else f 
        for f in features
    ]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            current_user = None
            db = None
            
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                elif hasattr(value, 'query'):
                    db = value
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required for feature access validation"
                )
            
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # Check if user has at least one of the required features
            has_access = False
            for feature_name in feature_names:
                try:
                    await validate_feature_access(current_user.id, feature_name, db)
                    has_access = True
                    break
                except FeatureAccessError:
                    continue
                except ValidationError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=str(e)
                    )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access requires at least one of: {', '.join(feature_names)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# FastAPI dependency functions for feature validation
async def validate_feature_dependency(
    feature: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
) -> bool:
    """
    FastAPI dependency for validating a single feature.
    
    Args:
        feature: Feature name to validate
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        bool: True if user has access to the feature
        
    Raises:
        HTTPException: If feature access is denied
    """
    try:
        return await validate_feature_access(current_user.id, feature, db)
    except FeatureAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def create_feature_dependency(feature: Union[str, FeatureNames]) -> Callable:
    """
    Create a FastAPI dependency for a specific feature.
    
    Args:
        feature: Feature name or FeatureNames enum value
        
    Returns:
        FastAPI dependency function
        
    Usage:
        require_analytics = create_feature_dependency(FeatureNames.ADVANCED_ANALYTICS)
        
        @app.get("/analytics")
        async def get_analytics(
            _: bool = Depends(require_analytics),
            current_user: User = Depends(get_current_user)
        ):
            pass
    """
    feature_name = feature.value if isinstance(feature, FeatureNames) else feature
    
    async def feature_dependency(
        current_user: User = Depends(get_current_user),
        db = Depends(get_db)
    ) -> bool:
        return await validate_feature_dependency(feature_name, current_user, db)
    
    return feature_dependency


# Pre-defined feature dependencies for common features
require_basic_pos = create_feature_dependency(FeatureNames.BASIC_POS)
require_order_management = create_feature_dependency(FeatureNames.ORDER_MANAGEMENT)
require_basic_inventory = create_feature_dependency(FeatureNames.BASIC_INVENTORY)
require_advanced_analytics = create_feature_dependency(FeatureNames.ADVANCED_ANALYTICS)
require_multi_branch = create_feature_dependency(FeatureNames.MULTI_BRANCH)
require_staff_management = create_feature_dependency(FeatureNames.STAFF_MANAGEMENT)
require_advanced_inventory = create_feature_dependency(FeatureNames.ADVANCED_INVENTORY)
require_customer_management = create_feature_dependency(FeatureNames.CUSTOMER_MANAGEMENT)
require_loyalty_program = create_feature_dependency(FeatureNames.LOYALTY_PROGRAM)
require_integration_api = create_feature_dependency(FeatureNames.INTEGRATION_API)
require_custom_reports = create_feature_dependency(FeatureNames.CUSTOM_REPORTS)
require_advanced_security = create_feature_dependency(FeatureNames.ADVANCED_SECURITY)
require_audit_logs = create_feature_dependency(FeatureNames.AUDIT_LOGS)
require_white_label = create_feature_dependency(FeatureNames.WHITE_LABEL)
require_housekeeping_module = create_feature_dependency(FeatureNames.HOUSEKEEPING_MODULE)
require_delivery_management = create_feature_dependency(FeatureNames.DELIVERY_MANAGEMENT)
require_table_reservation = create_feature_dependency(FeatureNames.TABLE_RESERVATION)
require_kitchen_display = create_feature_dependency(FeatureNames.KITCHEN_DISPLAY)


class FeatureValidator:
    """
    Utility class for feature validation in business logic.
    """
    
    def __init__(self, db):
        self.db = db
    
    async def user_has_feature(self, user_id: int, feature: Union[str, FeatureNames]) -> bool:
        """
        Check if a user has access to a feature without raising exceptions.
        
        Args:
            user_id: User ID to check
            feature: Feature name or FeatureNames enum value
            
        Returns:
            bool: True if user has access, False otherwise
        """
        feature_name = feature.value if isinstance(feature, FeatureNames) else feature
        
        try:
            await validate_feature_access(user_id, feature_name, self.db)
            return True
        except (FeatureAccessError, ValidationError):
            return False
    
    async def user_has_any_feature(self, user_id: int, features: List[Union[str, FeatureNames]]) -> bool:
        """
        Check if a user has access to at least one of the specified features.
        
        Args:
            user_id: User ID to check
            features: List of feature names or FeatureNames enum values
            
        Returns:
            bool: True if user has access to at least one feature
        """
        for feature in features:
            if await self.user_has_feature(user_id, feature):
                return True
        return False
    
    async def user_has_all_features(self, user_id: int, features: List[Union[str, FeatureNames]]) -> bool:
        """
        Check if a user has access to all specified features.
        
        Args:
            user_id: User ID to check
            features: List of feature names or FeatureNames enum values
            
        Returns:
            bool: True if user has access to all features
        """
        for feature in features:
            if not await self.user_has_feature(user_id, feature):
                return False
        return True
    
    async def filter_features_by_access(
        self, 
        user_id: int, 
        features: List[Union[str, FeatureNames]]
    ) -> List[str]:
        """
        Filter a list of features to only include those the user has access to.
        
        Args:
            user_id: User ID to check
            features: List of feature names or FeatureNames enum values
            
        Returns:
            List[str]: List of accessible feature names
        """
        accessible_features = []
        
        for feature in features:
            if await self.user_has_feature(user_id, feature):
                feature_name = feature.value if isinstance(feature, FeatureNames) else feature
                accessible_features.append(feature_name)
        
        return accessible_features