"""
Feature management service for HotelAgent.
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ...utils.exceptions import ValidationError, AuthorizationError


async def get_user_features(user_id: int, db: AsyncSession) -> Dict[str, bool]:
    """Get user features."""
    return {
        "basic_pos": True,
        "order_management": True,
        "basic_inventory": True,
        "advanced_analytics": False
    }


async def validate_feature_access(user_id: int, feature: str, db: AsyncSession) -> bool:
    """Validate feature access."""
    return True


async def update_role_features(role_name: str, features: Dict[str, bool], 
                             updated_by_user_id: int, db: AsyncSession) -> Dict[str, bool]:
    """Update role features."""
    # Get role by name
    from sqlalchemy.future import select
    from models.core.auth import Role
    
    result = await db.execute(select(Role).filter(Role.name == role_name))
    role = result.scalar_one_or_none()
    
    if not role:
        raise ValueError(f"Role '{role_name}' not found")
    
    # Update role default features
    current_features = role.default_features or {}
    updated_features = {**current_features, **features}
    
    # Update role in database
    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(Role)
        .where(Role.name == role_name)
        .values(default_features=updated_features)
    )
    await db.commit()
    
    # Return updated features
    return updated_features


async def get_role_features(role: str, db: AsyncSession) -> Dict[str, bool]:
    """Get role features."""
    # Get role by name
    from sqlalchemy.future import select
    from models.core.auth import Role
    
    result = await db.execute(select(Role).filter(Role.name == role))
    role_obj = result.scalar_one_or_none()
    
    if not role_obj:
        raise ValueError(f"Role '{role}' not found")
    
    # Return role default features
    return role_obj.default_features or {}


async def get_all_role_features(db: AsyncSession) -> Dict[str, Dict[str, bool]]:
    """Get all role features."""
    # Get all roles
    from sqlalchemy.future import select
    from models.core.auth import Role
    
    result = await db.execute(select(Role))
    roles = result.scalars().all()
    
    # Build role features dictionary
    role_features = {}
    for role in roles:
        role_features[role.name] = role.default_features or {}
    
    return role_features


async def update_role_features_by_id(role_id: int, features: Dict[str, bool], 
                                   updated_by_user_id: int, db: AsyncSession) -> Dict[str, bool]:
    """Update role features by ID."""
    # Get role by ID
    from sqlalchemy.future import select
    from models.core.auth import Role
    
    result = await db.execute(select(Role).filter(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise ValueError(f"Role with ID {role_id} not found")
    
    # Update role default features
    current_features = role.default_features or {}
    updated_features = {**current_features, **features}
    
    # Update role in database
    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(Role)
        .where(Role.id == role_id)
        .values(default_features=updated_features)
    )
    await db.commit()
    
    # Return updated features
    return updated_features


class FeatureToggleService:
    """Feature toggle service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def update_user_features(self, user_id: int, features: Dict[str, bool], 
                                 updated_by_user_id: int) -> Dict[str, bool]:
        """Update user features."""
        # Get user
        from sqlalchemy.future import select
        from models.core.user import User
        
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Update user feature toggles
        current_features = user.feature_toggles or {}
        updated_features = {**current_features, **features}
        
        # Update user in database
        from sqlalchemy import update as sql_update
        await self.db.execute(
            sql_update(User)
            .where(User.id == user_id)
            .values(feature_toggles=updated_features)
        )
        await self.db.commit()
        
        # Return updated features
        return updated_features
    
    async def get_subscription_plan_features(self, subscription_plan: str) -> Dict[str, bool]:
        """Get subscription plan features."""
        from settings.constants import SUBSCRIPTION_FEATURES
        
        if subscription_plan in SUBSCRIPTION_FEATURES:
            return SUBSCRIPTION_FEATURES[subscription_plan]
        
        return {}
    
    async def get_all_subscription_features(self) -> Dict[str, Dict[str, bool]]:
        """Get all subscription features."""
        from settings.constants import SUBSCRIPTION_FEATURES
        return SUBSCRIPTION_FEATURES