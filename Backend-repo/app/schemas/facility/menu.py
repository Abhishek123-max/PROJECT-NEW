"""Pydantic schemas for the Menu Management feature."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --- Base Schemas ---


class BaseAudit(BaseModel):
    """Base schema for audit fields to be inherited."""

    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- Counter Schemas ---


class CounterBase(BaseModel):
    """Base schema for counter data."""

    name: str = Field(default=...)
    floor_number: int = Field(default=...)
    staff_assign_id: Optional[int] = Field(default=None)


class CounterCreate(CounterBase):
    """Schema for creating a counter."""

    branch_id: int = Field(default=...)


class CounterUpdate(BaseModel):
    """Schema for updating a counter (all fields are optional)."""

    name: Optional[str] = Field(default=None)
    floor_number: Optional[int] = Field(default=None)
    staff_assign_id: Optional[int] = Field(default=None)
    active: Optional[bool] = Field(default=None)

class CounterstatusResponse(BaseModel):
    success: bool
    data: CounterResponse

class CounterResponse(CounterBase, BaseAudit):
    """Schema for returning a counter."""

    id: int
    branch_id: int
    counter_sequence: int
    active: bool


# --- Category Schemas ---


class CategoryBase(BaseModel):
    """Base schema for category data."""

    name: str = Field(default=...)


class CategoryCreate(CategoryBase):
    """Schema for creating a category or sub-category."""

    counter_id: int = Field(default=...)
    parent_id: Optional[int] = Field(default=None)


class CategoryResponse(CategoryBase, BaseAudit):
    """Schema for returning a single category."""

    id: int
    counter_id: int
    parent_id: Optional[int]
    category_sequence: int
    active: bool

class CategorysuccessResponse(BaseModel):
    success: bool
    data: List[CategoryResponse]

class CategoryNode(CategoryResponse):
    """Recursive schema for returning a category with its children."""

    children: List["CategoryNode"] = []


# --- Menu Item Schemas ---


class MenuItemBase(BaseModel):
    """Shared fields for menu items."""

    name: str = Field(default=...)
    item_code: Optional[str] = Field(default=None)  # Not stored in database, kept for API compatibility
    description: Optional[str] = Field(default=None)
    base_price: Decimal = Field(default=...)
    item_type: str = Field(default=...)
    tags: Optional[List[str]] = Field(default=None)
    cooking_instructions: Optional[List[Dict[str, Any]]] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    tax_profile_id: Optional[int] = Field(default=None)


class MenuItemCreate(MenuItemBase):
    """Payload for creating a new menu item."""

    category_id: int = Field(default=...)
    active: bool = Field(default=True)


class MenuItemUpdate(BaseModel):
    """Payload for partially updating a menu item."""

    name: Optional[str] = Field(default=None)
    description: Optional[str] = None
    base_price: Optional[Decimal] = Field(default=None)
    item_type: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = None
    cooking_instructions: Optional[List[Dict[str, Any]]] = None
    image_url: Optional[str] = None
    tax_profile_id: Optional[int] = None
    category_id: Optional[int] = Field(default=None)
    active: Optional[bool] = None


class MenuItemResponse(MenuItemBase, BaseAudit):
    """Response schema for a menu item."""

    id: int
    category_id: int
    counter_id: int
    item_sequence: int
    active: bool