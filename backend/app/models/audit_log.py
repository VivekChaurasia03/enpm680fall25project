from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index, Text
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """
    Database model for storing audit trail events.
    Provides persistent storage for security and user actions.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Nullable for system events
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(Integer, nullable=True)
    result = Column(String(20), nullable=False, index=True)  # SUCCESS, FAILURE, ERROR
    ip_address = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)  # Store full user agent string
    details = Column(JSON, nullable=True)  # Additional context in JSON format
    
    # Add composite indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_ip_timestamp', 'ip_address', 'timestamp'),
        Index('idx_audit_resource_type_timestamp', 'resource_type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} by user {self.user_id} at {self.timestamp}>"


class FailedLoginAttempt(Base):
    """
    Database model for tracking failed login attempts and account lockouts.
    Used for implementing account lockout protection.
    """
    __tablename__ = "failed_login_attempts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_email = Column(String(255), nullable=False, index=True)
    attempt_count = Column(Integer, nullable=False, default=1)
    first_attempt = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_attempt = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True, index=True)
    locked_until = Column(DateTime(timezone=True), nullable=True)  # NULL if not locked
    
    # Add composite index for lockout queries
    __table_args__ = (
        Index('idx_failed_login_email_time', 'user_email', 'last_attempt'),
        Index('idx_failed_login_ip_time', 'ip_address', 'last_attempt'),
    )
    
    def __repr__(self):
        return f"<FailedLoginAttempt {self.id}: {self.user_email} - {self.attempt_count} attempts>"
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def lockout_remaining_minutes(self) -> int:
        """Get remaining lockout time in minutes"""
        if not self.is_locked:
            return 0
        remaining = self.locked_until - datetime.utcnow()
        return max(0, int(remaining.total_seconds() / 60))


class SecurityEvent(Base):
    """
    Database model for storing security-related events.
    Provides persistent storage for security monitoring and alerting.
    """
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)  # INFO, WARNING, CRITICAL
    user_id = Column(Integer, nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    resolved = Column(DateTime(timezone=True), nullable=True)  # When event was resolved
    
    # Add composite indexes for security monitoring
    __table_args__ = (
        Index('idx_security_type_severity', 'event_type', 'severity'),
        Index('idx_security_timestamp_severity', 'timestamp', 'severity'),
        Index('idx_security_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_security_ip_timestamp', 'ip_address', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SecurityEvent {self.id}: {self.event_type} - {self.severity}>"
    
    @property
    def is_resolved(self) -> bool:
        """Check if security event has been resolved"""
        return self.resolved is not None