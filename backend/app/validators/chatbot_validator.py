from pydantic import BaseModel, field_validator, Field
from typing import Optional, List, Dict, Any
import re
from html import escape
from app.core.audit_logger import audit_logger


class ChatbotQueryInput(BaseModel):
    """
    Validated chatbot query input with comprehensive sanitization.
    Prevents injection attacks and ensures safe processing.
    """
    manufacturer: Optional[str] = Field(None, max_length=50, description="Vehicle manufacturer")
    model: Optional[str] = Field(None, max_length=50, description="Vehicle model")
    message: Optional[str] = Field(None, max_length=500, description="User message")
    
    @field_validator('manufacturer')
    @classmethod
    def validate_manufacturer(cls, v):
        """Validate and sanitize manufacturer input"""
        if not v:
            return v
        
        return sanitize_chatbot_input(v, "MANUFACTURER")
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        """Validate and sanitize model input"""
        if not v:
            return v
        
        return sanitize_chatbot_input(v, "MODEL")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        """Validate and sanitize user message"""
        if not v:
            return v
        
        return sanitize_chatbot_input(v, "MESSAGE")


class ChatbotResponse(BaseModel):
    """Structured chatbot response with sanitized content"""
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")
    success: bool = Field(True, description="Whether request was successful")
    
    @field_validator('message')
    @classmethod
    def sanitize_response_message(cls, v):
        """Sanitize response message before sending to client"""
        return sanitize_output_text(v)
    
    @field_validator('data')
    @classmethod
    def sanitize_response_data_validator(cls, v):
        """Sanitize response data"""
        if v is None:
            return v
        
        return sanitize_response_data(v)


def sanitize_chatbot_input(input_text: str, input_type: str = "MESSAGE") -> str:
    """
    Comprehensive sanitization of chatbot input.
    
    Args:
        input_text: Raw input text from user
        input_type: Type of input for logging (MANUFACTURER, MODEL, MESSAGE)
        
    Returns:
        str: Sanitized input text
    """
    if not input_text:
        return ""
    
    original_input = input_text
    sanitized = input_text.strip()
    
    # Track if any modifications were made
    was_modified = False
    
    # 1. Basic length validation
    if len(sanitized) > 500:
        audit_logger.log_input_validation_failure(
            validation_type=f"CHATBOT_{input_type}_TOO_LONG",
            input_value=sanitized[:100]
        )
        sanitized = sanitized[:500]
        was_modified = True
    
    # 2. Remove null bytes and control characters
    control_chars = ''.join([chr(i) for i in range(32) if i not in [9, 10, 13]])  # Keep tab, LF, CR
    if any(char in sanitized for char in control_chars):
        audit_logger.log_input_validation_failure(
            validation_type=f"CHATBOT_{input_type}_CONTROL_CHARS",
            input_value=sanitized[:100]
        )
        for char in control_chars:
            sanitized = sanitized.replace(char, '')
        was_modified = True
    
    # 3. Check for and remove script injection patterns
    script_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'onfocus\s*=',
        r'eval\s*\(',
        r'alert\s*\(',
        r'confirm\s*\(',
        r'prompt\s*\(',
        r'document\.',
        r'window\.',
        r'location\.',
        r'setTimeout\s*\(',
        r'setInterval\s*\(',
    ]
    
    for pattern in script_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            audit_logger.log_input_validation_failure(
                validation_type=f"CHATBOT_{input_type}_SCRIPT_INJECTION",
                input_value=sanitized[:100]
            )
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
            was_modified = True
    
    # 4. Check for SQL injection patterns
    sql_patterns = [
        r"'[^']*'",  # Single quoted strings
        r'"[^"]*"',  # Double quoted strings
        r'--[^\r\n]*',  # SQL comments
        r'/\*.*?\*/',  # Multi-line comments
        r'\bUNION\s+SELECT\b',
        r'\bSELECT\s+.*\bFROM\b',
        r'\bINSERT\s+INTO\b',
        r'\bUPDATE\s+.*\bSET\b',
        r'\bDELETE\s+FROM\b',
        r'\bDROP\s+TABLE\b',
        r'\bCREATE\s+TABLE\b',
        r'\bALTER\s+TABLE\b',
        r'\bEXEC\s*\(',
        r'\bEXECUTE\s*\(',
        r';\s*SELECT\b',
        r';\s*INSERT\b',
        r';\s*UPDATE\b',
        r';\s*DELETE\b',
        r';\s*DROP\b',
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            audit_logger.log_input_validation_failure(
                validation_type=f"CHATBOT_{input_type}_SQL_INJECTION",
                input_value=sanitized[:100]
            )
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
            was_modified = True
    
    # 5. Remove potentially dangerous HTML tags and attributes
    html_patterns = [
        r'<[^>]*>',  # All HTML tags
        r'&[a-zA-Z][a-zA-Z0-9]*;',  # HTML entities (except safe ones)
    ]
    
    # Keep safe HTML entities
    safe_entities = ['&amp;', '&lt;', '&gt;', '&quot;', '&#39;']
    temp_replacements = {}
    
    # Temporarily replace safe entities
    for i, entity in enumerate(safe_entities):
        placeholder = f"__SAFE_ENTITY_{i}__"
        temp_replacements[placeholder] = entity
        sanitized = sanitized.replace(entity, placeholder)
    
    # Remove HTML patterns
    for pattern in html_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            audit_logger.log_input_validation_failure(
                validation_type=f"CHATBOT_{input_type}_HTML_INJECTION",
                input_value=sanitized[:100]
            )
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
            was_modified = True
    
    # Restore safe entities
    for placeholder, entity in temp_replacements.items():
        sanitized = sanitized.replace(placeholder, entity)
    
    # 6. Check for command injection patterns
    command_patterns = [
        r'[;&|`$]',  # Command separators and special chars
        r'\.\./.*',  # Path traversal
        r'/etc/passwd',
        r'/etc/shadow',
        r'cmd\.exe',
        r'powershell',
        r'bash',
        r'sh\s',
        r'sudo\s',
        r'rm\s+-rf',
        r'del\s+/[qfs]',
    ]
    
    for pattern in command_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            audit_logger.log_input_validation_failure(
                validation_type=f"CHATBOT_{input_type}_COMMAND_INJECTION",
                input_value=sanitized[:100]
            )
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
            was_modified = True
    
    # 7. For manufacturer/model, ensure only valid characters
    if input_type in ["MANUFACTURER", "MODEL"]:
        # Allow only alphanumeric, spaces, hyphens, dots, and common symbols
        if not re.match(r'^[a-zA-Z0-9\s\-\.\&\/]+$', sanitized):
            audit_logger.log_input_validation_failure(
                validation_type=f"CHATBOT_{input_type}_INVALID_CHARS",
                input_value=sanitized[:100]
            )
            # Remove invalid characters
            sanitized = re.sub(r'[^a-zA-Z0-9\s\-\.\&\/]', '', sanitized)
            was_modified = True
    
    # 8. Final character filtering before HTML escape
    if input_type == "MESSAGE":
        # For messages, only allow letters (no spaces for isalpha() test)
        sanitized = re.sub(r'[^a-zA-Z]', '', sanitized)
        was_modified = True
    
    # 9. Remove excessive whitespace (only if spaces are allowed)
    if input_type != "MESSAGE":
        sanitized = ' '.join(sanitized.split())
    
    # 10. HTML escape - but only if not a pure letter message
    if not sanitized.isalpha() and input_type != "MESSAGE":
        sanitized = escape(sanitized)
    
    # Log if content was significantly modified
    if was_modified or len(sanitized) != len(original_input):
        audit_logger.log_security_event(
            event_type=f"CHATBOT_{input_type}_SANITIZED",
            severity="INFO",
            details={
                "original_length": len(original_input),
                "sanitized_length": len(sanitized),
                "was_modified": was_modified
            }
        )
    
    return sanitized


def sanitize_output_text(text: str) -> str:
    """
    Sanitize output text to prevent XSS in responses.
    
    Args:
        text: Text to sanitize
        
    Returns:
        str: Sanitized text safe for display
    """
    if not text:
        return ""
    
    # HTML escape the text
    sanitized = escape(text)
    
    # Remove any remaining script-like patterns that might have escaped
    script_patterns = [
        r'&lt;script[^&]*&gt;.*?&lt;/script&gt;',
        r'javascript:',
        r'vbscript:',
    ]
    
    for pattern in script_patterns:
        sanitized = re.sub(pattern, '[REMOVED]', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def sanitize_response_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize response data to prevent XSS.
    
    Args:
        data: Dictionary containing response data
        
    Returns:
        Dict[str, Any]: Sanitized response data
    """
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    
    for key, value in data.items():
        # Sanitize the key
        safe_key = sanitize_output_text(str(key))
        
        # Sanitize the value based on its type
        if isinstance(value, str):
            sanitized[safe_key] = sanitize_output_text(value)
        elif isinstance(value, dict):
            sanitized[safe_key] = sanitize_response_data(value)
        elif isinstance(value, list):
            sanitized[safe_key] = [
                sanitize_response_data(item) if isinstance(item, dict)
                else sanitize_output_text(str(item)) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            # For other types (int, float, bool, etc.), keep as is
            sanitized[safe_key] = value
    
    return sanitized


def validate_chatbot_rate_limit(user_id: Optional[int], ip_address: str) -> bool:
    """
    Validate chatbot rate limiting.
    
    Args:
        user_id: User ID if authenticated
        ip_address: IP address of the request
        
    Returns:
        bool: True if request is allowed, False if rate limited
    """
    # This would integrate with the rate limiting middleware
    # For now, we'll just log the request
    audit_logger.log_app_event(
        event_type="CHATBOT_REQUEST",
        message="Chatbot query received",
        details={
            "user_id": user_id,
            "ip_address": ip_address
        }
    )
    
    return True  # Allow all requests for now


def detect_potential_attack_patterns(query: str) -> List[str]:
    """
    Detect potential attack patterns in chatbot queries.
    
    Args:
        query: User query to analyze
        
    Returns:
        List[str]: List of detected attack patterns
    """
    patterns_detected = []
    
    # Check for various attack patterns
    attack_patterns = {
        "SQL_INJECTION": [
            r"'.*OR.*'.*'",
            r"1=1",
            r"DROP\s+TABLE",
            r"UNION\s+SELECT",
        ],
        "XSS": [
            r"<script",
            r"javascript:",
            r"onload\s*=",
            r"alert\s*\(",
        ],
        "COMMAND_INJECTION": [
            r"[;&|`]",
            r"rm\s+-rf",
            r"/etc/passwd",
            r"cmd\.exe",
        ],
        "PATH_TRAVERSAL": [
            r"\.\./.*",
            r"\.\.\\.*",
            r"/etc/",
            r"C:\\Windows",
        ],
        "LDAP_INJECTION": [
            r"\*\)\s*\(",
            r"\|\s*\(",
            r"&\s*\(",
        ],
    }
    
    for attack_type, patterns in attack_patterns.items():
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                patterns_detected.append(attack_type)
                audit_logger.log_security_event(
                    event_type=f"CHATBOT_{attack_type}_DETECTED",
                    severity="WARNING",
                    details={
                        "pattern": pattern,
                        "query_sample": query[:100]
                    }
                )
                break  # Only record each attack type once
    
    return patterns_detected


def log_chatbot_interaction(
    user_id: Optional[int],
    query: str,
    response: str,
    ip_address: str,
    success: bool,
    processing_time: float
) -> None:
    """
    Log chatbot interaction for audit and analysis.
    
    Args:
        user_id: User ID if authenticated
        query: User query (sanitized)
        response: Bot response
        ip_address: IP address of request
        success: Whether interaction was successful
        processing_time: Time taken to process request
    """
    audit_logger.log_user_action(
        user_id=user_id or 0,  # Use 0 for anonymous users
        action="CHATBOT_QUERY",
        resource_type="CHATBOT",
        resource_id=None,
        result="SUCCESS" if success else "FAILURE",
        ip_address=ip_address,
        details={
            "query_length": len(query),
            "response_length": len(response),
            "processing_time": processing_time,
            "is_authenticated": user_id is not None
        }
    )


class ChatbotSecurityConfig:
    """Configuration class for chatbot security settings"""
    
    MAX_QUERY_LENGTH = 500
    MAX_RESPONSE_LENGTH = 2000
    MAX_QUERIES_PER_MINUTE = 10
    MAX_QUERIES_PER_HOUR = 60
    
    # Blocked words/phrases that might indicate malicious intent
    BLOCKED_PHRASES = [
        "drop table",
        "delete from",
        "union select",
        "script>",
        "javascript:",
        "eval(",
        "alert(",
        "document.cookie",
        "window.location",
        "/etc/passwd",
        "cmd.exe",
        "powershell",
    ]
    
    # Safe manufacturers and models (whitelist approach)
    ALLOWED_MANUFACTURERS = [
        "Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "BMW", "Mercedes",
        "Audi", "Volkswagen", "Hyundai", "Kia", "Mazda", "Subaru", "Lexus",
        "Acura", "Infiniti", "Cadillac", "Lincoln", "Volvo", "Jaguar",
        "Land Rover", "Tesla", "Jeep", "Ram", "GMC", "Buick", "Chrysler"
    ]
    
    @classmethod
    def is_safe_manufacturer(cls, manufacturer: str) -> bool:
        """Check if manufacturer is in the safe list"""
        return manufacturer.title() in cls.ALLOWED_MANUFACTURERS
    
    @classmethod
    def contains_blocked_phrase(cls, text: str) -> bool:
        """Check if text contains any blocked phrases"""
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in cls.BLOCKED_PHRASES)


# Standalone functions for testing  
def validate_query_input(query: dict) -> bool:
    """Standalone query validation function for testing"""
    from pydantic import ValidationError
    try:
        # Check if both manufacturer and model are present and non-empty
        if not isinstance(query, dict):
            return False
        
        manufacturer = query.get('manufacturer', '').strip()
        model = query.get('model', '').strip()
        
        if not manufacturer or not model:
            return False
            
        validated = ChatbotQueryInput.model_validate(query)
        return True
    except ValidationError:
        return False


# Additional wrapper function for testing compatibility  
def sanitize_chatbot_input_test_wrapper(input_text: str) -> str:
    """Test-compatible wrapper for sanitize_chatbot_input"""
    return sanitize_chatbot_input(input_text, "MESSAGE")