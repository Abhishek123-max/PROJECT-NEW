"""
Authentication core functionality for HotelAgent API.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi.concurrency import run_in_threadpool

from ..settings.base import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload:
    """Token payload class."""
    
    def __init__(
        self, 
        user_id: int, 
        username: str = None, 
        type: str = "access", 
        role_name: str = None, 
        hotel_id: int = None, 
        branch_id: int = None, 
        zone_id: int = None, 
        floor_id: int = None, 
        section_id: int = None
    ):
        self.user_id = user_id
        self.username = username
        self.type = type
        self.role_name = role_name
        self.hotel_id = hotel_id
        self.branch_id = branch_id
        self.zone_id = zone_id
        self.floor_id = floor_id
        self.section_id = section_id

    def dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "type": self.type,
            "role_name": self.role_name,
            "hotel_id": self.hotel_id,
            "branch_id": self.branch_id,
            "zone_id": self.zone_id,
            "floor_id": self.floor_id,
            "section_id": self.section_id,
        }


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password."""
    return pwd_context.verify(plain_password, hashed_password)


async def get_password_hash(password: str) -> str:
    """Get password hash."""
    return await run_in_threadpool(pwd_context.hash, password)


def create_access_token(data: Dict[str, Any]) -> str:
    """Create access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")
        token_type = payload.get("type", "access")
        role_name = payload.get("role_name")
        hotel_id = payload.get("hotel_id")
        branch_id = payload.get("branch_id")
        zone_id = payload.get("zone_id")
        floor_id = payload.get("floor_id")
        section_id = payload.get("section_id")
        
        if user_id is None:
            return None
        
        return TokenPayload(
            user_id=user_id, 
            username=username, 
            type=token_type, 
            role_name=role_name, 
            hotel_id=hotel_id, 
            branch_id=branch_id, 
            zone_id=zone_id, 
            floor_id=floor_id, 
            section_id=section_id
        )
    except jwt.PyJWTError:
        return None


def generate_tokens_for_user(
    user_id: int, 
    username: str, 
    role_name: str = None, 
    hotel_id: int = None, 
    branch_id: int = None, 
    zone_id: int = None, 
    floor_id: int = None, 
    section_id: int = None
) -> Dict[str, str]:
    """Generate access and refresh tokens for a user."""
    token_data = {
        "user_id": user_id, 
        "username": username,
        "role_name": role_name,
        "hotel_id": hotel_id,
        "branch_id": branch_id,
        "zone_id": zone_id,
        "floor_id": floor_id,
        "section_id": section_id
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }
def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """Refresh access token using a valid refresh token."""
    token_payload = decode_token(refresh_token)
    
    if not token_payload or token_payload.type != "refresh":
        return None
    
    # Generate new access token
    token_data = {"user_id": token_payload.user_id, "username": token_payload.username}
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }