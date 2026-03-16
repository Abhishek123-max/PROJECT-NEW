"""
Database seeding script for HotelAgent authentication system.
Creates initial roles, default Product Admin user, and sample data.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database, get_db_session, create_tables
from app.models.core.user import User
from app.models.core.auth import Role, Hotel, Branch
from app.settings.constants import (
    RoleNames,
    SUBSCRIPTION_FEATURES,
    DEFAULT_PAGE_PERMISSIONS,
    get_role_level,
    DEFAULT_CAN_CREATE_ROLES,
    DEFAULT_ROLE_FEATURES,
    ROLE_PERMISSIONS,
    page_permissions_for_role,
)
from app.utils.helpers import hash_password


class DatabaseSeeder:
    """Database seeding utility class."""
    
    def __init__(self):
        self.roles_created = {}
        self.hotels_created = {}
        self.branches_created = {}
        self.users_created = {}

    async def seed_all(self, create_sample_data: bool = False) -> None:
        """
        Seed all initial data.
        
        Args:
            create_sample_data: Whether to create sample hotels and users
        """
        print("🌱 Starting database seeding...")
        
        try:
            # Initialize database
            await init_database()
            
            # Create tables if they don't exist
            # await create_tables()  # Schema management should be handled by Alembic migrations.
            # print("✅ Database tables created/verified")
            
            async with get_db_session() as session:
                # Seed roles
                await self.seed_roles(session)
                
                # Seed Product Admin user
                await self.seed_product_admin(session)
                
                # Retroactively assign the product_admin as the creator of the default roles
                await self.update_roles_creator(session)
                
                # Optionally create sample data
                if create_sample_data:
                    await self.seed_sample_data(session)
                
                await session.commit()
                print("✅ Database seeding completed successfully!")
                
        except Exception as e:
            print(f"❌ Database seeding failed: {e}")
            raise

    async def seed_roles(self, session) -> None:
        """Create all system roles with proper hierarchy and permissions."""
        print("📋 Seeding roles...")
        
        for role_name, permissions in DEFAULT_ROLE_FEATURES.items():
            # Check if role already exists
            from sqlalchemy import select
            result = await session.execute(
                select(Role).filter(Role.name == role_name)
            )
            existing_role = result.scalar_one_or_none()
            permissions = page_permissions_for_role(role_name)
            can_create = DEFAULT_CAN_CREATE_ROLES.get(role_name, [])
            default_features = DEFAULT_ROLE_FEATURES.get(role_name, {})

            if existing_role:
                print(f"   🔄 Role '{role_name}' already exists, updating permissions...")
                existing_role.can_create_roles = can_create
                existing_role.default_features = default_features
                existing_role.permissions = permissions  # Ensure permissions are also up-to-date
                self.roles_created[role_name] = existing_role
                print(f"     - Updated 'can_create_roles' to: {can_create}")
                continue
            
            # Create new role
            role = Role(
                name=role_name,
                display_name=role_name.replace('_', ' ').title(),
                description=f"System-defined {role_name.replace('_', ' ').title()} role.",
                level=get_role_level(role_name),
                permissions=permissions,
                can_create_roles=can_create,
                default_features=default_features,
                is_default=True,
            )
            
            session.add(role)
            await session.flush()  # Get the ID
            
            self.roles_created[role_name] = role
            print(f"   ✅ Created role: {role.display_name} (Level {role.level})")
        
        print(f"✅ Created {len(self.roles_created)} roles")

        # --- Ensure core system roles (by RoleNames constants) exist ---
        # These are the logical roles used throughout the system (e.g. 'product_admin').
        # The page-based DEFAULT_PAGE_PERMISSIONS keys are different (they're page names),
        # so we must also create the actual role entities for RoleNames.
        core_roles = [
            RoleNames.PRODUCT_ADMIN,
            RoleNames.SUPER_ADMIN,
            RoleNames.ADMIN,
            RoleNames.MANAGER,
            RoleNames.CASHIER,
            RoleNames.KITCHEN_STAFF,
            RoleNames.WAITERS,
            RoleNames.INVENTORY_MANAGER,
            RoleNames.HOUSEKEEPING,
        ]
        
        from sqlalchemy import select
        core_created = 0
        for core_name in core_roles:
            # Skip if already tracked in this run
            if core_name in self.roles_created:
                continue

            # Check DB for existing role entity with that name
            res = await session.execute(select(Role).filter(Role.name == core_name))
            rows = res.scalars().all()
            if rows:
                if len(rows) > 1:
                    print(f"   ⚠️  Multiple roles found for '{core_name}'; using the first one.")
                existing = rows[0]
                self.roles_created[core_name] = existing
                continue

            # Build role data from constants
            role_permissions = page_permissions_for_role(core_name)
            can_create = DEFAULT_CAN_CREATE_ROLES.get(core_name, [])
            role_features = DEFAULT_ROLE_FEATURES.get(core_name, {})

            role = Role(
                name=core_name,
                display_name=core_name.replace('_', ' ').title(),
                description=f"System role: {core_name}",
                level=get_role_level(core_name),
                permissions=role_permissions,
                can_create_roles=can_create,
                default_features=role_features,
                is_default=True,
            )

            session.add(role)
            await session.flush()
            self.roles_created[core_name] = role
            core_created += 1
            print(f"   ✅ Created core role: {role.display_name} (Level {role.level})")

        if core_created > 0:
            print(f"✅ Created {core_created} core roles")

    async def seed_product_admin(self, session) -> None:
        """Create the hardcoded Product Admin user."""
        print("👤 Seeding Product Admin user...")
        
        # Check if Product Admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).filter(User.username == "productadmin@rb.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("   ⏭️  Product Admin user already exists, skipping...")
            self.users_created["product_admin"] = existing_user
            return
        
        # Get Product Admin role
        product_admin_role = self.roles_created.get(RoleNames.PRODUCT_ADMIN)
        if not product_admin_role:
            raise ValueError("Product Admin role not found. Seed roles first.")
        
        # Create Product Admin user
        hashed_password = hash_password("admin123")
        
        product_admin = User(
            username="productadmin@rb.com",
            contact_email="productadmin@rb.com",
            password_hash=hashed_password,
            role_id=product_admin_role.id, hotel_id=None,  # Product Admin has no hotel restriction
            branch_id=None,
            feature_toggles=product_admin_role.default_features,
            created_by=None,  # Self-created
            is_active=True,
            is_one_time_password=False # Explicitly set for seeded user
        )
        
        session.add(product_admin)
        await session.flush()
        
        self.users_created["product_admin"] = product_admin
        print("   ✅ Created Product Admin user: productadmin@rb.com")

    async def update_roles_creator(self, session) -> None:
        """Sets the product_admin as the creator for all default roles that lack one."""
        print("🏷️  Updating default roles with creator...")
        product_admin = self.users_created.get("product_admin")
        if not product_admin:
            print("   ⚠️ Product admin user not found, skipping role creator update.")
            return

        # Instead of iterating over self.roles_created, which only contains roles
        # processed in this specific run, we query all roles from the database.
        # This makes the function idempotent and ensures it fixes roles created
        # by older, incomplete seeding scripts.
        from sqlalchemy import select
        all_roles_result = await session.execute(select(Role))
        all_roles = all_roles_result.scalars().all()

        updated_count = 0
        for role in all_roles:
            if role.created_by is None:
                role.created_by = product_admin.id
                updated_count += 1
                print(f"   - Set creator for '{role.name}' to Product Admin (ID: {product_admin.id})")
        
        if updated_count > 0:
            print(f"   ✅ Updated creator for {updated_count} roles.")
        else:
            print("   ⏭️  All roles already have a creator assigned.")

    async def seed_sample_data(self, session) -> None:
        """Create sample hotels, branches, and users for testing."""
        print("🏨 Seeding sample data...")
        
        # Create sample hotel
        await self.create_sample_hotel(session)
        
        # Create sample branches
        await self.create_sample_branches(session)
        
        # Create sample users
        await self.create_sample_users(session)

    async def create_sample_hotel(self, session) -> None:
        """Create a sample hotel."""
        print("   🏨 Creating sample hotel...")
        
        product_admin = self.users_created["product_admin"]
        
        sample_hotel = Hotel(name="Grand Palace Hotel",
                             owner_name="Rajesh Kumar",
                             gst_number="29ABCDE1234F1Z5",
                             address_line_1="123 MG Road",
                             city="Bangalore",
                             state="Karnataka",
                             country="India",
                             pincode="560001",
                             phone="+91-80-12345678",
                             email="info@grandpalace.com",
                             subscription_plan="premium",
                             is_active=True,
                             created_by=product_admin.id)
        
        session.add(sample_hotel)
        await session.flush()
        
        self.hotels_created["sample_hotel"] = sample_hotel
        print(f"   ✅ Created sample hotel: {sample_hotel.name}")

    async def create_sample_branches(self, session) -> None:
        """Create sample branches for the hotel."""
        print("   🏢 Creating sample branches...")
        
        sample_hotel = self.hotels_created["sample_hotel"]
        
        branches_data = [
            {
                "name": "Main Branch", "code": "MAIN",
                "address_line_1": "123 MG Road",
                "area": "MG Road Area", "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560001",
                "phone": "+91-80-12345678",
                "email": "main@grandpalace.com",
                "admin_name": "Suresh Reddy",
                "seating_capacity": 100,
            },
            {
                "name": "Airport Branch", "code": "AIRPORT",
                "address_line_1": "Kempegowda International Airport",
                "area": "Airport Area", "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560300",
                "phone": "+91-80-87654321",
                "email": "airport@grandpalace.com",
                "admin_name": "Priya Sharma",
                "seating_capacity": 60,
            }
        ]
        
        for branch_data in branches_data:
            branch = Branch(
                hotel_id=sample_hotel.id,
                name=branch_data["name"],
                code=branch_data["code"], address_line_1=branch_data["address_line_1"],
                area=branch_data["area"],
                city=branch_data["city"],
                state=branch_data["state"],
                pincode=branch_data["pincode"],
                phone=branch_data["phone"],
                email=branch_data["email"],
                admin_name=branch_data["admin_name"],
                seating_capacity=branch_data["seating_capacity"],
                operating_hours={ # Example operating hours
                    "monday": {"open": "06:00", "close": "23:00"},
                    "tuesday": {"open": "06:00", "close": "23:00"},
                    "wednesday": {"open": "06:00", "close": "23:00"},
                    "thursday": {"open": "06:00", "close": "23:00"},
                    "friday": {"open": "06:00", "close": "23:00"},
                    "saturday": {"open": "06:00", "close": "23:00"},
                    "sunday": {"open": "06:00", "close": "23:00"}
                },
                is_active=True,
                created_by=self.users_created["product_admin"].id
            )
            
            session.add(branch)
            await session.flush()
            
            self.branches_created[branch_data["code"]] = branch
            print(f"   ✅ Created branch: {branch.name}")

    async def create_sample_users(self, session) -> None:
        """Create sample users with different roles."""
        print("   👥 Creating sample users...")
        
        sample_hotel = self.hotels_created["sample_hotel"]
        main_branch = self.branches_created["MAIN"]
        
        # Sample users data
        users_data = [
            {
                "email": "superadmin@grandpalace.com",
                "password": "admin123",
                "role": RoleNames.SUPER_ADMIN,
                "hotel_id": sample_hotel.id,
                "branch_id": None,
            },
            {
                "email": "admin@grandpalace.com",
                "password": "admin123",
                "role": RoleNames.ADMIN,
                "hotel_id": sample_hotel.id,
                "branch_id": main_branch.id,
            },
            {
                "email": "manager@grandpalace.com",
                "password": "manager123",
                "role": RoleNames.MANAGER,
                "hotel_id": sample_hotel.id,
                "branch_id": main_branch.id,
            },
            {
                "email": "cashier@grandpalace.com",
                "password": "cashier123",
                "role": RoleNames.CASHIER,
                "hotel_id": sample_hotel.id,
                "branch_id": main_branch.id,
            },
            {
                "email": "kitchen@grandpalace.com",
                "password": "kitchen123",
                "role": RoleNames.KITCHEN_STAFF,
                "hotel_id": sample_hotel.id,
                "branch_id": main_branch.id,
            },
            {
                "email": "waiter@grandpalace.com",
                "password": "waiter123",
                "role": RoleNames.WAITERS,
                "hotel_id": sample_hotel.id,
                "branch_id": main_branch.id,
            }
        ]
        
        product_admin = self.users_created["product_admin"]
        
        for user_data in users_data:
            # Get role
            role = self.roles_created[user_data["role"]]
            
            # Hash password
            hashed_password = hash_password(user_data["password"])
            
            # Get subscription features
            subscription_features = SUBSCRIPTION_FEATURES.get(sample_hotel.subscription_plan, {})
            
            # Merge role features with subscription features
            user_features = role.default_features.copy()
            for feature, enabled in subscription_features.items():
                if feature in user_features:
                    user_features[feature] = user_features[feature] and enabled
            
            # Create user
            user = User(
                username=user_data["email"], # Use email as username for sample data
                contact_email=user_data["email"],
                password_hash=hashed_password,
                role_id=role.id,
                hotel_id=user_data["hotel_id"],
                branch_id=user_data["branch_id"],
                feature_toggles=user_features,
                created_by=product_admin.id,
                is_active=True,
                is_one_time_password=False # Seeded users have known passwords
            )
            
            session.add(user)
            await session.flush()
            
            self.users_created[user_data["role"]] = user
            print(f"   ✅ Created user: {user.email} ({role.display_name})")

    async def cleanup_existing_data(self, session) -> None:
        """Clean up existing data (use with caution!)."""
        print("🧹 Cleaning up existing data...")
        
        # Delete in reverse dependency order
        await session.execute("DELETE FROM refresh_tokens")
        await session.execute("DELETE FROM audit_logs")
        await session.execute("DELETE FROM users WHERE username != 'productadmin@rb.com'")
        await session.execute("DELETE FROM branches")
        await session.execute("DELETE FROM hotels")
        
        print("✅ Existing data cleaned up")


async def main():
    """Main seeding function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed HotelAgent database")
    parser.add_argument("--sample-data", action="store_true", help="Create sample data")
    parser.add_argument("--cleanup", action="store_true", help="Clean up existing data first")
    
    args = parser.parse_args()
    
    seeder = DatabaseSeeder()
    
    try:
        if args.cleanup:
            async with get_db_session() as session:
                await seeder.cleanup_existing_data(session)
                await session.commit()
        
        await seeder.seed_all(create_sample_data=args.sample_data)
        
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())