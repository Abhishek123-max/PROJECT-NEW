"""
SQLAlchemy model for Notifications.
"""

import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from .auth import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True, nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True, index=True)
    details = Column(JSONB, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, server_default="f")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)