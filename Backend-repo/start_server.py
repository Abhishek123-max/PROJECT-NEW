#!/usr/bin/env python3
"""
Server startup script for HotelAgent.
Initializes database and starts the FastAPI server.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_database


async def startup():
    """Initialize database connection."""
    try:
        await init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Initialize database
    # asyncio.run(startup())
    
    # Start the server
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        # reload=True
    )