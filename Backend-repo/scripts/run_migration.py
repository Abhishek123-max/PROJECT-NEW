#!/usr/bin/env python
"""
Script to run the migration to add the phone column to the users table.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic import command
from alembic.config import Config


def run_migration():
    """Run the migration to add the phone column to the users table."""
    print("\n=== Running Migration to Add Phone Column ===\n")
    
    # Get the alembic.ini file path
    alembic_ini_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'alembic.ini')
    
    # Create the Alembic configuration
    alembic_cfg = Config(alembic_ini_path)
    
    try:
        # Run the migration
        command.upgrade(alembic_cfg, "head")
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")


if __name__ == "__main__":
    run_migration()