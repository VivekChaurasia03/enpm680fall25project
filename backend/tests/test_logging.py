"""
Audit logging tests for FleetWise application.

Tests logging functionality for all 5 required categories:
1. Authentication events
2. Sensitive function access
3. Input validation failures  
4. System errors
5. Administrative actions

As specified in Phase 5 security requirements.
"""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, Mock, mock_open
from datetime import datetime

from app.core.audit_logger import audit_logger, AuditLogger
from app.models.audit_log import AuditLog


class TestAuditLogger:
    """Test the AuditLogger class functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_logger = AuditLogger()
        self.test_log_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log')
        self.test_log_file.close()
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.test_log_file.name):
            os.unlink(self.test_log_file.name)


class TestAuthenticationLogging:
    """Test authentication event logging"""
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_login_success_logged(self, mock_get_logger, mock_file_handler):
        """Test that successful login creates proper log entry"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test login success logging
        audit_logger_instance.log_authentication(
            user_email="user@fleet.com",
            success=True,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Test Browser)"
        )
        
        # Verify logger was called
        assert mock_logger.info.called
        
        # Check log entry content
        log_call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["action"] == "LOGIN_SUCCESS"
        assert log_entry["user_email"] == "user@fleet.com"
        assert log_entry["ip_address"] == "192.168.1.100"
        assert log_entry["user_agent"] == "Mozilla/5.0 (Test Browser)"
        assert "timestamp" in log_entry
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_login_failure_logged(self, mock_get_logger, mock_file_handler):
        """Test that failed login creates proper log entry"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test login failure logging
        audit_logger_instance.log_authentication(
            user_email="hacker@evil.com",
            success=False,
            ip_address="10.0.0.1",
            user_agent="Evil Bot 1.0"
        )
        
        # Verify logger was called
        assert mock_logger.info.called
        
        # Check log entry content
        log_call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["action"] == "LOGIN_FAILED"
        assert log_entry["user_email"] == "hacker@evil.com"
        assert log_entry["ip_address"] == "10.0.0.1"
        assert "timestamp" in log_entry
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_logout_logged(self, mock_get_logger, mock_file_handler):
        """Test that logout events are logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test logout logging
        audit_logger_instance.log_action(
            user_id=123,
            action="LOGOUT",
            resource_type="auth",
            details={"session_duration": "25 minutes"}
        )
        
        # Verify logger was called
        assert mock_logger.info.called
        
        log_call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["action"] == "LOGOUT"
        assert log_entry["user_id"] == 123
        assert log_entry["resource_type"] == "auth"
        assert log_entry["details"]["session_duration"] == "25 minutes"


class TestSensitiveFunctionLogging:
    """Test logging of sensitive function access"""
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_vehicle_creation_logged(self, mock_get_logger, mock_file_handler):
        """Test that vehicle creation is logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test vehicle creation logging
        audit_logger_instance.log_action(
            user_id=1,
            action="CREATE_VEHICLE",
            resource_type="VEHICLE",
            resource_id=456,
            result="SUCCESS",
            details={
                "manufacturer": "Toyota",
                "model": "Camry",
                "license_plate": "ABC-1234"
            }
        )
        
        # Verify logger was called
        assert mock_logger.info.called
        
        log_call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["action"] == "CREATE_VEHICLE"
        assert log_entry["user_id"] == 1
        assert log_entry["resource_type"] == "VEHICLE"
        assert log_entry["resource_id"] == 456
        assert log_entry["result"] == "SUCCESS"
        assert log_entry["details"]["manufacturer"] == "Toyota"
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_vehicle_deletion_logged(self, mock_get_logger, mock_file_handler):
        """Test that vehicle deletion is logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test vehicle deletion logging
        audit_logger_instance.log_action(
            user_id=1,
            action="DELETE_VEHICLE",
            resource_type="VEHICLE",
            resource_id=456,
            result="SUCCESS",
            details={"reason": "Vehicle decommissioned"}
        )
        
        # Verify logging occurred
        assert mock_logger.info.called
        
        log_call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["action"] == "DELETE_VEHICLE"
        assert log_entry["resource_type"] == "VEHICLE"
        assert log_entry["resource_id"] == 456
        assert log_entry["result"] == "SUCCESS"
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_reservation_creation_logged(self, mock_get_logger, mock_file_handler):
        """Test that reservation creation is logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test reservation creation logging
        audit_logger_instance.log_action(
            user_id=1,  # Manager who created the reservation
            action="CREATE_RESERVATION",
            resource_type="RESERVATION",
            resource_id=789,
            result="SUCCESS",
            details={
                "reserved_for_user_id": 2,
                "vehicle_id": 456,
                "reservation_date": "2025-11-10T10:30:00Z"
            }
        )
        
        # Verify logging occurred
        assert mock_logger.info.called
        
        log_call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["action"] == "CREATE_RESERVATION"
        assert log_entry["resource_type"] == "RESERVATION"
        assert log_entry["details"]["reserved_for_user_id"] == 2


class TestUnauthorizedAccessLogging:
    """Test logging of unauthorized access attempts"""
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_unauthorized_access_logged(self, mock_get_logger, mock_file_handler):
        """Test that unauthorized access attempts are logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test unauthorized access logging
        audit_logger_instance.log_unauthorized_access(
            user_id=2,
            role="FLEET_USER",
            required_role="FLEET_MANAGER",
            endpoint="create_vehicle"
        )
        
        # Verify warning was logged (unauthorized access uses warning level)
        assert mock_logger.warning.called
        
        log_call_args = mock_logger.warning.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["event_type"] == "UNAUTHORIZED_ACCESS"
        assert log_entry["user_id"] == 2
        assert log_entry["user_role"] == "FLEET_USER"
        assert log_entry["required_role"] == "FLEET_MANAGER"
        assert log_entry["endpoint"] == "create_vehicle"
        assert log_entry["result"] == "BLOCKED"


class TestValidationFailureLogging:
    """Test logging of input validation failures"""
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_validation_failure_logged(self, mock_get_logger, mock_file_handler):
        """Test that validation failures are logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test validation failure logging
        audit_logger_instance.log_security_event(
            event_type="VALIDATION_FAILURE",
            severity="WARNING",
            details={
                "field": "email",
                "value": "invalid-email-format",
                "error": "Invalid email format",
                "endpoint": "/auth/register"
            }
        )
        
        # Verify warning was logged
        assert mock_logger.warning.called
        
        log_call_args = mock_logger.warning.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["event_type"] == "VALIDATION_FAILURE"
        assert log_entry["severity"] == "WARNING"
        assert log_entry["details"]["field"] == "email"
        assert log_entry["details"]["error"] == "Invalid email format"
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_sql_injection_attempt_logged(self, mock_get_logger, mock_file_handler):
        """Test that SQL injection attempts are logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test SQL injection logging
        audit_logger_instance.log_security_event(
            event_type="SQL_INJECTION_ATTEMPT",
            severity="CRITICAL",
            details={
                "input": "'; DROP TABLE vehicles; --",
                "endpoint": "/chatbot/query",
                "user_id": 999,
                "blocked": True
            }
        )
        
        # Verify warning was logged
        assert mock_logger.warning.called
        
        log_call_args = mock_logger.warning.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["event_type"] == "SQL_INJECTION_ATTEMPT"
        assert log_entry["severity"] == "CRITICAL"
        assert log_entry["details"]["blocked"] is True


class TestSystemErrorLogging:
    """Test logging of system errors"""
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_database_error_logged(self, mock_get_logger, mock_file_handler):
        """Test that database errors are logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test database error logging
        audit_logger_instance.log_security_event(
            event_type="DATABASE_ERROR",
            severity="ERROR",
            details={
                "error": "Connection timeout",
                "operation": "SELECT * FROM vehicles",
                "duration": "30 seconds"
            }
        )
        
        # Verify warning was logged
        assert mock_logger.warning.called
        
        log_call_args = mock_logger.warning.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["event_type"] == "DATABASE_ERROR"
        assert log_entry["severity"] == "ERROR"
        assert log_entry["details"]["error"] == "Connection timeout"
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_api_error_logged(self, mock_get_logger, mock_file_handler):
        """Test that API errors are logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test API error logging
        audit_logger_instance.log_security_event(
            event_type="API_ERROR",
            severity="ERROR",
            details={
                "endpoint": "/vehicles",
                "method": "POST",
                "status_code": 500,
                "error": "Internal server error"
            }
        )
        
        # Verify warning was logged
        assert mock_logger.warning.called
        
        log_call_args = mock_logger.warning.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["event_type"] == "API_ERROR"
        assert log_entry["details"]["status_code"] == 500


class TestAdministrativeActionLogging:
    """Test logging of administrative actions"""
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_user_role_change_logged(self, mock_get_logger, mock_file_handler):
        """Test that user role changes are logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test user role change logging
        audit_logger_instance.log_action(
            user_id=1,  # Admin who made the change
            action="CHANGE_USER_ROLE",
            resource_type="USER",
            resource_id=2,  # User whose role was changed
            result="SUCCESS",
            details={
                "old_role": "FLEET_USER",
                "new_role": "FLEET_MANAGER",
                "reason": "Promotion to manager"
            }
        )
        
        # Verify logging occurred
        assert mock_logger.info.called
        
        log_call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["action"] == "CHANGE_USER_ROLE"
        assert log_entry["resource_type"] == "USER"
        assert log_entry["resource_id"] == 2
        assert log_entry["details"]["old_role"] == "FLEET_USER"
        assert log_entry["details"]["new_role"] == "FLEET_MANAGER"
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_account_unlock_logged(self, mock_get_logger, mock_file_handler):
        """Test that account unlock actions are logged"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test account unlock logging
        audit_logger_instance.log_action(
            user_id=1,  # Admin who unlocked the account
            action="UNLOCK_ACCOUNT",
            resource_type="USER",
            resource_id=3,  # User whose account was unlocked
            result="SUCCESS",
            details={
                "locked_reason": "Failed login attempts",
                "unlock_reason": "User verified identity"
            }
        )
        
        # Verify logging occurred
        assert mock_logger.info.called
        
        log_call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call_args)
        
        assert log_entry["action"] == "UNLOCK_ACCOUNT"
        assert log_entry["resource_type"] == "USER"
        assert log_entry["details"]["locked_reason"] == "Failed login attempts"


class TestLogFormat:
    """Test log format and structure"""
    
    @patch('app.core.audit_logger.logging.FileHandler')
    @patch('app.core.audit_logger.logging.getLogger')
    def test_logs_are_json_format(self, mock_get_logger, mock_file_handler):
        """Test that all logs are in valid JSON format"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger_instance = AuditLogger()
        
        # Test various log types
        audit_logger_instance.log_action(
            user_id=1,
            action="TEST_ACTION",
            resource_type="TEST",
            result="SUCCESS"
        )
        
        # Verify logger was called
        assert mock_logger.info.called
        
        # Check that the log entry is valid JSON
        log_call_args = mock_logger.info.call_args[0][0]
        log_entry = json.loads(log_call_args)  # This will raise exception if not valid JSON
        
        # Check required fields are present
        assert "timestamp" in log_entry
        assert "user_id" in log_entry
        assert "action" in log_entry
        assert "result" in log_entry
        
        # Check timestamp format
        timestamp_str = log_entry["timestamp"]
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))  # Should not raise exception
    
    def test_log_file_creation(self):
        """Test that log files are created properly"""
        # This test would typically check that the actual log files exist
        # For now, we'll test the logger configuration
        
        audit_logger_instance = AuditLogger()
        
        # Check that logger has the correct name
        assert audit_logger_instance.logger.name == "audit"
        
        # Check that logger has file handler
        assert len(audit_logger_instance.logger.handlers) > 0


class TestLogRotation:
    """Test log rotation functionality"""
    
    def test_log_rotation_configuration(self):
        """Test that log rotation is properly configured"""
        # This would typically test the actual rotation
        # For now, verify the logger setup
        
        audit_logger_instance = AuditLogger()
        
        # Verify logger exists and is configured
        assert audit_logger_instance.logger is not None
        assert audit_logger_instance.logger.level == 20  # INFO level