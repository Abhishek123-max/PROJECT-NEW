"""
Default constants for staff role permissions.
"""

# Default permissions dict for staff roles
DEFAULT_PERMISSIONS_DICT = {
    "floors": ["create", "read", "update", "delete", "import", "export"],
    "halls": ["create", "read", "update", "delete", "import", "export"],
    "sections": ["create", "read", "update", "delete", "import", "export"],
    "tables": ["create", "read", "update", "delete", "import", "export"],
    "employees/staff": ["create", "read", "update", "delete", "import", "export"],
    "menu and pricing": ["create", "read", "update", "delete", "import", "export"],
    "billing and payments": ["create", "read", "update", "delete", "import", "export"],
    "kitchen stations": ["create", "read", "update", "delete", "import", "export"],
}
