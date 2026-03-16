"""
Authentication API endpoints for HotelAgent.
Handles login, logout, token refresh, and current user information.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import jwt, JWTError
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from ...core.dependencies import (
    get_db_session,
    get_current_user_from_token,
    get_current_active_user,
    jwt_bearer
)
from ...schemas.core.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefresh,
    TokenResponse,
    LogoutResponse,
    UserInfoResponse,
    CurrentUser,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordForgotRequest,
    ResetPasswordAccessTokenRequest,
    VerifyTokenResponse,
)
from ...services.core.auth import (
    authenticate_user,
    generate_tokens_for_user,
    revoke_user_tokens,
    refresh_access_token  # This was pointing to the wrong implementation
)
from ...services.core import email_service, password_service
from ...services.core.password_service import UserNotFoundError
from ...models.core.user import User
from ...models.core.auth import Hotel
from ...models.core.password_reset import PasswordResetToken
from ...core.audit import audit_service
from ...utils.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    TokenExpiredError,
    InvalidTokenError,
    AuthenticationError,
    RateLimitExceededError,
    BruteForceDetectedError,
)
from ...middleware.rate_limit import brute_force_protection
from ...settings.base import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])
password_router = APIRouter(tags=["Password Management"])

settings = get_settings()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Authenticate user with email and password.
    
    Returns JWT access and refresh tokens on successful authentication.
    
    Args:
        request: FastAPI request object for IP extraction
        login_data: Login credentials (email and password)
        db: Database session
        
    Returns:
        LoginResponse: Success response with tokens and user info
        
    Raises:
        HTTPException: 401 for invalid credentials, 403 for locked accounts
    """
    try:
        # Extract client IP for audit logging
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")

        # Check for brute force protection
        block_status = await brute_force_protection.is_blocked(
            identifier=login_data.username,
            ip_address=client_ip
        )
        
        if block_status["blocked"]:
            # Log blocked attempt
            await audit_service.log_authentication_event(
                event_type="login_blocked_brute_force",
                user_id=None,
                username=login_data.username,
                success=False,
                ip_address=client_ip,
                error_code="BRUTE_FORCE_BLOCKED",
                error_message=block_status["reason"]
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Too many failed attempts",
                    "reason": block_status["reason"],
                    "retry_after": block_status["retry_after"]
                },
                headers={
                    "Retry-After": str(block_status["retry_after"])
                }
            )
        
        # Authenticate user
        user = await authenticate_user(
            username=login_data.username,
            password=login_data.password,
            db=db
        )

        # Eagerly load the role relationship to prevent lazy loading errors in async context.
        await db.refresh(user, ['role'])

        # --- Onboarding Status Check for Super Admin ---
        # Default to False. It's only relevant for super_admins.
        onboarding_completed = False
        if user.role and user.role.name == "super_admin":
            if user.hotel_id:
                hotel = await db.get(Hotel, user.hotel_id)
                if hotel:
                    onboarding_completed = (hotel.onboarding_status == 'completed')
                else:
                    onboarding_completed = False # Hotel not found, so onboarding is not complete.
            else:
                onboarding_completed = False # No hotel assigned, so onboarding is not complete.

        # Check if the user needs to reset their one-time password
        reset_required = user.is_one_time_password
        
        # Generate JWT tokens
        tokens = generate_tokens_for_user(
            user_id=user.id,
            username=user.username,
            role_name=user.role.name if user.role else None,
            hotel_id=user.hotel_id,
            branch_id=user.branch_id,
            floor_id=user.floor_id, # Keep floor_id and section_id for staff-level context
            section_id=user.section_id 
        )
        
        # Record successful login attempt for brute force protection
        await brute_force_protection.record_login_attempt(
            identifier=login_data.username,
            success=True,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Log successful authentication
        await audit_service.log_authentication_event(
            event_type="login_success",
            user_id=user.id,
            username=user.username,
            success=True,
            ip_address=client_ip,
            role=user.role.name if user.role else None,
            hotel_id=user.hotel_id,
            branch_id=user.branch_id
        )
        
        # Create user response
        current_user = CurrentUser(
            id=user.id,
            username=user.username,
            role=user.role.name if user.role else None,
            hotel_id=user.hotel_id,
            branch_id=user.branch_id,
            floor_id=user.floor_id,
            section_id=user.section_id,
            is_active=user.is_active,
            feature_toggles=user.feature_toggles,
            permissions=user.role.permissions if user.role and user.role.permissions else {},
            last_login=user.last_login,
            created_at=user.created_at
        )
        
        # --- DEBUG LOG: This is the "after" log for a successful request. ---
        logger.info(f"Login successful for user: {login_data.username}. Tokens generated.")

        response = LoginResponse(
            success=True,
            message="Login successful",
            data=TokenResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                expires_in=tokens["expires_in"]
            ),
            user=current_user,
            reset_required=reset_required,
            onboarding_completed=onboarding_completed
        )
        # If you want to include a top-level 'role_permissions', add it like this:
        return response.dict() | {"role_permissions": user.role.permissions if user.role and user.role.permissions else {}}
        
    except InvalidCredentialsError as e:
        # Record failed login attempt for brute force protection
        await brute_force_protection.record_login_attempt(
            identifier=login_data.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Log failed authentication attempt
        await audit_service.log_authentication_event(
            event_type="login_failed",
            user_id=None,
            username=login_data.username,
            success=False,
            ip_address=client_ip,
            error_code="INVALID_CREDENTIALS",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
        
    except AccountLockedError as e:
        # Record failed login attempt for brute force protection
        await brute_force_protection.record_login_attempt(
            identifier=login_data.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Log locked account attempt
        await audit_service.log_authentication_event(
            event_type="login_blocked",
            user_id=None,
            username=login_data.username,
            success=False,
            ip_address=client_ip,
            error_code="ACCOUNT_LOCKED",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
        
    except AuthenticationError as e:
        # Log general authentication error
        await audit_service.log_authentication_event(
            event_type="login_error",
            user_id=None,
            username=login_data.username,
            success=False,
            ip_address=client_ip,
            error_code="AUTHENTICATION_ERROR",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: Request,
    refresh_data: TokenRefresh,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Refresh access token using valid refresh token.
    
    Args:
        request: FastAPI request object for IP extraction
        refresh_data: Refresh token data
        db: Database session
        
    Returns:
        TokenResponse: New access and refresh tokens
        
    Raises:
        HTTPException: 401 for invalid/expired tokens
    """
    try:
        # Extract client IP for audit logging
        client_ip = request.client.host if request.client else "unknown"
        
        # Refresh tokens
        new_tokens = await refresh_access_token(
            refresh_token=refresh_data.refresh_token,
            db=db
        )
        
        # Extract user_id from token for logging
        from ...core.auth import decode_token
        token_payload = decode_token(new_tokens.get("access_token", ""))
        user_id = token_payload.user_id if token_payload else None
        
        # Log successful token refresh
        await audit_service.log_authentication_event(
            event_type="token_refresh_success",
            user_id=user_id,
            success=True,
            ip_address=client_ip
        )
        
        return TokenResponse(
            access_token=new_tokens["access_token"],
            refresh_token=new_tokens["refresh_token"],
            token_type=new_tokens["token_type"],
            expires_in=new_tokens["expires_in"]
        )
        
    except TokenExpiredError as e:
        # Log expired token attempt
        await audit_service.log_authentication_event(
            event_type="token_refresh_failed",
            user_id=None,
            success=False,
            ip_address=client_ip,
            error_code="TOKEN_EXPIRED",
            error_message="Refresh token has expired"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please login again."
        )
        
    except InvalidTokenError as e:
        # Log invalid token attempt
        await audit_service.log_authentication_event(
            event_type="token_refresh_failed",
            user_id=None,
            success=False,
            ip_address=client_ip,
            error_code="INVALID_TOKEN",
            error_message="Invalid refresh token"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token. Please login again."
        )
        
    except AuthenticationError as e:
        # Log general refresh error
        await audit_service.log_authentication_event(
            event_type="token_refresh_error",
            user_id=None,
            success=False,
            ip_address=client_ip,
            error_code="REFRESH_ERROR",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh service error"
        )
        
    except Exception as e:
        # Catch-all for any unexpected errors
        logger.error(f"Unexpected error in refresh token endpoint: {str(e)}", exc_info=True)
        
        await audit_service.log_authentication_event(
            event_type="token_refresh_error",
            user_id=None,
            success=False,
            ip_address=client_ip,
            error_code="UNEXPECTED_ERROR",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during token refresh"
        )


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Logout user and revoke all refresh tokens.
    
    Args:
        request: FastAPI request object for IP extraction
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        LogoutResponse: Success response
        
    Raises:
        HTTPException: 500 for logout service errors
    """
    try:
        # Extract client IP for audit logging
        client_ip = request.client.host if request.client else "unknown"
        
        # Revoke all user tokens
        success = await revoke_user_tokens(
            user_id=current_user.id,
            db=db,
            reason="logout"
        )
        
        if not success:
            raise AuthenticationError("Failed to revoke tokens")
        
        # Log successful logout
        await audit_service.log_authentication_event(
            event_type="logout_success",
            user_id=current_user.id,
            username=current_user.username,
            success=True,
            ip_address=client_ip
        )
        
        return LogoutResponse(
            success=True,
            message="Logout successful"
        )
        
    except AuthenticationError as e:
        # Log logout error
        await audit_service.log_authentication_event(
            event_type="logout_error",
            user_id=current_user.id,
            success=False,
            ip_address=client_ip,
            error_code="LOGOUT_ERROR",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout service error"
        )


@router.get("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserInfoResponse: Current user information
    """
    try:
        # Create user response
        user_data = CurrentUser(
            id=current_user.id,
            username=current_user.username,
            role=current_user.role.name if current_user.role else None,
            hotel_id=current_user.hotel_id,
            branch_id=current_user.branch_id,
            is_active=current_user.is_active,
            feature_toggles=current_user.feature_toggles,
            last_login=current_user.last_login,
            created_at=current_user.created_at
        )
        
        return UserInfoResponse(
            success=True,
            message="User information retrieved successfully",
            data=user_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user information: {str(e)}"
        )


@password_router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=status.HTTP_200_OK)
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Sends a password reset link to the user's email if the user exists.
    Always returns a success message to prevent username enumeration. For testing,
    it also returns the username and reset token if the user is found.
    """
    client_ip = request.client.host if request.client else "unknown"
    response_message = "If an account with that username exists, a password reset link has been sent to the associated email address."
    
    # Apply rate limiting
    block_status = await brute_force_protection.is_blocked(identifier=data.username, ip_address=client_ip)
    if block_status["blocked"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(block_status["retry_after"])}
        )

    # Always record an attempt for rate limiting for non-blocked requests
    await brute_force_protection.record_login_attempt(identifier=data.username, success=False, ip_address=client_ip)

    user = await password_service.get_user_by_username_for_reset(data.username, db)

    if user and user.is_active:
        # Eagerly load the role relationship to prevent lazy loading errors in async context.
        await db.refresh(user, ['role'])

        try:
            reset_token = await password_service.generate_password_reset_token(user, db)
            await email_service.send_forgot_password_email(
                to_email=user.contact_email,
                first_name=user.first_name,
                reset_token=reset_token
            )
            await audit_service.log_authentication_event(
                event_type="password_reset_request_sent",
                user_id=user.id,
                username=user.username,
                success=True,
                ip_address=client_ip,
                role=user.role.name if user.role else None,
                hotel_id=user.hotel_id,
                branch_id=user.branch_id
            )
            return ForgotPasswordResponse(
                message=response_message,
                username=user.username,
                reset_token=reset_token
            )
        except Exception as e:
            await audit_service.log_authentication_event(
                event_type="password_reset_request_failed",
                user_id=user.id,
                username=user.username,
                success=False,
                ip_address=client_ip,
                error_message=str(e)
            )
            return ForgotPasswordResponse(message=response_message)
    else:
        # Log the attempt but don't reveal that the user doesn't exist
        await audit_service.log_authentication_event(
            event_type="password_reset_request_failed",
            username=data.username,
            success=False,
            ip_address=client_ip,
            error_message="User not found or inactive"
        )
        return ForgotPasswordResponse(message=response_message)


@password_router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password_first_time(
    request: Request,
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Resets the user's password for the first time using the one-time password.
    """
    client_ip = request.client.host if request.client else "unknown"
    try:
        user = await password_service.reset_password_first_time(
            username=data.username,
            current_password=data.onetime_password,
            new_password=data.new_password,
            token=data.reset_token,
            db=db
        )

        # Eagerly load the role relationship to prevent lazy loading errors in async context.
        await db.refresh(user, ['role'])

        await audit_service.log_authentication_event(
            event_type="password_reset_success_first_time",
            user_id=user.id,
            username=user.username,
            success=True,
            ip_address=client_ip,
            role=user.role.name if user.role else None,
            hotel_id=user.hotel_id,
            branch_id=user.branch_id
        )
        return {"message": "Password has been reset successfully."}
    except (InvalidCredentialsError, InvalidTokenError, UserNotFoundError) as e:
        await audit_service.log_authentication_event(
            event_type="password_reset_failed_first_time",
            username=data.username,
            success=False,
            ip_address=client_ip,
            error_message=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@password_router.post("/reset-password-forgot", status_code=status.HTTP_200_OK)
async def reset_password_forgot(
    request: Request,
    data: ResetPasswordForgotRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Resets the user's password using a token from the 'forgot password' email.
    """
    client_ip = request.client.host if request.client else "unknown"
    try:
        user = await password_service.reset_password_with_token(
            username=data.username,
            new_password=data.new_password,
            token=data.token,
            db=db
        )

        # Eagerly load the role relationship to prevent lazy loading errors in async context.
        await db.refresh(user, ['role'])

        await audit_service.log_authentication_event(
            event_type="password_reset_success_forgot",
            user_id=user.id,
            username=user.username,
            success=True,
            ip_address=client_ip,
            role=user.role.name if user.role else None,
            hotel_id=user.hotel_id,
            branch_id=user.branch_id
        )
        return {"message": "Password has been reset successfully."}
    except (InvalidCredentialsError, InvalidTokenError, UserNotFoundError) as e:
        await audit_service.log_authentication_event(
            event_type="password_reset_failed_forgot",
            username=data.username,
            success=False,
            ip_address=client_ip,
            error_message=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@password_router.post("/reset-password_with_user", status_code=status.HTTP_200_OK)
async def reset_password_with_User(
    request: Request,
    data: ResetPasswordAccessTokenRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Resets the user's password using a token from the 'forgot password' email.
    """
    client_ip = request.client.host if request.client else "unknown"
    try:
        user = await password_service.reset_password_with_accesstoken(
            username=data.username,
            new_password=data.new_password,
            current_user=current_user,
            db=db
        )

        # Eagerly load the role relationship to prevent lazy loading errors in async context.
        await db.refresh(user, ['role'])

        await audit_service.log_authentication_event(
            event_type="password_reset_success_forgot",
            user_id=user.id,
            username=user.username,
            success=True,
            ip_address=client_ip,
            role=user.role.name if user.role else None,
            hotel_id=user.hotel_id,
            branch_id=user.branch_id
        )
        return {"message": "Password has been reset successfully."}
    except (InvalidCredentialsError, InvalidTokenError, UserNotFoundError) as e:
        await audit_service.log_authentication_event(
            event_type="password_reset_failed_forgot",
            username=data.username,
            success=False,
            ip_address=client_ip,
            error_message=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@password_router.post("/verify-reset-token", response_model=VerifyTokenResponse, status_code=status.HTTP_200_OK)
async def verify_reset_token(token: str, db: AsyncSession = Depends(get_db_session)):
    """
    Verifies if a password reset token is valid without consuming it.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "password_reset":
            raise InvalidTokenError("Invalid token type.")
        
        user_id = int(payload.get("sub"))
        expires_at = datetime.fromtimestamp(payload.get("exp"))

        if expires_at < datetime.utcnow():
            raise InvalidTokenError("Token has expired.")

        # Check if token exists in DB (it shouldn't be deleted until used)
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.user_id == user_id
        )
        result = await db.execute(stmt)
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise InvalidTokenError("Token has already been used or is invalid.")

        return VerifyTokenResponse(is_valid=True, message="Token is valid.")

    except (JWTError, ValueError, TypeError, InvalidTokenError) as e:
        return VerifyTokenResponse(is_valid=False, message=str(e))