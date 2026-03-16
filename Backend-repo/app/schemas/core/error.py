"""
Error response schemas for HotelAgent API.
"""

from typing import Optional, Any
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Error response schema."""
    error_code: str
    message: str
    details: Optional[Any] = None
    timestamp: str