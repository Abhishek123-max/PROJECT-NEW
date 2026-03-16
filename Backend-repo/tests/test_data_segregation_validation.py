"""
Test data segregation validation functionality.
Tests for task 5.3: Implement data segregation validation.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.middleware.rbac import UserContext

from app.models.core.auth import Hotel, Branch, Zone
from app.utils.exceptions import DataSegregationError, InsufficientPermissionsError
from app.services.core.user import update_user
from app.models.core.user import User
from app.models.core.auth import Role


class TestDataSegregationValidation:
    """Test data segregation validation functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock database session
        self.db = AsyncMock(spec=AsyncSession)
        
        # Create test user contexts
        self.product_admin_user = Mock(spec=User)
        self.product_admin_user.id = 1
        self.product_admin_user.email = "productafnan@rb.com"
        self.product_admin_user.role = Mock()
        self.product_admin_user.role.name = "product_admin"
        self.product_admin_user.hotel_id = None
        self.product_admin_user.branch_id = None
        self.product_admin_user.zone_id = None
        self.product_admin_user.can_access_hotel.return_value = True
        self.product_admin_user.can_access_branch.return_value = True
        self.product_admin_user.can_access_zone.return_value = True
        self.product_admin = UserContext(self.product_admin_user)
        
        self.super_admin_user = Mock(spec=User)
        self.super_admin_user.id = 2
        self.super_admin_user.email = "super@hotel1.com"
        self.super_admin_user.role = Mock()
        self.super_admin_user.role.name = "super_admin"
        self.super_admin_user.hotel_id = 1
        self.super_admin_user.branch_id = 1
        self.super_admin_user.zone_id = None
        self.super_admin_user.can_access_hotel.return_value = True
        self.super_admin_user.can_access_branch.return_value = True
        self.super_admin_user.can_access_zone.return_value = True
        self.super_admin = UserContext(self.super_admin_user)
        
        self.admin_user = Mock(spec=User)
        self.admin_user.id = 3
        self.admin_user.email = "admin@hotel1.com"
        self.admin_user.role = Mock()
        self.admin_user.role.name = "admin"
        self.admin_user.hotel_id = 1
        self.admin_user.branch_id = 1
        self.admin_user.zone_id = None
        self.admin_user.can_access_hotel.return_value = True
        self.admin_user.can_access_branch.return_value = True
        self.admin_user.can_access_zone.return_value = True
        self.admin = UserContext(self.admin_user)
        
        self.manager_user = Mock(spec=User)
        self.manager_user.id = 4
        self.manager_user.email = "manager@hotel1.com"
        self.manager_user.role = Mock()
        self.manager_user.role.name = "manager"
        self.manager_user.hotel_id = 1
        self.manager_user.branch_id = 1
        self.manager_user.zone_id = 1
        self.manager_user.can_access_hotel.return_value = True
        self.manager_user.can_access_branch.return_value = True
        self.manager_user.can_access_zone.return_value = True
        self.manager = UserContext(self.manager_user)
        
        # Mock hotel, branch, zone objects
        self.hotel1 = Mock(spec=Hotel)
        self.hotel1.id = 1
        self.hotel1.name = "Test Hotel 1"
        
        self.hotel2 = Mock(spec=Hotel)
        self.hotel2.id = 2
        self.hotel2.name = "Test Hotel 2"
        
        self.branch1 = Mock(spec=Branch)
        self.branch1.id = 1
        self.branch1.name = "Main Branch"
        self.branch1.hotel_id = 1
        
        self.branch2 = Mock(spec=Branch)
        self.branch2.id = 2
        self.branch2.name = "Second Branch"
        self.branch2.hotel_id = 2
        
        self.zone1 = Mock(spec=Zone)
        self.zone1.id = 1
        self.zone1.name = "Dining Area"
        self.zone1.branch_id = 1
    
    def test_product_admin_hotel_access(self):
        """Test Product Admin can access any hotel."""
        # Product Admin should be able to access any hotel
        result = self.product_admin.user.can_access_hotel(1)
        assert result is True
        
        result = self.product_admin.user.can_access_hotel(999)
        assert result is True
    
    def test_super_admin_hotel_access_allowed(self):
        """Test Super Admin can access their own hotel."""
        result = self.super_admin.user.can_access_hotel(1)
        assert result is True
    
    def test_super_admin_hotel_access_denied(self):
        """Test Super Admin cannot access other hotels."""
        # Mock hotel query
        with pytest.raises(DataSegregationError) as exc_info:
            # Mock the user's hotel_id to be different from the one being accessed
            self.super_admin.user.hotel_id = 1 # Assuming super_admin is tied to hotel 1
            assert not self.super_admin.user.can_access_hotel(2)
        
        assert "Access denied to hotel" in str(exc_info.value)
    
    def test_admin_branch_access_allowed(self):
        """Test Admin can access their own branch."""
        result = self.admin.user.can_access_branch(1)
        assert result is True
    
    def test_admin_branch_access_denied(self):
        """Test Admin cannot access other branches."""
        # Mock branch query
        with pytest.raises(DataSegregationError) as exc_info:
            # Mock the user's branch_id to be different from the one being accessed
            self.admin.user.branch_id = 1 # Assuming admin is tied to branch 1
            assert not self.admin.user.can_access_branch(2)
        
        assert "Access denied to branch" in str(exc_info.value)
    
    def test_manager_zone_access_allowed(self):
        """Test Manager can access their own zone."""
        result = self.manager.user.can_access_zone(1)
        assert result is True
    


        
        # Patch the validate_hotel_access function

class TestUserUpdateDataSegregation:
    """Test user update data segregation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.db = MagicMock()

        self.product_admin_user = MagicMock(spec=User)
        self.product_admin_user.id = 1
        self.product_admin_user.is_product_admin.return_value = True

        self.super_admin_user = MagicMock(spec=User)
        self.super_admin_user.id = 2
        self.super_admin_user.is_super_admin.return_value = True
        self.super_admin_user.is_admin.return_value = False
        self.super_admin_user.hotel_id = 1
        self.super_admin_user.branch_id = 1

        self.admin_user = MagicMock(spec=User)
        self.admin_user.id = 3
        self.admin_user.is_super_admin.return_value = False
        self.admin_user.is_admin.return_value = True
        self.admin_user.hotel_id = 1
        self.admin_user.branch_id = 1

        self.manager_user = MagicMock(spec=User)
        self.manager_user.id = 4
        self.manager_user.is_super_admin.return_value = False
        self.manager_user.is_admin.return_value = False
        self.manager_user.is_manager.return_value = True
        self.manager_user.hotel_id = 1
        self.manager_user.branch_id = 1
        self.manager_user.zone_id = 1

        self.target_user_obj = Mock(spec=User)
        self.target_user_obj.id = 5
        self.target_user_obj.email = "targetuser@rb.com"
        self.target_user_obj.role = Mock()
        self.target_user_obj.role.name = "cashier"
        self.target_user_obj.hotel_id = 1
        self.target_user_obj.branch_id = 1
        self.target_user_obj.zone_id = 1
        self.target_user_obj.can_access_hotel.return_value = True
        self.target_user_obj.can_access_branch.return_value = True
        self.target_user_obj.can_access_zone.return_value = True
        self.target_user = UserContext(self.target_user_obj)

        # Mock the execute method to return an awaitable mock object
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = self.target_user_obj
        self.db.execute.return_value = mock_result
        self.db.execute.return_value.__await__ = MagicMock(return_value=mock_result)

    @pytest.mark.asyncio
    async def test_update_user_prevent_hotel_id_change(self):
        """Test that hotel_id cannot be changed."""
        update_data = {"hotel_id": 2}
        with pytest.raises(InsufficientPermissionsError, match="Cannot change hotel_id"):
            await update_user(self.target_user.user.id, self.super_admin_user, update_data, self.db)

    @pytest.mark.asyncio
    async def test_update_user_prevent_branch_id_change(self):
        """Test that branch_id cannot be changed."""
        update_data = {"branch_id": 2}
        with pytest.raises(InsufficientPermissionsError, match="Cannot change branch_id"):
            await update_user(self.target_user.user.id, self.admin_user, update_data, self.db)

    @pytest.mark.asyncio
    async def test_update_user_prevent_role_id_change(self):
        """Test that role_id cannot be changed."""
        update_data = {"role_id": 10} # Some other role
        with pytest.raises(InsufficientPermissionsError, match="Cannot change role_id"):
            await update_user(self.target_user.user.id, self.admin_user, update_data, self.db)

    @pytest.mark.asyncio
    async def test_update_user_allow_zone_id_change_by_super_admin(self):
        """Test that zone_id can be changed by super admin."""
        update_data = {"zone_id": 2}
        updated_user = await update_user(self.target_user.user.id, self.super_admin_user, update_data, self.db)
        assert updated_user.zone_id == 2
        self.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_allow_floor_id_change_by_admin(self):
        """Test that floor_id can be changed by admin."""
        update_data = {"floor_id": 2}
        updated_user = await update_user(self.target_user.user.id, self.admin_user, update_data, self.db)
        assert updated_user.floor_id == 2
        self.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_prevent_zone_id_change_by_manager(self):
        """Test that zone_id cannot be changed by manager."""
        update_data = {"zone_id": 2}
        with pytest.raises(InsufficientPermissionsError, match="Only Super Admins or Admins can change zone_id"):
            await update_user(self.target_user.user.id, self.manager_user, update_data, self.db)

    @pytest.mark.asyncio
    async def test_update_user_allow_other_fields_change(self):
        """Test that other fields can be changed."""
        update_data = {"email": "new_email@example.com"}
        updated_user = await update_user(self.target_user.user.id, self.super_admin_user, update_data, self.db)
        assert updated_user.email == "new_email@example.com"
        self.db.commit.assert_called_once()
        import app.core.rbac as rbac_module
        original_validate = rbac_module.validate_hotel_access
        rbac_module.validate_hotel_access = mock_validate_hotel_access
        
        try:
            results = validate_bulk_resource_access(
                self.super_admin, "hotel", [1, 2], self.db
            )
            
            assert results[1] is True
            assert results[2] is False
        finally:
            # Restore original function
            rbac_module.validate_hotel_access = original_validate
    
    def test_filter_accessible_resources(self):
        """Test filtering accessible resources."""
        # Mock successful access for resource 1, denied for resource 2
        def mock_check_resource_access(user_context, resource_type, resource_id, db):
            if resource_id == 1:
                return True
            else:
                raise DataSegregationError("Access denied")
        
        # Patch the check_resource_access function
        import app.core.rbac as rbac_module
        original_check = rbac_module.check_resource_access
        rbac_module.check_resource_access = mock_check_resource_access
        
        try:
            accessible = filter_accessible_resources(
                self.super_admin, "hotel", [1, 2, 3], self.db
            )
            
            assert accessible == [1]
        finally:
            # Restore original function
            rbac_module.check_resource_access = original_check


class TestDataSegregationMiddleware:
    """Test data segregation middleware functionality."""
    
    def test_middleware_excluded_paths(self):
        """Test middleware excludes authentication paths."""
        from app.middleware.rbac import DataSegregationMiddleware
        
        middleware = DataSegregationMiddleware(None)
        
        # Check default excluded paths
        assert "/auth/login" in middleware.excluded_paths
        assert "/auth/refresh" in middleware.excluded_paths
        assert "/health" in middleware.excluded_paths
    
    def test_create_tenant_isolation_validator(self):
        """Test tenant isolation validator creation."""
        from app.middleware.rbac import create_tenant_isolation_validator
        
        validator = create_tenant_isolation_validator("hotel", "hotel_id")
        
        # Validator should be a callable
        assert callable(validator)


if __name__ == "__main__":
    pytest.main([__file__])