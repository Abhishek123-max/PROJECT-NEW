"""
Authentication services for HotelAgent.
Handles user authentication, token generation, and validation.
"""

import jwt
from starlette.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from supabase_auth import datetime

from ...models.core.user import User
from ...models.core.subscription import Subscription
from ...models.core.auth import Hotel
from ...models.core.refresh_token import RefreshToken
from ...utils.helpers import verify_password
from ...utils.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    TokenExpiredError,
    InvalidTokenError,
    AuthenticationError
)
from ...utils.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    TokenExpiredError,
    InvalidTokenError,
    AuthenticationError
)
from ...core.auth import (
    generate_tokens_for_user,
    decode_token
)


async def authenticate_user(username: str, password: str, db: AsyncSession) -> User:
    """
    Authenticates a user by username and password.

    This function uses the correct async SQLAlchemy 2.0 syntax to prevent the
    "Column expression... expected" error.

    Args:
        username: User's username.
        password: User's password.
        db: The database session.

    Returns:
        The authenticated user object.

    Raises:
        InvalidCredentialsError: If username/password is incorrect.
        AccountLockedError: If the user account is inactive.
    """
    # Step 2: Consolidate DB queries. Eagerly load all related data in one trip.
    stmt = select(User).options( # Use joinedload for more efficient single query
        joinedload(User.role),
        joinedload(User.hotel).selectinload(Hotel.subscriptions)
    ).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise InvalidCredentialsError("Invalid username or password")

    if not user.is_active:
        raise AccountLockedError("Account is locked or inactive. Please contact support.")

    # Step 1: Offload blocking CPU work. Run password verification in a threadpool.
    is_password_valid = await run_in_threadpool(verify_password, password, user.password_hash)
    if not is_password_valid:
        raise InvalidCredentialsError("Invalid username or password")

    # --- Recalculate feature toggles based on active subscription on login ---
    if user.hotel and user.role:
        from ...settings.constants import DEFAULT_ROLE_FEATURES  # Local import to avoid cycles
        from copy import deepcopy

        def merge_features(role_feats, subscription_feats):
            """
            Deeply merge role and subscription features.
            - Booleans are ANDed when a subscription toggle exists; otherwise role value is used.
            - Nested dicts are merged recursively.
            """
            if not subscription_feats:
                return deepcopy(role_feats)

            merged = {}
            for key, role_val in (role_feats or {}).items():
                sub_val = subscription_feats.get(key)
                if isinstance(role_val, dict):
                    merged[key] = merge_features(role_val, sub_val if isinstance(sub_val, dict) else {})
                else:
                    merged[key] = bool(role_val and bool(sub_val))
            return merged

        # Prefer persisted role defaults; fall back to static defaults when missing.
        role_features = user.role.default_features or DEFAULT_ROLE_FEATURES.get(user.role.name, {})
        subscription_features = {}

        # Step 2: Use the already-loaded subscription data instead of a new query.
        active_sub = next((s for s in user.hotel.subscriptions if s.status == 'active'), None)

        if active_sub:
            subscription_features = active_sub.feature_toggles or {}

        user.feature_toggles = merge_features(role_features, subscription_features)

    return user


async def refresh_access_token(
    refresh_token: str,
    db: AsyncSession
) -> dict:
    """
    Refresh access token using a valid refresh token.
    
    Args:
        refresh_token: The refresh token to validate and use
        db: Database session
        
    Returns:
        dict: Dictionary containing new access_token, refresh_token, token_type, and expires_in
        
    Raises:
        TokenExpiredError: If the refresh token has expired
        InvalidTokenError: If the refresh token is invalid or not a refresh token
        AuthenticationError: If user validation fails or other errors occur
    """
    try:
        # Decode the refresh token directly to catch expiration errors
        from ...settings.base import get_settings
        
        settings = get_settings()
        
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid refresh token: {str(e)}")
        
        # Decode to get TokenPayload object (this should work now since we validated above)
        token_payload = decode_token(refresh_token)
        
        if not token_payload:
            raise InvalidTokenError("Invalid refresh token format")
        
        if token_payload.type != "refresh":
            raise InvalidTokenError("Token is not a refresh token")
        
        # Get user from database to validate they still exist and are active
        stmt = select(User).options(selectinload(User.role)).where(User.id == token_payload.user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise InvalidTokenError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        
        # Generate new tokens with all user context
        # Note: SQLAlchemy returns actual values, not Column objects when accessing attributes
        new_tokens = generate_tokens_for_user(
            user_id=user.id,  # type: ignore
            username=user.username,  # type: ignore
            role_name=user.role.name if user.role and user.role.name else None,  # type: ignore
            hotel_id=user.hotel_id,  # type: ignore
            branch_id=user.branch_id,  # type: ignore
            floor_id=user.floor_id,  # type: ignore
            section_id=user.section_id  # type: ignore
        )
        
        return new_tokens
        
    except (TokenExpiredError, InvalidTokenError, AuthenticationError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise AuthenticationError(f"Token refresh failed: {str(e)}")

async def revoke_user_tokens(user_id: int, db: AsyncSession, reason: str) -> bool:
    """
    Revokes all active refresh tokens for a given user.
    This is the actual implementation that interacts with the database.
    """
    try:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        )
        result = await db.execute(stmt)
        tokens_to_revoke = result.scalars().all()

        for token in tokens_to_revoke:
            token.is_revoked = True
            token.revoked_at = datetime.utcnow()
            token.revoked_reason = reason

        return True
    except Exception:
        return False