#!/usr/bin/env python
"""
Test script for JWT-based ID assignment in user creation.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.auth import create_access_token, TokenPayload
from app.models.core.user import User
from app.models.core.auth import Role
from app.services.core.user import create_unified_user
from app.core.database import get_db
from app.settings.constants import RoleNames


async def test_jwt_id_assignment():
    """Test JWT-based ID assignment for user creation."""
    print("\n=== Testing JWT-based ID Assignment ===\n")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create a mock product admin user for testing
        product_admin_role = await db.execute(f"SELECT * FROM roles WHERE name = '{RoleNames.PRODUCT_ADMIN}'")
        product_admin_role = product_admin_role.fetchone()
        
        if not product_admin_role:
            print("Error: Product Admin role not found in database.")
            return
        
        # Create a mock product admin user
        mock_product_admin = User(
            email="test_product_admin@example.com",
            password_hash="hashed_password",  # In a real scenario, this would be properly hashed
            role_id=product_admin_role.id,
            is_active=True
        )
        
        # Create a token payload with hierarchical IDs
        token_payload = TokenPayload(
            user_id=1,  # Mock user ID
            role_name=RoleNames.PRODUCT_ADMIN,
            type="access",
            hotel_id=100,  # Mock hotel ID
            branch_id=200,  # Mock branch ID
            zone_id=300,  # Mock zone ID
            floor_id=400,  # Mock floor ID
            section_id=500  # Mock section ID
        )
        
        print("Created mock product admin user and token payload:")
        print(f"Token Payload: {token_payload}")
        
        # Test creating a user with JWT-based ID assignment
        print("\nTesting user creation with JWT-based ID assignment...")
        
        # Test case 1: Create user with explicit IDs
        print("\nTest Case 1: Create user with explicit IDs")
        new_user_1 = await create_unified_user(
            creator=mock_product_admin,
            role_name=RoleNames.MANAGER,
            email="test_manager_1@example.com",
            db=db,
            creator_token_payload=token_payload,
            branch_id=201,  # Different from token payload
            zone_id=301  # Different from token payload
        )
        
        print(f"User created with explicit IDs:")
        print(f"  hotel_id: {new_user_1.hotel_id} (Expected: 100 from token)")
        print(f"  branch_id: {new_user_1.branch_id} (Expected: 201 from explicit parameter)")
        print(f"  zone_id: {new_user_1.zone_id} (Expected: 301 from explicit parameter)")
        
        # Test case 2: Create user without explicit IDs (should use token payload)
        print("\nTest Case 2: Create user without explicit IDs")
        new_user_2 = await create_unified_user(
            creator=mock_product_admin,
            role_name=RoleNames.CASHIER,
            email="test_cashier_1@example.com",
            db=db,
            creator_token_payload=token_payload
        )
        
        print(f"User created without explicit IDs:")
        print(f"  hotel_id: {new_user_2.hotel_id} (Expected: 100 from token)")
        print(f"  branch_id: {new_user_2.branch_id} (Expected: 200 from token)")
        print(f"  zone_id: {new_user_2.zone_id} (Expected: 300 from token)")
        
        print("\n=== JWT-based ID Assignment Test Completed ===\n")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        # Clean up test data (in a real test, you would delete the created users)
        # await db.execute("DELETE FROM users WHERE email LIKE 'test_%@example.com'")
        # await db.commit()
        db.close()


if __name__ == "__main__":
    asyncio.run(test_jwt_id_assignment())