from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic.types import constr
from typing import Optional
import re
from app.core.config import settings
from app.core.audit_logger import audit_logger


class UserRegistrationInput(BaseModel):
    """
    Validated user registration input with comprehensive security validation.
    Implements all security requirements from Phase 4 specification.
    """
    name: constr(min_length=1, max_length=100) = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Valid email address")
    employee_id: constr(min_length=1, max_length=50) = Field(..., description="Unique employee ID")
    phone: constr(min_length=10, max_length=20) = Field(..., description="Phone number")
    password: constr(min_length=settings.PASSWORD_MIN_LENGTH, max_length=128) = Field(..., description="Password")
    role: str = Field(default="FLEET_USER", description="User role", pattern='^(FLEET_USER|FLEET_MANAGER)$')
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name contains only letters, spaces, hyphens, and apostrophes"""
        if not re.match(r"^[a-zA-Z\s\-']+$", v.strip()):
            audit_logger.log_input_validation_failure(
                validation_type="INVALID_NAME",
                input_value=v[:50]  # Truncate for logging
            )
            raise ValueError('Name must contain only letters, spaces, hyphens, and apostrophes')
        return v.strip()
    
    @field_validator('employee_id')
    @classmethod
    def validate_employee_id(cls, v):
        """Validate employee ID format (alphanumeric, hyphens, underscores)"""
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v.strip()):
            audit_logger.log_input_validation_failure(
                validation_type="INVALID_EMPLOYEE_ID",
                input_value=v[:50]
            )
            raise ValueError('Employee ID must contain only letters, numbers, hyphens, and underscores')
        return v.strip()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format"""
        # Remove all non-digit characters for validation
        phone_digits = re.sub(r'\D', '', v)
        
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            audit_logger.log_input_validation_failure(
                validation_type="INVALID_PHONE_FORMAT",
                input_value=v[:20]
            )
            raise ValueError('Phone number must contain 10-15 digits')
        
        # Allow formats like: +1-234-567-8900, (234) 567-8900, 234.567.8900, 2345678900
        if not re.match(r'^[\+]?[\d\s\-\(\)\.]{10,20}$', v):
            audit_logger.log_input_validation_failure(
                validation_type="INVALID_PHONE_FORMAT",
                input_value=v[:20]
            )
            raise ValueError('Invalid phone number format')
        
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets all security requirements"""
        
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            audit_logger.log_input_validation_failure(
                validation_type="WEAK_PASSWORD_LENGTH",
                input_value="[password redacted]"
            )
            raise ValueError(f'Password must be at least {settings.PASSWORD_MIN_LENGTH} characters')
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', v):
            audit_logger.log_input_validation_failure(
                validation_type="WEAK_PASSWORD_NO_UPPERCASE",
                input_value="[password redacted]"
            )
            raise ValueError('Password must contain at least one uppercase letter')
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', v):
            audit_logger.log_input_validation_failure(
                validation_type="WEAK_PASSWORD_NO_LOWERCASE",
                input_value="[password redacted]"
            )
            raise ValueError('Password must contain at least one lowercase letter')
        
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', v):
            audit_logger.log_input_validation_failure(
                validation_type="WEAK_PASSWORD_NO_DIGIT",
                input_value="[password redacted]"
            )
            raise ValueError('Password must contain at least one digit')
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', v):
            audit_logger.log_input_validation_failure(
                validation_type="WEAK_PASSWORD_NO_SPECIAL",
                input_value="[password redacted]"
            )
            raise ValueError('Password must contain at least one special character')
        
        # Check for common weak passwords (exact matches or simple variations)
        weak_patterns = [
            r'^password\d*$',     # password, password1, password123, etc.
            r'^123456\d*$',       # 123456, 1234567890, etc.
            r'^qwerty\d*$',       # qwerty, qwerty123, etc.
            r'^admin\d*$',        # admin, admin123, etc.
            r'^letmein\d*$',      # letmein, letmein123, etc.
            r'^(.)\1{7,}$',       # Repeating character (8+ times)
            r'^password\W*$',     # password!, password@, etc.
            r'^12345678+$',       # Sequential numbers
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, v.lower()):
                audit_logger.log_input_validation_failure(
                    validation_type="WEAK_PASSWORD_PATTERN",
                    input_value="[password redacted]"
                )
                raise ValueError('Password contains weak patterns and is not secure')
        
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email_security(cls, v):
        """Additional email security validation beyond Pydantic's EmailStr"""
        
        # Check for potential email injection attempts
        dangerous_chars = ['<', '>', '"', '\\', '\n', '\r', '\t']
        for char in dangerous_chars:
            if char in v:
                audit_logger.log_input_validation_failure(
                    validation_type="EMAIL_INJECTION_ATTEMPT",
                    input_value=v[:100]
                )
                raise ValueError('Email contains invalid characters')
        
        # Ensure email is not too long (prevents DoS)
        if len(v) > 254:  # RFC 5321 limit
            audit_logger.log_input_validation_failure(
                validation_type="EMAIL_TOO_LONG",
                input_value=v[:100]
            )
            raise ValueError('Email address is too long')
        
        # Check for suspicious patterns
        if re.search(r'\.{2,}', v):  # Multiple consecutive dots
            audit_logger.log_input_validation_failure(
                validation_type="INVALID_EMAIL_PATTERN",
                input_value=v[:100]
            )
            raise ValueError('Invalid email format')
        
        return v.lower().strip()


class UserUpdateInput(BaseModel):
    """Validated user update input"""
    name: Optional[constr(min_length=1, max_length=100)] = None
    phone: Optional[constr(min_length=10, max_length=20)] = None
    
    @field_validator('name')
    @classmethod
    def validate_name_update(cls, v):
        """Validate name for updates"""
        if v is not None:
            if not re.match(r"^[a-zA-Z\s\-']+$", v.strip()):
                audit_logger.log_input_validation_failure(
                    validation_type="INVALID_NAME_UPDATE",
                    input_value=v[:50]
                )
                raise ValueError('Name must contain only letters, spaces, hyphens, and apostrophes')
            return v.strip()
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone_update(cls, v):
        """Validate phone for updates"""
        if v is not None:
            phone_digits = re.sub(r'\D', '', v)
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                audit_logger.log_input_validation_failure(
                    validation_type="INVALID_PHONE_UPDATE",
                    input_value=v[:20]
                )
                raise ValueError('Phone number must contain 10-15 digits')
            
            if not re.match(r'^[\+]?[\d\s\-\(\)\.]{10,20}$', v):
                audit_logger.log_input_validation_failure(
                    validation_type="INVALID_PHONE_FORMAT_UPDATE",
                    input_value=v[:20]
                )
                raise ValueError('Invalid phone number format')
            return v.strip()
        return v


class PasswordChangeInput(BaseModel):
    """Validated password change input"""
    current_password: str = Field(..., description="Current password")
    new_password: constr(min_length=settings.PASSWORD_MIN_LENGTH, max_length=128) = Field(..., description="New password")
    confirm_password: str = Field(..., description="Confirm new password")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        """Validate new password meets security requirements"""
        # Reuse password strength validation
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {settings.PASSWORD_MIN_LENGTH} characters')
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Ensure password confirmation matches"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Password confirmation does not match')
        return v


def validate_user_id(user_id: int) -> int:
    """
    Validate user ID parameter.
    
    Args:
        user_id: User ID to validate
        
    Returns:
        int: Validated user ID
        
    Raises:
        ValueError: If user ID is invalid
    """
    if not isinstance(user_id, int) or user_id <= 0:
        audit_logger.log_input_validation_failure(
            validation_type="INVALID_USER_ID",
            input_value=str(user_id)
        )
        raise ValueError("User ID must be a positive integer")
    
    # Check for potential integer overflow attacks
    if user_id > 2147483647:  # Max 32-bit signed integer
        audit_logger.log_input_validation_failure(
            validation_type="USER_ID_OVERFLOW",
            input_value=str(user_id)
        )
        raise ValueError("User ID is too large")
    
    return user_id


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search queries to prevent injection attacks.
    
    Args:
        query: Search query string
        
    Returns:
        str: Sanitized query string
    """
    if not query:
        return ""
    
    # Remove potential SQL injection patterns
    dangerous_patterns = [
        r"'",
        r'"',
        r';',
        r'--',
        r'/\*',
        r'\*/',
        r'<script',
        r'javascript:',
        r'onload=',
        r'onerror='
    ]
    
    sanitized = query.strip()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            audit_logger.log_input_validation_failure(
                validation_type="SEARCH_INJECTION_ATTEMPT",
                input_value=sanitized[:100]
            )
            # Remove the dangerous pattern
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Limit length to prevent DoS
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    # Only allow alphanumeric characters, spaces, and basic punctuation
    sanitized = re.sub(r'[^a-zA-Z0-9\s\-_@.]', '', sanitized)
    
    return sanitized.strip()


# Standalone functions for testing
def validate_email(email: str) -> bool:
    """Standalone email validation function for testing"""
    from pydantic import ValidationError
    try:
        UserRegistrationInput.model_validate({
            'name': 'Test User',
            'email': email,
            'employee_id': 'TEST001', 
            'phone': '1234567890',
            'password': 'TempPass@123',
            'role': 'FLEET_USER'
        })
        return True
    except ValidationError:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Standalone password validation function for testing"""
    from pydantic import ValidationError
    try:
        UserRegistrationInput.model_validate({
            'name': 'Test User',
            'email': 'test@example.com',
            'employee_id': 'TEST001',
            'phone': '1234567890', 
            'password': password,
            'role': 'FLEET_USER'
        })
        return True, "Password is valid"
    except ValidationError as e:
        error_msg = str(e)
        # Extract meaningful error message from validation errors
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
        elif not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        elif not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        elif not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        elif not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            return False, "Password must contain at least one special character"
        else:
            return False, "Password does not meet requirements"


def sanitize_name(name: str) -> str:
    """Standalone name sanitization function for testing"""
    if not name:
        return ""
    
    # Remove dangerous characters and HTML tags
    import re
    sanitized = name.strip()
    
    # Remove HTML tags and script elements
    sanitized = re.sub(r'<[^>]*>', '', sanitized)
    
    # Remove SQL injection patterns
    sql_patterns = [
        r'\bDROP\b',
        r'\bTABLE\b',
        r'\bSELECT\b',
        r'\bINSERT\b',
        r'\bUPDATE\b', 
        r'\bDELETE\b',
        r'--',
        r';'
    ]
    
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Remove dangerous characters except letters, spaces, hyphens, apostrophes
    sanitized = re.sub(r"[^a-zA-Z\s\-']", '', sanitized)
    
    # Remove excessive whitespace
    sanitized = ' '.join(sanitized.split())
    
    return sanitized