"""Database configuration for HotelAgent API."""

from typing import AsyncGenerator, Optional, AsyncContextManager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from ..settings.base import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_database() -> None:
    """Initialize database connection."""
    try:
        # Test database connection
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise


async def create_tables() -> None:
    """Create database tables."""
    from sqlalchemy import MetaData, inspect, text
    from sqlalchemy.schema import CreateTable
    from ..models.core.auth import Base
    
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SET session_replication_role = 'replica';"))
            await conn.run_sync(Base.metadata.drop_all)
            print("Existing tables dropped")
            await conn.run_sync(Base.metadata.create_all)
            print("Tables created successfully")
            await conn.execute(text("SET session_replication_role = 'origin';"))
    except Exception as e:
        print(f"Failed to create tables: {e}")
        raise


@asynccontextmanager
async def get_db_session() -> AsyncContextManager[AsyncSession]:
    """Get database session as async context manager."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()