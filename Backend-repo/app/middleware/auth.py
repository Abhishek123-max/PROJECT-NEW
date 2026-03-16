"""
JWT authentication middleware for HotelAgent.
Handles JWT token extraction, validation, and user context injection.
"""

import jwt
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.auth import decode_token, TokenPayload
from ..core.database import get_db
from ..core.dependencies import get_current_user_from_db
from ..utils.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    AuthenticationError
)


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT token validation and user context injection.
    
    Extracts JWT tokens from Authorization header, validates them,
    and injects user context into request state for downstream handlers.
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/auth/login",
            "/auth/refresh",
            "/"
        ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and validate JWT token if present.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response: HTTP response
        """
        # Immediately pass through OPTIONS requests for CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Extract token from Authorization header
        token = self._extract_token_from_header(request)
        
        if token:
            try:
                # Validate token and get user context
                user_context = await self._validate_token_and_get_user(token, request)
                
                # Inject user context into request state
                request.state.user = user_context
                request.state.token_payload = user_context.get("token_payload")
                request.state.is_authenticated = True
                
            except (TokenExpiredError, InvalidTokenError, AuthenticationError) as e:
                # Token validation failed - continue without user context
                # Individual endpoints can decide if authentication is required
                request.state.user = None
                request.state.token_payload = None
                request.state.is_authenticated = False
                request.state.auth_error = str(e)
        else:
            # No token provided
            request.state.user = None
            request.state.token_payload = None
            request.state.is_authenticated = False
        
        return await call_next(request)
    
    def _extract_token_from_header(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: JWT token or None if not found
        """
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None
    
    async def _validate_token_and_get_user(self, token: str, request: Request) -> dict:
        """
        Validate JWT token and get user context.
        
        Args:
            token: JWT token to validate
            request: FastAPI request object
            
        Returns:
            dict: User context with user object and token payload
            
        Raises:
            TokenExpiredError: If token is expired
            InvalidTokenError: If token is invalid
            AuthenticationError: If user validation fails
        """
        try:
            # Decode and validate token
            token_payload = decode_token(token)
            
            if not token_payload or token_payload.type != "access":
                raise InvalidTokenError("Invalid access token")
            
            # Get database session
            db = next(get_db())
            request.state.db = db
            
            try:
                # Get user from database
                user = await get_current_user_from_db(token_payload.user_id, db)
                
                if not user:
                    request.state.db = None
                    raise InvalidTokenError("User not found or inactive")
                
                return {
                    "user": user,
                    "token_payload": token_payload,
                    "ip_address": self._get_client_ip(request),
                    "user_agent": request.headers.get("User-Agent", "")
                }
                
            finally:
                request.state.db = None
                db.close()
                
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Access token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token format")
        except Exception as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Client IP address
        """
        # Check for forwarded headers first (for load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"


class JWTBearer(HTTPBearer):
    """
    FastAPI security scheme for JWT Bearer token authentication.
    
    Used as a dependency to enforce authentication on specific endpoints.
    """
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[str]:
        """
        Extract and validate JWT token from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: JWT token
            
        Raises:
            HTTPException: If token is missing or invalid
        """
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization header missing",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        if credentials.scheme != "Bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        # Validate token format
        token = credentials.credentials
        if not self._is_valid_token_format(token):
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        
        return token
    
    def _is_valid_token_format(self, token: str) -> bool:
        """
        Basic token format validation.
        
        Args:
            token: JWT token to validate
            
        Returns:
            bool: True if token format is valid
        """
        if not token:
            return False
        
        # JWT tokens have 3 parts separated by dots
        parts = token.split(".")
        return len(parts) == 3


# Global instances
jwt_bearer = JWTBearer()
optional_jwt_bearer = JWTBearer(auto_error=False)


def validate_token_middleware(token: str) -> TokenPayload:
    """
    Middleware function for token validation.
    
    Args:
        token: JWT token to validate
        
    Returns:
        TokenPayload: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = decode_token(token)
        
        if not payload or payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from request object.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: JWT token or None if not found
    """
    authorization = request.headers.get("Authorization")
    
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() == "bearer":
            return token
    except ValueError:
        pass
    
    return None


def get_user_from_request(request: Request) -> Optional[dict]:
    """
    Get user context from request state (injected by middleware).
    
    Args:
        request: FastAPI request object
        
    Returns:
        dict: User context or None if not authenticated
    """
    return getattr(request.state, "user", None)


def get_token_payload_from_request(request: Request) -> Optional[TokenPayload]:
    """
    Get token payload from request state (injected by middleware).
    
    Args:
        request: FastAPI request object
        
    Returns:
        TokenPayload: Token payload or None if not authenticated
    """
    return getattr(request.state, "token_payload", None)


def is_request_authenticated(request: Request) -> bool:
    """
    Check if request is authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        bool: True if request is authenticated
    """
    return getattr(request.state, "is_authenticated", False)