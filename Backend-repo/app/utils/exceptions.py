"""Custom exceptions for the HotelAgent application."""

class AuthenticationError(Exception):
    """Custom exception for authentication failures."""
    pass

class AuthorizationError(Exception):
    """Custom exception for authorization failures."""
    pass

class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""
    pass

class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid."""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Raised for invalid login credentials."""
    pass

class AccountLockedError(AuthenticationError):
    """Raised when a user account is locked."""
    pass

class InsufficientPermissionsError(AuthorizationError):
    """Raised when a user lacks required permissions."""
    pass

class DataSegregationError(AuthorizationError):
    """Raised for cross-tenant data access violations."""
    pass

class ItemNotFoundError(Exception):
    """Raised when a requested database item is not found."""
    pass

class RoleHierarchyError(AuthorizationError):
    """Raised for violations of role hierarchy rules."""
    pass

class FeatureAccessError(AuthorizationError):
    """Raised when a user tries to access a feature they are not subscribed to."""
    pass

class ValidationError(Exception):
    """Custom exception for general validation errors."""
    pass

class RateLimitExceededError(Exception):
    """Raised when a user exceeds the rate limit."""
    pass

class BruteForceDetectedError(AuthenticationError):
    """Raised when brute force attack is detected."""
    pass

class UserAlreadyExistsError(Exception):
    """Raised when attempting to create a user that already exists."""
    pass

# Add other custom exceptions as needed...