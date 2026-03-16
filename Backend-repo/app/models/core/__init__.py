# Core models pac# app/models/__init__.py

# Core / auth
from app.models.core.auth import Base
from app.models.core.user import User
from app.models.core.floor_manager import FloorManager

# Domain models
from app.models.core.floor import Floor
from app.models.hotel.branch import Branch
from app.models.hotel.hotel import Hotel