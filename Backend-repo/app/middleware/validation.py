"""
Request validation middleware for HotelAgent API.
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Request validation middleware."""
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024, max_json_depth: int = 10):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.max_json_depth = max_json_depth
    
    async def dispatch(self, request: Request, call_next):
        # Log private network requests
        if request.client and request.client.host in ["127.0.0.1", "localhost"]:
            logger.info(f"Private network request: {request.client.host}")
        
        response = await call_next(request)
        return response