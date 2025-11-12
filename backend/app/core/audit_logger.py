from datetime import datetime
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any


class AuditLogger:
    """
    Comprehensive audit logger for FleetWise security events.
    Handles logging of authentication events, user actions, security events,
    and system errors in structured JSON format.
    """
    
    def __init__(self):
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Initialize separate loggers for different categories
        self._init_loggers()
    
    def _init_loggers(self):
        """Initialize separate loggers for different log categories"""
        # Audit logger for user actions
        self.logger = logging.getLogger("audit")  # ADD THIS: tests expect self.logger
        self.audit_logger = self.logger  # Keep both for compatibility
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.handlers.clear()
        
        audit_handler = RotatingFileHandler(
            filename="logs/audit.log",
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        )
        audit_handler.setFormatter(logging.Formatter('%(message)s'))
        self.audit_logger.addHandler(audit_handler)
        
        # Security logger for security events
        self.security_logger = logging.getLogger("security")
        self.security_logger.setLevel(logging.WARNING)
        self.security_logger.handlers.clear()
        
        security_handler = RotatingFileHandler(
            filename="logs/security.log",
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        )
        security_handler.setFormatter(logging.Formatter('%(message)s'))
        self.security_logger.addHandler(security_handler)
        
        # Error logger for system errors
        self.error_logger = logging.getLogger("error")
        self.error_logger.setLevel(logging.ERROR)
        self.error_logger.handlers.clear()
        
        error_handler = RotatingFileHandler(
            filename="logs/error.log",
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        )
        error_handler.setFormatter(logging.Formatter('%(message)s'))
        self.error_logger.addHandler(error_handler)
        
        # App logger for general application logs
        self.app_logger = logging.getLogger("app")
        self.app_logger.setLevel(logging.INFO)
        self.app_logger.handlers.clear()
        
        app_handler = RotatingFileHandler(
            filename="logs/app.log",
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        )
        app_handler.setFormatter(logging.Formatter('%(message)s'))
        self.app_logger.addHandler(app_handler)
    
    # ADD THIS METHOD: Tests expect log_action()
    def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        result: str = "SUCCESS",
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log user actions for audit trail.
        
        Args:
            user_id: ID of the user performing the action
            action: Action performed (CREATE_VEHICLE, DELETE_VEHICLE, etc.)
            resource_type: Type of resource (VEHICLE, RESERVATION, USER)
            resource_id: ID of the resource affected
            result: Result of the action (SUCCESS, FAILURE, ERROR)
            ip_address: IP address of the user
            details: Additional context-specific details
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "USER_ACTION",
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "result": result,
            "ip_address": ip_address,
            "details": details or {}
        }
        
        self.audit_logger.info(json.dumps(log_entry))
    
    def log_user_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        result: str = "SUCCESS",
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log user actions for audit trail (alias for log_action).
        """
        self.log_action(user_id, action, resource_type, resource_id, result, ip_address, details)
    
    # ADD THIS METHOD: Tests expect log_authentication()
    def log_authentication(
        self,
        user_email: str,
        success: bool,
        ip_address: str,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> None:
        """
        Log authentication attempts (success and failure).
        
        Args:
            user_email: Email of user attempting to authenticate
            success: Whether authentication was successful
            ip_address: IP address of the authentication attempt
            user_agent: User agent string from the request
            failure_reason: Reason for authentication failure
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "AUTHENTICATION",
            "action": "LOGIN_SUCCESS" if success else "LOGIN_FAILED",
            "user_email": user_email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "result": "SUCCESS" if success else "FAILURE",
            "details": {
                "failure_reason": failure_reason
            } if failure_reason else {}
        }
        
        # Log to both audit and security logs
        self.audit_logger.info(json.dumps(log_entry))
        if not success:
            self.security_logger.warning(json.dumps(log_entry))
    
    def log_authentication_attempt(
        self,
        user_email: str,
        success: bool,
        ip_address: str,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> None:
        """Log authentication attempts (alias for log_authentication)."""
        self.log_authentication(user_email, success, ip_address, user_agent, failure_reason)
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log security-related events.
        
        Args:
            event_type: Type of security event (UNAUTHORIZED_ACCESS, RATE_LIMIT_VIOLATION, etc.)
            severity: Severity level (INFO, WARNING, CRITICAL)
            user_id: User ID if applicable
            ip_address: IP address associated with the event
            details: Additional context-specific details
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "SECURITY_EVENT",
            "event_type": event_type,
            "severity": severity,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {}
        }
        
        self.security_logger.warning(json.dumps(log_entry))
    
    # FIX THIS METHOD: Tests expect 'role' parameter and fields at top level
    def log_unauthorized_access(
        self,
        user_id: int,
        role: str,  # CHANGED from user_role to role
        required_role: str,
        endpoint: str,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log unauthorized access attempts.
        
        Args:
            user_id: ID of user attempting unauthorized access
            role: Current role of the user
            required_role: Required role for the endpoint
            endpoint: Endpoint that was accessed
            ip_address: IP address of the request
        """
        # Test expects all fields at top level
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "SECURITY_EVENT",
            "event_type": "UNAUTHORIZED_ACCESS",
            "severity": "WARNING",
            "user_id": user_id,
            "user_role": role,
            "required_role": required_role,
            "endpoint": endpoint,
            "result": "BLOCKED",  # Top-level field
            "ip_address": ip_address,
            "details": {}
        }
        
        self.security_logger.warning(json.dumps(log_entry))
    
    def log_input_validation_failure(
        self,
        validation_type: str,
        input_value: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log input validation failures.
        
        Args:
            validation_type: Type of validation that failed
            input_value: The input value that failed (sanitized)
            user_id: User ID if available
            ip_address: IP address of the request
            details: Additional validation details
        """
        # Sanitize input value to prevent log injection
        sanitized_input = input_value[:100] if input_value else ""
        
        # Merge provided details with default fields
        log_details = {
            "validation_type": validation_type,
            "sanitized_input": sanitized_input
        }
        if details:
            log_details.update(details)
        
        self.log_security_event(
            event_type="INPUT_VALIDATION_FAILURE",
            severity="WARNING",
            user_id=user_id,
            ip_address=ip_address,
            details=log_details
        )
    
    def log_system_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log system errors and exceptions.
        
        Args:
            error_type: Type of error (DATABASE_ERROR, API_ERROR, etc.)
            error_message: Error message
            user_id: User ID if available
            endpoint: Endpoint where error occurred
            details: Additional error details
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "SYSTEM_ERROR",
            "error_type": error_type,
            "error_message": error_message,
            "user_id": user_id,
            "endpoint": endpoint,
            "details": details or {}
        }
        
        self.error_logger.error(json.dumps(log_entry))
    
    def log_admin_action(
        self,
        admin_user_id: int,
        action: str,
        target_user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log administrative actions.
        
        Args:
            admin_user_id: ID of admin user performing the action
            action: Administrative action performed
            target_user_id: ID of user being affected (if applicable)
            details: Additional action details
        """
        self.log_user_action(
            user_id=admin_user_id,
            action=action,
            resource_type="ADMIN",
            resource_id=target_user_id,
            result="SUCCESS",
            details=details
        )
    
    def log_rate_limit_violation(
        self,
        ip_address: str,
        endpoint: str,
        user_id: Optional[int] = None,
        rate_limit: str = None
    ) -> None:
        """
        Log rate limit violations.
        
        Args:
            ip_address: IP address that exceeded rate limit
            endpoint: Endpoint that was rate limited
            user_id: User ID if available
            rate_limit: The rate limit that was exceeded
        """
        self.log_security_event(
            event_type="RATE_LIMIT_VIOLATION",
            severity="WARNING",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "endpoint": endpoint,
                "rate_limit": rate_limit
            }
        )
    
    def log_app_event(
        self,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log general application events.
        
        Args:
            event_type: Type of application event
            message: Event message
            details: Additional event details
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": "APPLICATION",
            "event_type": event_type,
            "message": message,
            "details": details or {}
        }
        
        self.app_logger.info(json.dumps(log_entry))


# Global audit logger instance
audit_logger = AuditLogger()