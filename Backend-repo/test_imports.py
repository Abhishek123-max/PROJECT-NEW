#!/usr/bin/env python3
"""
Test script to check if all imports work correctly.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    
    # Test core imports
    from app.core.database import init_database, get_db_session
    print("✓ Database imports OK")
    
    from app.core.auth import create_token_pair, decode_token
    print("✓ Auth core imports OK")
    
    from app.services.core.auth import authenticate_user
    print("✓ Auth service imports OK")
    
    from app.models.core.user import User
    from app.models.core.auth import Role, Hotel, Branch, RefreshToken
    print("✓ Model imports OK")
    
    from app.schemas.core.auth import LoginRequest, LoginResponse
    print("✓ Schema imports OK")
    
    from app.routes.auth.auth import router
    print("✓ Route imports OK")
    
    from app.routers import api_router
    print("✓ Router imports OK")
    
    from app.main import app
    print("✓ Main app imports OK")
    
    print("\nAll imports successful! ✅")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)