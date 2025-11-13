from pydantic import BaseModel, constr, field_validator, Field
from typing import Optional, List
import re
from app.core.audit_logger import audit_logger


class VehicleCreateInput(BaseModel):
    """
    Validated vehicle creation input with security validation.
    Ensures all vehicle data is properly sanitized and validated.
    """
    manufacturer: constr(min_length=1, max_length=50) = Field(..., description="Vehicle manufacturer")
    model: constr(min_length=1, max_length=50) = Field(..., description="Vehicle model")
    license_plate: constr(min_length=5, max_length=20) = Field(..., description="License plate number")
    
    @field_validator('manufacturer')
    @classmethod
    def validate_manufacturer(cls, v):
        """Validate manufacturer name format and content"""
        if not v or not v.strip():
            raise ValueError('Manufacturer cannot be empty')
        
        # Allow letters, numbers, spaces, hyphens, and ampersands
        if not re.match(r'^[a-zA-Z0-9\s\-&]+$', v.strip()):
            audit_logger.log_input_validation_failure(
                validation_type="INVALID_MANUFACTURER_FORMAT",
                input_value=v[:50]
            )
            raise ValueError('Manufacturer must contain only letters, numbers, spaces, hyphens, and ampersands')
        
        # Check for potential script injection attempts
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'onload=',
            r'onerror=',
            r'<iframe',
            r'<img',
            r'eval\(',
            r'alert\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                audit_logger.log_input_validation_failure(
                    validation_type="MANUFACTURER_SCRIPT_INJECTION",
                    input_value=v[:50]
                )
                raise ValueError('Invalid characters in manufacturer name')
        
        # Ensure reasonable length
        cleaned = v.strip()
        if len(cleaned) < 1:
            raise ValueError('Manufacturer name is too short')
        
        return cleaned.title()  # Standardize capitalization
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        """Validate vehicle model format and content"""
        if not v or not v.strip():
            raise ValueError('Model cannot be empty')
        
        # Allow letters, numbers, spaces, hyphens, periods, and forward slashes
        if not re.match(r'^[a-zA-Z0-9\s\-\./]+$', v.strip()):
            audit_logger.log_input_validation_failure(
                validation_type="INVALID_MODEL_FORMAT",
                input_value=v[:50]
            )
            raise ValueError('Model must contain only letters, numbers, spaces, hyphens, periods, and forward slashes')
        
        # Check for script injection attempts
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'onload=',
            r'onerror=',
            r'<iframe',
            r'<img',
            r'eval\(',
            r'alert\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                audit_logger.log_input_validation_failure(
                    validation_type="MODEL_SCRIPT_INJECTION",
                    input_value=v[:50]
                )
                raise ValueError('Invalid characters in model name')
        
        cleaned = v.strip()
        if len(cleaned) < 1:
            raise ValueError('Model name is too short')
        
        return cleaned
    
    @field_validator('license_plate')
    @classmethod
    def validate_license_plate(cls, v):
        """Validate license plate format with comprehensive security checks"""
        if not v or not v.strip():
            raise ValueError('License plate cannot be empty')
        
        cleaned = v.strip().upper()
        
        # Basic length check
        if len(cleaned) < 5 or len(cleaned) > 20:
            audit_logger.log_input_validation_failure(
                validation_type="INVALID_LICENSE_PLATE_LENGTH",
                input_value=v
            )
            raise ValueError('License plate must be between 5 and 20 characters')
        
        # Allow only alphanumeric characters and hyphens (no spaces)
        if not re.match(r'^[A-Z0-9\-]+$', cleaned):
            audit_logger.log_input_validation_failure(
                validation_type="INVALID_LICENSE_PLATE_FORMAT",
                input_value=v
            )
            raise ValueError('License plate must contain only letters, numbers, and hyphens')
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'^[0-9]+$',  # All numbers (suspicious)
            r'^[A-Z]+$',  # All letters (may be suspicious depending on length)
            r'(.)\1{4,}', # Repeating characters (e.g., AAAAA)
            r'(..)\1{2,}', # Repeating pairs (e.g., ABABABAB)
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, cleaned):
                # Log but don't reject - some valid plates might match these
                audit_logger.log_input_validation_failure(
                    validation_type="SUSPICIOUS_LICENSE_PLATE_PATTERN",
                    input_value=v
                )
        
        # Check for profanity or inappropriate content (basic filter)
        inappropriate_words = [
            'HATE', 'KILL', 'DRUG', 'SEX', 'PORN', 'BOMB',
            'NAZI', 'ISIS', 'FUCK', 'SHIT', 'DAMN', 'HELL'
        ]
        
        for word in inappropriate_words:
            if word in cleaned.replace('-', '').replace(' ', ''):
                audit_logger.log_input_validation_failure(
                    validation_type="INAPPROPRIATE_LICENSE_PLATE",
                    input_value=v
                )
                raise ValueError('License plate contains inappropriate content')
        
        # Validate common license plate formats - be strict about hyphen patterns
        # Check if the plate has proper hyphen format or no hyphens
        hyphen_count = cleaned.count('-')
        
        if hyphen_count == 0:
            # No hyphens - validate as continuous alphanumeric
            valid_no_hyphen = [
                r'^[A-Z]{1,3}[0-9]{1,4}[A-Z]{0,2}$',  # ABC1234, A123B, etc.
                r'^[0-9]{1,3}[A-Z]{1,3}[0-9]{1,4}$',  # 123ABC456
                r'^[A-Z0-9]{5,8}$',  # Mixed alphanumeric
            ]
            is_valid_format = any(re.match(pattern, cleaned) for pattern in valid_no_hyphen)
        elif hyphen_count == 1:
            # Single hyphen - validate specific patterns
            valid_hyphen = [
                r'^[A-Z]{2,4}\-[0-9]{3,5}$',  # AB-1234, ABC-1234, TEST-001, ABCD-12345
                r'^[0-9]{3}\-[A-Z]{2,3}$',  # 123-ABC, 123-AB
                r'^[A-Z]{2,3}\-[0-9]{2,4}$',  # FL-123, XYZ-567
            ]
            is_valid_format = any(re.match(pattern, cleaned) for pattern in valid_hyphen)
        else:
            # Multiple hyphens are not allowed
            is_valid_format = False
        
        if not is_valid_format:
            audit_logger.log_input_validation_failure(
                validation_type="INVALID_LICENSE_PLATE_FORMAT",
                input_value=v
            )
            raise ValueError('License plate format is not recognized')
        
        return cleaned


class VehicleUpdateInput(BaseModel):
    """Validated vehicle update input"""
    manufacturer: Optional[constr(min_length=1, max_length=50)] = None
    model: Optional[constr(min_length=1, max_length=50)] = None
    license_plate: Optional[constr(min_length=5, max_length=20)] = None
    
    @field_validator('manufacturer')
    @classmethod
    def validate_manufacturer_update(cls, v):
        """Validate manufacturer for updates"""
        if v is not None:
            return VehicleCreateInput.validate_manufacturer(v)
        return v
    
    @field_validator('model')
    @classmethod
    def validate_model_update(cls, v):
        """Validate model for updates"""
        if v is not None:
            return VehicleCreateInput.validate_model(v)
        return v
    
    @field_validator('license_plate')
    @classmethod
    def validate_license_plate_update(cls, v):
        """Validate license plate for updates"""
        if v is not None:
            return VehicleCreateInput.validate_license_plate(v)
        return v


class VehicleSearchInput(BaseModel):
    """Validated vehicle search input"""
    manufacturer: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern='^(AVAILABLE|RENTED)$')
    limit: Optional[int] = Field(default=50, ge=1, le=100)
    offset: Optional[int] = Field(default=0, ge=0)
    
    @field_validator('manufacturer', 'model')
    @classmethod
    def sanitize_search_fields(cls, v):
        """Sanitize search input to prevent injection attacks"""
        if v is None:
            return v
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>"\';\\]', '', v.strip())
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"'.*'",
            r'".*"',
            r'--',
            r'/\*',
            r'\*/',
            r'\bUNION\b',
            r'\bSELECT\b',
            r'\bINSERT\b',
            r'\bUPDATE\b',
            r'\bDELETE\b',
            r'\bDROP\b',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                audit_logger.log_input_validation_failure(
                    validation_type="SEARCH_SQL_INJECTION_ATTEMPT",
                    input_value=v[:50]
                )
                return ""  # Return empty string for safety
        
        return sanitized


def validate_vehicle_id(vehicle_id: int) -> int:
    """
    Validate vehicle ID parameter.
    
    Args:
        vehicle_id: Vehicle ID to validate
        
    Returns:
        int: Validated vehicle ID
        
    Raises:
        ValueError: If vehicle ID is invalid
    """
    if not isinstance(vehicle_id, int) or vehicle_id <= 0:
        audit_logger.log_input_validation_failure(
            validation_type="INVALID_VEHICLE_ID",
            input_value=str(vehicle_id)
        )
        raise ValueError("Vehicle ID must be a positive integer")
    
    # Check for potential integer overflow attacks
    if vehicle_id > 2147483647:  # Max 32-bit signed integer
        audit_logger.log_input_validation_failure(
            validation_type="VEHICLE_ID_OVERFLOW",
            input_value=str(vehicle_id)
        )
        raise ValueError("Vehicle ID is too large")
    
    return vehicle_id


def validate_bulk_operation(vehicle_ids: List[int]) -> List[int]:
    """
    Validate list of vehicle IDs for bulk operations.
    
    Args:
        vehicle_ids: List of vehicle IDs
        
    Returns:
        List[int]: Validated vehicle IDs
        
    Raises:
        ValueError: If any vehicle ID is invalid or list is too large
    """
    if not vehicle_ids:
        raise ValueError("Vehicle ID list cannot be empty")
    
    # Prevent DoS attacks with large lists
    if len(vehicle_ids) > 100:
        audit_logger.log_input_validation_failure(
            validation_type="BULK_OPERATION_TOO_LARGE",
            input_value=f"List size: {len(vehicle_ids)}"
        )
        raise ValueError("Cannot process more than 100 vehicles at once")
    
    # Validate each ID
    validated_ids = []
    for vehicle_id in vehicle_ids:
        validated_ids.append(validate_vehicle_id(vehicle_id))
    
    # Check for duplicates
    if len(set(validated_ids)) != len(validated_ids):
        audit_logger.log_input_validation_failure(
            validation_type="DUPLICATE_VEHICLE_IDS",
            input_value=str(validated_ids)
        )
        raise ValueError("Duplicate vehicle IDs not allowed")
    
    return validated_ids


def sanitize_vehicle_data_export(data: dict) -> dict:
    """
    Sanitize vehicle data for export to prevent information disclosure.
    
    Args:
        data: Raw vehicle data dictionary
        
    Returns:
        dict: Sanitized vehicle data
    """
    # Define allowed fields for export
    allowed_fields = {
        'vehicle_id',
        'manufacturer',
        'model',
        'license_plate',
        'status',
        'created_at'
    }
    
    # Only include allowed fields
    sanitized = {key: value for key, value in data.items() if key in allowed_fields}
    
    # Ensure no sensitive data is included
    sensitive_patterns = [
        'password',
        'secret',
        'key',
        'token',
        'hash'
    ]
    
    for key in list(sanitized.keys()):
        for pattern in sensitive_patterns:
            if pattern in key.lower():
                audit_logger.log_security_event(
                    event_type="SENSITIVE_DATA_EXPORT_ATTEMPT",
                    severity="WARNING",
                    details={"attempted_field": key}
                )
                del sanitized[key]
                break
    
    return sanitized


# Standalone functions for testing
def validate_license_plate(license_plate: str) -> bool:
    """Standalone license plate validation function for testing"""
    from pydantic import ValidationError
    try:
        VehicleCreateInput.model_validate({
            'manufacturer': 'Test Manufacturer',
            'model': 'Test Model',
            'license_plate': license_plate
        })
        return True
    except ValidationError:
        return False


def sanitize_vehicle_input(input_str: str) -> str:
    """Standalone vehicle input sanitization function for testing"""
    if not input_str:
        return ""
    
    import re
    sanitized = input_str.strip()
    
    # Remove HTML tags and script elements
    sanitized = re.sub(r'<[^>]*>', '', sanitized)
    
    # Remove SQL injection patterns
    dangerous_patterns = [
        r"'.*'",
        r'".*"',
        r'--',
        r'/\*',
        r'\*/',
        r'\bDROP\b',
        r'\bSELECT\b',
        r'\bINSERT\b',
        r'\bUPDATE\b',
        r'\bDELETE\b',
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Keep only alphanumeric characters, spaces, and hyphens  
    sanitized = re.sub(r'[^a-zA-Z0-9\s\-]', '', sanitized)
    
    # Remove excessive whitespace
    sanitized = ' '.join(sanitized.split())
    
    return sanitized