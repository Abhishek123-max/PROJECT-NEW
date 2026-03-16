"""
SQLAlchemy model for the 'halls' table.
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    Index,
)
from sqlalchemy.orm import relationship

from .auth import Base


class Hall(Base):
    __tablename__ = "halls"

    id = Column(Integer, primary_key=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)
    hall_name = Column(String(100), nullable=False)
    hall_capacity = Column(Integer, nullable=True)
    hall_sequence = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    floor = relationship("Floor")

    __table_args__ = (Index("ix_floor_id_hall_sequence", "floor_id", "hall_sequence", unique=True),)