"""Test script for the unified user API endpoints."""

import asyncio
import httpx
import json
from typing import Dict, Any

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Test credentials - using existing users from the system
PRODUCT_ADMIN_EMAIL = "productadmin@mail.com"
PRODUCT_ADMIN_PASSWORD = "afnan123"

# Alternative credentials if product admin doesn't work
SUPER_ADMIN_EMAIL = "afnan@superadmin.com"
SUPER_ADMIN_PASSWORD = "superafnan"

# Test data
TEST_SUPER_ADMIN = {
    "role_name": "super_admin",
    "email": "test_super_admin@example.com",
    "password": "password123",
    "hotel_name": "Test Hotel",
    "owner_name": "Test Owner",
    "hotel_location": "Test Location",
    "gst_number": "TEST12345"
}

TEST_ADMIN = {
    "role_name": "admin",
    "email": "test_admin@example.com",
    "password": "password123",
    "branch_id": 1
}

TEST_MANAGER = {
    "role_name": "manager",
    "email": "test_manager@example.com",
    "password": "password123",
    "branch_id": 1,
    "zone_id": 1
}

TEST_STAFF = {
    "role_name": "cashier",
    "email": "test_cashier@example.com",
    "password": "password123",
    "branch_id": 1,
    "zone_id": 1
}


async def login(email: str, password: str) -> Dict[str, Any]:
    """Login and get access token."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Login failed: {response.text}")
                return None
        except httpx.TimeoutException:
            print(f"Login request timed out for {email}")
            return None


async def create_user(token: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a user using the unified endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/users/create",
                json=user_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Create user response: {response.status_code}")
            return response.json() if response.status_code < 400 else response.text
        except httpx.TimeoutException:
            print(f"Create user request timed out for {user_data.get('email')}")
            return f"Request timed out for {user_data.get('email')}"


async def update_user(token: str, user_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a user using the unified endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.put(
                f"{BASE_URL}/users/update/{user_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Update user response: {response.status_code}")
            return response.json() if response.status_code < 400 else response.text
        except httpx.TimeoutException:
            print(f"Update user request timed out for user ID {user_id}")
            return f"Request timed out for user ID {user_id}"


async def delete_user(token: str, user_id: int) -> Dict[str, Any]:
    """Delete a user using the unified endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.delete(
                f"{BASE_URL}/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Delete user response: {response.status_code}")
            return response.json() if response.status_code < 400 else response.text
        except httpx.TimeoutException:
            print(f"Delete user request timed out for user ID {user_id}")
            return f"Request timed out for user ID {user_id}"


async def main():
    """Run the test script."""
    print("Testing unified user API endpoints...")
    
    # Try to login with product admin first
    print("\nLogging in as product admin...")
    login_result = await login(PRODUCT_ADMIN_EMAIL, PRODUCT_ADMIN_PASSWORD)
    
    # If product admin login fails, try super admin
    if not login_result:
        print("Product admin login failed, trying super admin...")
        login_result = await login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        
    if not login_result:
        print("All login attempts failed. Exiting.")
        return
    
    admin_token = login_result["data"]["access_token"]
    print(f"Login successful. Token: {admin_token[:10]}...")
    
    # Create super admin
    print("\nCreating super admin...")
    super_admin_result = await create_user(admin_token, TEST_SUPER_ADMIN)
    print(f"Super admin creation result: {json.dumps(super_admin_result, indent=2) if not isinstance(super_admin_result, str) else super_admin_result}")
    
    if isinstance(super_admin_result, str):
        print("Failed to create super admin. Continuing with other tests...")
        super_admin_id = None
    else:
        super_admin_id = super_admin_result["data"]["id"]
    
    # Test creating admin with the admin token
    print("\nCreating admin...")
    admin_result = await create_user(admin_token, TEST_ADMIN)
    print(f"Admin creation result: {json.dumps(admin_result, indent=2) if not isinstance(admin_result, str) else admin_result}")
    
    if isinstance(admin_result, str):
        print("Failed to create admin. Continuing with other tests...")
        admin_id = None
    else:
        admin_id = admin_result["data"]["id"]
        
        # Try to login as the newly created admin
        print("\nLogging in as admin...")
        admin_login = await login(TEST_ADMIN["email"], TEST_ADMIN["password"])
        if admin_login:
            admin_token = admin_login["data"]["access_token"]
            print(f"Logged in as admin. Token: {admin_token[:10]}...")
            
            # Create manager with admin token
            print("\nCreating manager...")
            manager_result = await create_user(admin_token, TEST_MANAGER)
            print(f"Manager creation result: {json.dumps(manager_result, indent=2) if not isinstance(manager_result, str) else manager_result}")
            
            if not isinstance(manager_result, str):
                manager_id = manager_result["data"]["id"]
                
                # Try to login as the newly created manager
                print("\nLogging in as manager...")
                manager_login = await login(TEST_MANAGER["email"], TEST_MANAGER["password"])
                if manager_login:
                    manager_token = manager_login["data"]["access_token"]
                    print(f"Logged in as manager. Token: {manager_token[:10]}...")
                    
                    # Create staff with manager token
                    print("\nCreating staff...")
                    staff_result = await create_user(manager_token, TEST_STAFF)
                    print(f"Staff creation result: {json.dumps(staff_result, indent=2) if not isinstance(staff_result, str) else staff_result}")
                    
                    if not isinstance(staff_result, str):
                        staff_id = staff_result["data"]["id"]
                        
                        # Test update and delete operations
                        print("\nUpdating staff...")
                        update_result = await update_user(manager_token, staff_id, {"is_active": False})
                        print(f"Staff update result: {json.dumps(update_result, indent=2) if not isinstance(update_result, str) else update_result}")
                        
                        print("\nDeleting staff...")
                        delete_result = await delete_user(manager_token, staff_id)
                        print(f"Staff deletion result: {json.dumps(delete_result, indent=2) if not isinstance(delete_result, str) else delete_result}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())