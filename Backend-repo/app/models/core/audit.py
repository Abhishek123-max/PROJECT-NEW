"""
Audit logging model for HotelAgent authentication system.
Tracks all authentication, authorization, and user management events.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from .auth import Base


class AuditLog(Base):
    """
    Audit log model for tracking security and user management events.
    
    Provides comprehensive logging for authentication, authorization,
    user management, and system access events with multi-tenant support.
    """
    __tablename__ = "audit_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Event identification
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, create_user, etc.
    action = Column(String(100), nullable=False, index=True)  # specific action taken
    resource = Column(String(100), nullable=True, index=True)  # resource affected (user, role, etc.)
    resource_id = Column(Integer, nullable=True, index=True)  # ID of affected resource
    
    # User and context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # For user management actions
    
    # Multi-tenant context
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    
    # Request context
    ip_address = Column(INET, nullable=True, index=True)  # Client IP address
    user_agent = Column(Text, nullable=True)  # Browser/client information
    request_id = Column(String(36), nullable=True, index=True)  # Request correlation ID
    session_id = Column(String(100), nullable=True, index=True)  # Session identifier
    
    # Event details
    details = Column(JSONB, nullable=False, default=dict)  # Additional event-specific data
    old_values = Column(JSONB, nullable=True)  # Previous values for update operations
    new_values = Column(JSONB, nullable=True)  # New values for update operations
    
    # Result and status
    success = Column(String(20), nullable=False, default="success", index=True)  # success, failure, error
    error_code = Column(String(50), nullable=True, index=True)  # Error code if failed
    error_message = Column(Text, nullable=True)  # Error details
    
    # Performance metrics
    duration_ms = Column(Integer, nullable=True)  # Operation duration in milliseconds
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="audit_logs", lazy="select")
    target_user = relationship("User", foreign_keys=[target_user_id], lazy="select")
    hotel = relationship("Hotel", back_populates="audit_logs", lazy="select")
    branch = relationship("Branch", back_populates="audit_logs", lazy="select")

    # Indexes for performance and querying
    __table_args__ = (
        # Time-based indexes for log queries
        Index("ix_audit_logs_timestamp_desc", "timestamp", postgresql_using="btree"),
        Index("ix_audit_logs_date_event", "timestamp", "event_type"),
        
        # User activity indexes
        Index("ix_audit_logs_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_logs_user_event", "user_id", "event_type"),
        Index("ix_audit_logs_target_user_timestamp", "target_user_id", "timestamp"),
        
        # Multi-tenant indexes
        Index("ix_audit_logs_hotel_timestamp", "hotel_id", "timestamp"),
        Index("ix_audit_logs_branch_timestamp", "branch_id", "timestamp"),
        Index("ix_audit_logs_hotel_event", "hotel_id", "event_type"),
        
        # Security monitoring indexes
        Index("ix_audit_logs_ip_timestamp", "ip_address", "timestamp"),
        Index("ix_audit_logs_failed_events", "success", "event_type", postgresql_where="success = 'failure'"),
        Index("ix_audit_logs_login_events", "event_type", "timestamp", postgresql_where="event_type IN ('login', 'logout', 'login_failed')"),
        
        # Resource tracking indexes
        Index("ix_audit_logs_resource_timestamp", "resource", "resource_id", "timestamp"),
        Index("ix_audit_logs_session_timestamp", "session_id", "timestamp"),
        
        # Cleanup and archival indexes
        Index("ix_audit_logs_cleanup", "timestamp", "event_type"),
    )

    # Event type constants
    EVENT_TYPES = {
        # Authentication events
        "login": "User login attempt",
        "login_success": "Successful user login",
        "login_failed": "Failed user login",
        "logout": "User logout",
        "token_refresh": "JWT token refresh",
        "token_revoke": "Token revocation",
        "password_change": "Password change",
        "account_locked": "Account locked due to failed attempts",
        "account_unlocked": "Account unlocked",
        
        # Authorization events
        "access_denied": "Access denied to resource",
        "permission_check": "Permission validation",
        "role_check": "Role validation",
        "feature_access": "Feature access attempt",
        
        # User management events
        "user_created": "New user created",
        "user_updated": "User information updated",
        "user_deactivated": "User account deactivated",
        "user_activated": "User account activated",
        "user_deleted": "User account deleted",
        "role_assigned": "Role assigned to user",
        "role_removed": "Role removed from user",
        
        # System events
        "system_startup": "System startup",
        "system_shutdown": "System shutdown",
        "database_migration": "Database migration",
        "configuration_change": "System configuration change",
        
        # Security events
        "suspicious_activity": "Suspicious activity detected",
        "brute_force_attempt": "Brute force attack attempt",
        "sql_injection_attempt": "SQL injection attempt",
        "xss_attempt": "XSS attack attempt",
    }

    @validates('event_type')
    def validate_event_type(self, key: str, event_type: str) -> str:
        """Validate event type."""
        if not event_type:
            raise ValueError("Event type cannot be empty")
        return event_type.lower().strip()

    @validates('success')
    def validate_success(self, key: str, success: str) -> str:
        """Validate success status."""
        valid_statuses = ["success", "failure", "error", "warning"]
        if success not in valid_statuses:
            raise ValueError(f"Invalid success status. Must be one of: {valid_statuses}")
        return success

    @validates('details')
    def validate_details(self, key: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate details structure."""
        if not isinstance(details, dict):
            raise ValueError("Details must be a dictionary")
        return details

    def is_security_event(self) -> bool:
        """Check if this is a security-related event."""
        security_events = [
            "login_failed", "access_denied", "account_locked", "suspicious_activity",
            "brute_force_attempt", "sql_injection_attempt", "xss_attempt"
        ]
        return self.event_type in security_events

    def is_authentication_event(self) -> bool:
        """Check if this is an authentication-related event."""
        auth_events = [
            "login", "login_success", "login_failed", "logout", 
            "token_refresh", "token_revoke", "password_change"
        ]
        return self.event_type in auth_events

    def is_user_management_event(self) -> bool:
        """Check if this is a user management event."""
        user_mgmt_events = [
            "user_created", "user_updated", "user_deactivated", 
            "user_activated", "user_deleted", "role_assigned", "role_removed"
        ]
        return self.event_type in user_mgmt_events

    def get_event_description(self) -> str:
        """Get human-readable event description."""
        return self.EVENT_TYPES.get(self.event_type, f"Unknown event: {self.event_type}")

    def add_detail(self, key: str, value: Any) -> None:
        """Add a detail to the event."""
        if self.details is None:
            self.details = {}
        self.details[key] = value

    def set_error(self, error_code: str, error_message: str) -> None:
        """Set error information for failed events."""
        self.success = "failure"
        self.error_code = error_code
        self.error_message = error_message

    def set_duration(self, start_time: datetime) -> None:
        """Set operation duration based on start time."""
        if start_time:
            duration = datetime.utcnow() - start_time
            self.duration_ms = int(duration.total_seconds() * 1000)

    @classmethod
    def create_login_event(
        cls,
        user_id: Optional[int],
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        **details
    ) -> "AuditLog":
        """Create a login audit event."""
        event = cls(
            event_type="login_success" if success else "login_failed",
            action="authenticate_user",
            resource="user",
            resource_id=user_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success="success" if success else "failure",
            error_code=error_code,
            error_message=error_message,
            details=details
        )
        return event

    @classmethod
    def create_user_management_event(
        cls,
        event_type: str,
        actor_user_id: int,
        target_user_id: Optional[int] = None,
        hotel_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        **details
    ) -> "AuditLog":
        """Create a user management audit event."""
        event = cls(
            event_type=event_type,
            action=event_type,
            resource="user",
            resource_id=target_user_id,
            user_id=actor_user_id,
            target_user_id=target_user_id,
            hotel_id=hotel_id,
            branch_id=branch_id,
            old_values=old_values,
            new_values=new_values,
            details=details
        )
        return event

    @classmethod
    def create_access_denied_event(
        cls,
        user_id: int,
        resource: str,
        action: str,
        reason: str,
        ip_address: Optional[str] = None,
        **details
    ) -> "AuditLog":
        """Create an access denied audit event."""
        event = cls(
            event_type="access_denied",
            action=action,
            resource=resource,
            user_id=user_id,
            ip_address=ip_address,
            success="failure",
            error_code="ACCESS_DENIED",
            error_message=reason,
            details=details
        )
        return event

    @classmethod
    def cleanup_old_logs(cls, session, retention_days: int = 365) -> int:
        """Clean up old audit logs based on retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Keep security events longer (2x retention period)
        security_cutoff = datetime.utcnow() - timedelta(days=retention_days * 2)
        
        # Delete non-security events older than retention period
        deleted_count = session.query(cls).filter(
            cls.timestamp < cutoff_date,
            ~cls.event_type.in_([
                "login_failed", "access_denied", "account_locked", "suspicious_activity",
                "brute_force_attempt", "sql_injection_attempt", "xss_attempt"
            ])
        ).delete()
        
        # Delete old security events
        deleted_count += session.query(cls).filter(
            cls.timestamp < security_cutoff,
            cls.event_type.in_([
                "login_failed", "access_denied", "account_locked", "suspicious_activity",
                "brute_force_attempt", "sql_injection_attempt", "xss_attempt"
            ])
        ).delete()
        
        return deleted_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary representation."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "action": self.action,
            "resource": self.resource,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "target_user_id": self.target_user_id,
            "hotel_id": self.hotel_id,
            "branch_id": self.branch_id,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "details": self.details,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "success": self.success,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', user_id={self.user_id}, timestamp={self.timestamp})>"

    def __str__(self) -> str:
        return f"Audit: {self.event_type} by user {self.user_id} at {self.timestamp}"