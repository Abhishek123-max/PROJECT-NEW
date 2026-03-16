"""Database models for the Menu Management feature."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    Enum,
    Numeric,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.core.base import Base


class Counter(Base):
    """
    Represents a kitchen station or counter within a branch.
    """
    __tablename__ = "counters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False, index=True)
    floor_number = Column(Integer, nullable=False)
    staff_assign_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    counter_sequence = Column(Integer, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    branch = relationship("Branch")
    assigned_staff = relationship("User", foreign_keys=[staff_assign_id])
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_counters")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_counters")
    categories = relationship("Category", back_populates="counter", cascade="all, delete-orphan")
    items = relationship("MenuItem", back_populates="counter", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('branch_id', 'floor_number', 'counter_sequence', name='_branch_floor_sequence_uc'),
    )


class Category(Base):
    """
    Represents a menu category or sub-category, linked to a counter.
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    counter_id = Column(Integer, ForeignKey('counters.id', ondelete='CASCADE'), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    category_sequence = Column(Integer, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    counter = relationship("Counter", back_populates="categories")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    items = relationship("MenuItem", back_populates="category", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_categories")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_categories")

    __table_args__ = (
        UniqueConstraint('counter_id', 'parent_id', 'category_sequence', name='_counter_parent_sequence_uc'),
    )


class MenuItem(Base):
    """
    Represents an individual item on the menu.
    """
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    # item_code = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    base_price = Column(Numeric(10, 2), nullable=False)
    item_sequence = Column(Integer, nullable=False)
    tags = Column(JSONB, nullable=True)
    cooking_instructions = Column(JSONB, nullable=True)
    image_url = Column(Text, nullable=True)
    item_type = Column(Enum('food', 'bev', 'packaged', name='item_type_enum'), nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False, index=True)
    counter_id = Column(Integer, ForeignKey('counters.id'), nullable=False, index=True)
    tax_profile_id = Column(Integer, ForeignKey('tax_profiles.id'), nullable=True)

    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="items")
    counter = relationship("Counter", back_populates="items")
    tax_profile = relationship("TaxProfile")
    variants = relationship("Variant", back_populates="item", cascade="all, delete-orphan")
    add_ons = relationship("AddOn", back_populates="item", cascade="all, delete-orphan")
    pricing_rules = relationship("PricingRule", back_populates="item")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_menu_items")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_menu_items")

    __table_args__ = (
        UniqueConstraint('category_id', 'item_sequence', name='_category_item_sequence_uc'),
        Index('ix_menu_items_name_fts', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
    )


class Variant(Base):
    """Represents a variant of a menu item, e.g., 'Small', 'Large'."""
    __tablename__ = "variants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price_adjust = Column(Numeric(10, 2), nullable=False, default=0.0)
    stock = Column(Integer, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    item_id = Column(Integer, ForeignKey('menu_items.id', ondelete='CASCADE'), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    item = relationship("MenuItem", back_populates="variants")


class AddOn(Base):
    """Represents an add-on for a menu item, e.g., 'Extra Cheese'."""
    __tablename__ = "add_ons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    max_selections = Column(Integer, default=1)
    active = Column(Boolean, default=True, nullable=False)
    item_id = Column(Integer, ForeignKey('menu_items.id', ondelete='CASCADE'), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    item = relationship("MenuItem", back_populates="add_ons")


class TaxProfile(Base):
    """Defines a tax rate that can be applied to items."""
    __tablename__ = "tax_profiles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    rate = Column(Numeric(5, 4), nullable=False) # e.g., 0.05 for 5%
    item_type = Column(Enum('food', 'bev', 'packaged', name='tax_item_type_enum'), nullable=True)
    auto_assign = Column(Boolean, default=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PricingRule(Base):
    """Defines dynamic pricing rules for items."""
    __tablename__ = "pricing_rules"
    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(Enum('time', 'zone', 'inventory', name='rule_type_enum'), nullable=False)
    conditions = Column(JSONB, nullable=False)
    priority = Column(Integer, default=0)
    active = Column(Boolean, default=True, nullable=False)
    item_id = Column(Integer, ForeignKey('menu_items.id', ondelete='CASCADE'), nullable=True, index=True) # Nullable for global rules
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    item = relationship("MenuItem", back_populates="pricing_rules")


class Tag(Base):
    """Defines tags that can be applied to menu items, e.g., 'vegetarian'."""
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    emoji = Column(String(10), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id', ondelete='CASCADE'), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())