"""Subscription models for HotelAgent API."""

from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .auth import Base


class Subscription(Base):
    """Subscription model."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", name="fk_subscriptions_hotel_id"), nullable=False, index=True)
    plan_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default='pending', index=True)
    subscription_start_date = Column(DateTime(timezone=True), nullable=False)
    subscription_end_date = Column(DateTime(timezone=True), nullable=False)
    amount_paid = Column(Float, nullable=True) # Temporarily allow NULLs
    payment_method = Column(String(50), nullable=True)
    transaction_id = Column(String(100), nullable=True)
    onboarding_mode = Column(String(50), nullable=True)
    feature_toggles = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    hotel = relationship("Hotel", back_populates="subscriptions")

    __table_args__ = (
        # This composite index is CRITICAL for login performance.
        # The authenticate_user function queries by hotel_id and status
        # to find the active subscription for feature toggles. Without this
        # index, the query will perform a full table scan, leading to
        # very slow login times as the subscriptions table grows.
        Index('ix_subscriptions_hotel_id_status', 'hotel_id', 'status'),
    )