"""Auth models for HotelAgent API."""

from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime, Text, Float, UniqueConstraint
import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


from .base import Base
from .subscription import Subscription
from .audit import AuditLog


class Role(Base):
    """Role model."""
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", name="fk_roles_hotel_id"), nullable=True, index=True)
    level = Column(Integer, nullable=False, default=3)
    permissions = Column(JSON, nullable=False, default={})
    can_create_roles = Column(JSON, nullable=False, default=[])
    default_features = Column(JSON, nullable=False, default={})
    is_default = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", name="fk_roles_created_by"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], backref="created_roles")
    hotel = relationship("Hotel", backref="roles")
    users = relationship("User", back_populates="role", foreign_keys="[User.role_id]")

    __table_args__ = (
        # Allow same role name in different hotels; enforce uniqueness per hotel.
        sa.UniqueConstraint("name", "hotel_id", name="uq_roles_name_hotel_id"),
    )


class Hotel(Base):
    """Hotel model."""
    
    __tablename__ = "hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    hotel_code = Column(String(10), unique=True, nullable=True)
    owner_name = Column(String(100), nullable=True)
    gst_number = Column(String(20), nullable=True)
    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    area = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    subscription_plan = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    onboarding_status = Column(String(50), nullable=False, server_default='pending')
    business_type = Column(String(100), nullable=True)
    logo_url = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    fssai_number = Column(String(100), nullable=True)
    tin_number = Column(String(100), nullable=True)
    professional_tax_reg_number = Column(String(100), nullable=True)
    trade_license_number = Column(String(100), nullable=True)
    bank_details = Column(JSON, nullable=True, default={})
    social_media_links = Column(JSON, nullable=True, default={})
    created_by = Column(Integer, ForeignKey("users.id", name="fk_hotels_created_by"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    branches = relationship("Branch", back_populates="hotel")
    subscriptions = relationship("Subscription", back_populates="hotel")
    users = relationship("User", back_populates="hotel", foreign_keys="[User.hotel_id]")
    audit_logs = relationship("AuditLog", back_populates="hotel")


class Branch(Base):
    """Branch model."""
    
    __tablename__ = "branches"
    
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", name="fk_branches_hotel_id"), nullable=False, index=True)
    branch_sequence = Column(Integer, nullable=False, default=1)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=True)
    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    area = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    owner_name = Column(String(100), nullable=True)
    gst_number = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    subscription_plan = Column(String(50), nullable=True)
    business_type = Column(String(100), nullable=True)
    logo_url = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    fssai_number = Column(String(100), nullable=True)
    tin_number = Column(String(100), nullable=True)
    professional_tax_reg_number = Column(String(100), nullable=True)
    trade_license_number = Column(String(100), nullable=True)
    bank_details = Column(JSON, nullable=True, default={})
    social_media_links = Column(JSON, nullable=True, default={})
    admin_name = Column(String(100), nullable=True)
    seating_capacity = Column(Integer, nullable=True)
    operating_hours = Column(JSON, nullable=True)
    # Tracks whether this branch is the default one for the hotel
    defaultbranch = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit and Timestamps
    created_by = Column(Integer, ForeignKey("users.id", name="fk_branches_created_by"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id", name="fk_branches_updated_by"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    hotel = relationship("Hotel", back_populates="branches")
    floors = relationship("Floor", back_populates="branch")
    users = relationship("User", foreign_keys="[User.branch_id]", back_populates="branch")
    audit_logs = relationship("AuditLog", back_populates="branch")
    creator = relationship("User", foreign_keys=[created_by], backref="created_branches")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_branches")

    __table_args__ = (
        # This composite unique constraint also creates an index, which is crucial for performance
        # when looking up branches by hotel_id and branch_sequence.
        UniqueConstraint('hotel_id', 'branch_sequence', name='uq_hotel_branch_sequence'),
    )

    @property
    def defaultBranch(self) -> bool:
        """
        Provide a camelCase accessor so Pydantic's from_orm can populate
        BranchResponse.defaultBranch directly from the model.
        """
        return bool(self.defaultbranch) if self.defaultbranch is not None else False

    @defaultBranch.setter
    def defaultBranch(self, value: bool) -> None:
        self.defaultbranch = value