"""FloorManager model for HotelAgent API."""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.core.auth import Base


class FloorManager(Base):
    __tablename__ = "floor_managers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "hotel_id",
            "floor_id",
            "user_id",
            name="uq_floor_manager_tenant",
        ),
    )

    floor = relationship("Floor", back_populates="floor_managers", overlaps="managers,managed_floors")
    user = relationship("User", back_populates="managed_floor_links", overlaps="managed_floors,managers")