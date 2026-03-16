from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.core.auth import Hotel


async def get_hotel_by_id(hotel_id: int, db: AsyncSession) -> Optional[Hotel]:
    """Asynchronously gets a hotel by its ID."""
    result = await db.execute(select(Hotel).filter(Hotel.id == hotel_id))
    return result.scalar_one_or_none()