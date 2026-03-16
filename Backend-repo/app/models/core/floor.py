"""Floor model for HotelAgent API."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.core.auth import Base


class Floor(Base):
    """Floor model."""

    __tablename__ = "floors"

    id = Column(Integer, primary_key=True, index=True)

    # Tenant scope
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, index=True)

    # Hierarchy
    branch_id = Column(
        Integer,
        ForeignKey("branches.id", name="fk_floors_branch_id"),
        nullable=False,
    )

    # Floor identity
    floor_sequence = Column(Integer, nullable=False)
    floor_number = Column(Integer, nullable=False)  # 0=Ground, 1=First
    floor_name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_by = Column(
        Integer,
        ForeignKey("users.id", name="fk_floors_created_by"),
        nullable=False,
    )
    updated_by = Column(
        Integer,
        ForeignKey("users.id", name="fk_floors_updated_by"),
        nullable=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ------------------
    # Relationships
    # ------------------

    branch = relationship("Branch", back_populates="floors")
    users = relationship("User", back_populates="floor", foreign_keys="User.floor_id")
    # Association-table relationship
    floor_managers = relationship(
        "FloorManager",
        back_populates="floor",
        cascade="all, delete-orphan",
    )

    @property
    def floor_manager_ids(self):
        if hasattr(self, "floor_managers") and self.floor_managers:
            return [fm.user_id for fm in self.floor_managers]
        return []

    # Convenience access to users (READ-ONLY)
    managers = relationship(
    "User",
    secondary="floor_managers",
    viewonly=True,
    back_populates="managed_floors",
    overlaps="managed_floor_links"
)
    floor_managers = relationship(
        "FloorManager",
        back_populates="floor",
        cascade="all, delete-orphan"
    )


    creator = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_floors",
    )

    updater = relationship(
        "User",
        foreign_keys=[updated_by],
        backref="updated_floors",
    )

    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "floor_number",
            name="uq_branch_floor_number",
        ),
        UniqueConstraint(
            "branch_id",
            "floor_sequence",
            name="uq_branch_floor_sequence",
        ),
        UniqueConstraint('branch_id', 'floor_name', name='uq_branch_floor_name'),
    )
