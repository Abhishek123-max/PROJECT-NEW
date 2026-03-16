"""
Alembic environment configuration for HotelAgent database migrations.
Supports both async and sync database operations.
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.engine import engine_from_config
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import application modules
from app.models.core.auth import Base
from app.settings.base import get_settings

# Import all models to ensure they are registered with Base.metadata
from app.models.core.auth import Base, Role, Hotel, Branch
from app.models.core.hall import Hall
from app.models.core.section import Section
from app.models.core.table import Table
from app.models.core.user import User
from app.models.core.audit import AuditLog
from app.models.core.password_reset import PasswordResetToken
from app.models.core.subscription import Subscription
from app.models.core.floor import Floor # New import for Floor model
from app.models.core.refresh_token import RefreshToken
from app.models.core.notification import Notification
# Import new Menu Management models
from app.models.facility.menu import (
    Counter,
    Category,
    MenuItem,
    Variant,
    AddOn,
    TaxProfile,
    PricingRule,
    Tag,
)


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def include_object(object, name, type_, reflected, compare_to):
    """
    Exclude tables from schemas we don't want to manage (e.g., auth, storage).
    """
    if type_ == "table" and object.schema is not None:
        return False
    return True


def get_database_url() -> str:
    """Get database URL from settings or environment."""
    try:
        settings = get_settings()
        return settings.DATABASE_URL
    except Exception:
        # Fallback to environment variable
        return os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:MyStrongPassword123!@localhost:5432/hotelagent")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(configuration) -> None:
    """Run migrations in async mode."""
    # Create async engine
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    database_url = get_database_url()
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = database_url

    if "+asyncpg" in database_url:
        # Async driver detected
        asyncio.run(run_async_migrations(configuration))
    else:
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            do_run_migrations(connection)

        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()