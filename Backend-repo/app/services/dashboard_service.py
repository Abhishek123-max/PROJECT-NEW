"""
Service layer for the Product Admin Dashboard.

This module contains the business logic to aggregate data from various sources
for the dashboard summary.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core.auth import Branch, Hotel
from app.models.core.subscription import Subscription


async def get_dashboard_summary(
    db: AsyncSession, start_date: Optional[datetime], end_date: Optional[datetime]
) -> Dict[str, Any]:
    """
    Aggregates and retrieves summary data for the Product Admin dashboard.
    
    This function runs multiple database queries concurrently for maximum efficiency.
    """
    utc_now = datetime.utcnow()
    thirty_days_ago = utc_now - timedelta(days=30)
    thirty_days_from_now = utc_now + timedelta(days=30)

    # Define individual async query functions
    async def _get_counts():
        hotel_count_query = select(func.count(Hotel.id))
        branch_count_query = select(func.count(Branch.id))
        hotel_result = await db.execute(hotel_count_query)
        branch_result = await db.execute(branch_count_query)
        return hotel_result.scalar_one(), branch_result.scalar_one()

    async def _get_subscription_stats():
        query = select(
            func.count(case((Subscription.status == 'active', Subscription.id))).label('active'),
            func.count(case((Subscription.status.in_(['inactive', 'expired']), Subscription.id))).label('inactive')
        )
        result = await db.execute(query)
        stats = result.one()
        return {"active": stats.active, "inactive": stats.inactive}

    async def _get_expiring_subscriptions():
        query = (
            select(
                Subscription.id.label("subscription_id"),
                Subscription.hotel_id,
                Hotel.name.label("hotel_name"),
                Subscription.subscription_end_date
            )
            .join(Hotel, Subscription.hotel_id == Hotel.id)
            .where(
                Subscription.status == 'active',
                Subscription.subscription_end_date.between(utc_now, thirty_days_from_now)
            )
            .order_by(Subscription.subscription_end_date)
        )
        result = await db.execute(query)
        return result.mappings().all()

    async def _get_revenue_report():
        query = select(
            Subscription.onboarding_mode,
            func.coalesce(func.sum(Subscription.payment_amount), 0.0).label("total")
        ).group_by(Subscription.onboarding_mode)

        if start_date:
            query = query.where(Subscription.payment_date >= start_date)
        if end_date:
            query = query.where(Subscription.payment_date <= end_date)

        result = await db.execute(query)
        revenue_by_mode = {row.onboarding_mode: row.total for row in result.mappings().all()}
        
        online = revenue_by_mode.get('online', 0.0)
        offline = revenue_by_mode.get('offline', 0.0)
        
        return {
            "online_payments": online,
            "offline_payments": offline,
            "total_revenue": online + offline
        }

    async def _get_new_hotels():
        query = select(
            Hotel.id.label("hotel_id"),
            Hotel.name.label("hotel_name"),
            Hotel.created_at.label("onboarding_date")
        )

        date_filter = Hotel.created_at >= thirty_days_ago
        if start_date and end_date:
            date_filter = Hotel.created_at.between(start_date, end_date)
        
        query = query.where(date_filter).order_by(Hotel.created_at.desc())
        result = await db.execute(query)
        return result.mappings().all()

    async def _get_geographical_data():
        query = select(
            Hotel.id.label("hotel_id"),
            Hotel.name.label("hotel_name"),
            Hotel.latitude,
            Hotel.longitude
        ).where(Hotel.latitude.isnot(None), Hotel.longitude.isnot(None))
        
        result = await db.execute(query)
        return result.mappings().all()

    # Run queries sequentially to ensure thread-safety with the single DB session.
    # Using asyncio.gather with a single session is not safe.
    counts = await _get_counts()
    subscription_stats = await _get_subscription_stats()
    expiring_subscriptions = await _get_expiring_subscriptions()
    revenue_report = await _get_revenue_report()
    new_hotels = await _get_new_hotels()
    geographical_data = await _get_geographical_data()

    # Assemble the final response dictionary
    return {
        "total_hotels": counts[0],
        "total_branches": counts[1],
        "subscription_stats": subscription_stats,
        "expiring_subscriptions": expiring_subscriptions,
        "revenue_report": revenue_report,
        "new_hotels": new_hotels,
        "geographical_data": geographical_data,
    }