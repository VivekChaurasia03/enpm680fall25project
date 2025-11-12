import traceback
import uuid
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from pydantic import ValidationError
from jose import JWTError

from app.core.audit_logger import audit_logger


class ErrorHandler:
    """
    Centralized error handling with comprehensive logging and sanitized responses.
    Ensures no sensitive information is leaked to clients.
    """
    
    def __init__(self):
        self.error_mappings = {
            # Authentication and authorization errors
            JWTError: {
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "detail": "Authentication failed",
                "headers": {"WWW-Authenticate": "Bearer"}
            },
            
            # Database errors
            IntegrityError: {
                "status_code": status.HTTP_409_CONFLICT,
                "detail": "Data integrity constraint violated"
            },
            OperationalError: {
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "detail": "Service temporarily unavailable"
            },
            SQLAlchemyError: {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Database operation failed"
            },
            
            # Validation errors
            ValidationError: {
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "detail": "Invalid input data"
            },
            
            # General errors
            ValueError: {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": "Invalid request parameters"
            },
            KeyError: {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": "Missing required parameter"
            },
            FileNotFoundError: {
                "status_code": status.HTTP_404_NOT_FOUND,
                "detail": "Resource not found"
            },
            PermissionError: {
                "status_code": status.HTTP_403_FORBIDDEN,
                "detail": "Access denied"
            }
        }
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking"""
        return str(uuid.uuid4())[:8]
    
    def _extract_user_info(self, request: Request) -> Dict[str, Any]:
        """Extract user information from request for logging"""
        user_info = {
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
            "endpoint": request.url.path,
            "method": request.method,
            "user_id": None
        }
        
        # Try to extract user ID from token (simplified)
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                from jose import jwt
                from app.core.config import settings
                
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_info["user_email"] = payload.get("sub")
        except:
            pass
        
        return user_info
    
    def _sanitize_error_details(self, error: Exception) -> str:
        """Sanitize error details to prevent information disclosure"""
        error_str = str(error)
        
        # List of sensitive patterns to redact
        sensitive_patterns = [
            r"password\s*[:=]\s*\S+",
            r"token\s*[:=]\s*\S+",
            r"key\s*[:=]\s*\S+",
            r"secret\s*[:=]\s*\S+",
            r"auth\s*[:=]\s*\S+",
            r"/[a-zA-Z]:/.*",  # Windows paths
            r"/home/.*",       # Unix home paths
            r"/etc/.*",        # System paths
        ]
        
        import re
        sanitized = error_str
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
        
        # Truncate if too long
        if len(sanitized) > 200:
            sanitized = sanitized[:197] + "..."
        
        return sanitized
    
    async def handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions"""
        error_id = self._generate_error_id()
        user_info = self._extract_user_info(request)
        
        # Log the error
        log_details = {
            "error_id": error_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
            **user_info
        }
        
        if exc.status_code >= 500:
            # Server errors
            audit_logger.log_system_error(
                error_type="HTTP_SERVER_ERROR",
                error_message=f"HTTP {exc.status_code}: {exc.detail}",
                endpoint=user_info["endpoint"],
                details=log_details
            )
        elif exc.status_code == 403:
            # Forbidden - security event
            audit_logger.log_security_event(
                event_type="ACCESS_DENIED",
                severity="WARNING",
                user_id=user_info.get("user_id"),
                ip_address=user_info["ip_address"],
                details=log_details
            )
        elif exc.status_code == 401:
            # Unauthorized - authentication failure
            audit_logger.log_security_event(
                event_type="AUTHENTICATION_FAILED",
                severity="WARNING",
                ip_address=user_info["ip_address"],
                details=log_details
            )
        else:
            # Client errors
            audit_logger.log_app_event(
                event_type="HTTP_CLIENT_ERROR",
                message=f"HTTP {exc.status_code}: {exc.detail}",
                details=log_details
            )
        
        # Prepare response
        response_content = {
            "error": exc.detail,
            "status_code": exc.status_code,
            "error_id": error_id
        }
        
        # Add extra information for certain status codes
        if exc.status_code == 429:
            response_content["retry_after"] = 60
        elif exc.status_code == 503:
            response_content["retry_after"] = 120
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_content,
            headers=exc.headers
        )
    
    async def handle_validation_error(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors"""
        error_id = self._generate_error_id()
        user_info = self._extract_user_info(request)
        
        # Extract validation details
        validation_errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            validation_errors.append({
                "field": field,
                "message": message,
                "type": error["type"]
            })
        
        # Log validation failure
        audit_logger.log_input_validation_failure(
            validation_type="REQUEST_VALIDATION",
            input_value=f"Fields: {', '.join([err['field'] for err in validation_errors[:3]])}",
            user_id=user_info.get("user_id"),
            ip_address=user_info["ip_address"]
        )
        
        # Log detailed error for debugging
        audit_logger.log_system_error(
            error_type="VALIDATION_ERROR",
            error_message=f"Request validation failed: {len(validation_errors)} errors",
            endpoint=user_info["endpoint"],
            details={
                "error_id": error_id,
                "validation_errors": validation_errors[:5],  # Limit to first 5 errors
                **user_info
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation failed",
                "status_code": 422,
                "error_id": error_id,
                "details": validation_errors[:10]  # Limit to first 10 errors
            }
        )
    
    async def handle_database_error(self, request: Request, exc: SQLAlchemyError) -> JSONResponse:
        """Handle database-related errors"""
        error_id = self._generate_error_id()
        user_info = self._extract_user_info(request)
        
        # Determine specific error type and response
        if isinstance(exc, IntegrityError):
            status_code = status.HTTP_409_CONFLICT
            error_detail = "Data integrity constraint violated"
            log_severity = "WARNING"
        elif isinstance(exc, OperationalError):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            error_detail = "Database service temporarily unavailable"
            log_severity = "CRITICAL"
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_detail = "Database operation failed"
            log_severity = "ERROR"
        
        # Log the database error
        audit_logger.log_system_error(
            error_type="DATABASE_ERROR",
            error_message=self._sanitize_error_details(exc),
            endpoint=user_info["endpoint"],
            details={
                "error_id": error_id,
                "exception_type": type(exc).__name__,
                **user_info
            }
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": error_detail,
                "status_code": status_code,
                "error_id": error_id
            }
        )
    
    async def handle_generic_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle all other unhandled exceptions"""
        error_id = self._generate_error_id()
        user_info = self._extract_user_info(request)
        
        # Get error mapping if available
        error_mapping = self.error_mappings.get(type(exc))
        if error_mapping:
            status_code = error_mapping["status_code"]
            error_detail = error_mapping["detail"]
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_detail = "Internal server error"
        
        # Get stack trace for logging (not for client)
        stack_trace = traceback.format_exc()
        
        # Log the error with full details
        audit_logger.log_system_error(
            error_type="UNHANDLED_EXCEPTION",
            error_message=self._sanitize_error_details(exc),
            endpoint=user_info["endpoint"],
            details={
                "error_id": error_id,
                "exception_type": type(exc).__name__,
                "stack_trace": stack_trace[:1000],  # Truncate stack trace
                **user_info
            }
        )
        
        # For security, don't expose internal error details to client
        return JSONResponse(
            status_code=status_code,
            content={
                "error": error_detail,
                "status_code": status_code,
                "error_id": error_id,
                "message": "An unexpected error occurred. Please contact support if the issue persists."
            }
        )


# Global error handler instance
error_handler = ErrorHandler()


async def global_exception_middleware(request: Request, call_next):
    """
    Global exception handling middleware.
    Catches all unhandled exceptions and returns appropriate responses.
    """
    try:
        response = await call_next(request)
        return response
        
    except HTTPException as exc:
        return await error_handler.handle_http_exception(request, exc)
    
    except RequestValidationError as exc:
        return await error_handler.handle_validation_error(request, exc)
    
    except SQLAlchemyError as exc:
        return await error_handler.handle_database_error(request, exc)
    
    except Exception as exc:
        return await error_handler.handle_generic_exception(request, exc)


# Specific exception handlers for FastAPI app

async def http_exception_handler(request: Request, exc: HTTPException):
    """FastAPI HTTP exception handler"""
    return await error_handler.handle_http_exception(request, exc)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """FastAPI validation exception handler"""
    return await error_handler.handle_validation_error(request, exc)


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Database exception handler"""
    return await error_handler.handle_database_error(request, exc)


async def generic_exception_handler(request: Request, exc: Exception):
    """Generic exception handler"""
    return await error_handler.handle_generic_exception(request, exc)


# Security-specific error handlers

class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


class RateLimitError(SecurityError):
    """Exception for rate limit violations"""
    pass


class AuthenticationError(SecurityError):
    """Exception for authentication failures"""
    pass


class AuthorizationError(SecurityError):
    """Exception for authorization failures"""
    pass


class InputValidationError(SecurityError):
    """Exception for input validation failures"""
    pass


async def security_exception_handler(request: Request, exc: SecurityError):
    """Handler for security-related exceptions"""
    error_id = error_handler._generate_error_id()
    user_info = error_handler._extract_user_info(request)
    
    # Map security errors to HTTP status codes
    status_mappings = {
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        InputValidationError: status.HTTP_400_BAD_REQUEST,
    }
    
    status_code = status_mappings.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log security event
    audit_logger.log_security_event(
        event_type=f"SECURITY_{type(exc).__name__.upper()}",
        severity="WARNING",
        user_id=user_info.get("user_id"),
        ip_address=user_info["ip_address"],
        details={
            "error_id": error_id,
            "error_message": str(exc),
            **user_info
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": str(exc),
            "status_code": status_code,
            "error_id": error_id
        }
    )


# Helper functions for error handling

def create_error_response(
    status_code: int,
    message: str,
    error_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_id: Optional error ID for tracking
        details: Optional additional details
    """
    content = {
        "error": message,
        "status_code": status_code,
    }
    
    if error_id:
        content["error_id"] = error_id
    
    if details:
        content["details"] = details
    
    return JSONResponse(status_code=status_code, content=content)


def log_and_raise_error(
    error_type: str,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    **log_details
):
    """
    Log error and raise HTTPException.
    
    Args:
        error_type: Type of error for logging
        message: Error message
        status_code: HTTP status code
        **log_details: Additional details for logging
    """
    error_id = error_handler._generate_error_id()
    
    audit_logger.log_system_error(
        error_type=error_type,
        error_message=message,
        details={"error_id": error_id, **log_details}
    )
    
    raise HTTPException(
        status_code=status_code,
        detail=f"{message} (Error ID: {error_id})"
    )