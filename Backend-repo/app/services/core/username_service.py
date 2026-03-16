"""
Service for generating unique usernames for HotelAgent users.
"""

import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.core.user import User
from app.models.core.auth import Hotel
from app.settings.constants import ROLE_NAME_TO_CODE


async def _generate_hotel_code(db: AsyncSession, hotel_name: str) -> str:
    """Generates a unique short code for a hotel."""
    # Take the first letter of each word, up to 3 letters
    initials = "".join(word[0] for word in hotel_name.split() if word).lower()[:3]
    if not initials:
        initials = "hotel"

    base_code = initials
    code_suffix = 0
    
    while True:
        test_code = f"{base_code}{code_suffix if code_suffix > 0 else ''}"
        result = await db.execute(select(Hotel).filter(Hotel.hotel_code == test_code))
        if not result.scalar_one_or_none():
            return test_code
        code_suffix += 1


async def generate_unique_username(
    db: AsyncSession,
    first_name: str,
    role_name: str,
    hotel_id: int,
    branch_sequence_id: Optional[int]
) -> str:
    """
    Generates a unique username based on user, role, and hotel details.

    Format: firstname_role@hotelcode{branch_sequence}.com
    """
    if not first_name:
        raise ValueError("First name is required to generate a username.")

    # 1. Get Hotel and generate hotel_code if needed
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found.")

    if not hotel.hotel_code:
        hotel.hotel_code = await _generate_hotel_code(db, hotel.name)
        db.add(hotel)
        await db.flush() # Ensure hotel_code is persisted before use

    # 2. Get role code
    role_code = ROLE_NAME_TO_CODE.get(role_name)
    if not role_code:
        # For custom roles, use the first letter
        role_code = f"_{role_name[0].lower()}"

    # 3. Assemble the base username parts
    # Sanitize first name to be alphanumeric
    sanitized_first_name = re.sub(r'[^a-zA-Z0-9]', '', first_name).lower()
    
    # Branch ID is part of the domain for non-super-admins
    branch_part = str(branch_sequence_id) if branch_sequence_id is not None else ""

    domain = f"{hotel.hotel_code}{branch_part}.com"
    base_username_part = f"{sanitized_first_name}{role_code}"

    # 4. Loop to ensure uniqueness
    username_suffix = 0
    while True:
        username_part = f"{base_username_part}{username_suffix if username_suffix > 0 else ''}"
        full_username = f"{username_part}@{domain}"
        
        result = await db.execute(select(User).filter(User.username == full_username))
        if not result.scalar_one_or_none():
            return full_username
        username_suffix += 1