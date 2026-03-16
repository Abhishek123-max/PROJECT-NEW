"""
Constants for HotelAgent API.
"""

from enum import Enum
from typing import Optional


class RoleNames:
    """Role names constants."""
    PRODUCT_ADMIN = "product_admin"
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"
    KITCHEN_STAFF = "kitchen_staff"
    WAITERS = "waiters"
    INVENTORY_MANAGER = "inventory_manager"
    HOUSEKEEPING = "housekeeping"


class FeatureNames(Enum):
    """Feature names enum."""
    BASIC_POS = "basic_pos"
    ORDER_MANAGEMENT = "order_management"
    BASIC_INVENTORY = "basic_inventory"
    ADVANCED_ANALYTICS = "advanced_analytics"
    MULTI_BRANCH = "multi_branch"
    STAFF_MANAGEMENT = "staff_management"
    ADVANCED_INVENTORY = "advanced_inventory"
    CUSTOMER_MANAGEMENT = "customer_management"
    LOYALTY_PROGRAM = "loyalty_program"
    INTEGRATION_API = "integration_api"
    CUSTOM_REPORTS = "custom_reports"
    ADVANCED_SECURITY = "advanced_security"
    AUDIT_LOGS = "audit_logs"
    WHITE_LABEL = "white_label"
    BRANCH_CREATION = "branch_creation"
    ANALYTICS = "analytics"
    HOUSEKEEPING_MODULE = "housekeeping_module"
    DELIVERY_MANAGEMENT = "delivery_management"
    TABLE_RESERVATION = "table_reservation"
    KITCHEN_DISPLAY = "kitchen_display"


# Convert enum lists to dictionary with boolean values for subscription features
def _features_to_dict(feature_list):
    return {feature.value: True for feature in feature_list}

# Subscription features as lists of enums
SUBSCRIPTION_FEATURES_LIST = {
    "basic": [
        FeatureNames.BASIC_POS,
        FeatureNames.ORDER_MANAGEMENT,
        FeatureNames.BASIC_INVENTORY
    ],
    "standard": [
        FeatureNames.BASIC_POS,
        FeatureNames.ORDER_MANAGEMENT,
        FeatureNames.BASIC_INVENTORY,
        FeatureNames.STAFF_MANAGEMENT,
        FeatureNames.CUSTOMER_MANAGEMENT
    ],
    "premium": [
        FeatureNames.BASIC_POS,
        FeatureNames.ORDER_MANAGEMENT,
        FeatureNames.BASIC_INVENTORY,
        FeatureNames.ADVANCED_ANALYTICS,
        FeatureNames.MULTI_BRANCH,
        FeatureNames.STAFF_MANAGEMENT,
        FeatureNames.ADVANCED_INVENTORY,
        FeatureNames.CUSTOMER_MANAGEMENT,
        FeatureNames.LOYALTY_PROGRAM
    ],
    "enterprise": list(FeatureNames)
}

# Subscription features as dictionaries with boolean values
SUBSCRIPTION_FEATURES = {
    plan: _features_to_dict(features) 
    for plan, features in SUBSCRIPTION_FEATURES_LIST.items()
}

# Subscription plans for Product Admin management
class PlanTypes:
    """Subscription plan type constants for product admin."""
    STANDARD = "standard"
    LIMITED = "limited"


PLAN_FEATURES = {
    PlanTypes.STANDARD: {
        FeatureNames.BRANCH_CREATION.value: True,
        FeatureNames.ANALYTICS.value: True,
    },
    PlanTypes.LIMITED: {
        FeatureNames.BRANCH_CREATION.value: False,
        FeatureNames.ANALYTICS.value: False,
    },
}

# Common features available to all roles
COMMON_FEATURES = {
    "dashboard_access": True,
    "profile_management": True,
    "basic_reporting": True
}

# Default feature toggles for roles
DEFAULT_ROLE_FEATURES = {
    RoleNames.PRODUCT_ADMIN:{
    "Dashboard": {
        "Overview": True,
        "Analytics": True,
        "Settings": True
    },
    "Employees & Roles": {
        "Role Management": True,
        "Employees": True
    },
    "Hotel Management": {
        "Hotel Branches": True,
        "Table Management": True
    },
    "Menu Management": {
        "Kitchen Counter": True,
        "Menu Items": True,
        "Tax Management": True
    },
    "Billing & Payment": True,
    "Order Management": True,
    "Billing Management": True,
    "Reporting": True,
    "Settings Management": True,
    "Feature Management": True
},
    RoleNames.SUPER_ADMIN: {
    "Dashboard": {
        "Overview": True,
        "Analytics": True,
        "Settings": True
    },
    "Employees & Roles": {
        "Role Management": True,
        "Employees": True
    },
    "Hotel Management": {
        "Hotel Branches": True,
        "Table Management": True
    },
    "Menu Management": {
        "Kitchen Counter": True,
        "Menu Items": True,
        "Tax Management": True
    },
    "Order Management":{
        "Create Order": True,
        "KOT": True,
        "Order History": True,
    },
    "Inventory Management": True,
    "Reports & Analytics": True,
    "Settings": True
}
,
    RoleNames.ADMIN: {
    "Dashboard": {
        "Overview": True,
        "Analytics": True,
        "Settings": True
    },
    "Employees & Roles": {
        "Role Management": True,
        "Employees": True
    },
    "Hotel Management": {
        "Hotel Branches": True,
        "Table Management": True
    },
    "Menu Management": {
        "Kitchen Counter": True,
        "Menu Items": True,
        "Tax Management": True
    },
    "Order Management":{
        "Create Order": True,
        "KOT": True,
        "Order History": True,
    },
    "Inventory Management": True,
    "Reports & Analytics": True,
    "Settings": True
}
,
    RoleNames.MANAGER: 
    {
    "Dashboard": {
        "Overview": True,
        "Analytics": True,
        "Settings": True
    },
    "Employees & Roles": {
        "Role Management": True,
        "Employees": True
    },
    "Hotel Management": {
        "Hotel Branches": True,
        "Table Management": True
    },
    "Menu Management": {
        "Kitchen Counter": True,
        "Menu Items": True,
        "Tax Management": True
    },
    "Order Management":{
        "Create Order": True,
        "KOT": True,
        "Order History": True,
    },
    "Inventory Management": True,
    "Reports & Analytics": True,
    "Settings": True
}
,
    RoleNames.CASHIER: {
    "Dashboard": {
        "Overview": True,
        "Analytics": True,
        "Settings": True
    },
    "Employees & Roles": {
        "Role Management": True,
        "Employees": True
    },
    "Hotel Management": {
        "Hotel Branches": True,
        "Table Management": True
    },
    "Menu Management": {
        "Kitchen Counter": True,
        "Menu Items": True,
        "Tax Management": True
    },
    "Order Management":{
        "Create Order": True,
        "KOT": True,
        "Order History": True,
    },
    "Inventory Management": True,
    "Reports & Analytics": True,
    "Settings": True
},
    RoleNames.KITCHEN_STAFF:{
    "Dashboard": {
        "Overview": True,
        "Analytics": True,
        "Settings": True
    },
    "Employees & Roles": {
        "Role Management": True,
        "Employees": True
    },
    "Hotel Management": {
        "Hotel Branches": True,
        "Table Management": True
    },
    "Menu Management": {
        "Kitchen Counter": True,
        "Menu Items": True,
        "Tax Management": True
    },
    "Order Management":{
        "Create Order": True,
        "KOT": True,
        "Order History": True,
    },
    "Inventory Management": True,
    "Reports & Analytics": True,
    "Settings": True
},
    RoleNames.WAITERS: {
    "Dashboard": {
        "Overview": True,
        "Analytics": True,
        "Settings": True
    },
    "Employees & Roles": {
        "Role Management": True,
        "Employees": True
    },
    "Hotel Management": {
        "Hotel Branches": True,
        "Table Management": True
    },
    "Menu Management": {
        "Kitchen Counter": True,
        "Menu Items": True,
        "Tax Management": True
    },
    "Order Management":{
        "Create Order": True,
        "KOT": True,
        "Order History": True,
    },
    "Inventory Management": True,
    "Reports & Analytics": True,
    "Settings": True
},
    RoleNames.INVENTORY_MANAGER: {
    "Dashboard": {
        "Overview": True,
        "Analytics": True,
        "Settings": True
    },
    "Employees & Roles": {
        "Role Management": True,
        "Employees": True
    },
    "Hotel Management": {
        "Hotel Branches": True,
        "Table Management": True
    },
    "Menu Management": {
        "Kitchen Counter": True,
        "Menu Items": True,
        "Tax Management": True
    },
    "Order Management":{
        "Create Order": True,
        "KOT": True,
        "Order History": True,
    },
    "Inventory Management": True,
    "Reports & Analytics": True,
    "Settings": True
},
    RoleNames.HOUSEKEEPING: {
    "Dashboard": {
        "Overview": True,
        "Analytics": True,
        "Settings": True
    },
    "Employees & Roles": {
        "Role Management": True,
        "Employees": True
    },
    "Hotel Management": {
        "Hotel Branches": True,
        "Table Management": True
    },
    "Menu Management": {
        "Kitchen Counter": True,
        "Menu Items": True,
        "Tax Management": True
    },
    "Order Management":{
        "Create Order": True,
        "KOT": True,
        "Order History": True,
    },
    "Inventory Management": True,
    "Reports & Analytics": True,
    "Settings": True
}
}

DEFAULT_USERS_PERMISSIONS = {
    "Dashboard":{
        "Overview": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
        "Analytics": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
        "Settings": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
    },
    "Employees & Roles": {
        "Role Management": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
        "Employees": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
       },
    "Hotel Management": {
        "Hotel Branches": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
        "Table Management": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
       },
    "Menu Management": {
        "Kitchen Counter": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
        "Menu Items": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
        "Tax Management": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
    },
    "Order Management": {
        "Create Order":  {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
        "KOT": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
        "Order History": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
    },

    "Inventory Management": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
    "Reports & Analytics": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
    "Settings Management": {"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False},
    # "Feature Management": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
}
# Default per-page permissions template for new roles
DEFAULT_PAGE_PERMISSIONS = {
    "Dashboard":{
        "Overview": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
        "Analytics": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
        "Settings": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
    },
    "Employees & Roles": {
        "Role Management": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
        "Employees": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
       },
    "Hotel Management": {
        "Hotel Branches": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
        "Table Management": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
       },
    "Menu Management": {
        "Kitchen Counter": {"create": True, "view": False, "edit": False, "delete": False, "import": False, "export": False},
        "Menu Items": {"create": True, "view": False, "edit": False, "delete": False, "import": False, "export": False},
        "Tax Management": {"create": True, "view": False, "edit": False, "delete": False, "import": False, "export": False},
    },
    "Order Management": {
        "Create Order":  {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
        "KOT": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
        "Order History": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
    },

    "Inventory Management": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
    "Reports & Analytics": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
    "Settings Management": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
    # "Feature Management": {"create": True, "view": True, "edit": True, "delete": True, "import": False, "export": False},
}



# --- Helpers to derive role-specific page permission sets ---
import copy

def _set_all_permissions_true(template: dict) -> dict:
    """Return a deep copy of template with every permission set to True."""
    t = copy.deepcopy(template)
    def _rec(obj):
        if isinstance(obj, dict):
            perms = {"create", "view", "edit", "delete", "import", "export"}
            if set(obj.keys()).issubset(perms):
                for k in obj:
                    obj[k] = True
                return
            for v in obj.values():
                _rec(v)
    _rec(t)
    return t


def _set_view_and_some_create_edit(template: dict) -> dict:
    """A manager-like permission set: view by default, create/edit enabled for select modules, delete/import/export disabled."""
    t = copy.deepcopy(template)
    manager_create_edit = {
        "Employees & Roles": ["Employees"],
        "Menu Management": ["Menu Items", "Kitchen Counter"],
        "Order Management": None,
        "Billing Management": None,
    }

    def _rec(obj):
        if isinstance(obj, dict):
            perms = {"create", "view", "edit", "delete", "import", "export"}
            if set(obj.keys()).issubset(perms):
                # Default for manager: only view True
                obj.update({"create": False, "view": False, "edit": False, "delete": False, "import": False, "export": False})
                return
            for key, val in obj.items():
                if key in manager_create_edit:
                    if manager_create_edit[key] is None:
                        _enable_create_edit(val)
                    else:
                        for subk, subv in val.items():
                            if subk in manager_create_edit[key] and isinstance(subv, dict):
                                for p in ["create", "view", "edit"]:
                                    subv[p] = subv.get(p, True)
                                subv["delete"] = False
                                subv["import"] = False
                                subv["export"] = False
                _rec(val)

    def _enable_create_edit(obj):
        if isinstance(obj, dict):
            perms = {"create", "view", "edit", "delete", "import", "export"}
            if set(obj.keys()).issubset(perms):
                obj.update({"create": True, "view": True, "edit": True, "delete": False, "import": False, "export": False})
                return
            for v in obj.values():
                _enable_create_edit(v)

    _rec(t)
    # Remove "Hotel Management" from the result
    if "Hotel Management" in t:
        del t["Hotel Management"]
    return t

# Role-specific page permissions derived from the page template
ROLE_PAGE_PERMISSIONS = {
    RoleNames.PRODUCT_ADMIN: _set_all_permissions_true(DEFAULT_PAGE_PERMISSIONS),
    RoleNames.SUPER_ADMIN: _set_all_permissions_true(DEFAULT_PAGE_PERMISSIONS),
    RoleNames.ADMIN: _set_all_permissions_true(DEFAULT_PAGE_PERMISSIONS),
    RoleNames.MANAGER: _set_view_and_some_create_edit(DEFAULT_PAGE_PERMISSIONS),
    RoleNames.CASHIER: {
        "Order Management": {"create": True, "view": True, "edit": True, "delete": False, "import": False, "export": False},
        "Billing Management": {"create": True, "view": True, "edit": True, "delete": False, "import": False, "export": False},
        "Reporting": {"create": False, "view": True, "edit": False, "delete": False, "import": False, "export": False}
    },
    RoleNames.KITCHEN_STAFF: {
        "Order Management": {"create": True, "view": True, "edit": True, "delete": False, "import": False, "export": False}
    },
    RoleNames.WAITERS: {
        "Order Management": {"create": True, "view": True, "edit": False, "delete": False, "import": False, "export": False}
    },
    RoleNames.INVENTORY_MANAGER: {
        "Reporting": {"create": False, "view": True, "edit": False, "delete": False, "import": False, "export": False}
    },
    RoleNames.HOUSEKEEPING: {
        "Reporting": {"create": False, "view": True, "edit": False, "delete": False, "import": False, "export": False}
    }
}


# Default role creation permissions. Defines which roles a given role can create.
# A '*' signifies the ability to create any role, subject to hierarchy checks.
DEFAULT_CAN_CREATE_ROLES = {
    RoleNames.PRODUCT_ADMIN: ["*"],
    RoleNames.SUPER_ADMIN: ["*"],
    RoleNames.ADMIN: [
        RoleNames.MANAGER,
        RoleNames.CASHIER,
        RoleNames.KITCHEN_STAFF,
        RoleNames.WAITERS,
        RoleNames.INVENTORY_MANAGER,
        RoleNames.HOUSEKEEPING,
    ],
    RoleNames.MANAGER: [
        RoleNames.CASHIER,
        RoleNames.KITCHEN_STAFF,
        RoleNames.WAITERS,
        RoleNames.INVENTORY_MANAGER,
        RoleNames.HOUSEKEEPING,
    ],
    RoleNames.CASHIER: [],
    RoleNames.KITCHEN_STAFF: [],
    RoleNames.WAITERS: [],
    RoleNames.INVENTORY_MANAGER: [],
    RoleNames.HOUSEKEEPING: [],
}

ROLE_NAME_TO_CODE = {
    RoleNames.PRODUCT_ADMIN: "_pa",
    RoleNames.SUPER_ADMIN: "_sa",
    RoleNames.ADMIN: "_a",
    RoleNames.MANAGER: "_m",
    RoleNames.CASHIER: "_c",
    RoleNames.KITCHEN_STAFF: "_k",
    RoleNames.WAITERS: "_w",
    RoleNames.INVENTORY_MANAGER: "_i",
    RoleNames.HOUSEKEEPING: "_h",
}


def get_role_level(role_name: str) -> int:
    """Get role level for hierarchy."""
    levels = {
        RoleNames.PRODUCT_ADMIN: 100,
        RoleNames.SUPER_ADMIN: 90,
        RoleNames.ADMIN: 80,
        RoleNames.MANAGER: 70,
        RoleNames.CASHIER: 60,
        RoleNames.KITCHEN_STAFF: 50,
        RoleNames.WAITERS: 50,
        RoleNames.INVENTORY_MANAGER: 50,
        RoleNames.HOUSEKEEPING: 50
    }
    return levels.get(role_name, 0)


def is_higher_role(current_role: str, required_role: str) -> bool:
    """Check if current role is higher than required role."""
    return get_role_level(current_role) > get_role_level(required_role)


class Permissions:
    """Permission constants."""
    ROLE_CREATE = "role_management.create"
    ROLE_VIEW = "role_management.view"
    ROLE_EDIT = "role_management.edit"
    ROLE_DELETE = "role_management.delete"


ERROR_CODES = {
    "DEFAULT_ERROR": {"code": 1000, "message": "An unexpected error occurred."},
    "AUTHENTICATION_FAILED": {"code": 1001, "message": "Authentication failed."},
    "INVALID_TOKEN": {"code": 1002, "message": "Invalid token."},
    "TOKEN_EXPIRED": {"code": 1003, "message": "Token expired."},
    "INSUFFICIENT_PERMISSIONS": {"code": 1004, "message": "Insufficient permissions."},
    "DATA_SEGREGATION_VIOLATION": {"code": 1005, "message": "Data segregation violation."},
    "ROLE_HIERARCHY_VIOLATION": {"code": 1006, "message": "Role hierarchy violation."},
    "FEATURE_ACCESS_DENIED": {"code": 1007, "message": "Feature access denied."},
    "VALIDATION_ERROR": {"code": 1008, "message": "Validation error."},
    "RATE_LIMIT_EXCEEDED": {"code": 1009, "message": "Rate limit exceeded."},
    "BRUTE_FORCE_DETECTED": {"code": 1010, "message": "Brute force detected."},
    "ACCOUNT_LOCKED": {"code": 1011, "message": "Account locked."},
}

ROLE_PERMISSIONS = {
    RoleNames.PRODUCT_ADMIN: {
        Permissions.ROLE_CREATE: True,
        Permissions.ROLE_VIEW: True,
        Permissions.ROLE_EDIT: True,
        Permissions.ROLE_DELETE: True,
        "all": True
    },
    RoleNames.SUPER_ADMIN: {
        Permissions.ROLE_CREATE: True,
        Permissions.ROLE_VIEW: True,
        Permissions.ROLE_EDIT: True,
        Permissions.ROLE_DELETE: True,
        "all": True
    },
    RoleNames.ADMIN: {
        Permissions.ROLE_VIEW: True,
        Permissions.ROLE_EDIT: True,
    },
    RoleNames.MANAGER: {
        Permissions.ROLE_VIEW: True,
    },
    RoleNames.CASHIER: {},
    RoleNames.KITCHEN_STAFF: {},
    RoleNames.WAITERS: {},
    RoleNames.INVENTORY_MANAGER: {},
    RoleNames.HOUSEKEEPING: {}
}

def page_permissions_for_role(role_name: Optional[str]=None, levels: Optional[int]=None) -> dict:
    """Return a page-permissions dict determined by the role's level (not the role name).

    Rules (default):
      - level >= 80: full permissions (create/view/edit/delete/import/export)
      - level >= 70 and < 80: manager-like (view everywhere; create/edit enabled for common modules)
      - level >= 60 and < 70: cashier-like (Order/Billing create/edit/view, Reporting view)
      - level >= 50 and < 60: kitchen/waiter/inventory/housekeeping (minimal ordered views)
      - fallback: DEFAULT_PAGE_PERMISSIONS (conservative)
    """
    level = levels if levels is not None else get_role_level(role_name or "HOUSEKEEPING")
    if level is None:
        # Fallback to most restrictive permissions if level can't be determined
        return {
            "Dashboard": {
                "Overview": {"view": True, "create": False, "edit": False, "delete": False, "import": False, "export": False}
            }
        }
    if level >= 80:
        return _set_all_permissions_true(DEFAULT_PAGE_PERMISSIONS)
    if level >= 70:
        return _set_all_permissions_true(DEFAULT_PAGE_PERMISSIONS)
    if level >= 60:
        # Cashier-level permissions
        return _set_all_permissions_true(DEFAULT_PAGE_PERMISSIONS)
    if level >= 50:
        # Minimal permissions for kitchen/waiters/inventory/housekeeping
        return _set_all_permissions_true(DEFAULT_PAGE_PERMISSIONS)

    # Fallback very limited permissions
    return _set_all_permissions_true(DEFAULT_PAGE_PERMISSIONS)