#!/usr/bin/env python3
"""
Database initialization script for HotelAgent.
Creates tables and seeds initial data for testing.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_database, create_tables
from app.models.core.auth import Role, Hotel, Branch
from app.models.core.floor import Floor
from app.settings.constants import DEFAULT_PAGE_PERMISSIONS, Permissions, page_permissions_for_role
from app.models.core.user import User
from app.utils.helpers import hash_password
from app.core.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession


async def create_initial_roles():
    """Create initial roles in the system."""
    async with get_db_session() as db:
        # Check if roles already exist
        from sqlalchemy import text
        result = await db.execute(text("SELECT COUNT(*) FROM roles"))
        count = result.scalar()
        if count > 0:
            print("Roles already exist, marking them as default")
            await db.execute(text("UPDATE roles SET is_default = true"))
            await db.commit()
            return

        roles_data = [
            {
                "name": "product_admin",
                "display_name": "Product Admin",
                "description": "System administrator with full access",
                "level": 1,
                "permissions": page_permissions_for_role("product_admin"),
                "can_create_roles": ["super_admin"],
                "default_features": {"all": True}
            },
            {
                "name": "super_admin",
                "display_name": "Super Admin",
                "description": "Hotel owner/administrator",
                "level": 2,
                "permissions": page_permissions_for_role("super_admin"),
                "can_create_roles": ["admin", "manager"],
                "default_features": {"basic_pos": True, "order_management": True}
            },
            {
                "name": "admin",
                "display_name": "Admin",
                "description": "Branch administrator",
                "level": 3,
                "permissions": page_permissions_for_role("admin"),
                "can_create_roles": ["manager", "cashier", "kitchen_staff", "waiters"],
                "default_features": {"basic_pos": True, "order_management": True}
            },
            {
                "name": "manager",
                "display_name": "Manager",
                "description": "Zone/area manager",
                "level": 4,
                "permissions": page_permissions_for_role("manager"),
                "can_create_roles": ["cashier", "kitchen_staff", "waiters"],
                "default_features": {"basic_pos": True, "order_management": True}
            },
            {
                "name": "cashier",
                "display_name": "Cashier",
                "description": "Point of sale operator",
                "level": 5,
                "permissions": page_permissions_for_role("cashier"),
                "can_create_roles": [],
                "default_features": {"basic_pos": True}
            },
            {
                "name": "kitchen_staff",
                "display_name": "Kitchen Staff",
                "description": "Kitchen operations staff",
                "level": 6,
                "permissions": page_permissions_for_role("kitchen_staff"),
                "can_create_roles": [],
                "default_features": {"order_management": True}
            },
            {
                "name": "waiters",
                "display_name": "Waiters",
                "description": "Service staff",
                "level": 7,
                "permissions": page_permissions_for_role("waiters"),
                "can_create_roles": [],
                "default_features": {"basic_pos": True, "order_management": True}
            },
            {
                "name": "inventory_manager",
                "display_name": "Inventory Manager",
                "description": "Inventory management staff",
                "level": 8,
                "permissions": page_permissions_for_role("inventory_manager"),
                "can_create_roles": [],
                "default_features": {"basic_inventory": True}
            },
            {
                "name": "housekeeping",
                "display_name": "Housekeeping",
                "description": "Housekeeping staff",
                "level": 9,
                "permissions": page_permissions_for_role("housekeeping"),
                "can_create_roles": [],
                "default_features": {"housekeeping_module": True}
            }
        ]

        for role_data in roles_data:
            role_data["is_default"] = True
            role = Role(**role_data)
            db.add(role)

        await db.commit()
        print("Created initial roles")


async def create_test_data():
    """Create test hotel, branch, zone, and users."""
    async with get_db_session() as db:
        # Check if test data already exists
        from sqlalchemy import text
        result = await db.execute(text("SELECT COUNT(*) FROM hotels"))
        count = result.scalar()
        if count > 0:
            print("Test data already exists, skipping test data creation")

        # Get roles
        # Get all roles
        roles = {}
        role_names = ["product_admin", "super_admin", "admin", "manager", "cashier", "kitchen_staff", "waiters", "inventory_manager", "housekeeping"]
        for role_name in role_names:
            from sqlalchemy import select
            result = await db.execute(select(Role).where(Role.name == role_name))
            roles[role_name] = result.scalar_one_or_none()


        # Create Product Admin user (no hotel/branch association)
        product_admin = User(
            email="productadmin@hotelagent.com",
            password_hash=hash_password("admin123"),
            role_id=roles["product_admin"].id,
            is_active=True,
            feature_toggles={"all": True}
        )
        db.add(product_admin)
        await db.flush()  # Get the ID

        # Create test hotel
        hotel = Hotel(
            name="Test Hotel",
            owner_name="Test Owner",
            gst_number="12ABCDE3456F1Z5",
            address="123 Test Street",
            city="Test City",
            state="Test State",
            country="India",
            pincode="123456",
            phone="9876543210",
            email="test@hotel.com",
            subscription_plan="premium",
            created_by=product_admin.id
        )
        db.add(hotel)
        await db.flush()  # Get the ID

        # Create test branch
        branch = Branch(
            hotel_id=hotel.id,
            name="Main Branch",
            code="MAIN",
            address="123 Test Street",
            city="Test City",
            state="Test State",
            pincode="123456",
            phone="9876543210",
            email="main@hotel.com",
            manager_name="Branch Manager",
            seating_capacity=50,
            operating_hours={
                "monday": {"open": "09:00", "close": "22:00"},
                "tuesday": {"open": "09:00", "close": "22:00"},
                "wednesday": {"open": "09:00", "close": "22:00"},
                "thursday": {"open": "09:00", "close": "22:00"},
                "friday": {"open": "09:00", "close": "23:00"},
                "saturday": {"open": "09:00", "close": "23:00"},
                "sunday": {"open": "10:00", "close": "22:00"}
            }
        )
        db.add(branch)
        await db.flush()  # Get the ID

        # Create users for different roles
        super_admin = User(
            email="superadmin@hotel.com",
            password_hash=hash_password("superadmin123"),
            role_id=roles["super_admin"].id,
            hotel_id=hotel.id,
            is_active=True
        )
        db.add(super_admin)

        admin = User(
            email="admin@mainbranch.com",
            password_hash=hash_password("admin123"),
            role_id=roles["admin"].id,
            hotel_id=hotel.id,
            branch_id=branch.id,
            is_active=True
        )
        db.add(admin)

        manager = User(
            email="manager@dining.com",
            password_hash=hash_password("manager123"),
            role_id=roles["manager"].id,
            hotel_id=hotel.id,
            branch_id=branch.id,
            is_active=True
        )
        db.add(manager)

        cashier = User(
            email="cashier@mainbranch.com",
            password_hash=hash_password("cashier123"),
            role_id=roles["cashier"].id,
            hotel_id=hotel.id,
            branch_id=branch.id,
            is_active=True
        )
        db.add(cashier)

        kitchen_staff = User(
            email="kitchen@mainbranch.com",
            password_hash=hash_password("kitchen123"),
            role_id=roles["kitchen_staff"].id,
            hotel_id=hotel.id,
            branch_id=branch.id,
            is_active=True
        )
        db.add(kitchen_staff)

        waiter = User(
            email="waiter@dining.com",
            password_hash=hash_password("waiter123"),
            role_id=roles["waiters"].id,
            hotel_id=hotel.id,
            branch_id=branch.id,
            is_active=True
        )
        db.add(waiter)

        inventory_manager = User(
            email="inventory@mainbranch.com",
            password_hash=hash_password("inventory123"),
            role_id=roles["inventory_manager"].id,
            hotel_id=hotel.id,
            branch_id=branch.id,
            is_active=True
        )
        db.add(inventory_manager)

        housekeeping = User(
            email="housekeeping@mainbranch.com",
            password_hash=hash_password("housekeeping123"),
            role_id=roles["housekeeping"].id,
            hotel_id=hotel.id,
            branch_id=branch.id,
            is_active=True
        )
        db.add(housekeeping)

        await db.commit()

        print("Created test data:")
        print(f"- Hotel: {hotel.name} (ID: {hotel.id})")
        print(f"- Branch: {branch.name} (ID: {branch.id})")
        print(f"- Product Admin: {product_admin.email} / admin123")
        print(f"- Super Admin: {super_admin.email} / superadmin123")
        print(f"- Admin: {admin.email} / admin123")
        print(f"- Manager: {manager.email} / manager123")
        print(f"- Cashier: {cashier.email} / cashier123")
        print(f"- Kitchen Staff: {kitchen_staff.email} / kitchen123")
        print(f"- Waiter: {waiter.email} / waiter123")
        print(f"- Inventory Manager: {inventory_manager.email} / inventory123")
        print(f"- Housekeeping: {housekeeping.email} / housekeeping123")



async def main():
    """Main initialization function."""
    try:
        print("Initializing HotelAgent database...")

        
        # Initialize database connection
        await init_database()
        print("Database connection initialized")
        
        # Create tables
        await create_tables()
        print("Database tables created")
        
        # Create initial roles
        await create_initial_roles()
        
        # Create test data
        await create_test_data()
        
        print("\nDatabase initialization completed successfully!")
        print("\nYou can now test the login endpoint with:")
        print("POST http://localhost:8000/api/v1/auth/login")
        print('{"email": "admin@example.com", "password": "securepassword123"}')
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())