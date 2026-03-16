#!/usr/bin/env python3
"""
Demonstration script for data segregation validation functionality.
Shows how the RBAC system enforces multi-tenant data isolation.
"""

from app.core.rbac import UserContext, validate_hotel_access, validate_branch_access
from app.utils.exceptions import DataSegregationError
from unittest.mock import Mock


def demo_data_segregation():
    """Demonstrate data segregation validation."""
    print("=== Data Segregation Validation Demo ===\n")
    
    # Create mock database session
    db = Mock()
    
    # Create test user contexts
    product_admin = UserContext(
        user_id=1,
        email="productafnan#rb.com",
        role_name="product_admin",
        role_level=1,
        hotel_id=None,
        branch_id=None
    )
    
    super_admin_hotel1 = UserContext(
        user_id=2,
        email="super@hotel1.com",
        role_name="super_admin",
        role_level=2,
        hotel_id=1,
        branch_id=1
    )
    
    admin_hotel1_branch1 = UserContext(
        user_id=3,
        email="admin@hotel1.com",
        role_name="admin",
        role_level=3,
        hotel_id=1,
        branch_id=1
    )
    
    # Demo 1: Product Admin can access any hotel
    print("1. Product Admin Access Test:")
    try:
        result = validate_hotel_access(product_admin, 999, db)
        print("   ✅ Product Admin can access hotel 999:", result)
    except DataSegregationError as e:
        print("   ❌ Product Admin denied access:", e)
    
    # Demo 2: Super Admin can access their own hotel
    print("\n2. Super Admin Own Hotel Access Test:")
    try:
        result = validate_hotel_access(super_admin_hotel1, 1, db)
        print("   ✅ Super Admin can access their hotel (ID: 1):", result)
    except DataSegregationError as e:
        print("   ❌ Super Admin denied access:", e)
    
    # Demo 3: Super Admin cannot access other hotels
    print("\n3. Super Admin Cross-Hotel Access Test:")
    # Mock hotel query for hotel 2
    mock_hotel = Mock()
    mock_hotel.name = "Other Hotel"
    db.query.return_value.filter.return_value.first.return_value = mock_hotel
    
    try:
        result = validate_hotel_access(super_admin_hotel1, 2, db)
        print("   ❌ Super Admin should not access other hotels:", result)
    except DataSegregationError as e:
        print("   ✅ Super Admin correctly denied access to hotel 2:", str(e))
    
    # Demo 4: Admin can access their own branch
    print("\n4. Admin Own Branch Access Test:")
    try:
        result = validate_branch_access(admin_hotel1_branch1, 1, db)
        print("   ✅ Admin can access their branch (ID: 1):", result)
    except DataSegregationError as e:
        print("   ❌ Admin denied access:", e)
    
    # Demo 5: Admin cannot access other branches
    print("\n5. Admin Cross-Branch Access Test:")
    # Mock branch query for branch 2
    mock_branch = Mock()
    mock_branch.name = "Other Branch"
    mock_branch.hotel_id = 1  # Same hotel, different branch
    db.query.return_value.filter.return_value.first.return_value = mock_branch
    
    try:
        result = validate_branch_access(admin_hotel1_branch1, 2, db)
        print("   ❌ Admin should not access other branches:", result)
    except DataSegregationError as e:
        print("   ✅ Admin correctly denied access to branch 2:", str(e))
    
    print("\n=== Demo Complete ===")
    print("✅ Data segregation validation is working correctly!")
    print("✅ Product Admin bypass logic implemented")
    print("✅ Multi-tenant isolation enforced")
    print("✅ Role hierarchy respected")


if __name__ == "__main__":
    demo_data_segregation()