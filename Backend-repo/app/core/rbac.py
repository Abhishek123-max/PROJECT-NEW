"""
Role-based access control for HotelAgent API.
"""

from typing import Optional
from ..models.core.user import User
from ..settings.constants import DEFAULT_PAGE_PERMISSIONS


class UserContext:
    """User context for RBAC."""
    
    def __init__(self, user: User):
        self.user = user
        self.user_id = user.id
        self.role_name = user.role.name if user.role else None
        self.hotel_id = user.hotel_id
        self.branch_id = user.branch_id
        self.zone_id = user.zone_id
        self.permissions = DEFAULT_PAGE_PERMISSIONS.get(self.role, {})
    
    @classmethod
    def from_user(cls, user: User) -> "UserContext":
        """Create UserContext from User."""
        return cls(user)