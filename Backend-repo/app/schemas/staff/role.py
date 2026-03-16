"""Pydantic schemas for Staff Role management."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class RoleBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="The unique name of the role (e.g., 'concierge').")
    display_name: str = Field(..., max_length=100, description="A human-readable name for the role (e.g., 'Concierge').")
    description: Optional[str] = Field(None, description="A brief description of the role's purpose.")
    level: int = Field(..., ge=1, le=100, description="The hierarchical level of the role (lower is more powerful).")
    permissions: Dict[str, Any] = Field({}, description="A JSON object of specific permissions for the role.")
    can_create_roles: List[str] = Field([], description="A list of role names that this role is allowed to create.")
    default_features: Dict[str, Any] = Field({}, description="Default feature toggles for users with this role.")

class RoleCreate(RoleBase):
    can_create_roles: List[str] = Field(..., description="A list of role names that this role is allowed to create.")
    level: int = Field(..., ge=1, le=99, description="The hierarchical level of the role (1-99). Lower is more powerful.")
    permissions: Dict[str, Any] = Field(..., description="Nesting of modules/pages to fine-grained permission dicts; e.g., {'hotel_management': {'floors': {...actions...}}}.")
    hotel_id: Optional[int] = Field(None, description="Hotel to which this role belongs. Leave null for global roles.")

class RoleUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    can_create_roles: Optional[List[str]] = None
    default_features: Optional[Dict[str, Any]] = None

from app.schemas.core.user import UserResponse

class RoleAssignedUser(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    employee_pic: str | None = None
    employee_id: str | None = None

class RoleOut(RoleBase):
    id: int
    hotel_id: Optional[int] = None
    level: int
    permissions: Dict[str, Any]
    can_create_roles: List[str]
    default_features: Dict[str, Any]
    is_default: bool
    assigned_users: Optional[List[RoleAssignedUser]] = None

    class Config:
        from_attributes = True

class RoleWithCreatorOut(RoleOut):
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class RoleListResponse(BaseModel):
    roles: List[RoleOut]

class RoleWithCreatorListResponse(BaseModel):
    roles: List[RoleWithCreatorOut]