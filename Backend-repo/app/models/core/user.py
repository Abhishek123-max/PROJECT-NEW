"""User model for HotelAgent API."""

from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy import Column, Date, Integer, String, Boolean, JSON, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


from .base import Base
from .section import Section

from .floor import Floor
from app.models.facility.menu import Counter


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    __allow_unmapped__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    contact_email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    employee_pic = Column(String(500), nullable=True)
    employee_id = Column(String(100), nullable=True)
    is_one_time_password = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    report_manager = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    annual_salary = Column(Float, nullable=True)
    joining_date = Column(Date, nullable=True)
    department = Column(String(100), nullable=True)
    street_address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pin_code = Column(String(10), nullable=True)
    country = Column(String(100), nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(100), nullable=True)
    # Foreign keys
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True, index=True)
    
    # JSON fields
    feature_toggles = Column(JSON, nullable=False, default={})
    settings = Column(JSON, nullable=False, default={})
    
    # Timestamps
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Non-database attribute to store token payload
    token_payload: Optional[Dict[str, Any]] = None

    # Relationships
    role = relationship("Role", back_populates="users", foreign_keys=[role_id])
    floor = relationship("Floor", back_populates="users", foreign_keys=[floor_id], lazy="select")
    managed_floor_links = relationship("FloorManager", back_populates="user", cascade="all, delete-orphan")
    managed_floors = relationship(
    "Floor",
    secondary="floor_managers",
    back_populates="managers",
    overlaps="managed_floor_links,floor_managers"
)
    hotel = relationship("Hotel", back_populates="users", foreign_keys=[hotel_id], lazy="joined")
    branch = relationship("Branch", back_populates="users", foreign_keys=[branch_id], lazy="select")
    floor = relationship("Floor", back_populates="users", foreign_keys=[floor_id], lazy="select")
    section = relationship("Section", back_populates="users", foreign_keys=[section_id], lazy="select")
    audit_logs = relationship("AuditLog", back_populates="user", foreign_keys="[AuditLog.user_id]")
    # The refresh_tokens relationship was already added in the previous step, this is just for confirmation.
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    # Relationships to new Menu Management models
    created_counters = relationship("Counter", foreign_keys="[Counter.created_by]", back_populates="creator")
    updated_counters = relationship("Counter", foreign_keys="[Counter.updated_by]", back_populates="updater")
    created_categories = relationship("Category", foreign_keys="[Category.created_by]", back_populates="creator")
    updated_categories = relationship("Category", foreign_keys="[Category.updated_by]", back_populates="updater")
    created_menu_items = relationship("MenuItem", foreign_keys="[MenuItem.created_by]", back_populates="creator")
    updated_menu_items = relationship("MenuItem", foreign_keys="[MenuItem.updated_by]", back_populates="updater")


    
    def check_if_locked(self) -> bool:
        """Check if user is locked."""
        return self.is_locked
    
    def is_product_admin(self) -> bool:
        """Check if user is product admin."""
        return self.role and self.role.name == "product_admin"
    
    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return self.role and self.role.name == "super_admin"
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role and self.role.name == "admin"
    
    def is_manager(self) -> bool:
        """Check if user is manager."""
        return self.role and self.role.name == "manager"
    
    def can_access_hotel(self, hotel_id: int) -> bool:
        """Check if user can access hotel."""
        if self.is_product_admin() or self.is_super_admin():
            return True
        return self.hotel_id == hotel_id
    
    def can_access_branch(self, branch_id: int) -> bool:
        """Check if user can access branch."""
        if self.is_product_admin() or self.is_super_admin():
            return True
        return self.branch_id == branch_id and self.can_access_hotel(self.hotel_id)


    def can_access_floor(self, floor_id: int) -> bool:
        """Check if user can access floor."""
        if self.is_product_admin() or self.is_super_admin() or self.is_admin() or self.is_manager():
            return True
        return self.floor_id == floor_id and self.branch_id is not None and self.can_access_branch(self.branch_id)

    def can_access_section(self, section_id: int) -> bool:
        """Check if user can access section."""
        if self.is_product_admin() or self.is_super_admin() or self.is_admin() or self.is_manager():
            return True
        return self.section_id == section_id and self.can_access_floor(self.floor_id)
    
    def get_access_level(self) -> str:
        """Get user access level."""
        if self.role:
            return self.role.name
        return "guest"