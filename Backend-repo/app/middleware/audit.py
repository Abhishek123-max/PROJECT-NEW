"""
Audit middleware for HotelAgent authentication system.
Provides automatic logging of sensitive operations with request/response tracking
and performance monitoring for comprehensive security auditing.
"""

import time
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Set
from functools import wraps
from contextlib import asynccontextmanager

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.audit import audit_service, extract_ip_address, extract_user_agent, generate_request_id, get_db_session
from ..core.dependencies import get_optional_user
from ..models.core.user import User

# Configure logging
logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic audit logging of HTTP requests and responses.
    
    Provides selective logging based on endpoints, performance monitoring,
    and comprehensive request/response tracking for security auditing.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        sensitive_endpoints: Optional[Set[str]] = None,
        excluded_endpoints: Optional[Set[str]] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_size: int = 10000,  # Maximum body size to log (bytes)
        performance_threshold_ms: int = 1000,  # Log slow requests
    ):
        """
        Initialize audit middleware.
        
        Args:
            app: ASGI application
            sensitive_endpoints: Set of endpoint patterns to always audit
            excluded_endpoints: Set of endpoint patterns to exclude from auditing
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            max_body_size: Maximum body size to log in bytes
            performance_threshold_ms: Threshold for logging slow requests
        """
        super().__init__(app)
        
        # Default sensitive endpoints that should always be audited
        self.sensitive_endpoints = sensitive_endpoints or {
            "/auth/login",
            "/auth/logout", 
            "/auth/refresh",
            "/auth/users",
            "/auth/users/",
            "/auth/features",
            "/admin/",
            "/api/v1/users",
            "/api/v1/auth",
        }
        
        # Endpoints to exclude from auditing (health checks, static files, etc.)
        self.excluded_endpoints = excluded_endpoints or {
            "/health",
            "/ready",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/static/",
        }
        
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.performance_threshold_ms = performance_threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request and response with audit logging.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response: HTTP response
        """
        # Generate request ID for correlation
        request_id = generate_request_id()
        request.state.request_id = request_id
        
        # Extract request context
        start_time = time.time()
        ip_address = extract_ip_address(request)
        user_agent = extract_user_agent(request)
        method = request.method
        url = str(request.url)
        path = request.url.path
        
        # Check if this endpoint should be audited
        should_audit = self._should_audit_endpoint(path, method)
        
        # Initialize audit context
        audit_context = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "url": url,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "start_time": start_time,
            "should_audit": should_audit,
        }
        
        # Get current user if available (for authenticated requests)
        current_user = None
        try:
            async for db in get_db_session():
                current_user = await get_optional_user(request, db)
                if current_user:
                    audit_context["user_id"] = current_user.id
                    audit_context["user_email"] = current_user.email
                    audit_context["hotel_id"] = current_user.hotel_id
                    audit_context["branch_id"] = current_user.branch_id
        except Exception as e:
            logger.debug(f"Could not extract user from request: {e}")
        
        # Log request body if configured and appropriate
        request_body = None
        if should_audit and self.log_request_body and self._should_log_body(request):
            try:
                request_body = await self._read_request_body(request)
                audit_context["request_body_size"] = len(request_body) if request_body else 0
            except Exception as e:
                logger.warning(f"Failed to read request body: {e}")
        
        # Process request
        response = None
        error = None
        try:
            response = await call_next(request)
            audit_context["status_code"] = response.status_code
            
        except Exception as e:
            error = e
            audit_context["error"] = str(e)
            audit_context["status_code"] = 500
            
            # Create error response
            response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": request_id}
            )
        
        # Calculate duration
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        audit_context["duration_ms"] = duration_ms
        
        # Log response body if configured and appropriate
        response_body = None
        if should_audit and self.log_response_body and response:
            try:
                response_body = await self._read_response_body(response)
                audit_context["response_body_size"] = len(response_body) if response_body else 0
            except Exception as e:
                logger.warning(f"Failed to read response body: {e}")
        
        # Perform audit logging
        if should_audit:
            await self._log_request_audit(
                audit_context=audit_context,
                request_body=request_body,
                response_body=response_body,
                error=error
            )
        
        # Log performance issues
        if duration_ms > self.performance_threshold_ms:
            await self._log_performance_issue(audit_context)
        
        return response
    
    def _should_audit_endpoint(self, path: str, method: str) -> bool:
        """
        Determine if an endpoint should be audited.
        
        Args:
            path: Request path
            method: HTTP method
            
        Returns:
            bool: True if endpoint should be audited
        """
        # Skip excluded endpoints
        for excluded in self.excluded_endpoints:
            if path.startswith(excluded):
                return False
        
        # Always audit sensitive endpoints
        for sensitive in self.sensitive_endpoints:
            if path.startswith(sensitive):
                return True
        
        # Audit all POST, PUT, DELETE operations by default
        if method in ["POST", "PUT", "DELETE", "PATCH"]:
            return True
        
        # Skip GET requests to non-sensitive endpoints
        return False
    
    def _should_log_body(self, request: Request) -> bool:
        """
        Determine if request body should be logged.
        
        Args:
            request: FastAPI request object
            
        Returns:
            bool: True if body should be logged
        """
        content_type = request.headers.get("content-type", "")
        
        # Only log JSON and form data
        if not any(ct in content_type.lower() for ct in ["json", "form"]):
            return False
        
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            return False
        
        return True
    
    async def _read_request_body(self, request: Request) -> Optional[str]:
        """
        Safely read request body.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Request body as string or None
        """
        try:
            body = await request.body()
            if len(body) > self.max_body_size:
                return f"[Body too large: {len(body)} bytes]"
            
            # Try to decode as JSON for better formatting
            try:
                json_body = json.loads(body)
                # Remove sensitive fields
                json_body = self._sanitize_sensitive_data(json_body)
                return json.dumps(json_body, indent=2)
            except (json.JSONDecodeError, TypeError):
                # Return as string if not JSON
                return body.decode("utf-8", errors="replace")[:self.max_body_size]
                
        except Exception as e:
            logger.warning(f"Failed to read request body: {e}")
            return None
    
    async def _read_response_body(self, response: Response) -> Optional[str]:
        """
        Safely read response body.
        
        Args:
            response: FastAPI response object
            
        Returns:
            str: Response body as string or None
        """
        try:
            if hasattr(response, 'body'):
                body = response.body
                if len(body) > self.max_body_size:
                    return f"[Body too large: {len(body)} bytes]"
                
                # Try to decode as JSON
                try:
                    json_body = json.loads(body)
                    return json.dumps(json_body, indent=2)
                except (json.JSONDecodeError, TypeError):
                    return body.decode("utf-8", errors="replace")[:self.max_body_size]
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to read response body: {e}")
            return None
    
    def _sanitize_sensitive_data(self, data: Any) -> Any:
        """
        Remove sensitive data from request/response bodies.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Any: Sanitized data
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if key.lower() in ["password", "token", "secret", "key", "authorization"]:
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = self._sanitize_sensitive_data(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_sensitive_data(item) for item in data]
        else:
            return data
    
    async def _log_request_audit(
        self,
        audit_context: Dict[str, Any],
        request_body: Optional[str] = None,
        response_body: Optional[str] = None,
        error: Optional[Exception] = None
    ) -> None:
        """
        Log request audit event.
        
        Args:
            audit_context: Request context information
            request_body: Request body content
            response_body: Response body content
            error: Exception if request failed
        """
        try:
            event_type = "api_request"
            success = audit_context.get("status_code", 500) < 400 and error is None
            
            details = {
                "method": audit_context.get("method"),
                "path": audit_context.get("path"),
                "url": audit_context.get("url"),
                "status_code": audit_context.get("status_code"),
                "duration_ms": audit_context.get("duration_ms"),
                "request_id": audit_context.get("request_id"),
            }
            
            # Add body information if available
            if request_body:
                details["request_body"] = request_body
                details["request_body_size"] = audit_context.get("request_body_size", 0)
            
            if response_body:
                details["response_body"] = response_body
                details["response_body_size"] = audit_context.get("response_body_size", 0)
            
            if error:
                details["error"] = str(error)
                details["error_type"] = type(error).__name__
            
            # Log the audit event
            # The 'details' dictionary contains extra info. We pass it as kwargs.
            await audit_service.log_authentication_event(
                event_type=event_type,
                username=audit_context.get("user_email"),
                user_id=audit_context.get("user_id"),
                success=success,
                ip_address=audit_context.get("ip_address"),
                error_message=str(error) if error else None,
                **details  # Unpack the details dictionary into keyword arguments
            )
            
        except Exception as e:
            logger.error(f"Failed to log request audit: {e}")
    
    async def _log_performance_issue(self, audit_context: Dict[str, Any]) -> None:
        """
        Log performance issue for slow requests.
        
        Args:
            audit_context: Request context information
        """
        try:
            details = {
                "method": audit_context.get("method"),
                "path": audit_context.get("path"),
                "duration_ms": audit_context.get("duration_ms"),
                "threshold_ms": self.performance_threshold_ms,
                "request_id": audit_context.get("request_id"),
            }
            await audit_service.log_authentication_event(
                event_type="performance_issue",
                success=False,  # It's an issue, so not a "success"
                ip_address=audit_context.get("ip_address"),
                **details
            )
            
        except Exception as e:
            logger.error(f"Failed to log performance issue: {e}")


class AuditDecorator:
    """
    Decorator class for adding audit logging to specific functions.
    
    Provides @audit_action decorator for comprehensive function-level auditing
    with automatic context extraction and performance monitoring.
    """
    
    def __init__(
        self,
        action: str,
        resource: Optional[str] = None,
        log_args: bool = False,
        log_result: bool = False,
        sensitive_args: Optional[Set[str]] = None
    ):
        """
        Initialize audit decorator.
        
        Args:
            action: Action being performed
            resource: Resource being acted upon
            log_args: Whether to log function arguments
            log_result: Whether to log function result
            sensitive_args: Set of argument names to redact
        """
        self.action = action
        self.resource = resource or "unknown"
        self.log_args = log_args
        self.log_result = log_result
        self.sensitive_args = sensitive_args or {"password", "token", "secret", "key"}
    
    def __call__(self, func: Callable) -> Callable:
        """
        Apply audit decorator to function.
        
        Args:
            func: Function to decorate
            
        Returns:
            Callable: Decorated function
        """
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self._audit_async_function(func, args, kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async audit logging
            # So we'll use a background task or simplified logging
            return self._audit_sync_function(func, args, kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    async def _audit_async_function(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """
        Audit async function execution.
        
        Args:
            func: Function being executed
            args: Function positional arguments
            kwargs: Function keyword arguments
            
        Returns:
            Any: Function result
        """
        start_time = datetime.utcnow()
        function_name = f"{func.__module__}.{func.__name__}"
        
        # Extract user context if available
        user_id = None
        hotel_id = None
        branch_id = None
        
        # Try to extract user from arguments
        for arg in args:
            if hasattr(arg, 'id') and hasattr(arg, 'email'):  # Likely a User object
                user_id = arg.id
                hotel_id = getattr(arg, 'hotel_id', None)
                branch_id = getattr(arg, 'branch_id', None)
                break
        
        # Check kwargs for user context
        if 'current_user' in kwargs:
            user = kwargs['current_user']
            if user:
                user_id = user.id
                hotel_id = getattr(user, 'hotel_id', None)
                branch_id = getattr(user, 'branch_id', None)
        
        # Prepare audit details
        details = {
            "function": function_name,
            "action": self.action,
        }
        
        # Log arguments if configured
        if self.log_args:
            sanitized_kwargs = self._sanitize_arguments(kwargs)
            details["arguments"] = sanitized_kwargs
        
        # Execute function
        result = None
        error = None
        try:
            result = await func(*args, **kwargs)
            
            # Log result if configured
            if self.log_result and result is not None:
                details["result_type"] = type(result).__name__
                if hasattr(result, 'id'):
                    details["result_id"] = result.id
            
        except Exception as e:
            error = e
            details["error"] = str(e)
            details["error_type"] = type(e).__name__
            raise
        
        finally:
            # Calculate duration
            end_time = datetime.utcnow()
            duration = end_time - start_time
            duration_ms = int(duration.total_seconds() * 1000)
            details["duration_ms"] = duration_ms
            
            # Log audit event
            try:
                await audit_service.log_authentication_event(
                    event_type="function_call",
                    user_id=user_id,
                    success=error is None,
                    error_code=type(error).__name__ if error else None,
                    error_message=str(error) if error else None,
                    **details
                )
            except Exception as audit_error:
                logger.error(f"Failed to log function audit: {audit_error}")
        
        return result
    
    def _audit_sync_function(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """
        Audit sync function execution (simplified).
        
        Args:
            func: Function being executed
            args: Function positional arguments
            kwargs: Function keyword arguments
            
        Returns:
            Any: Function result
        """
        start_time = datetime.utcnow()
        function_name = f"{func.__module__}.{func.__name__}"
        
        # Execute function
        result = None
        error = None
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            error = e
            raise
        finally:
            # Log to application logger (can't use async audit service)
            end_time = datetime.utcnow()
            duration = end_time - start_time
            duration_ms = int(duration.total_seconds() * 1000)
            
            log_level = logging.INFO if error is None else logging.ERROR
            logger.log(
                log_level,
                f"Function audit: {function_name}, action={self.action}, "
                f"duration={duration_ms}ms, success={error is None}"
            )
        
        return result
    
    def _sanitize_arguments(self, kwargs: dict) -> dict:
        """
        Sanitize function arguments for logging.
        
        Args:
            kwargs: Function keyword arguments
            
        Returns:
            dict: Sanitized arguments
        """
        sanitized = {}
        for key, value in kwargs.items():
            if key.lower() in self.sensitive_args:
                sanitized[key] = "[REDACTED]"
            elif hasattr(value, 'id') and hasattr(value, 'email'):
                # User-like object
                sanitized[key] = f"User(id={value.id})"
            elif isinstance(value, (str, int, float, bool, type(None))):
                sanitized[key] = value
            else:
                sanitized[key] = f"{type(value).__name__}(...)"
        
        return sanitized


# Convenience decorator function
def audit_action(
    action: str,
    resource: Optional[str] = None,
    log_args: bool = False,
    log_result: bool = False,
    sensitive_args: Optional[Set[str]] = None
) -> Callable:
    """
    Decorator for adding audit logging to functions.
    
    Args:
        action: Action being performed
        resource: Resource being acted upon
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        sensitive_args: Set of argument names to redact
        
    Returns:
        Callable: Decorator function
        
    Example:
        @audit_action("create_user", resource="user", log_args=True)
        async def create_user(user_data: UserCreate, current_user: User):
            # Function implementation
            pass
    """
    return AuditDecorator(
        action=action,
        resource=resource,
        log_args=log_args,
        log_result=log_result,
        sensitive_args=sensitive_args
    )


class PerformanceMonitor:
    """
    Performance monitoring utilities for audit operations.
    
    Provides context managers and decorators for monitoring
    performance of audit-related operations.
    """
    
    def __init__(self, threshold_ms: int = 100):
        """
        Initialize performance monitor.
        
        Args:
            threshold_ms: Threshold for logging slow operations
        """
        self.threshold_ms = threshold_ms
    
    @asynccontextmanager
    async def monitor_operation(self, operation_name: str, user_id: Optional[int] = None):
        """
        Context manager for monitoring operation performance.
        
        Args:
            operation_name: Name of the operation being monitored
            user_id: User ID if applicable
            
        Yields:
            dict: Performance context with timing information
        """
        start_time = datetime.utcnow()
        context = {
            "operation": operation_name,
            "start_time": start_time,
            "user_id": user_id,
        }
        
        try:
            yield context
        finally:
            end_time = datetime.utcnow()
            duration = end_time - start_time
            duration_ms = int(duration.total_seconds() * 1000)
            context["duration_ms"] = duration_ms
            
            # Log if operation was slow
            if duration_ms > self.threshold_ms:
                await self._log_slow_operation(context)
    
    async def _log_slow_operation(self, context: Dict[str, Any]) -> None:
        """
        Log slow operation for performance monitoring.
        
        Args:
            context: Operation context information
        """
        try:
            details = {
                "operation": context.get("operation"),
                "duration_ms": context.get("duration_ms"),
                "threshold_ms": self.threshold_ms,
            }
            await audit_service.log_system_event(
                event_type="slow_operation",
                user_id=context.get("user_id"),
                success=True,
                **details
            )
        except Exception as e:
            logger.error(f"Failed to log slow operation: {e}")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Utility functions for common audit scenarios
async def audit_authentication_attempt(
    email: str,
    success: bool,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    error_code: Optional[str] = None,
    duration_ms: Optional[int] = None
) -> None:
    """
    Audit authentication attempt with comprehensive logging.
    
    Args:
        email: Email address used for authentication
        success: Whether authentication was successful
        user_id: User ID if authentication was successful
        ip_address: Client IP address
        user_agent: Client user agent
        error_code: Error code if authentication failed
        duration_ms: Authentication operation duration
    """
    try:
        event_type = "login_success" if success else "login_failed"
        
        await audit_service.log_authentication_event(
            event_type=event_type,
            user_id=user_id,
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            error_code=error_code,
            duration_ms=duration_ms
        )
    except Exception as e:
        logger.error(f"Failed to audit authentication attempt: {e}")


async def audit_authorization_failure(
    user_id: int,
    resource: str,
    action: str,
    reason: str,
    ip_address: Optional[str] = None,
    hotel_id: Optional[int] = None,
    branch_id: Optional[int] = None
) -> None:
    """
    Audit authorization failure with context information.
    
    Args:
        user_id: User ID attempting access
        resource: Resource being accessed
        action: Action being attempted
        reason: Reason for authorization failure
        ip_address: Client IP address
        hotel_id: Hotel ID context
        branch_id: Branch ID context
    """
    try:
        await audit_service.log_authorization_failure(
            user_id=user_id,
            resource=resource,
            action=action,
            reason=reason,
            ip_address=ip_address,
            hotel_id=hotel_id,
            branch_id=branch_id
        )
    except Exception as e:
        logger.error(f"Failed to audit authorization failure: {e}")


async def audit_user_management_action(
    action: str,
    actor_user_id: int,
    target_user_id: Optional[int] = None,
    target_user_email: Optional[str] = None,
    hotel_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    **additional_details
) -> None:
    """
    Audit user management action with comprehensive context.
    
    Args:
        action: Action being performed (create_user, update_user, etc.)
        actor_user_id: User ID performing the action
        target_user_id: User ID being acted upon
        target_user_email: Email of user being acted upon
        hotel_id: Hotel ID context
        branch_id: Branch ID context
        ip_address: Client IP address
        **additional_details: Additional action-specific details
    """
    try:
        if action == "create_user" and target_user_email:
            await audit_service.log_user_creation(
                creator_user_id=actor_user_id,
                created_user_id=target_user_id,
                created_user_email=target_user_email,
                created_user_role=additional_details.get("role", "unknown"),
                hotel_id=hotel_id,
                branch_id=branch_id,
                ip_address=ip_address,
                **additional_details
            )
        else:
            # Generic user management event
            await audit_service.log_authentication_event(
                event_type=action,
                user_id=actor_user_id,
                success=True,
                hotel_id=hotel_id,
                branch_id=branch_id,
                target_user_id=target_user_id,
                target_user_email=target_user_email,
                **additional_details
            )
    except Exception as e:
        logger.error(f"Failed to audit user management action: {e}")


# Import asyncio for decorator functionality
import asyncio