"""Section model for HotelAgent API."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Section(Base):
    """Section model for organizing areas within a hall."""

    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=True)  # Changed to nullable=True
    section_name = Column(String(100), nullable=True, unique=True)
    section_type = Column(String(50), nullable=True)
    section_sequence = Column(Integer, nullable=False, server_default='1')
    is_active = Column(Boolean, default=True, server_default='true')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
    UniqueConstraint("hall_id", "section_sequence", name="uq_hall_section_sequence"),
    UniqueConstraint("hall_id", "section_name", name="uq_hall_section_name"),
    )
    # Relationships
    users = relationship("User", back_populates="section", foreign_keys="[User.section_id]")