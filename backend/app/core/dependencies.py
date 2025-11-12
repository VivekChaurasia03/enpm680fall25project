from typing import Optional, Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.models.models import User, UserRole
from app.models.audit_log import FailedLoginAttempt
from app.core.audit_logger import audit_logger
from app.schemas.schemas import TokenData
from datetime import datetime


# Enhanced OAuth2 scheme with better error handling
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Enhanced dependency to get current authenticated user with comprehensive security checks.
    Includes audit logging and session validation.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract IP address and user agent for logging
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    # Check if credentials are provided
    if not credentials:
        audit_logger.log_security_event(
            event_type="MISSING_AUTHENTICATION_TOKEN",
            severity="WARNING",
            ip_address=ip_address,
            details={"endpoint": request.url.path}
        )
        raise credentials_exception
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        role: str = payload.get("role")
        token_type: str = payload.get("type", "access")
        
        if email is None:
            audit_logger.log_security_event(
                event_type="INVALID_TOKEN_NO_SUBJECT",
                severity="WARNING",
                ip_address=ip_address,
                details={"endpoint": request.url.path}
            )
            raise credentials_exception
        
        # Verify this is an access token
        if token_type != "access":
            audit_logger.log_security_event(
                event_type="INVALID_TOKEN_TYPE",
                severity="WARNING",
                ip_address=ip_address,
                details={"token_type": token_type, "endpoint": request.url.path}
            )
            raise credentials_exception
        
        token_data = TokenData(email=email, role=role)
    
    except JWTError as e:
        audit_logger.log_security_event(
            event_type="JWT_VALIDATION_FAILED",
            severity="WARNING",
            ip_address=ip_address,
            details={
                "error": str(e),
                "endpoint": request.url.path,
                "user_agent": user_agent
            }
        )
        raise credentials_exception
    
    # Query user from database
    try:
        result = await db.execute(select(User).where(User.email == token_data.email))
        user = result.scalar_one_or_none()
        
        if user is None:
            audit_logger.log_security_event(
                event_type="TOKEN_USER_NOT_FOUND",
                severity="WARNING",
                ip_address=ip_address,
                details={
                    "email": token_data.email,
                    "endpoint": request.url.path
                }
            )
            raise credentials_exception
        
        # Verify role matches (additional security check)
        if user.role.value != token_data.role:
            audit_logger.log_security_event(
                event_type="TOKEN_ROLE_MISMATCH",
                severity="CRITICAL",
                ip_address=ip_address,
                details={
                    "user_id": user.user_id,
                    "token_role": token_data.role,
                    "actual_role": user.role.value,
                    "endpoint": request.url.path
                }
            )
            raise credentials_exception
        
        # Check if account is locked (additional security layer)
        failed_attempt_result = await db.execute(
            select(FailedLoginAttempt).where(FailedLoginAttempt.user_email == user.email)
        )
        failed_attempt = failed_attempt_result.scalar_one_or_none()
        
        if failed_attempt and failed_attempt.is_locked:
            audit_logger.log_security_event(
                event_type="LOCKED_ACCOUNT_ACCESS_ATTEMPT",
                severity="WARNING",
                ip_address=ip_address,
                details={
                    "user_id": user.user_id,
                    "lockout_remaining": failed_attempt.lockout_remaining_minutes,
                    "endpoint": request.url.path
                }
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked. Try again in {failed_attempt.lockout_remaining_minutes} minutes."
            )
        
        # Log successful authentication validation
        audit_logger.log_app_event(
            event_type="TOKEN_VALIDATION_SUCCESS",
            message="User successfully authenticated",
            details={
                "user_id": user.user_id,
                "role": user.role.value,
                "endpoint": request.url.path,
                "ip_address": ip_address
            }
        )
        
        return user
    
    except HTTPException:
        raise
    except Exception as e:
        audit_logger.log_system_error(
            error_type="USER_AUTHENTICATION_ERROR",
            error_message=str(e),
            endpoint=request.url.path,
            details={
                "ip_address": ip_address,
                "email": token_data.email if 'token_data' in locals() else "unknown"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Enhanced dependency to ensure user is active.
    Can be extended to check for account suspension, email verification, etc.
    """
    # Check if email is verified (if email verification is implemented)
    if not current_user.email_verified:
        audit_logger.log_security_event(
            event_type="UNVERIFIED_EMAIL_ACCESS_ATTEMPT",
            severity="WARNING",
            details={
                "user_id": current_user.user_id,
                "email": current_user.email
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified. Please verify your email to continue."
        )
    
    # Additional checks can be added here:
    # - Account suspension
    # - Password expiration
    # - Terms of service acceptance
    # - etc.
    
    return current_user


async def get_current_fleet_manager(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Enhanced dependency to ensure current user is a Fleet Manager with audit logging.
    """
    if current_user.role != UserRole.FLEET_MANAGER:
        audit_logger.log_unauthorized_access(
            user_id=current_user.user_id,
            user_role=current_user.role.value,
            required_role="FLEET_MANAGER",
            endpoint="fleet_manager_endpoint"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires Fleet Manager privileges"
        )
    return current_user


async def get_current_fleet_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Enhanced dependency to ensure current user is a Fleet User with audit logging.
    """
    if current_user.role != UserRole.FLEET_USER:
        audit_logger.log_unauthorized_access(
            user_id=current_user.user_id,
            user_role=current_user.role.value,
            required_role="FLEET_USER",
            endpoint="fleet_user_endpoint"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation is only available to Fleet Users"
        )
    return current_user


async def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get current user (for endpoints that work with or without authentication).
    Returns None if no valid authentication is provided.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


def get_request_context() -> Generator[dict, None, None]:
    """
    Dependency to get request context information.
    Useful for logging and security checks.
    """
    from contextvars import ContextVar
    from fastapi import Request
    
    context = {}
    yield context


async def validate_api_key(
    request: Request,
    api_key: Optional[str] = None
) -> bool:
    """
    Dependency for API key validation (for future API integrations).
    Currently returns True but can be enhanced for API access.
    """
    # This can be enhanced to validate API keys from headers
    # x-api-key or similar
    
    api_key_header = request.headers.get("x-api-key")
    if api_key_header:
        # Validate API key logic here
        # For now, just log the attempt
        audit_logger.log_app_event(
            event_type="API_KEY_ACCESS_ATTEMPT",
            message="API key access attempted",
            details={
                "ip_address": request.client.host if request.client else "unknown",
                "endpoint": request.url.path
            }
        )
    
    return True


async def get_db_with_logging() -> Generator[AsyncSession, None, None]:
    """
    Database dependency with enhanced logging for security-sensitive operations.
    """
    db = None
    try:
        async for session in get_db():
            db = session
            yield session
    except Exception as e:
        audit_logger.log_system_error(
            error_type="DATABASE_CONNECTION_ERROR",
            error_message=str(e),
            details={"component": "database_dependency"}
        )
        raise
    finally:
        if db:
            try:
                await db.close()
            except Exception as e:
                audit_logger.log_system_error(
                    error_type="DATABASE_CLOSE_ERROR",
                    error_message=str(e)
                )


class SecurityDependencies:
    """
    Class-based dependencies for complex security scenarios.
    """
    
    @staticmethod
    async def require_fresh_authentication(
        current_user: User = Depends(get_current_user),
        request: Request = None
    ) -> User:
        """
        Require that the user authenticated recently (for sensitive operations).
        """
        # This would check token issued time against current time
        # and require re-authentication for sensitive operations
        # For now, just log the sensitive operation attempt
        
        audit_logger.log_user_action(
            user_id=current_user.user_id,
            action="SENSITIVE_OPERATION_ATTEMPT",
            resource_type="AUTH",
            ip_address=request.client.host if request and request.client else "unknown"
        )
        
        return current_user
    
    @staticmethod
    async def require_password_verification(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        Require password verification for highly sensitive operations.
        This would typically require a password field in the request.
        """
        # Implementation would verify the user's password again
        # For now, just return the user
        return current_user
    
    @staticmethod
    async def validate_session_security(
        request: Request,
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        Validate session security including IP consistency, user agent, etc.
        """
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Log session details for security monitoring
        audit_logger.log_app_event(
            event_type="SESSION_VALIDATION",
            message="Session security validation",
            details={
                "user_id": current_user.user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "endpoint": request.url.path
            }
        )
        
        # Additional session security checks can be added here:
        # - IP address consistency
        # - User agent consistency
        # - Session timeout
        # - Concurrent session limits
        
        return current_user


# Utility functions for dependency injection

def create_permission_checker(permission: str):
    """
    Factory function to create permission-checking dependencies.
    """
    async def check_permission(current_user: User = Depends(get_current_user)) -> User:
        from app.core.permissions import Permissions
        
        if not Permissions.has_permission(current_user.role, permission):
            audit_logger.log_unauthorized_access(
                user_id=current_user.user_id,
                user_role=current_user.role.value,
                required_role=f"Permission: {permission}",
                endpoint="permission_protected_endpoint"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {permission}"
            )
        return current_user
    
    return check_permission


def create_role_checker(allowed_roles: list):
    """
    Factory function to create role-checking dependencies.
    """
    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in allowed_roles:
            audit_logger.log_unauthorized_access(
                user_id=current_user.user_id,
                user_role=current_user.role.value,
                required_role=", ".join(allowed_roles),
                endpoint="role_protected_endpoint"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return check_role