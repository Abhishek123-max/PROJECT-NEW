"""
Database seeding script for roles.

This script connects to the database and ensures that all default roles
defined in `app/settings/constants.py` exist and have the correct
permissions, especially the `can_create_roles` property.

Run this script from the project root directory:
python scripts/seed_roles.py
"""

import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path to allow importing from 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.core.auth import Role
from app.models.core.user import User  # Import User to resolve relationship
from app.settings.constants import (
    RoleNames,
    DEFAULT_CAN_CREATE_ROLES,
    DEFAULT_ROLE_FEATURES,
    get_role_level,
)
from app.settings.base import get_settings


async def seed_roles():
    """
    Seeds the database with default roles and updates their permissions.
    This script will:
    1. Connect to the database using the DATABASE_URL from your .env file.
    2. Iterate through the default roles defined in constants.py.
    3. For each role, check if it exists in the database.
    4. If it exists, it will UPDATE the 'can_create_roles' field to match the new defaults.
    5. If it does not exist, it will CREATE the role with all default properties.
    """
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

    async with AsyncSessionLocal() as db:
        print("Starting role seeding/update process...")

        all_role_names = [getattr(RoleNames, attr) for attr in dir(RoleNames) if not attr.startswith('__')]

        for role_name in all_role_names:
            result = await db.execute(select(Role).filter(Role.name == role_name))
            role = result.scalar_one_or_none()

            can_create = DEFAULT_CAN_CREATE_ROLES.get(role_name, [])
            default_features = DEFAULT_ROLE_FEATURES.get(role_name, {})

            if role:
                print(f"Updating existing role: '{role_name}'...")
                role.can_create_roles = can_create
                print(f"  - Set 'can_create_roles' to: {can_create}")
            else:
                print(f"Creating new role: '{role_name}'...")
                new_role = Role(
                    name=role_name,
                    display_name=role_name.replace("_", " ").title(),
                    description=f"System-defined {role_name.replace('_', ' ').title()} role.",
                    level=get_role_level(role_name),
                    default_features=default_features,
                    can_create_roles=can_create,
                    is_default=True,
                )
                db.add(new_role)
                print(f"  - Created with 'can_create_roles': {can_create}")

        await db.commit()
        print("\nSuccessfully updated role permissions in the database.")


if __name__ == "__main__":
    print("This script will update role permissions in your database based on 'constants.py'.")
    print("Make sure your .env file is configured correctly.")
    asyncio.run(seed_roles())