"""Service layer for password management."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from ...models.core.user import User
from ...models.core.password_reset import PasswordResetToken
from ...core.auth import get_password_hash
from ...utils.helpers import verify_password
from ...utils.exceptions import InvalidTokenError, InvalidCredentialsError
from ...settings.base import get_settings

settings = get_settings()

class UserNotFoundError(Exception):
    """Custom exception for user not found errors."""
    pass


async def generate_password_reset_token(user: User, db: AsyncSession) -> str:
    """
    Generates a password reset JWT and stores it in the database.
    """
    expires_delta = timedelta(hours=24)
    expires_at = datetime.utcnow() + expires_delta
    
    to_encode = {
        "sub": str(user.id),
        "exp": expires_at,
        "type": "password_reset"
    }
    
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    # Store the token
    db_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(db_token)
    await db.commit()
    
    return token


async def verify_and_use_reset_token(token: str, db: AsyncSession) -> User:
    """
    Verifies a password reset token, returns the user, and deletes the token.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "password_reset":
            raise InvalidTokenError("Invalid token type.")
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise InvalidTokenError("Invalid or expired password reset token.")

    # Find the token in the database
    stmt = select(PasswordResetToken).where(PasswordResetToken.token == token)
    result = await db.execute(stmt)
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.user_id != user_id or db_token.expires_at.replace(tzinfo=None) < datetime.utcnow():
        raise InvalidTokenError("Invalid or expired password reset token.")

    # Find the user
    user = await db.get(User, user_id)
    if not user:
        raise UserNotFoundError("User associated with token not found.")

    # Delete the token after successful verification
    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.id == db_token.id))
    await db.commit()

    return user


async def reset_password_first_time(
    username: str,
    current_password: str,
    new_password: str,
    token: str,
    db: AsyncSession
) -> User:
    """Handles the first-time password reset flow."""
    user = await verify_and_use_reset_token(token, db)

    if user.username != username:
        raise InvalidCredentialsError("Username does not match the token.")

    if not user.is_one_time_password:
        raise InvalidCredentialsError("One-time password has already been used.")

    if not verify_password(current_password, user.password_hash):
        raise InvalidCredentialsError("Incorrect current password.")

    # Update password
    user.password_hash = await get_password_hash(new_password)
    user.is_one_time_password = False
    await db.commit()
    await db.refresh(user)

    return user


async def reset_password_with_token(
    username: str,
    new_password: str,
    token: str,
    db: AsyncSession
) -> User:
    """Handles the 'forgot password' reset flow."""
    user = await verify_and_use_reset_token(token, db)

    if user.username != username:
        raise InvalidCredentialsError("Username does not match the token.")

    # Update password
    user.password_hash = await get_password_hash(new_password)
    user.is_one_time_password = False  # Ensure this is false
    await db.commit()
    await db.refresh(user)

    return user


async def reset_password_with_accesstoken(
    username: str,
    new_password: str,
    current_user:str,
    db: AsyncSession
) -> User:
    """Handles the 'forgot password' reset flow."""
    user = current_user;

    if user.username != username:
        raise InvalidCredentialsError("Username does not match the token.")

    # Update password
    user.password_hash = await get_password_hash(new_password)
    user.is_one_time_password = False  # Ensure this is false
    await db.commit()
    await db.refresh(user)

    return user


async def get_user_by_username_for_reset(username: str, db: AsyncSession) -> Optional[User]:
    """Finds a user by username for the forgot password flow."""
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user