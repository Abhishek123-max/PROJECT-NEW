"""
Audit service for HotelAgent API.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from .database import get_db_session

logger = logging.getLogger(__name__)


class AuditService:
    async def log_user_deletion(
        self,
        deleter_user_id: int,
        deleted_user_id: int,
        ip_address: str,
        hotel_id: int = None,
        branch_id: int = None,
        reason: str = None
    ):
        """Log user deletion event."""
        log_data = {
            "event_type": "user_deletion",
            "deleter_user_id": deleter_user_id,
            "deleted_user_id": deleted_user_id,
            "ip_address": ip_address,
            "hotel_id": hotel_id,
            "branch_id": branch_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"User deletion: {log_data}")
    
    async def log_authentication_event(
        self,
        event_type: str,
        success: bool,
        ip_address: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        role: Optional[str] = None,
        hotel_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        **kwargs: Any
    ):
        """Log authentication event."""
        log_data = {
            **kwargs,  # Capture all other keyword arguments
            "event_type": event_type,
            "success": success,
            "ip_address": ip_address,
            "user_id": user_id,
            "username": username,
            "user_agent": user_agent,
            "error_code": error_code,
            "error_message": error_message,
            "role": role,
            "hotel_id": hotel_id,
            "branch_id": branch_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Authentication event: {log_data}")
    
    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        user_id: Optional[int] = None,
        **kwargs: Any
    ):
        """Log security event."""
        log_data = {
            **kwargs,
            "event_type": event_type,
            "severity": severity,
            "description": description,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.warning(f"Security event: {log_data}")
    
    async def log_authorization_failure(
        self,
        user_id: Optional[int],
        resource: str,
        action: str,
        reason: str,
        ip_address: str,
        user_agent: Optional[str] = None
    ):
        """Log authorization failure."""
        log_data = {
            "event_type": "authorization_failure",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "reason": reason,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.warning(f"Authorization failure: {log_data}")
    
    async def log_user_creation(
        self,
        creator_user_id: int,
        created_user_id: int,
        created_user_username: str,
        created_user_role: str,
        hotel_id: Optional[int],
        branch_id: Optional[int],
        ip_address: str,
        zone_id: Optional[int] = None,
        hotel_name: Optional[str] = None,
        owner_name: Optional[str] = None
    ):
        """Log user creation."""
        log_data = {
            "event_type": "user_creation",
            "creator_user_id": creator_user_id,
            "created_user_id": created_user_id,
            "created_user_username": created_user_username,
            "created_user_role": created_user_role,
            "hotel_id": hotel_id,
            "branch_id": branch_id,
            "zone_id": zone_id,
            "hotel_name": hotel_name,
            "owner_name": owner_name,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"User creation: {log_data}")
    
    async def log_user_update(
        self,
        updater_user_id: int,
        updated_user_id: int,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        hotel_id: Optional[int],
        branch_id: Optional[int],
        ip_address: str,
        action: str = "update_user"
    ):
        """Log user update."""
        log_data = {
            "event_type": action,
            "updater_user_id": updater_user_id,
            "updated_user_id": updated_user_id,
            "old_values": old_values,
            "new_values": new_values,
            "hotel_id": hotel_id,
            "branch_id": branch_id,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"User update: {log_data}")


# Global audit service instance
audit_service = AuditService()


def extract_ip_address(request) -> str:
    """Extract IP address from request."""
    return request.client.host if request.client else "unknown"


def extract_user_agent(request) -> str:
    """Extract user agent from request."""
    return request.headers.get("User-Agent", "")


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())