"""
Input validation tests for FleetWise application.

Tests all validators to ensure proper input sanitization and validation
as specified in Phase 5 security requirements.
"""

import pytest
from pydantic import ValidationError

from app.validators.user_validator import (
    validate_email,
    validate_password_strength,
    sanitize_name
)
from app.validators.vehicle_validator import (
    validate_license_plate,
    sanitize_vehicle_input
)
from app.validators.reservation_validator import (
    validate_reservation_limit,
    validate_business_rules
)
from app.validators.chatbot_validator import (
    sanitize_chatbot_input,
    validate_query_input
)


class TestEmailValidation:
    """Test email validation functionality"""
    
    def test_valid_emails_pass(self):
        """Test that valid email formats are accepted"""
        valid_emails = [
            "user@example.com",
            "test.email@domain.org",
            "user+tag@company.co.uk",
            "admin@fleet.gov",
            "contact@test-domain.net"
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True
    
    def test_invalid_emails_fail(self):
        """Test that invalid email formats are rejected"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user space@domain.com",
            "user@domain",
            "",
            "user@@domain.com",
            "user@domain..com"
        ]
        
        for email in invalid_emails:
            assert validate_email(email) is False
    
    def test_email_length_limits(self):
        """Test email length validation"""
        # Too long email
        long_email = "a" * 250 + "@domain.com"
        assert validate_email(long_email) is False
        
        # Normal length email
        normal_email = "user@domain.com"
        assert validate_email(normal_email) is True


class TestPasswordValidation:
    """Test password strength validation"""
    
    def test_strong_passwords_pass(self):
        """Test that strong passwords are accepted"""
        strong_passwords = [
            "Password123!",
            "MySecure@Pass1",
            "Fleet2024#Safe",
            "Complex&Pass99"
        ]
        
        for password in strong_passwords:
            is_valid, _ = validate_password_strength(password)
            assert is_valid is True
    
    def test_weak_passwords_fail(self):
        """Test that weak passwords are rejected"""
        weak_passwords = [
            "password",          # No uppercase, no digit, no special
            "PASSWORD",          # No lowercase, no digit, no special  
            "Password",          # No digit, no special
            "Password123",       # No special character
            "Password!",         # No digit
            "pass123!",          # No uppercase
            "Pass1!",           # Too short
            ""                  # Empty
        ]
        
        for password in weak_passwords:
            is_valid, error_msg = validate_password_strength(password)
            assert is_valid is False
            assert isinstance(error_msg, str)
            assert len(error_msg) > 0
    
    def test_password_requirements_messages(self):
        """Test that specific error messages are returned"""
        # Test missing uppercase
        is_valid, msg = validate_password_strength("password123!")
        assert is_valid is False
        assert "uppercase" in msg.lower()
        
        # Test missing digit
        is_valid, msg = validate_password_strength("Password!")
        assert is_valid is False
        assert "digit" in msg.lower()
        
        # Test too short
        is_valid, msg = validate_password_strength("Pass1!")
        assert is_valid is False
        assert "8" in msg or "length" in msg.lower()


class TestLicensePlateValidation:
    """Test license plate validation"""
    
    def test_valid_license_plates(self):
        """Test valid license plate formats"""
        valid_plates = [
            "ABC-1234",
            "XYZ-567",
            "TEST-001",
            "FL-123",
            "ABCD-1234",
            "A1B2C3"
        ]
        
        for plate in valid_plates:
            assert validate_license_plate(plate) is True
    
    def test_invalid_license_plates(self):
        """Test invalid license plate formats"""
        invalid_plates = [
            "",                  # Empty
            "A",                # Too short
            "ABCDEFGHIJK",      # Too long
            "ABC-",             # Incomplete
            "ABC@1234",         # Invalid character
            "ABC 1234",         # Space not allowed
            "ABC_1234",         # Underscore not allowed
            "123-ABC-456"       # Wrong format
        ]
        
        for plate in invalid_plates:
            assert validate_license_plate(plate) is False
    
    def test_license_plate_length_limits(self):
        """Test license plate length constraints"""
        # Minimum length (5 characters)
        assert validate_license_plate("AB123") is True
        assert validate_license_plate("ABCD") is False
        
        # Maximum length (10 characters)
        assert validate_license_plate("ABCD-12345") is True
        assert validate_license_plate("ABCD-123456") is False


class TestNameSanitization:
    """Test name input sanitization"""
    
    def test_name_sanitization(self):
        """Test that names are properly sanitized"""
        # Valid names should pass through unchanged
        valid_names = ["John", "Mary-Jane", "O'Connor", "Van Der Berg"]
        
        for name in valid_names:
            sanitized = sanitize_name(name)
            assert sanitized == name.strip()
    
    def test_dangerous_name_input(self):
        """Test that dangerous characters are removed from names"""
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "John<img src=x>",
            "Mary'; DROP TABLE users; --",
            "Name with <tags>",
        ]
        
        for dangerous_input in dangerous_inputs:
            sanitized = sanitize_name(dangerous_input)
            # Should not contain HTML tags or SQL injection attempts
            assert "<" not in sanitized
            assert ">" not in sanitized
            assert "DROP" not in sanitized.upper()
            assert "SCRIPT" not in sanitized.upper()


class TestVehicleInputSanitization:
    """Test vehicle input sanitization"""
    
    def test_vehicle_input_sanitization(self):
        """Test vehicle manufacturer and model sanitization"""
        valid_inputs = ["Toyota", "Honda Civic", "Ford F-150", "BMW X5"]
        
        for input_str in valid_inputs:
            sanitized = sanitize_vehicle_input(input_str)
            assert sanitized == input_str.strip()
    
    def test_dangerous_vehicle_input(self):
        """Test that dangerous vehicle input is sanitized"""
        dangerous_inputs = [
            "Toyota<script>alert(1)</script>",
            "Honda'; DROP TABLE vehicles; --",
            "Ford<img src=x onerror=alert(1)>",
            "BMW & Co."
        ]
        
        for dangerous_input in dangerous_inputs:
            sanitized = sanitize_vehicle_input(dangerous_input)
            # Should only contain safe characters
            assert all(c.isalnum() or c in " -" for c in sanitized)


class TestChatbotInputSanitization:
    """Test chatbot input validation and sanitization"""
    
    def test_chatbot_input_sanitization(self):
        """Test that chatbot inputs are properly sanitized"""
        clean_inputs = ["Toyota", "Honda", "Ford", "BMW", "Camry", "Accord"]
        
        for input_str in clean_inputs:
            sanitized = sanitize_chatbot_input(input_str)
            assert sanitized == input_str
    
    def test_sql_injection_blocked(self):
        """Test that SQL injection attempts are sanitized"""
        sql_injection_attempts = [
            "'; DROP TABLE vehicles; --",
            "1' OR '1'='1",
            "admin'--",
            "'; UPDATE vehicles SET status='available'; --",
            "UNION SELECT * FROM users"
        ]
        
        for injection_attempt in sql_injection_attempts:
            sanitized = sanitize_chatbot_input(injection_attempt)
            # Should not contain SQL injection patterns
            assert "DROP" not in sanitized.upper()
            assert "UNION" not in sanitized.upper()
            assert "SELECT" not in sanitized.upper()
            assert "--" not in sanitized
            assert "'" not in sanitized
    
    def test_xss_attempts_sanitized(self):
        """Test that XSS attempts are sanitized"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('xss')",
            "<iframe src='malicious.com'></iframe>",
            "onload=alert(1)"
        ]
        
        for xss_attempt in xss_attempts:
            sanitized = sanitize_chatbot_input(xss_attempt)
            # Should not contain HTML tags or JavaScript
            assert "<" not in sanitized
            assert ">" not in sanitized
            assert "javascript:" not in sanitized.lower()
            assert "script" not in sanitized.lower()
    
    def test_special_characters_removed(self):
        """Test that special characters are properly handled"""
        inputs_with_special_chars = [
            "Toyota!@#$%",
            "Honda^&*()",
            "Ford{}[]",
            "BMW+=|\\",
        ]
        
        for input_str in inputs_with_special_chars:
            sanitized = sanitize_chatbot_input(input_str)
            # Should only contain alphanumeric characters
            assert sanitized.isalpha()


class TestReservationValidation:
    """Test reservation business rule validation"""
    
    def test_reservation_limit_validation(self):
        """Test 3-vehicle reservation limit enforcement"""
        # User with 0 reservations should be allowed
        assert validate_reservation_limit(0) is True
        
        # User with 1-2 reservations should be allowed
        assert validate_reservation_limit(1) is True
        assert validate_reservation_limit(2) is True
        
        # User with 3 reservations should be at limit
        result, message = validate_reservation_limit(3)
        assert result is False
        assert "3" in message or "maximum" in message.lower()
        
        # User with more than 3 should definitely be blocked
        result, message = validate_reservation_limit(4)
        assert result is False
    
    def test_business_rules_validation(self):
        """Test various business rule validations"""
        # Valid reservation data
        valid_data = {
            "user_id": 123,
            "vehicle_id": 456,
            "current_reservations": 1
        }
        
        result, message = validate_business_rules(valid_data)
        assert result is True
        
        # Invalid user ID
        invalid_user_data = valid_data.copy()
        invalid_user_data["user_id"] = -1
        
        result, message = validate_business_rules(invalid_user_data)
        assert result is False
        assert "user" in message.lower()
        
        # Invalid vehicle ID
        invalid_vehicle_data = valid_data.copy()
        invalid_vehicle_data["vehicle_id"] = 0
        
        result, message = validate_business_rules(invalid_vehicle_data)
        assert result is False
        assert "vehicle" in message.lower()


class TestQueryInputValidation:
    """Test query input validation"""
    
    def test_valid_query_inputs(self):
        """Test that valid query inputs are accepted"""
        valid_queries = [
            {"manufacturer": "Toyota", "model": "Camry"},
            {"manufacturer": "Honda", "model": "Accord"},
            {"manufacturer": "Ford", "model": "F150"}
        ]
        
        for query in valid_queries:
            assert validate_query_input(query) is True
    
    def test_invalid_query_inputs(self):
        """Test that invalid query inputs are rejected"""
        invalid_queries = [
            {},  # Empty query
            {"manufacturer": ""},  # Empty manufacturer
            {"model": "Camry"},  # Missing manufacturer
            {"manufacturer": "Toyota"},  # Missing model
            {"manufacturer": "Toyota", "model": ""},  # Empty model
        ]
        
        for query in invalid_queries:
            assert validate_query_input(query) is False