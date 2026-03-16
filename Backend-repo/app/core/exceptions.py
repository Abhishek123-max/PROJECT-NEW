"""Custom exceptions for the application."""

class BaseException(Exception):
    """Base exception class for the application."""
    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(self.message)


class NotFoundException(BaseException):
    """Exception raised when a resource is not found."""
    pass


class ValidationException(BaseException):
    """Exception raised when validation fails."""
    pass


class AuthenticationException(BaseException):
    """Exception raised when authentication fails."""
    pass


class AuthorizationException(BaseException):
    """Exception raised when authorization fails."""
    pass


class DatabaseException(BaseException):
    """Exception raised when a database operation fails."""
    pass